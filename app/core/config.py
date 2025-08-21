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
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://sms_user:sms_password@localhost:5432/sms_marketing"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
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
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()