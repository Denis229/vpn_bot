"""Configuration models and helpers for the VPN Telegram bot."""
from __future__ import annotations

from functools import lru_cache
from typing import Optional

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Environment-driven settings for the bot."""

    telegram_token: str = Field(..., description="Telegram bot token")
    webhook_url: Optional[str] = Field(
        None, description="Optional webhook URL. When set, bot will use webhook mode."
    )

    # YooKassa settings
    yookassa_shop_id: str = Field(..., description="YooKassa shop ID")
    yookassa_secret_key: str = Field(..., description="YooKassa secret key")
    plan_price: float = Field(..., description="Plan price in RUB")

    # 3x-ui settings
    panel_base_url: str = Field(..., description="Base URL of 3x-ui panel, e.g. https://panel.example.com")
    panel_api_key: str = Field(..., description="API key for 3x-ui panel")
    inbound_id: int = Field(..., description="Inbound ID to attach new clients to")
    days_valid: int = Field(30, description="Number of days the account should stay active")
    traffic_gb: int = Field(10, description="Traffic allowance in gigabytes")

    # General settings
    storage_path: str = Field("data/payments.json", description="Path to store payment records")
    bot_name: str = Field("VPN Bot", description="Public bot name shown to users")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


class VpnUser(BaseModel):
    """Represents a VPN client returned by the 3x-ui panel."""

    username: str
    remark: str
    subscription_url: str
    qr_data: str


@lru_cache
def get_settings() -> BotSettings:
    """Returns cached bot settings loaded from environment variables."""

    return BotSettings()

