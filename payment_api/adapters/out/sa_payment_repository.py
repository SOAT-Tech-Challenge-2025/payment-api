"""SQL Alchemy implementation of the PaymentRepository port"""

from sqlalchemy import exists, insert, select
from sqlalchemy.exc import NoResultFound, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from payment_api.domain.entities import PaymentIn, PaymentOut
from payment_api.domain.exceptions import NotFound, PersistenceError
from payment_api.domain.ports import PaymentRepository
from payment_api.infrastructure.orm.models import Payment as PaymentModel


class SAPaymentRepository(PaymentRepository):
    """A SQL Alchemy implementation of the PaymentRepository port"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def find_by_id(self, payment_id: str) -> PaymentOut:
        try:
            result = await self.session.execute(
                select(PaymentModel).where(PaymentModel.id == payment_id)
            )

            return PaymentOut.model_validate(result.scalars().one())

        except NoResultFound as error:
            raise NotFound() from error

        except SQLAlchemyError as error:
            raise PersistenceError() from error

    async def exists_by_id(self, payment_id: str) -> bool:
        try:
            result = await self.session.execute(
                select(exists().where(PaymentModel.id == payment_id))
            )

            return result.scalar()

        except SQLAlchemyError as error:
            raise PersistenceError() from error

    async def exists_by_external_id(self, external_id: str) -> bool:
        try:
            result = await self.session.execute(
                select(exists().where(PaymentModel.external_id == external_id))
            )

            return result.scalar()

        except SQLAlchemyError as error:
            raise PersistenceError() from error

    async def save(self, payment: PaymentIn) -> PaymentOut:
        try:
            result = await self.session.execute(
                insert(PaymentModel)
                .values(**payment.model_dump())
                .returning(PaymentModel)
            )

            find_payment = PaymentOut.model_validate(result.scalars().one())
            await self.session.commit()
            return find_payment

        except SQLAlchemyError as error:
            raise PersistenceError() from error
