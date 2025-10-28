from datetime import datetime

from sqlalchemy import func, types
from sqlalchemy.orm import Mapped, mapped_column

from payment_api.domain.value_objects import PaymentStatus

from .base import BaseModel


class Payment(BaseModel):
    """The payment ORM model"""

    __tablename__ = "tb_pagamento"

    id: Mapped[str] = mapped_column(
        types.String, primary_key=True, unique=True, nullable=False
    )

    external_id: Mapped[str] = mapped_column(
        types.String, name="id_externo", unique=True, nullable=False
    )

    payment_status: Mapped[PaymentStatus] = mapped_column(
        types.Enum(PaymentStatus, native_enum=False),
        name="st_pagamento",
        nullable=False,
        index=True,
    )

    total_order_value: Mapped[float] = mapped_column(
        types.Float, name="vl_total_pedido", nullable=False
    )

    qr_code: Mapped[str] = mapped_column(types.Text, name="codigo_qr", nullable=False)

    expiration: Mapped[datetime] = mapped_column(
        types.TIMESTAMP, name="expiracao", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        types.TIMESTAMP,
        name="dt_inclusao",
        default=func.now(),  # pylint: disable=E1102
        nullable=False,
    )

    timestamp: Mapped[datetime] = mapped_column(
        types.TIMESTAMP,
        name="timestamp",
        default=func.now(),  # pylint: disable=E1102
        onupdate=func.now(),  # pylint: disable=E1102
        nullable=False,
    )

    def __repr__(self):
        return f"{type(self).__name__}[{self.id}]"
