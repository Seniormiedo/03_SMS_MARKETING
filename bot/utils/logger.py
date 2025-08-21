"""
Professional logging system for Contact Extractor Bot
Uses structlog for structured logging with rich formatting
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from rich.console import Console
from rich.logging import RichHandler

from config import get_config


class BotLogger:
    """
    Professional logging system for the Contact Extractor Bot
    Provides structured logging with audit capabilities
    """
    
    def __init__(self):
        self.config = get_config()
        self.console = Console()
        self._setup_logging()
        self.logger = structlog.get_logger("ContactExtractorBot")
    
    def _setup_logging(self):
        """Setup structured logging with file and console handlers"""
        
        # Create log directory
        log_dir = Path(self.config.log_path)
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.contextvars.merge_contextvars,
                structlog.processors.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.dev.set_exc_info,
                structlog.processors.TimeStamper(fmt="ISO"),
                structlog.dev.ConsoleRenderer() if self.config.bot_environment == "development" 
                else structlog.processors.JSONRenderer()
            ],
            wrapper_class=structlog.make_filtering_bound_logger(
                getattr(logging, self.config.bot_log_level)
            ),
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        # Setup standard logging
        logging.basicConfig(
            level=getattr(logging, self.config.bot_log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[
                RichHandler(console=self.console, rich_tracebacks=True),
                logging.FileHandler(
                    log_dir / f"bot_{datetime.now().strftime('%Y%m%d')}.log"
                )
            ]
        )
        
        # Setup audit logging if enabled
        if self.config.enable_audit_log:
            self._setup_audit_logging(log_dir)
    
    def _setup_audit_logging(self, log_dir: Path):
        """Setup audit logging for extractions"""
        audit_logger = logging.getLogger("audit")
        audit_handler = logging.FileHandler(
            log_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.log"
        )
        audit_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - AUDIT - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
        audit_logger.addHandler(audit_handler)
        audit_logger.setLevel(logging.INFO)
        self.audit_logger = audit_logger
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self.logger.critical(message, **kwargs)
    
    def audit(self, action: str, details: Dict[str, Any]):
        """
        Log audit event for compliance and tracking
        
        Args:
            action: Action performed (e.g., 'EXTRACTION', 'EXPORT', 'STATUS_UPDATE')
            details: Additional details about the action
        """
        if not self.config.enable_audit_log:
            return
        
        audit_data = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "bot_version": self.config.bot_version,
            **details
        }
        
        audit_message = " | ".join([f"{k}={v}" for k, v in audit_data.items()])
        self.audit_logger.info(audit_message)
    
    def log_extraction_request(
        self, 
        extraction_type: str, 
        amount: int, 
        location: Optional[str] = None,
        format_type: str = "xlsx"
    ):
        """Log extraction request"""
        details = {
            "extraction_type": extraction_type,
            "amount": amount,
            "format": format_type,
            "location": location or "premium"
        }
        
        self.info("Extraction requested", **details)
        self.audit("EXTRACTION_REQUEST", details)
    
    def log_extraction_success(
        self, 
        contact_ids: list, 
        file_path: str,
        execution_time: float
    ):
        """Log successful extraction"""
        details = {
            "contacts_extracted": len(contact_ids),
            "file_path": file_path,
            "execution_time_seconds": round(execution_time, 2),
            "contact_ids_sample": contact_ids[:5] if len(contact_ids) > 5 else contact_ids
        }
        
        self.info("Extraction completed successfully", **details)
        self.audit("EXTRACTION_SUCCESS", details)
    
    def log_extraction_error(self, error: str, details: Dict[str, Any]):
        """Log extraction error"""
        error_details = {
            "error": error,
            **details
        }
        
        self.error("Extraction failed", **error_details)
        self.audit("EXTRACTION_ERROR", error_details)
    
    def log_status_update(self, contact_count: int, new_status: str):
        """Log contact status update"""
        details = {
            "contacts_updated": contact_count,
            "new_status": new_status
        }
        
        self.info("Contact status updated", **details)
        self.audit("STATUS_UPDATE", details)
    
    def log_file_export(self, file_path: str, file_size: int, format_type: str):
        """Log file export"""
        details = {
            "file_path": file_path,
            "file_size_bytes": file_size,
            "format": format_type
        }
        
        self.info("File exported", **details)
        self.audit("FILE_EXPORT", details)
    
    def log_validation_error(self, validation_type: str, error: str, input_data: Any):
        """Log validation error"""
        details = {
            "validation_type": validation_type,
            "error": error,
            "input": str(input_data)
        }
        
        self.warning("Validation failed", **details)
        self.audit("VALIDATION_ERROR", details)
    
    def log_rate_limit_exceeded(self, limit_type: str, current_count: int, limit: int):
        """Log rate limit exceeded"""
        details = {
            "limit_type": limit_type,
            "current_count": current_count,
            "limit": limit
        }
        
        self.warning("Rate limit exceeded", **details)
        self.audit("RATE_LIMIT_EXCEEDED", details)
    
    def log_system_info(self):
        """Log system information at startup"""
        import platform
        import psutil
        
        system_info = {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "bot_version": self.config.bot_version,
            "environment": self.config.bot_environment
        }
        
        self.info("Bot started", **system_info)
        self.audit("BOT_STARTUP", system_info)


# Global logger instance
_logger_instance: Optional[BotLogger] = None


def get_logger() -> BotLogger:
    """
    Get the global logger instance (singleton pattern)
    
    Returns:
        BotLogger: The logger instance
    """
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = BotLogger()
    return _logger_instance


def setup_logging():
    """Setup logging system"""
    logger = get_logger()
    logger.log_system_info()
    return logger


# Convenience functions
def log_info(message: str, **kwargs):
    """Log info message (convenience function)"""
    get_logger().info(message, **kwargs)


def log_error(message: str, **kwargs):
    """Log error message (convenience function)"""
    get_logger().error(message, **kwargs)


def log_audit(action: str, details: Dict[str, Any]):
    """Log audit event (convenience function)"""
    get_logger().audit(action, details)


# Export main classes and functions
__all__ = [
    "BotLogger",
    "get_logger",
    "setup_logging",
    "log_info",
    "log_error", 
    "log_audit"
]