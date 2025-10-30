"""Order created event listener entrypoint module"""

import asyncio

from payment_api.infrastructure import factory


async def main():
    """Run the order created event listener"""

    try:
        settings = factory.get_settings()
        session_manager = factory.get_session_manager(settings=settings)
        http_client = factory.get_http_client(settings=settings)
        aws_session = factory.get_aws_session(settings=settings)
        async with factory.get_db_session(session_manager) as db_session:
            repository = factory.get_payment_repository(session=db_session)
            mp_api_client = factory.get_mercado_pago_api_client(
                settings=settings, http_client=http_client
            )

            gateway = factory.get_payment_gateway(
                settings=settings,
                mp_client=mp_api_client,
            )

            create_payment_from_order_use_case = (
                factory.get_create_payment_from_order_use_case(
                    payment_repository=repository,
                    payment_gateway=gateway,
                )
            )

            handler = factory.order_created_handler(
                use_case=create_payment_from_order_use_case
            )

            listener = factory.create_order_created_listener(
                session=aws_session,
                handler=handler,
                settings=settings,
            )

            await listener.listen()
    finally:
        await session_manager.close()
        await http_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
