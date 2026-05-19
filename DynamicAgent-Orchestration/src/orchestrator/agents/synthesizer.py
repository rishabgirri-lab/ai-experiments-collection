"""Synthesizer agent.

Takes the outputs from multiple specialists and merges them into one
coherent final answer.
"""
from __future__ import annotations

import logging

from orchestrator.agents.base import Agent, AgentResult

logger = logging.getLogger(__name__)


SYNTHESIZER_SYSTEM_PROMPT = """You are the Synthesizer agent. You receive outputs
from multiple specialist agents. Combine them into ONE coherent, well-organized
answer for the user. Remove redundancy. Resolve conflicts when possible.
Cite which agent contributed which insight only when it adds clarity."""


class SynthesizerAgent(Agent):
    NAME = "synthesizer"
    SYSTEM_PROMPT = SYNTHESIZER_SYSTEM_PROMPT

    def synthesize(self, task: str, specialist_results: list[AgentResult]) -> str:
        """Produce a final, merged answer from the specialists' outputs."""
        successful = [r for r in specialist_results if r.success]
        if not successful:
            logger.error("No successful specialist results to synthesize.")
            return "No specialist agents produced usable output; synthesis aborted."

        context_blocks = [
            f"--- {r.agent_name.upper()} ---\n{r.output}" for r in successful
        ]
        context = "\n\n".join(context_blocks)

        prompt = (
            f"Original task: {task}\n\n"
            f"Agent outputs:\n{context}\n\n"
            "Produce the final answer for the user."
        )
        result = self._llm.complete(self.SYSTEM_PROMPT, prompt)
        return result
