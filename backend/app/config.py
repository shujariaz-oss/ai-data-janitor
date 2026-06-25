"""Application configuration via Pydantic Settings."""
from functools import lru_cache
from typing import Optional

from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")
    secret_key: str = Field(default="change-me", alias="SECRET_KEY")
    encryption_key: str = Field(default="change-me-32-bytes", alias="ENCRYPTION_KEY")

    database_url: PostgresDsn = Field(
        default="postgresql+asyncpg://janitor:janitor@localhost:5432/data_janitor",
        alias="DATABASE_URL",
    )

    redis_url: RedisDsn = Field(
        default="redis://localhost:6379/0", alias="REDIS_URL"
    )

    celery_broker_url: str = Field(
        default="redis://localhost:6379/1", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND"
    )

    stripe_secret_key: Optional[str] = Field(default=None, alias="STRIPE_SECRET_KEY")
    stripe_webhook_secret: Optional[str] = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")
    stripe_price_id: Optional[str] = Field(default=None, alias="STRIPE_PRICE_ID")

    salesforce_client_id: Optional[str] = Field(default=None, alias="SALESFORCE_CLIENT_ID")
    salesforce_client_secret: Optional[str] = Field(default=None, alias="SALESFORCE_CLIENT_SECRET")
    salesforce_redirect_uri: Optional[str] = Field(default=None, alias="SALESFORCE_REDIRECT_URI")

    hubspot_client_id: Optional[str] = Field(default=None, alias="HUBSPOT_CLIENT_ID")
    hubspot_client_secret: Optional[str] = Field(default=None, alias="HUBSPOT_CLIENT_SECRET")
    hubspot_redirect_uri: Optional[str] = Field(default=None, alias="HUBSPOT_REDIRECT_URI")

    clearbit_api_key: Optional[str] = Field(default=None, alias="CLEARBIT_API_KEY")
    hunter_api_key: Optional[str] = Field(default=None, alias="HUNTER_API_KEY")
    apollo_api_key: Optional[str] = Field(default=None, alias="APOLLO_API_KEY")

    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")
    proxy_url: Optional[str] = Field(default=None, alias="PROXY_URL")

    billable_unit_price_cents: int = 2
    free_records_per_month: int = 500
    crm_poll_interval_seconds: int = 300
    dedup_threshold: float = 0.85
    auto_merge_threshold: float = 0.95
    token_encryption_enabled: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
