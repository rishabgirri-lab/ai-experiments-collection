"""Planner agent.

Reads the user task and decides which specialist agents to invoke.
This is what makes the orchestration "dynamic" — the agent roster
changes per task.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from orchestrator.agents.base import Agent
from orchestrator.llm import LLMClient

logger = logging.getLogger(__name__)


PLANNER_SYSTEM_PROMPT = """You are the Planner agent in a multi-agent system.
Given a user task, decide which specialist agents should be invoked.

Available agents:
  - researcher : gathers facts and background
  - coder      : writes or reviews code
  - analyst    : reasons about trade-offs and implications
  - writer     : produces polished prose for the end user

Return ONLY valid JSON with this exact schema:
{"agents": ["agent_name", ...], "reasoning": "brief explanation"}

Pick 1-4 agents. Always include "writer" if the user wants a written answer.
Do NOT wrap the JSON in markdown code fences."""


@dataclass
class Plan:
    """The Planner's decision about which agents to run."""

    agents: list[str]
    reasoning: str


class PlannerAgent(Agent):
    NAME = "planner"
    SYSTEM_PROMPT = PLANNER_SYSTEM_PROMPT

    def __init__(self, llm: LLMClient, available_agents: list[str]) -> None:
        super().__init__(llm)
        self._available_agents = set(available_agents)

    def plan(self, task: str) -> Plan:
        """Produce a Plan for the given task."""
        result = self.run(task)
        if not result.success:
            logger.warning("Planner failed (%s); falling back to default plan.", result.error)
            return self._default_plan("Planner LLM call failed.")
        return self._parse_plan(result.output)

    def _parse_plan(self, raw: str) -> Plan:
        """Parse the planner's JSON output defensively."""
        cleaned = raw.strip()

        # Strip markdown fences if the model wrapped its output.
        if cleaned.startswith("```"):
            parts = cleaned.split("```")
            if len(parts) >= 2:
                cleaned = parts[1]
                if cleaned.lower().startswith("json"):
                    cleaned = cleaned[4:]
                cleaned = cleaned.strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.warning("Planner output not valid JSON (%s); using default plan.", e)
            return self._default_plan("Planner output unparseable.")

        agents = [a for a in parsed.get("agents", []) if a in self._available_agents]
        if not agents:
            logger.warning("Planner returned no valid agents; using default plan.")
            return self._default_plan("Planner returned no valid agents.")

        return Plan(
            agents=agents,
            reasoning=parsed.get("reasoning", "(no reasoning provided)"),
        )

    def _default_plan(self, reason: str) -> Plan:
        # Pick a sensible default that's likely available.
        defaults = [a for a in ("researcher", "writer") if a in self._available_agents]
        if not defaults:
            defaults = list(self._available_agents)[:2]
        return Plan(agents=defaults, reasoning=f"Default plan ({reason})")
