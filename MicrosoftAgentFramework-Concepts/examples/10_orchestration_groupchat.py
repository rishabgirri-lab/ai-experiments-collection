"""
10 — Group Chat Orchestration
=============================

CONCEPT
-------
Multiple agents collaborate in a shared conversation, taking turns. An
orchestrator/selection policy decides who speaks next, and a termination
condition (or max rounds) ends it. Use it for debate, brainstorming, or
role-play where agents build on each other turn by turn.



Difference vs Concurrent: group chat is *turn-based and shared* (agents read each
other's messages); concurrent is *parallel and independent*.

Interview soundbite:
  "Group chat = a managed round-robin/selected conversation among agents with a
   termination condition. The orchestrator picks the next speaker each round."

RUN
---
    python examples/10_orchestration_groupchat.py
"""

import asyncio

from _shared import banner, build_chat_client

import asyncio

from agent_framework import AgentResponse, AgentResponseUpdate
from agent_framework.orchestrations import GroupChatBuilder, GroupChatState

from _shared import banner, build_chat_client

SPEAKERS = ["Optimist", "Pessimist"]


def round_robin_selector(state: GroupChatState) -> str:
    """Deterministic alternation. Never returns None (this build treats the
    return value as a required participant name; termination is max_rounds)."""
    return SPEAKERS[state.current_round % len(SPEAKERS)]


async def main() -> None:
    banner("10 — Group Chat Orchestration")

    client = build_chat_client()

    optimist = client.as_agent(
        name="Optimist",
        instructions="You argue FOR the idea. One short paragraph per turn. Be specific.",
    )
    pessimist = client.as_agent(
        name="Pessimist",
        instructions="You argue AGAINST the idea. One short paragraph per turn. Be specific.",
    )

    workflow = (
        GroupChatBuilder(
            participants=[optimist, pessimist],
            selection_func=round_robin_selector,
            intermediate_output_from=[optimist, pessimist],
        )
        .with_max_rounds(8)   # 8 turns -> 4 Optimist + 4 Pessimist
        .build()
    )

    task = "Should companies switch to a 4-day work week?"

    last_author: str | None = None

    async for event in workflow.run(task, stream=True):
        if event.type not in ("intermediate", "output"):
            continue

        data = event.data

        # Streaming delta from a participant
        if isinstance(data, AgentResponseUpdate):
            author = data.author_name or "?"
            if author != last_author:
                print(f"\n\n[{author}]")
                last_author = author
            print(data.text or "", end="", flush=True)

        # Terminal completion (orchestrator)
        elif isinstance(data, AgentResponse):
            for msg in data.messages:
                print(f"\n\n[{msg.author_name or msg.role}]\n{msg.text}")

    print()


if __name__ == "__main__":
    asyncio.run(main())