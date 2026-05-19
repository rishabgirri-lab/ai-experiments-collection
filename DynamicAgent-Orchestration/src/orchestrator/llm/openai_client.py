"""OpenAI LLM client.

Also works with any OpenAI-API-compatible service (Groq, OpenRouter, Together,
Ollama) when OPENAI_BASE_URL is set.
"""
from __future__ import annotations

import logging

from orchestrator.config import get_settings
from orchestrator.llm.base import LLMClient, LLMError

logger = logging.getLogger(__name__)


class OpenAIClient(LLMClient):
    """Concrete LLM client backed by OpenAI's Chat Completions API."""

    def __init__(self) -> None:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise LLMError(
                "openai package not installed. Run: pip install openai"
            ) from e

        settings = get_settings()
        if not settings.openai_api_key:
            raise LLMError("OPENAI_API_KEY is not set.")

        # base_url is optional — set it for Groq/OpenRouter/Ollama compatibility
        client_kwargs: dict[str, object] = {"api_key": settings.openai_api_key}
        if settings.openai_base_url:
            client_kwargs["base_url"] = settings.openai_base_url

        self._client = OpenAI(**client_kwargs)
        self._model = settings.openai_model
        self._max_tokens = settings.max_tokens
        self._temperature = settings.temperature

    @property
    def name(self) -> str:
        return f"openai:{self._model}"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        try:
            logger.debug("OpenAI call: model=%s, prompt_len=%d", self._model, len(user_prompt))
            resp = self._client.chat.completions.create(
                model=self._model,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise LLMError(f"OpenAI call failed: {e}") from e
