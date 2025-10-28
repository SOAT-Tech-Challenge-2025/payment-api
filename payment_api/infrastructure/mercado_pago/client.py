"""Client for interacting with the Mercado Pago API."""

from typing import NoReturn

from httpx import AsyncClient, HTTPError, HTTPStatusError

from payment_api.infrastructure.config import Settings
from payment_api.infrastructure.mercado_pago.exceptions import (
    MPClientError,
    MPNotFoundError,
)
from payment_api.infrastructure.mercado_pago.schemas import (
    MPCreateOrderIn,
    MPCreateOrderOut,
    MPOrder,
    MPPayment,
)


class MercadoPagoAPIClient:
    """Client for interacting with the Mercado Pago API."""

    def __init__(self, settings: Settings, http_client: AsyncClient):
        self.access_token = settings.MERCADO_PAGO_ACCESS_TOKEN
        self.user_id = settings.MERCADO_PAGO_USER_ID
        self.pos = settings.MERCADO_PAGO_POS
        self.callback_url = settings.MERCADO_PAGO_CALLBACK_URL
        self.http_client = http_client
        self.base_url = "https://api.mercadopago.com"

    async def create_dynamic_qr_order(
        self, order_data: MPCreateOrderIn
    ) -> MPCreateOrderOut:
        """Create a dynamic QR code order in Mercado Pago.

        :param order_data: Data required to create the order.
        :return: Response containing the QR code data.
        :raises MPClientError: If there is an error with the Mercado Pago API.
        """

        url = (
            f"{self.base_url}/instore/orders/qr/seller/collectors/{self.user_id}"
            f"/pos/{self.pos}/qrs"
        )

        headers = {**self._get_headers(), "Content-Type": "application/json"}
        request = order_data.model_dump()
        try:
            response = await self.http_client.post(url, json=request, headers=headers)
            response.raise_for_status()
        except HTTPStatusError as exc:
            self._handle_http_status_error(exc)
        except HTTPError as exc:
            self._handle_http_error(exc)

        return MPCreateOrderOut(**response.json())

    async def find_order_by_id(self, order_id: str) -> MPOrder:
        """Find an order in Mercado Pago by its ID.

        :param order_id: The ID of the order to find.
        :type order_id: str
        :return: The found order.
        :raises MPNotFoundError: If the order is not found.
        :raises MPClientError: If there is an error with the Mercado Pago API.
        """

        url = f"{self.base_url}/merchant_orders/{order_id}"
        try:
            response = await self.http_client.get(url, headers=self._get_headers())
            response.raise_for_status()
        except HTTPStatusError as exc:
            self._handle_http_status_error(exc)
        except HTTPError as exc:
            self._handle_http_error(exc)

        return MPOrder(**response.json())

    async def find_payment_by_id(self, payment_id: str) -> MPPayment:
        """Find a payment in Mercado Pago by its ID.

        :param payment_id: The ID of the payment to find.
        :type payment_id: str
        :return: The found payment.
        :raises MPNotFoundError: If the payment is not found.
        :raises MPClientError: If there is an error with the Mercado Pago API.
        """

        url = f"{self.base_url}/v1/payments/{payment_id}"
        try:
            response = await self.http_client.get(url, headers=self._get_headers())
            response.raise_for_status()
        except HTTPStatusError as exc:
            self._handle_http_status_error(exc)
        except HTTPError as exc:
            self._handle_http_error(exc)

        return MPPayment(**response.json())

    def _get_headers(self) -> dict[str, str]:
        """Generate headers for Mercado Pago API requests."""
        return {"Authorization": f"Bearer {self.access_token}"}

    def _handle_http_status_error(self, exc: HTTPStatusError) -> NoReturn:
        """Handle HTTP errors from Mercado Pago API requests."""
        if exc.response is not None and exc.response.status_code == 404:
            raise MPNotFoundError("Mercado Pago resource not found.") from exc

        raise MPClientError(f"Mercado Pago API error: {str(exc)}") from exc

    def _handle_http_error(self, exc: HTTPError) -> NoReturn:
        """Handle generic errors from Mercado Pago API requests."""
        raise MPClientError(f"Mercado Pago API error: {str(exc)}") from exc
