"""
System Configuration Module

Centralized configuration management for the SMS Marketing Platform.
Uses Pydantic Settings for type-safe configuration with environment variable support.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
from enum import Enum

from pydantic import BaseSettings, Field, validator, root_validator


class Environment(str, Enum):
    """Application environment enumeration."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging level enumeration."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseSettings):
    """Database configuration settings."""

    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_user: str = Field(default="sms_user", env="POSTGRES_USER")
    postgres_password: str = Field(..., env="POSTGRES_PASSWORD")
    postgres_database: str = Field(default="sms_marketing", env="POSTGRES_DATABASE")
    postgres_schema: str = Field(default="public", env="POSTGRES_SCHEMA")

    # MongoDB Configuration
    mongodb_host: str = Field(default="localhost", env="MONGODB_HOST")
    mongodb_port: int = Field(default=27017, env="MONGODB_PORT")
    mongodb_user: Optional[str] = Field(None, env="MONGODB_USER")
    mongodb_password: Optional[str] = Field(None, env="MONGODB_PASSWORD")
    mongodb_database: str = Field(default="validations", env="MONGODB_DATABASE")

    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    redis_database: int = Field(default=0, env="REDIS_DATABASE")

    # Connection Pool Settings
    postgres_pool_size: int = Field(default=20, env="POSTGRES_POOL_SIZE")
    postgres_max_overflow: int = Field(default=30, env="POSTGRES_MAX_OVERFLOW")
    postgres_pool_timeout: int = Field(default=30, env="POSTGRES_POOL_TIMEOUT")

    # Connection URLs (computed properties)
    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )

    @property
    def postgres_sync_url(self) -> str:
        """Get PostgreSQL synchronous connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_database}"
        )

    @property
    def mongodb_url(self) -> str:
        """Get MongoDB connection URL."""
        if self.mongodb_user and self.mongodb_password:
            return (
                f"mongodb://{self.mongodb_user}:{self.mongodb_password}"
                f"@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"
            )
        return f"mongodb://{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_database}"

    @property
    def redis_url(self) -> str:
        """Get Redis connection URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_database}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_database}"

    class Config:
        env_prefix = "DB_"
        case_sensitive = False


class ApiConfig(BaseSettings):
    """API configuration settings."""

    # Server Configuration
    host: str = Field(default="0.0.0.0", env="API_HOST")
    port: int = Field(default=8080, env="API_PORT")
    workers: int = Field(default=4, env="API_WORKERS")

    # Security
    secret_key: str = Field(..., env="API_SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    cors_methods: List[str] = Field(default=["GET", "POST", "PUT", "DELETE"], env="CORS_METHODS")
    cors_headers: List[str] = Field(default=["*"], env="CORS_HEADERS")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=1000, env="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=10000, env="RATE_LIMIT_PER_HOUR")
    rate_limit_per_day: int = Field(default=100000, env="RATE_LIMIT_PER_DAY")

    # Request Limits
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    request_timeout: int = Field(default=30, env="REQUEST_TIMEOUT")

    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_prefix = "API_"
        case_sensitive = False


class ValidationConfig(BaseSettings):
    """Platform validation configuration."""

    # WhatsApp Configuration
    whatsapp_enabled: bool = Field(default=True, env="WHATSAPP_ENABLED")
    whatsapp_api_key: Optional[str] = Field(None, env="WHATSAPP_API_KEY")
    whatsapp_rate_limit: int = Field(default=100, env="WHATSAPP_RATE_LIMIT")
    whatsapp_timeout: int = Field(default=30, env="WHATSAPP_TIMEOUT")
    whatsapp_weight: int = Field(default=25, env="WHATSAPP_WEIGHT")

    # Instagram Configuration
    instagram_enabled: bool = Field(default=True, env="INSTAGRAM_ENABLED")
    instagram_api_key: Optional[str] = Field(None, env="INSTAGRAM_API_KEY")
    instagram_rate_limit: int = Field(default=50, env="INSTAGRAM_RATE_LIMIT")
    instagram_timeout: int = Field(default=30, env="INSTAGRAM_TIMEOUT")
    instagram_weight: int = Field(default=20, env="INSTAGRAM_WEIGHT")

    # Facebook Configuration
    facebook_enabled: bool = Field(default=True, env="FACEBOOK_ENABLED")
    facebook_api_key: Optional[str] = Field(None, env="FACEBOOK_API_KEY")
    facebook_rate_limit: int = Field(default=50, env="FACEBOOK_RATE_LIMIT")
    facebook_timeout: int = Field(default=30, env="FACEBOOK_TIMEOUT")
    facebook_weight: int = Field(default=20, env="FACEBOOK_WEIGHT")

    # Google Configuration
    google_enabled: bool = Field(default=True, env="GOOGLE_ENABLED")
    google_api_key: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    google_rate_limit: int = Field(default=100, env="GOOGLE_RATE_LIMIT")
    google_timeout: int = Field(default=30, env="GOOGLE_TIMEOUT")
    google_weight: int = Field(default=20, env="GOOGLE_WEIGHT")

    # Apple Configuration
    apple_enabled: bool = Field(default=True, env="APPLE_ENABLED")
    apple_api_key: Optional[str] = Field(None, env="APPLE_API_KEY")
    apple_rate_limit: int = Field(default=50, env="APPLE_RATE_LIMIT")
    apple_timeout: int = Field(default=30, env="APPLE_TIMEOUT")
    apple_weight: int = Field(default=15, env="APPLE_WEIGHT")

    # General Validation Settings
    max_concurrent_validations: int = Field(default=20, env="MAX_CONCURRENT_VALIDATIONS")
    validation_cache_ttl: int = Field(default=86400, env="VALIDATION_CACHE_TTL")  # 24 hours
    retry_attempts: int = Field(default=3, env="VALIDATION_RETRY_ATTEMPTS")
    retry_delay: int = Field(default=1, env="VALIDATION_RETRY_DELAY")

    # Proxy Configuration
    proxy_enabled: bool = Field(default=False, env="PROXY_ENABLED")
    proxy_pool_size: int = Field(default=50, env="PROXY_POOL_SIZE")
    proxy_rotation_interval: int = Field(default=300, env="PROXY_ROTATION_INTERVAL")

    @root_validator
    def validate_weights_sum(cls, values):
        """Ensure platform weights sum to 100."""
        weights = [
            values.get("whatsapp_weight", 25),
            values.get("instagram_weight", 20),
            values.get("facebook_weight", 20),
            values.get("google_weight", 20),
            values.get("apple_weight", 15),
        ]
        if sum(weights) != 100:
            raise ValueError("Platform weights must sum to 100")
        return values

    class Config:
        env_prefix = "VALIDATION_"
        case_sensitive = False


class TelegramConfig(BaseSettings):
    """Telegram bot configuration."""

    bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    bot_username: str = Field(..., env="TELEGRAM_BOT_USERNAME")
    authorized_group_id: int = Field(..., env="TELEGRAM_AUTHORIZED_GROUP_ID")

    # Bot Limits
    max_extraction_amount: int = Field(default=10000, env="BOT_MAX_EXTRACTION_AMOUNT")
    max_daily_extractions: int = Field(default=50000, env="BOT_MAX_DAILY_EXTRACTIONS")
    max_hourly_extractions: int = Field(default=20, env="BOT_MAX_HOURLY_EXTRACTIONS")

    # Bot Features
    enable_rate_limiting: bool = Field(default=True, env="BOT_ENABLE_RATE_LIMITING")
    enable_audit_log: bool = Field(default=True, env="BOT_ENABLE_AUDIT_LOG")

    class Config:
        env_prefix = "BOT_"
        case_sensitive = False


class CeleryConfig(BaseSettings):
    """Celery task queue configuration."""

    broker_url: str = Field(..., env="CELERY_BROKER_URL")
    result_backend: str = Field(..., env="CELERY_RESULT_BACKEND")

    # Task Configuration
    task_serializer: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    result_serializer: str = Field(default="json", env="CELERY_RESULT_SERIALIZER")
    accept_content: List[str] = Field(default=["json"], env="CELERY_ACCEPT_CONTENT")
    timezone: str = Field(default="UTC", env="CELERY_TIMEZONE")

    # Worker Configuration
    worker_concurrency: int = Field(default=4, env="CELERY_WORKER_CONCURRENCY")
    worker_prefetch_multiplier: int = Field(default=1, env="CELERY_WORKER_PREFETCH_MULTIPLIER")
    task_acks_late: bool = Field(default=True, env="CELERY_TASK_ACKS_LATE")

    # Task Routing
    task_routes: Dict[str, Dict[str, str]] = Field(
        default={
            "validation.*": {"queue": "validation"},
            "scoring.*": {"queue": "scoring"},
            "export.*": {"queue": "export"},
        },
        env="CELERY_TASK_ROUTES"
    )

    class Config:
        env_prefix = "CELERY_"
        case_sensitive = False


class MonitoringConfig(BaseSettings):
    """Monitoring and observability configuration."""

    # Metrics
    metrics_enabled: bool = Field(default=True, env="METRICS_ENABLED")
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")

    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO, env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    log_file: Optional[str] = Field(None, env="LOG_FILE")

    # Health Checks
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")

    # Tracing
    tracing_enabled: bool = Field(default=False, env="TRACING_ENABLED")
    jaeger_endpoint: Optional[str] = Field(None, env="JAEGER_ENDPOINT")

    class Config:
        env_prefix = "MONITORING_"
        case_sensitive = False


class SystemConfig(BaseSettings):
    """Main system configuration that aggregates all config sections."""

    # Environment
    environment: Environment = Field(default=Environment.DEVELOPMENT, env="ENVIRONMENT")
    debug: bool = Field(default=False, env="DEBUG")

    # Project Information
    project_name: str = Field(default="SMS Marketing Platform", env="PROJECT_NAME")
    version: str = Field(default="2.0.0", env="VERSION")
    description: str = Field(
        default="Enterprise SMS Marketing Platform with Multi-Platform Lead Validation",
        env="DESCRIPTION"
    )

    # Paths
    base_path: Path = Field(default=Path.cwd(), env="BASE_PATH")
    data_path: Path = Field(default=Path.cwd() / "data", env="DATA_PATH")
    logs_path: Path = Field(default=Path.cwd() / "logs", env="LOGS_PATH")
    exports_path: Path = Field(default=Path.cwd() / "exports", env="EXPORTS_PATH")

    # Configuration Sections
    database: DatabaseConfig = DatabaseConfig()
    api: ApiConfig = ApiConfig()
    validation: ValidationConfig = ValidationConfig()
    telegram: TelegramConfig = TelegramConfig()
    celery: CeleryConfig = CeleryConfig()
    monitoring: MonitoringConfig = MonitoringConfig()

    @validator("base_path", "data_path", "logs_path", "exports_path", pre=True)
    def parse_path(cls, v):
        """Parse path from string or Path object."""
        return Path(v) if isinstance(v, str) else v

    @root_validator
    def create_directories(cls, values):
        """Create necessary directories if they don't exist."""
        paths_to_create = ["data_path", "logs_path", "exports_path"]
        for path_name in paths_to_create:
            path = values.get(path_name)
            if path and isinstance(path, Path):
                path.mkdir(parents=True, exist_ok=True)
        return values

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == Environment.PRODUCTION

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == Environment.DEVELOPMENT

    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == Environment.TESTING

    def get_service_url(self, service_name: str, port: int) -> str:
        """
        Get service URL for inter-service communication.

        Args:
            service_name: Name of the service
            port: Port number

        Returns:
            Service URL
        """
        if self.is_development():
            return f"http://localhost:{port}"
        else:
            return f"http://{service_name}:{port}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            """Customize settings sources priority."""
            return (
                init_settings,
                env_settings,
                file_secret_settings,
            )


# Global configuration instance
_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """
    Get global configuration instance (singleton pattern).

    Returns:
        SystemConfig instance
    """
    global _config
    if _config is None:
        _config = SystemConfig()
    return _config


def reload_config() -> SystemConfig:
    """
    Reload configuration from environment variables.

    Returns:
        New SystemConfig instance
    """
    global _config
    _config = SystemConfig()
    return _config


# Export commonly used configurations
__all__ = [
    "SystemConfig",
    "DatabaseConfig",
    "ApiConfig",
    "ValidationConfig",
    "TelegramConfig",
    "CeleryConfig",
    "MonitoringConfig",
    "Environment",
    "LogLevel",
    "get_config",
    "reload_config",
]
