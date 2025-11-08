# pylint: disable=W0621

"""Unit tests for Order Created Listener and Handler"""

import json
from unittest.mock import MagicMock, Mock

import pytest
from botocore.exceptions import ClientError as BotoCoreClientError
from pytest_mock import MockerFixture
from sqlalchemy.ext.asyncio import AsyncSession

from payment_api.adapters.inbound.listeners.order_created import (
    OrderCreatedHandler,
    OrderCreatedListener,
)
from payment_api.application.commands import CreatePaymentFromOrderCommand, ProductDTO
from payment_api.application.use_cases import CreatePaymentFromOrderUseCase
from payment_api.infrastructure.orm import SessionManager


@pytest.fixture
def mock_session_manager(mocker: MockerFixture) -> MagicMock:
    """Mock SessionManager for testing"""
    mock_session_manager = mocker.Mock(spec=SessionManager)
    mock_db_session = mocker.Mock(spec=AsyncSession)

    # Create async context manager mock
    async_context_manager = mocker.AsyncMock()
    async_context_manager.__aenter__ = mocker.AsyncMock(return_value=mock_db_session)
    async_context_manager.__aexit__ = mocker.AsyncMock(return_value=None)
    mock_session_manager.session.return_value = async_context_manager

    return mock_session_manager


@pytest.fixture
def mock_use_case(mocker: MockerFixture) -> MagicMock:
    """Mock CreatePaymentFromOrderUseCase for testing"""
    return mocker.Mock(spec=CreatePaymentFromOrderUseCase)


@pytest.fixture
def mock_use_case_factory(mock_use_case: MagicMock, mocker: MockerFixture) -> MagicMock:
    """Mock use case factory for testing"""
    factory = mocker.MagicMock()
    factory.return_value = mock_use_case
    return factory


@pytest.fixture
def sample_order_message_dict() -> dict:
    """Sample order message dictionary for testing"""
    return {
        "Message": json.dumps(
            {
                "order_id": "A001",
                "total_order_value": 100.50,
                "products": [
                    {
                        "name": "Product 1",
                        "category": "Category A",
                        "unit_price": 50.25,
                        "quantity": 2,
                    }
                ],
            }
        )
    }


@pytest.fixture
def mock_sqs_message(
    sample_order_message_dict: dict, mocker: MockerFixture
) -> MagicMock:
    """Mock SQS message for testing"""
    message = mocker.MagicMock()

    # Create coroutines for body and message_id that return awaitable values
    async def get_body():
        return json.dumps(sample_order_message_dict)

    async def get_message_id():
        return "MSG123"

    # Set the attributes to the coroutine objects themselves (not calling them)
    message.body = get_body()
    message.message_id = get_message_id()
    message.delete = mocker.AsyncMock()
    return message


@pytest.fixture
def listener_settings(mocker: MockerFixture) -> Mock:
    """OrderCreatedListenerSettings for testing"""
    mock_settings = mocker.Mock()
    mock_settings.QUEUE_NAME = "test-queue"
    mock_settings.WAIT_TIME_SECONDS = 5
    mock_settings.MAX_NUMBER_OF_MESSAGES_PER_BATCH = 10
    mock_settings.VISIBILITY_TIMEOUT_SECONDS = 30
    return mock_settings


@pytest.fixture
def mock_aio_boto3_session(mocker: MockerFixture) -> MagicMock:
    """Mock AIOBoto3Session for testing"""
    session = mocker.MagicMock()
    mock_sqs_client = mocker.MagicMock()
    mock_queue = mocker.MagicMock()

    session.resource.return_value.__aenter__.return_value = mock_sqs_client
    session.resource.return_value.__aexit__.return_value = None
    mock_sqs_client.get_queue_by_name = mocker.AsyncMock(return_value=mock_queue)
    return session


class TestOrderCreatedHandler:
    """Test cases for the OrderCreatedHandler class"""

    async def test_should_process_valid_message_successfully(
        self,
        mock_session_manager: MagicMock,
        mock_use_case_factory: MagicMock,
        mock_use_case: MagicMock,
        mock_sqs_message: MagicMock,
        mocker: MockerFixture,
    ):
        """Given a valid SQS message with order data
        When the handler processes the message
        Then it should create payment command and execute use case successfully
        """

        # Given
        mock_use_case.execute = mocker.AsyncMock()
        handler = OrderCreatedHandler(
            session_manager=mock_session_manager, use_case_factory=mock_use_case_factory
        )

        # When
        await handler.handle(message=mock_sqs_message)

        # Then
        mock_session_manager.session.assert_called_once()
        mock_use_case_factory.assert_called_once()

        # Verify the command was created correctly
        mock_use_case.execute.assert_awaited_once_with(
            command=CreatePaymentFromOrderCommand(
                order_id="A001",
                total_order_value=100.50,
                products=[
                    ProductDTO(
                        name="Product 1",
                        category="Category A",
                        unit_price=50.25,
                        quantity=2,
                    )
                ],
            )
        )

        mock_sqs_message.delete.assert_awaited_once_with()


class TestOrderCreatedListener:
    """Test cases for the OrderCreatedListener class"""

    async def test_should_initialize_listener_with_correct_settings(
        self,
        mock_aio_boto3_session: MagicMock,
        listener_settings: Mock,
        mocker: MockerFixture,
    ):
        """Given valid settings and dependencies
        When creating an OrderCreatedListener
        Then it should initialize with correct configuration
        """

        # Given
        mock_handler = mocker.Mock(spec=OrderCreatedHandler)

        # When
        listener = OrderCreatedListener(
            session=mock_aio_boto3_session,
            handler=mock_handler,
            settings=listener_settings,
        )

        # Then
        assert listener.queue_name == "test-queue"
        assert listener.wait_time == 5
        assert listener.max_messages == 10
        assert listener.visibility_timeout == 30

    async def test_should_consume_messages_successfully(
        self,
        mock_aio_boto3_session: MagicMock,
        listener_settings: Mock,
        mock_sqs_message: MagicMock,
        mocker: MockerFixture,
    ):
        """Given messages available in the queue
        When consuming messages
        Then it should retrieve and process them successfully
        """

        # Given
        mock_handler = mocker.Mock(spec=OrderCreatedHandler)
        mock_handler.handle = mocker.AsyncMock()

        mock_queue = mocker.MagicMock()
        mock_queue.receive_messages = mocker.AsyncMock(return_value=[mock_sqs_message])

        listener = OrderCreatedListener(
            session=mock_aio_boto3_session,
            handler=mock_handler,
            settings=listener_settings,
        )

        # When
        messages = await listener._consume(queue=mock_queue)  # pylint: disable=W0212

        # Then
        assert len(messages) == 1
        mock_queue.receive_messages.assert_awaited_once_with(
            MessageAttributeNames=["All"],
            MaxNumberOfMessages=10,
            WaitTimeSeconds=5,
            VisibilityTimeout=30,
        )

        mock_handler.handle.assert_awaited_once_with(message=mock_sqs_message)

    async def test_should_handle_sqs_client_error_during_consume(
        self,
        mock_aio_boto3_session: MagicMock,
        listener_settings: Mock,
        mocker: MockerFixture,
    ):
        """Given an SQS client error occurs
        When consuming messages
        Then it should raise the client error
        """

        # Given
        mock_handler = mocker.Mock(spec=OrderCreatedHandler)

        mock_queue = mocker.MagicMock()
        client_error = BotoCoreClientError(
            error_response={"Error": {"Code": "TestError", "Message": "Test error"}},
            operation_name="ReceiveMessage",
        )

        mock_queue.receive_messages = mocker.AsyncMock(side_effect=client_error)
        listener = OrderCreatedListener(
            session=mock_aio_boto3_session,
            handler=mock_handler,
            settings=listener_settings,
        )

        # When/Then
        with pytest.raises(BotoCoreClientError):
            await listener._consume(queue=mock_queue)  # pylint: disable=W0212

    async def test_should_handle_message_processing_failure_and_delete_message(
        self,
        mock_aio_boto3_session: MagicMock,
        listener_settings: Mock,
        mock_sqs_message: MagicMock,
        mocker: MockerFixture,
    ):
        """Given a message processing failure occurs
        When consuming messages
        Then it should log error and delete the message to avoid retries
        """

        # Given
        mock_handler = mocker.Mock(spec=OrderCreatedHandler)
        mock_handler.handle = mocker.AsyncMock(
            side_effect=Exception("Processing failed")
        )

        mock_queue = mocker.MagicMock()
        mock_queue.receive_messages = mocker.AsyncMock(return_value=[mock_sqs_message])

        listener = OrderCreatedListener(
            session=mock_aio_boto3_session,
            handler=mock_handler,
            settings=listener_settings,
        )

        # When
        messages = await listener._consume(queue=mock_queue)  # pylint: disable=W0212

        # Then
        assert len(messages) == 1
        mock_handler.handle.assert_awaited_once_with(message=mock_sqs_message)
        mock_sqs_message.delete.assert_awaited_once_with()

    async def test_should_handle_empty_message_queue(
        self,
        mock_aio_boto3_session: MagicMock,
        listener_settings: Mock,
        mocker: MockerFixture,
    ):
        """Given no messages in the queue
        When consuming messages
        Then it should return empty list
        """

        # Given
        mock_handler = mocker.Mock(spec=OrderCreatedHandler)

        mock_queue = mocker.MagicMock()
        mock_queue.receive_messages = mocker.AsyncMock(return_value=[])

        listener = OrderCreatedListener(
            session=mock_aio_boto3_session,
            handler=mock_handler,
            settings=listener_settings,
        )

        # When
        messages = await listener._consume(queue=mock_queue)  # pylint: disable=W0212

        # Then
        assert len(messages) == 0
        mock_handler.handle.assert_not_awaited()

    async def test_should_stop_listening_on_shutdown_signal(
        self,
        mock_aio_boto3_session: MagicMock,
        listener_settings: Mock,
        mocker: MockerFixture,
    ):
        """Given a shutdown signal is received
        When listening for messages
        Then it should stop the listening loop gracefully
        """

        # Given
        mock_handler = mocker.Mock(spec=OrderCreatedHandler)
        mock_handler.handle = mocker.AsyncMock()

        mock_shutdown_handler = mocker.MagicMock()
        mock_shutdown_handler.shutdown = True  # Simulate shutdown signal

        # Mock the SQS resource context manager
        mock_sqs_client = mocker.MagicMock()
        mock_queue = mocker.MagicMock()
        mock_sqs_client.get_queue_by_name = mocker.AsyncMock(return_value=mock_queue)

        mock_aio_boto3_session.resource.return_value.__aenter__.return_value = (
            mock_sqs_client
        )

        mock_aio_boto3_session.resource.return_value.__aexit__.return_value = None
        listener = OrderCreatedListener(
            session=mock_aio_boto3_session,
            handler=mock_handler,
            settings=listener_settings,
        )

        # When
        await listener.listen(shutdown_event=mock_shutdown_handler)

        # Then
        # Should have attempted to get the queue but stopped due to shutdown
        mock_aio_boto3_session.resource.assert_called_once_with("sqs")
        mock_sqs_client.get_queue_by_name.assert_awaited_once_with(
            QueueName="test-queue"
        )

        mock_handler.handle.assert_not_awaited()
