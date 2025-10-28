"""Concrete implementation of AbstractMercadoPagoClient using MercadoPagoAPIClient"""

from payment_api.application.use_cases.ports.mercado_pago_client import (
    AbstractMercadoPagoClient,
    MPOrder,
    MPPayment,
)
from payment_api.infrastructure.mercado_pago import MercadoPagoAPIClient


class MercadoPagoClient(AbstractMercadoPagoClient):
    """Implementation of AbstractMercadoPagoClient using MercadoPagoAPIClient"""

    def __init__(self, api_client: MercadoPagoAPIClient):
        self.api_client = api_client

    async def find_order_by_id(self, order_id: str) -> MPOrder:
        order = await self.api_client.find_order_by_id(order_id=order_id)
        return MPOrder.model_validate(order.model_dump())

    async def find_payment_by_id(self, payment_id: str) -> MPPayment:
        payment = await self.api_client.find_payment_by_id(payment_id=payment_id)
        return MPPayment.model_validate(payment.model_dump())
