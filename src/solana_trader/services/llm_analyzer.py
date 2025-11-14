"""LLM analyzer service using LangChain agents and OpenRouter.

This module provides LLM-powered trading decision analysis using:
- OpenRouter for multi-LLM support (Claude, GPT-4, DeepSeek, Gemini)
- LangChain v1.0+ agent framework
- Trading tools (solana_trade, get_wallet_balance)
"""

import json
import time
from datetime import datetime, timezone
from typing import Any

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..config import BotConfiguration
from ..langchain_tools import get_wallet_balance, set_trade_executor, set_wallet_manager, solana_trade
from ..models.trading_signal import MarketConditions, TradingSignal
from ..utils.logger import get_logger
from ..wallet.manager import WalletManager
from .storage import StorageService
from .trade_executor import TradeExecutor

logger = get_logger("llm_analyzer")

# OpenRouter model mapping
OPENROUTER_MODELS = {
    "claude": "anthropic/claude-3.5-sonnet",
    "gpt4": "openai/gpt-4-turbo-preview",
    "deepseek": "deepseek/deepseek-chat",
    "gemini": "google/gemini-pro-1.5",
}

# System prompt for trading agent
TRADING_AGENT_SYSTEM_PROMPT = """You are a Solana trading bot with REAL money control.

CRITICAL SAFETY RULES:
1. ALWAYS use dry_run=True for the first call to test any trade
2. NEVER trade more than 0.1 SOL at once without explicit user confirmation
3. ALWAYS check wallet balance before trading using get_wallet_balance tool
4. ALWAYS provide clear rationale for every trade decision
5. If a dry-run succeeds, ask user for confirmation before executing real trade

Available tools:
- get_wallet_balance: Check current SOL and USDT balances
- solana_trade: Execute BUY or SELL trade on Jupiter DEX (use dry_run=True first!)

Trading Process:
1. Check wallet balance first using get_wallet_balance
2. Analyze the request and market conditions
3. Make a test call with dry_run=True to verify quote
4. If dry_run succeeds, provide clear reasoning
5. Only execute real trade if explicitly confirmed or instructed

Response Format:
Always provide your analysis in this JSON structure:
{{
  "signal": "BUY" | "SELL" | "HOLD",
  "confidence": 0.0 to 1.0,
  "rationale": "Clear explanation (minimum 50 words)",
  "suggested_amount_sol": 0.01,
  "market_conditions": {{
    "trend": "bullish" | "bearish" | "neutral" | "unknown",
    "volume_assessment": "high" | "medium" | "low" | "unknown",
    "volatility": "high" | "medium" | "low" | "unknown",
    "risk_level": "high" | "medium" | "low"
  }}
}}

Remember: You control REAL MONEY. Be cautious, test first, and provide clear reasoning."""


class LLMAnalyzer:
    """LLM-powered trading signal analyzer using LangChain agents."""

    def __init__(
        self,
        config: BotConfiguration,
        wallet_manager: WalletManager,
        trade_executor: TradeExecutor,
        storage: StorageService,
    ):
        """Initialize LLM analyzer with OpenRouter client and LangChain agent.

        Args:
            config: Bot configuration
            wallet_manager: Wallet manager for balance queries
            trade_executor: Trade executor for executing trades
            storage: Storage service for persisting signals
        """
        self.config = config
        self.wallet_manager = wallet_manager
        self.trade_executor = trade_executor
        self.storage = storage

        # Set global tool dependencies
        set_wallet_manager(wallet_manager)
        set_trade_executor(trade_executor)

        # Initialize OpenRouter client (OpenAI-compatible API)
        self.client = ChatOpenAI(
            model=OPENROUTER_MODELS.get(config.llm_provider, "anthropic/claude-3.5-sonnet"),
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=config.openrouter_api_key,
            temperature=0.7,
        )

        # Initialize fallback client
        self.fallback_client = ChatOpenAI(
            model=OPENROUTER_MODELS.get(config.llm_fallback_provider, "openai/gpt-4-turbo-preview"),
            openai_api_base="https://openrouter.ai/api/v1",
            openai_api_key=config.openrouter_api_key,
            temperature=0.7,
        )

        # Create LangChain agent
        self.agent = self._create_agent(self.client)
        logger.info(
            "LLM analyzer initialized",
            primary_model=config.llm_provider,
            fallback_model=config.llm_fallback_provider,
        )

    def _create_agent(self, llm: ChatOpenAI) -> AgentExecutor:
        """Create LangChain agent with trading tools.

        Args:
            llm: LangChain LLM instance

        Returns:
            Configured AgentExecutor
        """
        # Define tools
        tools = [get_wallet_balance, solana_trade]

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", TRADING_AGENT_SYSTEM_PROMPT),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}"),
        ])

        # Create agent
        agent = create_tool_calling_agent(llm, tools, prompt)

        # Create agent executor
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )

        return agent_executor

    async def get_trading_decision(
        self,
        user_prompt: str,
        dry_run: bool = True,
    ) -> TradingSignal:
        """Get trading decision from LLM agent.

        Args:
            user_prompt: User's trading instruction or market context
            dry_run: Override config dry_run mode

        Returns:
            TradingSignal with LLM decision and reasoning

        Raises:
            Exception: If LLM analysis fails
        """
        start_time = time.time()
        timestamp = datetime.now(timezone.utc)

        try:
            logger.info("Starting LLM analysis", prompt_length=len(user_prompt))

            # Invoke agent with user prompt
            result = await self.agent.ainvoke({
                "input": user_prompt
            })

            # Extract output
            output = result.get("output", "")
            logger.info("LLM agent completed", output_length=len(output))

            # Parse JSON response from LLM
            signal_data = self._parse_llm_output(output)

            # Create TradingSignal with server-side metadata
            signal = TradingSignal(
                timestamp=timestamp,
                signal=signal_data["signal"],
                confidence=signal_data["confidence"],
                rationale=signal_data["rationale"],
                suggested_amount_sol=signal_data.get("suggested_amount_sol"),
                market_conditions=MarketConditions(**signal_data["market_conditions"]),
                llm_model=self.config.llm_provider,
                analysis_duration_sec=time.time() - start_time,
            )

            # Save to database
            await self.storage.save_trading_signal(signal.model_dump())

            logger.info(
                "Trading signal generated",
                signal=signal.signal,
                confidence=signal.confidence,
            )

            return signal

        except Exception as e:
            logger.error("LLM analysis failed", error=str(e))
            # Try fallback provider
            try:
                logger.info("Attempting fallback LLM provider")
                fallback_agent = self._create_agent(self.fallback_client)
                result = await fallback_agent.ainvoke({"input": user_prompt})
                output = result.get("output", "")
                signal_data = self._parse_llm_output(output)

                signal = TradingSignal(
                    timestamp=timestamp,
                    signal=signal_data["signal"],
                    confidence=signal_data["confidence"],
                    rationale=signal_data["rationale"],
                    suggested_amount_sol=signal_data.get("suggested_amount_sol"),
                    market_conditions=MarketConditions(**signal_data["market_conditions"]),
                    llm_model=f"{self.config.llm_fallback_provider} (fallback)",
                    analysis_duration_sec=time.time() - start_time,
                )

                await self.storage.save_trading_signal(signal.model_dump())
                logger.info("Fallback LLM succeeded")
                return signal

            except Exception as fallback_error:
                logger.error("Fallback LLM also failed", error=str(fallback_error))
                raise RuntimeError(f"LLM analysis failed: {e}, Fallback also failed: {fallback_error}")

    def _parse_llm_output(self, output: str) -> dict[str, Any]:
        """Parse LLM output to extract trading signal JSON.

        Args:
            output: LLM output text (may contain JSON)

        Returns:
            Dictionary with signal, confidence, rationale, market_conditions

        Raises:
            ValueError: If output cannot be parsed
        """
        # Try to find JSON in output
        try:
            # If output is already valid JSON
            data = json.loads(output)
            return data
        except json.JSONDecodeError:
            # Try to extract JSON block from markdown
            import re
            json_match = re.search(r'```json\n(.*?)\n```', output, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(1))
                    return data
                except json.JSONDecodeError:
                    pass

            # Try to extract JSON without markdown
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                try:
                    data = json.loads(json_match.group(0))
                    return data
                except json.JSONDecodeError:
                    pass

        # If all parsing fails, return default HOLD signal
        logger.warning("Could not parse LLM output, returning HOLD signal")
        return {
            "signal": "HOLD",
            "confidence": 0.5,
            "rationale": f"LLM output could not be parsed into valid JSON format. Raw output: {output[:200]}...",
            "market_conditions": {
                "trend": "unknown",
                "volume_assessment": "unknown",
                "volatility": "unknown",
                "risk_level": "medium",
            }
        }

    def validate_signal_json(self, signal_dict: dict[str, Any]) -> bool:
        """Validate signal dictionary against JSON schema.

        Args:
            signal_dict: Signal data dictionary

        Returns:
            True if valid, False otherwise
        """
        required_fields = ["signal", "confidence", "rationale", "market_conditions"]
        for field in required_fields:
            if field not in signal_dict:
                logger.warning(f"Missing required field: {field}")
                return False

        if signal_dict["signal"] not in ["BUY", "SELL", "HOLD"]:
            logger.warning(f"Invalid signal: {signal_dict['signal']}")
            return False

        if not 0 <= signal_dict["confidence"] <= 1:
            logger.warning(f"Invalid confidence: {signal_dict['confidence']}")
            return False

        return True
