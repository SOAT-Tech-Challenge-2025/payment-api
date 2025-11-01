"""A AIOBoto3 implementation of the AWS SNS Publisher port"""

import logging

from aioboto3 import Session as AIOBoto3Session
from botocore.exceptions import ClientError as BotoCoreClientError

from payment_api.domain.events import PaymentClosedEvent
from payment_api.domain.exceptions import EventPublishingError
from payment_api.domain.ports.payment_closed_publisher import PaymentClosedPublisher
from payment_api.infrastructure.config import PaymentClosedPublisherSettings

logger = logging.getLogger(__name__)


class BotoPaymentClosedPublisher(PaymentClosedPublisher):
    """A AIOBoto3 implementation of the AWS SNS Publisher port"""

    def __init__(
        self,
        aio_boto3_session: AIOBoto3Session,
        settings: PaymentClosedPublisherSettings,
    ):
        self.topic_arn = settings.TOPIC_ARN
        self.group_id = settings.GROUP_ID
        self.aio_boto3_session = aio_boto3_session

    async def publish(self, event: PaymentClosedEvent) -> None:
        """Publish a payment closed event

        :param event: The payment closed event to publish
        :return: None
        :raises EventPublishingError: If an error occurs while publishing the event
        """
        async with self.aio_boto3_session.resource("sns") as sns:
            topic = await sns.Topic(self.topic_arn)
            try:
                response = await topic.publish(
                    Subject="payment-closed",
                    Message=event.model_dump_json(),
                    MessageGroupId=self.group_id,
                    MessageDeduplicationId=str(event.id),
                )

                message_id = response["MessageId"]
                logger.debug("Published message ID=%s, topic=%s", message_id, topic.arn)

            except BotoCoreClientError as error:
                raise EventPublishingError(
                    "Error publishing message to SNS topic"
                ) from error
