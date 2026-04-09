"""
database.py — async SQLAlchemy engine and session factory.

Usage in a Robyn route:

    from database import get_session

    @app.get("/tokayo/:uuid")
    async def get_tokayo(request: Request):
        async with get_session() as session:
            tokayo = await session.get(Tokayo, uuid.UUID(request.path_params["uuid"]))
            ...
"""

import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost/tokaya",
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,          # set True in dev to log SQL
    pool_size=10,
    max_overflow=20,
)

AsyncSessionFactory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


@asynccontextmanager
async def get_session() -> AsyncSession:
    """Context manager that yields a transactional AsyncSession."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
