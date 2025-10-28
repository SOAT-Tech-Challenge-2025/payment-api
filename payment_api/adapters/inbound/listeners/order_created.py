"""Listener for order created events from SQS"""

import json
import logging

from aioboto3 import Session as AIOBoto3Session
from botocore.exceptions import ClientError as BotoCoreClientError
from pydantic import BaseModel, Field

from payment_api.application.commands import CreatePaymentFromOrderCommand, ProductDTO
from payment_api.application.use_cases import CreatePaymentFromOrderUseCase
from payment_api.infrastructure.config import Settings

logger = logging.getLogger(__name__)


class OrderCreatedMessage(BaseModel):
    """Model for order created SQS message"""

    order_id: str = Field(..., description="Unique identifier for the order")
    total_order_value: float = Field(..., description="Total value of the order")
    products: list[ProductDTO] = Field(
        ..., description="List of products associated with the order"
    )


class OrderCreatedListener:
    """Listener for handling order created events from SQS"""

    def __init__(
        self,
        session: AIOBoto3Session,
        use_case: CreatePaymentFromOrderUseCase,
        settings: Settings,
    ):
        self.session = session
        self.use_case = use_case
        self.queue_name = settings.SQS_ORDER_CREATED_QUEUE_NAME

    async def listen(self):
        """Listen for order created events and process them"""
        async with self.session.resource("sqs") as sqs_client:
            logger.info("Listening for messages on queue: %s", self.queue_name)
            queue = await sqs_client.get_queue_by_name(QueueName=self.queue_name)
            wait_time = 20
            while True:
                messages = await self._receive_messages(
                    queue=queue, max_messages=1, wait_time=wait_time
                )
                if not messages:
                    logger.info("No messages received in %d seconds.", wait_time)
                    continue

    async def _receive_messages(self, queue, max_messages, wait_time):
        try:
            messages = await queue.receive_messages(
                MessageAttributeNames=["All"],
                MaxNumberOfMessages=max_messages,
                WaitTimeSeconds=wait_time,
            )

            for msg in messages:
                await self._process_message(message=msg)
        except BotoCoreClientError as error:
            logger.exception("Couldn't receive messages from queue: %s", queue)
            raise error
        else:
            return messages

    async def _process_message(self, message):
        """Process a single SQS message"""
        body = await message.body
        message_id = await message.message_id
        logger.info("Received message: %s: %s", message_id, body)
        try:
            body_dict = json.loads(body)
            order_message = OrderCreatedMessage.model_validate_json(
                body_dict["Message"]
            )
            command = CreatePaymentFromOrderCommand(
                order_id=order_message.order_id,
                total_order_value=order_message.total_order_value,
                products=order_message.products,
            )
            await self.use_case.execute(command=command)
        except Exception as e:
            logger.error(
                "Error %s processing message ID: %s: %s",
                e.__class__.__name__,
                message_id,
                e,
                exc_info=True,
            )
        finally:
            await message.delete()
            logger.info("Deleted message ID: %s", message_id)
