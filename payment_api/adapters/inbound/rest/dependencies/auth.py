"""Module with authentication dependencies for the REST API"""

import logging
from typing import Annotated

from fastapi import HTTPException, Query

from .core import MercadoPagoSettingsDep

logger = logging.getLogger(__name__)


def validate_mercado_pago_notification(
    key: Annotated[str, Query(alias="x-mp-webhook-key")],
    settings: MercadoPagoSettingsDep,
):
    """Validate Mercado Pago notification using webhook key"""

    if key != settings.WEBHOOK_KEY:
        logger.warning("Invalid Mercado Pago webhook key")
        raise HTTPException(status_code=401, detail="Unauthorized")
