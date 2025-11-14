"""LLM-controlled trading CLI script.

This script allows users to interact with the trading bot using natural language.
The LLM agent will use tools (get_wallet_balance, solana_trade) to execute trades.

Usage: python -m solana_trader.scripts.llm_trade --prompt "Your instruction" --dry-run
"""

import argparse
import asyncio
import sys

from ..config import load_config
from ..services.llm_analyzer import LLMAnalyzer
from ..services.storage import StorageService
from ..services.trade_executor import TradeExecutor
from ..utils.logger import get_logger
from ..wallet.manager import WalletManager

logger = get_logger("llm_trade_cli")


async def main() -> None:
    """Main entry point for LLM trading CLI."""
    parser = argparse.ArgumentParser(
        description="LLM-controlled trading CLI for Solana trading bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check wallet balance
  python -m solana_trader.scripts.llm_trade --prompt "Check my wallet balance"

  # Request trade analysis (dry-run)
  python -m solana_trader.scripts.llm_trade --prompt "Should I buy SOL right now?" --dry-run

  # Execute trade with LLM reasoning (dry-run)
  python -m solana_trader.scripts.llm_trade --prompt "Buy 0.01 SOL worth of tokens in dry-run mode"

  # Real trade with confirmation (⚠️ COSTS REAL MONEY)
  python -m solana_trader.scripts.llm_trade --prompt "Buy 0.01 SOL. Test with dry-run first, then ask before real trade."

Advanced Examples:
  # Multi-step reasoning
  python -m solana_trader.scripts.llm_trade --prompt "Check my balance, analyze if it's a good time to buy, and execute a small test trade in dry-run mode"

  # Risk assessment
  python -m solana_trader.scripts.llm_trade --prompt "Analyze current market conditions and recommend whether to buy, sell, or hold"
        """,
    )

    parser.add_argument(
        "--prompt",
        type=str,
        required=True,
        help="Natural language instruction for the LLM trading agent",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Override config to ensure trades are simulated (recommended)",
    )

    args = parser.parse_args()

    # Load configuration
    print("=" * 80)
    print("Solana AI Trading Bot - LLM-Controlled Trading CLI")
    print("=" * 80)
    print()

    try:
        config = load_config()
        print("✓ Configuration loaded")
    except Exception as e:
        print(f"✗ Failed to load configuration: {e}")
        print("\nPlease ensure .env file exists with all required variables.")
        print("Run: python -m solana_trader.config")
        sys.exit(1)

    # Initialize services
    print("✓ Initializing services...")
    storage = StorageService(config.database_path)
    wallet_manager = WalletManager(config)
    trade_executor = TradeExecutor(config, wallet_manager, storage)
    llm_analyzer = LLMAnalyzer(config, wallet_manager, trade_executor, storage)

    # Display configuration
    print(f"✓ LLM Provider: {config.llm_provider} (fallback: {config.llm_fallback_provider})")
    print(f"✓ Wallet: {wallet_manager.get_public_key()}")

    try:
        balance = await wallet_manager.get_balance()
        print(f"✓ Balance: {balance:.6f} SOL")
    except Exception as e:
        print(f"⚠ Could not fetch balance: {e}")

    print()
    print("User Prompt:")
    print("-" * 80)
    print(f"  {args.prompt}")
    print("-" * 80)
    print()

    # Safety mode display
    if args.dry_run or config.dry_run_mode:
        print("🛡️  SAFETY MODE: Trades will be simulated (dry-run)")
    else:
        print("⚠️  LIVE MODE: Trades will be executed with REAL MONEY!")
        print("⚠️  The LLM agent has control over real transactions!")
        print()
        confirmation = input("Type 'YES' to confirm live trading: ")
        if confirmation != "YES":
            print("Cancelled by user.")
            await trade_executor.close()
            sys.exit(0)

    print()
    print("=" * 80)
    print("LLM Agent Processing...")
    print("=" * 80)
    print()

    try:
        # Get trading decision from LLM
        signal = await llm_analyzer.get_trading_decision(
            user_prompt=args.prompt,
            dry_run=args.dry_run or config.dry_run_mode,
        )

        print()
        print("=" * 80)
        print("LLM Trading Signal")
        print("=" * 80)
        print()
        print(f"Signal:           {signal.signal}")
        print(f"Confidence:       {signal.confidence:.2f}")
        print(f"LLM Model:        {signal.llm_model}")
        print(f"Analysis Time:    {signal.analysis_duration_sec:.2f}s")
        print()
        print("Rationale:")
        print("-" * 80)
        print(signal.rationale)
        print("-" * 80)
        print()
        print("Market Conditions:")
        print(f"  Trend:          {signal.market_conditions.trend}")
        print(f"  Volume:         {signal.market_conditions.volume_assessment}")
        print(f"  Volatility:     {signal.market_conditions.volatility}")
        print(f"  Risk Level:     {signal.market_conditions.risk_level}")
        print()

        if signal.suggested_amount_sol:
            print(f"Suggested Amount: {signal.suggested_amount_sol} SOL")
            print()

        # Check recent signals
        recent_signals = await storage.get_recent_signals(limit=5)
        if recent_signals:
            print("Recent Signals (last 5):")
            print("-" * 80)
            for rs in recent_signals:
                print(f"  {rs['timestamp']}: {rs['signal']} (confidence: {rs['confidence']:.2f})")
            print()

        print("=" * 80)
        print()

        if signal.signal == "HOLD":
            print("✓ LLM recommends HOLD - No trade executed")
        else:
            print(f"✓ LLM recommends {signal.signal} - Check agent output above for trade execution details")

        print()
        print("Next steps:")
        print("1. Review LLM reasoning and market conditions above")
        print("2. Check database for trade execution records (if any)")
        print("3. For real trades, verify on Solscan.io")
        print("=" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print("✗ LLM analysis failed:")
        print(f"Error: {e}")
        print("=" * 80)
        logger.error("LLM trade CLI failed", error=str(e))
        await trade_executor.close()
        sys.exit(1)

    finally:
        await trade_executor.close()


if __name__ == "__main__":
    asyncio.run(main())
