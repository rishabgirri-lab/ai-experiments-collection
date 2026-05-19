"""Command-line entry point.

Usage:
    python -m orchestrator "your task here"
    python -m orchestrator                       # uses demo task

Honors environment variables:
    LLM_PROVIDER       (anthropic | openai | mock)
    ANTHROPIC_API_KEY  (if provider=anthropic)
    OPENAI_API_KEY     (if provider=openai)
    LOG_LEVEL          (DEBUG | INFO | WARNING | ERROR)
"""
from __future__ import annotations
from dotenv import load_dotenv
load_dotenv()

import sys

from orchestrator.config import get_settings
from orchestrator.core import build_default_orchestrator
from orchestrator.logging_setup import configure_logging


DEFAULT_TASK = "Explain how solar panels work and write a short summary for a 10-year-old."


def main(argv: list[str] | None = None) -> int:
    configure_logging()
    settings = get_settings()

    task = " ".join(sys.argv[1:] if argv is None else argv) or DEFAULT_TASK

    print(f"\n{'=' * 60}")
    print(f"Provider: {settings.provider}")
    print(f"Task:     {task}")
    print(f"{'=' * 60}\n")

    orchestrator = build_default_orchestrator()
    result = orchestrator.run(task)

    print(f"\n{'=' * 60}\nPLAN\n{'=' * 60}")
    print(f"Agents:    {result.plan.agents}")
    print(f"Reasoning: {result.plan.reasoning}")

    print(f"\n{'=' * 60}\nSPECIALIST RESULTS\n{'=' * 60}")
    for r in result.specialist_results:
        status = "OK" if r.success else "FAIL"
        print(f"  - {r.agent_name:12s} [{status}] {r.latency_seconds}s")
        if not r.success:
            print(f"      error: {r.error}")

    print(f"\n{'=' * 60}\nFINAL ANSWER\n{'=' * 60}")
    print(result.final_answer)
    print(f"\n{'=' * 60}")
    print(f"Total latency: {result.total_latency_seconds}s")
    print(f"{'=' * 60}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
