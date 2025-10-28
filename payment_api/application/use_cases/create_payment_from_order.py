"""Use case for creating a new payment"""

from datetime import datetime, timedelta, timezone

from payment_api.application.commands import CreatePaymentFromOrderCommand
from payment_api.domain.entities import PaymentIn, PaymentOut, Product
from payment_api.domain.exceptions import PaymentCreationError
from payment_api.domain.ports import PaymentGateway, PaymentRepository
from payment_api.domain.value_objects import PaymentStatus


class CreatePaymentFromOrderUseCase:
    """Use case to handle the creation of a new payment based on an order"""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        payment_gateway: PaymentGateway,
    ):
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway

    async def execute(self, command: CreatePaymentFromOrderCommand) -> PaymentOut:
        """Execute the use case to create a new payment

        :param command: command containing the details for payment creation
        :type command: CreatePaymentFromOrderCommand
        :return: PaymentOut entity representing the created payment
        :rtype: PaymentOut
        :raises PaymentCreationError: if there is an error during payment creation
        :raises PersistenceError: if there is an error during data persistence to
            the repository
        """

        # validate
        if await self.payment_repository.exists_by_id(payment_id=command.order_id):
            raise PaymentCreationError(
                f"Payment with ID {command.order_id} already exists"
            )

        # convert ProductDTOs to Products
        products = [
            Product.model_validate(product.model_dump()) for product in command.products
        ]

        # create payment entity
        now = datetime.now(timezone.utc)
        naive_now = now.replace(tzinfo=None)
        expiration = naive_now + timedelta(minutes=15)
        payment = PaymentIn(
            id=command.order_id,
            external_id=f"empty-{command.order_id}",
            payment_status=PaymentStatus.OPENED,
            total_order_value=command.total_order_value,
            products=products,
            expiration=expiration,
        )

        # create payment in gateway
        try:
            payment = await self.payment_gateway.create(
                payment=payment, products=products
            )
        except Exception as e:
            raise PaymentCreationError(
                f"Error creating payment in gateway: {str(e)}"
            ) from e

        # save payment in repository
        return await self.payment_repository.save(payment=payment)
