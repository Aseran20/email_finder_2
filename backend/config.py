"""
Configuration management for VPS Email Finder
Centralizes all environment variables and settings
"""
import os
from typing import Optional


class Config:
    """Application configuration loaded from environment variables"""

    # SMTP Settings
    SMTP_HOSTNAME: str = os.getenv("SMTP_HOSTNAME", "vps.auraia.ch")
    SMTP_FROM_EMAIL: str = os.getenv("SMTP_FROM_EMAIL", "verify@vps.auraia.ch")
    SMTP_TIMEOUT: int = int(os.getenv("SMTP_TIMEOUT", "10"))

    # Retry Logic
    SMTP_MAX_RETRIES: int = int(os.getenv("SMTP_MAX_RETRIES", "3"))
    SMTP_RETRY_DELAY_BASE: float = float(os.getenv("SMTP_RETRY_DELAY_BASE", "1.0"))  # seconds

    # MX Fallback
    MAX_MX_SERVERS: int = int(os.getenv("MAX_MX_SERVERS", "2"))

    # Rate Limiting
    RATE_LIMIT_DELAY: float = float(os.getenv("RATE_LIMIT_DELAY", "1.0"))  # seconds between checks

    # Cache Settings
    MX_CACHE_TTL: int = int(os.getenv("MX_CACHE_TTL", "3600"))  # 1 hour default

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./email_finder.db")

    # Application
    APP_VERSION: str = "v6"
    APP_NAME: str = "VPS Email Finder"

    @classmethod
    def get_smtp_timeout(cls) -> int:
        """Get SMTP timeout in seconds"""
        return cls.SMTP_TIMEOUT

    @classmethod
    def get_retry_delay(cls, attempt: int) -> float:
        """
        Calculate exponential backoff delay for retry attempt.

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds (1s → 2s → 4s)
        """
        return cls.SMTP_RETRY_DELAY_BASE * (2 ** attempt)

    @classmethod
    def should_retry_error(cls, error_message: str) -> bool:
        """
        Determine if an error is transient and should be retried.

        Args:
            error_message: The error message string

        Returns:
            True if error is transient (timeout, connection), False otherwise
        """
        transient_errors = [
            "timeout",
            "timed out",
            "connection refused",
            "connection reset",
            "connection closed",
            "temporarily unavailable",
            "network unreachable",
            "no route to host"
        ]

        error_lower = error_message.lower()

        # Don't retry user-not-found errors (550, 551, 553)
        permanent_codes = ["550", "551", "553"]
        if any(code in error_message for code in permanent_codes):
            return False

        # Retry on transient errors
        return any(transient in error_lower for transient in transient_errors)


# Global config instance
config = Config()
