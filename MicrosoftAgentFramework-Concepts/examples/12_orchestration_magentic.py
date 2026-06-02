"""
12 — Magentic Orchestration (Manager-led Planning)
==================================================

CONCEPT
-------
"Magentic" (from Microsoft's Magentic-One research) is a manager-led pattern for
open-ended, complex tasks. A **manager** maintains a task ledger (facts + plan),
delegates sub-tasks to specialist agents, tracks progress, detects stalls, and
decides when the task is done. It's the most autonomous of the orchestration
patterns — closest to "give it a goal and let the team figure it out."

KEY API
-------
    from agent_framework.orchestrations import MagenticBuilder
    wf = MagenticBuilder(
            participants=[researcher, coder, writer],
            manager_agent=manager_brain,    # the LLM that plans & coordinates
            max_round_count=8,
         ).build()
    result = await wf.run("the open-ended goal")

When to use which orchestration (interview cheat-sheet):
  * Sequential  -> known, fixed pipeline of steps
  * Concurrent  -> independent perspectives, merge results
  * Group chat  -> turn-based collaboration/debate
  * Handoff     -> dynamic routing to specialists
  * Magentic    -> open-ended goal needing a planner/manager

RUN
---
    python examples/12_orchestration_magentic.py
"""

import asyncio

from agent_framework.orchestrations import MagenticBuilder

from _shared import banner, build_chat_client


async def main() -> None:
    banner("12 — Magentic Orchestration")

    client = build_chat_client()

    manager = client.as_agent(
        name="Manager",
        instructions="You plan and coordinate specialists to fully solve the user's goal.",
    )
    researcher = client.as_agent(
        name="Researcher",
        instructions="You gather and summarise relevant facts for the task.",
    )
    writer = client.as_agent(
        name="Writer",
        instructions="You produce the final polished written deliverable.",
    )

    workflow = (
        MagenticBuilder(
            participants=[researcher, writer],
            manager_agent=manager,
            max_round_count=6,   # keep it bounded so the demo always finishes
        ).build()
    )

    result = await workflow.run(
        "Produce a 5-bullet beginner guide to starting a home compost bin."
    )

    for item in result.get_outputs():
        text = getattr(item, "text", None)
        if text:
            print(text)
        else:
            for msg in getattr(item, "messages", []) or []:
                print(f"\n[{msg.author_name or msg.role}]\n{msg.text}")


if __name__ == "__main__":
    asyncio.run(main())
