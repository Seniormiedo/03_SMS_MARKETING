"""
Application Configuration
"""

import os
from typing import List
from pydantic import validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""

    # Basic settings
    PROJECT_NAME: str = "SMS Marketing Platform"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALLOWED_HOSTS: str = "*"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sms_user:sms_password@localhost:15432/sms_marketing"
    POSTGRES_USER: str = "sms_user"
    POSTGRES_PASSWORD: str = "sms_password"
    POSTGRES_DB: str = "sms_marketing"

    # Redis
    REDIS_URL: str = "redis://localhost:16379/0"
    REDIS_PASSWORD: str = ""

    # Bot configuration (from existing .env)
    BOT_TELEGRAM_BOT_TOKEN: str = ""
    BOT_TELEGRAM_BOT_USERNAME: str = ""

    # SMS Providers
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_PHONE_NUMBER: str = ""

    # Telnyx (for number validation)
    TELNYX_API_KEY: str = ""

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # Application limits
    MAX_CONTACTS_PER_CAMPAIGN: int = 1000000
    DEFAULT_SMS_RATE_LIMIT: int = 100  # messages per minute

    @property
    def allowed_hosts_list(self) -> List[str]:
        """Convert ALLOWED_HOSTS string to list"""
        if self.ALLOWED_HOSTS == "*":
            return ["*"]
        return [host.strip() for host in self.ALLOWED_HOSTS.split(",")]

    @property
    def cors_origins_list(self) -> List[str]:
        """Convert CORS_ORIGINS string to list"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "allow"  # Allow extra fields from .env
    }

# Create settings instance
settings = Settings()
