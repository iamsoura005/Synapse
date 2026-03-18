"""Integrations API router — OAuth connect/disconnect for external services."""
import base64
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from cryptography.fernet import Fernet

from app.database.postgres import get_db
from app.models.user import User
from app.config import settings
from app.api.demo_store import store

router = APIRouter(tags=["integrations"])

SUPPORTED_INTEGRATIONS = ["google_calendar", "gmail", "slack", "splitwise"]

# OAuth config per integration (redirect URIs etc. would be environment-specific)
OAUTH_CONFIGS = {
    "google_calendar": {
        "auth_url": "https://accounts.google.com/o/oauth2/auth",
        "scopes": ["https://www.googleapis.com/auth/calendar.readonly"],
    },
    "gmail": {
        "auth_url": "https://accounts.google.com/o/oauth2/auth",
        "scopes": ["https://www.googleapis.com/auth/gmail.metadata"],
    },
    "slack": {
        "auth_url": "https://slack.com/oauth/v2/authorize",
        "scopes": ["channels:history", "reactions:read"],
    },
    "splitwise": {
        "auth_url": "https://secure.splitwise.com/oauth/authorize",
        "scopes": [],
    },
}


def _get_fernet() -> Fernet:
    key = settings.INTEGRATION_ENCRYPTION_KEY
    if not key:
        # Generate a temporary key for dev (not persistent)
        key = base64.urlsafe_b64encode(os.urandom(32)).decode()
    return Fernet(key.encode() if isinstance(key, str) else key)


@router.post("/integrations/connect/{integration_name}")
async def connect_integration(integration_name: str, user_id: str):
    """Return the OAuth authorization URL for the given integration."""
    if integration_name not in SUPPORTED_INTEGRATIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported integration: {integration_name}")

    if settings.DEMO_MODE:
        store.connect_integration(user_id=user_id, integration_name=integration_name)
        return {
            "integration": integration_name,
            "auth_url": "demo://connected",
            "scopes": OAUTH_CONFIGS[integration_name]["scopes"],
            "message": "Connected in demo mode",
        }

    config = OAUTH_CONFIGS[integration_name]
    return {
        "integration": integration_name,
        "auth_url": config["auth_url"],
        "scopes": config["scopes"],
        "message": "Redirect user to auth_url with your OAuth client credentials",
    }


@router.get("/integrations/callback/{integration_name}")
async def integration_callback(
    integration_name: str,
    code: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    OAuth callback endpoint.
    In production: exchange code for token, encrypt, store in user record.
    """
    if integration_name not in SUPPORTED_INTEGRATIONS:
        raise HTTPException(status_code=400, detail="Unsupported integration")

    if settings.DEMO_MODE:
        store.connect_integration(user_id=user_id, integration_name=integration_name)
        return {"status": "connected", "integration": integration_name}

    fernet = _get_fernet()
    encrypted_token = fernet.encrypt(code.encode()).decode()

    # Append to user's connected_integrations array (PostgreSQL array column)
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    integrations = list(user.connected_integrations or [])
    if integration_name not in integrations:
        integrations.append(integration_name)
    user.connected_integrations = integrations
    await db.commit()

    return {"status": "connected", "integration": integration_name}


@router.delete("/integrations/{integration_name}")
async def disconnect_integration(
    integration_name: str,
    user_id: str,
    db: AsyncSession = Depends(get_db),
):
    if settings.DEMO_MODE:
        store.disconnect_integration(user_id=user_id, integration_name=integration_name)
        return {"status": "disconnected", "integration": integration_name}

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    integrations = [i for i in (user.connected_integrations or []) if i != integration_name]
    user.connected_integrations = integrations
    await db.commit()
    return {"status": "disconnected", "integration": integration_name}


@router.get("/integrations/status")
async def get_integration_status(user_id: str, db: AsyncSession = Depends(get_db)):
    if settings.DEMO_MODE:
        return {"integrations": store.get_integration_status(user_id)}

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    all_statuses = {
        name: (name in (user.connected_integrations or []))
        for name in SUPPORTED_INTEGRATIONS
    }
    return {"integrations": all_statuses}
