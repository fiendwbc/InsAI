"""SQLite storage service for market data, trading signals, and trade executions.

This module provides async wrappers around sqlite3 for storing and querying
trading bot data with proper schema initialization and indexing.
"""

import asyncio
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from ..utils.logger import get_logger

logger = get_logger("storage")


class StorageService:
    """SQLite storage service with async wrappers and schema management."""

    def __init__(self, database_path: str = "trading_bot.db"):
        """Initialize storage service and create database schema.

        Args:
            database_path: Path to SQLite database file (default: trading_bot.db)
        """
        self.database_path = database_path
        self._ensure_schema()
        logger.info("Storage service initialized", database_path=database_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Get a new database connection.

        Returns:
            sqlite3.Connection with row_factory set to Row for dict-like access
        """
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row  # Enable column access by name
        return conn

    def _ensure_schema(self) -> None:
        """Create database tables and indexes if they don't exist."""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Create market_data table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS market_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    source TEXT NOT NULL CHECK(source IN ('jupiter', 'coingecko', 'coinkarma')),
                    sol_price_usd REAL NOT NULL CHECK(sol_price_usd > 0),
                    volume_24h REAL,
                    price_change_24h_pct REAL,
                    quote_amount INTEGER,
                    pulse_index REAL,
                    liquidity_index REAL,
                    liquidity_value REAL,
                    metadata JSON,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_market_data_timestamp
                ON market_data(timestamp DESC)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_market_data_source
                ON market_data(source)
            """
            )

            # Create trading_signals table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS trading_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    signal TEXT NOT NULL CHECK(signal IN ('BUY', 'SELL', 'HOLD')),
                    confidence REAL NOT NULL CHECK(confidence >= 0 AND confidence <= 1),
                    rationale TEXT NOT NULL CHECK(length(rationale) >= 10),
                    suggested_amount_sol REAL CHECK(suggested_amount_sol > 0),
                    market_conditions JSON NOT NULL,
                    llm_model TEXT NOT NULL,
                    analysis_duration_sec REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_trading_signals_timestamp
                ON trading_signals(timestamp DESC)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_trading_signals_signal
                ON trading_signals(signal)
            """
            )

            # Create trade_executions table
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS trade_executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    signal TEXT NOT NULL CHECK(signal IN ('BUY', 'SELL')),
                    input_token TEXT NOT NULL,
                    output_token TEXT NOT NULL,
                    input_amount REAL NOT NULL CHECK(input_amount > 0),
                    output_amount REAL CHECK(output_amount > 0),
                    expected_output REAL CHECK(expected_output > 0),
                    slippage_bps INTEGER NOT NULL CHECK(slippage_bps >= 0 AND slippage_bps <= 10000),
                    status TEXT NOT NULL CHECK(status IN ('pending', 'success', 'failed', 'dry_run')),
                    transaction_signature TEXT UNIQUE,
                    error_message TEXT,
                    execution_duration_sec REAL,
                    gas_fee_sol REAL CHECK(gas_fee_sol >= 0),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_trade_executions_timestamp
                ON trade_executions(timestamp DESC)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_trade_executions_status
                ON trade_executions(status)
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_trade_executions_signature
                ON trade_executions(transaction_signature)
            """
            )

            conn.commit()
            logger.info("Database schema initialized successfully")

    async def save_market_data(self, data: dict[str, Any]) -> int:
        """Save market data record to database.

        Args:
            data: Market data dictionary (from MarketData.model_dump())

        Returns:
            Row ID of inserted record

        Example:
            >>> market_data = MarketData(timestamp=datetime.now(), source="jupiter", ...)
            >>> row_id = await storage.save_market_data(market_data.model_dump())
        """

        def _insert() -> int:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO market_data (
                        timestamp, source, sol_price_usd, volume_24h,
                        price_change_24h_pct, quote_amount, pulse_index,
                        liquidity_index, liquidity_value, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        data["timestamp"].isoformat() if isinstance(data["timestamp"], datetime) else data["timestamp"],
                        data["source"],
                        data["sol_price_usd"],
                        data.get("volume_24h"),
                        data.get("price_change_24h_pct"),
                        data.get("quote_amount"),
                        data.get("pulse_index"),
                        data.get("liquidity_index"),
                        data.get("liquidity_value"),
                        json.dumps(data.get("metadata", {})),
                    ),
                )
                conn.commit()
                return cursor.lastrowid

        row_id = await asyncio.to_thread(_insert)
        logger.info("Market data saved", row_id=row_id, source=data["source"])
        return row_id

    async def save_trading_signal(self, signal: dict[str, Any]) -> int:
        """Save trading signal record to database.

        Args:
            signal: Trading signal dictionary (from TradingSignal.model_dump())

        Returns:
            Row ID of inserted record
        """

        def _insert() -> int:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO trading_signals (
                        timestamp, signal, confidence, rationale,
                        suggested_amount_sol, market_conditions, llm_model,
                        analysis_duration_sec
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        signal["timestamp"].isoformat() if isinstance(signal["timestamp"], datetime) else signal["timestamp"],
                        signal["signal"],
                        signal["confidence"],
                        signal["rationale"],
                        signal.get("suggested_amount_sol"),
                        json.dumps(signal["market_conditions"]),
                        signal["llm_model"],
                        signal.get("analysis_duration_sec"),
                    ),
                )
                conn.commit()
                return cursor.lastrowid

        row_id = await asyncio.to_thread(_insert)
        logger.info("Trading signal saved", row_id=row_id, signal=signal["signal"])
        return row_id

    async def save_trade_execution(self, execution: dict[str, Any]) -> int:
        """Save trade execution record to database.

        Args:
            execution: Trade execution dictionary (from TradeExecution.model_dump())

        Returns:
            Row ID of inserted record
        """

        def _insert() -> int:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO trade_executions (
                        timestamp, signal, input_token, output_token,
                        input_amount, output_amount, expected_output,
                        slippage_bps, status, transaction_signature,
                        error_message, execution_duration_sec, gas_fee_sol
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        execution["timestamp"].isoformat() if isinstance(execution["timestamp"], datetime) else execution["timestamp"],
                        execution["signal"],
                        execution["input_token"],
                        execution["output_token"],
                        execution["input_amount"],
                        execution.get("output_amount"),
                        execution.get("expected_output"),
                        execution["slippage_bps"],
                        execution["status"],
                        execution.get("transaction_signature"),
                        execution.get("error_message"),
                        execution.get("execution_duration_sec"),
                        execution.get("gas_fee_sol"),
                    ),
                )
                conn.commit()
                return cursor.lastrowid

        row_id = await asyncio.to_thread(_insert)
        logger.info(
            "Trade execution saved",
            row_id=row_id,
            signal=execution["signal"],
            status=execution["status"],
        )
        return row_id

    async def get_latest_market_data(self, source: str | None = None) -> dict[str, Any] | None:
        """Get the most recent market data record.

        Args:
            source: Optional source filter (jupiter, coingecko, coinkarma)

        Returns:
            Latest market data as dictionary, or None if no records exist
        """

        def _query() -> dict[str, Any] | None:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                if source:
                    cursor.execute(
                        """
                        SELECT * FROM market_data
                        WHERE source = ?
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """,
                        (source,),
                    )
                else:
                    cursor.execute(
                        """
                        SELECT * FROM market_data
                        ORDER BY timestamp DESC
                        LIMIT 1
                    """
                    )
                row = cursor.fetchone()
                return dict(row) if row else None

        return await asyncio.to_thread(_query)

    async def get_recent_signals(self, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent trading signals.

        Args:
            limit: Maximum number of signals to return (default: 10)

        Returns:
            List of trading signal dictionaries
        """

        def _query() -> list[dict[str, Any]]:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT * FROM trading_signals
                    ORDER BY timestamp DESC
                    LIMIT ?
                """,
                    (limit,),
                )
                return [dict(row) for row in cursor.fetchall()]

        return await asyncio.to_thread(_query)

    async def get_trades_count_today(self) -> int:
        """Get count of trades executed today.

        Returns:
            Number of trades (excluding dry_run) today
        """

        def _query() -> int:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM trade_executions
                    WHERE date(timestamp) = date('now')
                    AND status != 'dry_run'
                """
                )
                return cursor.fetchone()[0]

        return await asyncio.to_thread(_query)

    async def get_trades_count_last_hour(self) -> int:
        """Get count of trades in the last hour.

        Returns:
            Number of trades (excluding dry_run) in last 60 minutes
        """

        def _query() -> int:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT COUNT(*) FROM trade_executions
                    WHERE timestamp >= datetime('now', '-1 hour')
                    AND status != 'dry_run'
                """
                )
                return cursor.fetchone()[0]

        return await asyncio.to_thread(_query)
