"""V1 Payment REST API endpoint module"""

import logging

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response
from pydantic import ValidationError

from payment_api.adapters.inbound.rest.dependencies.core import (
    FinalizePaymentByMercadoPagoPaymentIdUseCaseDep,
    FindPaymentByIdUseCaseDep,
    RenderQRCodeUseCaseDep,
)
from payment_api.adapters.inbound.rest.v1.schemas import MercadoPagoWebhookV1, PaymentV1
from payment_api.application.commands import (
    FinalizePaymentByMercadoPagoPaymentIdCommand,
    FindPaymentByIdCommand,
    RenderQRCodeCommand,
)
from payment_api.application.use_cases.ports import MPClientError
from payment_api.domain.exceptions import (
    EventPublishingError,
    NotFound,
    PersistenceError,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/payment", tags=["payment"])


@router.get("/{payment_id}", response_model=PaymentV1)
async def find(
    payment_id: str,
    use_case: FindPaymentByIdUseCaseDep,
):
    """Find a payment by its ID"""

    logger.info("Received request to find payment with ID: %s", payment_id)
    command = FindPaymentByIdCommand(payment_id=payment_id)
    try:
        payment = await use_case.execute(command=command)

    except NotFound as error:
        logger.error("Cannot find payment with ID: %s", payment_id)
        raise HTTPException(status_code=404, detail="Payment not found") from error

    except PersistenceError as error:
        logger.error(
            "Persistence error occurred while processing request for payment ID: %s",
            payment_id,
            exc_info=True,
        )

        raise HTTPException(
            status_code=500, detail="An error occurred while processing your request"
        ) from error

    return PaymentV1.model_validate(payment.model_dump())


@router.get("/{payment_id}/qr")
async def render_qr_code(
    payment_id: str,
    use_case: RenderQRCodeUseCaseDep,
):
    """Render QR code for a payment"""

    logger.info("Received request to render QR code for payment ID: %s", payment_id)
    command = RenderQRCodeCommand(payment_id=payment_id)
    try:
        qr_code = await use_case.execute(command=command)

    except NotFound as error:
        logger.error("Cannot find payment with ID %s to render QR code", payment_id)
        raise HTTPException(status_code=404, detail="Payment not found") from error

    except PersistenceError as error:
        logger.error(
            "Persistence error occurred while rendering QR code for payment ID %s",
            payment_id,
            exc_info=True,
        )

        raise HTTPException(
            status_code=500, detail="An error occurred while rendering the QR code"
        ) from error

    except ValueError as error:
        logger.error(
            "Value error occurred while rendering QR code for payment ID %s",
            payment_id,
            exc_info=True,
        )

        raise HTTPException(status_code=400, detail=str(error)) from error

    return Response(content=qr_code, media_type="image/png")


@router.post("/notifications/mercado-pago", response_model=PaymentV1)
async def mercado_pago_webhook(
    request: Request,
    use_case: FinalizePaymentByMercadoPagoPaymentIdUseCaseDep,
):
    """Handle MercadoPago webhook notifications"""

    body = await request.body()
    logger.info("Received Mercado Pago webhook with body: %s", body.decode())

    try:
        webhook = MercadoPagoWebhookV1.model_validate_json(body)
    except ValidationError as error:
        logger.info(
            "Discarding Mercado Pago webhook by validation error: %s", str(error)
        )

        return Response(status_code=204)

    if webhook.action != "payment.created" or webhook.type != "payment":
        logger.info(
            "Discarding Mercado Pago webhook: action=%s, type=%s",
            webhook.action,
            webhook.type,
        )

        return Response(status_code=204)

    logger.info("Accepted Mercado Pago webhook for payment ID: %s", webhook.data.id)
    command = FinalizePaymentByMercadoPagoPaymentIdCommand(payment_id=webhook.data.id)
    try:
        payment = await use_case.execute(command=command)

    except NotFound as error:
        logger.error(
            "Payment with ID %s not found while processing MercadoPago webhook",
            webhook.data.id,
        )

        raise HTTPException(status_code=404, detail="Payment not found") from error

    except PersistenceError as error:
        logger.error(
            "Persistence error occurred while processing MercadoPago webhook for "
            "MP payment ID %s",
            webhook.data.id,
            exc_info=True,
        )

        raise HTTPException(
            status_code=500, detail="An error occurred while processing the webhook"
        ) from error

    except MPClientError as error:
        logger.error(
            "MercadoPago client error occurred while processing webhook for"
            "MP payment ID %s",
            webhook.data.id,
            exc_info=True,
        )

        raise HTTPException(
            status_code=502, detail="Error communicating with MercadoPago"
        ) from error

    except EventPublishingError:
        logger.error(
            "Event publishing error occurred while processing MercadoPago webhook for "
            "MP payment ID %s. Payment finalized but event not published, so we "
            "respond 204 to avoid retries",
            webhook.data.id,
            exc_info=True,
        )

        logger.warning(
            "Webhook with MP payment ID %s finalized but PaymentClosedEvent "
            "not published",
            webhook.data.id,
        )
        # TODO: Implement some mechanism to retry publishing the event later

        return Response(status_code=204)

    except ValueError as error:
        logger.error(
            "Value error occurred while processing MercadoPago webhook for"
            "MP payment ID %s",
            webhook.data.id,
            exc_info=True,
        )

        raise HTTPException(status_code=400, detail=str(error)) from error

    return PaymentV1.model_validate(payment.model_dump())
