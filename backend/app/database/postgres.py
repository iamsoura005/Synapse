from typing import AsyncGenerator
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Use pydantic-settings in a real app, here we fallback to os.getenv for simplicity
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://synapse:password@localhost:5432/synapse")

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if settings.DEMO_MODE:
        yield None
        return
    async with async_session_maker() as session:
        yield session
