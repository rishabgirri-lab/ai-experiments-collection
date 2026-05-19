"""How to add a custom specialist agent.

This example registers a new "Critic" agent at runtime without modifying
the orchestrator package.

Run from project root:
    python examples/custom_agent.py
"""
from __future__ import annotations

from orchestrator.agents import (
    Agent,
    PlannerAgent,
    SynthesizerAgent,
    build_specialists,
)
from orchestrator.core import Orchestrator
from orchestrator.llm import build_llm_client
from orchestrator.logging_setup import configure_logging


class CriticAgent(Agent):
    NAME = "critic"
    SYSTEM_PROMPT = (
        "You are the Critic agent. Find weaknesses, missing considerations, "
        "or counterarguments in the topic at hand. Be sharp but fair. "
        "Output 3 bullet points."
    )


def main() -> None:
    configure_logging()

    llm = build_llm_client()

    # Build the default specialists, then add our new one.
    specialists = build_specialists(llm)
    specialists[CriticAgent.NAME] = CriticAgent(llm)

    # Tell the Planner about all available agents (including custom ones).
    available = list(specialists.keys())
    planner = PlannerAgent(llm, available_agents=available)
    synthesizer = SynthesizerAgent(llm)

    orchestrator = Orchestrator(planner, specialists, synthesizer)

    task = "Should companies adopt a 4-day work week?"
    result = orchestrator.run(task)

    print(f"\nPlan picked: {result.plan.agents}")
    print(f"\nFinal answer:\n{result.final_answer}\n")


if __name__ == "__main__":
    main()
