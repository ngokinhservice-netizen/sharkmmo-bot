import json
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # App Info
    APP_NAME: str = "SHARKMMO"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Telegram Bot
    BOT_TOKEN: str = Field(default="", description="Telegram Bot Token from @BotFather")
    ADMIN_IDS: Union[List[int], str] = Field(default="1336962312", description="List of Telegram user IDs with Admin privileges")

    # Canboso API
    CANBOSO_API_KEY: str = Field(default="", description="Buyer API key from Canboso (x-buyer-key)")
    CANBOSO_BASE_URL: str = Field(default="https://canboso.com", description="Base URL of Canboso API")
    CANBOSO_TIMEOUT_SECONDS: float = Field(default=30.0, description="Canboso HTTP request timeout")
    CANBOSO_CACHE_TTL_SECONDS: int = Field(default=60, description="Cache TTL for Canboso products & balance")
    SOURCE_BALANCE_ALERT_THRESHOLD: float = Field(default=100000.0, description="Low source balance alert threshold (VND)")

    # Database
    DATABASE_URL: str = Field(
        default="sqlite+aiosqlite:///./sharkmmo.db",
        description="Async database connection string"
    )

    # Security & Dashboard API
    ADMIN_API_KEY: str = Field(default="sharkmmo_admin_secret_key_2026", description="API Key for admin endpoints")
    JWT_SECRET: str = Field(default="sharkmmo_jwt_super_secret_key_987654321", description="JWT secret key")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Payment & VietQR
    BANK_CODE: str = Field(default="MB", description="Bank code (e.g. MB, VCB, TCB, VPB)")
    BANK_ACCOUNT_NO: str = Field(default="0988888888", description="Bank account number for VietQR")
    BANK_ACCOUNT_NAME: str = Field(default="SHARKMMO STORE", description="Bank account holder name")
    VIETQR_TEMPLATE: str = Field(default="compact2", description="VietQR template style")
    SEPAY_API_KEY: str = Field(default="", description="SePay API token / Webhook Authorization token")

    # Pricing Defaults
    DEFAULT_MARKUP_TYPE: str = Field(default="percent", description="'percent' or 'fixed'")
    DEFAULT_MARKUP_VALUE: float = Field(default=20.0, description="Default markup value (e.g. 20% or 10000 VND)")
    DEFAULT_ROUND_TO: int = Field(default=1000, description="Round calculated price to nearest (e.g. 1000 VND)")
    AUTO_SYNC_INTERVAL_MINUTES: int = Field(default=15, description="Minutes between automated product syncs")

    @field_validator("ADMIN_IDS", mode="before")
    @classmethod
    def parse_admin_ids(cls, v: Union[str, List[int]]) -> List[int]:
        if isinstance(v, list):
            return [int(x) for x in v]
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return []
            if v.startswith("[") and v.endswith("]"):
                try:
                    return [int(x) for x in json.loads(v)]
                except Exception:
                    pass
            return [int(x.strip()) for x in v.split(",") if x.strip().isdigit()]
        return []


settings = Settings()
