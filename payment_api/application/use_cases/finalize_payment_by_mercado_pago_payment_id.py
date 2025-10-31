"""Use case to finalize a payment using Mercado Pago payment ID"""

import logging

from payment_api.application.commands import (
    FinalizePaymentByMercadoPagoPaymentIdCommand,
)
from payment_api.application.use_cases.ports import (
    AbstractMercadoPagoClient,
    MPOrderStatus,
)
from payment_api.domain.entities import PaymentIn, PaymentOut
from payment_api.domain.ports import PaymentRepository
from payment_api.domain.value_objects import PaymentStatus

logger = logging.getLogger(__name__)


class FinalizePaymentByMercadoPagoPaymentIdUseCase:
    """Use case to finalize a payment using Mercado Pago payment ID"""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        mercado_pago_client: AbstractMercadoPagoClient,
    ):
        self.payment_repository = payment_repository
        self.mercado_pago_client = mercado_pago_client

    async def execute(
        self, command: FinalizePaymentByMercadoPagoPaymentIdCommand
    ) -> PaymentOut:
        """Finalize a payment using Mercado Pago payment ID

        :param command: command containing the Mercado Pago payment ID
        :type command: FinalizePaymentByMercadoPagoPaymentIdCommand
        :return: Finalized Payment
        :rtype: PaymentOut
        :raises NotFound: if the payment is not found
        :raises PersistenceError: if there is an error during data persistence to
            the repository
        :raises ValueError: if the payment cannot be finalized due to its current status
        :raises MPClientError: if there is an error communicating with Mercado Pago
        """

        logger.info(
            "Called the use case to finalize payment with Mercado Pago payment ID %s",
            command.payment_id,
        )

        # find payment in Mercado Pago
        mp_payment = await self.mercado_pago_client.find_payment_by_id(
            payment_id=command.payment_id
        )

        # find Mercado Pago order associated with the payment
        mp_order = await self.mercado_pago_client.find_order_by_id(
            order_id=int(mp_payment.order.id)
        )

        # validate if payment with Mercado Pago ID already exists
        order_id = mp_order.external_reference
        external_id = str(mp_order.id)
        if await self.payment_repository.exists_by_external_id(external_id=external_id):
            raise ValueError(f"Payment with external ID {external_id} already exists")

        # finalize payment in repository
        payment = await self.payment_repository.find_by_id(payment_id=order_id)
        payment.external_id = external_id
        payment.finalize(
            self._convert_mp_order_status_to_domain_status(mp_order.status)
        )

        logger.info(
            "External ID for payment %s set to %s finalized with status %s",
            payment.id,
            external_id,
            payment.payment_status.value,
        )

        return await self.payment_repository.save(
            payment=PaymentIn.model_validate(payment)
        )

    def _convert_mp_order_status_to_domain_status(
        self, mp_order_status: MPOrderStatus
    ) -> PaymentStatus:
        """Convert Mercado Pago order status to PaymentStatus

        :param mp_order_status: Mercado Pago order status
        :type mp_order_status: MPOrderStatus
        :return: Corresponding PaymentStatus
        :rtype: PaymentStatus
        """
        mapping = {
            MPOrderStatus.CLOSED: PaymentStatus.CLOSED,
            MPOrderStatus.EXPIRED: PaymentStatus.EXPIRED,
            MPOrderStatus.OPENED: PaymentStatus.OPENED,
        }

        return mapping[mp_order_status]
