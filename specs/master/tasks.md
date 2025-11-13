# Implementation Tasks: Solana AI Trading Bot

**Branch**: `master` | **Generated**: 2025-11-12 (REVISED) | **Plan**: [plan.md](./plan.md)

**🎯 PRIORITY OPTIMIZATION**: Tasks reordered to prioritize Solana mainnet trading and LLM control capabilities for early validation.

**Task Organization**: Core trading functionality (Phases 3-4) moved ahead of market data collection to enable faster real-world testing.

---

## Task Format

```
- [ ] [TaskID] [P] [Story] Description (file: path/to/file.py)
```

- **[TaskID]**: Unique identifier (e.g., SETUP-001, TRADE-001)
- **[P]**: Marks parallelizable tasks (can run concurrently)
- **[Story]**: Story label (US1, US2, US3) for tasks within user story phases
- **file**: Specific file path for implementation

---

## Phase 1: Project Setup (Foundation)

**Estimated Time**: 1 hour
**Parallel Tasks**: 0 (sequential setup)

### Initialize Project Structure

- [ ] SETUP-001 Initialize uv project with pyproject.toml (file: pyproject.toml)
  - Run: `uv init`
  - Verify Python 3.11+ requirement
  - Configure PEP 621 metadata
  - Add project.scripts entry: `solana-trader = "solana_trader.main:main"`

- [ ] SETUP-002 Create source directory structure (file: src/solana_trader/)
  - Create: `src/solana_trader/__init__.py`
  - Create: `src/solana_trader/models/`
  - Create: `src/solana_trader/services/`
  - Create: `src/solana_trader/langchain_tools/`
  - Create: `src/solana_trader/coinkarma/`
  - Create: `src/solana_trader/wallet/`
  - Create: `src/solana_trader/utils/`

- [ ] SETUP-003 Create test directory structure (file: tests/)
  - Create: `tests/unit/`
  - Create: `tests/integration/`
  - Create: `tests/contract/`
  - Create: `tests/performance/`

- [ ] SETUP-004 Install production dependencies with uv (file: uv.lock)
  - Run: `uv add langchain>=1.0.3 openai>=1.0.0 solana>=0.35.0 solders>=0.21.0`
  - Run: `uv add pydantic>=2.10.4 pydantic-settings>=2.0.0 python-dotenv>=1.0.0`
  - Run: `uv add aiohttp>=3.9.0 requests>=2.31.0 structlog>=24.0.0`
  - Run: `uv add cryptography>=44.0.0 pycryptodome>=3.20.0`

- [ ] SETUP-005 Install dev dependencies with uv (file: uv.lock)
  - Run: `uv add --dev pytest>=8.0.0 pytest-asyncio>=0.23.0 pytest-cov>=4.1.0 pytest-mock>=3.12.0`
  - Run: `uv add --dev ruff>=0.1.0 black>=24.0.0 mypy>=1.8.0 types-requests>=2.31.0`

- [ ] SETUP-006 Create environment configuration (file: .env.example)
  - Copy from .env.example template
  - Document all required variables with comments
  - Set DRY_RUN_MODE=true as default

- [ ] SETUP-007 Configure linting and formatting tools (file: pyproject.toml)
  - Add [tool.ruff] section with line-length=100, target-version="py311"
  - Add [tool.black] section with line-length=100
  - Add [tool.pytest.ini_options] with asyncio_mode="auto"
  - Add [tool.mypy] section with strict type checking

---

## Phase 2: Foundational Components (Core Infrastructure)

**Estimated Time**: 2 hours
**Parallel Tasks**: 5 (FOUND-001 through FOUND-005 can run concurrently)

### Utilities and Configuration

- [ ] FOUND-001 [P] Implement structured JSON logger (file: src/solana_trader/utils/logger.py)
  - Use structlog for structured logging
  - Include: timestamp, level, service, trace_id fields
  - Support LOG_LEVEL from environment
  - Test: Verify JSON output format

- [ ] FOUND-002 [P] Implement retry logic with exponential backoff (file: src/solana_trader/utils/retry.py)
  - Decorator: `@retry(max_attempts=3, backoff_factor=2)`
  - Handle: `aiohttp.ClientError`, `requests.RequestException`
  - Log each retry attempt with delay duration
  - Test: Verify backoff intervals (1s, 2s, 4s)

- [ ] FOUND-003 [P] Implement configuration loader (file: src/solana_trader/config.py)
  - Use pydantic_settings.BaseSettings for BotConfiguration
  - Load from .env file with python-dotenv
  - Validate all required fields (OpenRouter, CoinKarma, wallet keys)
  - Provide defaults for intervals and limits
  - Include config validation CLI: `python -m solana_trader.config`
  - Test: Verify validation errors for missing required fields

- [ ] FOUND-004 [P] Initialize SQLite database schema (file: src/solana_trader/services/storage.py)
  - Create tables: market_data, trading_signals, trade_executions
  - Add indexes: timestamp (DESC), status, transaction_signature
  - Implement connection pool with sqlite3.connect
  - Provide async wrappers for insert/query operations
  - Test: Verify schema creation with sample inserts

- [ ] FOUND-005 [P] Create __init__.py exports (file: src/solana_trader/__init__.py)
  - Export: BotConfiguration, logger, retry decorator
  - Define __version__ = "0.1.0"
  - Add top-level docstring with project description

---

## Phase 3: Core Trading Capabilities (🎯 PRIORITY 1)

**Estimated Time**: 4 hours
**Parallel Tasks**: 2 (TRADE-001, TRADE-002 can run concurrently after FOUND completes)
**🎯 FOCUS**: Get Solana mainnet trading working ASAP for real-world validation

### Data Models

- [X] TRADE-001 [P] [US3] Implement TradeExecution Pydantic model (file: src/solana_trader/models/trade_execution.py)
  - Fields: timestamp, signal, input_token, output_token, input_amount
  - Fields: output_amount, expected_output, slippage_bps, status
  - Fields: transaction_signature, error_message, execution_duration_sec, gas_fee_sol
  - Validation: signal in ["BUY", "SELL"], amount > 0, slippage 0-10000 bps
  - Validator: transaction_signature must be 88-char alphanumeric base58
  - Test: Validate with valid/invalid transaction data

### Wallet Management

- [X] TRADE-002 [P] [US3] Implement wallet manager (file: src/solana_trader/wallet/manager.py)
  - Class: WalletManager
  - Load: Private key from BotConfiguration.wallet_private_key (base58)
  - Method: `get_keypair() -> Keypair` - return solders.Keypair from base58
  - Method: `get_public_key() -> Pubkey` - return wallet address
  - Method: `get_balance() -> float` - query SOL balance from RPC
  - Test: Verify keypair derivation from test private key

### Solana RPC Client

- [X] TRADE-003 [US3] Initialize Solana RPC client (file: src/solana_trader/services/trade_executor.py - __init__)
  - Import: `from solana.rpc.async_api import AsyncClient`
  - Create: `self.solana_client = AsyncClient(config.solana_rpc_url)`
  - Method: `async def get_recent_blockhash() -> str`
  - Method: `async def get_transaction_status(signature: str) -> dict`
  - Test: Verify connection to mainnet RPC

### Jupiter Integration

- [X] TRADE-004 [US3] Implement Jupiter quote fetcher (file: src/solana_trader/services/trade_executor.py - get_jupiter_quote)
  - Function: `async def get_jupiter_quote(input_mint: str, output_mint: str, amount: int, slippage_bps: int) -> dict`
  - Query: GET `https://quote-api.jup.ag/v6/quote`
  - Params: inputMint, outputMint, amount (in lamports), slippageBps
  - Token addresses: SOL="So11111111111111111111111111111111111111112", USDT="Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB"
  - Return: Full quote response (includes routes, price impact, expected output)
  - Apply @retry decorator
  - Test: Mock aiohttp, verify quote parsing

- [X] TRADE-005 [US3] Implement Jupiter swap transaction builder (file: src/solana_trader/services/trade_executor.py - build_swap_transaction)
  - Function: `async def build_swap_transaction(quote: dict, user_pubkey: str) -> bytes`
  - Query: POST `https://quote-api.jup.ag/v6/swap`
  - Body: {"quoteResponse": quote, "userPublicKey": user_pubkey, "wrapAndUnwrapSol": true}
  - Parse: response["swapTransaction"]
  - Decode: base64.b64decode to get transaction bytes
  - Apply @retry decorator
  - Test: Mock aiohttp, verify transaction bytes format

- [X] TRADE-006 [US3] Implement trade execution with signing (file: src/solana_trader/services/trade_executor.py - execute_trade)
  - Method: `async def execute_trade(action: str, amount_sol: float, dry_run: bool = True) -> TradeExecution`
  - Check: Trade limits (max_trade_size, max_per_day, max_per_hour)
  - Check: Circuit breaker (if price_change > 20% in 1 hour, abort)
  - Determine mints: BUY (USDT→SOL), SELL (SOL→USDT)
  - Convert amount: SOL to lamports (amount * 1e9)
  - Get quote: Call get_jupiter_quote
  - Build tx: Call build_swap_transaction
  - Sign: `from solders.transaction import VersionedTransaction; tx = VersionedTransaction.from_bytes(tx_bytes); signed_tx = wallet_keypair.sign_message(tx.message.serialize())`
  - Send: `signature = await solana_client.send_raw_transaction(signed_tx.serialize())`
  - Confirm: Wait for confirmation (30s timeout)
  - Record: Create TradeExecution with status, signature, gas_fee
  - Dry-run: If dry_run=True, return status="dry_run" without sending
  - Error handling: Catch all exceptions, set status="failed", error_message
  - Test: Integration test with dry-run mode enabled

### Storage

- [X] TRADE-007 [US3] Implement trade execution persistence (file: src/solana_trader/services/storage.py - save_trade_execution)
  - Function: `async def save_trade_execution(execution: TradeExecution) -> int`
  - Insert into trade_executions table
  - Return: Row ID of inserted record
  - Test: Verify INSERT and SELECT with sample TradeExecution

### Manual Trading CLI (for testing)

- [X] TRADE-008 [US3] Create manual trading CLI script (file: src/solana_trader/scripts/manual_trade.py)
  - CLI args: `--action BUY|SELL --amount 0.01 [--dry-run]`
  - Load config from .env
  - Initialize WalletManager and TradeExecutor
  - Execute trade with provided params
  - Print: Quote details, transaction signature, execution time
  - Usage: `uv run python -m solana_trader.scripts.manual_trade --action BUY --amount 0.01 --dry-run`
  - Test: Run with dry-run, verify output format

### Mainnet Testing Checklist

- [ ] TRADE-009 [US3] Mainnet trading validation (manual test)
  - Prerequisites:
    - Fund test wallet with 0.1 SOL + 5 USDT
    - Set SOLANA_RPC_URL to mainnet or paid RPC (QuickNode/Helius)
    - Verify wallet balance: `uv run python -c "from solana_trader.wallet import WalletManager; import asyncio; wm = WalletManager(); print(asyncio.run(wm.get_balance()))"`
  - Test 1: Dry-run BUY
    - Run: `uv run python -m solana_trader.scripts.manual_trade --action BUY --amount 0.01 --dry-run`
    - Verify: Quote returned, no transaction sent, status="dry_run"
  - Test 2: Dry-run SELL
    - Run: `uv run python -m solana_trader.scripts.manual_trade --action SELL --amount 0.01 --dry-run`
    - Verify: Quote returned, no transaction sent, status="dry_run"
  - Test 3: Real BUY (⚠️ COSTS REAL MONEY)
    - Run: `uv run python -m solana_trader.scripts.manual_trade --action BUY --amount 0.01`
    - Verify: Transaction signature returned, check on Solscan.io
    - Verify: Wallet balance updated (SOL decreased, USDT increased)
  - Test 4: Real SELL (⚠️ COSTS REAL MONEY)
    - Run: `uv run python -m solana_trader.scripts.manual_trade --action SELL --amount 0.01`
    - Verify: Transaction signature returned, check on Solscan.io
    - Verify: Wallet balance updated (SOL increased, USDT decreased)
  - Document: All transaction signatures, execution times, gas fees in logs

---

## Phase 4: LLM Trading Control (🎯 PRIORITY 2)

**Estimated Time**: 4 hours
**Parallel Tasks**: 3 (LLM-001, LLM-002, LLM-003 can run concurrently after TRADE-006 completes)
**🎯 FOCUS**: Enable LLM to control real Solana trades

### Data Models

- [ ] LLM-001 [P] [US2] Implement TradingSignal Pydantic model (file: src/solana_trader/models/trading_signal.py)
  - Fields: timestamp, signal, confidence, rationale, suggested_amount_sol
  - Fields: market_conditions, llm_model, analysis_duration_sec
  - Validation: signal in ["BUY", "SELL", "HOLD"], confidence 0-1, rationale min 10 chars
  - Add validator for rationale whitespace check
  - Test: Validate with contract schema examples from llm-signals.schema.json

### LangChain Tools (v1.0+ @tool decorator pattern)

- [ ] LLM-002 [P] [US2] Implement execute_trade tool (file: src/solana_trader/langchain_tools/execute_trade.py)
  - Decorator: `@tool`
  - Function: `async def solana_trade(action: str, amount: float, dry_run: bool = True) -> str`
  - Docstring: "Execute a trade on Solana via Jupiter. Args: action ('BUY' or 'SELL'), amount (SOL), dry_run (default True for safety). Returns JSON with transaction signature and execution status."
  - Call: TradeExecutor.execute_trade with params
  - Return: JSON string with transaction_signature, status, execution_duration_sec, error_message (if failed)
  - Test: Unit test with mocked TradeExecutor

- [ ] LLM-003 [P] [US2] Implement get_wallet_balance tool (file: src/solana_trader/langchain_tools/wallet_info.py)
  - Decorator: `@tool`
  - Function: `async def get_wallet_balance() -> str`
  - Docstring: "Get current wallet balances for SOL and USDT. Use this before making trading decisions to ensure sufficient funds."
  - Call: WalletManager.get_balance() for SOL, query SPL token balance for USDT
  - Return: JSON string with sol_balance, usdt_balance, wallet_address
  - Test: Unit test with mocked wallet queries

### LLM Service

- [ ] LLM-004 [US2] Implement OpenRouter client (file: src/solana_trader/services/llm_analyzer.py - LLMAnalyzer.__init__)
  - Initialize: `openai.AsyncOpenAI` with base_url="https://openrouter.ai/api/v1"
  - Load API key from BotConfiguration.openrouter_api_key
  - Model mapping: {"claude": "anthropic/claude-3.5-sonnet", "gpt4": "openai/gpt-4-turbo-preview", "deepseek": "deepseek/deepseek-chat", "gemini": "google/gemini-pro-1.5"}
  - Test: Verify client initialization, test API key validity

- [ ] LLM-005 [US2] Create LangChain agent with trading tools (file: src/solana_trader/services/llm_analyzer.py - create_trading_agent)
  - Import: `from langchain.agents import create_agent`
  - Tools list: [solana_trade, get_wallet_balance]
  - System prompt:
    ```
    You are a Solana trading bot with REAL money control.

    SAFETY RULES:
    1. ALWAYS use dry_run=True for the first call to test
    2. NEVER trade more than 0.1 SOL at once
    3. Check wallet balance before trading
    4. Provide clear rationale for every trade decision

    Available tools:
    - get_wallet_balance: Check current SOL and USDT balances
    - solana_trade: Execute BUY or SELL trade on Jupiter DEX

    When asked to trade:
    1. Check wallet balance first
    2. Make a test call with dry_run=True
    3. If dry_run succeeds, ask user for confirmation before real trade
    4. Provide transaction signature after execution
    ```
  - Agent creation: `create_agent(model=model_name, tools=tools, system_prompt=prompt)`
  - Test: Verify agent can invoke tools

- [ ] LLM-006 [US2] Implement LLM trading decision method (file: src/solana_trader/services/llm_analyzer.py - get_trading_decision)
  - Method: `async def get_trading_decision(user_prompt: str, dry_run: bool = True) -> TradingSignal`
  - Invoke agent: `await agent.invoke({"messages": [{"role": "user", "content": user_prompt}]})`
  - Parse tool calls: Extract solana_trade calls from agent response
  - Create TradingSignal: Based on agent decision (action, amount, rationale)
  - Include: llm_model, analysis_duration_sec
  - Fallback: Try fallback provider if primary fails
  - Test: Integration test with mocked OpenRouter responses

### JSON Schema Validation

- [ ] LLM-007 [US2] Implement LLM signal validator (file: src/solana_trader/services/llm_analyzer.py - validate_signal)
  - Load schema: Read contracts/llm-signals.schema.json
  - Function: `def validate_signal_json(signal_dict: dict) -> bool`
  - Validate: Use jsonschema.validate
  - Log: Validation errors with full context
  - Test: Unit test with valid/invalid signal examples from schema

### Storage

- [ ] LLM-008 [US2] Implement trading signal persistence (file: src/solana_trader/services/storage.py - save_trading_signal)
  - Function: `async def save_trading_signal(signal: TradingSignal) -> int`
  - Insert into trading_signals table with JSON market_conditions
  - Return: Row ID of inserted record
  - Test: Verify INSERT and SELECT with sample TradingSignal

### LLM Trading CLI (for testing)

- [ ] LLM-009 [US2] Create LLM trading CLI script (file: src/solana_trader/scripts/llm_trade.py)
  - CLI args: `--prompt "Your trading instruction" [--dry-run]`
  - Load config from .env
  - Initialize LLMAnalyzer
  - Send prompt to LLM agent
  - Print: Agent reasoning, tool calls, trading signal, transaction result
  - Usage: `uv run python -m solana_trader.scripts.llm_trade --prompt "Check my balance and buy 0.01 SOL worth of tokens" --dry-run`
  - Test: Run with various prompts, verify tool execution

### LLM Trading Validation

- [ ] LLM-010 [US2] LLM-controlled trading tests (manual test)
  - Prerequisites:
    - Complete TRADE-009 (manual trading working)
    - Fund wallet with 0.2 SOL + 10 USDT
    - Verify OpenRouter API key has credits
  - Test 1: Balance check
    - Prompt: "Check my current wallet balance"
    - Verify: LLM calls get_wallet_balance, returns SOL and USDT amounts
  - Test 2: Dry-run BUY
    - Prompt: "I want to buy 0.01 SOL worth of tokens, use dry-run mode"
    - Verify: LLM calls solana_trade with dry_run=True, returns quote
  - Test 3: Dry-run SELL
    - Prompt: "Sell 0.01 SOL for USDT in dry-run mode"
    - Verify: LLM calls solana_trade with dry_run=True, returns quote
  - Test 4: Real BUY with confirmation (⚠️ COSTS REAL MONEY)
    - Prompt: "Buy 0.01 SOL worth of tokens. First test with dry-run, then ask me before executing real trade."
    - Verify: LLM does dry-run first, asks for confirmation, then executes
    - Verify: Transaction signature returned, check on Solscan.io
  - Test 5: Real SELL with confirmation (⚠️ COSTS REAL MONEY)
    - Prompt: "Sell 0.01 SOL. Test first, then ask before real execution."
    - Verify: LLM does dry-run first, asks for confirmation, then executes
    - Verify: Transaction signature returned, check on Solscan.io
  - Document: All prompts, LLM reasoning, tool calls, transaction signatures

---

## Phase 5: Market Data Collection (US1)

**Estimated Time**: 3 hours
**Parallel Tasks**: 3 (DATA-001, DATA-002, DATA-003 can run concurrently)
**Note**: Deferred to after core trading is validated

### Data Models

- [ ] DATA-001 [P] [US1] Implement MarketData Pydantic model (file: src/solana_trader/models/market_data.py)
  - Fields: timestamp, source, sol_price_usd, volume_24h, price_change_24h_pct
  - Fields: quote_amount, pulse_index, liquidity_index, liquidity_value, metadata
  - Validation: price > 0, source in ["jupiter", "coingecko", "coinkarma"]
  - Add Config.json_schema_extra with example
  - Test: Validate with valid/invalid data

### Data Collection Services

- [ ] DATA-002 [P] [US1] Implement Jupiter price fetcher (file: src/solana_trader/services/data_collector.py - fetch_price_from_jupiter)
  - Async function: `async def fetch_price_from_jupiter() -> float`
  - Reuse: TRADE-004 quote endpoint
  - Parse: outAmount / 1_000_000 (USDT has 6 decimals)
  - Apply @retry decorator with max 3 attempts
  - Test: Mock aiohttp response, verify price calculation

- [ ] DATA-003 [P] [US1] Implement CoinGecko price fetcher (file: src/solana_trader/services/data_collector.py - fetch_price_from_coingecko)
  - Async function: `async def fetch_price_from_coingecko() -> float`
  - Query: GET `https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd`
  - Parse: data["solana"]["usd"]
  - Apply @retry decorator
  - Test: Mock requests response, verify parsing

- [ ] DATA-004 [US1] Implement CoinKarma integration (file: src/solana_trader/coinkarma/)
  - Copy from agentipy: karmafetch.py, dateutil.py, descrypt.py
  - Adapt: Use BotConfiguration for token and device_id
  - Functions: `fetch_pulse_index()`, `fetch_liquidity_index()`
  - Test: Mock CoinKarma API responses, verify AES decryption

- [ ] DATA-005 [US1] Implement unified data collector service (file: src/solana_trader/services/data_collector.py - DataCollector class)
  - Method: `async def collect_market_data() -> MarketData`
  - Priority: Try Jupiter first, fallback to CoinGecko on error
  - Enrich: Add CoinKarma pulse_index and liquidity_index
  - Handle: Log errors but don't crash (partial data OK)
  - Return: MarketData instance with all available fields
  - Test: Integration test with mocked API responses

### Storage

- [ ] DATA-006 [US1] Implement market data persistence (file: src/solana_trader/services/storage.py - save_market_data)
  - Function: `async def save_market_data(data: MarketData) -> int`
  - Insert into market_data table with JSON metadata
  - Return: Row ID of inserted record
  - Test: Verify INSERT and SELECT with sample MarketData

### LangChain Tools for Market Data

- [ ] DATA-007 [US1] Implement fetch_price tool (file: src/solana_trader/langchain_tools/fetch_price.py)
  - Decorator: `@tool`
  - Function: `async def solana_fetch_price(token_address: str) -> str`
  - Docstring: "Fetch current token price from Jupiter or CoinGecko..."
  - Return: JSON string with status, price_usd, volume_24h, timestamp
  - Error handling: Return error JSON on exception
  - Test: Unit test with mocked data_collector

- [ ] DATA-008 [US1] Implement get_market_data tool (file: src/solana_trader/langchain_tools/get_market_data.py)
  - Decorator: `@tool`
  - Function: `async def solana_get_market_data() -> str`
  - Docstring: "Get comprehensive market data including price, volume, sentiment..."
  - Query: Latest MarketData from storage
  - Return: JSON string with all market indicators
  - Test: Unit test with mocked storage query

- [ ] DATA-009 [US1] Implement fetch_karma_indicators tool (file: src/solana_trader/langchain_tools/fetch_karma_indicators.py)
  - Decorator: `@tool`
  - Function: `async def fetch_coinkarma_indicators() -> str`
  - Docstring: "Fetch CoinKarma Pulse Index (sentiment) and Liquidity Index..."
  - Call: coinkarma.karmafetch functions
  - Return: JSON string with pulse_index, liquidity_index, liquidity_value
  - Test: Unit test with mocked CoinKarma responses

### Main Loop Integration

- [ ] DATA-010 [US1] Implement data collection loop in main (file: src/solana_trader/main.py - data_collection_loop)
  - Method: `async def data_collection_loop(self)`
  - Interval: Every DATA_FETCH_INTERVAL_SEC (default 60s)
  - Error handling: Try/except with 5s retry delay on failure
  - Logging: Log latency for each fetch (<5s target)
  - Test: Unit test with mocked DataCollector

- [ ] DATA-011 [US1] Integrate market data into LLM analysis (file: src/solana_trader/services/llm_analyzer.py)
  - Update: create_trading_agent to include market data tools
  - Update: System prompt to include market analysis instructions
  - Update: get_trading_decision to fetch and pass market data
  - Test: Verify LLM considers market data in decisions

---

## Phase 6: Polish and Production Readiness

**Estimated Time**: 3 hours
**Parallel Tasks**: 6 (all tasks can run concurrently)

### Main Application

- [ ] POLISH-001 [P] Implement main bot orchestrator (file: src/solana_trader/main.py)
  - Class: TradingBot
  - Method: `async def run()` - main event loop
  - Signal handlers: SIGINT, SIGTERM for graceful shutdown
  - Concurrent tasks: data_collection_loop, trading_loop (if auto-trading enabled)
  - Error handling: Global exception handler with structured logging
  - Test: Integration test with all services

### Error Handling

- [ ] POLISH-002 [P] Add comprehensive error handling (file: src/solana_trader/services/trade_executor.py)
  - Handle: Network errors, RPC timeouts, insufficient balance
  - Handle: Slippage exceeded, transaction failed, signature not found
  - Retry logic: Network errors only (not logic errors)
  - Circuit breaker: Track failures, pause if >3 consecutive failures
  - Test: Simulate various error scenarios

### Documentation

- [ ] POLISH-003 [P] Update README.md with actual test results (file: README.md)
  - Add: Real transaction signatures from TRADE-009 tests
  - Add: Actual performance metrics (latency, gas fees)
  - Add: Troubleshooting section with actual errors encountered
  - Update: All example outputs with real data

- [ ] POLISH-004 [P] Update quickstart.md post-implementation (file: specs/master/quickstart.md)
  - Replace: DRAFT status with tested commands
  - Verify: All commands work as documented
  - Add: Actual test wallet setup instructions
  - Add: Real Solscan links to test transactions

### Testing

- [ ] POLISH-005 [P] Write contract tests for LLM signals (file: tests/contract/test_llm_signal_contract.py)
  - Test: Validate all examples from llm-signals.schema.json
  - Test: Verify schema validation rejects malformed signals
  - Test: Ensure Pydantic TradingSignal matches JSON schema

- [ ] POLISH-006 [P] Write performance tests (file: tests/performance/test_trade_execution.py)
  - Test: Verify quote fetch <2s
  - Test: Verify tx build <3s
  - Test: Verify signing <1s
  - Test: Verify end-to-end trade execution <30s
  - Run: Against mainnet RPC (not mocked) with network variance

### Observability

- [ ] POLISH-007 Add performance metrics logging (file: src/solana_trader/utils/logger.py)
  - Metric: jupiter_quote_latency_sec
  - Metric: transaction_build_latency_sec
  - Metric: transaction_confirmation_latency_sec
  - Metric: trades_today_count, trades_hour_count
  - Metric: llm_analysis_latency_sec
  - Log: JSON format for easy parsing by monitoring tools

---

## Revised Priority Flow

```
Phase 1: SETUP (1h)
  ↓
Phase 2: FOUNDATIONAL (2h)
  ↓
Phase 3: CORE TRADING (4h) ← 🎯 PRIORITY 1
  ├─ Manual trading CLI
  ├─ Mainnet testing
  └─ Validate Jupiter integration
  ↓
Phase 4: LLM TRADING CONTROL (4h) ← 🎯 PRIORITY 2
  ├─ LangChain tools
  ├─ LLM agent with trading tools
  └─ LLM-controlled trading tests
  ↓
Phase 5: MARKET DATA (3h) ← Deferred
  └─ Full market data pipeline
  ↓
Phase 6: POLISH (3h)
  └─ Production hardening
```

**Key Advantages**:
1. ✅ **Fastest path to real trading**: Test actual Solana swaps by Phase 3 (7 hours)
2. ✅ **LLM trading by Phase 4**: Full LLM control validated by hour 11
3. ✅ **Risk management**: Dry-run mode required, gradual progression
4. ✅ **Real-world feedback**: Test with real mainnet conditions early
5. ✅ **Market data optional**: Can be added after core trading works

---

## Story Dependency Graph (Revised)

```
SETUP → FOUND → CORE TRADING (US3) → LLM CONTROL (US2) → MARKET DATA (US1) → POLISH
                     ↑                      ↑
                🎯 PRIORITY 1         🎯 PRIORITY 2
```

**Critical Path**:
1. Setup + Foundational (3h) - Cannot parallelize
2. Core Trading (4h) - Can test manually immediately
3. LLM Control (4h) - Depends on Core Trading tools
4. Market Data (3h) - Independent, can add later
5. Polish (3h) - Final cleanup

---

## Acceptance Criteria per Phase

### Phase 3: Core Trading (PRIORITY 1)

**AC3.1**: Manual BUY trade executes successfully on mainnet
- **Test**: Run manual_trade.py with real funds
- **Criterion**: Transaction confirmed on Solscan.io, wallet balance updated

**AC3.2**: Manual SELL trade executes successfully on mainnet
- **Test**: Run manual_trade.py with real funds
- **Criterion**: Transaction confirmed on Solscan.io, wallet balance updated

**AC3.3**: Dry-run mode prevents real transactions
- **Test**: Run with --dry-run flag
- **Criterion**: Quote returned, no tx signature, status="dry_run"

**AC3.4**: Trade execution completes in <30 seconds
- **Test**: Measure end-to-end latency (quote → confirm)
- **Criterion**: Average <30s, 95th percentile <45s

### Phase 4: LLM Trading Control (PRIORITY 2)

**AC4.1**: LLM can check wallet balance via tool
- **Test**: Prompt "Check my balance"
- **Criterion**: LLM calls get_wallet_balance, returns correct amounts

**AC4.2**: LLM executes dry-run trades correctly
- **Test**: Prompt "Buy 0.01 SOL in dry-run mode"
- **Criterion**: LLM calls solana_trade with dry_run=True, returns quote

**AC4.3**: LLM executes real trades with confirmation
- **Test**: Prompt "Buy 0.01 SOL, test first then ask confirmation"
- **Criterion**: LLM does dry-run, asks user, then executes real trade

**AC4.4**: LLM provides clear rationale for trades
- **Test**: Review LLM responses
- **Criterion**: Each trade has >50 word explanation of reasoning

**AC4.5**: LLM respects safety rules
- **Test**: Prompt "Buy 1 SOL" (exceeds limit)
- **Criterion**: LLM refuses or warns, suggests safer amount

---

## MVP Scope (Revised)

**Phase 1-4 = Fully Functional Trading Bot** (11 hours)

✅ **Include**:
- Phase 1: SETUP (all tasks)
- Phase 2: FOUND (all tasks)
- Phase 3: CORE TRADING (all tasks) - **Manual + mainnet validated**
- Phase 4: LLM TRADING CONTROL (all tasks) - **LLM-controlled trading**

❌ **Defer to v2**:
- Phase 5: MARKET DATA - Can trade without automated data collection
- Phase 6: POLISH - Production hardening can be incremental

**Rationale**: MVP delivers complete trading capability (manual + LLM-controlled) without market data automation. Can manually trigger trades based on external analysis initially.

---

## Total Estimated Time (Revised)

| Phase | Tasks | Time | Parallelizable | Priority |
|-------|-------|------|----------------|----------|
| Phase 1: Setup | 7 | 1h | No (sequential) | Foundation |
| Phase 2: Foundational | 5 | 2h | Yes (5 parallel) | Foundation |
| Phase 3: Core Trading | 9 | 4h | Partial (2 parallel) | 🎯 **PRIORITY 1** |
| Phase 4: LLM Control | 10 | 4h | Partial (3 parallel) | 🎯 **PRIORITY 2** |
| Phase 5: Market Data | 11 | 3h | Partial (3 parallel) | Deferred |
| Phase 6: Polish | 7 | 3h | Yes (6 parallel) | Deferred |
| **Total** | **49** | **17h** | **19 parallelizable** | - |

**MVP Timeline (Phases 1-4)**: 11 hours
**Full Implementation**: 17 hours

**Realistic Timeline**:
- **MVP (Trading + LLM)**: 2 days (with testing)
- **Full System**: 3 days (with all features)

---

## Task Checklist Summary

- **Total Tasks**: 49
- **Phase 3 (Core Trading)**: 9 tasks - Real Solana mainnet trading
- **Phase 4 (LLM Control)**: 10 tasks - LLM-controlled trading via LangChain
- **Parallelizable Tasks**: 19
- **Critical Path**: SETUP → FOUND → CORE TRADING → LLM CONTROL
- **Technology**: Python 3.11+, uv, LangChain v1.0.3+, OpenRouter, Jupiter v6, Solana mainnet

**Next Step**: Begin with Phase 1 (SETUP), then immediately proceed to Phase 3 (CORE TRADING) to validate mainnet integration.

---

**Status**: ✅ Tasks reordered for priority trading validation. Ready for implementation.

**⚠️ IMPORTANT SAFETY NOTES**:
1. Always test with **dry-run mode first**
2. Start with **small amounts** (0.01 SOL)
3. Use a **test wallet** with minimal funds initially
4. **Document every transaction** signature for audit trail
5. Set up **alerts** for failed transactions
6. **Monitor gas fees** - should be <0.001 SOL per trade
