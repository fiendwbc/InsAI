# Phase 3 Core Trading Testing Guide

**Solana AI Trading Bot - Manual Trading Functionality Testing**

Last Updated: 2025-11-13
Status: ✅ Phase 3 Implementation Complete

---

## 📋 Overview

This document provides step-by-step instructions for testing the Phase 3 core trading capabilities, including:
- Configuration validation
- Wallet connectivity
- Jupiter integration (quote fetching)
- Dry-run trade execution (safe testing)
- Real trade execution (mainnet validation)

---

## 🔧 Prerequisites

Before testing, ensure you have:

### 1. Environment Setup
- ✅ Python 3.11+ installed
- ✅ uv package manager installed
- ✅ All dependencies installed (`uv sync` completed)
- ✅ `.env` file created from `.env.example`

### 2. Required Credentials

Add these to your `.env` file:

```env
# Solana Configuration
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com  # Or paid RPC (QuickNode/Helius)
WALLET_TYPE=private_key
WALLET_PRIVATE_KEY=your-base58-private-key-here

# OpenRouter (for future LLM phases)
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LLM_PROVIDER=claude

# CoinKarma (for future data collection phases)
COINKARMA_TOKEN=Bearer your-token-here
COINKARMA_DEVICE_ID=your-device-id-here

# Safety Settings
DRY_RUN_MODE=true  # ALWAYS start with true!
MAX_TRADE_SIZE_SOL=0.1
SLIPPAGE_BPS=50
```

### 3. Test Wallet Setup

**⚠️ IMPORTANT: Use a TEST WALLET only!**

```bash
# Create a new test wallet (if needed)
solana-keygen new --outfile test-wallet.json

# Get the private key in base58 format
solana-keygen encode test-wallet.json

# Fund the test wallet with minimal SOL (~0.1 SOL)
# Use a faucet or transfer from your main wallet
```

**Recommended Test Funds:**
- Dry-run testing: No funds needed
- Real trade testing: 0.1 SOL + 5 USDT minimum

---

## 🧪 Test Procedures

### Test 1: Configuration Validation

**Purpose:** Verify all configuration is loaded correctly.

**Command:**
```bash
uv run python -m solana_trader.config
```

**Expected Output:**
```
✓ Configuration loaded successfully

✓ OpenRouter API key: ********************abcdefgh
✓ LLM Provider: claude (fallback: gpt4)
✓ CoinKarma Auth: Valid
✓ Wallet type: private_key
✓ Solana RPC: https://api.mainnet-beta.solana.com
✓ Dry-run mode: ENABLED (safe to test)
✓ Database: trading_bot.db
✓ Max trade size: 0.1 SOL
✓ Daily limit: 20 trades

All configuration checks passed ✓
```

**Troubleshooting:**
- ❌ "Configuration validation failed": Check your `.env` file
- ❌ "Invalid API key": Verify OPENROUTER_API_KEY format
- ❌ "Wallet error": Ensure WALLET_PRIVATE_KEY is base58 format
- ❌ "CoinKarma auth failed": Check COINKARMA_TOKEN starts with "Bearer "

**Status:** ☐ PASS / ☐ FAIL

---

### Test 2: Wallet Balance Check

**Purpose:** Verify wallet connectivity and fetch SOL balance.

**Command:**
```bash
uv run python -c "
import asyncio
from solana_trader.config import load_config
from solana_trader.wallet.manager import WalletManager

async def test():
    config = load_config()
    wallet = WalletManager(config)
    print(f'Wallet Address: {wallet.get_public_key()}')
    balance = await wallet.get_balance()
    print(f'SOL Balance: {balance:.6f} SOL')

asyncio.run(test())
"
```

**Expected Output:**
```
Wallet Address: 7xKxY8vZ9Abc...
SOL Balance: 0.100000 SOL
```

**Troubleshooting:**
- ❌ "Failed to initialize wallet": Invalid private key format
- ❌ "Failed to fetch wallet balance": RPC connection issue
- ❌ Balance is 0: Fund the wallet from faucet or main wallet

**Status:** ☐ PASS / ☐ FAIL

---

### Test 3: Dry-Run BUY Trade

**Purpose:** Test Jupiter quote fetching for BUY action (USDT→SOL) without executing.

**Command:**
```bash
uv run python -m solana_trader.scripts.manual_trade \
  --action BUY \
  --amount 0.01 \
  --dry-run
```

**Expected Output:**
```
================================================================================
Solana AI Trading Bot - Manual Trade CLI
================================================================================

✓ Configuration loaded
✓ Initializing services...
✓ Wallet: 7xKxY8vZ9Abc...
✓ Balance: 0.100000 SOL

Trade Parameters:
--------------------------------------------------------------------------------
  Action:       BUY
  Amount:       0.01 SOL
  Slippage:     50 bps (0.50%)
  Mode:         DRY-RUN (no real trade)
--------------------------------------------------------------------------------

Executing trade...

================================================================================
Trade Execution Results
================================================================================

Status:           DRY_RUN
Signal:           BUY
Input Token:      Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB
Output Token:     So11111111111111111111111111111111111111112
Input Amount:     0.01 SOL
Expected Output:  0.000237

Duration:         2.34s

✓ Dry-run completed successfully!

Next steps:
1. Review quote details above
2. If satisfied, run without --dry-run flag
3. Always start with small amounts (0.01 SOL)
================================================================================
```

**Validation Checklist:**
- ☐ Status is "DRY_RUN"
- ☐ Expected output amount is reasonable (check SOL/USDT price)
- ☐ No transaction signature (dry-run doesn't send tx)
- ☐ Duration is < 5 seconds
- ☐ No errors in output

**Status:** ☐ PASS / ☐ FAIL

---

### Test 4: Dry-Run SELL Trade

**Purpose:** Test Jupiter quote fetching for SELL action (SOL→USDT) without executing.

**Command:**
```bash
uv run python -m solana_trader.scripts.manual_trade \
  --action SELL \
  --amount 0.01 \
  --dry-run
```

**Expected Output:**
```
================================================================================
Trade Execution Results
================================================================================

Status:           DRY_RUN
Signal:           SELL
Input Token:      So11111111111111111111111111111111111111112
Output Token:     Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB
Input Amount:     0.01 SOL
Expected Output:  0.421500

Duration:         2.12s

✓ Dry-run completed successfully!
================================================================================
```

**Validation Checklist:**
- ☐ Status is "DRY_RUN"
- ☐ Expected USDT output matches current SOL price
- ☐ No transaction signature
- ☐ Duration is < 5 seconds
- ☐ No errors in output

**Status:** ☐ PASS / ☐ FAIL

---

### Test 5: Database Verification

**Purpose:** Verify dry-run trades are persisted to database.

**Command:**
```bash
sqlite3 trading_bot.db "
SELECT
  datetime(timestamp) as time,
  signal,
  input_amount,
  expected_output,
  status,
  execution_duration_sec
FROM trade_executions
ORDER BY timestamp DESC
LIMIT 5;
"
```

**Expected Output:**
```
2025-11-13 10:30:15|SELL|0.01|0.4215|dry_run|2.12
2025-11-13 10:28:42|BUY|0.01|0.000237|dry_run|2.34
```

**Validation Checklist:**
- ☐ Both BUY and SELL dry-run trades are recorded
- ☐ Status is "dry_run"
- ☐ Timestamps are correct
- ☐ Expected outputs match CLI output

**Status:** ☐ PASS / ☐ FAIL

---

## ⚠️ Real Trade Testing (COSTS REAL MONEY)

**STOP! Before proceeding:**

1. ✅ All dry-run tests (1-5) passed
2. ✅ You understand trades cannot be reversed
3. ✅ Test wallet is funded (0.1 SOL minimum)
4. ✅ You're using a TEST wallet (not main wallet)
5. ✅ Amount is small (start with 0.01 SOL)

**Enable Real Trading:**

Edit `.env`:
```env
DRY_RUN_MODE=false  # Change from true to false
```

---

### Test 6: Real BUY Trade (⚠️ COSTS MONEY)

**Purpose:** Execute a real BUY trade on Solana mainnet.

**Command:**
```bash
uv run python -m solana_trader.scripts.manual_trade \
  --action BUY \
  --amount 0.01
```

**Confirmation Required:**
```
⚠️  WARNING: You are about to execute a REAL trade with REAL money!
⚠️  This transaction cannot be reversed once confirmed on the blockchain.

Type 'YES' to confirm and proceed: YES
```

**Expected Output:**
```
================================================================================
Trade Execution Results
================================================================================

Status:           SUCCESS
Signal:           BUY
Input Token:      Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB
Output Token:     So11111111111111111111111111111111111111112
Input Amount:     0.01 SOL
Expected Output:  0.000237
Actual Output:    0.000236
Slippage:         0.42%
TX Signature:     5J8QyPzK7Vx3m9wN2hL4tY6rB8sF1eD9cG3aH5jK2mP4...
Solscan Link:     https://solscan.io/tx/5J8QyPzK7Vx3m9wN2hL4tY6rB8sF1eD9cG3aH5jK2mP4...
Gas Fee:          0.000005000 SOL
Duration:         12.45s

✓ Trade executed successfully!

Next steps:
1. Verify transaction on Solscan.io
2. Check wallet balance updates
3. Review trade record in database
================================================================================
```

**Validation Steps:**

1. **Verify on Solscan:**
   - Open the Solscan link from output
   - Confirm transaction is "Success"
   - Check SOL/USDT amounts match

2. **Check Wallet Balance:**
   ```bash
   uv run python -c "
   import asyncio
   from solana_trader.config import load_config
   from solana_trader.wallet.manager import WalletManager

   async def check():
       config = load_config()
       wallet = WalletManager(config)
       balance = await wallet.get_balance()
       print(f'New Balance: {balance:.6f} SOL')

   asyncio.run(check())
   "
   ```

3. **Verify Database Record:**
   ```bash
   sqlite3 trading_bot.db "
   SELECT
     datetime(timestamp) as time,
     signal,
     status,
     transaction_signature,
     gas_fee_sol
   FROM trade_executions
   WHERE status = 'success'
   ORDER BY timestamp DESC
   LIMIT 1;
   "
   ```

**Validation Checklist:**
- ☐ Status is "SUCCESS"
- ☐ Transaction signature is 88 characters
- ☐ Transaction confirmed on Solscan
- ☐ Slippage is within tolerance (< 1%)
- ☐ Gas fee is reasonable (< 0.001 SOL)
- ☐ Wallet balance decreased by ~0.01 SOL + gas
- ☐ Trade recorded in database

**Record Transaction Details:**
- Transaction Signature: `____________________________________`
- Execution Time: `_______ seconds`
- Gas Fee: `_______ SOL`
- Actual Slippage: `_______ %`

**Status:** ☐ PASS / ☐ FAIL

---

### Test 7: Real SELL Trade (⚠️ COSTS MONEY)

**Purpose:** Execute a real SELL trade on Solana mainnet.

**Command:**
```bash
uv run python -m solana_trader.scripts.manual_trade \
  --action SELL \
  --amount 0.01
```

**Expected Output:** (Similar to Test 6, but with SOL→USDT)

**Validation Steps:** (Same as Test 6)

**Validation Checklist:**
- ☐ Status is "SUCCESS"
- ☐ Transaction confirmed on Solscan
- ☐ Wallet balance increased by ~0.01 SOL (minus gas)
- ☐ Trade recorded in database

**Record Transaction Details:**
- Transaction Signature: `____________________________________`
- Execution Time: `_______ seconds`
- Gas Fee: `_______ SOL`
- Actual Slippage: `_______ %`

**Status:** ☐ PASS / ☐ FAIL

---

## 🐛 Troubleshooting Guide

### Common Issues

#### Issue 1: "Jupiter quote failed"
**Symptoms:** Error fetching quote from Jupiter API

**Solutions:**
1. Check Solana RPC is responding: `curl https://api.mainnet-beta.solana.com`
2. Try alternative RPC endpoint (QuickNode, Helius)
3. Verify network connectivity
4. Check Jupiter API status: https://status.jup.ag

#### Issue 2: "Transaction confirmation timeout"
**Symptoms:** Transaction sent but not confirmed within 30s

**Solutions:**
1. Check transaction on Solscan (may be pending)
2. Network congestion - wait and retry
3. Increase RPC reliability (use paid RPC)
4. Transaction may still succeed - check wallet balance

#### Issue 3: "Slippage exceeded"
**Symptoms:** Transaction fails due to price movement

**Solutions:**
1. Increase slippage tolerance: `SLIPPAGE_BPS=100` (1%)
2. Retry during lower volatility periods
3. Use smaller trade amounts
4. Check if price is moving rapidly (avoid trading)

#### Issue 4: "Insufficient funds"
**Symptoms:** Trade fails with balance error

**Solutions:**
1. Check wallet balance includes gas fees (~0.001 SOL)
2. Ensure you have both SOL and USDT for BUY trades
3. Reduce trade amount
4. Fund wallet with additional SOL

#### Issue 5: Database locked
**Symptoms:** SQLite database busy/locked error

**Solutions:**
1. Close any open SQLite connections
2. Ensure no other bot instances are running
3. Delete `trading_bot.db-wal` and `trading_bot.db-shm` files
4. Restart the script

---

## 📊 Test Results Summary

### Test Execution Log

| Test # | Test Name | Status | Duration | Notes |
|--------|-----------|--------|----------|-------|
| 1 | Configuration Validation | ☐ | _____s | |
| 2 | Wallet Balance Check | ☐ | _____s | |
| 3 | Dry-Run BUY | ☐ | _____s | |
| 4 | Dry-Run SELL | ☐ | _____s | |
| 5 | Database Verification | ☐ | _____s | |
| 6 | Real BUY Trade | ☐ | _____s | TX: ________ |
| 7 | Real SELL Trade | ☐ | _____s | TX: ________ |

### Performance Metrics

**Target vs Actual:**
- Jupiter Quote Latency: Target < 5s, Actual: _____s
- Trade Execution: Target < 30s, Actual: _____s
- Gas Fees: Target < 0.001 SOL, Actual: _____SOL
- Slippage: Target < 1%, Actual: _____%

### Overall Assessment

**Phase 3 Core Trading: ☐ PASS / ☐ FAIL**

**Notes:**
```
___________________________________________________________________________
___________________________________________________________________________
___________________________________________________________________________
```

**Tester:** _________________
**Date:** ___________________
**Environment:** ☐ Mainnet ☐ Devnet ☐ Testnet

---

## ✅ Next Steps After Phase 3 Testing

Once all tests pass:

1. **Restore Safety Mode:**
   ```env
   DRY_RUN_MODE=true  # Reset to true
   ```

2. **Document Results:**
   - Save transaction signatures
   - Record actual performance metrics
   - Note any issues encountered

3. **Ready for Phase 4:**
   Phase 4 (LLM Trading Control) can now be implemented, which will:
   - Add LangChain agent framework
   - Enable LLM to control trading via tools
   - Integrate OpenRouter for multi-LLM support
   - Create automated trading decision system

---

## 📚 References

- **Jupiter Documentation:** https://station.jup.ag/docs
- **Solana RPC API:** https://docs.solana.com/api
- **Solscan Explorer:** https://solscan.io
- **Project Documentation:** `specs/master/`
- **Configuration Guide:** `specs/master/quickstart.md`

---

**Document Version:** 1.0
**Last Review:** 2025-11-13
**Status:** ✅ Ready for Testing
