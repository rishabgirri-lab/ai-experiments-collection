"""Dynamic Agent Orchestration system.

A multi-agent pipeline where a Planner dynamically selects specialist
agents (Researcher, Coder, Analyst, Writer), they execute in parallel,
and a Synthesizer combines their outputs.

Quick usage:
    from orchestrator.core import build_default_orchestrator
    result = build_default_orchestrator().run("your task")
    print(result.final_answer)
"""
__version__ = "0.1.0"
