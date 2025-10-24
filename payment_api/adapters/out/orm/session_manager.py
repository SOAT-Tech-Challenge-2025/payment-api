"""The database session manager"""

import contextlib
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class SessionManagerNotInitializedError(Exception):
    """Raised when the SessionManager is not initialized"""

    def __init__(self, message: str = "SessionManager is not initialized"):
        super().__init__(message)


class SessionManager:
    """The database session manager"""

    def __init__(self, host: str, engine_kwargs: dict[str, Any] | None = None):
        engine_kwargs = engine_kwargs or {}
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(autocommit=False, bind=self._engine)

    async def close(self):
        """Close the database connection"""
        if self._engine is None:
            raise SessionManagerNotInitializedError()
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """Get a database connection"""
        if self._engine is None:
            raise SessionManagerNotInitializedError()

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """Get a database session"""
        if self._sessionmaker is None:
            raise SessionManagerNotInitializedError()

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
