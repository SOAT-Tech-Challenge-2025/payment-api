"""Core dependencies for the REST adapter"""

import logging
from typing import Annotated, AsyncIterator

from aioboto3 import Session as AIOBoto3Session
from fastapi import Depends, Request
from httpx import AsyncClient
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
from payment_api.domain.ports import PaymentClosedPublisher, PaymentRepository
from payment_api.infrastructure import factory
from payment_api.infrastructure.config import (
    AWSSettings,
    MercadoPagoSettings,
    PaymentClosedPublisherSettings,
)
from payment_api.infrastructure.mercado_pago import MercadoPagoAPIClient
from payment_api.infrastructure.orm import SessionManager

logger = logging.getLogger(__name__)


def aws_settings_dep(request: Request) -> AWSSettings:
    """Dependency that provides AWSSettings instance"""
    logger.debug("Providing AWSSettings via dependency")
    return request.app.state.aws_settings


def payment_closed_publisher_settings_dep(
    request: Request,
) -> PaymentClosedPublisherSettings:
    """Dependency that provides PaymentClosedPublisherSettings instance"""
    logger.debug("Providing PaymentClosedPublisherSettings via dependency")
    return request.app.state.payment_closed_publisher_settings


def mercado_pago_settings_dep(request: Request) -> MercadoPagoSettings:
    """Dependency that provides MercadoPagoSettings instance"""
    logger.debug("Providing MercadoPagoSettings via dependency")
    return request.app.state.mercado_pago_settings


def http_client_dep(request: Request) -> AsyncClient:
    """Dependency that provides an AsyncClient instance"""
    logger.debug("Providing AsyncClient via dependency")
    return request.app.state.http_client


def session_manager_dep(request: Request) -> SessionManager:
    """Dependency that provides a SessionManager instance"""
    logger.debug("Providing SessionManager via dependency")
    return request.app.state.session_manager


AWSSettingsDep = Annotated[AWSSettings, Depends(aws_settings_dep)]

PaymentClosedPublisherSettingsDep = Annotated[
    PaymentClosedPublisherSettings, Depends(payment_closed_publisher_settings_dep)
]

MercadoPagoSettingsDep = Annotated[
    MercadoPagoSettings, Depends(mercado_pago_settings_dep)
]

HTTPClientDep = Annotated[AsyncClient, Depends(http_client_dep)]

SessionManagerDep = Annotated[SessionManager, Depends(session_manager_dep)]


async def db_session(session_manager: SessionManagerDep) -> AsyncIterator[AsyncSession]:
    """Dependency that provides a database session"""
    async with factory.get_db_session(session_manager=session_manager) as session:
        logger.debug("Providing new database session via dependency")
        yield session


def get_aws_session(settings: AWSSettingsDep) -> AIOBoto3Session:
    """Dependency that provides an AIOBoto3Session instance"""
    logger.debug("Providing AIOBoto3Session via dependency")
    return factory.get_aws_session(settings=settings)


def qr_code_renderer() -> AbstractQRCodeRenderer:
    """Dependency that provides a QRCodeRenderer instance"""
    logger.debug("Providing QRCodeRenderer via dependency")
    return factory.get_qr_code_renderer()


def mercado_pago_api_client(
    settings: MercadoPagoSettingsDep, http_client: HTTPClientDep
) -> MercadoPagoAPIClient:
    """Dependency that provides a MercadoPagoAPIClient instance"""
    logger.debug("Providing MercadoPagoAPIClient via dependency")
    return factory.get_mercado_pago_api_client(
        settings=settings,
        http_client=http_client,
    )


DBSessionDep = Annotated[AsyncSession, Depends(db_session)]
QRCodeRendererDep = Annotated[AbstractQRCodeRenderer, Depends(qr_code_renderer)]
AWSSessionDep = Annotated[AIOBoto3Session, Depends(get_aws_session)]
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


def payment_closed_publisher_dep(
    settings: PaymentClosedPublisherSettingsDep, session: AWSSessionDep
) -> PaymentClosedPublisher:
    """Dependency that provides a PaymentClosedPublisher instance"""
    logger.debug("Providing PaymentClosedPublisher via dependency")
    return factory.get_payment_closed_publisher(
        settings=settings, aio_boto3_session=session
    )


PaymentRepositoryDep = Annotated[PaymentRepository, Depends(payment_repository)]
PaymentClosedPublisherDep = Annotated[
    PaymentClosedPublisher, Depends(payment_closed_publisher_dep)
]


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
    payment_closed_publisher: PaymentClosedPublisherDep,
) -> FinalizePaymentByMercadoPagoPaymentIdUseCase:
    """Dependency that provides a
    FinalizePaymentByMercadoPagoPaymentIdUseCase instance"""
    logger.debug(
        "Providing FinalizePaymentByMercadoPagoPaymentIdUseCase via dependency"
    )

    return factory.get_finalize_payment_by_mercado_pago_payment_id_use_case(
        payment_repository=repository,
        mercado_pago_client=mp_client,
        payment_closed_publisher=payment_closed_publisher,
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
    "AWSSettingsDep",
    "PaymentClosedPublisherSettingsDep",
    "MercadoPagoSettingsDep",
    "HTTPClientDep",
    "SessionManagerDep",
    "DBSessionDep",
    "QRCodeRendererDep",
    "AWSSessionDep",
    "MercadoPagoAPIClientDep",
    "MercadoPagoClientDep",
    "PaymentRepositoryDep",
    "PaymentClosedPublisherDep",
    "FindPaymentByIdUseCaseDep",
    "RenderQRCodeUseCaseDep",
    "FinalizePaymentByMercadoPagoPaymentIdUseCaseDep",
]
