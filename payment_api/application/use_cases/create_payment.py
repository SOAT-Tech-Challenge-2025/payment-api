"""Use case for creating a new payment"""

from datetime import datetime, timedelta

from payment_api.application.commands import CreatePaymentCommand
from payment_api.domain.entities import Payment
from payment_api.domain.exceptions import PaymentCreationError, PersistenceError
from payment_api.domain.ports import PaymentGateway, PaymentRepository
from payment_api.domain.value_objects import PaymentStatus


class CreatePaymentUseCase:
    """Use case to handle the creation of a new payment"""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        payment_gateway: PaymentGateway,
    ):
        self.payment_repository = payment_repository
        self.payment_gateway = payment_gateway

    async def execute(self, command: CreatePaymentCommand) -> Payment:
        """Execute the use case to create a new payment"""

        # validate
        if await self.payment_repository.exists_by_id(id=command.id):
            raise PaymentCreationError(f"Payment with ID {command.id} already exists")

        # create payment entity
        expiration = datetime.now() + timedelta(minutes=15)
        payment = Payment(
            id=command.id,
            external_id=f"empty-{command.id}",
            payment_status=PaymentStatus.OPENED,
            total_order_value=command.total_order_value,
            products=command.products,
            expiration=expiration,
        )

        # create payment in gateway
        try:
            payment = await self.payment_gateway.create(
                payment=payment, products=command.products
            )
        except Exception as e:
            raise PaymentCreationError(
                f"Error creating payment in gateway: {str(e)}"
            ) from e

        # save payment in repository
        try:
            return await self.payment_repository.save(payment=payment)
        except PersistenceError as exc:
            raise PaymentCreationError(
                f"Error saving payment to repository: {str(exc)}"
            ) from exc
