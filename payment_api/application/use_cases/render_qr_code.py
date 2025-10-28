"""Use case to render a QR code for a payment"""

from payment_api.application.commands import RenderQRCodeCommand
from payment_api.application.use_cases.ports import AbstractQRCodeRenderer
from payment_api.domain.ports import PaymentRepository


class RenderQRCodeUseCase:
    """Use case to handle the rendering of a QR code for a payment"""

    def __init__(
        self,
        payment_repository: PaymentRepository,
        qr_code_renderer: AbstractQRCodeRenderer,
    ):
        self.payment_repository = payment_repository
        self.qr_code_renderer = qr_code_renderer

    async def execute(self, command: RenderQRCodeCommand) -> bytes:
        """Execute the use case to render a QR code

        :param command: command containing payment ID
        :type command: RenderQRCodeCommand
        :return: bytes representing the QR code image
        :rtype: bytes
        :raises ValueError: if the payment does not have an associated QR code
        """

        # Fetch the payment details using the payment ID
        payment = await self.payment_repository.find_by_id(
            payment_id=command.payment_id
        )

        if not payment.qr_code:
            raise ValueError("Payment does not have an associated QR code.")

        return self.qr_code_renderer.render(data=payment.qr_code)
