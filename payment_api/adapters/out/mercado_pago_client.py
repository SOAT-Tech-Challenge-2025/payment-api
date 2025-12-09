"""Concrete implementation of AbstractMercadoPagoClient using MercadoPagoAPIClient"""

from payment_api.domain.ports import MercadoPagoClient as AbstractMercadoPagoClient
from payment_api.domain.ports import MPClientError as MPClientPortError
from payment_api.domain.ports import (
    MPOrder,
    MPPayment,
)
from payment_api.infrastructure.mercado_pago import (
    MercadoPagoAPIClient,
    MPClientError,
)


class MercadoPagoClient(AbstractMercadoPagoClient):
    """Implementation of AbstractMercadoPagoClient using MercadoPagoAPIClient"""

    def __init__(self, api_client: MercadoPagoAPIClient):
        self.api_client = api_client

    async def find_order_by_id(self, order_id: int) -> MPOrder:
        try:
            order = await self.api_client.find_order_by_id(order_id=order_id)
        except MPClientError as exc:
            raise MPClientPortError(str(exc)) from exc
        return MPOrder.model_validate(order.model_dump())

    async def find_payment_by_id(self, payment_id: str) -> MPPayment:
        try:
            payment = await self.api_client.find_payment_by_id(payment_id=payment_id)
        except MPClientError as exc:
            raise MPClientPortError(str(exc)) from exc
        return MPPayment.model_validate(payment.model_dump())
