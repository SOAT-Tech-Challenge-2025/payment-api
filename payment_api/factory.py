"""Factory module for manual dependency injection"""

from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from payment_api.adapters.out.orm.session_manager import SessionManager
from payment_api.adapters.out.sa_payment_repository import SAPaymentRepository
from payment_api.config import Settings
from payment_api.domain.ports import PaymentRepository


def get_settings() -> Settings:
    """Return a Settings instance"""
    return Settings()


def get_session_manager(settings: Settings) -> SessionManager:
    """Return a SessionManager instance"""
    return SessionManager(
        host=settings.DB_DSN, engine_kwargs={"echo": settings.DB_ECHO}
    )


async def get_db_session(
    session_manager: SessionManager,
) -> AsyncIterator[AsyncSession]:
    """Get a database session"""
    async with session_manager.session() as session:
        yield session


def get_payment_repository(session: AsyncSession) -> PaymentRepository:
    """Return a PaymentRepository instance"""
    return SAPaymentRepository(session=session)
