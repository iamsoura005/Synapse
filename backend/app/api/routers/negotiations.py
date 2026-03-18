"""Negotiations API router — view, approve, modify, override, delay, and create."""
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.postgres import get_db
from app.models.negotiation import Negotiation, NegotiationRound, NegotiationStatus
from app.agents.negotiation_engine import run_negotiation
from app.kafka.producer import synapse_producer
from app.config import settings
from app.api.demo_store import store

router = APIRouter(tags=["negotiations"])


@router.get("/negotiations")
async def list_negotiations(
    user_id: str,
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """List negotiations where the user is a party (paginated)."""
    if settings.DEMO_MODE:
        items = store.list_negotiations(user_id)
        return {"negotiations": items[skip: skip + limit], "skip": skip, "limit": limit}

    result = await db.execute(
        select(Negotiation)
        .where(Negotiation.party_ids.any(user_id))
        .offset(skip)
        .limit(limit)
    )
    items = result.scalars().all()
    return {"negotiations": [n.__dict__ for n in items], "skip": skip, "limit": limit}


@router.get("/negotiations/{negotiation_id}")
async def get_negotiation(negotiation_id: str, db: AsyncSession = Depends(get_db)):
    if settings.DEMO_MODE:
        item = store.get_negotiation(negotiation_id)
        if not item:
            raise HTTPException(status_code=404, detail="Not found")
        return item

    neg_uuid = uuid.UUID(negotiation_id)
    result = await db.execute(select(Negotiation).where(Negotiation.id == neg_uuid))
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Not found")
    return n.__dict__


@router.get("/negotiations/{negotiation_id}/rounds")
async def get_negotiation_rounds(negotiation_id: str, db: AsyncSession = Depends(get_db)):
    if settings.DEMO_MODE:
        return {"rounds": store.get_rounds(negotiation_id)}

    neg_uuid = uuid.UUID(negotiation_id)
    result = await db.execute(
        select(NegotiationRound)
        .where(NegotiationRound.negotiation_id == neg_uuid)
        .order_by(NegotiationRound.round_number)
    )
    rounds = result.scalars().all()
    return {"rounds": [r.__dict__ for r in rounds]}


@router.post("/negotiations/{negotiation_id}/approve")
async def approve_negotiation(negotiation_id: str, db: AsyncSession = Depends(get_db)):
    if settings.DEMO_MODE:
        item = store.approve_negotiation(negotiation_id)
        if not item:
            raise HTTPException(status_code=404, detail="Not found")
        return {"status": "approved", "negotiation_id": str(negotiation_id)}

    neg_uuid = uuid.UUID(negotiation_id)
    result = await db.execute(select(Negotiation).where(Negotiation.id == neg_uuid))
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Not found")

    n.status = NegotiationStatus.completed
    n.completed_at = datetime.utcnow()
    await db.commit()
    return {"status": "approved", "negotiation_id": str(negotiation_id)}


@router.post("/negotiations/{negotiation_id}/modify")
async def modify_negotiation(
    negotiation_id: str,
    modification: dict,
    db: AsyncSession = Depends(get_db),
):
    """User modifies one parameter — re-runs one final counter round."""
    if settings.DEMO_MODE:
        item = store.modify_negotiation(negotiation_id, modification)
        if not item:
            raise HTTPException(status_code=404, detail="Not found")
        return {"status": "modified", "resolution": item.get("resolution")}

    neg_uuid = uuid.UUID(negotiation_id)
    result = await db.execute(select(Negotiation).where(Negotiation.id == neg_uuid))
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Not found")

    # Inject user modification into context_brief and re-run
    brief = n.resolution or {}
    brief["user_modification"] = modification

    # Trigger one final counter round via negotiation engine
    final_state = await run_negotiation(str(negotiation_id), brief, max_rounds=1)
    n.resolution   = final_state.get("resolution", n.resolution)
    n.status       = NegotiationStatus.completed
    n.completed_at = datetime.utcnow()
    await db.commit()
    return {"status": "modified", "resolution": final_state.get("resolution")}


@router.post("/negotiations/{negotiation_id}/override")
async def override_negotiation(
    negotiation_id: str,
    custom_terms: dict,
    db: AsyncSession = Depends(get_db),
):
    """User ignores agent resolution and sets their own terms."""
    if settings.DEMO_MODE:
        item = store.override_negotiation(negotiation_id, custom_terms)
        if not item:
            raise HTTPException(status_code=404, detail="Not found")
        return {"status": "overridden"}

    neg_uuid = uuid.UUID(negotiation_id)
    result = await db.execute(select(Negotiation).where(Negotiation.id == neg_uuid))
    n = result.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Not found")

    n.status     = NegotiationStatus.overridden
    n.resolution = {"type": "user_override", "custom_terms": custom_terms, "overridden_at": datetime.utcnow().isoformat()}
    n.completed_at = datetime.utcnow()
    await db.commit()
    return {"status": "overridden"}


@router.post("/negotiations/{negotiation_id}/delay")
async def delay_negotiation(negotiation_id: uuid.UUID, redis=Depends(lambda: None)):
    """Push resolution delivery back by 2 hours."""
    if settings.DEMO_MODE:
        item = store.delay_negotiation(str(negotiation_id), delay_hours=2)
        if not item:
            raise HTTPException(status_code=404, detail="Not found")
        return {"status": "delayed", "retry_after_hours": 2}

    await synapse_producer.emit(
        topic="pipeline.resolution_queue",
        key=str(negotiation_id),
        value={"action": "delay", "negotiation_id": str(negotiation_id), "delay_hours": 2},
    )
    return {"status": "delayed", "retry_after_hours": 2}


@router.post("/negotiations/manual")
async def start_manual_negotiation(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """User-initiated negotiation (not triggered by ambient sensors)."""
    negotiation_type = payload.get("negotiation_type", "expense")
    party_ids = payload.get("party_ids", ["demo-user", "counterparty"])
    context = payload.get("context", "Manual negotiation context")
    urgency = payload.get("urgency", "medium")
    relationship_id = payload.get("relationship_id")

    if settings.DEMO_MODE:
        item = store.start_manual_negotiation(
            negotiation_type=negotiation_type,
            party_ids=party_ids,
            context=context,
            urgency=urgency,
            relationship_id=relationship_id,
        )
        return {"negotiation_id": item["id"], "resolution": item.get("resolution")}

    neg = Negotiation(
        party_ids=party_ids,
        negotiation_type=negotiation_type,
        status=NegotiationStatus.pending,
    )
    db.add(neg)
    await db.commit()

    # Kick off the negotiation engine with user context
    brief = {
        "alert_id":     str(neg.id),
        "tension_type": negotiation_type,
        "party_profiles": [
            {"party_id": pid, "negotiation_style": "collaborative",
             "historical_satisfaction_avg": 0.75, "typical_concession_pct": 10,
             "BATNA_estimate": "Walk away", "communication_preferences": ["async"]}
            for pid in party_ids
        ],
        "relationship_context": {"trust_index": 0.5, "health_score": 70, "total_past_negotiations": 0, "successful_resolution_rate": 0.75},
        "market_data": {},
        "recommended_approach": "collaborative",
        "estimated_rounds": 3,
        "risk_factors": [urgency],
        "user_context": context,
    }
    final_state = await run_negotiation(str(neg.id), brief)
    neg.resolution = final_state.get("resolution")
    neg.status     = NegotiationStatus.completed if final_state.get("agreement_reached") else NegotiationStatus.timed_out
    await db.commit()
    return {"negotiation_id": str(neg.id), "resolution": neg.resolution}
