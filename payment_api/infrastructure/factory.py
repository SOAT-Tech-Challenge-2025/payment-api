"""Factory module for manual dependency injection"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from aioboto3 import Session as AIOBoto3Session
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from payment_api.adapters.inbound.listeners import (
    OrderCreatedHandler,
    OrderCreatedListener,
)
from payment_api.adapters.inbound.rest.v1 import payment_router_v1
from payment_api.adapters.out import MPPaymentGateway, SAPaymentRepository
from payment_api.application.use_cases import (
    CreatePaymentFromOrderUseCase,
    FinalizePaymentByMercadoPagoPaymentIdUseCase,
    FindPaymentByIdUseCase,
    RenderQRCodeUseCase,
)
from payment_api.application.use_cases.ports import (
    AbstractMercadoPagoClient,
    AbstractQRCodeRenderer,
)
from payment_api.domain.ports import PaymentGateway, PaymentRepository
from payment_api.infrastructure.config import (
    APPSettings,
    AWSSettings,
    DatabaseSettings,
    HTTPClientSettings,
    MercadoPagoSettings,
    OrderCreatedListenerSettings,
)
from payment_api.infrastructure.mercado_pago import MercadoPagoAPIClient
from payment_api.infrastructure.mercado_pago_client import MercadoPagoClient
from payment_api.infrastructure.orm import SessionManager
from payment_api.infrastructure.qr_code_renderer import QRCodeRenderer

logger = logging.getLogger(__name__)


def get_app_settings() -> APPSettings:
    """Return an APPSettings instance"""
    return APPSettings()


def get_database_settings() -> DatabaseSettings:
    """Return a DatabaseSettings instance"""
    return DatabaseSettings()


def get_http_client_settings() -> HTTPClientSettings:
    """Return an HTTPClientSettings instance"""
    return HTTPClientSettings()


def get_mercado_pago_settings() -> MercadoPagoSettings:
    """Return a MercadoPagoSettings instance"""
    return MercadoPagoSettings()


def get_aws_settings() -> AWSSettings:
    """Return an AWSSettings instance"""
    return AWSSettings()


def get_order_created_listener_settings() -> OrderCreatedListenerSettings:
    """Return an OrderCreatedListenerSettings instance"""
    return OrderCreatedListenerSettings()


def get_session_manager(settings: DatabaseSettings) -> SessionManager:
    """Return a SessionManager instance"""
    return SessionManager(host=settings.DSN, engine_kwargs={"echo": settings.ECHO})


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
) -> FinalizePaymentByMercadoPagoPaymentIdUseCase:
    """Return a FinalizePaymentByMercadoPagoPaymentIdUseCase instance"""
    return FinalizePaymentByMercadoPagoPaymentIdUseCase(
        payment_repository=payment_repository,
        mercado_pago_client=mercado_pago_client,
    )


def order_created_handler(
    use_case: CreatePaymentFromOrderUseCase,
) -> OrderCreatedHandler:
    """Create an OrderCreatedHandler instance"""
    return OrderCreatedHandler(use_case=use_case)


def create_order_created_listener(
    session: AIOBoto3Session,
    handler: OrderCreatedHandler,
    settings: OrderCreatedListenerSettings,
) -> OrderCreatedListener:
    """Create an OrderCreatedListener instance"""
    return OrderCreatedListener(session=session, handler=handler, settings=settings)


def create_api() -> FastAPI:
    """Create FastAPI application instance"""

    logger.info("Creating FastAPI application instance")
    app = FastAPI(lifespan=fastapi_lifespan)
    logger.info("Including payment router v1")
    app.include_router(payment_router_v1)
    return app


@asynccontextmanager
async def fastapi_lifespan(app_instance: FastAPI):
    """Lifespan context manager for FastAPI application"""

    # Application state setup
    logger.info("Loading application settings")
    app_instance.state.app_settings = get_app_settings()
    logger.info("Loading database settings")
    app_instance.state.database_settings = get_database_settings()
    logger.info("Loading HTTP client settings")
    app_instance.state.http_client_settings = get_http_client_settings()
    logger.info("Loading MercadoPago settings")
    app_instance.state.mercado_pago_settings = get_mercado_pago_settings()
    app_instance.title = app_instance.state.app_settings.TITLE
    app_instance.version = app_instance.state.app_settings.VERSION
    app_instance.root_path = app_instance.state.app_settings.ROOT_PATH
    logger.info(
        "Application settings loaded title=%s version=%s root_path=%s",
        app_instance.title,
        app_instance.version,
        app_instance.root_path,
    )

    logger.info("Starting session manager")
    app_instance.state.session_manager = get_session_manager(
        settings=app_instance.state.database_settings
    )

    logger.info("Starting HTTP client")
    app_instance.state.http_client = get_http_client(
        settings=app_instance.state.http_client_settings
    )

    # Application state teardown
    yield
    logger.info("Closing session manager")
    await app_instance.state.session_manager.close()
    logger.info("Closing HTTP client")
    await app_instance.state.http_client.aclose()
