"""LangChain tools for market data access.

Provides tools for:
- Fetching current SOL price
- Getting complete market data (price, volume, sentiment)
- Querying CoinKarma indicators (Pulse Index, Liquidity)
"""

import json
from datetime import datetime, timezone
from typing import Any

from langchain_core.tools import tool

# Global dependencies (set by service layer)
_data_collector: Any = None


def set_data_collector(collector: Any) -> None:
    """Set data collector instance for tools.

    Args:
        collector: DataCollector instance
    """
    global _data_collector
    _data_collector = collector


@tool
async def fetch_price() -> str:
    """Fetch current SOL/USD price from Jupiter or CoinGecko.

    This tool fetches the most accurate real-time price for SOL.
    Jupiter is tried first (most accurate for trading), with CoinGecko as fallback.

    Returns:
        JSON string with:
        - sol_price_usd: Current SOL price in USD
        - source: Data source (jupiter or coingecko)
        - timestamp: When the price was fetched

    Example:
        {
          "sol_price_usd": 142.35,
          "source": "jupiter",
          "timestamp": "2025-01-14T10:30:00Z"
        }
    """
    if _data_collector is None:
        return json.dumps({"error": "Data collector not initialized"})

    try:
        # Try Jupiter first
        try:
            price = await _data_collector.fetch_price_from_jupiter()
            return json.dumps({
                "sol_price_usd": price,
                "source": "jupiter",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
        except Exception:
            # Fallback to CoinGecko
            data = await _data_collector.fetch_price_from_coingecko()
            return json.dumps({
                "sol_price_usd": data["price"],
                "source": "coingecko",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

    except Exception as e:
        return json.dumps({"error": f"Failed to fetch price: {str(e)}"})


@tool
async def get_market_data() -> str:
    """Get comprehensive market data including price, volume, and sentiment indicators.

    This tool provides a complete market overview by combining data from:
    - Jupiter: Real-time swap prices
    - CoinGecko: 24h volume and price changes
    - CoinKarma: Sentiment (Pulse Index) and Liquidity indicators

    Returns:
        JSON string with complete market snapshot:
        - sol_price_usd: Current SOL price
        - volume_24h: 24-hour trading volume in USD
        - price_change_24h_pct: 24-hour price change percentage
        - pulse_index: CoinKarma sentiment indicator (0-100)
        - liquidity_index: CoinKarma liquidity score (0-100)
        - liquidity_value: Absolute liquidity value
        - source: Primary data source
        - timestamp: Data collection time

    Example:
        {
          "sol_price_usd": 142.35,
          "volume_24h": 2847593102.45,
          "price_change_24h_pct": 5.23,
          "pulse_index": 67.5,
          "liquidity_index": 72.3,
          "liquidity_value": 1893247.82,
          "source": "jupiter",
          "timestamp": "2025-01-14T10:30:00Z"
        }
    """
    if _data_collector is None:
        return json.dumps({"error": "Data collector not initialized"})

    try:
        market_data = await _data_collector.collect_market_data()

        return json.dumps({
            "sol_price_usd": market_data.sol_price_usd,
            "volume_24h": market_data.volume_24h,
            "price_change_24h_pct": market_data.price_change_24h_pct,
            "pulse_index": market_data.pulse_index,
            "liquidity_index": market_data.liquidity_index,
            "liquidity_value": market_data.liquidity_value,
            "source": market_data.source,
            "timestamp": market_data.timestamp.isoformat(),
        })

    except Exception as e:
        return json.dumps({"error": f"Failed to collect market data: {str(e)}"})


@tool
async def fetch_karma_indicators() -> str:
    """Fetch CoinKarma sentiment and liquidity indicators for SOL.

    CoinKarma provides two key indicators:
    - Pulse Index: Market sentiment indicator (0-100)
      Higher values indicate stronger bullish sentiment
    - Liquidity Index: Market liquidity score (0-100)
      Higher values indicate better market depth and lower slippage

    Returns:
        JSON string with:
        - pulse_index: Sentiment indicator (0-100, or null if unavailable)
        - liquidity_index: Liquidity score (0-100, or null if unavailable)
        - liquidity_value: Absolute liquidity value in USD (or null)
        - timestamp: When indicators were fetched

    Example:
        {
          "pulse_index": 67.5,
          "liquidity_index": 72.3,
          "liquidity_value": 1893247.82,
          "timestamp": "2025-01-14T10:30:00Z"
        }

    Note:
        CoinKarma indicators may not always be available. Check for null values.
    """
    if _data_collector is None:
        return json.dumps({"error": "Data collector not initialized"})

    try:
        # Import here to avoid circular dependency
        from ..coinkarma import fetch_liquidity_index, fetch_pulse_index
        from datetime import datetime, timezone

        pulse_index = await fetch_pulse_index(_data_collector.config)
        liquidity_data = await fetch_liquidity_index(_data_collector.config)

        return json.dumps({
            "pulse_index": pulse_index,
            "liquidity_index": liquidity_data.get("liquidity_index"),
            "liquidity_value": liquidity_data.get("liquidity_value"),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    except Exception as e:
        return json.dumps({
            "error": f"Failed to fetch CoinKarma indicators: {str(e)}",
            "pulse_index": None,
            "liquidity_index": None,
            "liquidity_value": None,
        })
