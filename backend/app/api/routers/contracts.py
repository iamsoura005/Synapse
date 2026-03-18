"""Contracts API router — Living Contract CRUD and blockchain verification."""
import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.postgres import get_db
from app.models.contract import LivingContract, ContractStatus
from app.contracts.blockchain import polygon_notarizer
from app.config import settings
from app.api.demo_store import store

router = APIRouter(tags=["contracts"])


@router.get("/contracts")
async def list_contracts(user_id: str, db: AsyncSession = Depends(get_db)):
    if settings.DEMO_MODE:
        return {"contracts": store.list_contracts(user_id)}

    result = await db.execute(
        select(LivingContract).where(LivingContract.party_ids.any(user_id))
    )
    contracts = result.scalars().all()
    return {"contracts": [c.__dict__ for c in contracts]}


@router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str, db: AsyncSession = Depends(get_db)):
    if settings.DEMO_MODE:
        item = store.get_contract(contract_id)
        if not item:
            raise HTTPException(status_code=404, detail="Contract not found")
        return item

    contract_uuid = uuid.UUID(contract_id)
    result = await db.execute(select(LivingContract).where(LivingContract.id == contract_uuid))
    contract = result.scalar_one_or_none()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract.__dict__


@router.post("/contracts")
async def create_contract(
    payload: dict,
    db: AsyncSession = Depends(get_db),
):
    """Create and notarize a new Living Contract on Polygon Amoy."""
    negotiation_id = payload.get("negotiation_id")
    party_ids = payload.get("party_ids", [])
    clauses = payload.get("clauses", [])

    if not negotiation_id:
        raise HTTPException(status_code=400, detail="negotiation_id is required")

    if settings.DEMO_MODE:
        contract = store.create_contract(negotiation_id=negotiation_id, party_ids=party_ids, clauses=clauses)
        return {
            "contract_id": contract["id"],
            "polygon_hash": contract["polygon_hash"],
            "polygon_tx_hash": contract["polygon_tx_hash"],
            "polygon_scan_url": contract["polygon_scan_url"],
        }

    contract = LivingContract(
        negotiation_id=uuid.UUID(negotiation_id),
        party_ids=party_ids,
        clauses=clauses,
        status=ContractStatus.active,
        version=1,
    )
    db.add(contract)
    await db.flush()  # get the ID

    # Notarize
    contract_data = {
        "id": str(contract.id),
        "negotiation_id": negotiation_id,
        "party_ids": sorted(party_ids),
        "clauses": clauses,
        "version": 1,
        "created_at": contract.created_at.isoformat() if contract.created_at else datetime.utcnow().isoformat(),
    }
    content_hash, tx_hash, scan_url = await polygon_notarizer.notarize(
        contract_id=str(contract.id),
        contract_data=contract_data,
    )
    contract.polygon_hash     = content_hash
    contract.polygon_tx_hash  = tx_hash
    contract.polygon_scan_url = scan_url

    await db.commit()
    return {
        "contract_id":      str(contract.id),
        "polygon_hash":     content_hash,
        "polygon_tx_hash":  tx_hash,
        "polygon_scan_url": scan_url,
    }
