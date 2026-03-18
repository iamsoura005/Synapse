"""Relationships API router — CRUD + graph data for the relationship intelligence layer."""
import json
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.postgres import get_db
from app.database.redis_client import get_redis
from app.models.relationship import RelationshipProfile, RelationshipType
from app.graph.neo4j_client import neo4j_client
from app.config import settings
from app.api.demo_store import store

router = APIRouter(tags=["relationships"])


@router.get("/relationships")
async def list_relationships(
    user_id: str,  # In production: extracted from JWT
    db: AsyncSession = Depends(get_db),
):
    """List all relationships with health scores."""
    if settings.DEMO_MODE:
        return {"relationships": store.list_relationships(user_id)}

    result = await db.execute(
        select(RelationshipProfile).where(RelationshipProfile.user_id == user_id)
    )
    relationships = result.scalars().all()
    return {"relationships": [r.__dict__ for r in relationships]}


@router.get("/relationships/{relationship_id}")
async def get_relationship(relationship_id: str, db: AsyncSession = Depends(get_db)):
    if settings.DEMO_MODE:
        rel = store.get_relationship(relationship_id)
        if not rel:
            raise HTTPException(status_code=404, detail="Relationship not found")
        return rel

    result = await db.execute(
        select(RelationshipProfile).where(RelationshipProfile.id == uuid.UUID(relationship_id))
    )
    rel = result.scalar_one_or_none()
    if not rel:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return rel.__dict__


@router.get("/relationships/{relationship_id}/graph")
async def get_relationship_graph(relationship_id: str):
    """Return D3-compatible graph data for visualization."""
    if settings.DEMO_MODE:
        graph = store.get_relationship_graph(relationship_id)
        if not graph:
            raise HTTPException(status_code=404, detail="Relationship not found in graph")
        return graph

    ctx = await neo4j_client.get_relationship_context(relationship_id)
    if not ctx:
        raise HTTPException(status_code=404, detail="Relationship not found in graph")

    party_a = ctx.get("party_a", {})
    party_b = ctx.get("party_b", {})
    rel     = ctx.get("relationship", {})

    return {
        "nodes": [
            {"id": party_a.get("id"), "name": party_a.get("name", "You"), "type": "self"},
            {"id": party_b.get("id"), "name": party_b.get("name", "Contact"),
             "type": "contact", "health_score": rel.get("health_score", 70)},
        ],
        "edges": [
            {
                "source": party_a.get("id"),
                "target": party_b.get("id"),
                "health_score":       rel.get("health_score", 70),
                "relationship_type":  rel.get("type", "other"),
                "tension_trend":      "stable",
                "active_contracts":   0,
            }
        ],
    }


@router.get("/relationships/{relationship_id}/insights")
async def get_relationship_insights(relationship_id: str, redis=Depends(get_redis)):
    """AI-generated relationship insights cached for 24h."""
    if settings.DEMO_MODE:
        return {"insights": store.get_relationship_insights(relationship_id)}

    cache_key = f"insights:{relationship_id}"
    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    ctx = await neo4j_client.get_relationship_context(relationship_id)
    import google.generativeai as genai
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        settings.GEMINI_FLASH_MODEL,
        generation_config=genai.GenerationConfig(temperature=0.4),
    )
    prompt = (
        f"Given this negotiation history data: {json.dumps(ctx, default=str)}\n"
        "Generate exactly 3 actionable insights about this relationship's negotiation patterns.\n"
        'Format: [{"insight": str, "confidence": float, "actionable_suggestion": str}]\n'
        "Return JSON only."
    )
    try:
        resp = model.generate_content(prompt)
        text = resp.text.strip().removeprefix("```json").removesuffix("```").strip()
        insights = json.loads(text)
    except Exception:
        insights = [{"insight": "Insufficient data", "confidence": 0.5, "actionable_suggestion": "Keep using SYNAPSE"}]

    await redis.setex(cache_key, 86400, json.dumps(insights))
    return {"insights": insights}


@router.post("/relationships")
async def create_relationship(
    user_id: str,
    counterparty_id: str,
    relationship_type: RelationshipType,
    db: AsyncSession = Depends(get_db),
):
    if settings.DEMO_MODE:
        rel = store.create_relationship(user_id, counterparty_id, relationship_type.value)
        return {"id": rel["id"], "status": "created"}

    rel = RelationshipProfile(
        user_id=user_id,
        counterparty_id=counterparty_id,
        relationship_type=relationship_type,
    )
    db.add(rel)
    await db.commit()
    # Also create in Neo4j
    await neo4j_client.create_relationship(user_id, counterparty_id, relationship_type.value)
    return {"id": str(rel.id), "status": "created"}


@router.delete("/relationships/{relationship_id}")
async def delete_relationship(relationship_id: str, db: AsyncSession = Depends(get_db)):
    if settings.DEMO_MODE:
        deleted = store.delete_relationship(relationship_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Not found")
        return {"status": "deleted"}

    result = await db.execute(
        select(RelationshipProfile).where(RelationshipProfile.id == uuid.UUID(relationship_id))
    )
    rel = result.scalar_one_or_none()
    if not rel:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(rel)
    await db.commit()
    return {"status": "deleted"}
