"""Trade execution data model for Solana blockchain transactions."""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


class TradeExecution(BaseModel):
    """Record of trade execution on Solana blockchain.

    This model tracks all trade attempts including successful trades, failed
    attempts, and dry-run simulations for testing.
    """

    timestamp: datetime = Field(description="When trade was initiated (UTC)")
    signal: Literal["BUY", "SELL"] = Field(description="Trading signal that triggered execution")
    input_token: str = Field(description="Input token mint address (Solana public key)")
    output_token: str = Field(description="Output token mint address (Solana public key)")
    input_amount: float = Field(gt=0, description="Input token amount")
    output_amount: Optional[float] = Field(
        default=None, gt=0, description="Actual output amount received"
    )
    expected_output: Optional[float] = Field(
        default=None, gt=0, description="Expected output from Jupiter quote"
    )
    slippage_bps: int = Field(
        ge=0, le=10000, description="Slippage tolerance in basis points (50 bps = 0.5%)"
    )
    status: Literal["pending", "success", "failed", "dry_run"] = Field(
        description="Trade execution status"
    )
    transaction_signature: Optional[str] = Field(
        default=None,
        min_length=88,
        max_length=88,
        description="Solana transaction signature (base58, 88 chars)",
    )
    error_message: Optional[str] = Field(
        default=None, description="Error details if execution failed"
    )
    execution_duration_sec: Optional[float] = Field(
        default=None, ge=0, description="Time from submission to confirmation (seconds)"
    )
    gas_fee_sol: Optional[float] = Field(
        default=None, ge=0, description="Transaction fee paid in SOL"
    )

    @field_validator("transaction_signature")
    @classmethod
    def validate_signature_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate transaction signature is alphanumeric base58."""
        if v is not None and not v.isalnum():
            raise ValueError("Transaction signature must be alphanumeric base58")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-13T10:32:00Z",
                "signal": "BUY",
                "input_token": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDT
                "output_token": "So11111111111111111111111111111111111111112",  # SOL
                "input_amount": 2.11,
                "output_amount": 0.0501,
                "expected_output": 0.0500,
                "slippage_bps": 50,
                "status": "success",
                "transaction_signature": "5J8QyP..." + "x" * 80,  # 88 chars total
                "error_message": None,
                "execution_duration_sec": 12.5,
                "gas_fee_sol": 0.000005,
            }
        }
