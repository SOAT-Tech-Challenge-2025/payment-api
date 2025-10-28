"""Entrypoint module for the Payment API application"""

from payment_api.infrastructure import factory

app = factory.create_api()
