"""FastAPI main entrypoint for SYNAPSE backend."""
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database.postgres import engine, Base
from app.database.redis_client import get_redis, close_redis
from app.graph.neo4j_client import neo4j_client
from app.kafka.producer import synapse_producer
from app.kafka.consumer import (
    TensionSignalConsumer,
    NegotiationStartConsumer,
    ResolutionQueueConsumer,
    DeliveryReadyConsumer,
    ContractEventsConsumer,
)

from app.api.routers.relationships import router as relationships_router
from app.api.routers.negotiations import router as negotiations_router
from app.api.routers.contracts import router as contracts_router
from app.api.routers.integrations import router as integrations_router

logger = logging.getLogger(__name__)

# ── Background consumer tasks ─────────────────────────────────────────────────
_consumer_tasks: list[asyncio.Task] = []


async def _noop_handler(payload: dict):
    """Placeholder handler — replace with real agents in each consumer."""
    logger.debug(f"Received payload: {payload}")


async def start_kafka_consumers():
    consumers = [
        TensionSignalConsumer(_noop_handler),
        NegotiationStartConsumer(_noop_handler),
        ResolutionQueueConsumer(_noop_handler),
        DeliveryReadyConsumer(_noop_handler),
        ContractEventsConsumer(_noop_handler),
    ]
    for consumer in consumers:
        task = asyncio.create_task(consumer.run())
        _consumer_tasks.append(task)
    logger.info(f"Started {len(consumers)} Kafka consumers.")


async def stop_kafka_consumers():
    for task in _consumer_tasks:
        task.cancel()
    await asyncio.gather(*_consumer_tasks, return_exceptions=True)
    _consumer_tasks.clear()
    logger.info("All Kafka consumers stopped.")


async def check_all_services() -> dict:
    if settings.DEMO_MODE:
        return {"mode": "demo"}

    status = {}
    try:
        await neo4j_client.verify_connectivity()
        status["neo4j"] = "ok"
    except Exception as e:
        status["neo4j"] = f"error: {e}"
    try:
        redis = await get_redis()
        await redis.ping()
        status["redis"] = "ok"
    except Exception as e:
        status["redis"] = f"error: {e}"
    status["kafka"] = "running"  # consumers started = alive
    return status


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Startup
    logger.info("SYNAPSE starting up…")

    if settings.DEMO_MODE:
        logger.info("Demo mode enabled: external services are disabled.")
        logger.info("SYNAPSE ready.")
        yield
        logger.info("SYNAPSE shutting down…")
        return
    
    # Try to initialize database (optional, services may not be running)
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✓ Database initialized")
    except Exception as e:
        logger.warning(f"⚠ Database initialization failed (service may not be running): {e}")
    
    # Try to start Kafka consumers (optional)
    try:
        await start_kafka_consumers()
        logger.info("✓ Kafka consumers started")
    except Exception as e:
        logger.warning(f"⚠ Kafka startup failed (service may not be running): {e}")
    
    # Try to verify Neo4j (optional)
    try:
        await neo4j_client.verify_connectivity()
        logger.info("✓ Neo4j connected")
    except Exception as e:
        logger.warning(f"⚠ Neo4j connectivity check failed (service may not be running): {e}")
    
    logger.info("SYNAPSE ready. (Some services may be unavailable)")
    yield
    
    # Shutdown
    logger.info("SYNAPSE shutting down…")
    try:
        await stop_kafka_consumers()
    except Exception as e:
        logger.warning(f"⚠ Kafka shutdown error: {e}")
    
    try:
        synapse_producer.close()
    except Exception as e:
        logger.warning(f"⚠ Producer close error: {e}")
    
    try:
        await close_redis()
    except Exception as e:
        logger.warning(f"⚠ Redis close error: {e}")
    
    try:
        await neo4j_client.close()
    except Exception as e:
        logger.warning(f"⚠ Neo4j close error: {e}")


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="SYNAPSE API",
    description="Ambient Relationship Intelligence OS",
    version="0.1.0",
    lifespan=lifespan,
)

frontend_origins = [origin.strip() for origin in settings.FRONTEND_ORIGINS.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
API_PREFIX = "/api/v1"
app.include_router(relationships_router, prefix=API_PREFIX)
app.include_router(negotiations_router,  prefix=API_PREFIX)
app.include_router(contracts_router,     prefix=API_PREFIX)
app.include_router(integrations_router,  prefix=API_PREFIX)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    if settings.DEMO_MODE:
        return {"status": "ok", "mode": "demo"}
    services = await check_all_services()
    return {"status": "ok", "services": services}


# ── WebSocket real-time feed ──────────────────────────────────────────────────

# Simple in-memory connection manager (swap for Redis pub/sub in production)
class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self._connections.setdefault(user_id, []).append(ws)

    def disconnect(self, user_id: str, ws: WebSocket):
        if user_id in self._connections:
            self._connections[user_id].remove(ws)

    async def broadcast(self, user_id: str, message: dict):
        for ws in self._connections.get(user_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


@app.websocket("/ws/feed/{user_id}")
async def negotiation_feed(websocket: WebSocket, user_id: str):
    """Real-time event feed for the dashboard."""
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Keep connection alive; server pushes events via manager.broadcast()
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
