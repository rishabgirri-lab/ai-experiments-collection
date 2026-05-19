"""Mock LLM client that returns deterministic responses.

Used when LLM_PROVIDER=mock so the system can be exercised end-to-end
without any API key. Also useful in unit tests.
"""
from __future__ import annotations

import json
import logging
import time

from orchestrator.llm.base import LLMClient

logger = logging.getLogger(__name__)


class MockClient(LLMClient):
    """Returns canned responses based on the system prompt's detected role."""

    # Small artificial delay so concurrency behavior is observable in demos.
    SIMULATED_LATENCY_SECONDS = 0.3

    @property
    def name(self) -> str:
        return "mock"

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        time.sleep(self.SIMULATED_LATENCY_SECONDS)

        sp = system_prompt.lower()

        # Planner expects a strict JSON plan.
        if "planner" in sp:
            return json.dumps({
                "agents": ["researcher", "analyst", "writer"],
                "reasoning": "Mock plan: facts + analysis + write-up.",
            })

        # Identify which specialist role is calling so the mock output is labeled.
        role = "unknown"
        for r in ("researcher", "coder", "analyst", "writer", "synthesizer"):
            if r in sp:
                role = r
                break

        snippet = user_prompt[:120].replace("\n", " ")
        return (
            f"[MOCK {role.upper()} OUTPUT]\n"
            f"Simulated response for prompt: '{snippet}...'\n"
            f"Set LLM_PROVIDER=anthropic or openai with a real key for actual output."
        )
