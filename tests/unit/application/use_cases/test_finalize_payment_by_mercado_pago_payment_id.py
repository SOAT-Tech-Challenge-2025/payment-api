# pylint: disable=W0621

"""Unit tests for FinalizePaymentByMercadoPagoPaymentIdUseCase"""

import pytest
from freezegun import freeze_time
from pytest_mock import MockerFixture

from payment_api.application.commands import (
    FinalizePaymentByMercadoPagoPaymentIdCommand,
)
from payment_api.application.use_cases import (
    FinalizePaymentByMercadoPagoPaymentIdUseCase,
)
from payment_api.domain.entities import PaymentIn, PaymentOut
from payment_api.domain.ports import (
    MPOrder,
    MPOrderStatus,
    MPPayment,
    MPPaymentOrder,
)
from payment_api.domain.value_objects import PaymentStatus


@pytest.fixture
def use_case(mocker: MockerFixture) -> FinalizePaymentByMercadoPagoPaymentIdUseCase:
    """Fixture to create an instance of FinalizePaymentByMercadoPagoPaymentIdUseCase
    with mocked dependencies
    """
    payment_repository = mocker.Mock()
    mercado_pago_client = mocker.Mock()
    payment_closed_publisher = mocker.Mock()
    return FinalizePaymentByMercadoPagoPaymentIdUseCase(
        payment_repository=payment_repository,
        mercado_pago_client=mercado_pago_client,
        payment_closed_publisher=payment_closed_publisher,
    )


@freeze_time("2024-01-01T12:01:00Z")
async def test_should_finalize_payment_by_mercado_pago_payment_id_when_payment_exists(
    mocker: MockerFixture,
    use_case: FinalizePaymentByMercadoPagoPaymentIdUseCase,
):
    """Given a valid command to finalize a payment by Mercado Pago payment ID
    When executing the use case and the payment exists
    Then the payment should be finalized and returned
    """

    # Given
    command = FinalizePaymentByMercadoPagoPaymentIdCommand(
        payment_id="A048",
    )

    mp_order_mock = MPOrder(
        id=123, status=MPOrderStatus.CLOSED, external_reference="A048"
    )

    mp_payment_mock = MPPayment(
        order=MPPaymentOrder(
            id="123",
        ),
        status="approved",
    )

    payment_mock = PaymentOut(
        id="A048",
        external_id="empty-A048",
        payment_status=PaymentStatus.OPENED,
        total_order_value=100.0,
        qr_code="qr-sample",
        expiration="2024-01-01T12:15:00",
        created_at="2024-01-01T12:00:00Z",
        timestamp="2024-01-01T12:00:00Z",
    )

    payment_save_mock = PaymentIn.model_validate(
        {
            **payment_mock.model_dump(),
            "payment_status": PaymentStatus.CLOSED,
            "external_id": "123",
        }
    )

    use_case.mercado_pago_client.find_payment_by_id = mocker.AsyncMock(
        return_value=mp_payment_mock
    )

    use_case.mercado_pago_client.find_order_by_id = mocker.AsyncMock(
        return_value=mp_order_mock
    )

    use_case.payment_repository.exists_by_external_id = mocker.AsyncMock(
        return_value=False
    )

    use_case.payment_repository.find_by_id = mocker.AsyncMock(return_value=payment_mock)
    use_case.payment_repository.save = mocker.AsyncMock(return_value=payment_save_mock)
    use_case.payment_closed_publisher.publish = mocker.AsyncMock()

    # When
    finalized_payment = await use_case.execute(command=command)

    # Then
    assert finalized_payment.payment_status == PaymentStatus.CLOSED
    assert finalized_payment.external_id == "123"
    assert finalized_payment.id == "A048"

    use_case.mercado_pago_client.find_payment_by_id.assert_awaited_once_with(
        payment_id=command.payment_id
    )

    use_case.mercado_pago_client.find_order_by_id.assert_awaited_once_with(
        order_id=mp_order_mock.id
    )

    use_case.payment_repository.exists_by_external_id.assert_awaited_once_with(
        external_id="123"
    )

    use_case.payment_repository.find_by_id.assert_awaited_once_with(payment_id="A048")
    use_case.payment_repository.save.assert_awaited_once_with(payment=payment_save_mock)
    use_case.payment_closed_publisher.publish.assert_awaited_once()


async def test_should_not_finalize_payment_when_external_id_already_exists(
    mocker: MockerFixture,
    use_case: FinalizePaymentByMercadoPagoPaymentIdUseCase,
):
    """Given a valid command to finalize a payment by Mercado Pago payment ID
    When executing the use case and the payment with external ID already exists
    Then a ValueError should be raised
    """

    # Given
    command = FinalizePaymentByMercadoPagoPaymentIdCommand(
        payment_id="A048",
    )

    mp_order_mock = MPOrder(
        id=123, status=MPOrderStatus.CLOSED, external_reference="A048"
    )

    mp_payment_mock = MPPayment(
        order=MPPaymentOrder(
            id="123",
        ),
        status="approved",
    )

    use_case.mercado_pago_client.find_payment_by_id = mocker.AsyncMock(
        return_value=mp_payment_mock
    )

    use_case.mercado_pago_client.find_order_by_id = mocker.AsyncMock(
        return_value=mp_order_mock
    )

    use_case.payment_repository.exists_by_external_id = mocker.AsyncMock(
        return_value=True
    )

    # When / Then
    with pytest.raises(ValueError) as exc_info:
        await use_case.execute(command=command)

    assert str(exc_info.value) == "Payment with external ID 123 already exists"
    use_case.mercado_pago_client.find_payment_by_id.assert_awaited_once_with(
        payment_id=command.payment_id
    )

    use_case.mercado_pago_client.find_order_by_id.assert_awaited_once_with(
        order_id=mp_order_mock.id
    )

    use_case.payment_repository.exists_by_external_id.assert_awaited_once_with(
        external_id="123"
    )
