"""Market data model for price and technical indicators."""

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class MarketData(BaseModel):
    """Market data collected from price APIs.

    This model stores price data from various sources (Jupiter, CoinGecko)
    along with technical indicators from CoinKarma.
    """

    timestamp: datetime = Field(description="When data was collected (UTC)")
    source: Literal["jupiter", "coingecko", "coinkarma"] = Field(
        description="Data source identifier"
    )
    sol_price_usd: float = Field(gt=0, description="SOL price in USD/USDT")
    volume_24h: Optional[float] = Field(
        default=None, ge=0, description="24-hour trading volume (USD)"
    )
    price_change_24h_pct: Optional[float] = Field(
        default=None, description="24-hour price change percentage"
    )
    quote_amount: Optional[int] = Field(
        default=None, gt=0, description="Jupiter quote output amount in smallest units"
    )
    pulse_index: Optional[float] = Field(
        default=None, description="CoinKarma sentiment score (Pulse Index)"
    )
    liquidity_index: Optional[float] = Field(
        default=None, ge=0, description="CoinKarma liquidity indicator for SOL"
    )
    liquidity_value: Optional[float] = Field(
        default=None, ge=0, description="CoinKarma additional liquidity metric"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional source-specific data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-13T10:30:00Z",
                "source": "jupiter",
                "sol_price_usd": 42.15,
                "volume_24h": 1250000000.0,
                "price_change_24h_pct": 3.2,
                "quote_amount": 42150000,
                "pulse_index": 68.5,
                "liquidity_index": 42.3,
                "liquidity_value": 38.7,
                "metadata": {"slippage_bps": 50},
            }
        }
