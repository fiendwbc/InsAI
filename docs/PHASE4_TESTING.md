# Phase 4 LLM Trading Control Testing Guide

**Solana AI Trading Bot - LLM-Controlled Trading Functionality Testing**

Last Updated: 2025-11-13
Status: ✅ Phase 4 Implementation Complete

---

## 📋 Overview

This document provides testing procedures for Phase 4: LLM Trading Control, which enables AI agents to control real Solana trades using natural language instructions.

**Key Capabilities:**
- Natural language trading commands
- LLM agent with access to trading tools
- Multi-LLM support via OpenRouter (Claude, GPT-4, DeepSeek, Gemini)
- Safety-first approach (always dry-run first)
- Tool-based architecture (get_wallet_balance, solana_trade)

---

## 🔧 Prerequisites

### 1. Phase 3 Completion
✅ **REQUIRED**: Phase 3 tests must pass before testing Phase 4

Verify Phase 3 is working:
```bash
# Quick verification
uv run python -m solana_trader.scripts.manual_trade --action BUY --amount 0.01 --dry-run
```

If Phase 3 tests fail, refer to `docs/PHASE3_TESTING.md` first.

### 2. OpenRouter API Key

Phase 4 requires an OpenRouter API key for multi-LLM access.

**Get API Key:**
1. Sign up at https://openrouter.ai
2. Add credits to your account ($5 minimum recommended)
3. Generate API key from dashboard

**Add to `.env`:**
```env
OPENROUTER_API_KEY=sk-or-v1-your-openrouter-key-here
LLM_PROVIDER=claude                # Primary: claude, gpt4, deepseek, gemini
LLM_FALLBACK_PROVIDER=gpt4        # Backup provider
```

### 3. Test Environment
- ✅ All Phase 3 components working
- ✅ OpenRouter API key with credits
- ✅ Test wallet funded (0.2 SOL minimum for real trades)
- ✅ `DRY_RUN_MODE=true` in `.env`

---

## 🧪 Test Procedures

### Test 1: LLM Balance Check

**Purpose:** Verify LLM agent can query wallet balance using tools.

**Command:**
```bash
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Check my current wallet balance"
```

**Expected Output:**
```
================================================================================
Solana AI Trading Bot - LLM-Controlled Trading CLI
================================================================================

✓ Configuration loaded
✓ Initializing services...
✓ LLM Provider: claude (fallback: gpt4)
✓ Wallet: 7xKxY8vZ9Abc...
✓ Balance: 0.100000 SOL

User Prompt:
--------------------------------------------------------------------------------
  Check my current wallet balance
--------------------------------------------------------------------------------

🛡️  SAFETY MODE: Trades will be simulated (dry-run)

================================================================================
LLM Agent Processing...
================================================================================

> Entering new AgentExecutor chain...
> Invoking tool: get_wallet_balance
> Tool output:
{
  "status": "success",
  "wallet_address": "7xKxY8vZ9Abc...",
  "sol_balance": 0.1,
  "usdt_balance": 5.0
}
> Finished chain.

================================================================================
LLM Trading Signal
================================================================================

Signal:           HOLD
Confidence:       0.95
LLM Model:        claude
Analysis Time:    2.34s

Rationale:
--------------------------------------------------------------------------------
Your wallet currently has 0.1 SOL and 5.0 USDT. This is sufficient balance
for small test trades. No immediate trading action is recommended without
additional market analysis or specific trading instructions.
--------------------------------------------------------------------------------

Market Conditions:
  Trend:          neutral
  Volume:         unknown
  Volatility:     low
  Risk Level:     low

================================================================================

✓ LLM recommends HOLD - No trade executed
```

**Validation Checklist:**
- ☐ LLM calls `get_wallet_balance` tool
- ☐ Correct SOL balance displayed
- ☐ Signal is "HOLD" (no trading instruction)
- ☐ Rationale mentions wallet balance
- ☐ No errors in agent execution

**Status:** ☐ PASS / ☐ FAIL

---

### Test 2: LLM Dry-Run BUY Trade

**Purpose:** Test LLM agent executing BUY trade in dry-run mode.

**Command:**
```bash
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "I want to buy 0.01 SOL worth of tokens, use dry-run mode" \
  --dry-run
```

**Expected Behavior:**
1. LLM checks wallet balance first
2. LLM calls `solana_trade` with `dry_run=True`
3. Returns quote without real execution
4. Provides trading signal with rationale

**Expected Output:**
```
> Entering new AgentExecutor chain...
> Invoking tool: get_wallet_balance
> Tool output: {"status": "success", "sol_balance": 0.1, ...}

> Invoking tool: solana_trade
> Tool input: {"action": "BUY", "amount": 0.01, "dry_run": true}
> Tool output:
{
  "status": "dry_run",
  "signal": "BUY",
  "input_amount": 0.01,
  "expected_output": 0.000237,
  "execution_duration_sec": 2.1
}
> Finished chain.

================================================================================
LLM Trading Signal
================================================================================

Signal:           BUY
Confidence:       0.78
LLM Model:        claude
Analysis Time:    4.56s

Rationale:
--------------------------------------------------------------------------------
I've executed a dry-run test for buying 0.01 SOL worth of tokens. The quote
shows an expected output of 0.000237 tokens. This is a test transaction that
was not submitted to the blockchain. Your wallet balance remains unchanged.
--------------------------------------------------------------------------------
```

**Validation Checklist:**
- ☐ LLM calls `get_wallet_balance` first
- ☐ LLM calls `solana_trade` with `dry_run=True`
- ☐ Status is "dry_run"
- ☐ Expected output shown in quote
- ☐ Signal is "BUY"
- ☐ Rationale explains dry-run execution

**Status:** ☐ PASS / ☐ FAIL

---

### Test 3: LLM Dry-Run SELL Trade

**Purpose:** Test LLM agent executing SELL trade in dry-run mode.

**Command:**
```bash
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Sell 0.01 SOL for USDT in dry-run mode" \
  --dry-run
```

**Expected Output:** (Similar to Test 2, but with SELL action)

**Validation Checklist:**
- ☐ LLM executes SELL with `dry_run=True`
- ☐ Status is "dry_run"
- ☐ Signal is "SELL"
- ☐ Quote shows USDT output amount

**Status:** ☐ PASS / ☐ FAIL

---

### Test 4: LLM Multi-Step Reasoning

**Purpose:** Test LLM's ability to chain multiple tool calls.

**Command:**
```bash
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Check my balance, then recommend whether I should buy or hold based on my funds" \
  --dry-run
```

**Expected Behavior:**
1. LLM calls `get_wallet_balance`
2. LLM analyzes balance
3. LLM provides recommendation
4. May call `solana_trade` with `dry_run=True` to get quote

**Validation Checklist:**
- ☐ LLM makes multiple tool calls
- ☐ Recommendation is based on balance
- ☐ Clear reasoning provided

**Status:** ☐ PASS / ☐ FAIL

---

### Test 5: LLM Safety Rules Enforcement

**Purpose:** Verify LLM follows safety rules (always dry-run first).

**Command:**
```bash
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Buy 0.01 SOL. First test with dry-run, then ask me before executing real trade." \
  --dry-run
```

**Expected Behavior:**
1. LLM executes dry-run first
2. LLM shows dry-run results
3. LLM asks for confirmation before real trade
4. Since we're in `--dry-run` mode, no real trade happens

**Validation Checklist:**
- ☐ LLM performs dry-run first
- ☐ LLM mentions need for confirmation
- ☐ No real trade executed (due to CLI flag)

**Status:** ☐ PASS / ☐ FAIL

---

### Test 6: LLM Error Handling

**Purpose:** Test LLM behavior with invalid requests.

**Command:**
```bash
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Buy 999 SOL" \
  --dry-run
```

**Expected Behavior:**
- LLM should recognize insufficient funds
- Should refuse or warn about the trade
- May check balance first

**Validation Checklist:**
- ☐ LLM detects problem
- ☐ Clear error/warning message
- ☐ No trade executed

**Status:** ☐ PASS / ☐ FAIL

---

### Test 7: LLM Provider Fallback

**Purpose:** Test fallback to secondary LLM provider.

**Setup:**
Temporarily set invalid primary provider in `.env`:
```env
LLM_PROVIDER=invalid_model_name
LLM_FALLBACK_PROVIDER=gpt4
```

**Command:**
```bash
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Check my balance" \
  --dry-run
```

**Expected Behavior:**
- Primary provider fails
- System automatically switches to fallback
- Request succeeds with fallback provider

**Validation Checklist:**
- ☐ Primary provider error logged
- ☐ Fallback provider used
- ☐ Request succeeds
- ☐ LLM model shows "(fallback)" suffix

**Restore `.env` after test:**
```env
LLM_PROVIDER=claude
```

**Status:** ☐ PASS / ☐ FAIL

---

## ⚠️ Real Trade Testing (COSTS REAL MONEY)

**STOP! Before proceeding:**

1. ✅ All dry-run tests (1-7) passed
2. ✅ OpenRouter has sufficient credits
3. ✅ Test wallet funded (0.2 SOL minimum)
4. ✅ You understand LLM has real money control
5. ✅ You're comfortable with AI making trades

**Enable Real Trading:**

Edit `.env`:
```env
DRY_RUN_MODE=false  # Change from true
```

---

### Test 8: Real LLM-Controlled BUY (⚠️ COSTS MONEY)

**Purpose:** Execute real BUY trade controlled by LLM.

**Command:**
```bash
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Buy 0.01 SOL worth of tokens. First test with dry-run, then ask me before executing for real."
```

**Expected Flow:**
1. CLI asks for "YES" confirmation
2. LLM performs dry-run test
3. LLM shows dry-run results
4. LLM asks for confirmation
5. User types "YES"
6. LLM executes real trade
7. Transaction signature returned

**Validation Steps:**

1. **During Execution:**
   - ☐ CLI requires "YES" confirmation
   - ☐ LLM does dry-run first
   - ☐ LLM asks for trade confirmation

2. **After Execution:**
   - ☐ Transaction signature displayed
   - ☐ Status is "success"
   - ☐ Check on Solscan.io: https://solscan.io/tx/[SIGNATURE]

3. **Verify Balance:**
   ```bash
   uv run python -c "
   import asyncio
   from solana_trader.config import load_config
   from solana_trader.wallet.manager import WalletManager

   async def check():
       config = load_config()
       wallet = WalletManager(config)
       balance = await wallet.get_balance()
       print(f'Balance: {balance:.6f} SOL')

   asyncio.run(check())
   "
   ```

4. **Verify Database:**
   ```bash
   sqlite3 trading_bot.db "
   SELECT
     datetime(timestamp) as time,
     signal,
     status,
     transaction_signature,
     llm_model
   FROM trading_signals
   WHERE llm_model IS NOT NULL
   ORDER BY timestamp DESC
   LIMIT 1;
   "
   ```

**Record Transaction:**
- Transaction Signature: `____________________________________`
- LLM Model Used: `________________`
- Execution Time: `_______ seconds`
- Gas Fee: `_______ SOL`

**Status:** ☐ PASS / ☐ FAIL

---

### Test 9: Real LLM-Controlled SELL (⚠️ COSTS MONEY)

**Purpose:** Execute real SELL trade controlled by LLM.

**Command:**
```bash
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Sell 0.01 SOL. Test first, then ask before real execution."
```

**Follow same validation steps as Test 8.**

**Record Transaction:**
- Transaction Signature: `____________________________________`
- LLM Model Used: `________________`
- Execution Time: `_______ seconds`

**Status:** ☐ PASS / ☐ FAIL

---

### Test 10: Complex Multi-Step LLM Trade

**Purpose:** Test LLM's ability to handle complex instructions.

**Command:**
```bash
uv run python -m solana_trader.scripts.llm_trade \
  --prompt "Check my balance. If I have more than 0.1 SOL, buy 0.01 SOL worth with dry-run first. Show me the results and explain if this is a good trade."
```

**Expected Behavior:**
1. LLM checks balance
2. LLM evaluates condition (>0.1 SOL)
3. LLM executes conditional dry-run
4. LLM provides analysis
5. LLM asks for confirmation if proceeding

**Status:** ☐ PASS / ☐ FAIL

---

## 🐛 Troubleshooting

### Issue 1: "OpenRouter API key invalid"

**Solutions:**
1. Verify key starts with `sk-or-v1-`
2. Check OpenRouter dashboard for key status
3. Ensure account has credits
4. Regenerate API key if necessary

### Issue 2: "Agent executor timeout"

**Symptoms:** LLM agent takes too long, times out

**Solutions:**
1. Increase timeout in agent configuration
2. Try simpler prompts
3. Switch to faster LLM provider (gpt4 → deepseek)
4. Check OpenRouter service status

### Issue 3: "LLM output parsing failed"

**Symptoms:** Cannot parse LLM response into TradingSignal

**Solutions:**
1. Check LLM is returning JSON format
2. Review system prompt is being followed
3. Try different LLM provider
4. Enable DEBUG logging to see raw LLM output

### Issue 4: "Tool execution failed"

**Symptoms:** LLM tries to call tool but fails

**Solutions:**
1. Verify Phase 3 components work
2. Check wallet manager is initialized
3. Ensure trade executor is available
4. Review tool dependency injection

### Issue 5: "Fallback provider also failed"

**Symptoms:** Both primary and fallback LLMs fail

**Solutions:**
1. Check OpenRouter service status
2. Verify API key has credits for both models
3. Try different model combination
4. Check internet connectivity

---

## 📊 Test Results Summary

### Test Execution Log

| Test # | Test Name | Status | LLM Model | Duration | Notes |
|--------|-----------|--------|-----------|----------|-------|
| 1 | Balance Check | ☐ | _______ | _____s | |
| 2 | Dry-Run BUY | ☐ | _______ | _____s | |
| 3 | Dry-Run SELL | ☐ | _______ | _____s | |
| 4 | Multi-Step Reasoning | ☐ | _______ | _____s | |
| 5 | Safety Rules | ☐ | _______ | _____s | |
| 6 | Error Handling | ☐ | _______ | _____s | |
| 7 | Provider Fallback | ☐ | _______ | _____s | |
| 8 | Real BUY Trade | ☐ | _______ | _____s | TX: _______ |
| 9 | Real SELL Trade | ☐ | _______ | _____s | TX: _______ |
| 10 | Complex Multi-Step | ☐ | _______ | _____s | |

### Performance Metrics

**Target vs Actual:**
- LLM Response Time: Target < 10s, Actual: _____s
- Tool Execution Time: Target < 5s, Actual: _____s
- End-to-End Latency: Target < 15s, Actual: _____s
- Fallback Success Rate: Target 100%, Actual: _____%

### LLM Provider Comparison

| Provider | Avg Response Time | Success Rate | Cost per Request | Notes |
|----------|-------------------|--------------|------------------|-------|
| Claude 3.5 Sonnet | _____s | ____% | $_____ | |
| GPT-4 Turbo | _____s | ____% | $_____ | |
| DeepSeek | _____s | ____% | $_____ | |
| Gemini Pro | _____s | ____% | $_____ | |

### Overall Assessment

**Phase 4 LLM Trading Control: ☐ PASS / ☐ FAIL**

**Strengths:**
```
___________________________________________________________________________
___________________________________________________________________________
```

**Areas for Improvement:**
```
___________________________________________________________________________
___________________________________________________________________________
```

**Production Readiness:** ☐ Ready ☐ Needs Work

**Tester:** _________________
**Date:** ___________________
**LLM Provider Tested:** _________________

---

## ✅ Success Criteria

Phase 4 is considered successful if:

- ✅ LLM can check wallet balance via tools
- ✅ LLM can execute dry-run trades correctly
- ✅ LLM follows safety rules (dry-run first)
- ✅ LLM provides clear reasoning for decisions
- ✅ Real trades execute successfully when authorized
- ✅ Fallback provider works if primary fails
- ✅ All transactions are recorded in database
- ✅ No unauthorized trades (safety mechanisms work)

---

## 📚 Next Steps After Phase 4

Once Phase 4 tests pass:

1. **Restore Safety Mode:**
   ```env
   DRY_RUN_MODE=true  # Reset to safe mode
   ```

2. **Phase 5: Market Data Collection**
   - Add automated price fetching
   - Integrate CoinKarma indicators
   - Provide market data to LLM context
   - Enable data-driven trading decisions

3. **Phase 6: Production Polish**
   - Main bot orchestrator
   - Error handling improvements
   - Performance optimization
   - Documentation updates

---

## 🎓 Example Prompts for Testing

### Beginner Prompts
```
"Check my wallet balance"
"What is my current SOL balance?"
"Show me my account status"
```

### Intermediate Prompts
```
"Should I buy SOL right now based on my balance?"
"Analyze if this is a good time to trade"
"Execute a small test trade in dry-run mode"
```

### Advanced Prompts
```
"Check my balance, analyze market conditions, and recommend BUY/SELL/HOLD with reasoning"
"Buy 0.01 SOL if my balance is above 0.1 SOL, otherwise tell me I need more funds"
"Execute a series of test trades: first check balance, then buy 0.01 SOL in dry-run, then sell 0.01 SOL in dry-run"
```

### Safety Test Prompts
```
"Buy 1000 SOL"  # Should refuse or warn
"Sell all my SOL"  # Should ask for confirmation
"Execute 100 trades"  # Should hit rate limits
```

---

**Document Version:** 1.0
**Last Review:** 2025-11-13
**Status:** ✅ Ready for Testing
