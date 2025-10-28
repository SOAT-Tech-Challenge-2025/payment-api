"""Mercado Pago Payment Gateway adapter implementation"""

from datetime import datetime, timedelta, timezone

from payment_api.domain.entities import PaymentIn, Product
from payment_api.domain.exceptions import PaymentCreationError
from payment_api.domain.ports import PaymentGateway
from payment_api.infrastructure.config import Settings
from payment_api.infrastructure.mercado_pago import (
    MercadoPagoAPIClient,
    MPClientError,
    MPCreateOrderIn,
    MPItem,
)


class MPPaymentGateway(PaymentGateway):
    """Mercado Pago Payment Gateway adapter implementation."""

    def __init__(self, settings: Settings, mp_client: MercadoPagoAPIClient):
        self.callback_url = settings.MERCADO_PAGO_CALLBACK_URL
        self.mp_client = mp_client

    async def create(self, payment: PaymentIn, products: list[Product]) -> PaymentIn:
        mp_items = [
            MPItem(
                title=product.name,
                category=product.category,
                quantity=product.quantity,
                unit_measure="unit",
                unit_price=product.unit_price,
                total_amount=product.get_total_value(),
            )
            for product in products
        ]

        description = f"Order #{payment.id}"
        expiration = datetime.now(tz=timezone.utc) + timedelta(minutes=10)
        order_request = MPCreateOrderIn(
            external_reference=payment.id,
            total_amount=payment.total_order_value,
            title=description,
            description=description,
            expiration_date=expiration.isoformat(timespec="milliseconds"),
            items=mp_items,
            notification_url=self.callback_url,
        )

        try:
            mp_order_response = await self.mp_client.create_dynamic_qr_order(
                order_data=order_request
            )

            payment.qr_code = mp_order_response.qr_data
            return payment
        except MPClientError as exc:
            raise PaymentCreationError(
                f"Failed to create payment in Mercado Pago: {str(exc)}"
            ) from exc
