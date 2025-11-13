"""Wallet management for Solana transactions.

This module provides wallet initialization, balance checking, and keypair
management for signing transactions.
"""

from solana.rpc.async_api import AsyncClient
from solders.keypair import Keypair  # type: ignore
from solders.pubkey import Pubkey  # type: ignore

from ..config import BotConfiguration
from ..utils.logger import get_logger

logger = get_logger("wallet_manager")


class WalletManager:
    """Manages Solana wallet operations including keypair and balance queries.

    This class handles wallet initialization from private key, balance checking,
    and provides access to the keypair for transaction signing.
    """

    def __init__(self, config: BotConfiguration):
        """Initialize wallet manager from configuration.

        Args:
            config: Bot configuration containing wallet settings

        Raises:
            ValueError: If wallet_type is not supported
            Exception: If private key is invalid
        """
        self.config = config
        self._keypair: Keypair | None = None

        if config.wallet_type != "private_key":
            raise ValueError(f"Unsupported wallet type: {config.wallet_type}")

        # Load keypair from base58 private key
        try:
            # Convert base58 private key string to bytes
            import base58

            private_key_bytes = base58.b58decode(config.wallet_private_key)
            self._keypair = Keypair.from_bytes(private_key_bytes)
            logger.info("Wallet initialized", wallet_address=str(self.get_public_key()))
        except Exception as e:
            logger.error("Failed to initialize wallet", error=str(e))
            raise ValueError(f"Invalid wallet private key: {e}") from e

    def get_keypair(self) -> Keypair:
        """Get the wallet keypair for signing transactions.

        Returns:
            Solders Keypair instance

        Raises:
            RuntimeError: If keypair is not initialized
        """
        if self._keypair is None:
            raise RuntimeError("Wallet not initialized")
        return self._keypair

    def get_public_key(self) -> Pubkey:
        """Get the wallet public key (address).

        Returns:
            Solders Pubkey instance representing wallet address
        """
        return self.get_keypair().pubkey()

    async def get_balance(self) -> float:
        """Get current SOL balance for the wallet.

        Returns:
            SOL balance as float (e.g., 1.5 SOL)

        Raises:
            Exception: If RPC call fails
        """
        async with AsyncClient(self.config.solana_rpc_url) as client:
            response = await client.get_balance(self.get_public_key())
            if response.value is None:
                raise RuntimeError("Failed to fetch wallet balance")
            # Convert lamports to SOL (1 SOL = 1e9 lamports)
            balance_sol = response.value / 1e9
            logger.info("Wallet balance fetched", balance_sol=balance_sol)
            return balance_sol

    async def get_token_balance(self, token_mint: str) -> float:
        """Get SPL token balance for the wallet.

        Args:
            token_mint: Token mint address (e.g., USDT mint)

        Returns:
            Token balance as float

        Note:
            This is a placeholder for MVP. Full implementation would use
            get_token_accounts_by_owner and parse token balances.
        """
        # TODO: Implement SPL token balance query
        logger.warning("Token balance query not yet implemented", token_mint=token_mint)
        return 0.0
