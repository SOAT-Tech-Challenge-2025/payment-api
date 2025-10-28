"""Payment schema for REST API v1"""

from datetime import datetime

from pydantic import BaseModel, Field

from payment_api.domain.value_objects import PaymentStatus


class PaymentV1(BaseModel):
    """Payment schema representing a payment record"""

    id: str = Field(description="Unique identifier for the payment")
    external_id: str = Field(description="External identifier for the payment")
    payment_status: PaymentStatus = Field(description="Current status of the payment")
    total_order_value: float = Field(description="Total value of the order")
    qr_code: str = Field(description="QR code for the payment")
    expiration: datetime = Field(description="Expiration date and time of the payment")
    created_at: datetime = Field(description="Creation date and time of the payment")
    timestamp: datetime | None = Field(
        None, description="Last update date and time of the payment"
    )


class MercadoPagoWebhookDataV1(BaseModel):
    """Schema representing the data field in a MercadoPago webhook payload"""

    id: str = Field(description="The ID of the payment in MercadoPago")


class MercadoPagoWebhookV1(BaseModel):
    """Schema representing a MercadoPago webhook payload"""

    action: str = Field(description="The action performed in the webhook event")
    type: str = Field(description="The type of the webhook event")
    data: MercadoPagoWebhookDataV1 = Field(
        description="The data associated with the webhook event"
    )
