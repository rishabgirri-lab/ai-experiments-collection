"""Agents package — Planner, Specialists, and Synthesizer."""
from orchestrator.agents.base import Agent, AgentResult
from orchestrator.agents.planner import Plan, PlannerAgent
from orchestrator.agents.registry import available_specialist_names, build_specialists
from orchestrator.agents.specialists import (
    AnalystAgent,
    CoderAgent,
    ResearcherAgent,
    WriterAgent,
)
from orchestrator.agents.synthesizer import SynthesizerAgent

__all__ = [
    "Agent",
    "AgentResult",
    "Plan",
    "PlannerAgent",
    "SynthesizerAgent",
    "ResearcherAgent",
    "CoderAgent",
    "AnalystAgent",
    "WriterAgent",
    "available_specialist_names",
    "build_specialists",
]
