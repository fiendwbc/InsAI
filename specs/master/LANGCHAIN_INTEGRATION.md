# LangChain v1.0+ Integration for Solana Trading Bot

**Date**: 2025-11-12 (Updated for v1.0.3+)
**Context**: Upgraded to LangChain v1.0+ with `create_agent` and `@tool` decorator pattern

---

## Overview

The Solana AI Trading Bot uses **LangChain v1.0+** as the agent orchestration framework. Version 1.0+ introduces a simplified, production-ready API with the `create_agent` standard and `@tool` decorator for defining tools.

**Key Benefits of v1.0+**:
- Simplified agent creation via `create_agent(model, tools, system_prompt)`
- Function-based tools using `@tool` decorator (more Pythonic)
- Built-in middleware system (PII detection, summarization, human-in-the-loop)
- Unified content blocks for cross-provider compatibility
- Production-ready foundation maintained by LangChain team

---

## Key Changes from 0.3.x

| Feature | LangChain 0.3.x (Old) | LangChain v1.0+ (New) |
|---------|----------------------|----------------------|
| **Tool Definition** | `BaseTool` classes | `@tool` decorator on functions |
| **Agent Creation** | Manual `AgentExecutor` setup | `create_agent(model, tools)` |
| **Tool Import** | `from langchain.tools import BaseTool` | `from langchain.tools import tool` |
| **Agent Import** | `from langchain.agents import AgentExecutor` | `from langchain.agents import create_agent` |
| **Message Handling** | Provider-specific | Unified `content_blocks` |

---

## Dependencies

```toml
[tool.poetry.dependencies]
langchain = "^1.0.3"      # Production-ready v1.0+ release
openai = "^1.0.0"         # For OpenRouter (multi-LLM support)
```

**Note**: No need for `langchain-anthropic` - use OpenRouter with OpenAI-compatible SDK

---

## Architecture

**Agent Orchestration Flow**:
```
main.py → create_agent(model, tools, system_prompt)
          ↓
       LLM (via OpenRouter) decides which tools to call
          ↓
       [@tool functions: fetch_price, trade, get_market_data, fetch_karma]
          ↓
       External APIs (Jupiter, CoinGecko, CoinKarma, Solana RPC)
```

**Key Components**:
1. **Agent**: Created with `create_agent`, handles tool orchestration
2. **Tools**: Async functions decorated with `@tool`
3. **OpenRouter**: Multi-LLM provider (Claude/GPT-4/DeepSeek/Gemini)
4. **System Prompt**: Defines agent behavior and trading strategy

---

## Tool Definitions (v1.0+ Pattern)

### Directory Structure

```
src/solana_trader/langchain_tools/
├── __init__.py               # Export all tools
├── fetch_price.py            # @tool: solana_fetch_price
├── execute_trade.py          # @tool: solana_trade
├── get_market_data.py        # @tool: solana_get_market_data
└── fetch_karma_indicators.py # @tool: fetch_coinkarma_indicators
```

### Example: Price Fetch Tool

```python
# langchain_tools/fetch_price.py
from langchain.tools import tool
import json
from datetime import datetime, UTC

@tool
async def solana_fetch_price(token_address: str) -> str:
    """Fetch current token price from Jupiter or CoinGecko.

    Args:
        token_address: Solana token mint address (e.g., "So11111..." for SOL)

    Returns:
        JSON string with price_usd, volume_24h, price_change_24h_pct.
        Use this tool when you need current market data for trading decisions.
    """
    try:
        # Access shared data collector service
        from ..services.data_collector import fetch_price_from_jupiter

        price_data = await fetch_price_from_jupiter(token_address)

        return json.dumps({
            "status": "success",
            "token": token_address,
            "price_usd": price_data["price"],
            "volume_24h": price_data["volume"],
            "price_change_24h_pct": price_data["change_24h"],
            "timestamp": datetime.now(UTC).isoformat()
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to fetch price: {str(e)}"
        })
```

### Example: Trade Execution Tool

```python
# langchain_tools/execute_trade.py
from langchain.tools import tool
import json

@tool
async def solana_trade(action: str, amount: float) -> str:
    """Execute a SOL/USDT trade on Solana via Jupiter.

    Args:
        action: Trade action - must be "BUY" or "SELL"
        amount: Amount of SOL to trade (must be positive, respects MAX_TRADE_SIZE)

    Returns:
        JSON string with transaction_signature, status, actual_output_amount.
        IMPORTANT: Check dry_run_mode before calling. Returns error if limits exceeded.
    """
    try:
        from ..services.trade_executor import TradeExecutor
        from ..config import BotConfiguration

        config = BotConfiguration()
        executor = TradeExecutor(config)

        # Validate action
        if action not in ["BUY", "SELL"]:
            return json.dumps({
                "status": "error",
                "message": "Invalid action. Must be 'BUY' or 'SELL'"
            })

        # Execute trade
        result = await executor.execute_trade(action, amount)

        return json.dumps({
            "status": "success" if result.success else "failed",
            "transaction_signature": result.tx_signature,
            "input_amount": amount,
            "output_amount": result.output_amount,
            "dry_run": config.dry_run_mode
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Trade execution failed: {str(e)}"
        })
```

### Example: CoinKarma Indicators Tool

```python
# langchain_tools/fetch_karma_indicators.py
from langchain.tools import tool
import json
from datetime import datetime, timedelta

@tool
async def fetch_coinkarma_indicators(symbol: str = "solusdt") -> str:
    """Fetch sentiment and liquidity indicators from CoinKarma.

    Args:
        symbol: Token symbol (default: "solusdt" for SOL/USDT pair)

    Returns:
        JSON string with pulse_index (sentiment 0-100), liquidity_index, liquidity_value.
        Higher pulse_index = more bullish sentiment. Use for sentiment-based trading signals.
    """
    try:
        from ..coinkarma.karmafetch import get_pulse_index, get_liq_index
        from ..config import BotConfiguration

        config = BotConfiguration()
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Fetch indicators
        pulse = await get_pulse_index(yesterday, today, config.coinkarma_token, config.coinkarma_device_id)
        liq = await get_liq_index(symbol, yesterday, today, config.coinkarma_token, config.coinkarma_device_id)

        # Get latest values
        latest_pulse = pulse[-1] if pulse else None
        latest_liq = liq[-1] if liq else None

        return json.dumps({
            "status": "success",
            "symbol": symbol,
            "pulse_index": latest_pulse["value"] if latest_pulse else None,
            "liquidity_index": latest_liq["liq"] if latest_liq else None,
            "liquidity_value": latest_liq["value"] if latest_liq else None,
            "timestamp": datetime.now(UTC).isoformat()
        })
    except Exception as e:
        return json.dumps({
            "status": "error",
            "message": f"Failed to fetch CoinKarma indicators: {str(e)}"
        })
```

---

## Agent Setup (v1.0+ Pattern)

### Agent Initialization

```python
# services/llm_analyzer.py
from langchain.agents import create_agent
from openai import AsyncOpenAI
from ..langchain_tools import (
    solana_fetch_price,
    solana_trade,
    solana_get_market_data,
    fetch_coinkarma_indicators
)
from ..config import BotConfiguration

class LLMAnalyzer:
    def __init__(self, config: BotConfiguration):
        self.config = config

        # Initialize OpenRouter client
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=config.openrouter_api_key
        )

        # Model mapping
        self.models = {
            "claude": "anthropic/claude-3.5-sonnet",
            "gpt4": "openai/gpt-4-turbo-preview",
            "deepseek": "deepseek/deepseek-chat",
            "gemini": "google/gemini-pro-1.5"
        }

        # Create agent with LangChain v1.0+
        self.agent = create_agent(
            model=self.models[config.llm_provider],
            tools=[
                solana_fetch_price,
                solana_trade,
                solana_get_market_data,
                fetch_coinkarma_indicators
            ],
            system_prompt=self._build_system_prompt()
        )

    def _build_system_prompt(self) -> str:
        """Build system prompt for trading agent."""
        return """You are an expert Solana trading bot analyzing SOL/USDT markets.

Your responsibilities:
1. Fetch current SOL price using solana_fetch_price
2. Check sentiment/liquidity using fetch_coinkarma_indicators
3. Analyze market conditions and generate trading signals
4. Execute trades via solana_trade when confidence is high (>0.75)

Trading rules:
- ALWAYS check current price before trading
- Consider CoinKarma sentiment in your analysis
- Respect position limits (MAX_TRADE_SIZE from config)
- Generate clear rationale for each decision
- Default to HOLD unless strong signal

Output format:
- signal: "BUY" | "SELL" | "HOLD"
- confidence: 0.0 to 1.0
- rationale: Clear explanation of decision
- market_conditions: Key factors influencing decision
"""

    async def analyze(self, user_query: str = "Analyze current market and recommend action"):
        """Run agent analysis."""
        result = await self.agent.invoke({
            "messages": [
                {"role": "user", "content": user_query}
            ]
        })
        return result
```

### Main Loop Integration

```python
# main.py
import asyncio
from services.llm_analyzer import LLMAnalyzer
from config import BotConfiguration
import logging

async def main():
    config = BotConfiguration()
    analyzer = LLMAnalyzer(config)

    logging.info(f"Bot starting in {'DRY-RUN' if config.dry_run_mode else 'LIVE'} mode")
    logging.info(f"LLM Provider: {config.llm_provider} (fallback: {config.llm_fallback_provider})")

    try:
        while True:
            # Agent decides what tools to call and in what order
            result = await analyzer.analyze()

            # Agent automatically calls tools and returns final recommendation
            logging.info(f"Agent result: {result}")

            # Wait for next analysis cycle
            await asyncio.sleep(config.llm_analysis_interval_sec)

    except KeyboardInterrupt:
        logging.info("Shutting down gracefully...")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Testing Tools

### Unit Test Example

```python
# tests/unit/test_langchain_tools.py
import pytest
import json
from langchain_tools.fetch_price import solana_fetch_price

@pytest.mark.asyncio
async def test_fetch_price_success(mocker):
    """Test price fetch tool returns valid data."""
    # Mock the data collector
    mock_fetch = mocker.patch("services.data_collector.fetch_price_from_jupiter")
    mock_fetch.return_value = {
        "price": 42.15,
        "volume": 1_250_000_000,
        "change_24h": 3.2
    }

    # Call tool
    result = await solana_fetch_price("So11111111111111111111111111111111111111112")

    # Parse result
    data = json.loads(result)
    assert data["status"] == "success"
    assert data["price_usd"] == 42.15
    assert "timestamp" in data

@pytest.mark.asyncio
async def test_fetch_price_error(mocker):
    """Test price fetch tool handles errors gracefully."""
    # Mock failure
    mock_fetch = mocker.patch("services.data_collector.fetch_price_from_jupiter")
    mock_fetch.side_effect = Exception("API timeout")

    # Call tool
    result = await solana_fetch_price("invalid_address")

    # Parse result
    data = json.loads(result)
    assert data["status"] == "error"
    assert "API timeout" in data["message"]
```

---

## Migration from 0.3.x to v1.0+

### Code Changes Required

1. **Update Dependencies** (`pyproject.toml`):
   ```toml
   langchain = "^0.3.12"  # OLD
   langchain = "^1.0.3"   # NEW
   ```

2. **Replace BaseTool Classes with @tool Functions**:
   ```python
   # OLD (0.3.x)
   class SolanaFetchPriceTool(BaseTool):
       name = "fetch_price"
       async def _arun(self, input: str):
           # implementation

   # NEW (v1.0+)
   @tool
   async def solana_fetch_price(token_address: str) -> str:
       """Docstring becomes tool description."""
       # implementation
   ```

3. **Replace AgentExecutor with create_agent**:
   ```python
   # OLD (0.3.x)
   agent = create_structured_chat_agent(llm, tools, prompt)
   executor = AgentExecutor(agent=agent, tools=tools)

   # NEW (v1.0+)
   agent = create_agent(model="anthropic/claude-3.5-sonnet", tools=tools, system_prompt=prompt)
   ```

4. **Update Imports**:
   ```python
   # OLD
   from langchain.tools import BaseTool
   from langchain.agents import AgentExecutor, create_structured_chat_agent

   # NEW
   from langchain.tools import tool
   from langchain.agents import create_agent
   ```

---

## Best Practices

### Tool Design

1. **Always return JSON strings** - Makes parsing easier for LLM and humans
2. **Include status field** - `"success"` or `"error"` for error handling
3. **Detailed docstrings** - LLM reads this to understand when to use tool
4. **Type hints** - Helps LangChain validate inputs
5. **Async execution** - All tools should be async for performance

### Agent Configuration

1. **Clear system prompts** - Define trading rules and output format
2. **Tool selection** - Only include tools relevant to current task
3. **Error handling** - Tools should catch exceptions and return error JSON
4. **Logging** - Use structured logging for observability

### Security

1. **Validate inputs** - Check action/amount before executing trades
2. **Respect limits** - MAX_TRADE_SIZE, MAX_TRADES_PER_DAY, etc.
3. **Dry-run default** - Always start with DRY_RUN_MODE=true
4. **No hardcoded secrets** - Use environment variables

---

## Extensibility

### Adding New Tools

```python
# langchain_tools/new_tool.py
from langchain.tools import tool

@tool
async def my_new_tool(param: str) -> str:
    """Tool description for LLM.

    Args:
        param: Parameter description

    Returns:
        JSON string with result
    """
    # Implementation
    return json.dumps({"status": "success", "result": ...})
```

Then register in agent:
```python
from ..langchain_tools import my_new_tool

agent = create_agent(
    model="anthropic/claude-3.5-sonnet",
    tools=[solana_fetch_price, solana_trade, my_new_tool],  # Add here
    system_prompt=prompt
)
```

---

## Advantages Over Direct API Calls

1. **Dynamic Orchestration**: LLM decides tool call order based on context
2. **Modularity**: Each operation is self-contained and testable
3. **Extensibility**: Add new data sources/strategies by adding tools
4. **Observability**: LangChain provides built-in callbacks and logging
5. **Error Handling**: Tools return structured error messages
6. **Reusability**: Tools can be shared across different agents
7. **Type Safety**: Pydantic validation on tool inputs

---

## Resources

- **LangChain v1.0 Docs**: https://docs.langchain.com/oss/python/releases/langchain-v1
- **OpenRouter API**: https://openrouter.ai/docs
- **Tool Decorator Reference**: `from langchain.tools import tool`
- **Agent Creation**: `from langchain.agents import create_agent`

---

**Status**: LangChain v1.0+ integration complete ✅
**Next**: Implement tools and test agent behavior
