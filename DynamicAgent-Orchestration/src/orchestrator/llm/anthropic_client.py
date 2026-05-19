"""Anthropic Claude LLM client."""
from __future__ import annotations

import logging

from orchestrator.config import get_settings
from orchestrator.llm.base import LLMClient, LLMError

logger = logging.getLogger(__name__)


class AnthropicClient(LLMClient):
    """Concrete LLM client backed by Anthropic's Messages API."""

    def __init__(self) -> None:
        try:
            from anthropic import Anthropic
        except ImportError as e:
            raise LLMError(
                "anthropic package not installed. Run: pip install anthropic"
            ) from e

        settings = get_settings()
        if not settings.anthropic_api_key:
            raise LLMError("ANTHROPIC_API_KEY is not set.")

        self._client = Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model
        self._max_tokens = settings.max_tokens
        self._temperature = settings.temperature

    @property
    def name(self) -> str:
        return f"anthropic:{self._model}"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            logger.debug("Anthropic call: model=%s, prompt_len=%d", self._model, len(user_prompt))
            msg = self._client.messages.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            # content is a list of blocks; we want the first text block
            return msg.content[0].text
        except Exception as e:
            raise LLMError(f"Anthropic call failed: {e}") from e
