# pylint: disable=W0621

"""Unit tests for MercadoPagoAPIClient"""

import pytest
from httpx import HTTPError, HTTPStatusError, Request
from pytest_mock import MockerFixture

from payment_api.infrastructure.mercado_pago.client import MercadoPagoAPIClient
from payment_api.infrastructure.mercado_pago.exceptions import (
    MPClientError,
    MPNotFoundError,
)
from payment_api.infrastructure.mercado_pago.schemas import (
    MPCreateOrderIn,
    MPCreateOrderOut,
    MPItem,
    MPOrder,
    MPOrderStatus,
    MPPayment,
    MPPaymentOrder,
)


@pytest.fixture
def mp_settings(mocker: MockerFixture):
    """Fixture to create a mock MercadoPagoSettings for testing"""
    mock_settings = mocker.Mock()
    mock_settings.URL = "https://api.mercadopago.com"
    mock_settings.ACCESS_TOKEN = "test-access-token"
    mock_settings.USER_ID = "123456"
    mock_settings.POS = "POS001"
    mock_settings.CALLBACK_URL = "https://example.com/callback"
    mock_settings.WEBHOOK_KEY = "test-webhook-key"
    return mock_settings


@pytest.fixture
def client(mocker: MockerFixture, mp_settings) -> MercadoPagoAPIClient:
    """Fixture to create MercadoPagoAPIClient with mocked dependencies"""
    http_client = mocker.Mock()
    return MercadoPagoAPIClient(settings=mp_settings, http_client=http_client)


@pytest.fixture
def create_order_input() -> MPCreateOrderIn:
    """Fixture to create sample MPCreateOrderIn"""
    return MPCreateOrderIn(
        external_reference="A048",
        total_amount=45.0,
        title="Test Order",
        description="Test order description",
        expiration_date="2024-12-31T23:59:59.000Z",
        items=[
            MPItem(
                title="Product 1",
                category="Category A",
                quantity=2,
                unit_measure="unit",
                unit_price=10.0,
                total_amount=20.0,
            ),
            MPItem(
                title="Product 2",
                category="Category B",
                quantity=1,
                unit_measure="unit",
                unit_price=25.0,
                total_amount=25.0,
            ),
        ],
        notification_url="https://example.com/webhook",
    )


async def test_should_create_dynamic_qr_order_when_api_responds_successfully(
    mocker: MockerFixture,
    client: MercadoPagoAPIClient,
    create_order_input: MPCreateOrderIn,
):
    """Given a valid order creation request
    When the Mercado Pago API responds successfully
    Then a dynamic QR order should be created and returned
    """

    # Given
    expected_response = MPCreateOrderOut(qr_data="sample-qr-data")
    mock_response = mocker.Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = expected_response.model_dump()
    mock_response.raise_for_status.return_value = None

    client.http_client.request = mocker.AsyncMock(return_value=mock_response)

    # When
    result = await client.create_dynamic_qr_order(order_data=create_order_input)

    # Then
    assert result.qr_data == "sample-qr-data"
    client.http_client.request.assert_awaited_once_with(
        "POST",
        "https://api.mercadopago.com/instore/orders/qr/seller/collectors/123456/"
        "pos/POS001/qrs",
        headers={"Authorization": "Bearer test-access-token"},
        json=create_order_input.model_dump(),
    )


async def test_should_raise_mp_not_found_error_when_create_dynamic_qr_order_returns_404(
    mocker: MockerFixture,
    client: MercadoPagoAPIClient,
    create_order_input: MPCreateOrderIn,
):
    """Given a valid order creation request
    When the Mercado Pago API returns 404 status
    Then an MPNotFoundError should be raised
    """
    await _test_http_status_404_error(
        mocker, client.create_dynamic_qr_order, {"order_data": create_order_input}
    )


async def test_should_raise_mp_client_error_when_create_dynamic_qr_order_has_http_error(
    mocker: MockerFixture,
    client: MercadoPagoAPIClient,
    create_order_input: MPCreateOrderIn,
):
    """Given a valid order creation request
    When the Mercado Pago API has a generic HTTP error
    Then an MPClientError should be raised
    """
    await _test_http_generic_error(
        mocker, client.create_dynamic_qr_order, {"order_data": create_order_input}
    )


async def test_should_find_order_by_id_when_api_responds_successfully(
    mocker: MockerFixture,
    client: MercadoPagoAPIClient,
):
    """Given a valid order ID
    When the Mercado Pago API responds successfully
    Then the order should be found and returned
    """

    # Given
    order_id = 123456
    expected_order = MPOrder(
        id=order_id,
        status=MPOrderStatus.CLOSED,
        external_reference="A048",
    )

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_order.model_dump()
    mock_response.raise_for_status.return_value = None

    client.http_client.request = mocker.AsyncMock(return_value=mock_response)

    # When
    result = await client.find_order_by_id(order_id=order_id)

    # Then
    assert result.id == order_id
    assert result.status == MPOrderStatus.CLOSED
    assert result.external_reference == "A048"
    client.http_client.request.assert_awaited_once_with(
        "GET",
        f"https://api.mercadopago.com/merchant_orders/{order_id}",
        headers={"Authorization": "Bearer test-access-token"},
    )


async def test_should_raise_mp_not_found_error_when_find_order_by_id_returns_404(
    mocker: MockerFixture,
    client: MercadoPagoAPIClient,
):
    """Given a valid order ID
    When the Mercado Pago API returns 404 status
    Then an MPNotFoundError should be raised
    """
    await _test_http_status_404_error(
        mocker, client.find_order_by_id, {"order_id": 999999}
    )


async def test_should_raise_mp_client_error_when_find_order_by_id_has_http_error(
    mocker: MockerFixture,
    client: MercadoPagoAPIClient,
):
    """Given a valid order ID
    When the Mercado Pago API has a generic HTTP error
    Then an MPClientError should be raised
    """
    await _test_http_generic_error(
        mocker,
        client.find_order_by_id,
        {"order_id": 123456},
        "Network connection failed",
    )


async def test_should_find_payment_by_id_when_api_responds_successfully(
    mocker: MockerFixture,
    client: MercadoPagoAPIClient,
):
    """Given a valid payment ID
    When the Mercado Pago API responds successfully
    Then the payment should be found and returned
    """

    # Given
    payment_id = "PAY123456"
    expected_payment = MPPayment(
        order=MPPaymentOrder(id="123456"),
        status="approved",
    )

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = expected_payment.model_dump()
    mock_response.raise_for_status.return_value = None

    client.http_client.request = mocker.AsyncMock(return_value=mock_response)

    # When
    result = await client.find_payment_by_id(payment_id=payment_id)

    # Then
    assert result.order.id == "123456"
    assert result.status == "approved"
    client.http_client.request.assert_awaited_once_with(
        "GET",
        f"https://api.mercadopago.com/v1/payments/{payment_id}",
        headers={"Authorization": "Bearer test-access-token"},
    )


async def test_should_raise_mp_not_found_error_when_find_payment_by_id_returns_404(
    mocker: MockerFixture,
    client: MercadoPagoAPIClient,
):
    """Given a valid payment ID
    When the Mercado Pago API returns 404 status
    Then an MPNotFoundError should be raised
    """
    await _test_http_status_404_error(
        mocker, client.find_payment_by_id, {"payment_id": "INVALID_PAY"}
    )


async def test_should_raise_mp_client_error_when_find_payment_by_id_has_http_error(
    mocker: MockerFixture,
    client: MercadoPagoAPIClient,
):
    """Given a valid payment ID
    When the Mercado Pago API has a generic HTTP error
    Then an MPClientError should be raised
    """
    await _test_http_generic_error(
        mocker,
        client.find_payment_by_id,
        {"payment_id": "PAY123456"},
        "Request timeout",
    )


# Helper functions for error testing
async def _test_http_status_404_error(
    mocker: MockerFixture,
    client_method,
    method_args: dict,
    expected_exception=MPNotFoundError,
    expected_message="Mercado Pago resource not found.",
):
    """Generic helper to test 404 HTTP status errors"""
    mock_response = mocker.Mock()
    mock_response.status_code = 404
    mock_request = mocker.Mock(spec=Request)

    http_status_error = HTTPStatusError(
        message="Not Found",
        request=mock_request,
        response=mock_response,
    )

    client_method.__self__.http_client.request = mocker.AsyncMock(
        side_effect=http_status_error
    )

    with pytest.raises(expected_exception) as exc_info:
        await client_method(**method_args)

    assert str(exc_info.value) == expected_message


async def _test_http_generic_error(
    mocker: MockerFixture,
    client_method,
    method_args: dict,
    error_message: str = "Connection timeout",
    expected_exception=MPClientError,
):
    """Generic helper to test generic HTTP errors"""
    http_error = HTTPError(error_message)
    client_method.__self__.http_client.request = mocker.AsyncMock(
        side_effect=http_error
    )

    with pytest.raises(expected_exception) as exc_info:
        await client_method(**method_args)

    assert error_message in str(exc_info.value)
