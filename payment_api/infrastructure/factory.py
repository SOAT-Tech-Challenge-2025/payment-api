"""Factory module for manual dependency injection"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from aioboto3 import Session as AIOBoto3Session
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from payment_api.adapters.inbound.listeners import (
    OrderCreatedHandler,
    OrderCreatedListener,
)
from payment_api.adapters.out import (
    BotoPaymentClosedPublisher,
    MercadoPagoClient,
    MPPaymentGateway,
    QRCodeRenderer,
    SAPaymentRepository,
)
from payment_api.application.use_cases import (
    CreatePaymentFromOrderUseCase,
    FinalizePaymentByMercadoPagoPaymentIdUseCase,
    FindPaymentByIdUseCase,
    RenderQRCodeUseCase,
)
from payment_api.domain.ports import MercadoPagoClient as AbstractMercadoPagoClient
from payment_api.domain.ports import (
    PaymentClosedPublisher,
    PaymentGateway,
    PaymentRepository,
)
from payment_api.domain.ports import QRCodeRenderer as AbstractQRCodeRenderer
from payment_api.infrastructure.config import (
    AWSSettings,
    DatabaseSettings,
    HTTPClientSettings,
    MercadoPagoSettings,
    OrderCreatedListenerSettings,
    PaymentClosedPublisherSettings,
)
from payment_api.infrastructure.mercado_pago import MercadoPagoAPIClient
from payment_api.infrastructure.orm import SessionManager

logger = logging.getLogger(__name__)


def get_session_manager(settings: DatabaseSettings) -> SessionManager:
    """Return a SessionManager instance"""
    return SessionManager(settings=settings)


@asynccontextmanager
async def get_db_session(
    session_manager: SessionManager,
) -> AsyncIterator[AsyncSession]:
    """Get a database session"""

    async with session_manager.session() as session:
        yield session


def get_aws_session(settings: AWSSettings) -> AIOBoto3Session:
    """Return an AIOBoto3Session instance"""
    return AIOBoto3Session(
        aws_access_key_id=settings.ACCESS_KEY_ID,
        aws_secret_access_key=settings.SECRET_ACCESS_KEY,
        region_name=settings.REGION_NAME,
        aws_account_id=settings.ACCOUNT_ID,
    )


def get_http_client(settings: HTTPClientSettings) -> AsyncClient:
    """Return an AsyncClient instance"""
    return AsyncClient(timeout=settings.TIMEOUT)


def get_payment_repository(session: AsyncSession) -> PaymentRepository:
    """Return a PaymentRepository instance"""
    return SAPaymentRepository(session=session)


def get_mercado_pago_api_client(
    settings: MercadoPagoSettings, http_client: AsyncClient
) -> MercadoPagoAPIClient:
    """Return a MercadoPagoAPIClient instance"""
    return MercadoPagoAPIClient(settings=settings, http_client=http_client)


def get_payment_gateway(
    settings: MercadoPagoSettings, mp_client: MercadoPagoAPIClient
) -> PaymentGateway:
    """Return a MPPaymentGateway instance"""
    return MPPaymentGateway(settings=settings, mp_client=mp_client)


def get_payment_closed_publisher(
    settings: PaymentClosedPublisherSettings,
    aio_boto3_session: AIOBoto3Session,
) -> PaymentClosedPublisher:
    """Return a PaymentClosedPublisher instance"""
    return BotoPaymentClosedPublisher(
        aio_boto3_session=aio_boto3_session, settings=settings
    )


def get_qr_code_renderer() -> AbstractQRCodeRenderer:
    """Return a QRCodeRenderer instance"""
    return QRCodeRenderer()


def get_mercado_pago_client(
    mercado_pago_api_client: MercadoPagoAPIClient,
) -> AbstractMercadoPagoClient:
    """Return a MercadoPagoClient instance"""
    return MercadoPagoClient(api_client=mercado_pago_api_client)


def get_create_payment_from_order_use_case(
    payment_repository: PaymentRepository,
    payment_gateway: PaymentGateway,
) -> CreatePaymentFromOrderUseCase:
    """Return a CreatePaymentFromOrderUseCase instance"""
    return CreatePaymentFromOrderUseCase(
        payment_repository=payment_repository,
        payment_gateway=payment_gateway,
    )


def get_find_payment_by_id_use_case(
    payment_repository: PaymentRepository,
) -> FindPaymentByIdUseCase:
    """Return a FindPaymentByIdUseCase instance"""
    return FindPaymentByIdUseCase(payment_repository=payment_repository)


def get_render_qr_code_use_case(
    payment_repository: PaymentRepository,
    qr_code_renderer: AbstractQRCodeRenderer,
) -> RenderQRCodeUseCase:
    """Return a RenderQRCodeUseCase instance"""
    return RenderQRCodeUseCase(
        payment_repository=payment_repository, qr_code_renderer=qr_code_renderer
    )


def get_finalize_payment_by_mercado_pago_payment_id_use_case(
    payment_repository: PaymentRepository,
    mercado_pago_client: AbstractMercadoPagoClient,
    payment_closed_publisher: PaymentClosedPublisher,
) -> FinalizePaymentByMercadoPagoPaymentIdUseCase:
    """Return a FinalizePaymentByMercadoPagoPaymentIdUseCase instance"""
    return FinalizePaymentByMercadoPagoPaymentIdUseCase(
        payment_repository=payment_repository,
        mercado_pago_client=mercado_pago_client,
        payment_closed_publisher=payment_closed_publisher,
    )


def create_payment_from_order_use_case_factory(
    mercado_pago_settings: MercadoPagoSettings,
    http_client: AsyncClient,
):
    """Create a factory function for creating use cases with sessions"""

    def use_case_factory(session: AsyncSession) -> CreatePaymentFromOrderUseCase:
        repository = get_payment_repository(session=session)
        mp_api_client = get_mercado_pago_api_client(
            settings=mercado_pago_settings, http_client=http_client
        )

        gateway = get_payment_gateway(
            settings=mercado_pago_settings,
            mp_client=mp_api_client,
        )

        return get_create_payment_from_order_use_case(
            payment_repository=repository,
            payment_gateway=gateway,
        )

    return use_case_factory


def get_order_created_handler(
    session_manager: SessionManager,
    mercado_pago_settings: MercadoPagoSettings,
    http_client: AsyncClient,
) -> OrderCreatedHandler:
    """Create an OrderCreatedHandler instance"""
    return OrderCreatedHandler(
        session_manager=session_manager,
        use_case_factory=create_payment_from_order_use_case_factory(
            mercado_pago_settings=mercado_pago_settings, http_client=http_client
        ),
    )


def create_order_created_listener(
    session: AIOBoto3Session,
    handler: OrderCreatedHandler,
    settings: OrderCreatedListenerSettings,
) -> OrderCreatedListener:
    """Create an OrderCreatedListener instance"""
    return OrderCreatedListener(session=session, handler=handler, settings=settings)
