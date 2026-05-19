"""Shared pytest fixtures."""
from __future__ import annotations

import pytest

from orchestrator.llm.base import LLMClient


class FakeLLM(LLMClient):
    """LLM stub that returns pre-programmed responses by prompt-substring match."""

    def __init__(self, responses: dict[str, str], default: str = "default response") -> None:
        self._responses = responses
        self._default = default
        self.calls: list[tuple[str, str]] = []

    @property
    def name(self) -> str:
        return "fake"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        self.calls.append((system_prompt, user_prompt))
        for substring, response in self._responses.items():
            if substring.lower() in system_prompt.lower():
                return response
        return self._default


@pytest.fixture
def fake_llm_factory():
    """Factory fixture to build FakeLLM with custom response maps."""
    def _build(responses: dict[str, str], default: str = "default response") -> FakeLLM:
        return FakeLLM(responses, default)
    return _build
