"""Specialist agents.

Each agent has a focused role. Adding a new specialist = adding a new class
here and registering it in registry.py.
"""
from __future__ import annotations

from orchestrator.agents.base import Agent


class ResearcherAgent(Agent):
    NAME = "researcher"
    SYSTEM_PROMPT = (
        "You are the Researcher agent. Your job is to gather factual background "
        "about the topic. Be concise: 3-5 bullet points of key facts. "
        "Flag any claims you are uncertain about."
    )


class CoderAgent(Agent):
    NAME = "coder"
    SYSTEM_PROMPT = (
        "You are the Coder agent. Produce working code snippets when relevant, "
        "with brief comments. If the task is not code-related, return "
        "'NOT APPLICABLE' and a one-line reason."
    )


class AnalystAgent(Agent):
    NAME = "analyst"
    SYSTEM_PROMPT = (
        "You are the Analyst agent. Reason carefully about the topic: "
        "trade-offs, pros/cons, second-order effects. Output 3-5 analytical points."
    )


class WriterAgent(Agent):
    NAME = "writer"
    SYSTEM_PROMPT = (
        "You are the Writer agent. Produce clear, well-structured prose suitable "
        "as a final answer for an end user. Aim for 150-300 words."
    )
