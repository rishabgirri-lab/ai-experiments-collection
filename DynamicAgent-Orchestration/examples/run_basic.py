"""Programmatic-use example.

Demonstrates calling the orchestrator from Python code (instead of the CLI).

Run from project root:
    python examples/run_basic.py
"""
from __future__ import annotations

from orchestrator.core import build_default_orchestrator
from orchestrator.logging_setup import configure_logging


def main() -> None:
    configure_logging()

    orchestrator = build_default_orchestrator()

    tasks = [
        "Explain how solar panels work for a 10-year-old.",
        "Write a Python function that checks if a string is a palindrome.",
    ]

    for task in tasks:
        result = orchestrator.run(task)
        print(f"\n{'=' * 60}\nTASK: {task}\n{'=' * 60}")
        print(f"Plan: {result.plan.agents}")
        print(f"\nFinal answer:\n{result.final_answer}\n")


if __name__ == "__main__":
    main()
