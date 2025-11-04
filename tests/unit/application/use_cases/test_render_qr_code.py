# pylint: disable=W0621

"""Unit tests for RenderQRCodeUseCase"""

import pytest
from pytest_mock import MockerFixture

from payment_api.application.commands import RenderQRCodeCommand
from payment_api.application.use_cases import RenderQRCodeUseCase
from payment_api.domain.entities import PaymentOut
from payment_api.domain.value_objects import PaymentStatus


@pytest.fixture
def use_case(mocker: MockerFixture) -> RenderQRCodeUseCase:
    """Fixture to create an instance of RenderQRCodeUseCase with mocked
    dependencies
    """
    payment_repository = mocker.Mock()
    qr_code_renderer = mocker.Mock()
    return RenderQRCodeUseCase(
        payment_repository=payment_repository, qr_code_renderer=qr_code_renderer
    )


async def test_should_render_qr_code_when_payment_has_qr_code(
    mocker: MockerFixture,
    use_case: RenderQRCodeUseCase,
):
    """Given a valid command to render a QR code
    When executing the use case and the payment has an associated QR code
    Then the QR code bytes should be returned
    """

    # Given
    command = RenderQRCodeCommand(payment_id="A048")
    payment = PaymentOut(
        id="A048",
        external_id="A048",
        payment_status=PaymentStatus.CLOSED,
        total_order_value=100.0,
        qr_code="sample-qr-code",
        expiration="2024-12-31T23:59:59",
        created_at="2024-01-01T12:00:00Z",
        timestamp="2024-01-02T12:00:00Z",
    )

    use_case.payment_repository.find_by_id = mocker.AsyncMock(return_value=payment)

    expected_qr_code_bytes = b"qr-code-bytes"
    use_case.qr_code_renderer.render = mocker.Mock(return_value=expected_qr_code_bytes)

    # When
    result = await use_case.execute(command)

    # Then
    use_case.payment_repository.find_by_id.assert_awaited_once_with(payment_id="A048")
    use_case.qr_code_renderer.render.assert_called_once_with(data="sample-qr-code")
    assert result == expected_qr_code_bytes


async def test_should_raise_value_error_when_payment_has_no_qr_code(
    mocker: MockerFixture,
    use_case: RenderQRCodeUseCase,
):
    """Given a valid command to render a QR code
    When executing the use case and the payment does not have an associated QR code
    Then a ValueError should be raised
    """

    # Given
    command = RenderQRCodeCommand(payment_id="A049")
    payment = PaymentOut(
        id="A049",
        external_id="A049",
        payment_status=PaymentStatus.CLOSED,
        total_order_value=150.0,
        qr_code=None,
        expiration="2024-12-31T23:59:59",
        created_at="2024-01-01T12:00:00Z",
        timestamp="2024-01-02T12:00:00Z",
    )

    use_case.payment_repository.find_by_id = mocker.AsyncMock(return_value=payment)

    # When / Then
    with pytest.raises(ValueError) as exc_info:
        await use_case.execute(command)

    use_case.payment_repository.find_by_id.assert_awaited_once_with(payment_id="A049")
    assert str(exc_info.value) == "Payment does not have an associated QR code."
