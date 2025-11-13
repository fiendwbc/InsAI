"""Trading signal data model for LLM-generated trading decisions."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class MarketConditions(BaseModel):
    """Market conditions assessment from LLM analysis."""

    trend: Literal["bullish", "bearish", "neutral", "unknown"] = Field(
        description="Current market trend assessment"
    )
    volume_assessment: Literal["high", "medium", "low", "unknown"] = Field(
        description="24h volume assessment relative to historical average"
    )
    volatility: Literal["high", "medium", "low", "unknown"] = Field(
        description="Recent price volatility assessment"
    )
    risk_level: Literal["high", "medium", "low"] = Field(
        description="Assessed risk level for this trading signal"
    )

    class Config:
        extra = "forbid"  # Matches JSON schema additionalProperties: false


class TradingSignal(BaseModel):
    """LLM-generated trading signal with reasoning.

    This model represents the output from LLM analysis, combining the
    LLM-generated fields (signal, confidence, rationale, market_conditions)
    with server-side metadata (timestamp, llm_model, analysis_duration_sec).
    """

    timestamp: datetime = Field(description="When signal was generated (UTC)")
    signal: Literal["BUY", "SELL", "HOLD"] = Field(description="Trading action recommendation")
    confidence: float = Field(ge=0.0, le=1.0, description="LLM confidence score (0-1)")
    rationale: str = Field(min_length=10, description="Explanation for trading decision")
    suggested_amount_sol: Optional[float] = Field(
        default=None, gt=0, description="Recommended trade size in SOL"
    )
    market_conditions: MarketConditions = Field(
        description="Key market factors influencing decision"
    )
    llm_model: str = Field(description="LLM model identifier")
    analysis_duration_sec: Optional[float] = Field(
        default=None, ge=0, description="LLM analysis time in seconds"
    )

    @field_validator("rationale")
    @classmethod
    def validate_rationale_not_empty(cls, v: str) -> str:
        """Ensure rationale is not empty or whitespace."""
        if not v.strip():
            raise ValueError("Rationale cannot be empty or whitespace")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-13T10:31:00Z",
                "signal": "BUY",
                "confidence": 0.78,
                "rationale": "SOL price is 3.2% up in 24h with strong volume, technical indicators show upward momentum. Good entry point for long position.",
                "suggested_amount_sol": 0.05,
                "market_conditions": {
                    "trend": "bullish",
                    "volume_assessment": "high",
                    "volatility": "medium",
                    "risk_level": "medium",
                },
                "llm_model": "anthropic/claude-3.5-sonnet",
                "analysis_duration_sec": 2.3,
            }
        }
