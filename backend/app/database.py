"""
SQLite database for persistent storage of settings and generation history.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, String, DateTime, Text, Integer
from datetime import datetime
import json

DATABASE_URL = "sqlite+aiosqlite:///./data/settings.db"

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class SettingsRecord(Base):
    """Store encrypted application settings."""
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String, unique=True, nullable=False)
    encrypted_value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GenerationHistory(Base):
    """Track generation requests and outputs."""
    __tablename__ = "generation_history"
    
    id = Column(String, primary_key=True)
    request_data = Column(Text)  # JSON
    response_data = Column(Text)  # JSON
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    """Dependency for database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
