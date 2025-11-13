"""Retry logic with exponential backoff for API calls.

This module provides a decorator for automatic retry with exponential backoff,
useful for handling transient network errors and API rate limits.
"""

import asyncio
import time
from functools import wraps
from typing import Any, Callable, Type, TypeVar

import aiohttp
import requests

from .logger import get_logger

logger = get_logger("retry_utils")

# Type variable for function return type
T = TypeVar("T")


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (
        aiohttp.ClientError,
        requests.RequestException,
        ConnectionError,
        TimeoutError,
    ),
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """Decorator for retrying function calls with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (default: 3)
        backoff_factor: Multiplier for delay between retries (default: 2.0)
            Delay sequence: 1s, 2s, 4s, 8s, ...
        exceptions: Tuple of exception types to catch and retry (default: network errors)

    Returns:
        Decorated function with retry logic

    Example:
        >>> @retry(max_attempts=3, backoff_factor=2)
        ... async def fetch_price():
        ...     async with aiohttp.ClientSession() as session:
        ...         async with session.get("https://api.example.com/price") as response:
        ...             return await response.json()

        This will retry up to 3 times with delays of 1s, 2s, 4s between attempts.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> T:
            """Async wrapper with retry logic."""
            attempt = 0
            while attempt < max_attempts:
                try:
                    result = await func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            "Function succeeded after retries",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                        )
                    return result
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(
                            "Function failed after max retries",
                            function=func.__name__,
                            max_attempts=max_attempts,
                            error=str(e),
                            error_type=type(e).__name__,
                        )
                        raise

                    # Calculate delay: 1s * backoff_factor^attempt
                    delay = backoff_factor**attempt
                    logger.warning(
                        "Function failed, retrying with backoff",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay_seconds=delay,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    await asyncio.sleep(delay)

            # Should never reach here due to raise in last attempt
            raise RuntimeError(f"Retry logic error for {func.__name__}")

        @wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> T:
            """Sync wrapper with retry logic."""
            attempt = 0
            while attempt < max_attempts:
                try:
                    result = func(*args, **kwargs)
                    if attempt > 0:
                        logger.info(
                            "Function succeeded after retries",
                            function=func.__name__,
                            attempt=attempt + 1,
                            max_attempts=max_attempts,
                        )
                    return result
                except exceptions as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        logger.error(
                            "Function failed after max retries",
                            function=func.__name__,
                            max_attempts=max_attempts,
                            error=str(e),
                            error_type=type(e).__name__,
                        )
                        raise

                    # Calculate delay: 1s * backoff_factor^attempt
                    delay = backoff_factor**attempt
                    logger.warning(
                        "Function failed, retrying with backoff",
                        function=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay_seconds=delay,
                        error=str(e),
                        error_type=type(e).__name__,
                    )
                    time.sleep(delay)

            # Should never reach here due to raise in last attempt
            raise RuntimeError(f"Retry logic error for {func.__name__}")

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper  # type: ignore
        return sync_wrapper  # type: ignore

    return decorator
