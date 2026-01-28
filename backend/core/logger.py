"""
Structured logging configuration for email finder.
Provides JSON-formatted logs for better observability.
"""
import logging
import json
import sys
from datetime import datetime
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format.

    Example output:
    {
        "timestamp": "2026-01-28T10:30:45.123Z",
        "level": "INFO",
        "logger": "email_finder",
        "message": "Email verification completed",
        "domain": "example.com",
        "status": "valid"
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra fields if provided
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logger(name: str, level: int = logging.INFO, json_format: bool = True) -> logging.Logger:
    """
    Setup a logger with structured output.

    Args:
        name: Logger name
        level: Logging level (default: INFO)
        json_format: Use JSON format (True) or plain text (False)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers
    logger.handlers.clear()

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # Set formatter
    if json_format:
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


class StructuredLogger:
    """
    Wrapper for structured logging with extra context.

    Usage:
        logger = StructuredLogger("email_finder")
        logger.info("Email found", domain="example.com", email="john@example.com")
    """

    def __init__(self, name: str, json_format: bool = True):
        self.logger = setup_logger(name, json_format=json_format)

    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with extra fields."""
        # Create a log record with extra fields
        extra = {"extra_fields": kwargs}
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs):
        """Log debug message with optional context."""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message with optional context."""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message with optional context."""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message with optional context."""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message with optional context."""
        self._log(logging.CRITICAL, message, **kwargs)


# Global logger instance for convenience
logger = StructuredLogger("email_finder", json_format=False)  # Plain text for development
