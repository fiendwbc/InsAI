# Solana AI Trading Bot

> 🤖 AI-powered Solana trading bot using LangChain v1.0+, OpenRouter, and CoinKarma sentiment analysis

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![LangChain 1.0+](https://img.shields.io/badge/langchain-1.0+-green.svg)](https://python.langchain.com/)
[![uv](https://img.shields.io/badge/uv-latest-orange.svg)](https://docs.astral.sh/uv/)

## Features

- 🧠 **Multi-LLM Support**: Claude, GPT-4, DeepSeek, Gemini via OpenRouter
- 🔧 **LangChain v1.0+**: Modern agent framework with `@tool` decorator pattern
- 📊 **Sentiment Analysis**: CoinKarma Pulse Index and Liquidity indicators
- 💰 **Jupiter Integration**: Direct SOL/USDT swaps on Solana
- 🛡️ **Safety First**: Dry-run mode, position limits, circuit breakers
- ⚡ **Fast Setup**: Uses `uv` for 10-100x faster dependency management

## Quick Start

### Prerequisites

- **Python 3.11+**
- **uv** package manager: `pip install uv` or [installer](https://docs.astral.sh/uv/)
- **OpenRouter API key**: [Sign up](https://openrouter.ai)
- **CoinKarma credentials**: Token + Device ID
- **Solana wallet**: Private key (test wallet recommended)

### Installation

```bash
# Clone repository
git clone <repo-url>
cd InsAI

# Install dependencies with uv (automatic venv creation)
uv sync

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
# Windows: notepad .env
# Linux/Mac: nano .env
```

### Configuration

Update `.env` with your credentials:

```env
# Required: OpenRouter API key
OPENROUTER_API_KEY=sk-or-v1-your-key-here
LLM_PROVIDER=claude

# Required: CoinKarma credentials
COINKARMA_TOKEN=Bearer eyJ...
COINKARMA_DEVICE_ID=828601...

# Required: Solana wallet private key (base58)
WALLET_PRIVATE_KEY=your-base58-key-here

# Safety: Start in dry-run mode
DRY_RUN_MODE=true
```

### Run

```bash
# Test configuration
uv run python -m solana_trader.config

# Start bot (dry-run mode by default)
uv run python -m solana_trader.main
```

**Output:**
```
2025-11-12 10:30:00 | INFO | Bot starting in DRY-RUN mode
2025-11-12 10:30:01 | INFO | LLM Provider: claude (fallback: gpt4)
2025-11-12 10:30:02 | INFO | Fetching SOL price...
2025-11-12 10:30:03 | INFO | SOL/USDT: $42.15 (↑ 3.2%)
2025-11-12 10:30:04 | INFO | CoinKarma Pulse Index: 68.5 (bullish)
2025-11-12 10:30:07 | INFO | LLM Signal: HOLD (confidence: 0.62)
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Main Loop                          │
│  (Every 60s: Collect Data → LLM Analyze → Trade)      │
└──────────────────┬──────────────────────────────────────┘
                   │
       ┌───────────┴────────────┐
       │   LangChain Agent      │
       │   (create_agent)       │
       └───────────┬────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼───┐    ┌────▼────┐    ┌───▼────┐
│@tool  │    │@tool    │    │@tool   │
│fetch_ │    │solana_  │    │fetch_  │
│price  │    │trade    │    │karma   │
└───┬───┘    └────┬────┘    └───┬────┘
    │             │              │
┌───▼─────────────▼──────────────▼────┐
│   External APIs                     │
│  (Jupiter, CoinGecko, CoinKarma)   │
└─────────────────────────────────────┘
```

## Project Structure

```
InsAI/
├── src/
│   └── solana_trader/
│       ├── main.py              # Entry point
│       ├── config.py            # Configuration
│       ├── models/              # Pydantic data models
│       ├── services/            # Business logic
│       │   ├── data_collector.py
│       │   ├── llm_analyzer.py
│       │   ├── trade_executor.py
│       │   └── storage.py
│       ├── langchain_tools/     # LangChain @tool functions
│       │   ├── fetch_price.py
│       │   ├── execute_trade.py
│       │   ├── get_market_data.py
│       │   └── fetch_karma_indicators.py
│       ├── coinkarma/           # CoinKarma API client
│       ├── wallet/              # Wallet management
│       └── utils/               # Logger, retry logic
├── tests/                       # Test suite
├── specs/                       # Design documents
├── pyproject.toml               # uv dependencies (PEP 621)
├── uv.lock                      # Lockfile
├── .env.example                 # Environment template
└── README.md                    # This file
```

## Development

### Using uv

```bash
# Install dependencies (dev + production)
uv sync

# Add new dependency
uv add package-name

# Add dev dependency
uv add --dev pytest-something

# Update dependencies
uv lock --upgrade

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Format code
uv run black .
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=solana_trader --cov-report=html

# Run specific test file
uv run pytest tests/unit/test_models.py

# Run in watch mode (requires pytest-watch)
uv run ptw
```

### Code Quality

```bash
# Lint with ruff
uv run ruff check .

# Format with black
uv run black .

# Type check with mypy
uv run mypy src/
```

## Documentation

- **[Quickstart Guide](specs/master/quickstart.md)**: 15-minute deployment
- **[Implementation Plan](specs/master/plan.md)**: Architecture and design
- **[Data Model](specs/master/data-model.md)**: Pydantic entities and SQLite schema
- **[LangChain Integration](specs/master/LANGCHAIN_INTEGRATION.md)**: v1.0+ patterns
- **[Research](specs/master/research.md)**: Technology decisions

## Safety Features

- ✅ **Dry-run mode**: Default mode, no real trades
- ✅ **Position limits**: MAX_TRADE_SIZE_SOL, MAX_TRADES_PER_DAY
- ✅ **Circuit breaker**: Auto-pause on >20% price swings
- ✅ **Validation**: Pydantic models validate all data
- ✅ **Logging**: Structured JSON logs for audit trail

## Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `claude` | Primary LLM (claude/gpt4/deepseek/gemini) |
| `DRY_RUN_MODE` | `true` | Simulate trades without execution |
| `MAX_TRADE_SIZE_SOL` | `0.1` | Maximum SOL per trade |
| `MAX_TRADES_PER_DAY` | `20` | Daily trade limit |
| `SLIPPAGE_BPS` | `50` | Slippage tolerance (0.5%) |
| `DATA_FETCH_INTERVAL_SEC` | `60` | Price fetch interval |

See [.env.example](.env.example) for all options.

## Troubleshooting

### Bot won't start

```bash
# Check configuration
uv run python -m solana_trader.config

# Verify API keys in .env
cat .env | grep API_KEY

# Check logs
tail -f logs/trading_bot.log
```

### No trading signals

- Verify OpenRouter API key has credits: https://openrouter.ai/credits
- Check LLM_PROVIDER setting matches available models
- Increase LOG_LEVEL=DEBUG to see LLM prompts

### Dependencies issues

```bash
# Sync dependencies
uv sync

# Clear cache and reinstall
rm -rf .venv uv.lock
uv sync
```

## Why uv?

**uv** is 10-100x faster than pip/Poetry:

- 🚀 **Fast**: Written in Rust, parallel downloads
- 📦 **Standard**: Uses PEP 621 (pyproject.toml)
- 🔒 **Reliable**: Reproducible builds with uv.lock
- 🎯 **Simple**: `uv sync` for install, `uv add` for packages

[Learn more about uv](https://docs.astral.sh/uv/)

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## License

MIT License - see [LICENSE](LICENSE) file

## Disclaimer

⚠️ **This is educational software**. Use at your own risk. Always start in DRY_RUN_MODE. Never trade more than you can afford to lose. Cryptocurrency trading carries significant risk.

---

**Built with** [LangChain v1.0+](https://python.langchain.com/) | [uv](https://docs.astral.sh/uv/) | [OpenRouter](https://openrouter.ai)
