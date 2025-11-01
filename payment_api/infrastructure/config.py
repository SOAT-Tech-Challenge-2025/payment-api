"""Application configuration module"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class APPSettings(BaseSettings):
    """APP specific settings"""

    model_config = SettingsConfigDict(
        env_file="settings/app.env", env_file_encoding="utf-8"
    )

    TITLE: str = "SOAT Tech Challenge Payment Api"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "PRD"
    ROOT_PATH: str = "/api"


class DatabaseSettings(BaseSettings):
    """Database specific settings"""

    model_config = SettingsConfigDict(
        env_file="settings/database.env", env_file_encoding="utf-8"
    )

    DSN: str
    ECHO: bool = False


class HTTPClientSettings(BaseSettings):
    """HTTP Client specific settings"""

    model_config = SettingsConfigDict(
        env_file="settings/http_client.env", env_file_encoding="utf-8"
    )

    TIMEOUT: float = 10.0  # seconds


class MercadoPagoSettings(BaseSettings):
    """Mercado Pago integration settings"""

    model_config = SettingsConfigDict(
        env_file="settings/mercado_pago.env", env_file_encoding="utf-8"
    )

    ACCESS_TOKEN: str
    USER_ID: str
    POS: str
    CALLBACK_URL: str


class AWSSettings(BaseSettings):
    """AWS integration settings"""

    model_config = SettingsConfigDict(
        env_file="settings/aws.env", env_file_encoding="utf-8"
    )

    REGION_NAME: str = "us-east-1"
    ACCOUNT_ID: str
    ACCESS_KEY_ID: str
    SECRET_ACCESS_KEY: str


class OrderCreatedListenerSettings(BaseSettings):
    """Order Created Listener settings"""

    model_config = SettingsConfigDict(
        env_file="settings/order_created_listener.env", env_file_encoding="utf-8"
    )

    QUEUE_NAME: str
    WAIT_TIME_SECONDS: int = 5
    MAX_NUMBER_OF_MESSAGES_PER_BATCH: int = 5
    VISIBILITY_TIMEOUT_SECONDS: int = 60


class PaymentClosedPublisherSettings(BaseSettings):
    """Payment Closed Publisher settings"""

    model_config = SettingsConfigDict(
        env_file="settings/payment_closed_publisher.env",
        env_file_encoding="utf-8",
    )

    TOPIC_ARN: str
    GROUP_ID: str
