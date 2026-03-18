"""Emotion Agent — computes EmotionalReadiness score (0–100) for delivery gating."""
import logging
from datetime import datetime, timedelta
from typing import Optional
from app.agents.schemas import GatingDecision
from app.config import settings

logger = logging.getLogger(__name__)

READINESS_CACHE_KEY    = "emotion_readiness:{user_id}"
READINESS_CACHE_TTL    = 900   # 15 minutes
LAST_NOTIF_KEY         = "last_notif:{user_id}"
HARD_CAP_HOURS         = 48
MIN_DELIVERY_SCORE     = 60.0


class EmotionAgent:
    """
    Runs every 15 minutes per active user via Celery beat.
    Computes EmotionalReadiness score and stores in Redis.
    """

    def __init__(self, redis_client):
        self.redis = redis_client

    async def compute_readiness_score(self, user_id: str, user_config: dict) -> float:
        """
        user_config: {
            receptive_windows: [{start_hour, end_hour, days_of_week}],
            calendar_events: [{start, end}],   # upcoming/recent
        }
        """
        score = 100.0
        now = datetime.utcnow()

        # Factor 1: Time-of-day vs receptive windows
        in_window = self._in_receptive_window(now, user_config.get("receptive_windows", []))
        if not in_window:
            score -= 30

        # Factor 2: Calendar context
        calendar_events = user_config.get("calendar_events", [])
        for ev in calendar_events:
            start = datetime.fromisoformat(ev["start"].replace("Z", ""))
            end   = datetime.fromisoformat(ev["end"].replace("Z", ""))
            mins_since_end  = (now - end).total_seconds() / 60
            mins_until_start = (start - now).total_seconds() / 60

            if 0 < mins_since_end < 30:
                score -= 20       # meeting just ended — decompress time
            if 0 < mins_until_start < 15:
                score -= 25       # meeting imminent
            if (end - start).total_seconds() / 3600 >= 2 and start > now:
                score += 10       # upcoming long free block

        # Factor 3: Response latency (from Redis)
        latency_signal = await self.redis.get(f"response_latency:{user_id}")
        if latency_signal:
            ratio = float(latency_signal)
            if ratio > 2.0:
                score -= 15       # unusually slow responses = busy/stressed

        # Factor 4: Last notification sent
        last_notif = await self.redis.get(LAST_NOTIF_KEY.format(user_id=user_id))
        if last_notif:
            mins_since = (now - datetime.fromisoformat(last_notif)).total_seconds() / 60
            if mins_since < 30:
                score -= 10       # recent notification

        score = max(0.0, min(100.0, score))

        # Cache in Redis
        await self.redis.setex(
            READINESS_CACHE_KEY.format(user_id=user_id),
            READINESS_CACHE_TTL,
            str(score),
        )
        return score

    def _in_receptive_window(self, now: datetime, windows: list) -> bool:
        if not windows:
            return True  # default: always open if no config
        day_of_week = now.weekday()  # 0=Mon … 6=Sun
        hour = now.hour
        for win in windows:
            days = win.get("days_of_week", list(range(7)))
            if day_of_week in days and win["start_hour"] <= hour < win["end_hour"]:
                return True
        return False

    async def get_readiness(self, user_id: str) -> float:
        raw = await self.redis.get(READINESS_CACHE_KEY.format(user_id=user_id))
        return float(raw) if raw else 100.0  # default: assume ready if no data

    async def gate_resolution(
        self,
        resolution: dict,
        party_ids: list[str],
        queued_since: Optional[datetime] = None,
    ) -> GatingDecision:
        """
        Check readiness for ALL parties.
        Returns cleared=True when all parties are ready.
        Forces delivery if queued for > 48h.
        """
        now = datetime.utcnow()
        readiness = {}
        for pid in party_ids:
            readiness[pid] = await self.get_readiness(pid)

        all_ready = all(s >= MIN_DELIVERY_SCORE for s in readiness.values())

        # Hard cap: force after 48h regardless of scores
        forced = False
        if queued_since and (now - queued_since).total_seconds() > HARD_CAP_HOURS * 3600:
            all_ready = True
            forced = True
            logger.info(f"Emotion gate: 48h hard cap reached. Forcing delivery.")

        if all_ready:
            return GatingDecision(
                cleared=True,
                next_check_at=None,
                party_readiness=readiness,
                forced=forced,
            )

        return GatingDecision(
            cleared=False,
            next_check_at=now + timedelta(minutes=15),
            party_readiness=readiness,
        )
