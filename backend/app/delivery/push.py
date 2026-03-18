"""OneSignal push notification delivery for SYNAPSE."""
import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)

ONESIGNAL_API = "https://onesignal.com/api/v1/notifications"


class PushDelivery:
    """Send resolution cards via OneSignal push notifications."""

    async def send_resolution_card(
        self,
        user_id: str,
        resolution: dict,
        contract_id: str,
    ) -> bool:
        """
        Send a resolution card notification.
        Returns True if successfully accepted by OneSignal.
        """
        summary = resolution.get("resolution", {}).get("type", "Agreement reached")
        payload = {
            "app_id": settings.ONESIGNAL_APP_ID,
            "include_external_user_ids": [user_id],
            "headings": {"en": "Your agent reached a resolution 🤝"},
            "contents": {"en": f"{summary} · Tap to review"},
            "priority": 10,
            "ttl": 86400,
            "data": {
                "type": "resolution_card",
                "negotiation_id": resolution.get("negotiation_id", ""),
                "contract_id": contract_id,
                "resolution_summary": str(summary),
                "actions": ["approve", "modify", "override", "delay"],
            },
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    ONESIGNAL_API,
                    json=payload,
                    headers={
                        "Authorization": f"Basic {settings.ONESIGNAL_REST_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    timeout=10.0,
                )
                resp.raise_for_status()
                logger.info(f"Push sent to {user_id}: {resp.json()}")
                return True
        except Exception as e:
            logger.error(f"OneSignal push failed for {user_id}: {e}")
            return False
