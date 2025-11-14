"""LangChain tool for executing trades on Solana via Jupiter.

This module provides the @tool decorated function for LangChain agents to
execute BUY/SELL trades on the Solana blockchain.
"""

import json
from typing import Any

from langchain_core.tools import tool

from ..utils.logger import get_logger

logger = get_logger("langchain_tool_trade")

# Global state for dependency injection (set by LLMAnalyzer)
_trade_executor: Any = None


def set_trade_executor(executor: Any) -> None:
    """Set the global trade executor instance for the tool to use.

    Args:
        executor: TradeExecutor instance
    """
    global _trade_executor
    _trade_executor = executor


@tool
async def solana_trade(action: str, amount: float, dry_run: bool = True) -> str:
    """Execute a trade on Solana via Jupiter aggregator.

    This tool allows you to execute BUY or SELL trades for SOL/USDT pair on Solana.
    ALWAYS use dry_run=True first to test the trade before executing for real.

    Args:
        action: Trade action - must be "BUY" (USDT→SOL) or "SELL" (SOL→USDT)
        amount: Amount of SOL to trade (e.g., 0.01 for testing)
        dry_run: If True, simulate trade without real execution (default: True for safety)

    Returns:
        JSON string with trade execution results including:
        - status: "success", "failed", or "dry_run"
        - transaction_signature: Solana tx signature (if successful)
        - expected_output: Expected output amount from quote
        - execution_duration_sec: Time taken to execute
        - error_message: Error details if failed

    Example:
        # Test a trade first (safe)
        result = await solana_trade("BUY", 0.01, dry_run=True)

        # Execute for real (after confirming quote)
        result = await solana_trade("BUY", 0.01, dry_run=False)
    """
    if _trade_executor is None:
        return json.dumps({
            "status": "error",
            "error_message": "Trade executor not initialized. Contact system administrator."
        })

    try:
        logger.info(
            "LLM tool: solana_trade called",
            action=action,
            amount=amount,
            dry_run=dry_run
        )

        # Validate action
        if action not in ["BUY", "SELL"]:
            return json.dumps({
                "status": "error",
                "error_message": f"Invalid action '{action}'. Must be 'BUY' or 'SELL'."
            })

        # Validate amount
        if amount <= 0:
            return json.dumps({
                "status": "error",
                "error_message": f"Invalid amount {amount}. Must be greater than 0."
            })

        # Execute trade
        execution = await _trade_executor.execute_trade(
            action=action,
            amount_sol=amount,
            dry_run=dry_run
        )

        # Build response
        result = {
            "status": execution.status,
            "signal": execution.signal,
            "input_amount": execution.input_amount,
            "expected_output": execution.expected_output,
            "transaction_signature": execution.transaction_signature,
            "execution_duration_sec": execution.execution_duration_sec,
            "gas_fee_sol": execution.gas_fee_sol,
            "error_message": execution.error_message,
        }

        # Add output amount if available
        if execution.output_amount:
            result["actual_output"] = execution.output_amount
            if execution.expected_output:
                slippage = ((execution.expected_output - execution.output_amount) / execution.expected_output) * 100
                result["slippage_pct"] = round(slippage, 2)

        logger.info(
            "LLM tool: solana_trade completed",
            status=execution.status,
            signature=execution.transaction_signature
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error("LLM tool: solana_trade failed", error=str(e))
        return json.dumps({
            "status": "error",
            "error_message": str(e)
        })
