"""LLM client factory.

The factory is the only place that knows how to construct concrete clients.
Everything else takes an LLMClient instance via dependency injection.
"""
from __future__ import annotations

import logging

from orchestrator.config import get_settings
from orchestrator.llm.base import LLMClient, LLMError

logger = logging.getLogger(__name__)


def build_llm_client() -> LLMClient:
    """Construct an LLM client based on the configured provider."""
    settings = get_settings()
    settings.validate()

    logger.info("Initializing LLM client for provider=%s", settings.provider)

    if settings.provider == "anthropic":
        from orchestrator.llm.anthropic_client import AnthropicClient
        return AnthropicClient()

    if settings.provider == "openai":
        from orchestrator.llm.openai_client import OpenAIClient
        return OpenAIClient()

    if settings.provider == "mock":
        from orchestrator.llm.mock_client import MockClient
        return MockClient()

    raise LLMError(f"Unknown provider: {settings.provider}")
