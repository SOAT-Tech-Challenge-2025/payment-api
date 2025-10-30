"""Factory module for manual dependency injection"""

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
from payment_api.infrastructure.config import Settings
from payment_api.infrastructure.mercado_pago import MercadoPagoAPIClient
from payment_api.infrastructure.mercado_pago_client import MercadoPagoClient
from payment_api.infrastructure.orm import SessionManager
from payment_api.infrastructure.qr_code_renderer import QRCodeRenderer


def get_settings() -> Settings:
    """Return a Settings instance"""
    return Settings()


def get_session_manager(settings: Settings) -> SessionManager:
    """Return a SessionManager instance"""
    return SessionManager(
        host=settings.DB_DSN, engine_kwargs={"echo": settings.DB_ECHO}
    )


@asynccontextmanager
async def get_db_session(
    session_manager: SessionManager,
) -> AsyncIterator[AsyncSession]:
    """Get a database session"""

    async with session_manager.session() as session:
        yield session


def get_aws_session(settings: Settings) -> AIOBoto3Session:
    """Return an AIOBoto3Session instance"""
    return AIOBoto3Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION_NAME,
        aws_account_id=settings.AWS_ACCOUNT_ID,
    )


def get_http_client(settings: Settings) -> AsyncClient:
    """Return an AsyncClient instance"""
    return AsyncClient(timeout=settings.HTTP_TIMEOUT)


def get_payment_repository(session: AsyncSession) -> PaymentRepository:
    """Return a PaymentRepository instance"""
    return SAPaymentRepository(session=session)


def get_mercado_pago_api_client(
    settings: Settings, http_client: AsyncClient
) -> MercadoPagoAPIClient:
    """Return a MercadoPagoAPIClient instance"""
    return MercadoPagoAPIClient(settings=settings, http_client=http_client)


def get_payment_gateway(
    settings: Settings, mp_client: MercadoPagoAPIClient
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
    settings: Settings,
) -> OrderCreatedListener:
    """Create an OrderCreatedListener instance"""
    return OrderCreatedListener(session=session, handler=handler, settings=settings)


def create_api() -> FastAPI:
    """Create FastAPI application instance"""

    app = FastAPI(lifespan=fastapi_lifespan)
    app.include_router(payment_router_v1)
    return app


@asynccontextmanager
async def fastapi_lifespan(app_instance: FastAPI):
    """Lifespan context manager for FastAPI application"""

    # Application state setup
    app_instance.state.settings = get_settings()
    app_instance.title = app_instance.state.settings.PROJECT_NAME
    app_instance.version = app_instance.state.settings.VERSION
    app_instance.root_path = app_instance.state.settings.API_ROOT_PATH
    app_instance.state.session_manager = get_session_manager(
        settings=app_instance.state.settings
    )

    app_instance.state.http_client = get_http_client(
        settings=app_instance.state.settings
    )

    # Application state teardown
    yield
    await app_instance.state.session_manager.close()
    await app_instance.state.http_client.aclose()
