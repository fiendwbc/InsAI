# Feature Specification: Solana AI Trading Bot

**Feature Branch**: `master`
**Created**: 2025-11-11
**Status**: Draft
**Input**: User description: "从零开始创建一个后端项目,通过不断的获取solana的价格数据和其他网站提供的技术指标，输入给LLM，判断在何时交易solana/usdt，交易的实现依赖solana提供的接口。 请分析agentipy/ 文件夹中的项目作为参考，但是功能更简洁，以便快速验证功能"

## User Scenarios & Testing *(mandatory)*

**📋 PRIORITY NOTE**: Implementation order revised for faster mainnet validation - Core Trading (US3) → LLM Control (US2) → Market Data (US1). See tasks.md for detailed rationale.

---

### User Story 3 - Solana Trade Execution (Priority: P1) 🎯 MVP Phase 1

The system executes SOL/USDT trades on Solana blockchain via Jupiter aggregator, with both manual and LLM-controlled modes.

**Why this priority (UPDATED)**: Fastest path to validate core trading capability on real mainnet. Enables immediate testing of Jupiter integration, wallet management, and transaction execution without waiting for automated data collection. Can trade based on external market analysis initially, then add automation later.

**Independent Test**: Can be tested with minimal trade amounts on Solana mainnet. Verify transaction creation, signing, and on-chain confirmation. Start with dry-run mode for safety, then execute small real trades (0.01 SOL).

**Acceptance Scenarios**:

1. **Given** manual trade command is issued, **When** execution is triggered, **Then** SOL/USDT swap transaction is created and sent to Solana
2. **Given** trade is executed, **When** transaction completes, **Then** transaction signature, status, and final balances are logged
3. **Given** dry-run mode is enabled, **When** trade is attempted, **Then** quote is fetched but transaction is NOT sent to blockchain
4. **Given** insufficient balance exists, **When** trade is attempted, **Then** trade is rejected and balance warning is logged
5. **Given** trade fails, **When** error occurs, **Then** transaction is not retried, error is logged with details

---

### User Story 2 - LLM-Based Trading Control (Priority: P2) 🎯 MVP Phase 2

The system enables LLM to control real Solana trades via LangChain tools, with safety guardrails and dry-run testing.

**Why this priority (UPDATED)**: After core trading is validated (US3-P1), add LLM control layer. This allows LLM to execute trades based on natural language instructions while maintaining safety through dry-run defaults and confirmation workflows. More valuable than automated data collection for rapid experimentation.

**Independent Test**: Can be tested by sending prompts to LLM agent and verifying tool execution (wallet balance checks, dry-run trades, real trades with confirmation). No automated data pipeline required - LLM can trade based on external market information.

**Acceptance Scenarios**:

1. **Given** user sends prompt to LLM, **When** prompt requests balance check, **Then** LLM calls get_wallet_balance tool and returns SOL/USDT amounts
2. **Given** user requests trade, **When** LLM processes request, **Then** LLM performs dry-run first and asks for confirmation before real execution
3. **Given** LLM returns trading signal, **When** decision is logged, **Then** includes rationale, confidence score, and timestamp
4. **Given** LLM attempts unsafe trade (>0.1 SOL), **When** validation occurs, **Then** LLM warns user and suggests safer amount
5. **Given** LLM API fails, **When** error occurs, **Then** system logs error and does not execute any trades

---

### User Story 1 - Automated Market Data Collection (Priority: P3)

The system continuously fetches Solana (SOL) price data and technical indicators from external sources, storing them for analysis.

**Why this priority (UPDATED - DEFERRED)**: While data collection is valuable for fully automated trading, it's not required for MVP validation. Core trading (US3-P1) and LLM control (US2-P2) can operate with manual market analysis or external data sources. Automated data collection can be added once core trading is proven on mainnet.

**Independent Test**: Can be fully tested by verifying data collection from price APIs (e.g., CoinGecko, Jupiter) and confirming data is correctly formatted and logged. Delivers value by enabling automated trading decisions.

**Acceptance Scenarios**:

1. **Given** the system is running, **When** 60 seconds elapse, **Then** current SOL/USDT price is fetched and logged
2. **Given** price data is requested, **When** external API is called, **Then** response includes price, timestamp, and is validated
3. **Given** API call fails, **When** error occurs, **Then** system logs error, waits, and retries up to 3 times
4. **Given** multiple data sources exist, **When** collecting data, **Then** data from all sources is aggregated with source attribution

---

### Edge Cases

- What happens when external price API rate limit is exceeded?
- How does system handle network disconnections during trade execution?
- What happens when LLM returns malformed or invalid trading signals?
- How does system handle Solana blockchain congestion or high gas fees?
- What happens when wallet private key is missing or invalid?
- How does system behave when both price APIs are down simultaneously?

## Requirements *(mandatory)*

### Functional Requirements

**MVP Core (US3-P1, US2-P2) - MUST requirements**:
- **FR-005**: System MUST parse LLM response into structured trading signal (BUY/SELL/HOLD + rationale)
- **FR-006**: System MUST execute SOL/USDT swaps using Solana blockchain APIs (Jupiter aggregator)
- **FR-007**: System MUST validate wallet balance before executing trades
- **FR-008**: System MUST log all trading decisions with timestamp, signal, and rationale
- **FR-009**: System MUST log all executed trades with transaction signature and final balances
- **FR-010**: System MUST handle API failures gracefully with retry logic (max 3 retries, exponential backoff)
- **FR-011**: System MUST store trading history persistently (SQLite or JSON file)
- **FR-012**: System MUST load configuration from environment variables (.env file)
- **FR-013**: System MUST support dry-run mode (simulate trades without blockchain execution)
- **FR-015**: System MUST validate LLM responses before executing trades
- **FR-016**: System MUST provide LangChain tools for wallet balance queries and trade execution
- **FR-017**: System MUST enable LLM to control trades via natural language prompts with safety guardrails

**Automated Data Collection (US1-P3) - SHOULD requirements (deferred)**:
- **FR-001**: System SHOULD fetch SOL/USDT price data from at least one external API (CoinGecko, Jupiter, or Pyth)
- **FR-002**: System SHOULD collect data at configurable intervals (default: every 60 seconds)
- **FR-003**: System SHOULD aggregate technical indicators (price, volume, trend) for LLM analysis
- **FR-004**: System SHOULD send market data to LLM automatically, OR accept user prompts with market context
- **FR-014**: System SHOULD implement rate limiting for external API calls to avoid throttling

### Key Entities

- **MarketData**: Represents collected price and indicator data (timestamp, source, SOL price in USDT, volume, additional technical indicators)
- **TradingSignal**: LLM decision output (signal type: BUY/SELL/HOLD, confidence score, rationale text, timestamp)
- **TradeExecution**: Record of executed trade (transaction signature, input amount, output amount, status, timestamp, error details if failed)
- **Configuration**: System settings (API keys, data fetch interval, LLM model, trade amount limits, dry-run mode flag)

## Success Criteria *(mandatory)*

### Measurable Outcomes (MVP: US3-P1, US2-P2)

- **SC-002**: LLM generates valid trading signals (BUY/SELL/HOLD) in <10 seconds per analysis
- **SC-003**: Trade execution completes in <30 seconds from signal to on-chain confirmation (excluding blockchain congestion)
- **SC-004**: System handles API failures gracefully - no crashes, automatic retry with backoff
- **SC-005**: All trading decisions and executions are logged with complete traceability (timestamp, signal, rationale, tx signature)
- **SC-006**: Dry-run mode can operate for 1 hour without errors, demonstrating end-to-end flow without financial risk
- **SC-007**: System can be deployed and configured by following quickstart guide in <15 minutes
- **SC-008**: LLM can successfully check wallet balance and execute test trades via natural language prompts
- **SC-009**: Manual trading CLI can execute both BUY and SELL trades on mainnet with <5% failure rate

### Future Enhancements (US1-P3 - Automated Data Collection)

- **SC-001** *(deferred)*: System successfully fetches SOL price data every 60 seconds with <5% failure rate over 24 hours
