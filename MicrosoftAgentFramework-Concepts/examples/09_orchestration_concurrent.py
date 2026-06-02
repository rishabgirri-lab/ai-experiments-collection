"""
09 — Concurrent Orchestration (Fan-out / Fan-in)
================================================

CONCEPT
-------
Run several agents in parallel on the SAME input, then aggregate. Great when you
want multiple independent perspectives at once (e.g. researcher + marketer +
legal reviewing a product idea). Under the hood: a dispatcher fans out to all
participants, then a fan-in aggregator collects results.

KEY API
-------
    from agent_framework.orchestrations import ConcurrentBuilder
    wf = ConcurrentBuilder(participants=[a1, a2, a3]).build()
    result = await wf.run("the task")          # all run in parallel
    # .with_aggregator(fn) lets you customise how results are merged.

Interview soundbite:
  "Concurrent = fan-out/fan-in. Independent agents run simultaneously; an
   aggregator merges their outputs. Lower latency than running them in series."

RUN
---
    python examples/09_orchestration_concurrent.py
"""

import asyncio

from agent_framework.orchestrations import ConcurrentBuilder

from _shared import banner, build_chat_client


async def main() -> None:
    banner("09 — Concurrent Orchestration")

    client = build_chat_client()

    researcher = client.as_agent(
        name="Researcher",
        instructions="Give 2 bullet insights about the market for this idea.",
    )
    marketer = client.as_agent(
        name="Marketer",
        instructions="Give 2 bullet marketing angles for this idea.",
    )
    skeptic = client.as_agent(
        name="Skeptic",
        instructions="Give 2 bullet risks or objections about this idea.",
    )

    workflow = ConcurrentBuilder(participants=[researcher, marketer, skeptic]).build()

    result = await workflow.run(
        "A subscription service that delivers a new houseplant every month."
    )

    for item in result.get_outputs():
        for msg in getattr(item, "messages", []) or []:
            print(f"\n[{msg.author_name or msg.role}]\n{msg.text}")


if __name__ == "__main__":
    asyncio.run(main())
