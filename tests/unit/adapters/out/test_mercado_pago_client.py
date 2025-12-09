# pylint: disable=W0621

"""Unit tests for MercadoPagoClient"""

import pytest
from pytest_mock import MockerFixture

from payment_api.adapters.out import MercadoPagoClient
from payment_api.domain.ports import (
    MPClientError,
    MPOrder,
    MPOrderStatus,
    MPPayment,
)
from payment_api.infrastructure.mercado_pago import (
    MercadoPagoAPIClient,
)
from payment_api.infrastructure.mercado_pago import MPClientError as MPClientInfraError
from payment_api.infrastructure.mercado_pago.schemas import MPOrder as MPOrderInfra
from payment_api.infrastructure.mercado_pago.schemas import (
    MPOrderStatus as MPOrderStatusInfra,
)
from payment_api.infrastructure.mercado_pago.schemas import MPPayment as MPPaymentInfra
from payment_api.infrastructure.mercado_pago.schemas import (
    MPPaymentOrder as MPPaymentOrderInfra,
)


@pytest.fixture
def api_client(mocker: MockerFixture) -> MercadoPagoAPIClient:
    """Fixture to create a mock MercadoPagoAPIClient"""
    return mocker.Mock(spec=MercadoPagoAPIClient)


@pytest.fixture
def client(api_client: MercadoPagoAPIClient) -> MercadoPagoClient:
    """Fixture to create MercadoPagoClient with mocked dependencies"""
    return MercadoPagoClient(api_client=api_client)


async def test_should_find_order_by_id_when_api_client_responds_successfully(
    mocker: MockerFixture,
    client: MercadoPagoClient,
    api_client: MercadoPagoAPIClient,
):
    """Given a valid order ID
    When the API client responds successfully
    Then the order should be found and converted to application layer schema
    """

    # Given
    order_id = 123456
    infra_order = MPOrderInfra(
        id=order_id,
        status=MPOrderStatusInfra.CLOSED,
        external_reference="A048",
    )

    api_client.find_order_by_id = mocker.AsyncMock(return_value=infra_order)

    # When
    result = await client.find_order_by_id(order_id=order_id)

    # Then
    assert isinstance(result, MPOrder)
    assert result.id == order_id
    assert result.status == MPOrderStatus.CLOSED
    assert result.external_reference == "A048"
    api_client.find_order_by_id.assert_awaited_once_with(order_id=order_id)


async def test_should_raise_mp_client_error_when_find_order_by_id_fails(
    mocker: MockerFixture,
    client: MercadoPagoClient,
    api_client: MercadoPagoAPIClient,
):
    """Given a valid order ID
    When the API client raises an MPClientError
    Then an application layer MPClientError should be raised
    """

    # Given
    order_id = 999999
    error_message = "Mercado Pago API error occurred"
    api_client.find_order_by_id = mocker.AsyncMock(
        side_effect=MPClientInfraError(error_message)
    )

    # When / Then
    with pytest.raises(MPClientError) as exc_info:
        await client.find_order_by_id(order_id=order_id)

    assert str(exc_info.value) == error_message
    api_client.find_order_by_id.assert_awaited_once_with(order_id=order_id)


async def test_should_find_payment_by_id_when_api_client_responds_successfully(
    mocker: MockerFixture,
    client: MercadoPagoClient,
    api_client: MercadoPagoAPIClient,
):
    """Given a valid payment ID
    When the API client responds successfully
    Then the payment should be found and converted to application layer schema
    """

    # Given
    payment_id = "PAY123456"
    infra_payment = MPPaymentInfra(
        order=MPPaymentOrderInfra(id="123456"),
        status="approved",
    )

    api_client.find_payment_by_id = mocker.AsyncMock(return_value=infra_payment)

    # When
    result = await client.find_payment_by_id(payment_id=payment_id)

    # Then
    assert isinstance(result, MPPayment)
    assert result.order.id == "123456"
    assert result.status == "approved"
    api_client.find_payment_by_id.assert_awaited_once_with(payment_id=payment_id)


async def test_should_raise_mp_client_error_when_find_payment_by_id_fails(
    mocker: MockerFixture,
    client: MercadoPagoClient,
    api_client: MercadoPagoAPIClient,
):
    """Given a valid payment ID
    When the API client raises an MPClientError
    Then an application layer MPClientError should be raised
    """

    # Given
    payment_id = "INVALID_PAY"
    error_message = "Payment not found in Mercado Pago"
    api_client.find_payment_by_id = mocker.AsyncMock(
        side_effect=MPClientInfraError(error_message)
    )

    # When / Then
    with pytest.raises(MPClientError) as exc_info:
        await client.find_payment_by_id(payment_id=payment_id)

    assert str(exc_info.value) == error_message
    api_client.find_payment_by_id.assert_awaited_once_with(payment_id=payment_id)
