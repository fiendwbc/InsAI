"""Market data collection service for price and indicators.

This module provides unified data collection from multiple sources:
- Jupiter: Real-time swap prices
- CoinGecko: Market data and 24h volume
- CoinKarma: Sentiment (Pulse Index) and Liquidity indicators
"""

from datetime import datetime, timezone
from typing import Any

import aiohttp
import requests

from ..config import BotConfiguration
from ..models.market_data import MarketData
from ..utils.logger import get_logger
from ..utils.retry import retry

logger = get_logger("data_collector")

# Token addresses
SOL_MINT = "So11111111111111111111111111111111111111112"
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"

# API endpoints
JUPITER_QUOTE_URL = "https://quote-api.jup.ag/v6/quote"
COINGECKO_PRICE_URL = "https://api.coingecko.com/api/v3/simple/price"


class DataCollector:
    """Unified market data collector from multiple sources."""

    def __init__(self, config: BotConfiguration):
        """Initialize data collector.

        Args:
            config: Bot configuration
        """
        self.config = config
        logger.info("Data collector initialized")

    @retry(max_attempts=3, backoff_factor=2)
    async def fetch_price_from_jupiter(self) -> float:
        """Fetch SOL/USDT price from Jupiter quote API.

        Returns:
            SOL price in USDT

        Raises:
            aiohttp.ClientError: If API call fails
        """
        try:
            # Query for 1 SOL → USDT swap
            params = {
                "inputMint": SOL_MINT,
                "outputMint": USDT_MINT,
                "amount": str(int(1e9)),  # 1 SOL in lamports
                "slippageBps": "50",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(JUPITER_QUOTE_URL, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                    # Parse output amount (USDT has 6 decimals)
                    out_amount = int(data["outAmount"])
                    price = out_amount / 1e6

                    logger.info("Jupiter price fetched", sol_price_usd=price)
                    return price

        except Exception as e:
            logger.error("Failed to fetch price from Jupiter", error=str(e))
            raise

    @retry(max_attempts=3, backoff_factor=2)
    async def fetch_price_from_coingecko(self) -> dict[str, Any]:
        """Fetch SOL market data from CoinGecko API.

        Returns:
            Dictionary with price, volume, and price change data

        Raises:
            aiohttp.ClientError: If API call fails
        """
        try:
            params = {
                "ids": "solana",
                "vs_currencies": "usd",
                "include_24hr_vol": "true",
                "include_24hr_change": "true",
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(COINGECKO_PRICE_URL, params=params) as response:
                    response.raise_for_status()
                    data = await response.json()

                    solana_data = data.get("solana", {})
                    result = {
                        "price": solana_data.get("usd", 0),
                        "volume_24h": solana_data.get("usd_24h_vol", 0),
                        "price_change_24h_pct": solana_data.get("usd_24h_change", 0),
                    }

                    logger.info(
                        "CoinGecko data fetched",
                        sol_price_usd=result["price"],
                        volume_24h=result["volume_24h"],
                    )
                    return result

        except Exception as e:
            logger.error("Failed to fetch data from CoinGecko", error=str(e))
            raise

    async def collect_market_data(self) -> MarketData:
        """Collect unified market data from all available sources.

        This method tries Jupiter first (most accurate for trading),
        falls back to CoinGecko if Jupiter fails, and enriches with
        CoinKarma indicators if available.

        Returns:
            MarketData instance with all available data

        Raises:
            Exception: If all data sources fail
        """
        timestamp = datetime.now(timezone.utc)
        price = None
        volume_24h = None
        price_change_24h_pct = None
        source = None
        metadata: dict[str, Any] = {}

        # Try Jupiter first (most accurate for swap prices)
        try:
            price = await self.fetch_price_from_jupiter()
            source = "jupiter"
            logger.info("Using Jupiter as primary price source", price=price)
        except Exception as e:
            logger.warning("Jupiter fetch failed, falling back to CoinGecko", error=str(e))

            # Fallback to CoinGecko
            try:
                coingecko_data = await self.fetch_price_from_coingecko()
                price = coingecko_data["price"]
                volume_24h = coingecko_data["volume_24h"]
                price_change_24h_pct = coingecko_data["price_change_24h_pct"]
                source = "coingecko"
                logger.info("Using CoinGecko as fallback price source", price=price)
            except Exception as cg_error:
                logger.error("Both Jupiter and CoinGecko failed", error=str(cg_error))
                raise RuntimeError(
                    f"Failed to fetch price from any source. Jupiter: {e}, CoinGecko: {cg_error}"
                )

        # Try to enrich with CoinKarma indicators (optional, don't fail if unavailable)
        pulse_index = None
        liquidity_index = None
        liquidity_value = None

        try:
            # Import here to avoid circular dependency
            from ..coinkarma.karmafetch import fetch_liquidity_index, fetch_pulse_index

            pulse_index = await fetch_pulse_index(self.config)
            liquidity_data = await fetch_liquidity_index(self.config)
            liquidity_index = liquidity_data.get("liquidity_index")
            liquidity_value = liquidity_data.get("liquidity_value")

            logger.info(
                "CoinKarma indicators fetched",
                pulse_index=pulse_index,
                liquidity_index=liquidity_index,
            )
        except Exception as karma_error:
            logger.warning(
                "Failed to fetch CoinKarma indicators (optional)",
                error=str(karma_error),
            )
            # Don't fail if CoinKarma is unavailable, just log warning

        # Create MarketData instance
        market_data = MarketData(
            timestamp=timestamp,
            source=source,
            sol_price_usd=price,
            volume_24h=volume_24h,
            price_change_24h_pct=price_change_24h_pct,
            pulse_index=pulse_index,
            liquidity_index=liquidity_index,
            liquidity_value=liquidity_value,
            metadata=metadata,
        )

        logger.info(
            "Market data collected successfully",
            source=source,
            price=price,
            has_volume=volume_24h is not None,
            has_karma=pulse_index is not None,
        )

        return market_data


# Standalone functions for backward compatibility
@retry(max_attempts=3, backoff_factor=2)
async def fetch_price_from_jupiter() -> float:
    """Fetch SOL/USDT price from Jupiter (standalone function).

    Returns:
        SOL price in USDT
    """
    params = {
        "inputMint": SOL_MINT,
        "outputMint": USDT_MINT,
        "amount": str(int(1e9)),
        "slippageBps": "50",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(JUPITER_QUOTE_URL, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            out_amount = int(data["outAmount"])
            return out_amount / 1e6


@retry(max_attempts=3, backoff_factor=2)
async def fetch_price_from_coingecko() -> float:
    """Fetch SOL/USD price from CoinGecko (standalone function).

    Returns:
        SOL price in USD
    """
    params = {
        "ids": "solana",
        "vs_currencies": "usd",
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(COINGECKO_PRICE_URL, params=params) as response:
            response.raise_for_status()
            data = await response.json()
            return data["solana"]["usd"]
