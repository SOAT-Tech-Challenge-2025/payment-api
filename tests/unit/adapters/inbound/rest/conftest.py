# pylint: disable=W0621

"""Fixture to provide an AsyncClient for testing FastAPI endpoints"""

from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from pytest_mock import MockerFixture

from payment_api.adapters.inbound.rest.dependencies.auth import (
    validate_mercado_pago_notification,
)
from payment_api.adapters.inbound.rest.dependencies.core import (
    finalize_payment_by_mercado_pago_payment_id_use_case,
    find_payment_by_id_use_case,
    render_qr_code_use_case,
)
from payment_api.entrypoints.api import app


@pytest.fixture
def payment_use_cases_mock(mocker: MockerFixture):
    """Fixture to provide a mock for payment use cases called in the REST API"""
    return {
        "find_by_id": mocker.MagicMock(),
        "render_qr_code": mocker.MagicMock(),
        "finalize_by_mercado_pago_payment_id": mocker.MagicMock(),
    }


@pytest.fixture
async def test_app_client(
    payment_use_cases_mock: dict,
) -> AsyncGenerator[AsyncClient, None]:
    """Fixture to provide an AsyncClient for testing FastAPI endpoints"""
    app.dependency_overrides = {
        validate_mercado_pago_notification: lambda: None,
        find_payment_by_id_use_case: lambda: payment_use_cases_mock["find_by_id"],
        render_qr_code_use_case: lambda: payment_use_cases_mock["render_qr_code"],
        finalize_payment_by_mercado_pago_payment_id_use_case: (
            lambda: payment_use_cases_mock["finalize_by_mercado_pago_payment_id"]
        ),
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client

    app.dependency_overrides.clear()
