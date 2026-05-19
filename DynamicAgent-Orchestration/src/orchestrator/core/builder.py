"""Convenience builder that wires up the full orchestrator with defaults.

Call build_default_orchestrator() to get a ready-to-use Orchestrator
configured from environment variables.
"""
from __future__ import annotations

from orchestrator.agents import (
    PlannerAgent,
    SynthesizerAgent,
    available_specialist_names,
    build_specialists,
)
from orchestrator.core.orchestrator import Orchestrator
from orchestrator.llm import build_llm_client


def build_default_orchestrator() -> Orchestrator:
    """Construct an Orchestrator using settings from environment variables."""
    llm = build_llm_client()
    specialists = build_specialists(llm)
    planner = PlannerAgent(llm, available_agents=available_specialist_names())
    synthesizer = SynthesizerAgent(llm)
    return Orchestrator(planner=planner, specialists=specialists, synthesizer=synthesizer)
