"""Tests for Agent base, specialists, planner, and synthesizer."""
from __future__ import annotations

import json

import pytest

from orchestrator.agents import (
    AgentResult,
    PlannerAgent,
    ResearcherAgent,
    SynthesizerAgent,
    WriterAgent,
    available_specialist_names,
    build_specialists,
)
from orchestrator.agents.base import Agent


def test_agent_subclass_requires_name_and_prompt(fake_llm_factory):
    class BadAgent(Agent):
        pass

    with pytest.raises(ValueError):
        BadAgent(fake_llm_factory({}))


def test_specialist_run_returns_success(fake_llm_factory):
    llm = fake_llm_factory({"researcher": "Fact 1, Fact 2"})
    agent = ResearcherAgent(llm)
    result = agent.run("Tell me about solar panels")
    assert result.success is True
    assert result.agent_name == "researcher"
    assert "Fact" in result.output
    assert result.latency_seconds >= 0


def test_specialist_run_handles_exceptions(fake_llm_factory):
    class BrokenLLM:
        @property
        def name(self): return "broken"
        def complete(self, *a, **kw): raise RuntimeError("simulated boom")

    agent = WriterAgent(BrokenLLM())
    result = agent.run("anything")
    assert result.success is False
    assert "simulated boom" in (result.error or "")


def test_planner_parses_valid_json(fake_llm_factory):
    plan_json = json.dumps({"agents": ["researcher", "writer"], "reasoning": "test"})
    llm = fake_llm_factory({"planner": plan_json})
    planner = PlannerAgent(llm, available_agents=available_specialist_names())
    plan = planner.plan("some task")
    assert plan.agents == ["researcher", "writer"]
    assert plan.reasoning == "test"


def test_planner_strips_markdown_fences(fake_llm_factory):
    raw = '```json\n{"agents": ["analyst"], "reasoning": "fenced"}\n```'
    llm = fake_llm_factory({"planner": raw})
    planner = PlannerAgent(llm, available_agents=available_specialist_names())
    plan = planner.plan("task")
    assert plan.agents == ["analyst"]


def test_planner_falls_back_on_bad_json(fake_llm_factory):
    llm = fake_llm_factory({"planner": "not json at all"})
    planner = PlannerAgent(llm, available_agents=available_specialist_names())
    plan = planner.plan("task")
    # Default plan kicks in
    assert "researcher" in plan.agents or "writer" in plan.agents
    assert "unparseable" in plan.reasoning.lower() or "default" in plan.reasoning.lower()


def test_planner_filters_unknown_agents(fake_llm_factory):
    raw = json.dumps({"agents": ["researcher", "made_up_agent"], "reasoning": "x"})
    llm = fake_llm_factory({"planner": raw})
    planner = PlannerAgent(llm, available_agents=available_specialist_names())
    plan = planner.plan("task")
    assert plan.agents == ["researcher"]


def test_synthesizer_combines_outputs(fake_llm_factory):
    llm = fake_llm_factory({"synthesizer": "combined answer"})
    synth = SynthesizerAgent(llm)
    results = [
        AgentResult("researcher", "facts", 0.1, True),
        AgentResult("writer", "prose", 0.1, True),
    ]
    out = synth.synthesize("task", results)
    assert out == "combined answer"


def test_synthesizer_handles_no_successful_results(fake_llm_factory):
    llm = fake_llm_factory({})
    synth = SynthesizerAgent(llm)
    results = [AgentResult("researcher", "", 0.1, False, error="failed")]
    out = synth.synthesize("task", results)
    assert "aborted" in out.lower() or "no specialist" in out.lower()


def test_build_specialists_returns_all(fake_llm_factory):
    llm = fake_llm_factory({})
    specs = build_specialists(llm)
    assert set(specs.keys()) == set(available_specialist_names())
