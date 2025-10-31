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
        logger.info("Creating database session")
        async with factory.get_db_session(session_manager) as db_session:
            logger.info("Creating payment repository")
            repository = factory.get_payment_repository(session=db_session)
            logger.info("Creating Mercado Pago API client")
            mp_api_client = factory.get_mercado_pago_api_client(
                settings=mercado_pago_settings, http_client=http_client
            )

            logger.info("Creating payment gateway")
            gateway = factory.get_payment_gateway(
                settings=mercado_pago_settings,
                mp_client=mp_api_client,
            )

            logger.info("Creating use case for creating payment from order")
            create_payment_from_order_use_case = (
                factory.get_create_payment_from_order_use_case(
                    payment_repository=repository,
                    payment_gateway=gateway,
                )
            )

            logger.info("Creating order created event handler")
            handler = factory.order_created_handler(
                use_case=create_payment_from_order_use_case
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
