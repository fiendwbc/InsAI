"""Trade execution service using Jupiter aggregator on Solana.

This module handles the complete trade execution flow:
1. Fetch quote from Jupiter API
2. Build swap transaction
3. Sign with wallet keypair
4. Submit to Solana blockchain
5. Wait for confirmation
"""

import asyncio
import base64
import time
from datetime import datetime, timezone
from typing import Any

import aiohttp
from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Confirmed
from solders.transaction import VersionedTransaction  # type: ignore

from ..config import BotConfiguration
from ..models.trade_execution import TradeExecution
from ..utils.logger import get_logger
from ..utils.retry import retry
from ..wallet.manager import WalletManager
from .storage import StorageService

logger = get_logger("trade_executor")

# Token mint addresses
SOL_MINT = "So11111111111111111111111111111111111111112"
USDT_MINT = "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"

# Jupiter API endpoints
JUPITER_QUOTE_URL = "https://quote-api.jup.ag/v6/quote"
JUPITER_SWAP_URL = "https://quote-api.jup.ag/v6/swap"


class TradeExecutor:
    """Executes trades on Solana via Jupiter aggregator with safety checks."""

    def __init__(
        self,
        config: BotConfiguration,
        wallet_manager: WalletManager,
        storage: StorageService,
    ):
        """Initialize trade executor.

        Args:
            config: Bot configuration
            wallet_manager: Wallet manager for signing transactions
            storage: Storage service for persisting executions
        """
        self.config = config
        self.wallet_manager = wallet_manager
        self.storage = storage
        self.solana_client = AsyncClient(config.solana_rpc_url)
        self.circuit_breaker_active = False
        self.last_price: float | None = None
        logger.info("Trade executor initialized", rpc_url=config.solana_rpc_url)

    async def close(self) -> None:
        """Close the Solana RPC client connection."""
        await self.solana_client.close()

    async def get_recent_blockhash(self) -> str:
        """Get recent blockhash from Solana.

        Returns:
            Recent blockhash as string

        Raises:
            Exception: If RPC call fails
        """
        response = await self.solana_client.get_latest_blockhash(Confirmed)
        if response.value is None:
            raise RuntimeError("Failed to fetch recent blockhash")
        return str(response.value.blockhash)

    async def get_transaction_status(self, signature: str) -> dict[str, Any]:
        """Get transaction status from Solana.

        Args:
            signature: Transaction signature to check

        Returns:
            Transaction status dictionary
        """
        response = await self.solana_client.get_signature_statuses([signature])
        if response.value and len(response.value) > 0:
            status = response.value[0]
            return {
                "confirmed": status is not None,
                "err": status.err if status else None,
            }
        return {"confirmed": False, "err": None}

    @retry(max_attempts=3, backoff_factor=2)
    async def get_jupiter_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int,
    ) -> dict[str, Any]:
        """Fetch swap quote from Jupiter API.

        Args:
            input_mint: Input token mint address
            output_mint: Output token mint address
            amount: Input amount in smallest units (lamports for SOL)
            slippage_bps: Slippage tolerance in basis points (50 = 0.5%)

        Returns:
            Full quote response from Jupiter API

        Raises:
            aiohttp.ClientError: If API call fails
        """
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": str(slippage_bps),
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(JUPITER_QUOTE_URL, params=params) as response:
                response.raise_for_status()
                quote = await response.json()
                logger.info(
                    "Jupiter quote fetched",
                    input_mint=input_mint[:8],
                    output_mint=output_mint[:8],
                    amount=amount,
                    out_amount=quote.get("outAmount"),
                    price_impact=quote.get("priceImpactPct"),
                )
                return quote

    @retry(max_attempts=3, backoff_factor=2)
    async def build_swap_transaction(
        self,
        quote: dict[str, Any],
        user_pubkey: str,
    ) -> bytes:
        """Build swap transaction from Jupiter quote.

        Args:
            quote: Quote response from get_jupiter_quote
            user_pubkey: User's wallet public key as string

        Returns:
            Transaction bytes ready for signing

        Raises:
            aiohttp.ClientError: If API call fails
        """
        payload = {
            "quoteResponse": quote,
            "userPublicKey": user_pubkey,
            "wrapAndUnwrapSol": True,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(JUPITER_SWAP_URL, json=payload) as response:
                response.raise_for_status()
                data = await response.json()
                swap_transaction = data["swapTransaction"]
                tx_bytes = base64.b64decode(swap_transaction)
                logger.info("Jupiter swap transaction built", tx_size=len(tx_bytes))
                return tx_bytes

    async def check_trade_limits(self) -> tuple[bool, str | None]:
        """Check if trade limits allow a new trade.

        Returns:
            Tuple of (allowed, reason_if_blocked)
        """
        # Check daily limit
        trades_today = await self.storage.get_trades_count_today()
        if trades_today >= self.config.max_trades_per_day:
            return False, f"Daily trade limit reached ({trades_today}/{self.config.max_trades_per_day})"

        # Check hourly limit
        trades_hour = await self.storage.get_trades_count_last_hour()
        if trades_hour >= self.config.max_trades_per_hour:
            return False, f"Hourly trade limit reached ({trades_hour}/{self.config.max_trades_per_hour})"

        # Check circuit breaker
        if self.circuit_breaker_active:
            return False, "Circuit breaker active due to large price movement"

        return True, None

    async def execute_trade(
        self,
        action: str,
        amount_sol: float,
        dry_run: bool | None = None,
    ) -> TradeExecution:
        """Execute a trade on Solana via Jupiter.

        Args:
            action: Trade action ("BUY" or "SELL")
            amount_sol: Amount of SOL to trade
            dry_run: Override config dry_run mode (None = use config)

        Returns:
            TradeExecution record with transaction details

        Raises:
            ValueError: If action is invalid or amount exceeds limits
            RuntimeError: If trade execution fails
        """
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)

        # Validate action
        if action not in ["BUY", "SELL"]:
            raise ValueError(f"Invalid action: {action}. Must be 'BUY' or 'SELL'")

        # Use config dry_run if not explicitly overridden
        is_dry_run = dry_run if dry_run is not None else self.config.dry_run_mode

        # Check trade limits
        allowed, reason = await self.check_trade_limits()
        if not allowed and not is_dry_run:
            logger.warning("Trade blocked by limits", reason=reason)
            return TradeExecution(
                timestamp=timestamp,
                signal=action,
                input_token=USDT_MINT if action == "BUY" else SOL_MINT,
                output_token=SOL_MINT if action == "BUY" else USDT_MINT,
                input_amount=amount_sol,
                slippage_bps=self.config.slippage_bps,
                status="failed",
                error_message=reason,
            )

        # Check amount limits
        if amount_sol > self.config.max_trade_size_sol:
            error_msg = f"Amount {amount_sol} SOL exceeds max trade size {self.config.max_trade_size_sol} SOL"
            logger.error("Trade rejected", reason=error_msg)
            return TradeExecution(
                timestamp=timestamp,
                signal=action,
                input_token=USDT_MINT if action == "BUY" else SOL_MINT,
                output_token=SOL_MINT if action == "BUY" else USDT_MINT,
                input_amount=amount_sol,
                slippage_bps=self.config.slippage_bps,
                status="failed",
                error_message=error_msg,
            )

        # Determine token mints based on action
        if action == "BUY":
            # BUY: USDT → SOL (we need to estimate USDT amount)
            # For simplicity, we'll use SOL amount and let Jupiter calculate USDT needed
            input_mint = USDT_MINT
            output_mint = SOL_MINT
            amount_lamports = int(amount_sol * 1e9)  # Convert SOL to lamports for output
        else:  # SELL
            # SELL: SOL → USDT
            input_mint = SOL_MINT
            output_mint = USDT_MINT
            amount_lamports = int(amount_sol * 1e9)  # Convert SOL to lamports for input

        try:
            # Get quote from Jupiter
            logger.info("Fetching Jupiter quote", action=action, amount_sol=amount_sol)
            quote = await self.get_jupiter_quote(
                input_mint=input_mint,
                output_mint=output_mint,
                amount=amount_lamports,
                slippage_bps=self.config.slippage_bps,
            )

            expected_output = int(quote["outAmount"])
            price_impact = float(quote.get("priceImpactPct", 0))

            # Dry-run mode: return without executing
            if is_dry_run:
                execution_duration = time.time() - start_time
                logger.info(
                    "Dry-run trade completed",
                    action=action,
                    amount_sol=amount_sol,
                    expected_output=expected_output,
                    price_impact=price_impact,
                )
                execution = TradeExecution(
                    timestamp=timestamp,
                    signal=action,
                    input_token=input_mint,
                    output_token=output_mint,
                    input_amount=amount_sol,
                    expected_output=expected_output / 1e9 if action == "BUY" else expected_output / 1e6,
                    slippage_bps=self.config.slippage_bps,
                    status="dry_run",
                    execution_duration_sec=execution_duration,
                )
                await self.storage.save_trade_execution(execution.model_dump())
                return execution

            # Build transaction
            user_pubkey = str(self.wallet_manager.get_public_key())
            logger.info("Building swap transaction", user_pubkey=user_pubkey[:8])
            tx_bytes = await self.build_swap_transaction(quote, user_pubkey)

            # Deserialize, sign, and send transaction
            tx = VersionedTransaction.from_bytes(tx_bytes)
            keypair = self.wallet_manager.get_keypair()

            # Sign the transaction
            signed_tx = VersionedTransaction.populate(tx.message, [keypair])

            # Send transaction
            logger.info("Sending transaction to Solana")
            response = await self.solana_client.send_raw_transaction(
                bytes(signed_tx),
                opts={"skip_preflight": False}
            )

            signature = str(response.value)
            logger.info("Transaction sent", signature=signature)

            # Wait for confirmation (with timeout)
            confirmed = False
            for _ in range(30):  # 30 seconds timeout
                await asyncio.sleep(1)
                status = await self.get_transaction_status(signature)
                if status["confirmed"]:
                    confirmed = True
                    if status["err"]:
                        raise RuntimeError(f"Transaction failed: {status['err']}")
                    break

            if not confirmed:
                raise RuntimeError("Transaction confirmation timeout")

            execution_duration = time.time() - start_time
            logger.info(
                "Trade executed successfully",
                signature=signature,
                duration=execution_duration,
            )

            execution = TradeExecution(
                timestamp=timestamp,
                signal=action,
                input_token=input_mint,
                output_token=output_mint,
                input_amount=amount_sol,
                expected_output=expected_output / 1e9 if action == "BUY" else expected_output / 1e6,
                slippage_bps=self.config.slippage_bps,
                status="success",
                transaction_signature=signature,
                execution_duration_sec=execution_duration,
                gas_fee_sol=0.000005,  # Approximate, could be fetched from tx details
            )
            await self.storage.save_trade_execution(execution.model_dump())
            return execution

        except Exception as e:
            execution_duration = time.time() - start_time
            logger.error("Trade execution failed", error=str(e), duration=execution_duration)
            execution = TradeExecution(
                timestamp=timestamp,
                signal=action,
                input_token=input_mint,
                output_token=output_mint,
                input_amount=amount_sol,
                slippage_bps=self.config.slippage_bps,
                status="failed",
                error_message=str(e),
                execution_duration_sec=execution_duration,
            )
            await self.storage.save_trade_execution(execution.model_dump())
            return execution
