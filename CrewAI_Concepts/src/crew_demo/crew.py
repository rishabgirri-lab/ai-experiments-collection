"""
Crew.
=====
A Crew binds agents + tasks together and runs them under a Process.

Modes supported by this project:
  - "sequential"   -> Process.sequential, tasks pinned to agents.
  - "hierarchical" -> Process.hierarchical with a manager agent that
                      delegates and validates worker output.
  - "async"        -> Process.sequential, BUT two research tasks run in
                      parallel via async_execution=True before fan-in to
                      the writer.  (CrewAI has no Process.parallel; this
                      is the correct way to parallelize work.)

Other crew-level concepts shown:
  - verbose       -> stream orchestration logs
  - memory        -> let agents recall earlier context (off by default;
                     toggle via ENABLE_MEMORY env var)
  - max_rpm       -> rate-limit LLM requests per minute (cost/safety)
"""

import os
from typing import Literal

from crewai import Crew, Process

from src.crew_demo.agents import build_agents, build_manager_agent
from src.crew_demo.tasks import (
    build_async_tasks,
    build_hierarchical_tasks,
    build_sequential_tasks,
)
from src.crew_demo.logger import get_logger

log = get_logger("crew")

Mode = Literal["sequential", "hierarchical", "async"]


class ResearchWritingCrew:
    """Assembles a research -> write -> edit crew in one of three modes."""

    def __init__(self, mode: Mode = "sequential") -> None:
        if mode not in ("sequential", "hierarchical", "async"):
            raise ValueError(
                f"Unknown mode '{mode}'. "
                "Choose from: sequential, hierarchical, async."
            )
        self.mode = mode

    def build(self) -> Crew:
        log.info("Assembling crew in mode = %s", self.mode.upper())
        agents = build_agents()
        enable_memory = os.getenv("ENABLE_MEMORY", "false").lower() == "true"
        log.info("Memory enabled: %s", enable_memory)

        if self.mode == "sequential":
            return self._build_sequential(agents, enable_memory)
        if self.mode == "async":
            return self._build_async(agents, enable_memory)
        return self._build_hierarchical(agents, enable_memory)

    # ---- mode builders ------------------------------------------------------

    def _build_sequential(self, agents, enable_memory: bool) -> Crew:
        # Researcher + writer + editor are enough for sequential; the
        # audience_analyst is unused here but harmless to include.
        tasks = build_sequential_tasks(agents)
        crew = Crew(
            agents=[agents["researcher"], agents["writer"], agents["editor"]],
            tasks=tasks,
            process=Process.sequential,
            verbose=True,
            memory=enable_memory,
            max_rpm=30,
        )
        log.info("SEQUENTIAL crew: 3 agents, %d tasks", len(tasks))
        return crew

    def _build_async(self, agents, enable_memory: bool) -> Crew:
        tasks = build_async_tasks(agents)
        crew = Crew(
            agents=[
                agents["researcher"],
                agents["audience_analyst"],
                agents["writer"],
                agents["editor"],
            ],
            tasks=tasks,
            process=Process.sequential,  # parallelism comes from the tasks
            verbose=True,
            memory=enable_memory,
            max_rpm=30,
        )
        log.info("ASYNC crew: 4 agents, %d tasks (2 parallel research tasks)", len(tasks))
        return crew

    def _build_hierarchical(self, agents, enable_memory: bool) -> Crew:
        tasks = build_hierarchical_tasks()
        manager = build_manager_agent()
        # IMPORTANT: the manager is passed via manager_agent and MUST NOT
        # appear in the `agents` list (CrewAI validates this).
        crew = Crew(
            agents=[agents["researcher"], agents["writer"], agents["editor"]],
            tasks=tasks,
            process=Process.hierarchical,
            manager_agent=manager,
            verbose=True,
            memory=enable_memory,
            max_rpm=30,
        )
        log.info(
            "HIERARCHICAL crew: 1 manager + 3 worker agents, %d tasks (manager delegates)",
            len(tasks),
        )
        return crew
