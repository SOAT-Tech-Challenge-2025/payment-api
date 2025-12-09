# pylint: disable=W0621

"""Unit tests for QRCodeRenderer"""

import pytest
from pytest_mock import MockerFixture
from qrcode.image.pil import PilImage

from payment_api.adapters.out import QRCodeRenderer


@pytest.fixture
def renderer() -> QRCodeRenderer:
    """Fixture to create QRCodeRenderer instance"""
    return QRCodeRenderer()


def test_should_render_qr_code_when_valid_data_is_provided(
    mocker: MockerFixture,
    renderer: QRCodeRenderer,
):
    """Given a valid data string
    When rendering a QR code
    Then the QR code should be generated and returned as bytes
    """

    # Given
    test_data = "https://example.com/payment/A048"
    expected_qr_bytes = b"fake-qr-code-bytes"

    # Mock the QRCode and related components
    mock_qr_code = mocker.Mock()
    mock_image = mocker.Mock()
    mock_buffer = mocker.Mock()
    mock_buffer.getvalue.return_value = expected_qr_bytes

    # Mock the QRCode constructor and methods
    mock_qr_code_class = mocker.patch(
        "payment_api.adapters.out.qr_code_renderer.QRCode"
    )

    mock_qr_code_class.return_value = mock_qr_code
    mock_qr_code.make_image.return_value = mock_image

    # Mock BytesIO
    mock_bytes_io_class = mocker.patch(
        "payment_api.adapters.out.qr_code_renderer.BytesIO"
    )

    mock_bytes_io_class.return_value = mock_buffer

    # When
    result = renderer.render(data=test_data)

    # Then
    assert result == expected_qr_bytes
    assert isinstance(result, bytes)

    # Verify the QR code creation flow
    mock_qr_code_class.assert_called_once_with(image_factory=PilImage)
    mock_qr_code.add_data.assert_called_once_with(test_data)
    mock_qr_code.make_image.assert_called_once()
    mock_image.save.assert_called_once_with(mock_buffer, format="PNG")
    mock_buffer.getvalue.assert_called_once()
