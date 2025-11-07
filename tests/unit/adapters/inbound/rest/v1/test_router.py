# pylint: disable=W0621

"""Unit tests for Payment API v1 routes"""

from httpx import AsyncClient
from pytest_mock import MockerFixture

from payment_api.application.commands import (
    FinalizePaymentByMercadoPagoPaymentIdCommand,
    FindPaymentByIdCommand,
    RenderQRCodeCommand,
)
from payment_api.application.use_cases.ports import MPClientError
from payment_api.domain.entities import PaymentOut
from payment_api.domain.exceptions import (
    EventPublishingError,
    NotFound,
    PersistenceError,
)
from payment_api.domain.value_objects import PaymentStatus


class TestFindPaymentByIdRoute:
    """Test cases for the GET /v1/payment/{payment_id} route"""

    async def test_should_return_payment_when_payment_exists(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a valid payment ID
        When requesting the payment via GET endpoint and the payment exists
        Then the payment should be returned with status 200
        """

        # Given
        payment_id = "A048"
        expected_payment = PaymentOut(
            id=payment_id,
            external_id="MP123456",
            payment_status=PaymentStatus.CLOSED,
            total_order_value=100.0,
            qr_code="sample-qr-code",
            expiration="2024-12-31T23:59:59",
            created_at="2024-01-01T12:00:00Z",
            timestamp="2024-01-02T12:00:00Z",
        )

        payment_use_cases_mock["find_by_id"].execute = mocker.AsyncMock(
            return_value=expected_payment
        )

        # When
        response = await test_app_client.get(f"/v1/payment/{payment_id}")

        # Then
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == payment_id
        assert response_data["external_id"] == "MP123456"
        assert response_data["payment_status"] == PaymentStatus.CLOSED.value
        assert response_data["total_order_value"] == 100.0
        expected_command = FindPaymentByIdCommand(payment_id=payment_id)
        payment_use_cases_mock["find_by_id"].execute.assert_awaited_once_with(
            command=expected_command
        )

    async def test_should_return_404_when_payment_not_found(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a payment ID that does not exist
        When requesting the payment via GET endpoint
        Then a 404 error should be returned
        """

        # Given
        payment_id = "NONEXISTENT"
        payment_use_cases_mock["find_by_id"].execute = mocker.AsyncMock(
            side_effect=NotFound()
        )

        # When
        response = await test_app_client.get(f"/v1/payment/{payment_id}")

        # Then
        assert response.status_code == 404
        assert response.json()["detail"] == "Payment not found"
        expected_command = FindPaymentByIdCommand(payment_id=payment_id)
        payment_use_cases_mock["find_by_id"].execute.assert_awaited_once_with(
            command=expected_command
        )

    async def test_should_return_500_when_persistence_error_occurs(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a valid payment ID
        When requesting the payment via GET endpoint and a persistence error occurs
        Then a 500 error should be returned
        """

        # Given
        payment_id = "A048"
        payment_use_cases_mock["find_by_id"].execute = mocker.AsyncMock(
            side_effect=PersistenceError("Database connection failed")
        )

        # When
        response = await test_app_client.get(f"/v1/payment/{payment_id}")

        # Then
        assert response.status_code == 500
        assert (
            response.json()["detail"]
            == "An error occurred while processing your request"
        )

        expected_command = FindPaymentByIdCommand(payment_id=payment_id)
        payment_use_cases_mock["find_by_id"].execute.assert_awaited_once_with(
            command=expected_command
        )


class TestRenderQRCodeRoute:
    """Test cases for the GET /v1/payment/{payment_id}/qr route"""

    async def test_should_return_qr_code_when_payment_exists(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a valid payment ID
        When requesting the QR code via GET endpoint and the payment exists
        Then the QR code image should be returned with status 200
        """

        # Given
        payment_id = "A048"
        qr_code_bytes = b"fake_png_data"
        payment_use_cases_mock["render_qr_code"].execute = mocker.AsyncMock(
            return_value=qr_code_bytes
        )

        # When
        response = await test_app_client.get(f"/v1/payment/{payment_id}/qr")

        # Then
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.content == qr_code_bytes
        expected_command = RenderQRCodeCommand(payment_id=payment_id)
        payment_use_cases_mock["render_qr_code"].execute.assert_awaited_once_with(
            command=expected_command
        )

    async def test_should_return_404_when_payment_not_found_for_qr(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a payment ID that does not exist
        When requesting the QR code via GET endpoint
        Then a 404 error should be returned
        """

        # Given
        payment_id = "NONEXISTENT"
        payment_use_cases_mock["render_qr_code"].execute = mocker.AsyncMock(
            side_effect=NotFound()
        )

        # When
        response = await test_app_client.get(f"/v1/payment/{payment_id}/qr")

        # Then
        assert response.status_code == 404
        assert response.json()["detail"] == "Payment not found"
        expected_command = RenderQRCodeCommand(payment_id=payment_id)
        payment_use_cases_mock["render_qr_code"].execute.assert_awaited_once_with(
            command=expected_command
        )

    async def test_should_return_500_when_persistence_error_occurs_for_qr(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a valid payment ID
        When requesting the QR code via GET endpoint and a persistence error occurs
        Then a 500 error should be returned
        """

        # Given
        payment_id = "A048"
        payment_use_cases_mock["render_qr_code"].execute = mocker.AsyncMock(
            side_effect=PersistenceError("Database connection failed")
        )

        # When
        response = await test_app_client.get(f"/v1/payment/{payment_id}/qr")

        # Then
        assert response.status_code == 500
        assert (
            response.json()["detail"] == "An error occurred while rendering the QR code"
        )

        expected_command = RenderQRCodeCommand(payment_id=payment_id)
        payment_use_cases_mock["render_qr_code"].execute.assert_awaited_once_with(
            command=expected_command
        )

    async def test_should_return_400_when_value_error_occurs_for_qr(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a valid payment ID
        When requesting the QR code via GET endpoint and a value error occurs
        Then a 400 error should be returned
        """

        # Given
        payment_id = "A048"
        error_message = "Payment does not have an associated QR code"
        payment_use_cases_mock["render_qr_code"].execute = mocker.AsyncMock(
            side_effect=ValueError(error_message)
        )

        # When
        response = await test_app_client.get(f"/v1/payment/{payment_id}/qr")

        # Then
        assert response.status_code == 400
        assert response.json()["detail"] == error_message
        expected_command = RenderQRCodeCommand(payment_id=payment_id)
        payment_use_cases_mock["render_qr_code"].execute.assert_awaited_once_with(
            command=expected_command
        )


class TestMercadoPagoWebhookRoute:
    """Test cases for the POST /v1/payment/notifications/mercado-pago route"""

    async def test_should_process_payment_created_webhook_successfully(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a valid MercadoPago webhook payload for payment.created
        When posting to the webhook endpoint and processing succeeds
        Then the finalized payment should be returned with status 200
        """

        # Given
        webhook_payload = {
            "action": "payment.created",
            "type": "payment",
            "data": {"id": "MP123456"},
        }

        finalized_payment = PaymentOut(
            id="A048",
            external_id="MP123456",
            payment_status=PaymentStatus.CLOSED,
            total_order_value=100.0,
            qr_code="sample-qr-code",
            expiration="2024-12-31T23:59:59",
            created_at="2024-01-01T12:00:00Z",
            timestamp="2024-01-02T12:00:00Z",
        )

        payment_use_cases_mock["finalize_by_mercado_pago_payment_id"].execute = (
            mocker.AsyncMock(return_value=finalized_payment)
        )

        # When
        response = await test_app_client.post(
            "/v1/payment/notifications/mercado-pago", json=webhook_payload
        )

        # Then
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == "A048"
        assert response_data["external_id"] == "MP123456"
        assert response_data["payment_status"] == PaymentStatus.CLOSED.value
        expected_command = FinalizePaymentByMercadoPagoPaymentIdCommand(
            payment_id="MP123456"
        )

        payment_use_cases_mock[
            "finalize_by_mercado_pago_payment_id"
        ].execute.assert_awaited_once_with(command=expected_command)

    async def test_should_discard_webhook_with_invalid_json(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
    ):
        """Given an invalid JSON payload
        When posting to the webhook endpoint
        Then a 204 response should be returned (webhook discarded)
        """

        # Given
        invalid_payload = "invalid json"

        # When
        response = await test_app_client.post(
            "/v1/payment/notifications/mercado-pago",
            content=invalid_payload,
            headers={"content-type": "application/json"},
        )

        # Then
        assert response.status_code == 204
        payment_use_cases_mock[
            "finalize_by_mercado_pago_payment_id"
        ].execute.assert_not_called()

    async def test_should_discard_webhook_with_wrong_action(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
    ):
        """Given a MercadoPago webhook with wrong action
        When posting to the webhook endpoint
        Then a 204 response should be returned (webhook discarded)
        """

        # Given
        webhook_payload = {
            "action": "payment.updated",
            "type": "payment",
            "data": {"id": "MP123456"},
        }

        # When
        response = await test_app_client.post(
            "/v1/payment/notifications/mercado-pago", json=webhook_payload
        )

        # Then
        assert response.status_code == 204
        payment_use_cases_mock[
            "finalize_by_mercado_pago_payment_id"
        ].execute.assert_not_called()

    async def test_should_discard_webhook_with_wrong_type(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
    ):
        """Given a MercadoPago webhook with wrong type
        When posting to the webhook endpoint
        Then a 204 response should be returned (webhook discarded)
        """

        # Given
        webhook_payload = {
            "action": "payment.created",
            "type": "order",
            "data": {"id": "MP123456"},
        }

        # When
        response = await test_app_client.post(
            "/v1/payment/notifications/mercado-pago", json=webhook_payload
        )

        # Then
        assert response.status_code == 204
        payment_use_cases_mock[
            "finalize_by_mercado_pago_payment_id"
        ].execute.assert_not_called()

    async def test_should_return_404_when_payment_not_found_in_webhook(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a valid MercadoPago webhook payload
        When posting to the webhook endpoint and the payment is not found
        Then a 404 error should be returned
        """

        # Given
        webhook_payload = {
            "action": "payment.created",
            "type": "payment",
            "data": {"id": "NONEXISTENT"},
        }

        payment_use_cases_mock["finalize_by_mercado_pago_payment_id"].execute = (
            mocker.AsyncMock(side_effect=NotFound())
        )

        # When
        response = await test_app_client.post(
            "/v1/payment/notifications/mercado-pago", json=webhook_payload
        )

        # Then
        assert response.status_code == 404
        assert response.json()["detail"] == "Payment not found"
        expected_command = FinalizePaymentByMercadoPagoPaymentIdCommand(
            payment_id="NONEXISTENT"
        )

        payment_use_cases_mock[
            "finalize_by_mercado_pago_payment_id"
        ].execute.assert_awaited_once_with(command=expected_command)

    async def test_should_return_500_when_persistence_error_occurs_in_webhook(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a valid MercadoPago webhook payload
        When posting to the webhook endpoint and a persistence error occurs
        Then a 500 error should be returned
        """

        # Given
        webhook_payload = {
            "action": "payment.created",
            "type": "payment",
            "data": {"id": "MP123456"},
        }
        payment_use_cases_mock["finalize_by_mercado_pago_payment_id"].execute = (
            mocker.AsyncMock(side_effect=PersistenceError("Database connection failed"))
        )

        # When
        response = await test_app_client.post(
            "/v1/payment/notifications/mercado-pago", json=webhook_payload
        )

        # Then
        assert response.status_code == 500
        assert (
            response.json()["detail"]
            == "An error occurred while processing the webhook"
        )

        expected_command = FinalizePaymentByMercadoPagoPaymentIdCommand(
            payment_id="MP123456"
        )

        payment_use_cases_mock[
            "finalize_by_mercado_pago_payment_id"
        ].execute.assert_awaited_once_with(command=expected_command)

    async def test_should_return_502_when_mp_client_error_occurs_in_webhook(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a valid MercadoPago webhook payload
        When posting to the webhook endpoint and a MercadoPago client error occurs
        Then a 502 error should be returned
        """

        # Given
        webhook_payload = {
            "action": "payment.created",
            "type": "payment",
            "data": {"id": "MP123456"},
        }

        payment_use_cases_mock["finalize_by_mercado_pago_payment_id"].execute = (
            mocker.AsyncMock(side_effect=MPClientError("MercadoPago API error"))
        )

        # When
        response = await test_app_client.post(
            "/v1/payment/notifications/mercado-pago", json=webhook_payload
        )

        # Then
        assert response.status_code == 502
        assert response.json()["detail"] == "Error communicating with MercadoPago"
        expected_command = FinalizePaymentByMercadoPagoPaymentIdCommand(
            payment_id="MP123456"
        )

        payment_use_cases_mock[
            "finalize_by_mercado_pago_payment_id"
        ].execute.assert_awaited_once_with(command=expected_command)

    async def test_should_return_204_when_event_publishing_error_occurs_in_webhook(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a valid MercadoPago webhook payload
        When posting to the webhook endpoint and an event publishing error occurs
        Then a 204 response should be returned to avoid retries
        """

        # Given
        webhook_payload = {
            "action": "payment.created",
            "type": "payment",
            "data": {"id": "MP123456"},
        }
        payment_use_cases_mock["finalize_by_mercado_pago_payment_id"].execute = (
            mocker.AsyncMock(
                side_effect=EventPublishingError("Failed to publish event")
            )
        )

        # When
        response = await test_app_client.post(
            "/v1/payment/notifications/mercado-pago", json=webhook_payload
        )

        # Then
        assert response.status_code == 204
        expected_command = FinalizePaymentByMercadoPagoPaymentIdCommand(
            payment_id="MP123456"
        )

        payment_use_cases_mock[
            "finalize_by_mercado_pago_payment_id"
        ].execute.assert_awaited_once_with(command=expected_command)

    async def test_should_return_400_when_value_error_occurs_in_webhook(
        self,
        test_app_client: AsyncClient,
        payment_use_cases_mock: dict,
        mocker: MockerFixture,
    ):
        """Given a valid MercadoPago webhook payload
        When posting to the webhook endpoint and a value error occurs
        Then a 400 error should be returned
        """

        # Given
        webhook_payload = {
            "action": "payment.created",
            "type": "payment",
            "data": {"id": "MP123456"},
        }

        error_message = "Payment with external ID MP123456 already exists"
        payment_use_cases_mock["finalize_by_mercado_pago_payment_id"].execute = (
            mocker.AsyncMock(side_effect=ValueError(error_message))
        )

        # When
        response = await test_app_client.post(
            "/v1/payment/notifications/mercado-pago", json=webhook_payload
        )

        # Then
        assert response.status_code == 400
        expected_command = FinalizePaymentByMercadoPagoPaymentIdCommand(
            payment_id="MP123456"
        )

        payment_use_cases_mock[
            "finalize_by_mercado_pago_payment_id"
        ].execute.assert_awaited_once_with(command=expected_command)
