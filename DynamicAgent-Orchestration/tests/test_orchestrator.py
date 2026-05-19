"""Integration-style tests for the Orchestrator pipeline."""
from __future__ import annotations

import json

from orchestrator.agents import (
    PlannerAgent,
    SynthesizerAgent,
    available_specialist_names,
    build_specialists,
)
from orchestrator.core import Orchestrator


def test_orchestrator_runs_full_pipeline(fake_llm_factory):
    plan_json = json.dumps({"agents": ["researcher", "writer"], "reasoning": "facts + prose"})
    llm = fake_llm_factory({
        "planner": plan_json,
        "researcher": "Researcher output",
        "writer": "Writer output",
        "synthesizer": "Final synthesized answer",
    })

    specialists = build_specialists(llm)
    planner = PlannerAgent(llm, available_agents=available_specialist_names())
    synthesizer = SynthesizerAgent(llm)
    orch = Orchestrator(planner, specialists, synthesizer)

    result = orch.run("Test task")

    assert result.task == "Test task"
    assert result.plan.agents == ["researcher", "writer"]
    assert len(result.specialist_results) == 2
    assert all(r.success for r in result.specialist_results)
    assert result.final_answer == "Final synthesized answer"


def test_orchestrator_handles_partial_specialist_failure(fake_llm_factory):
    plan_json = json.dumps({"agents": ["researcher", "writer"], "reasoning": "x"})

    class PartialFailLLM:
        @property
        def name(self): return "partial"
        def __init__(self):
            self.call_count = 0
        def complete(self, sys_p, user_p):
            self.call_count += 1
            sp = sys_p.lower()
            if "planner" in sp:
                return plan_json
            if "researcher" in sp:
                raise RuntimeError("researcher boom")
            if "writer" in sp:
                return "writer ok"
            if "synthesizer" in sp:
                return "synthesized from writer only"
            return "?"

    llm = PartialFailLLM()
    specialists = build_specialists(llm)
    planner = PlannerAgent(llm, available_agents=available_specialist_names())
    synth = SynthesizerAgent(llm)
    orch = Orchestrator(planner, specialists, synth)

    result = orch.run("task")
    failures = [r for r in result.specialist_results if not r.success]
    successes = [r for r in result.specialist_results if r.success]
    assert len(failures) == 1
    assert len(successes) == 1
    assert result.final_answer == "synthesized from writer only"
