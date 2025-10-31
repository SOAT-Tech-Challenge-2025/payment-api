"""Core dependencies for the REST adapter"""

import logging
from typing import Annotated, AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from payment_api.application.use_cases import (
    FinalizePaymentByMercadoPagoPaymentIdUseCase,
    FindPaymentByIdUseCase,
    RenderQRCodeUseCase,
)
from payment_api.application.use_cases.ports import (
    AbstractMercadoPagoClient,
    AbstractQRCodeRenderer,
)
from payment_api.domain.ports import PaymentRepository
from payment_api.infrastructure import factory
from payment_api.infrastructure.mercado_pago import MercadoPagoAPIClient

logger = logging.getLogger(__name__)


async def db_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Dependency that provides a database session"""
    async with factory.get_db_session(
        session_manager=request.app.state.session_manager
    ) as session:
        logger.debug("Providing new database session via dependency")
        yield session


def qr_code_renderer() -> AbstractQRCodeRenderer:
    """Dependency that provides a QRCodeRenderer instance"""
    logger.debug("Providing QRCodeRenderer via dependency")
    return factory.get_qr_code_renderer()


def mercado_pago_api_client(request: Request) -> MercadoPagoAPIClient:
    """Dependency that provides a MercadoPagoAPIClient instance"""
    logger.debug("Providing MercadoPagoAPIClient via dependency")
    return factory.get_mercado_pago_api_client(
        settings=request.app.state.mercado_pago_settings,
        http_client=request.app.state.http_client,
    )


DBSessionDep = Annotated[AsyncSession, Depends(db_session)]
QRCodeRendererDep = Annotated[AbstractQRCodeRenderer, Depends(qr_code_renderer)]
MercadoPagoAPIClientDep = Annotated[
    MercadoPagoAPIClient, Depends(mercado_pago_api_client)
]


def mercado_pago_client(
    api_client: MercadoPagoAPIClientDep,
) -> AbstractMercadoPagoClient:
    """Dependency that provides a MercadoPagoClient instance"""
    logger.debug("Providing MercadoPagoClient via dependency")
    return factory.get_mercado_pago_client(mercado_pago_api_client=api_client)


MercadoPagoClientDep = Annotated[
    AbstractMercadoPagoClient, Depends(mercado_pago_client)
]


def payment_repository(session: DBSessionDep) -> PaymentRepository:
    """Dependency that provides a PaymentRepository instance"""
    logger.debug("Providing PaymentRepository via dependency")
    return factory.get_payment_repository(session=session)


PaymentRepositoryDep = Annotated[PaymentRepository, Depends(payment_repository)]


def find_payment_by_id_use_case(
    repository: PaymentRepositoryDep,
) -> FindPaymentByIdUseCase:
    """Dependency that provides a FindPaymentByIdUseCase instance"""
    logger.debug("Providing FindPaymentByIdUseCase via dependency")
    return factory.get_find_payment_by_id_use_case(payment_repository=repository)


def render_qr_code_use_case(
    repository: PaymentRepositoryDep, renderer: QRCodeRendererDep
) -> RenderQRCodeUseCase:
    """Dependency that provides a RenderQRCodeUseCase instance"""
    logger.debug("Providing RenderQRCodeUseCase via dependency")
    return factory.get_render_qr_code_use_case(
        payment_repository=repository, qr_code_renderer=renderer
    )


def finalize_payment_by_mercado_pago_payment_id_use_case(
    repository: PaymentRepositoryDep,
    mp_client: MercadoPagoClientDep,
) -> FinalizePaymentByMercadoPagoPaymentIdUseCase:
    """Dependency that provides a
    FinalizePaymentByMercadoPagoPaymentIdUseCase instance"""
    logger.debug(
        "Providing FinalizePaymentByMercadoPagoPaymentIdUseCase via dependency"
    )

    return factory.get_finalize_payment_by_mercado_pago_payment_id_use_case(
        payment_repository=repository,
        mercado_pago_client=mp_client,
    )


FindPaymentByIdUseCaseDep = Annotated[
    FindPaymentByIdUseCase, Depends(find_payment_by_id_use_case)
]

RenderQRCodeUseCaseDep = Annotated[
    RenderQRCodeUseCase, Depends(render_qr_code_use_case)
]

FinalizePaymentByMercadoPagoPaymentIdUseCaseDep = Annotated[
    FinalizePaymentByMercadoPagoPaymentIdUseCase,
    Depends(finalize_payment_by_mercado_pago_payment_id_use_case),
]


__all__ = [
    "DBSessionDep",
    "QRCodeRendererDep",
    "MercadoPagoAPIClientDep",
    "MercadoPagoClientDep",
    "PaymentRepositoryDep",
    "FindPaymentByIdUseCaseDep",
    "RenderQRCodeUseCaseDep",
    "FinalizePaymentByMercadoPagoPaymentIdUseCaseDep",
]
