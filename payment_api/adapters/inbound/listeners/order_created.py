"""Listener for order created events from SQS"""

import json
import logging
from typing import Callable

from aioboto3 import Session as AIOBoto3Session
from botocore.exceptions import ClientError as BotoCoreClientError
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from payment_api.application.commands import CreatePaymentFromOrderCommand, ProductDTO
from payment_api.application.use_cases import CreatePaymentFromOrderUseCase
from payment_api.infrastructure.config import OrderCreatedListenerSettings
from payment_api.infrastructure.orm import SessionManager

logger = logging.getLogger(__name__)


class OrderCreatedMessage(BaseModel):
    """Model for order created SQS message"""

    order_id: str = Field(..., description="Unique identifier for the order")
    total_order_value: float = Field(..., description="Total value of the order")
    products: list[ProductDTO] = Field(
        ..., description="List of products associated with the order"
    )


class OrderCreatedHandler:
    """Handler for processing order created messages"""

    def __init__(
        self,
        session_manager: SessionManager,
        use_case_factory: Callable[[AsyncSession], CreatePaymentFromOrderUseCase],
    ):
        self.session_manager = session_manager
        self.use_case_factory = use_case_factory

    async def handle(self, message):
        """Handle the order created message"""

        body = await message.body
        message_id = await message.message_id
        logger.info("Received message: %s: %s", message_id, body)
        async with self.session_manager.session() as db_session:
            use_case = self.use_case_factory(db_session)
            body_dict = json.loads(body)
            order_message = OrderCreatedMessage.model_validate_json(
                body_dict["Message"]
            )

            command = CreatePaymentFromOrderCommand(
                order_id=order_message.order_id,
                total_order_value=order_message.total_order_value,
                products=order_message.products,
            )

            await use_case.execute(command=command)
            await message.delete()
            logger.info("Successfully processed and deleted message ID: %s", message_id)


class OrderCreatedListener:
    """Listener for handling order created events from SQS"""

    def __init__(
        self,
        session: AIOBoto3Session,
        handler: OrderCreatedHandler,
        settings: OrderCreatedListenerSettings,
    ):
        self.session = session
        self.handler = handler
        self.queue_name = settings.QUEUE_NAME
        self.wait_time = settings.WAIT_TIME_SECONDS
        self.visibility_timeout = settings.VISIBILITY_TIMEOUT_SECONDS
        self.max_messages = settings.MAX_NUMBER_OF_MESSAGES_PER_BATCH

    async def listen(self, shutdown_event=None):
        """Listen for order created events and process them"""

        async with self.session.resource("sqs") as sqs_client:
            logger.info("Listening for messages on queue: %s", self.queue_name)
            queue = await sqs_client.get_queue_by_name(QueueName=self.queue_name)
            while True:
                if shutdown_event and shutdown_event.shutdown:
                    logger.info("Shutdown requested, stopping listener")
                    break

                messages = await self._consume(queue=queue)
                if not messages:
                    logger.debug("No messages received in %d seconds", self.wait_time)
                    continue

    async def _consume(self, queue):
        try:
            messages = await queue.receive_messages(
                MessageAttributeNames=["All"],
                MaxNumberOfMessages=self.max_messages,
                WaitTimeSeconds=self.wait_time,
                VisibilityTimeout=self.visibility_timeout,
            )

        except BotoCoreClientError as error:
            logger.error(
                "Couldn't receive messages from queue: %s", queue, exc_info=True
            )

            raise error

        for msg in messages:
            message_id = await msg.message_id
            try:
                await self.handler.handle(message=msg)
            except Exception:
                logger.error(
                    "Failed to process message ID: %s",
                    message_id,
                    exc_info=True,
                )

        return messages
