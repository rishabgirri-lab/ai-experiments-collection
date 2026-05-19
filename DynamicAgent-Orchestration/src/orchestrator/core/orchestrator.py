"""Core orchestrator.

Coordinates the full pipeline:
    Planner -> parallel Specialists -> Synthesizer

This module is intentionally thin: it composes pre-built agents that were
constructed elsewhere (factories + registry). All side effects (LLM calls)
happen inside the agents.
"""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from orchestrator.agents import (
    Agent,
    AgentResult,
    Plan,
    PlannerAgent,
    SynthesizerAgent,
)
from orchestrator.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """Final structured result returned by the orchestrator."""

    task: str
    plan: Plan
    specialist_results: list[AgentResult] = field(default_factory=list)
    final_answer: str = ""
    total_latency_seconds: float = 0.0


class Orchestrator:
    """The orchestration pipeline.

    Takes already-constructed agents via dependency injection so it can be
    tested with mocks and is decoupled from the LLM factory.
    """

    def __init__(
        self,
        planner: PlannerAgent,
        specialists: dict[str, Agent],
        synthesizer: SynthesizerAgent,
    ) -> None:
        self._planner = planner
        self._specialists = specialists
        self._synthesizer = synthesizer
        self._max_workers = get_settings().max_parallel_agents

    def run(self, task: str) -> OrchestrationResult:
        """Execute the full Plan -> Specialists -> Synthesize pipeline."""
        import time
        start = time.time()

        # Step 1: Planner picks which specialists to invoke.
        logger.info("Planning agents for task: %s", task[:80])
        plan = self._planner.plan(task)
        logger.info("Planner chose: %s | reason: %s", plan.agents, plan.reasoning)

        # Step 2: Run specialists in parallel.
        specialist_results = self._run_specialists_parallel(task, plan.agents)

        # Step 3: Synthesize.
        logger.info("Synthesizing %d specialist outputs", len(specialist_results))
        final_answer = self._synthesizer.synthesize(task, specialist_results)

        total = round(time.time() - start, 2)
        logger.info("Pipeline complete in %.2fs", total)

        return OrchestrationResult(
            task=task,
            plan=plan,
            specialist_results=specialist_results,
            final_answer=final_answer,
            total_latency_seconds=total,
        )

    def _run_specialists_parallel(self, task: str, agent_names: list[str]) -> list[AgentResult]:
        """Run the chosen specialist agents concurrently."""
        # Filter to ones we actually have registered (Planner should already do this,
        # but defense in depth).
        valid_names = [n for n in agent_names if n in self._specialists]
        if not valid_names:
            logger.warning("No valid specialists selected; returning empty result list.")
            return []

        results: list[AgentResult] = []
        max_workers = min(len(valid_names), self._max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            future_to_name = {
                pool.submit(self._specialists[name].run, task): name
                for name in valid_names
            }
            for future in as_completed(future_to_name):
                name = future_to_name[future]
                try:
                    results.append(future.result())
                except Exception as e:
                    # Should not happen — Agent.run already catches — but belt-and-suspenders.
                    logger.exception("Unexpected error from agent %s", name)
                    results.append(AgentResult(
                        agent_name=name,
                        output="",
                        latency_seconds=0.0,
                        success=False,
                        error=str(e),
                    ))
        return results
