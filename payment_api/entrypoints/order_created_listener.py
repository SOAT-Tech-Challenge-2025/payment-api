"""Order created event listener entrypoint module"""

import asyncio
import logging

from payment_api.infrastructure import factory

logger = logging.getLogger(__name__)


async def main():
    """Run the order created event listener"""

    try:
        logger.info("Loading database settings")
        db_settings = factory.get_database_settings()
        logger.info("Loading HTTP client settings")
        http_client_settings = factory.get_http_client_settings()
        logger.info("Loading AWS settings")
        aws_settings = factory.get_aws_settings()
        logger.info("Loading Mercado Pago settings")
        mercado_pago_settings = factory.get_mercado_pago_settings()
        logger.info("Loading order created listener settings")
        order_created_listener_settings = factory.get_order_created_listener_settings()
        logger.info("Starting session manager")
        session_manager = factory.get_session_manager(settings=db_settings)
        logger.info("Starting HTTP client")
        http_client = factory.get_http_client(settings=http_client_settings)
        logger.info("Starting AWS session")
        aws_session = factory.get_aws_session(settings=aws_settings)
        logger.info("Creating order created handler")
        handler = factory.get_order_created_handler(
            session_manager=session_manager,
            mercado_pago_settings=mercado_pago_settings,
            http_client=http_client,
        )

        logger.info("Creating order created event listener")
        listener = factory.create_order_created_listener(
            session=aws_session,
            handler=handler,
            settings=order_created_listener_settings,
        )

        logger.info("Starting order created event listener")
        await listener.listen()
    finally:
        logger.info("Closing session manager")
        await session_manager.close()
        logger.info("Closing HTTP client")
        await http_client.aclose()


if __name__ == "__main__":
    import logging.config

    logging.config.fileConfig("logging.ini", disable_existing_loggers=False)
    asyncio.run(main())
