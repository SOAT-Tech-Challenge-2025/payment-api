"""Payment entity module"""

from datetime import datetime

from pydantic import BaseModel, Field

from payment_api.domain.value_objects import PaymentStatus


class Payment(BaseModel):
    """Payment entity representing a payment record."""

    id: str = Field(description="Unique identifier for the payment")
    external_id: str = Field(description="External identifier for the payment")
    payment_status: PaymentStatus = Field(description="Current status of the payment")
    total_order_value: float = Field(description="Total value of the order")
    qr_code: str = Field(description="QR code for the payment")
    expiration: datetime = Field(description="Expiration date and time of the payment")
    created_at: datetime | None = Field(
        None, description="Creation date and time of the payment"
    )

    timestamp: datetime | None = Field(
        None, description="Last update date and time of the payment"
    )

    def finalize(self, payment_status: PaymentStatus) -> "Payment":
        """Finalize the payment by updating its status and timestamp.

        :param payment_status: The new payment status to set.
        :rtype: Payment
        :return: The updated Payment instance.
        :raises ValueError: If the payment cannot be finalized due to its current
            status.
        """

        self._check_if_is_valid_to_finalize(payment_status)
        self.payment_status = payment_status
        return self

    def _check_if_is_valid_to_finalize(
        self, new_payment_status: PaymentStatus
    ) -> "Payment":
        """Check if the payment can be finalized with the new status.

        :param new_payment_status: The new payment status to set.
        :rtype: Payment
        :return: The Payment instance if valid.
        :raises ValueError: If the payment cannot be finalized due to its current
            status.
        """

        is_valid_status = self.payment_status == PaymentStatus.OPENED
        is_valid_new_status = new_payment_status != PaymentStatus.OPENED
        if not is_valid_status or not is_valid_new_status:
            raise ValueError(
                f"Unable to update a payment status from {self.payment_status} to "
                f"{new_payment_status}"
            )

        return self
