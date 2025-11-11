# LangChain Integration for Solana Trading Bot

**Date**: 2025-11-11 (Updated)
**Context**: Added LangChain agent framework based on agentipy reference implementation

---

## Overview

The Solana AI Trading Bot now uses **LangChain** as the agent orchestration framework, following the proven pattern from the agentipy project. This enables modular tool design and allows Claude LLM to dynamically select and chain operations.

---

## Key Changes

### 1. Dependencies Added

```toml
[tool.poetry.dependencies]
langchain = "^0.3.12"
langchain-anthropic = "^0.3.0"
```

### 2. Architecture Pattern (from agentipy)

**Before** (Direct API calls):
```
main.py → data_collector.py → External APIs
       → llm_analyzer.py → Claude API
       → trade_executor.py → Jupiter API
```

**After** (LangChain Agent):
```
main.py → LangChain AgentExecutor
          ↓
       Claude LLM (decides which tools to use)
          ↓
       [SolanaFetchPriceTool, SolanaTradeTool, SolanaMarketDataTool]
          ↓
       SolanaAgentKit → External APIs
```

### 3. New Directory: `langchain_tools/`

Following agentipy's `agentipy/langchain/` pattern:

```
src/solana_trader/langchain_tools/
├── __init__.py               # Export all tools
├── fetch_price.py            # SolanaFetchPriceTool(BaseTool)
├── execute_trade.py          # SolanaTradeTool(BaseTool)
└── get_market_data.py        # SolanaMarketDataTool(BaseTool)
```

Each tool:
- Inherits from `langchain.tools.BaseTool`
- Has `name`, `description`, and `args_schema` (Pydantic)
- Receives `SolanaAgentKit` instance for blockchain operations
- Implements async `_arun()` method

---

## Implementation Example

### Tool Definition (agentipy pattern)

```python
# langchain_tools/fetch_price.py
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import json

class FetchPriceInput(BaseModel):
    """Input schema for price fetch."""
    token_address: str = Field(
        description="Solana token mint address (e.g., So11...112 for SOL)"
    )

class SolanaFetchPriceTool(BaseTool):
    """Fetch current token price from Jupiter or CoinGecko."""

    name: str = "fetch_solana_price"
    description: str = """
    Fetch the current price of a Solana token in USDT.
    Returns: price_usd, volume_24h, price_change_24h_pct.
    Use this tool when you need current market data.
    """
    args_schema: Type[BaseModel] = FetchPriceInput
    solana_kit: SolanaAgentKit  # Injected dependency

    async def _arun(self, token_address: str) -> str:
        """Async execution."""
        try:
            # Primary: Jupiter Quote API
            price = await self.solana_kit.fetch_price(token_address)
            return json.dumps({
                "status": "success",
                "price_usd": price,
                "source": "jupiter"
            })
        except Exception as e:
            # Backup: CoinGecko
            return await self._fetch_from_coingecko(token_address)

    def _run(self, token_address: str) -> str:
        """Sync fallback (required by BaseTool)."""
        raise NotImplementedError("Use async version")
```

### Agent Initialization

```python
# main.py
from langchain.agents import AgentExecutor, create_structured_chat_agent
from langchain_anthropic import ChatAnthropic
from solana_trader.langchain_tools import (
    SolanaFetchPriceTool,
    SolanaTradeTool,
    SolanaMarketDataTool
)
from solana_trader.agent import SolanaAgentKit

# Initialize Claude LLM
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20241022",
    api_key=config.anthropic_api_key,
    temperature=0.7
)

# Initialize Solana agent (wallet + RPC)
solana_kit = SolanaAgentKit(
    private_key=config.wallet_private_key,
    rpc_url=config.solana_rpc_url
)

# Create tools list
tools = [
    SolanaFetchPriceTool(solana_kit=solana_kit),
    SolanaTradeTool(solana_kit=solana_kit),
    SolanaMarketDataTool(solana_kit=solana_kit)
]

# Create agent with tool selection capability
agent = create_structured_chat_agent(
    llm=llm,
    tools=tools,
    prompt=trading_prompt_template
)

# Agent executor handles tool invocation
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=5
)

# Run agent
async def analyze_and_trade():
    result = await agent_executor.ainvoke({
        "input": """
        Analyze current SOL/USDT market conditions.
        If conditions are favorable (strong upward momentum, high volume),
        execute a BUY trade with 0.05 SOL.
        Otherwise, explain why conditions are not favorable.
        """
    })
    return result
```

---

## Benefits vs Direct API Calls

| Aspect | Direct Calls | LangChain Agent |
|--------|--------------|-----------------|
| **Tool Selection** | Hardcoded sequence | LLM decides dynamically |
| **Error Handling** | Manual try/except | Built-in AgentExecutor retry |
| **Extensibility** | Modify main loop | Add new tool class |
| **Observability** | Custom logging | LangChain callbacks |
| **Testing** | Mock each service | Mock individual tools |
| **Proven Pattern** | Custom | agentipy production-tested |

---

## Example Agent Flow

**User Request**: "Should I buy SOL now?"

**Agent Execution**:
1. **Tool: `fetch_solana_price`**
   - Calls Jupiter API → SOL = $42.15
   - Returns: `{"price_usd": 42.15, "volume_24h": 1.25B, "change_24h_pct": 3.2}`

2. **Tool: `get_market_data`**
   - Aggregates indicators: trend=bullish, volume=high
   - Returns: `{"trend": "bullish", "volume_assessment": "high"}`

3. **Claude LLM Analysis** (internal reasoning):
   - "SOL up 3.2% with high volume → bullish momentum"
   - "Good entry point for long position"
   - Decision: BUY with 0.05 SOL

4. **Tool: `execute_solana_trade`**
   - Calls Jupiter swap: 0.05 SOL → USDT
   - Returns: `{"status": "success", "tx": "5J8Q...xyz"}`

5. **Agent Response**:
   ```json
   {
     "action": "BUY",
     "amount_sol": 0.05,
     "rationale": "Strong bullish momentum (+3.2%) with high volume...",
     "transaction": "5J8Q...xyz"
   }
   ```

---

## Migration from Direct Calls

### Before (services/llm_analyzer.py)
```python
async def analyze_market(market_data: MarketData) -> TradingSignal:
    # Manual prompt construction
    prompt = f"Analyze this data: {market_data.dict()}"

    # Direct Claude API call
    response = await anthropic_client.messages.create(...)

    # Manual JSON parsing
    signal = json.loads(response.content[0].text)
    return TradingSignal(**signal)
```

### After (LangChain Agent)
```python
# main.py
result = await agent_executor.ainvoke({
    "input": "Analyze current SOL market and recommend action"
})

# Agent automatically:
# 1. Calls fetch_solana_price tool
# 2. Calls get_market_data tool
# 3. Analyzes with Claude
# 4. Optionally calls execute_solana_trade
# 5. Returns structured result
```

---

## Testing Strategy

### Unit Tests (Mock Tools)
```python
# tests/unit/test_langchain_tools.py
@pytest.mark.asyncio
async def test_fetch_price_tool():
    mock_kit = Mock(SolanaAgentKit)
    mock_kit.fetch_price.return_value = 42.15

    tool = SolanaFetchPriceTool(solana_kit=mock_kit)
    result = await tool._arun("So11111111111111111111111111111111111111112")

    assert json.loads(result)["price_usd"] == 42.15
```

### Integration Tests (Mock LLM)
```python
# tests/integration/test_agent_with_tools.py
@pytest.mark.asyncio
async def test_agent_can_fetch_and_trade():
    # Mock LLM to return specific tool calls
    mock_llm = FakeChatModel(responses=[
        AIMessage(tool_calls=[
            {"name": "fetch_solana_price", "args": {"token_address": "SOL"}},
            {"name": "execute_solana_trade", "args": {"amount": 0.05}}
        ])
    ])

    agent_executor = AgentExecutor(agent=..., tools=real_tools)
    result = await agent_executor.ainvoke({"input": "Buy 0.05 SOL"})

    assert result["output"]["status"] == "success"
```

---

## Configuration Updates

### .env (New Variables)
```env
# Existing
ANTHROPIC_API_KEY=sk-ant-...
WALLET_PRIVATE_KEY=...
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# LangChain specific (optional)
LANGCHAIN_TRACING_V2=true        # Enable LangSmith tracing
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=ls__...        # For debugging (optional)
LANGCHAIN_PROJECT=solana-trader  # Project name in LangSmith
```

### pyproject.toml
```toml
[tool.poetry.dependencies]
python = "^3.11"
anthropic = "^0.58.1"
langchain = "^0.3.12"
langchain-anthropic = "^0.3.0"
solana = "^0.35.0"
solders = "^0.21.0"
pydantic = "^2.10.4"
aiohttp = "^3.11.11"
python-dotenv = "^1.0.1"
```

---

## References

- **agentipy Source**: `agentipy/agentipy/langchain/` directory
- **Example Usage**: `agentipy/examples/langChain/CoinGecko/coingecko_chatbot.py`
- **LangChain Docs**: https://python.langchain.com/docs/modules/agents/
- **Research Document**: `specs/master/research.md` (Section 6)

---

## Next Steps

1. **Implement Core Tools** (in `/speckit.tasks`):
   - `SolanaFetchPriceTool` - Price from Jupiter/CoinGecko
   - `SolanaMarketDataTool` - Aggregate indicators
   - `SolanaTradeTool` - Execute swap via Jupiter

2. **Create Agent Prompt Template**:
   - System message with trading rules
   - Tool usage instructions
   - Output format specification

3. **Test Agent Behavior**:
   - Verify tool selection logic
   - Validate error handling
   - Confirm dry-run mode respects safety limits

---

**Status**: Design complete ✅ | Ready for implementation via `/speckit.tasks`
