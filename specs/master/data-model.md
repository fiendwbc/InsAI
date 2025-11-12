# Data Model: Solana AI Trading Bot

**Phase 1 Output** | **Date**: 2025-11-11

This document defines all data entities used in the trading bot system, implemented as Pydantic models for type safety and validation.

---

## Core Entities

### 1. MarketData

Represents collected price and technical indicator data from external sources.

**Purpose**: Store raw market data for LLM analysis and historical tracking.

**Fields**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `timestamp` | `datetime` | Yes | When data was collected (UTC) | Must be valid datetime |
| `source` | `str` | Yes | Data source identifier | One of: "jupiter", "coingecko", "coinkarma" |
| `sol_price_usd` | `float` | Yes | SOL price in USD/USDT | Must be > 0 |
| `volume_24h` | `float` | No | 24-hour trading volume (USD) | Must be >= 0 if present |
| `price_change_24h_pct` | `float` | No | 24-hour price change percentage | Range: -100 to +infinite |
| `quote_amount` | `int` | No | Jupiter quote output amount (if from Jupiter) | Must be > 0 if present |
| `pulse_index` | `float` | No | CoinKarma sentiment score (Pulse Index) | Range: typically 0-100 |
| `liquidity_index` | `float` | No | CoinKarma liquidity indicator for SOL | Must be >= 0 if present |
| `liquidity_value` | `float` | No | CoinKarma additional liquidity metric | Must be >= 0 if present |
| `metadata` | `Dict[str, Any]` | No | Additional data source-specific info | JSON-serializable dict |

**Pydantic Implementation**:
```python
from datetime import datetime
from typing import Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, field_validator

class MarketData(BaseModel):
    """Market data collected from price APIs."""

    timestamp: datetime = Field(
        description="When data was collected (UTC)"
    )
    source: Literal["jupiter", "coingecko", "coinkarma"] = Field(
        description="Data source identifier"
    )
    sol_price_usd: float = Field(
        gt=0,
        description="SOL price in USD/USDT"
    )
    volume_24h: Optional[float] = Field(
        default=None,
        ge=0,
        description="24-hour trading volume (USD)"
    )
    price_change_24h_pct: Optional[float] = Field(
        default=None,
        description="24-hour price change percentage"
    )
    quote_amount: Optional[int] = Field(
        default=None,
        gt=0,
        description="Jupiter quote output amount in smallest units"
    )
    pulse_index: Optional[float] = Field(
        default=None,
        description="CoinKarma sentiment score (Pulse Index)"
    )
    liquidity_index: Optional[float] = Field(
        default=None,
        ge=0,
        description="CoinKarma liquidity indicator for SOL"
    )
    liquidity_value: Optional[float] = Field(
        default=None,
        ge=0,
        description="CoinKarma additional liquidity metric"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional source-specific data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-11T10:30:00Z",
                "source": "jupiter",
                "sol_price_usd": 42.15,
                "volume_24h": 1250000000.0,
                "price_change_24h_pct": 3.2,
                "quote_amount": 42150000,
                "pulse_index": 68.5,
                "liquidity_index": 42.3,
                "liquidity_value": 38.7,
                "metadata": {"slippage_bps": 50}
            }
        }
```

**Storage**: Persisted to SQLite `market_data` table for historical analysis.

---

### 2. TradingSignal

LLM decision output indicating trading action and reasoning.

**Purpose**: Structured format for LLM trading decisions with confidence and rationale.

**Fields**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `timestamp` | `datetime` | Yes | When signal was generated (UTC) | Must be valid datetime |
| `signal` | `str` | Yes | Trading action | One of: "BUY", "SELL", "HOLD" |
| `confidence` | `float` | Yes | LLM confidence score | Range: 0.0 to 1.0 |
| `rationale` | `str` | Yes | Explanation for the decision | Min length: 10 chars |
| `suggested_amount_sol` | `float` | No | Suggested trade size (SOL) | Must be > 0 if present |
| `market_conditions` | `MarketConditions` | Yes | Key market factors in decision | Must include: trend, volume_assessment, volatility, risk_level |
| `llm_model` | `str` | Yes | LLM model used | e.g., "claude-3-5-sonnet-20241022" |
| `analysis_duration_sec` | `float` | No | Time taken for LLM analysis | Must be >= 0 |

**Pydantic Implementation**:
```python
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

class MarketConditions(BaseModel):
    """Market conditions assessment (matches llm-signals.schema.json contract)."""

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
    """LLM-generated trading signal with reasoning."""

    timestamp: datetime = Field(
        description="When signal was generated (UTC)"
    )
    signal: Literal["BUY", "SELL", "HOLD"] = Field(
        description="Trading action recommendation"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="LLM confidence score (0-1)"
    )
    rationale: str = Field(
        min_length=10,
        description="Explanation for trading decision"
    )
    suggested_amount_sol: Optional[float] = Field(
        default=None,
        gt=0,
        description="Recommended trade size in SOL"
    )
    market_conditions: MarketConditions = Field(
        description="Key market factors influencing decision (REQUIRED)"
    )
    llm_model: str = Field(
        description="LLM model identifier"
    )
    analysis_duration_sec: Optional[float] = Field(
        default=None,
        ge=0,
        description="LLM analysis time in seconds"
    )

    @field_validator('rationale')
    @classmethod
    def validate_rationale_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Rationale cannot be empty or whitespace")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-11T10:31:00Z",
                "signal": "BUY",
                "confidence": 0.78,
                "rationale": "SOL price is 3.2% up in 24h with strong volume, technical indicators show upward momentum. Good entry point for long position.",
                "suggested_amount_sol": 0.05,
                "market_conditions": {
                    "trend": "bullish",
                    "volume_assessment": "high",
                    "volatility": "medium",
                    "risk_level": "medium"
                },
                "llm_model": "claude-3-5-sonnet-20241022",
                "analysis_duration_sec": 2.3
            }
        }
```

**Storage**: Persisted to SQLite `trading_signals` table for audit trail.

---

### 3. TradeExecution

Record of an executed (or attempted) trade on Solana blockchain.

**Purpose**: Track all trade attempts with transaction details and outcomes.

**Fields**:

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `timestamp` | `datetime` | Yes | When trade was initiated (UTC) | Must be valid datetime |
| `signal` | `str` | Yes | Signal that triggered trade | One of: "BUY", "SELL" |
| `input_token` | `str` | Yes | Input token mint address | Valid Solana public key |
| `output_token` | `str` | Yes | Output token mint address | Valid Solana public key |
| `input_amount` | `float` | Yes | Input token amount | Must be > 0 |
| `output_amount` | `float` | No | Actual output received | Must be > 0 if present |
| `expected_output` | `float` | No | Expected output from quote | Must be > 0 if present |
| `slippage_bps` | `int` | Yes | Slippage tolerance (basis points) | Range: 0 to 10000 |
| `status` | `str` | Yes | Trade execution status | One of: "pending", "success", "failed", "dry_run" |
| `transaction_signature` | `str` | No | Solana transaction signature | 88-char base58 string if present |
| `error_message` | `str` | No | Error details if failed | Present only if status="failed" |
| `execution_duration_sec` | `float` | No | Time from submission to confirmation | Must be >= 0 if present |
| `gas_fee_sol` | `float` | No | Transaction fee paid (SOL) | Must be >= 0 if present |

**Pydantic Implementation**:
```python
from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator

class TradeExecution(BaseModel):
    """Record of trade execution on Solana blockchain."""

    timestamp: datetime = Field(
        description="When trade was initiated (UTC)"
    )
    signal: Literal["BUY", "SELL"] = Field(
        description="Trading signal that triggered execution"
    )
    input_token: str = Field(
        description="Input token mint address (Solana public key)"
    )
    output_token: str = Field(
        description="Output token mint address (Solana public key)"
    )
    input_amount: float = Field(
        gt=0,
        description="Input token amount"
    )
    output_amount: Optional[float] = Field(
        default=None,
        gt=0,
        description="Actual output amount received"
    )
    expected_output: Optional[float] = Field(
        default=None,
        gt=0,
        description="Expected output from Jupiter quote"
    )
    slippage_bps: int = Field(
        ge=0,
        le=10000,
        description="Slippage tolerance in basis points"
    )
    status: Literal["pending", "success", "failed", "dry_run"] = Field(
        description="Trade execution status"
    )
    transaction_signature: Optional[str] = Field(
        default=None,
        min_length=88,
        max_length=88,
        description="Solana transaction signature (base58)"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error details if execution failed"
    )
    execution_duration_sec: Optional[float] = Field(
        default=None,
        ge=0,
        description="Time from submission to confirmation (seconds)"
    )
    gas_fee_sol: Optional[float] = Field(
        default=None,
        ge=0,
        description="Transaction fee paid in SOL"
    )

    @field_validator('transaction_signature')
    @classmethod
    def validate_signature_format(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.isalnum():
            raise ValueError("Transaction signature must be alphanumeric base58")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2025-11-11T10:32:00Z",
                "signal": "BUY",
                "input_token": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
                "output_token": "So11111111111111111111111111111111111111112",
                "input_amount": 2.11,
                "output_amount": 0.0501,
                "expected_output": 0.0500,
                "slippage_bps": 50,
                "status": "success",
                "transaction_signature": "5J8Q...(88 chars)...xyz",
                "error_message": None,
                "execution_duration_sec": 12.5,
                "gas_fee_sol": 0.000005
            }
        }
```

**Storage**: Persisted to SQLite `trade_executions` table for compliance and analysis.

---

### 4. BotConfiguration

System configuration loaded from environment variables and defaults.

**Purpose**: Centralized configuration for all bot parameters.

**Fields**:

| Field | Type | Required | Description | Default |
|-------|------|----------|-------------|---------|
| `openrouter_api_key` | `str` | Yes | OpenRouter API key | From `OPENROUTER_API_KEY` env |
| `llm_provider` | `str` | No | LLM provider to use | `"claude"` (options: claude/gpt4/deepseek/gemini) |
| `llm_fallback_provider` | `str` | No | Fallback LLM provider | `"gpt4"` |
| `coinkarma_token` | `str` | Yes | CoinKarma auth token | From `COINKARMA_TOKEN` env |
| `coinkarma_device_id` | `str` | Yes | CoinKarma device ID | From `COINKARMA_DEVICE_ID` env |
| `solana_rpc_url` | `str` | Yes | Solana RPC endpoint | `https://api.mainnet-beta.solana.com` |
| `wallet_type` | `str` | No | Wallet type (MVP: private_key) | `"private_key"` |
| `wallet_private_key` | `str` | Yes | Wallet private key (base58) | From `WALLET_PRIVATE_KEY` env |
| `data_fetch_interval_sec` | `int` | No | Price data fetch interval | `60` |
| `llm_analysis_interval_sec` | `int` | No | LLM analysis interval | `60` |
| `max_trade_size_sol` | `float` | No | Maximum trade size per execution | `0.1` |
| `slippage_bps` | `int` | No | Default slippage tolerance | `50` (0.5%) |
| `max_trades_per_day` | `int` | No | Daily trade limit | `20` |
| `max_trades_per_hour` | `int` | No | Hourly trade limit | `5` |
| `circuit_breaker_price_change_pct` | `float` | No | Price change % to trigger pause | `20.0` |
| `dry_run_mode` | `bool` | No | Simulate trades without execution | `True` |
| `log_level` | `str` | No | Logging level | `"INFO"` |
| `database_path` | `str` | No | SQLite database file path | `"trading_bot.db"` |

**Pydantic Implementation**:
```python
from typing import Literal
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

class BotConfiguration(BaseSettings):
    """Trading bot configuration from environment variables."""

    # LLM API Keys (Multi-Provider via OpenRouter)
    openrouter_api_key: str = Field(
        description="OpenRouter API key for multi-LLM access"
    )
    llm_provider: Literal["claude", "gpt4", "deepseek", "gemini"] = Field(
        default="claude",
        description="Primary LLM provider"
    )
    llm_fallback_provider: Literal["claude", "gpt4", "deepseek", "gemini"] = Field(
        default="gpt4",
        description="Fallback LLM provider if primary fails"
    )

    # CoinKarma API
    coinkarma_token: str = Field(
        description="CoinKarma authentication token"
    )
    coinkarma_device_id: str = Field(
        description="CoinKarma device ID"
    )

    # Blockchain
    solana_rpc_url: str = Field(
        default="https://api.mainnet-beta.solana.com",
        description="Solana RPC endpoint"
    )

    # Wallet
    wallet_type: Literal["private_key"] = Field(
        default="private_key",
        description="Wallet type (MVP: private_key only)"
    )
    wallet_private_key: str = Field(
        description="Wallet private key in base58 format"
    )

    # Intervals
    data_fetch_interval_sec: int = Field(
        default=60,
        ge=10,
        description="Price data fetch interval in seconds"
    )
    llm_analysis_interval_sec: int = Field(
        default=60,
        ge=30,
        description="LLM analysis interval in seconds"
    )

    # Trading Limits
    max_trade_size_sol: float = Field(
        default=0.1,
        gt=0,
        le=10.0,
        description="Maximum SOL per trade"
    )
    slippage_bps: int = Field(
        default=50,
        ge=0,
        le=1000,
        description="Default slippage tolerance (basis points)"
    )
    max_trades_per_day: int = Field(
        default=20,
        ge=1,
        le=1000,
        description="Maximum trades allowed per day"
    )
    max_trades_per_hour: int = Field(
        default=5,
        ge=1,
        le=100,
        description="Maximum trades allowed per hour"
    )

    # Circuit Breaker
    circuit_breaker_price_change_pct: float = Field(
        default=20.0,
        gt=0,
        description="Price change % to trigger circuit breaker"
    )

    # Safety
    dry_run_mode: bool = Field(
        default=True,
        description="Run in simulation mode without real trades"
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )

    # Storage
    database_path: str = Field(
        default="trading_bot.db",
        description="SQLite database file path"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
```

**Loading**: Automatically loaded from `.env` file using Pydantic Settings.

---

## Entity Relationships

```
MarketData (collected every 60s)
    ↓
TradingSignal (generated by LLM)
    ↓
TradeExecution (if signal != HOLD)
```

**Flow**:
1. `MarketData` collected from Jupiter/CoinGecko (price) + CoinKarma (sentiment/liquidity)
2. Latest `MarketData` sent to LLM → produces `TradingSignal`
3. If `TradingSignal.signal != "HOLD"` → create `TradeExecution`
4. All entities persisted to SQLite for audit trail

---

## SQLite Schema

### Table: `market_data`
```sql
CREATE TABLE market_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    source TEXT NOT NULL,
    sol_price_usd REAL NOT NULL,
    volume_24h REAL,
    price_change_24h_pct REAL,
    quote_amount INTEGER,
    pulse_index REAL,
    liquidity_index REAL,
    liquidity_value REAL,
    metadata JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_market_data_timestamp ON market_data(timestamp DESC);
CREATE INDEX idx_market_data_source ON market_data(source);
```

### Table: `trading_signals`
```sql
CREATE TABLE trading_signals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    signal TEXT NOT NULL CHECK(signal IN ('BUY', 'SELL', 'HOLD')),
    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
    rationale TEXT NOT NULL,
    suggested_amount_sol REAL,
    market_conditions JSON,
    llm_model TEXT NOT NULL,
    analysis_duration_sec REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trading_signals_timestamp ON trading_signals(timestamp DESC);
CREATE INDEX idx_trading_signals_signal ON trading_signals(signal);
```

### Table: `trade_executions`
```sql
CREATE TABLE trade_executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    signal TEXT NOT NULL CHECK(signal IN ('BUY', 'SELL')),
    input_token TEXT NOT NULL,
    output_token TEXT NOT NULL,
    input_amount REAL NOT NULL,
    output_amount REAL,
    expected_output REAL,
    slippage_bps INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'success', 'failed', 'dry_run')),
    transaction_signature TEXT UNIQUE,
    error_message TEXT,
    execution_duration_sec REAL,
    gas_fee_sol REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trade_executions_timestamp ON trade_executions(timestamp DESC);
CREATE INDEX idx_trade_executions_status ON trade_executions(status);
CREATE INDEX idx_trade_executions_signature ON trade_executions(transaction_signature);
```

---

## Validation Rules Summary

| Entity | Critical Validations |
|--------|----------------------|
| `MarketData` | Price > 0, timestamp valid, source in allowed list |
| `TradingSignal` | Signal in [BUY/SELL/HOLD], confidence 0-1, rationale not empty |
| `TradeExecution` | Amount > 0, slippage 0-10000 bps, signature 88 chars if present |
| `BotConfiguration` | All secrets present, trade limits reasonable (max 10 SOL) |

**Error Handling**: All Pydantic validation errors are caught and logged with full context.

---

## Usage Example

```python
from datetime import datetime, timezone
from models import MarketData, TradingSignal, TradeExecution

# Create market data
market_data = MarketData(
    timestamp=datetime.now(timezone.utc),
    source="jupiter",
    sol_price_usd=42.15,
    volume_24h=1_250_000_000.0,
    price_change_24h_pct=3.2
)

# Create trading signal
signal = TradingSignal(
    timestamp=datetime.now(timezone.utc),
    signal="BUY",
    confidence=0.78,
    rationale="Strong upward momentum with high volume",
    suggested_amount_sol=0.05,
    llm_model="claude-3-5-sonnet-20241022"
)

# Create trade execution
trade = TradeExecution(
    timestamp=datetime.now(timezone.utc),
    signal="BUY",
    input_token="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    output_token="So11111111111111111111111111111111111111112",
    input_amount=2.11,
    slippage_bps=50,
    status="pending"
)

# All models are JSON-serializable
print(market_data.model_dump_json(indent=2))
```

---

**Status**: Data model design complete ✅
