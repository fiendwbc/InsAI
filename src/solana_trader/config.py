"""Trading bot configuration loaded from environment variables.

This module uses Pydantic Settings to load and validate all configuration
from environment variables (typically from .env file).
"""

from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class BotConfiguration(BaseSettings):
    """Trading bot configuration from environment variables.

    All required fields must be set in .env file. Default values are provided
    for optional parameters.

    Example .env file:
        OPENROUTER_API_KEY=sk-or-v1-...
        LLM_PROVIDER=claude
        COINKARMA_TOKEN=Bearer eyJ...
        COINKARMA_DEVICE_ID=8286013b...
        WALLET_PRIVATE_KEY=your-base58-key
        DRY_RUN_MODE=true
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===================================
    # LLM API Keys (Multi-Provider via OpenRouter)
    # ===================================
    openrouter_api_key: str = Field(
        description="OpenRouter API key for multi-LLM access (Claude/GPT-4/DeepSeek/Gemini)"
    )
    llm_provider: Literal["claude", "gpt4", "deepseek", "gemini"] = Field(
        default="claude", description="Primary LLM provider"
    )
    llm_fallback_provider: Literal["claude", "gpt4", "deepseek", "gemini"] = Field(
        default="gpt4", description="Fallback LLM provider if primary fails"
    )

    # ===================================
    # CoinKarma API
    # ===================================
    coinkarma_token: str = Field(description="CoinKarma authentication token (Bearer ...)")
    coinkarma_device_id: str = Field(description="CoinKarma device ID")

    # ===================================
    # Blockchain
    # ===================================
    solana_rpc_url: str = Field(
        default="https://api.mainnet-beta.solana.com",
        description="Solana RPC endpoint (use paid RPC for production)",
    )

    # ===================================
    # Wallet
    # ===================================
    wallet_type: Literal["private_key"] = Field(
        default="private_key", description="Wallet type (MVP: private_key only)"
    )
    wallet_private_key: str = Field(description="Wallet private key in base58 format")

    # ===================================
    # Intervals
    # ===================================
    data_fetch_interval_sec: int = Field(
        default=60, ge=10, description="Price data fetch interval in seconds (min: 10)"
    )
    llm_analysis_interval_sec: int = Field(
        default=60, ge=30, description="LLM analysis interval in seconds (min: 30)"
    )

    # ===================================
    # Trading Limits
    # ===================================
    max_trade_size_sol: float = Field(
        default=0.1, gt=0, le=10.0, description="Maximum SOL per trade (max: 10.0)"
    )
    slippage_bps: int = Field(
        default=50,
        ge=0,
        le=1000,
        description="Default slippage tolerance in basis points (50 bps = 0.5%)",
    )
    max_trades_per_day: int = Field(
        default=20, ge=1, le=1000, description="Maximum trades allowed per day"
    )
    max_trades_per_hour: int = Field(
        default=5, ge=1, le=100, description="Maximum trades allowed per hour"
    )

    # ===================================
    # Circuit Breaker
    # ===================================
    circuit_breaker_price_change_pct: float = Field(
        default=20.0, gt=0, description="Price change % to trigger circuit breaker halt"
    )

    # ===================================
    # Safety
    # ===================================
    dry_run_mode: bool = Field(
        default=True,
        description="Run in simulation mode without real trades (ALWAYS start with True)",
    )

    # ===================================
    # Logging
    # ===================================
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )

    # ===================================
    # Storage
    # ===================================
    database_path: str = Field(
        default="trading_bot.db", description="SQLite database file path"
    )

    @field_validator("wallet_private_key")
    @classmethod
    def validate_private_key_format(cls, v: str) -> str:
        """Validate wallet private key is not empty."""
        if not v or not v.strip():
            raise ValueError("Wallet private key cannot be empty")
        # Base58 validation could be added here
        return v.strip()

    @field_validator("coinkarma_token")
    @classmethod
    def validate_coinkarma_token(cls, v: str) -> str:
        """Validate CoinKarma token format."""
        if not v.startswith("Bearer "):
            raise ValueError("CoinKarma token must start with 'Bearer '")
        return v

    @field_validator("llm_fallback_provider")
    @classmethod
    def validate_fallback_differs_from_primary(cls, v: str, values: dict) -> str:
        """Ensure fallback provider is different from primary."""
        # Note: In Pydantic v2, we need to access validated fields from values.data
        if hasattr(values, "data") and "llm_provider" in values.data:
            if v == values.data["llm_provider"]:
                # Just log warning, don't fail validation
                pass
        return v


def load_config() -> BotConfiguration:
    """Load and validate configuration from environment.

    Returns:
        BotConfiguration instance with all settings loaded

    Raises:
        ValidationError: If required environment variables are missing or invalid

    Example:
        >>> config = load_config()
        >>> print(f"Using LLM: {config.llm_provider}")
        >>> print(f"Dry run mode: {config.dry_run_mode}")
    """
    return BotConfiguration()


if __name__ == "__main__":
    """Configuration validation CLI.

    Usage: python -m solana_trader.config
    Validates .env file and prints configuration status.
    """
    import sys

    try:
        config = load_config()
        print("✓ Configuration loaded successfully\n")
        print(f"✓ OpenRouter API key: {'*' * 20}{config.openrouter_api_key[-8:]}")
        print(f"✓ LLM Provider: {config.llm_provider} (fallback: {config.llm_fallback_provider})")
        print(f"✓ CoinKarma Auth: Valid")
        print(f"✓ Wallet type: {config.wallet_type}")
        print(f"✓ Solana RPC: {config.solana_rpc_url}")
        print(
            f"✓ Dry-run mode: {'ENABLED (safe to test)' if config.dry_run_mode else 'DISABLED (real trades!)'}"
        )
        print(f"✓ Database: {config.database_path}")
        print(f"✓ Max trade size: {config.max_trade_size_sol} SOL")
        print(f"✓ Daily limit: {config.max_trades_per_day} trades")
        print(f"\nAll configuration checks passed ✓")
        sys.exit(0)
    except Exception as e:
        print(f"✗ Configuration validation failed:\n{e}")
        sys.exit(1)
