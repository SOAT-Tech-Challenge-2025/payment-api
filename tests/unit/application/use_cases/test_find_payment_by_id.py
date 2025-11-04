# pylint: disable=W0621

"""Unit tests for FindPaymentByIdUseCase"""

import pytest
from pytest_mock import MockerFixture

from payment_api.application.commands import FindPaymentByIdCommand
from payment_api.application.use_cases import FindPaymentByIdUseCase
from payment_api.domain.entities import PaymentOut
from payment_api.domain.exceptions import NotFound
from payment_api.domain.value_objects import PaymentStatus


@pytest.fixture
def use_case(mocker: MockerFixture) -> FindPaymentByIdUseCase:
    """Fixture to create an instance of FindPaymentByIdUseCase with mocked
    dependencies
    """
    payment_repository = mocker.Mock()
    return FindPaymentByIdUseCase(payment_repository=payment_repository)


async def test_should_find_payment_by_id_when_it_exists(
    mocker: MockerFixture,
    use_case: FindPaymentByIdUseCase,
):
    """Given a valid command to find a payment by ID
    When executing the use case and the payment exists
    Then the payment should be returned
    """

    # Given
    command = FindPaymentByIdCommand(payment_id="A048")
    expected_payment = PaymentOut(
        id="A048",
        external_id="A048",
        payment_status=PaymentStatus.CLOSED,
        total_order_value=100.0,
        qr_code="sample-qr-code",
        expiration="2024-12-31T23:59:59",
        created_at="2024-01-01T12:00:00Z",
        timestamp="2024-01-02T12:00:00Z",
    )
    use_case.payment_repository.find_by_id = mocker.AsyncMock(
        return_value=expected_payment
    )

    # When
    result = await use_case.execute(command)

    # Then
    use_case.payment_repository.find_by_id.assert_awaited_once_with(payment_id="A048")
    assert result == expected_payment


async def test_should_not_find_payment_by_id_when_it_does_not_exist(
    mocker: MockerFixture,
    use_case: FindPaymentByIdUseCase,
):
    """Given a valid command to find a payment by ID
    When executing the use case and the payment does not exist
    Then a NotFound exception should be raised
    """

    # Given
    command = FindPaymentByIdCommand(payment_id="A050")
    use_case.payment_repository.find_by_id = mocker.AsyncMock(side_effect=NotFound())

    # When / Then
    with pytest.raises(NotFound) as exc_info:
        await use_case.execute(command)

    use_case.payment_repository.find_by_id.assert_awaited_once_with(payment_id="A050")

    assert str(exc_info.value) == "Not found"
