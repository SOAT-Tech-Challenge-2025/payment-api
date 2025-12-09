"""Abstract client interface and related schemas for interacting with Mercado Pago API
in the application layer."""

from abc import ABC, abstractmethod
from enum import Enum, unique

from pydantic import BaseModel, Field


@unique
class MPOrderStatus(str, Enum):
    """Enumeration of possible order statuses in Mercado Pago."""

    OPENED = "opened"
    CLOSED = "closed"
    EXPIRED = "expired"


class MPOrder(BaseModel):
    """Schema representing an order in Mercado Pago."""

    id: int = Field(..., description="Unique identifier for the order.")
    status: MPOrderStatus = Field(..., description="Status of the order.")
    external_reference: str = Field(
        ..., description="External reference for the order."
    )


class MPPaymentOrder(BaseModel):
    """Schema representing the order associated with a payment in Mercado Pago."""

    id: str = Field(..., description="Unique identifier for the order.")


class MPPayment(BaseModel):
    """Schema representing a payment in Mercado Pago."""

    order: MPPaymentOrder = Field(..., description="Order associated with the payment.")
    status: str = Field(..., description="Status of the payment.")


class MPClientError(Exception):
    """Custom exception for Mercado Pago client errors."""


class MercadoPagoClient(ABC):
    """Abstract client interface for interacting with Mercado Pago API in the
    application layer."""

    @abstractmethod
    async def find_order_by_id(self, order_id: int) -> MPOrder:
        """Fetch an order from Mercado Pago by its ID.

        :param order_id: The unique identifier of the order in Mercado Pago.
        :type order_id: int
        :return: An instance of MPOrder representing the fetched order.
        :rtype: MPOrder
        :raises MPClientError: if there is an error communicating with Mercado Pago
        """

    @abstractmethod
    async def find_payment_by_id(self, payment_id: str) -> MPPayment:
        """Fetch a payment from Mercado Pago by its ID.

        :param payment_id: The unique identifier of the payment in Mercado Pago.
        :type payment_id: str
        :return: An instance of MPPayment representing the fetched payment.
        :rtype: MPPayment
        :raises MPClientError: if there is an error communicating with Mercado Pago
        """
