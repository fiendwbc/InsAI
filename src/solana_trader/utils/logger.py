"""Structured JSON logging setup using structlog.

This module provides a configured logger with JSON output format, including
timestamp, level, service, and trace_id fields for easy monitoring and debugging.
"""

import logging
import os
import sys
from typing import Any

import structlog


def configure_logger() -> structlog.BoundLogger:
    """Configure and return a structured logger with JSON output format.

    The logger includes the following fields in each log entry:
    - timestamp: ISO 8601 format timestamp
    - level: Log level (DEBUG, INFO, WARNING, ERROR)
    - service: Service name (solana_trader)
    - event: Log message
    - Additional context fields can be bound to the logger

    Returns:
        Configured structlog BoundLogger instance

    Example:
        >>> logger = configure_logger()
        >>> logger.info("Market data fetched", price_usd=42.15, source="jupiter")
        {"timestamp": "2025-11-13T10:30:00Z", "level": "info", "service": "solana_trader",
         "event": "Market data fetched", "price_usd": 42.15, "source": "jupiter"}
    """
    # Get log level from environment (default: INFO)
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level_int = getattr(logging, log_level, logging.INFO)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level_int,
    )

    # Configure structlog processors
    structlog.configure(
        processors=[
            # Add log level name
            structlog.stdlib.add_log_level,
            # Add logger name
            structlog.stdlib.add_logger_name,
            # Add timestamp in ISO 8601 format
            structlog.processors.TimeStamper(fmt="iso"),
            # Add caller info (file, line, function)
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ]
            ),
            # Stack unwinder for exceptions
            structlog.processors.StackInfoRenderer(),
            # Format exception tracebacks
            structlog.processors.format_exc_info,
            # Render as JSON
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Create and return bound logger with service name
    logger = structlog.get_logger().bind(service="solana_trader")

    return logger


# Global logger instance
logger = configure_logger()


def get_logger(name: str | None = None, **initial_values: Any) -> structlog.BoundLogger:
    """Get a logger instance with optional name and initial bound values.

    Args:
        name: Optional logger name (defaults to "solana_trader")
        **initial_values: Initial key-value pairs to bind to the logger

    Returns:
        BoundLogger with initial values bound

    Example:
        >>> logger = get_logger("trade_executor", component="jupiter")
        >>> logger.info("Trade executed", tx_signature="5J8Q...")
    """
    if name:
        return structlog.get_logger(name).bind(service="solana_trader", **initial_values)
    return logger.bind(**initial_values)
