"""LangChain tool for querying wallet balance information.

This module provides the @tool decorated function for LangChain agents to
check wallet balances before making trading decisions.
"""

import json
from typing import Any

from langchain_core.tools import tool

from ..utils.logger import get_logger

logger = get_logger("langchain_tool_wallet")

# Global state for dependency injection (set by LLMAnalyzer)
_wallet_manager: Any = None


def set_wallet_manager(manager: Any) -> None:
    """Set the global wallet manager instance for the tool to use.

    Args:
        manager: WalletManager instance
    """
    global _wallet_manager
    _wallet_manager = manager


@tool
async def get_wallet_balance() -> str:
    """Get current wallet balances for SOL and USDT.

    Use this tool before making trading decisions to ensure sufficient funds.
    This helps you understand the current wallet state and calculate appropriate
    trade sizes.

    Returns:
        JSON string with wallet information:
        - wallet_address: Solana wallet public key
        - sol_balance: Current SOL balance
        - usdt_balance: Current USDT balance (placeholder in MVP)

    Example:
        balance = await get_wallet_balance()
        # Returns: {"wallet_address": "7xKx...", "sol_balance": 0.1, "usdt_balance": 5.0}
    """
    if _wallet_manager is None:
        return json.dumps({
            "status": "error",
            "error_message": "Wallet manager not initialized. Contact system administrator."
        })

    try:
        logger.info("LLM tool: get_wallet_balance called")

        # Get wallet address
        wallet_address = str(_wallet_manager.get_public_key())

        # Get SOL balance
        sol_balance = await _wallet_manager.get_balance()

        # Get USDT balance (placeholder for MVP)
        usdt_balance = await _wallet_manager.get_token_balance(
            "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
        )

        result = {
            "status": "success",
            "wallet_address": wallet_address,
            "sol_balance": round(sol_balance, 6),
            "usdt_balance": round(usdt_balance, 6),
        }

        logger.info(
            "LLM tool: get_wallet_balance completed",
            sol_balance=sol_balance
        )

        return json.dumps(result, indent=2)

    except Exception as e:
        logger.error("LLM tool: get_wallet_balance failed", error=str(e))
        return json.dumps({
            "status": "error",
            "error_message": str(e)
        })
