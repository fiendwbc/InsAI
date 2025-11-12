# Implementation Plan: Solana AI Trading Bot

**Branch**: `master` | **Date**: 2025-11-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/master/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a lightweight Python backend service that continuously collects Solana (SOL) price data and technical indicators from external APIs, feeds this data to an LLM for trading decision analysis, and executes SOL/USDT swaps on the Solana blockchain. The system emphasizes simplicity for rapid validation, using async Python with minimal dependencies, structured logging, and dry-run mode for safe testing. Reference implementation from agentipy provides Solana integration patterns, but this implementation is streamlined for faster deployment.

## Technical Context

**Language/Version**: Python 3.11+ (matches agentipy compatibility, modern async support)
**Primary Dependencies**:
- `solana` (v0.36.6): Blockchain interaction
- `solders` (v0.26.0): Solana SDK types
- `anthropic`: Claude LLM API client (selected after research)
- `openai`: Openai LLM API
- `langchain` (v1.0.3): Agent framework and tool abstraction
- `langchain-anthropic`: LangChain integration for Claude
- `langchain-openai`: LangChain integration for Openai
- `aiohttp`: Async HTTP for API calls
- `python-dotenv`: Environment config
- `pydantic` (v2.10+): Data validation
- `requests`: Price API calls (CoinGecko/Jupiter)

**Storage**: SQLite (trading history, signals) + JSON files (config backup)
**Testing**: pytest with pytest-asyncio (async test support)
**Target Platform**: Linux/Windows server (Docker deployable)
**Project Type**: Single backend service (no frontend/API endpoints initially)
**Agent Framework**: LangChain for tool orchestration and LLM interaction patterns
**Performance Goals**:
- Data fetch: <5s per cycle (60s intervals)
- LLM analysis: <10s response time
- Trade execution: <30s end-to-end (excluding blockchain confirmation)
- Support 1 concurrent trading pair (SOL/USDT)

**Constraints**:
- Memory: <200MB steady-state (no large data caching)
- API rate limits: CoinGecko free tier (50 calls/min), OpenAI tier limits
- Network: Requires stable internet for blockchain RPC + external APIs
- Wallet: Single wallet management (no multi-wallet support initially)

**Scale/Scope**:
- MVP scope: Single trading bot instance monitoring 1 pair (SOL/USDT)
- ~500 lines of Python code (streamlined vs agentipy's extensive toolkit)
- Runs continuously as background service
- No web UI (logs and file-based monitoring only)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Review against constitution principles (`.specify/memory/constitution.md`):

- [x] **Code Quality First**: Yes - modular design with separate services for data collection, LLM analysis, and trade execution. Each function <50 lines. Type hints with Pydantic. Google-style docstrings.
- [x] **Testing Standards**: Yes - TDD planned. Unit tests (data validators, parsers), integration tests (API mocking), contract tests (LLM response format), performance tests (data fetch latency).
- [x] **UX Consistency**: Partially - No UI, but CLI/logs have actionable error messages. API errors include retry guidance. No REST API in MVP (backend service only).
- [x] **Performance Requirements**: Yes - Budgets defined: <5s data fetch, <10s LLM response, <30s trade execution. Logging includes latency metrics for monitoring.
- [x] **Observability**: Yes - Structured JSON logging (timestamp, level, service, trace_id). Metrics: trade count, success rate, latency. Critical flow: data→LLM→trade fully traceable.
- [x] **Security & Risk**: Yes - API keys in .env (never hardcoded). Wallet private key from secure env. Input validation with Pydantic. Rate limiting for APIs. Trade amount limits in config.

**Violations requiring justification**:
- None - all constitution principles aligned for MVP scope

## Project Structure

### Documentation (this feature)

```text
specs/master/
├── plan.md              # This file (/speckit.plan command output)
├── spec.md              # Feature specification (already created)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   └── llm-signals.schema.json  # LLM trading signal contract
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
src/
├── solana_trader/           # Main application package
│   ├── __init__.py
│   ├── main.py             # Entry point, orchestrates data→LLM→trade loop
│   ├── config.py           # Configuration loader (env vars, defaults)
│   ├── agent.py            # SolanaAgentKit wrapper (simplified from agentipy)
│   ├── models/             # Data models (Pydantic schemas)
│   │   ├── __init__.py
│   │   ├── market_data.py  # MarketData schema
│   │   ├── trading_signal.py  # TradingSignal schema
│   │   └── trade_execution.py # TradeExecution schema
│   ├── services/           # Business logic services
│   │   ├── __init__.py
│   │   ├── data_collector.py   # Fetch prices from CoinGecko/Jupiter
│   │   ├── llm_analyzer.py     # LangChain agent with Claude
│   │   ├── trade_executor.py   # Execute trades on Solana (Jupiter swap)
│   │   └── storage.py          # SQLite persistence for history
│   ├── langchain_tools/    # LangChain tool definitions (agentipy pattern)
│   │   ├── __init__.py
│   │   ├── fetch_price.py      # SolanaFetchPriceTool (BaseTool)
│   │   ├── execute_trade.py    # SolanaTradeTool (BaseTool)
│   │   └── get_market_data.py  # SolanaMarketDataTool (BaseTool)
│   └── utils/              # Utilities
│       ├── __init__.py
│       ├── logger.py       # Structured JSON logging setup
│       └── retry.py        # Retry logic with exponential backoff

tests/
├── unit/                   # Unit tests (isolated functions)
│   ├── test_models.py
│   ├── test_data_collector.py
│   ├── test_llm_analyzer.py
│   ├── test_langchain_tools.py
│   └── test_storage.py
├── integration/            # Integration tests (mocked APIs)
│   ├── test_data_to_llm.py
│   ├── test_llm_to_trade.py
│   └── test_agent_with_tools.py
├── contract/               # Contract tests (API/LLM response formats)
│   ├── test_llm_signal_contract.py
│   └── test_tool_schemas.py
└── performance/            # Performance tests (latency validation)
    └── test_data_fetch_latency.py

.env.example                # Environment variable template
pyproject.toml              # Poetry dependencies (Python 3.11+)
README.md                   # Project overview
```

**Structure Decision**: Single project structure selected. Backend-only service with no frontend/API. Clean separation: models (data schemas), services (business logic), langchain_tools (agent tools following agentipy BaseTool pattern), utils (cross-cutting concerns). Tests organized by type (unit/integration/contract/performance) per constitution requirements.

**LangChain Integration Pattern** (from agentipy):
- All Solana operations exposed as LangChain `BaseTool` subclasses
- Tools receive `SolanaAgentKit` instance for blockchain interaction
- Agent orchestrates tool calls via LangChain's agent framework
- Enables LLM to decide when to fetch prices, analyze data, or execute trades

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations** - All constitution principles satisfied by current design.

---

## Phase 0: Research Summary

**Status**: ✅ Completed | **Output**: `research.md`

**Key Decisions Made**:
1. **LLM Provider**: Anthropic Claude 3.5 Sonnet (2x cheaper, better structured output)
2. **Price Data**: Jupiter Quote API (primary) + CoinGecko (backup)
3. **Trade Execution**: Jupiter v6 REST API (production-stable, no experimental SDK)
4. **Async Pattern**: asyncio event loop with signal handling for graceful shutdown
5. **Risk Management**: Dry-run mode default, position sizing, circuit breakers

---

## Phase 1: Design Summary

**Status**: ✅ Completed (Updated with LangChain) | **Outputs**:
- `data-model.md` - 4 Pydantic entities with SQLite schema
- `contracts/llm-signals.schema.json` - LLM response contract
- `quickstart.md` - 15-minute deployment guide
- `research.md` - Updated with LangChain agent framework decision

**Entities Defined**:
1. `MarketData` - Price and indicators from APIs
2. `TradingSignal` - LLM decision with confidence and rationale
3. `TradeExecution` - Blockchain transaction records
4. `BotConfiguration` - Environment-based settings

**API Contract**: Strict JSON schema for LLM signals (BUY/SELL/HOLD + market_conditions)

**LangChain Integration**:
- Agent framework for tool orchestration (following agentipy pattern)
- All Solana operations wrapped as `BaseTool` subclasses
- Tools: `SolanaFetchPriceTool`, `SolanaTradeTool`, `SolanaMarketDataTool`
- Claude LLM dynamically selects and executes tools via `AgentExecutor`

---

## Constitution Re-Check (Post-Design)

*Verification after Phase 1 design completion:*

- [x] **Code Quality First**: ✅ Pydantic models enforce type safety. Services separated by responsibility. All functions designed <50 lines.
- [x] **Testing Standards**: ✅ Test structure defined in data-model.md. Unit/integration/contract/performance tests planned.
- [x] **UX Consistency**: ✅ Structured logging with clear error messages. Quickstart guide provides 15-min setup experience.
- [x] **Performance Requirements**: ✅ Targets confirmed: <5s data fetch, <10s LLM, <30s trade. Monitoring via structured logs.
- [x] **Observability**: ✅ SQLite audit trail for all decisions and trades. JSON logging with trace_id for critical flows.
- [x] **Security & Risk**: ✅ .env for secrets, Pydantic validation, dry-run default, position limits, circuit breakers defined.

**Result**: No constitution violations. Design fully compliant. ✅

---

## Complexity Tracking (Deprecated Section)

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
