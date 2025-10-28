"""Payment repository interface."""

from abc import ABC, abstractmethod

from payment_api.domain.entities import PaymentIn, PaymentOut


class PaymentRepository(ABC):
    """Payment repository interface."""

    @abstractmethod
    async def find_by_id(self, payment_id: str) -> PaymentOut:
        """Find a payment by its ID.

        :param payment_id: The ID of the payment.
        :return: The payment entity.
        :raises NotFound: If the payment is not found.
        :raises PersistenceError: If an error occurs while retrieving the payment.
        """

    @abstractmethod
    async def exists_by_id(self, payment_id: str) -> bool:
        """Check if a payment exists by its ID.

        :param payment_id: The ID of the payment.
        :return: True if the payment exists, False otherwise.
        :raises PersistenceError: If an error occurs while checking the payment.
        """

    @abstractmethod
    async def exists_by_external_id(self, external_id: str) -> bool:
        """
        Check if a payment exists by its external ID.

        :param external_id: The external ID of the payment.
        :return: True if the payment exists, False otherwise.
        :raises PersistenceError: If an error occurs while checking the payment.
        """

    @abstractmethod
    async def save(self, payment: PaymentIn) -> PaymentOut:
        """Save a payment entity.
        :param payment: The payment entity to be saved.
        :return: The saved payment entity.
        :raises PersistenceError: If an error occurs while saving the payment.
        """
