# Research: Solana AI Trading Bot

**Phase 0 Output** | **Date**: 2025-11-11

This document resolves all "NEEDS CLARIFICATION" items from the Technical Context and documents technology selection decisions.

---

## Research Areas

### 1. LLM Provider Selection: OpenAI vs Anthropic Claude

**Question**: Which LLM provider is better for trading decision analysis with structured JSON output?

**Research Findings**:
- **Claude 3.5 Sonnet** (Anthropic):
  - Better at structured JSON output and following multi-step instructions
  - 2x cheaper for input tokens vs GPT-4o ($3/MTok vs $6/MTok)
  - Faster response times in preliminary tests
  - More methodical, step-by-step reasoning (less likely to skip logic)
  - Real-world trading platform (NexusTrade) found Claude slightly better for cost, speed, and reasoning

- **GPT-4o** (OpenAI):
  - Strong general performance
  - More established ecosystem
  - Higher cost for high-frequency use (1440 calls/day = ~2M tokens/day input)

**Decision**: **Use Anthropic Claude 3.5 Sonnet**

**Rationale**:
1. **Cost**: At 60s intervals (1440 decisions/day), input cost is critical. Claude saves ~$6-9/day on input tokens
2. **Structured output**: Trading signals require strict JSON format (BUY/SELL/HOLD + rationale). Claude excels at this
3. **Reasoning quality**: Financial decisions need step-by-step logic - Claude's methodical approach is safer
4. **API stability**: Claude API is production-ready, well-documented

**Implementation**:
```python
# Use anthropic Python SDK
from anthropic import AsyncAnthropic
client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# JSON mode for structured output
response = await client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"}  # Ensure JSON
)
```

---

### 2. Solana Price Data Sources

**Question**: Which API should be used for SOL/USDT price data and technical indicators?

**Options Evaluated**:

1. **CoinGecko API**
   - Coverage: 12,000+ cryptocurrencies, 500+ exchanges
   - Update frequency: Demo tier allows 30 calls/min (sufficient for 60s intervals)
   - Latency: Sub-second for simple price queries
   - Cost: Free tier available (10,000 calls/month = ~333 calls/day)
   - Data: Volume-weighted average across exchanges, historical data
   - **Limitation**: Monthly cap may be tight for 24/7 operation (1440 calls/day > 333/day average)

2. **Pyth Network**
   - Update frequency: 400ms (200,000 updates/day)
   - Latency: Sub-second, on-chain oracle
   - Coverage: 380+ price feeds including SOL/USD
   - Cost: Free to query on-chain
   - **Limitation**: Requires Solana RPC connection, confidence intervals (not simple price)

3. **Jupiter API** (quote endpoint)
   - Direct integration with swap execution
   - Real-time swap rates (not historical prices)
   - No rate limit for quote endpoint (non-transactional)
   - **Best fit**: Get exact swap price before execution

**Decision**: **Hybrid approach**

**Primary**: **Jupiter Quote API** (`https://quote-api.jup.ag/v6/quote`)
- Reason: Real-time swap rates, unlimited queries, same API used for execution
- Used for: Current SOL/USDT price for trading decisions

**Backup**: **CoinGecko Simple Price API** (`/simple/price?ids=solana&vs_currencies=usd`)
- Reason: Fallback if Jupiter is down, provides market context
- Used for: Validation and historical context

**Rationale**:
1. Jupiter quote gives actual executable price (no slippage surprise)
2. CoinGecko backup ensures resilience
3. Combined approach stays within free tier limits
4. Simplicity: REST APIs, no on-chain complexity

**Implementation**:
```python
# Primary: Jupiter quote
async def get_sol_price_jupiter():
    url = "https://quote-api.jup.ag/v6/quote"
    params = {
        "inputMint": "So11111111111111111111111111111111111111112",  # SOL
        "outputMint": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDT
        "amount": "1000000000",  # 1 SOL in lamports
        "slippageBps": 50  # 0.5%
    }
    response = await aiohttp.get(url, params=params)
    data = await response.json()
    return float(data["outAmount"]) / 1_000_000  # USDT has 6 decimals

# Backup: CoinGecko
async def get_sol_price_coingecko():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": "solana", "vs_currencies": "usd"}
    response = await aiohttp.get(url, params=params)
    data = await response.json()
    return data["solana"]["usd"]
```

---

### 3. Jupiter Swap Integration

**Question**: How to execute SOL/USDT swaps using Jupiter aggregator?

**Research Findings**:
- **Jupiter Python SDK** exists (https://github.com/0xTaoDev/jupiter-python-sdk) but marked as **experimental** (not production-ready)
- **Jupiter v6 API** is the recommended approach:
  - Step 1: GET `/v6/quote` to get swap route
  - Step 2: POST `/v6/swap` to get unsigned transaction
  - Step 3: Sign transaction with wallet keypair
  - Step 4: Send to Solana RPC

**Decision**: **Use Jupiter v6 REST API directly** (not SDK)

**Rationale**:
1. SDK is experimental - avoid production risk
2. REST API is stable, well-documented
3. Direct control over transaction signing and error handling
4. Matches agentipy pattern (they also use direct API calls)

**Implementation Flow**:
```python
# Step 1: Get quote
quote_response = await aiohttp.get(
    "https://quote-api.jup.ag/v6/quote",
    params={
        "inputMint": SOL_MINT,
        "outputMint": USDT_MINT,
        "amount": amount_lamports,
        "slippageBps": 50  # 0.5% slippage
    }
)

# Step 2: Get swap transaction
swap_response = await aiohttp.post(
    "https://quote-api.jup.ag/v6/swap",
    json={
        "quoteResponse": quote_response.json(),
        "userPublicKey": str(wallet.pubkey()),
        "wrapAndUnwrapSol": True
    }
)

# Step 3: Sign and send
swap_tx = swap_response.json()["swapTransaction"]
tx_bytes = base64.b64decode(swap_tx)
signed_tx = wallet.sign_transaction(VersionedTransaction.from_bytes(tx_bytes))
signature = await solana_client.send_raw_transaction(signed_tx.serialize())
```

**Slippage Configuration**:
- Default: 50 bps (0.5%) for automated trading
- Reasoning: Balance between execution success and price protection
- Configurable via environment variable for testing

---

### 4. Async Python Long-Running Service Patterns

**Question**: Best practices for building a continuously-running async Python bot?

**Research Findings**:
- **Pattern**: Use `asyncio.run()` with main event loop + `asyncio.create_task()` for periodic tasks
- **Graceful shutdown**: Handle SIGTERM/SIGINT signals to cancel tasks cleanly
- **Error recovery**: Wrap periodic tasks in try/except with exponential backoff

**Decision**: **Event loop + scheduled tasks with signal handling**

**Implementation**:
```python
import asyncio
import signal

class TradingBot:
    def __init__(self):
        self.running = True

    async def data_collection_loop(self):
        """Run every 60 seconds"""
        while self.running:
            try:
                await self.collect_market_data()
            except Exception as e:
                logger.error(f"Data collection failed: {e}")
                await asyncio.sleep(5)  # Short retry delay
            else:
                await asyncio.sleep(60)  # Normal interval

    async def trading_loop(self):
        """Main trading logic"""
        while self.running:
            try:
                data = await self.get_latest_data()
                signal = await self.analyze_with_llm(data)
                if signal.action != "HOLD":
                    await self.execute_trade(signal)
            except Exception as e:
                logger.error(f"Trading loop error: {e}")
            await asyncio.sleep(60)

    def shutdown(self, signum, frame):
        """Signal handler for graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    async def run(self):
        # Register signal handlers
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)

        # Start concurrent tasks
        tasks = [
            asyncio.create_task(self.data_collection_loop()),
            asyncio.create_task(self.trading_loop())
        ]

        await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == "__main__":
    bot = TradingBot()
    asyncio.run(bot.run())
```

**Key Patterns**:
1. **Self-healing loops**: Exceptions don't crash the service, just logged and retried
2. **Signal handling**: Allows Docker/systemd to stop cleanly (`docker stop` sends SIGTERM)
3. **Concurrent tasks**: Data collection and trading run independently
4. **Configurable intervals**: Easy to change from 60s to other values

---

### 5. Trading Risk Management Patterns

**Question**: What safety mechanisms should be built into an automated trading bot?

**Research Findings from Trading Best Practices**:

**Standard Risk Controls**:
1. **Position Sizing**: Never risk >1-2% of portfolio per trade
2. **Maximum Trade Frequency**: Limit to prevent overtrading (e.g., max 10 trades/day)
3. **Circuit Breakers**: Pause trading on anomalies (e.g., >20% price drop in 1 hour)
4. **Dry-Run Mode**: Test without real transactions

**Decision**: **Implement tiered safety controls**

**Implementation**:
```python
# config.py
class TradingConfig:
    # Position sizing
    MAX_TRADE_SIZE_SOL: float = 0.1  # Max 0.1 SOL per trade
    MAX_PORTFOLIO_RISK_PCT: float = 2.0  # Max 2% portfolio risk

    # Frequency limits
    MAX_TRADES_PER_HOUR: int = 5
    MAX_TRADES_PER_DAY: int = 20
    MIN_TIME_BETWEEN_TRADES_SEC: int = 300  # 5 minutes

    # Circuit breakers
    MAX_PRICE_CHANGE_PCT: float = 20.0  # Halt if >20% change
    CIRCUIT_BREAKER_COOLDOWN_SEC: int = 3600  # 1 hour pause

    # Safety
    DRY_RUN_MODE: bool = True  # Default to dry-run
    REQUIRE_CONFIRMATION: bool = False  # For large trades

# trade_executor.py
class TradeExecutor:
    async def execute_trade(self, signal: TradingSignal):
        # Check frequency limits
        if self.trades_today >= self.config.MAX_TRADES_PER_DAY:
            logger.warning("Daily trade limit reached")
            return

        # Check circuit breaker
        if self.circuit_breaker_active:
            logger.warning("Circuit breaker active, skipping trade")
            return

        # Position sizing
        trade_amount = min(
            signal.amount,
            self.config.MAX_TRADE_SIZE_SOL
        )

        # Dry-run mode
        if self.config.DRY_RUN_MODE:
            logger.info(f"[DRY RUN] Would execute: {signal}")
            return

        # Execute real trade
        await self._execute_jupiter_swap(trade_amount)
```

**Rationale**:
1. **Start safe**: Default to dry-run mode, require explicit enable
2. **Multiple limits**: Prevent single bug from causing large losses
3. **Observability**: All limit hits are logged for analysis
4. **Configurable**: Easy to adjust limits based on testing

---

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| **LLM** | Anthropic Claude | 3.5 Sonnet | Best structured output, 2x cheaper, better reasoning |
| **Price Data (Primary)** | Jupiter Quote API | v6 | Real-time swap rates, unlimited free tier |
| **Price Data (Backup)** | CoinGecko API | v3 | Free tier, market validation |
| **Trade Execution** | Jupiter Swap API | v6 | Direct REST API, production-stable |
| **Blockchain** | Solana RPC | Latest | Via `solana-py` library |
| **Async Runtime** | asyncio | Python 3.11+ | Event loop + concurrent tasks |
| **Validation** | Pydantic | v2 | Data models with type safety |
| **Logging** | structlog | Latest | Structured JSON logging |
| **Storage** | SQLite | 3.x | Lightweight, no server needed |
| **Config** | python-dotenv | Latest | .env file for secrets |

---

## Alternatives Considered and Rejected

### 1. Pyth Network for Price Data
**Rejected because**: Requires on-chain RPC calls, adds complexity. Jupiter quote is simpler and equally accurate for swap execution.

### 2. OpenAI GPT-4o
**Rejected because**: 2x more expensive for input tokens. At 1440 calls/day, cost adds up. Claude performs equally well for this use case.

### 3. Jupiter Python SDK
**Rejected because**: Marked as experimental, not production-ready. Direct REST API is more stable.

### 4. WebSocket for Real-Time Prices
**Rejected because**: Unnecessary complexity for 60-second intervals. REST polling is sufficient and simpler.

### 5. PostgreSQL/MongoDB for Storage
**Rejected because**: Overkill for single-instance bot. SQLite is sufficient for trade history (~1440 records/day).

---

## Risk Mitigation Summary

| Risk | Mitigation |
|------|------------|
| API rate limits | Hybrid data sources (Jupiter + CoinGecko), respect free tier limits |
| LLM hallucination | Strict JSON schema validation, reject malformed signals |
| Network failure | Retry logic with exponential backoff (max 3 retries) |
| Solana RPC downtime | Configurable RPC endpoint, fallback to public RPC |
| Price slippage | 0.5% slippage tolerance, abort if quote differs from execution |
| Overtrading | Daily/hourly trade limits, minimum time between trades |
| Large losses | Position sizing (max 0.1 SOL/trade), circuit breakers |
| Production bugs | Dry-run mode by default, comprehensive logging |

---

## Next Steps (Phase 1)

1. Generate `data-model.md` with Pydantic schemas
2. Generate `contracts/llm-signals.schema.json` for LLM response format
3. Generate `quickstart.md` for deployment guide
4. Update agent context with confirmed technology stack

**Status**: All NEEDS CLARIFICATION items resolved ✅
