"""Agent registry.

Maps agent names to Agent classes. To add a new specialist:
  1. Implement an Agent subclass in specialists.py
  2. Register it here
  3. (Optional) Update the Planner's system prompt to mention it

This indirection lets the Planner pick agents by name without the
orchestrator hard-coding which classes exist.
"""
from __future__ import annotations

from orchestrator.agents.base import Agent
from orchestrator.agents.specialists import (
    AnalystAgent,
    CoderAgent,
    ResearcherAgent,
    WriterAgent,
)
from orchestrator.llm import LLMClient

# Mapping of agent name -> Agent subclass.
_SPECIALIST_CLASSES: dict[str, type[Agent]] = {
    ResearcherAgent.NAME: ResearcherAgent,
    CoderAgent.NAME: CoderAgent,
    AnalystAgent.NAME: AnalystAgent,
    WriterAgent.NAME: WriterAgent,
}


def available_specialist_names() -> list[str]:
    """Return the list of registered specialist agent names."""
    return list(_SPECIALIST_CLASSES.keys())


def build_specialists(llm: LLMClient) -> dict[str, Agent]:
    """Instantiate every registered specialist with the given LLM client."""
    return {name: cls(llm) for name, cls in _SPECIALIST_CLASSES.items()}
