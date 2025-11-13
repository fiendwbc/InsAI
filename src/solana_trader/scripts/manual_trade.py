"""Manual trading CLI script for testing trade execution.

This script allows manual testing of trade execution with Jupiter integration.
Usage: python -m solana_trader.scripts.manual_trade --action BUY --amount 0.01 --dry-run
"""

import argparse
import asyncio
import sys
from datetime import datetime

from ..config import load_config
from ..services.storage import StorageService
from ..services.trade_executor import TradeExecutor
from ..utils.logger import get_logger
from ..wallet.manager import WalletManager

logger = get_logger("manual_trade")


async def main() -> None:
    """Main entry point for manual trading CLI."""
    parser = argparse.ArgumentParser(
        description="Manual trading CLI for Solana trading bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run BUY (safe test mode)
  python -m solana_trader.scripts.manual_trade --action BUY --amount 0.01 --dry-run

  # Dry-run SELL
  python -m solana_trader.scripts.manual_trade --action SELL --amount 0.01 --dry-run

  # Real BUY (⚠️ COSTS REAL MONEY)
  python -m solana_trader.scripts.manual_trade --action BUY --amount 0.01

  # Real SELL (⚠️ COSTS REAL MONEY)
  python -m solana_trader.scripts.manual_trade --action SELL --amount 0.01
        """,
    )

    parser.add_argument(
        "--action",
        type=str,
        required=True,
        choices=["BUY", "SELL"],
        help="Trading action: BUY (USDT→SOL) or SELL (SOL→USDT)",
    )

    parser.add_argument(
        "--amount",
        type=float,
        required=True,
        help="Amount of SOL to trade (e.g., 0.01)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simulate trade without real execution (recommended for testing)",
    )

    args = parser.parse_args()

    # Load configuration
    print("=" * 80)
    print("Solana AI Trading Bot - Manual Trade CLI")
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

    # Display wallet info
    try:
        balance = await wallet_manager.get_balance()
        print(f"✓ Wallet: {wallet_manager.get_public_key()}")
        print(f"✓ Balance: {balance:.6f} SOL")
    except Exception as e:
        print(f"✗ Failed to fetch wallet balance: {e}")
        await trade_executor.close()
        sys.exit(1)

    # Display trade parameters
    print()
    print("Trade Parameters:")
    print("-" * 80)
    print(f"  Action:       {args.action}")
    print(f"  Amount:       {args.amount} SOL")
    print(f"  Slippage:     {config.slippage_bps} bps ({config.slippage_bps / 100:.2f}%)")
    print(f"  Mode:         {'DRY-RUN (no real trade)' if args.dry_run else '⚠️  LIVE (real money!)'}")
    print("-" * 80)
    print()

    # Safety confirmation for real trades
    if not args.dry_run:
        print("⚠️  WARNING: You are about to execute a REAL trade with REAL money!")
        print("⚠️  This transaction cannot be reversed once confirmed on the blockchain.")
        print()
        confirmation = input("Type 'YES' to confirm and proceed: ")
        if confirmation != "YES":
            print("Trade cancelled by user.")
            await trade_executor.close()
            sys.exit(0)
        print()

    # Execute trade
    print("Executing trade...")
    print()

    try:
        start_time = datetime.now()

        # Execute trade
        execution = await trade_executor.execute_trade(
            action=args.action,
            amount_sol=args.amount,
            dry_run=args.dry_run,
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Display results
        print("=" * 80)
        print("Trade Execution Results")
        print("=" * 80)
        print()
        print(f"Status:           {execution.status.upper()}")
        print(f"Signal:           {execution.signal}")
        print(f"Input Token:      {execution.input_token}")
        print(f"Output Token:     {execution.output_token}")
        print(f"Input Amount:     {execution.input_amount} SOL")

        if execution.expected_output:
            print(f"Expected Output:  {execution.expected_output:.6f}")

        if execution.output_amount:
            print(f"Actual Output:    {execution.output_amount:.6f}")
            if execution.expected_output:
                slippage = ((execution.expected_output - execution.output_amount) / execution.expected_output) * 100
                print(f"Slippage:         {slippage:.2f}%")

        if execution.transaction_signature:
            print(f"TX Signature:     {execution.transaction_signature}")
            print(f"Solscan Link:     https://solscan.io/tx/{execution.transaction_signature}")

        if execution.gas_fee_sol:
            print(f"Gas Fee:          {execution.gas_fee_sol:.9f} SOL")

        print(f"Duration:         {duration:.2f}s")

        if execution.error_message:
            print(f"Error:            {execution.error_message}")

        print()

        if execution.status == "success":
            print("✓ Trade executed successfully!")
            print()
            print("Next steps:")
            print("1. Verify transaction on Solscan.io")
            print("2. Check wallet balance updates")
            print("3. Review trade record in database")
        elif execution.status == "dry_run":
            print("✓ Dry-run completed successfully!")
            print()
            print("Next steps:")
            print("1. Review quote details above")
            print("2. If satisfied, run without --dry-run flag")
            print("3. Always start with small amounts (0.01 SOL)")
        else:
            print("✗ Trade execution failed!")
            print()
            print("Troubleshooting:")
            print("1. Check error message above")
            print("2. Verify wallet has sufficient balance")
            print("3. Ensure Solana RPC is responding")
            print("4. Try increasing slippage tolerance (SLIPPAGE_BPS)")

        print("=" * 80)

    except Exception as e:
        print()
        print("=" * 80)
        print("✗ Trade execution failed with exception:")
        print(f"Error: {e}")
        print("=" * 80)
        logger.error("Manual trade failed", error=str(e))
        await trade_executor.close()
        sys.exit(1)

    finally:
        await trade_executor.close()


if __name__ == "__main__":
    asyncio.run(main())
