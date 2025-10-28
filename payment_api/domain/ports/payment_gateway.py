"""Payment gateway interface module"""

from abc import ABC, abstractmethod

from payment_api.domain.entities import PaymentIn, Product


class PaymentGateway(ABC):
    """Payment gateway interface."""

    @abstractmethod
    async def create(self, payment: PaymentIn, products: list[Product]) -> PaymentIn:
        """Create a payment in the external gateway.

        :param payment: The payment to be created.
        :param products: The products associated with the payment.
        :return: The created payment with updated information.
        :raises PaymentCreationError: If an error occurs while creating the payment.
        """
