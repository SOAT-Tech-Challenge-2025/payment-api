"""Module defining the CreatePaymentCommand for creating payments"""

from pydantic import BaseModel, Field

from payment_api.domain.entities import Product


class CreatePaymentCommand(BaseModel):
    """Command to create a new payment"""

    id: str = Field(..., description="Unique identifier for the payment")
    total_order_value: float = Field(..., description="Total value of the order")
    products: list[Product] = Field(
        ..., description="List of products associated with the payment"
    )
