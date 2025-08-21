"""
Configuration module for Contact Extractor Bot
Handles all configuration settings using Pydantic for validation
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class BotConfig(BaseSettings):
    """
    Configuration settings for the Contact Extractor Bot
    Uses Pydantic for validation and type safety
    """
    
    # ==========================================
    # DATABASE CONFIGURATION
    # ==========================================
    db_host: str = Field(default="localhost", description="Database host")
    db_port: int = Field(default=5432, description="Database port")
    db_name: str = Field(default="sms_marketing", description="Database name")
    db_user: str = Field(default="sms_user", description="Database user")
    db_password: str = Field(description="Database password")
    
    # ==========================================
    # BOT CONFIGURATION
    # ==========================================
    bot_name: str = Field(default="ContactExtractorBot", description="Bot name")
    bot_version: str = Field(default="1.0.0", description="Bot version")
    bot_log_level: str = Field(default="INFO", description="Logging level")
    bot_environment: str = Field(default="development", description="Environment")
    
    # ==========================================
    # TELEGRAM CONFIGURATION
    # ==========================================
    telegram_bot_token: str = Field(description="Telegram bot token")
    telegram_bot_username: str = Field(default="RNumbeRs_bot", description="Telegram bot username")
    telegram_webhook_url: Optional[str] = Field(default=None, description="Telegram webhook URL")
    telegram_webhook_secret: Optional[str] = Field(default=None, description="Telegram webhook secret")
    telegram_max_file_size_mb: int = Field(default=50, description="Maximum file size for Telegram")
    
    # ==========================================
    # EXTRACTION LIMITS
    # ==========================================
    min_extraction_amount: int = Field(default=100, description="Minimum contacts per extraction")
    max_extraction_amount: int = Field(default=10000, description="Maximum contacts per extraction")
    max_daily_extractions: int = Field(default=50000, description="Maximum daily extractions")
    max_hourly_extractions: int = Field(default=10, description="Maximum hourly extractions")
    
    # ==========================================
    # FILE CONFIGURATION
    # ==========================================
    export_path: str = Field(default="./exports/", description="Export files directory")
    log_path: str = Field(default="./logs/", description="Log files directory")
    file_retention_days: int = Field(default=7, description="File retention in days")
    max_file_size_mb: int = Field(default=100, description="Maximum file size in MB")
    
    # ==========================================
    # SECURITY CONFIGURATION
    # ==========================================
    require_confirmation: bool = Field(default=True, description="Require confirmation for large extractions")
    enable_audit_log: bool = Field(default=True, description="Enable audit logging")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    
    # ==========================================
    # PERFORMANCE CONFIGURATION
    # ==========================================
    db_pool_size: int = Field(default=20, description="Database connection pool size")
    db_max_overflow: int = Field(default=30, description="Database max overflow connections")
    db_pool_timeout: int = Field(default=30, description="Timeout to get connection from pool")
    db_pool_recycle: int = Field(default=3600, description="Recycle connections every hour")
    query_timeout: int = Field(default=60, description="Database query timeout in seconds")
    extraction_timeout: int = Field(default=300, description="Extraction timeout in seconds")
    export_batch_size: int = Field(default=5000, description="Export batch size")
    
    # ==========================================
    # EXTRACTION OPTIMIZATION
    # ==========================================
    max_concurrent_extractions: int = Field(default=5, description="Max concurrent extractions")
    large_extraction_threshold: int = Field(default=5000, description="Threshold for large extractions")
    progress_update_interval: int = Field(default=30, description="Progress update interval in seconds")
    
    # ==========================================
    # CACHE CONFIGURATION
    # ==========================================
    cache_locations_ttl: int = Field(default=3600, description="Cache locations TTL in seconds")
    cache_availability_ttl: int = Field(default=300, description="Cache availability TTL in seconds")
    cache_premium_ladas_ttl: int = Field(default=86400, description="Cache premium LADAs TTL in seconds")
    
    # ==========================================
    # FORMAT CONFIGURATION
    # ==========================================
    phone_format_digits: int = Field(default=12, description="Phone number format digits")
    xlsx_sheet_name: str = Field(default="Contactos", description="Excel sheet name")
    txt_encoding: str = Field(default="utf-8", description="Text file encoding")
    
    # ==========================================
    # CLEANUP CONFIGURATION
    # ==========================================
    auto_cleanup_enabled: bool = Field(default=True, description="Enable automatic cleanup")
    cleanup_schedule_hours: int = Field(default=24, description="Cleanup schedule in hours")
    temp_file_ttl_minutes: int = Field(default=60, description="Temporary file TTL in minutes")
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"
        env_prefix = "BOT_"
        case_sensitive = False
        validate_assignment = True
    
    @validator("bot_log_level")
    def validate_log_level(cls, v):
        """Validate log level"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator("bot_environment")
    def validate_environment(cls, v):
        """Validate environment"""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()
    
    @validator("min_extraction_amount", "max_extraction_amount")
    def validate_extraction_amounts(cls, v):
        """Validate extraction amounts"""
        if v < 1:
            raise ValueError("Extraction amounts must be positive")
        return v
    
    @validator("max_extraction_amount")
    def validate_max_greater_than_min(cls, v, values):
        """Validate max is greater than min"""
        if "min_extraction_amount" in values and v < values["min_extraction_amount"]:
            raise ValueError("max_extraction_amount must be greater than min_extraction_amount")
        return v
    
    @validator("export_path", "log_path")
    def validate_paths(cls, v):
        """Validate and create paths if they don't exist"""
        path = Path(v)
        path.mkdir(parents=True, exist_ok=True)
        return str(path)
    
    @property
    def database_url(self) -> str:
        """Get database connection URL"""
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def async_database_url(self) -> str:
        """Get async database connection URL"""
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"
    
    @property
    def export_path_obj(self) -> Path:
        """Get export path as Path object"""
        return Path(self.export_path)
    
    @property
    def log_path_obj(self) -> Path:
        """Get log path as Path object"""
        return Path(self.log_path)
    
    def is_valid_extraction_amount(self, amount: int) -> bool:
        """Check if extraction amount is valid"""
        return self.min_extraction_amount <= amount <= self.max_extraction_amount
    
    def get_confirmation_threshold(self) -> int:
        """Get threshold for requiring confirmation"""
        return 5000  # Require confirmation for extractions > 5000
    
    def should_require_confirmation(self, amount: int) -> bool:
        """Check if confirmation is required for this amount"""
        return self.require_confirmation and amount > self.get_confirmation_threshold()


# Global configuration instance
config = None


def get_config() -> BotConfig:
    """
    Get the global configuration instance
    
    Returns:
        BotConfig: The configuration instance
    """
    global config
    if config is None:
        from dotenv import load_dotenv
        from pathlib import Path
        
        # Load .env file
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        
        config = BotConfig()
    return config


def reload_config() -> BotConfig:
    """
    Reload configuration from environment
    
    Returns:
        BotConfig: The reloaded configuration instance
    """
    global config
    config = BotConfig()
    return config


# Export commonly used values
__all__ = [
    "BotConfig",
    "config",
    "get_config",
    "reload_config"
]