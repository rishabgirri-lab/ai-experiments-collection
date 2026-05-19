"""Base Agent class shared by all specialists.

An Agent is a thin wrapper around an LLM call with a specific system prompt
(its "role") and a structured result. Subclasses just supply the prompt.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import ClassVar

from orchestrator.llm import LLMClient

logger = logging.getLogger(__name__)


@dataclass
class AgentResult:
    """Structured output from an agent run."""

    agent_name: str
    output: str
    latency_seconds: float
    success: bool
    error: str | None = None


class Agent:
    """Base class for specialist agents.

    Subclasses set NAME and SYSTEM_PROMPT as class variables.
    """

    NAME: ClassVar[str] = "base"
    SYSTEM_PROMPT: ClassVar[str] = ""

    def __init__(self, llm: LLMClient) -> None:
        if not self.NAME or not self.SYSTEM_PROMPT:
            raise ValueError(
                f"{type(self).__name__} must define NAME and SYSTEM_PROMPT class variables."
            )
        self._llm = llm

    def run(self, task: str, context: str = "") -> AgentResult:
        """Execute the agent against a task with optional shared context."""
        user_prompt = self._build_prompt(task, context)
        start = time.time()
        try:
            logger.debug("Agent %s starting", self.NAME)
            output = self._llm.complete(self.SYSTEM_PROMPT, user_prompt)
            elapsed = time.time() - start
            logger.info("Agent %s finished in %.2fs", self.NAME, elapsed)
            return AgentResult(
                agent_name=self.NAME,
                output=output,
                latency_seconds=round(elapsed, 2),
                success=True,
            )
        except Exception as e:
            elapsed = time.time() - start
            logger.exception("Agent %s failed", self.NAME)
            return AgentResult(
                agent_name=self.NAME,
                output="",
                latency_seconds=round(elapsed, 2),
                success=False,
                error=str(e),
            )

    @staticmethod
    def _build_prompt(task: str, context: str) -> str:
        if context:
            return f"Task: {task}\n\nContext from other agents:\n{context}"
        return f"Task: {task}"
