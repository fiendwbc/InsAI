# Quickstart Guide: Solana AI Trading Bot

🚧 **DRAFT - Under Development** 🚧

**Status**: This guide is created before implementation as an executable specification. It will be updated with actual commands and outputs after code implementation completes.

**Target Time**: 15 minutes from clone to running

This guide walks you through setting up and running the Solana AI trading bot in dry-run mode (safe simulation without real trades).

---

## Prerequisites

Before starting, ensure you have:

- **Python 3.11+** installed (`python --version`)
- **uv** package manager (install: `pip install uv` or via installer from https://docs.astral.sh/uv/)
- **OpenRouter API key** (sign up at https://openrouter.ai - provides access to Claude, GPT-4, DeepSeek, Gemini)
- **CoinKarma credentials** (authentication token + device ID from CoinKarma dashboard)
- **Solana wallet** with private key (create with `solana-keygen new`)
- **Git** for cloning the repository

---

## Step 1: Clone and Install (5 min)

```bash
# Clone repository
cd F:\Project\AITrader\InsAI

# Install dependencies with uv (creates .venv automatically)
uv sync

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate
```

**Dependencies installed**:
- `openai` (^1.0.0) - OpenRouter SDK (OpenAI-compatible API for multi-LLM support)
- `langchain` (^1.0.3) - Agent framework with `create_agent` standard and `@tool` decorator
- `solana` (^0.35.0) - Blockchain interaction
- `solders` (^0.21.0) - Solana SDK types
- `requests` - HTTP client for CoinGecko/Jupiter/CoinKarma APIs
- `aiohttp` - Async HTTP requests
- `pydantic` (^2.10.4) - Data validation
- `python-dotenv` - Environment config
- `structlog` - Structured logging
- `pytest` - Testing framework

---

## Step 2: Configure Environment (3 min)

Create `.env` file in project root:

```bash
# Copy example template
cp .env.example .env

# Edit with your credentials
# Windows: notepad .env
# Linux/Mac: nano .env
```

**Required Configuration** (`.env`):
```env
# Multi-LLM via OpenRouter
OPENROUTER_API_KEY=sk-or-v1-...your-key-here
LLM_PROVIDER=claude                # Options: claude, gpt4, deepseek, gemini
LLM_FALLBACK_PROVIDER=gpt4

# CoinKarma Indicators (sentiment + liquidity data)
COINKARMA_TOKEN=Bearer eyJ...your-token-here
COINKARMA_DEVICE_ID=8286013b...your-device-id

# Solana Wallet (base58 private key)
# ⚠️ IMPORTANT: Use a TEST WALLET with minimal funds initially
WALLET_TYPE=private_key
WALLET_PRIVATE_KEY=your-base58-private-key-here

# Solana RPC (use public endpoint for testing)
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Safety: Start in dry-run mode (no real trades)
DRY_RUN_MODE=true

# Trading Limits (conservative defaults)
MAX_TRADE_SIZE_SOL=0.1
MAX_TRADES_PER_DAY=20
MAX_TRADES_PER_HOUR=5
SLIPPAGE_BPS=50

# Intervals (in seconds)
DATA_FETCH_INTERVAL_SEC=60
LLM_ANALYSIS_INTERVAL_SEC=60

# Logging
LOG_LEVEL=INFO
DATABASE_PATH=trading_bot.db
```

**Security Notes**:
- Never commit `.env` to git (already in `.gitignore`)
- Start with `DRY_RUN_MODE=true` for safe testing
- Use a test wallet with <$10 SOL for initial runs

---

## Step 3: Verify Configuration (2 min)

Test your setup without starting the bot:

```bash
# Run configuration test (with activated venv)
python -m solana_trader.config

# Or using uv directly:
uv run python -m solana_trader.config

# Expected output:
# ✓ OpenRouter API key: Valid (sk-or-v1-...)
# ✓ LLM Provider: claude (fallback: gpt4)
# ✓ CoinKarma Auth: Valid
# ✓ Wallet address: 7xKx...ABC
# ✓ Solana RPC: Responding (latency: 120ms)
# ✓ Dry-run mode: ENABLED (safe to test)
# ✓ Database: trading_bot.db (will be created)
```

**Troubleshooting**:
- `Invalid API key`: Check `OPENROUTER_API_KEY` in `.env`
- `CoinKarma auth failed`: Verify `COINKARMA_TOKEN` and `COINKARMA_DEVICE_ID`
- `Wallet error`: Ensure `WALLET_PRIVATE_KEY` is base58 format
- `RPC timeout`: Try alternative RPC (e.g., QuickNode, Alchemy)

---

## Step 4: Run the Bot (1 min)

Start in dry-run mode (simulates trades without blockchain execution):

```bash
# Start the trading bot (with activated venv)
python -m solana_trader.main

# Or using uv directly (automatically uses project venv):
uv run python -m solana_trader.main
```

**Expected Console Output**:
```
2025-11-11 10:30:00 | INFO | Bot starting in DRY-RUN mode (no real trades)
2025-11-11 10:30:01 | INFO | Fetching SOL price from Jupiter...
2025-11-11 10:30:02 | INFO | SOL/USDT: $42.15 (source: jupiter)
2025-11-11 10:30:03 | INFO | Sending market data to Claude for analysis...
2025-11-11 10:30:06 | INFO | LLM Signal: HOLD (confidence: 0.55)
2025-11-11 10:30:06 | INFO | Rationale: Market consolidating, no clear signals
2025-11-11 10:31:00 | INFO | Next analysis in 60 seconds...
```

**Stopping the Bot**:
- Press `Ctrl+C` (SIGINT) for graceful shutdown
- Docker: `docker stop <container_id>` sends SIGTERM

---

## Step 5: Monitor Logs and Data (2 min)

### View Structured Logs

```bash
# Tail logs in real-time (if logging to file)
tail -f logs/trading_bot.log

# Filter for specific events
grep "LLM Signal" logs/trading_bot.log
grep "Trade Execution" logs/trading_bot.log
```

### Inspect Database

```bash
# Open SQLite database
sqlite3 trading_bot.db

# View recent market data
SELECT timestamp, source, sol_price_usd, price_change_24h_pct
FROM market_data
ORDER BY timestamp DESC
LIMIT 10;

# View trading signals
SELECT timestamp, signal, confidence, rationale
FROM trading_signals
ORDER BY timestamp DESC
LIMIT 10;

# View trade executions (dry-run will show status='dry_run')
SELECT timestamp, signal, input_amount, status
FROM trade_executions
ORDER BY timestamp DESC
LIMIT 10;

# Exit SQLite
.quit
```

---

## Step 6: Enable Real Trading (Optional, Advanced)

**⚠️ WARNING**: Only proceed if you've tested thoroughly in dry-run mode and understand the risks.

### Prerequisites for Real Trading

1. **Funded Wallet**: Ensure wallet has sufficient SOL + USDT
   ```bash
   # Check balance
   solana balance <YOUR_WALLET_ADDRESS>
   ```

2. **Test with Minimal Amount**: Start with `MAX_TRADE_SIZE_SOL=0.01` (≈$0.50)

3. **Monitor Closely**: Watch first 5 trades manually

### Enable Real Trading

Edit `.env`:
```env
# Change this line
DRY_RUN_MODE=false

# Keep conservative limits
MAX_TRADE_SIZE_SOL=0.01  # Start small!
MAX_TRADES_PER_DAY=5      # Limit exposure
```

Restart bot:
```bash
uv run python -m solana_trader.main
```

**Expected Output** (real trading):
```
2025-11-11 11:00:00 | WARNING | Bot starting in LIVE mode (real trades enabled)
2025-11-11 11:00:30 | INFO | LLM Signal: BUY (confidence: 0.82)
2025-11-11 11:00:32 | INFO | Executing trade: 0.01 SOL → USDT
2025-11-11 11:00:45 | INFO | ✓ Trade successful (tx: 5J8Q...xyz)
2025-11-11 11:00:45 | INFO | Output: 0.42 USDT (expected: 0.42, slippage: 0.1%)
```

### Monitor Real Trades

```bash
# View transaction on Solana explorer
# https://solscan.io/tx/<TRANSACTION_SIGNATURE>

# Check wallet balance
solana balance <YOUR_WALLET_ADDRESS>

# Verify database records
sqlite3 trading_bot.db
SELECT * FROM trade_executions WHERE status='success' ORDER BY timestamp DESC LIMIT 5;
```

---

## Configuration Reference

### Key Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENROUTER_API_KEY` | Yes | - | OpenRouter API key for multi-LLM access |
| `LLM_PROVIDER` | No | `claude` | Primary LLM provider (claude/gpt4/deepseek/gemini) |
| `LLM_FALLBACK_PROVIDER` | No | `gpt4` | Fallback LLM provider |
| `COINKARMA_TOKEN` | Yes | - | CoinKarma authentication token |
| `COINKARMA_DEVICE_ID` | Yes | - | CoinKarma device ID |
| `WALLET_TYPE` | No | `private_key` | Wallet type (MVP: private_key only) |
| `WALLET_PRIVATE_KEY` | Yes | - | Solana wallet private key (base58) |
| `SOLANA_RPC_URL` | No | `https://api.mainnet-beta.solana.com` | Solana RPC endpoint |
| `DRY_RUN_MODE` | No | `true` | Simulate trades without execution |
| `MAX_TRADE_SIZE_SOL` | No | `0.1` | Maximum SOL per trade |
| `MAX_TRADES_PER_DAY` | No | `20` | Daily trade limit |
| `SLIPPAGE_BPS` | No | `50` | Slippage tolerance (0.5%) |
| `DATA_FETCH_INTERVAL_SEC` | No | `60` | Price fetch interval |
| `LOG_LEVEL` | No | `INFO` | Logging level (DEBUG/INFO/WARNING/ERROR) |

### Trading Limits Explained

- **`MAX_TRADE_SIZE_SOL`**: Caps individual trade size. Start with `0.01` for testing.
- **`MAX_TRADES_PER_DAY`**: Prevents overtrading. Conservative: `5-10`, Aggressive: `20-50`.
- **`SLIPPAGE_BPS`**: Price tolerance. `50` bps = 0.5% = acceptable for most trades.
- **Circuit Breaker**: Automatically pauses if SOL price changes >20% in 1 hour (hardcoded safety).

---

## Testing Strategy

### 1. Dry-Run Testing (Recommended: 24 hours)

Run bot for at least 24 hours in `DRY_RUN_MODE=true`:

- Verify LLM signals are reasonable (check `trading_signals` table)
- Confirm no crashes or errors
- Review logs for any warnings
- Validate performance budgets (data fetch <5s, LLM <10s)

### 2. Testnet Testing (Optional)

Switch to Solana devnet for real transactions without real money:

```env
SOLANA_RPC_URL=https://api.devnet.solana.com
# Request devnet SOL: https://solfaucet.com
DRY_RUN_MODE=false
```

### 3. Mainnet with Minimal Funds

Start with `MAX_TRADE_SIZE_SOL=0.01` and `MAX_TRADES_PER_DAY=5`:

- Monitor first 10 trades manually
- Verify execution prices match quotes
- Check gas fees are reasonable (<0.001 SOL)

---

## Troubleshooting

### Bot Won't Start

**Error**: `pydantic.ValidationError: OPENROUTER_API_KEY field required`
- **Fix**: Add `OPENROUTER_API_KEY=sk-or-v1-...` to `.env`

**Error**: `solana.rpc.core.RPCException: Too Many Requests`
- **Fix**: Use paid RPC (QuickNode, Helius) or reduce fetch frequency

**Error**: `KeyError: 'outAmount'` when fetching Jupiter quote
- **Fix**: Check Solana RPC is responding. Try alternative RPC endpoint.

### No Trading Signals Generated

**Issue**: Bot fetches data but LLM always returns HOLD
- **Check**: Review `market_data` table - is price data valid? Are CoinKarma indicators present?
- **Check**: OpenRouter API key has credits (https://openrouter.ai/credits)
- **Check**: Selected LLM provider is available (try switching `LLM_PROVIDER` to fallback)
- **Fix**: Increase `LOG_LEVEL=DEBUG` to see LLM prompts and responses

### Trades Failing

**Issue**: `status='failed'` in `trade_executions` table
- **Check**: Wallet has sufficient SOL + USDT for trade + gas
- **Check**: Slippage tolerance not too tight (increase to `SLIPPAGE_BPS=100` = 1%)
- **Check**: Solana network not congested (view on https://solanabeach.io)

---

## Docker Deployment (Optional)

### Build Image

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy dependency files
COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false && poetry install --no-dev

# Copy application
COPY src/ ./src/
COPY .env .env

# Run bot
CMD ["python", "-m", "solana_trader.main"]
```

### Run Container

```bash
# Build
docker build -t solana-trader-bot .

# Run
docker run -d \
  --name trading-bot \
  --env-file .env \
  -v $(pwd)/trading_bot.db:/app/trading_bot.db \
  -v $(pwd)/logs:/app/logs \
  solana-trader-bot

# View logs
docker logs -f trading-bot

# Stop
docker stop trading-bot
```

---

## Performance Benchmarks

Expected performance on standard VPS (2 CPU, 4GB RAM):

| Metric | Target | Typical |
|--------|--------|---------|
| Data fetch latency | <5s | 1-2s |
| LLM analysis latency | <10s | 3-7s |
| Trade execution (quote → tx) | <30s | 10-20s |
| Memory usage | <200MB | 80-150MB |
| Database size (7 days) | <10MB | 2-5MB |

---

## Next Steps

After successful quickstart:

1. **Review Logs**: Analyze trading signals and understand LLM reasoning
2. **Adjust Parameters**: Fine-tune intervals, limits based on observations
3. **Implement Monitoring**: Set up alerts for errors, circuit breaker triggers
4. **Backtest**: Collect dry-run data for 7-30 days, analyze performance
5. **Gradual Ramp-Up**: Start `MAX_TRADE_SIZE_SOL=0.01`, increase to `0.05`, then `0.1`

---

## Support & Resources

- **Documentation**: See `/specs/master/` for detailed specs
- **Data Model**: See `data-model.md` for entity definitions
- **LLM Contract**: See `contracts/llm-signals.schema.json` for signal format
- **Research**: See `research.md` for technology decisions

**Safety Reminder**: Always start in `DRY_RUN_MODE=true`. Never trade amounts you can't afford to lose. This bot is for educational purposes.

---

**Estimated Time**: 15 minutes ✅
**Status**: Ready to run 🚀
