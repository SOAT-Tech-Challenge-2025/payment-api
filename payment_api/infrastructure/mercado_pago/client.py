"""Client for interacting with the Mercado Pago API."""

import logging
from typing import NoReturn, TypeVar

from httpx import AsyncClient, HTTPError, HTTPStatusError
from pydantic import BaseModel

from payment_api.infrastructure.config import MercadoPagoSettings
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

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class MercadoPagoAPIClient:
    """Client for interacting with the Mercado Pago API."""

    def __init__(self, settings: MercadoPagoSettings, http_client: AsyncClient):
        self.access_token = settings.ACCESS_TOKEN
        self.user_id = settings.USER_ID
        self.pos = settings.POS
        self.base_url = settings.URL
        self.http_client = http_client

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

        return await self._make_request(
            method="POST",
            url=url,
            json=order_data.model_dump(),
            response_model=MPCreateOrderOut,
        )

    async def find_order_by_id(self, order_id: int) -> MPOrder:
        """Find an order in Mercado Pago by its ID.

        :param order_id: The ID of the order to find.
        :type order_id: int
        :return: The found order.
        :raises MPNotFoundError: If the order is not found.
        :raises MPClientError: If there is an error with the Mercado Pago API.
        """

        url = f"{self.base_url}/merchant_orders/{order_id}"
        return await self._make_request(method="GET", url=url, response_model=MPOrder)

    async def find_payment_by_id(self, payment_id: str) -> MPPayment:
        """Find a payment in Mercado Pago by its ID.

        :param payment_id: The ID of the payment to find.
        :type payment_id: str
        :return: The found payment.
        :raises MPNotFoundError: If the payment is not found.
        :raises MPClientError: If there is an error with the Mercado Pago API.
        """

        url = f"{self.base_url}/v1/payments/{payment_id}"
        return await self._make_request(method="GET", url=url, response_model=MPPayment)

    async def _make_request(
        self,
        method: str,
        url: str,
        response_model: type[T],
        **kwargs,
    ) -> T:
        """Make an HTTP request to the Mercado Pago API."""

        err_prefix = (
            f"[{method}] {url} - Failed to make {method} request to Mercado Pago API: "
        )

        json = kwargs.get("json")
        if json:
            logger.debug("Calling %s %s with payload: %s", method, url, json)
        else:
            logger.debug("Calling url %s with method %s", url, method)

        try:
            response = await self.http_client.request(
                method, url, headers=self._get_headers(), **kwargs
            )

            logger.debug("Response %s %s -> %s", method, url, response.status_code)
            response.raise_for_status()
        except HTTPStatusError as exc:
            self._handle_http_status_error(exc, err_prefix)
        except HTTPError as exc:
            self._handle_http_error(exc, err_prefix)

        return response_model.model_validate(response.json())

    def _get_headers(self) -> dict[str, str]:
        """Generate headers for Mercado Pago API requests."""
        return {"Authorization": f"Bearer {self.access_token}"}

    def _handle_http_status_error(
        self, exc: HTTPStatusError, err_prefix: str
    ) -> NoReturn:
        """Handle HTTP errors from Mercado Pago API requests."""
        if exc.response is not None and exc.response.status_code == 404:
            raise MPNotFoundError("Mercado Pago resource not found.") from exc

        raise MPClientError(f"{err_prefix}{str(exc)}") from exc

    def _handle_http_error(self, exc: HTTPError, err_prefix: str) -> NoReturn:
        """Handle generic errors from Mercado Pago API requests."""
        raise MPClientError(f"{err_prefix}{str(exc)}") from exc
