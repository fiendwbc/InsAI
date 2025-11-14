# Phase 5: Market Data Collection - Testing Guide

## Overview

Phase 5 adds comprehensive market data collection capabilities to the Solana AI Trading Bot. The implementation includes:

- **DataCollector Service**: Unified service for collecting price, volume, and sentiment data
- **Multi-Source Integration**: Jupiter (real-time prices), CoinGecko (market data), CoinKarma (sentiment indicators)
- **LangChain Tools**: Three new tools for LLM agents to access market data
- **LLM Integration**: Enhanced trading agent with market analysis capabilities

This guide provides step-by-step testing procedures for all Phase 5 functionality.

---

## Prerequisites

### 1. Environment Setup

Ensure your `.env` file has all required credentials:

```bash
# Core Configuration
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
WALLET_PRIVATE_KEY=your_base58_private_key_here
DRY_RUN_MODE=true

# LLM Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
LLM_PROVIDER=claude
LLM_FALLBACK_PROVIDER=gpt4

# CoinKarma Configuration (required for Phase 5)
COINKARMA_TOKEN=your_coinkarma_bearer_token_here
COINKARMA_DEVICE_ID=your_coinkarma_device_id_here
```

### 2. CoinKarma Credentials

To obtain CoinKarma credentials:

1. Visit https://www.coinkarma.co/
2. Sign up and log in
3. Open browser DevTools (F12) → Network tab
4. Perform any action on the site
5. Look for API requests to `data.coinkarma.co`
6. Copy the `Authorization` header (Bearer token) to `COINKARMA_TOKEN`
7. Copy the `x-device-id` header to `COINKARMA_DEVICE_ID`

### 3. Verify Installation

```bash
cd src
uv run python -c "from solana_trader.services.data_collector import DataCollector; print('DataCollector imported successfully')"
```

---

## Test Suite

### Test 1: Jupiter Price Fetcher

**Purpose**: Verify real-time SOL price fetching from Jupiter aggregator

**Steps**:

```bash
# Create test script
cat > test_jupiter_price.py << 'EOF'
import asyncio
from solana_trader.services.data_collector import DataCollector
from solana_trader.config import load_config

async def main():
    config = load_config()
    collector = DataCollector(config)

    print("Fetching SOL price from Jupiter...")
    price = await collector.fetch_price_from_jupiter()

    print(f"✓ SOL Price (Jupiter): ${price:.2f}")
    assert price > 0, "Price should be positive"
    print("✓ Test passed: Jupiter price fetcher working")

asyncio.run(main())
EOF

# Run test
uv run python test_jupiter_price.py
```

**Expected Output**:
```
Fetching SOL price from Jupiter...
✓ SOL Price (Jupiter): $142.35
✓ Test passed: Jupiter price fetcher working
```

**Success Criteria**:
- Price is returned as a positive float
- Price is reasonable (typically $50-$500 for SOL)
- No exceptions or errors

---

### Test 2: CoinGecko Market Data

**Purpose**: Verify market data fetching from CoinGecko API

**Steps**:

```bash
# Create test script
cat > test_coingecko.py << 'EOF'
import asyncio
from solana_trader.services.data_collector import DataCollector
from solana_trader.config import load_config

async def main():
    config = load_config()
    collector = DataCollector(config)

    print("Fetching market data from CoinGecko...")
    data = await collector.fetch_price_from_coingecko()

    print(f"✓ SOL Price: ${data['price']:.2f}")
    print(f"✓ 24h Volume: ${data['volume_24h']:,.0f}")
    print(f"✓ 24h Change: {data['price_change_24h_pct']:+.2f}%")

    assert data['price'] > 0, "Price should be positive"
    assert data['volume_24h'] > 0, "Volume should be positive"
    print("✓ Test passed: CoinGecko data fetcher working")

asyncio.run(main())
EOF

# Run test
uv run python test_coingecko.py
```

**Expected Output**:
```
Fetching market data from CoinGecko...
✓ SOL Price: $142.35
✓ 24h Volume: $2,847,593,102
✓ 24h Change: +5.23%
✓ Test passed: CoinGecko data fetcher working
```

**Success Criteria**:
- Price, volume, and price change are returned
- All values are reasonable
- No API errors

---

### Test 3: CoinKarma Sentiment Indicators

**Purpose**: Verify CoinKarma Pulse Index and Liquidity Index fetching

**Steps**:

```bash
# Create test script
cat > test_coinkarma.py << 'EOF'
import asyncio
from solana_trader.coinkarma import fetch_pulse_index, fetch_liquidity_index
from solana_trader.config import load_config

async def main():
    config = load_config()

    print("Fetching CoinKarma indicators...")

    # Fetch Pulse Index (sentiment)
    pulse = await fetch_pulse_index(config)
    print(f"✓ Pulse Index: {pulse:.1f}/100")

    # Fetch Liquidity Index
    liq_data = await fetch_liquidity_index(config)
    print(f"✓ Liquidity Index: {liq_data['liquidity_index']:.1f}/100")
    print(f"✓ Liquidity Value: ${liq_data['liquidity_value']:,.2f}")

    print("✓ Test passed: CoinKarma integration working")

asyncio.run(main())
EOF

# Run test
uv run python test_coinkarma.py
```

**Expected Output**:
```
Fetching CoinKarma indicators...
✓ Pulse Index: 67.5/100
✓ Liquidity Index: 72.3/100
✓ Liquidity Value: $1,893,247.82
✓ Test passed: CoinKarma integration working
```

**Success Criteria**:
- Pulse Index is between 0-100
- Liquidity Index is between 0-100
- Liquidity Value is positive
- No decryption errors

**Troubleshooting**:
- If you get authentication errors, verify your CoinKarma credentials are correct
- Token may expire; get fresh credentials from browser DevTools
- Ensure `x-device-id` header is also set correctly

---

### Test 4: Unified Market Data Collection

**Purpose**: Test the complete data collection pipeline with fallback logic

**Steps**:

```bash
# Create test script
cat > test_unified_collector.py << 'EOF'
import asyncio
from solana_trader.services.data_collector import DataCollector
from solana_trader.config import load_config

async def main():
    config = load_config()
    collector = DataCollector(config)

    print("Collecting unified market data...")
    market_data = await collector.collect_market_data()

    print("\n=== Market Data ===")
    print(f"Source: {market_data.source}")
    print(f"Timestamp: {market_data.timestamp}")
    print(f"SOL Price: ${market_data.sol_price_usd:.2f}")

    if market_data.volume_24h:
        print(f"24h Volume: ${market_data.volume_24h:,.0f}")
    if market_data.price_change_24h_pct:
        print(f"24h Change: {market_data.price_change_24h_pct:+.2f}%")

    if market_data.pulse_index:
        print(f"Pulse Index: {market_data.pulse_index:.1f}/100")
    if market_data.liquidity_index:
        print(f"Liquidity Index: {market_data.liquidity_index:.1f}/100")
    if market_data.liquidity_value:
        print(f"Liquidity Value: ${market_data.liquidity_value:,.2f}")

    print("\n✓ Test passed: Unified data collector working")

asyncio.run(main())
EOF

# Run test
uv run python test_unified_collector.py
```

**Expected Output**:
```
Collecting unified market data...

=== Market Data ===
Source: jupiter
Timestamp: 2025-01-14 10:30:00+00:00
SOL Price: $142.35
24h Volume: $2,847,593,102
24h Change: +5.23%
Pulse Index: 67.5/100
Liquidity Index: 72.3/100
Liquidity Value: $1,893,247.82

✓ Test passed: Unified data collector working
```

**Success Criteria**:
- Price is fetched from Jupiter (primary source)
- CoinGecko data is included (volume, price change)
- CoinKarma indicators are included (Pulse, Liquidity)
- All values are reasonable
- No exceptions

**Fallback Test**:

To test CoinGecko fallback (simulate Jupiter failure):

```bash
# Temporarily modify data_collector.py to raise exception in fetch_price_from_jupiter
# Then run test again - should see "source: coingecko"
```

---

### Test 5: LangChain Market Data Tools

**Purpose**: Verify LangChain tools for LLM agents

#### Test 5.1: fetch_price Tool

```bash
cat > test_fetch_price_tool.py << 'EOF'
import asyncio
import json
from solana_trader.langchain_tools import fetch_price, set_data_collector
from solana_trader.services.data_collector import DataCollector
from solana_trader.config import load_config

async def main():
    config = load_config()
    collector = DataCollector(config)
    set_data_collector(collector)

    print("Testing fetch_price tool...")
    result = await fetch_price.ainvoke({})
    data = json.loads(result)

    print(f"✓ Price: ${data['sol_price_usd']:.2f}")
    print(f"✓ Source: {data['source']}")
    print(f"✓ Timestamp: {data['timestamp']}")
    print("✓ Test passed: fetch_price tool working")

asyncio.run(main())
EOF

uv run python test_fetch_price_tool.py
```

#### Test 5.2: get_market_data Tool

```bash
cat > test_get_market_data_tool.py << 'EOF'
import asyncio
import json
from solana_trader.langchain_tools import get_market_data, set_data_collector
from solana_trader.services.data_collector import DataCollector
from solana_trader.config import load_config

async def main():
    config = load_config()
    collector = DataCollector(config)
    set_data_collector(collector)

    print("Testing get_market_data tool...")
    result = await get_market_data.ainvoke({})
    data = json.loads(result)

    print(f"✓ Price: ${data['sol_price_usd']:.2f}")
    print(f"✓ Volume 24h: ${data['volume_24h']:,.0f}")
    print(f"✓ Pulse Index: {data['pulse_index']:.1f}")
    print(f"✓ Liquidity Index: {data['liquidity_index']:.1f}")
    print("✓ Test passed: get_market_data tool working")

asyncio.run(main())
EOF

uv run python test_get_market_data_tool.py
```

#### Test 5.3: fetch_karma_indicators Tool

```bash
cat > test_karma_tool.py << 'EOF'
import asyncio
import json
from solana_trader.langchain_tools import fetch_karma_indicators, set_data_collector
from solana_trader.services.data_collector import DataCollector
from solana_trader.config import load_config

async def main():
    config = load_config()
    collector = DataCollector(config)
    set_data_collector(collector)

    print("Testing fetch_karma_indicators tool...")
    result = await fetch_karma_indicators.ainvoke({})
    data = json.loads(result)

    print(f"✓ Pulse Index: {data['pulse_index']:.1f}")
    print(f"✓ Liquidity Index: {data['liquidity_index']:.1f}")
    print(f"✓ Liquidity Value: ${data['liquidity_value']:,.2f}")
    print("✓ Test passed: fetch_karma_indicators tool working")

asyncio.run(main())
EOF

uv run python test_karma_tool.py
```

**Success Criteria**:
- All tools return valid JSON strings
- Data is accurate and matches collector output
- Tools can be invoked by LangChain agents

---

### Test 6: LLM Agent with Market Data

**Purpose**: Verify LLM agent can use market data tools for analysis

**Test 6.1: Market Analysis Query**

```bash
cd src
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Analyze current market conditions for SOL. Check the price, volume, sentiment indicators, and provide your assessment." \
  --dry-run
```

**Expected Behavior**:
- LLM calls `get_market_data` tool
- Receives comprehensive market snapshot
- Analyzes price trends, volume, sentiment, liquidity
- Provides informed market assessment
- Returns HOLD signal with detailed rationale

**Test 6.2: Data-Driven Trading Decision**

```bash
cd src
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Check current market data and wallet balance. If conditions are favorable (high volume, positive sentiment, good liquidity), recommend a small test trade. Otherwise recommend HOLD." \
  --dry-run
```

**Expected Behavior**:
- LLM calls `get_market_data` tool first
- Analyzes all indicators (price, volume, Pulse Index, Liquidity Index)
- Calls `get_wallet_balance` to check funds
- Makes informed BUY/SELL/HOLD decision based on data
- Provides detailed rationale citing specific indicators

**Test 6.3: Price Comparison**

```bash
cd src
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Fetch the current SOL price and compare it to typical market ranges. Is it relatively high or low right now?" \
  --dry-run
```

**Expected Behavior**:
- LLM calls `fetch_price` tool
- Analyzes price level
- Provides context based on historical ranges
- Gives informed opinion on current price level

---

## Integration Testing

### Test 7: End-to-End Market-Informed Trading

**Purpose**: Full workflow from market data collection to trading decision

**Steps**:

```bash
cd src
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "You are a professional trader. First, gather all available market data (price, volume, sentiment, liquidity). Second, check my wallet balance. Third, analyze if market conditions are favorable for a small BUY trade (0.01 SOL). If favorable, do a dry-run test. Provide detailed reasoning for your decision." \
  --dry-run
```

**Expected Workflow**:

1. **Market Data Collection**:
   - LLM calls `get_market_data`
   - Receives: price, volume, 24h change, Pulse Index, Liquidity Index

2. **Wallet Balance Check**:
   - LLM calls `get_wallet_balance`
   - Confirms sufficient funds

3. **Market Analysis**:
   - Analyzes volume (high/medium/low)
   - Interprets Pulse Index (sentiment: bullish/bearish/neutral)
   - Evaluates Liquidity Index (market depth quality)
   - Considers 24h price trend

4. **Trading Decision**:
   - If favorable: BUY signal with 0.01 SOL
   - If unfavorable: HOLD signal
   - Detailed rationale citing all indicators

5. **Dry-Run Execution** (if BUY):
   - Calls `solana_trade` with `dry_run=True`
   - Verifies Jupiter quote
   - Returns execution preview

**Success Criteria**:
- All market data tools are called correctly
- LLM provides detailed analysis of each indicator
- Trading decision is well-reasoned and data-driven
- Confidence score reflects data quality
- Dry-run executes successfully if BUY recommended

---

## Performance Testing

### Test 8: Data Collection Latency

**Purpose**: Verify data collection meets performance requirements (<5s total)

```bash
cat > test_latency.py << 'EOF'
import asyncio
import time
from solana_trader.services.data_collector import DataCollector
from solana_trader.config import load_config

async def test_latencies():
    config = load_config()
    collector = DataCollector(config)

    # Test Jupiter price fetch
    start = time.time()
    await collector.fetch_price_from_jupiter()
    jupiter_time = time.time() - start
    print(f"Jupiter latency: {jupiter_time:.3f}s")

    # Test CoinGecko fetch
    start = time.time()
    await collector.fetch_price_from_coingecko()
    coingecko_time = time.time() - start
    print(f"CoinGecko latency: {coingecko_time:.3f}s")

    # Test CoinKarma fetch
    from solana_trader.coinkarma import fetch_pulse_index, fetch_liquidity_index
    start = time.time()
    await fetch_pulse_index(config)
    await fetch_liquidity_index(config)
    coinkarma_time = time.time() - start
    print(f"CoinKarma latency: {coinkarma_time:.3f}s")

    # Test unified collection
    start = time.time()
    await collector.collect_market_data()
    total_time = time.time() - start
    print(f"Unified collection latency: {total_time:.3f}s")

    # Performance checks
    assert jupiter_time < 2.0, f"Jupiter too slow: {jupiter_time:.3f}s"
    assert coingecko_time < 2.0, f"CoinGecko too slow: {coingecko_time:.3f}s"
    assert coinkarma_time < 3.0, f"CoinKarma too slow: {coinkarma_time:.3f}s"
    assert total_time < 5.0, f"Total collection too slow: {total_time:.3f}s"

    print("\n✓ All latency tests passed")

asyncio.run(test_latencies())
EOF

uv run python test_latency.py
```

**Target Latencies**:
- Jupiter: <2s
- CoinGecko: <2s
- CoinKarma: <3s
- Total unified collection: <5s

---

## Troubleshooting

### Issue: CoinKarma Authentication Failed

**Symptoms**: 401 Unauthorized or 403 Forbidden errors

**Solutions**:
1. Get fresh credentials from browser DevTools:
   - Visit https://www.coinkarma.co/
   - Open DevTools → Network tab
   - Look for `data.coinkarma.co` requests
   - Copy fresh `Authorization` and `x-device-id` headers

2. Verify `.env` format:
   ```bash
   COINKARMA_TOKEN=Bearer eyJhbGc...  # Must include "Bearer "
   COINKARMA_DEVICE_ID=8286013b4f...  # Hex string
   ```

### Issue: Jupiter Price Fetch Timeout

**Symptoms**: Timeout errors or slow responses

**Solutions**:
1. Check your internet connection
2. Verify RPC endpoint is responsive:
   ```bash
   curl -X POST https://api.mainnet-beta.solana.com \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","id":1,"method":"getHealth"}'
   ```
3. Jupiter may be rate-limiting; wait 1 minute and retry
4. Use CoinGecko fallback (automatic in unified collector)

### Issue: CoinGecko Rate Limit

**Symptoms**: 429 Too Many Requests

**Solutions**:
1. CoinGecko free tier has rate limits (50 calls/minute)
2. Add delays between requests (automatic in @retry decorator)
3. Consider CoinGecko Pro API key (optional)

### Issue: LLM Not Using Market Data Tools

**Symptoms**: LLM makes decisions without calling data tools

**Solutions**:
1. Verify tools are registered:
   ```python
   # In llm_analyzer.py
   tools = [
       get_wallet_balance,
       solana_trade,
       fetch_price,  # Should be here
       get_market_data,  # Should be here
       fetch_karma_indicators,  # Should be here
   ]
   ```

2. Make prompts more explicit:
   ```bash
   --prompt "First, use get_market_data tool to fetch current conditions..."
   ```

3. Check system prompt includes market data instructions

---

## Next Steps

After completing Phase 5 testing:

1. **Document Results**: Record actual test results, latencies, and any issues
2. **Phase 6: Polish**: Implement main bot orchestrator and production features
3. **Continuous Testing**: Re-run tests after any changes to data collection logic

---

## Summary

Phase 5 adds powerful market data capabilities to the trading bot:

✅ **Multi-source data collection** (Jupiter, CoinGecko, CoinKarma)
✅ **Sentiment indicators** (Pulse Index for market sentiment)
✅ **Liquidity metrics** (Liquidity Index for market depth)
✅ **LangChain tools** for LLM agent integration
✅ **Enhanced trading decisions** based on real market data

The bot can now make informed trading decisions using comprehensive market analysis, significantly improving decision quality over simple price-based strategies.
