"""CoinKarma integration adapter for BotConfiguration.

This module provides async wrappers around the existing CoinKarma API functions,
making them compatible with the BotConfiguration system.
"""

import asyncio
from datetime import datetime
from typing import Any

from ..config import BotConfiguration
from .karmafetch import get_liq_index, get_pulse_index


def get_current_date_str() -> str:
    """Get current date in YYYY-MM-DD format."""
    return datetime.now().strftime("%Y-%m-%d")


async def fetch_pulse_index(config: BotConfiguration) -> float | None:
    """Fetch latest Pulse Index value from CoinKarma.

    Args:
        config: Bot configuration with CoinKarma credentials

    Returns:
        Latest pulse index value, or None if unavailable

    Raises:
        Exception: If API call fails
    """
    date = get_current_date_str()

    # Run blocking API call in thread pool
    data = await asyncio.to_thread(
        get_pulse_index,
        date,
        date,
        config.coinkarma_token,
        config.coinkarma_device_id,
    )

    # Return latest value
    if data and len(data) > 0:
        return data[-1]["value"]
    return None


async def fetch_liquidity_index(config: BotConfiguration, symbol: str = "solusdt") -> dict[str, Any]:
    """Fetch liquidity index data for a symbol from CoinKarma.

    Args:
        config: Bot configuration with CoinKarma credentials
        symbol: Trading pair symbol (default: solusdt)

    Returns:
        Dictionary with:
        - liquidity_index: Latest liquidity score (0-100)
        - liquidity_value: Absolute liquidity value

    Raises:
        Exception: If API call fails
    """
    date = get_current_date_str()

    # Run blocking API call in thread pool
    data = await asyncio.to_thread(
        get_liq_index,
        symbol,
        date,
        date,
        config.coinkarma_token,
        config.coinkarma_device_id,
    )

    # Extract latest values
    if data and len(data) > 0:
        latest = data[-1]
        return {
            "liquidity_index": latest.get("liq"),
            "liquidity_value": latest.get("value"),
        }

    return {
        "liquidity_index": None,
        "liquidity_value": None,
    }
