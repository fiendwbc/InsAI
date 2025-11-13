"""Solana AI Trading Bot - Main package exports.

This package provides an AI-powered trading bot for Solana blockchain,
integrating LangChain v1.0+ agents with OpenRouter multi-LLM support.
"""

from .config import BotConfiguration, load_config
from .utils.logger import configure_logger, get_logger, logger
from .utils.retry import retry

__version__ = "0.1.0"

__all__ = [
    "BotConfiguration",
    "load_config",
    "logger",
    "get_logger",
    "configure_logger",
    "retry",
    "__version__",
]
