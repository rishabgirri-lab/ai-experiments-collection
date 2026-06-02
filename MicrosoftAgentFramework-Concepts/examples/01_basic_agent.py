"""
01 — The Basic Agent
====================

CONCEPT
-------
An **agent** = an LLM (the "brain") + instructions (its persona/policy) + an
optional set of tools/memory. In MAF the smallest useful unit is created by
wrapping a chat client into an Agent.

Two equivalent ways to build one:
    agent = chat_client.as_agent(name=..., instructions=...)        # convenience
    agent = Agent(client=chat_client, name=..., instructions=...)   # explicit

KEY API (agent-framework 1.7.x)
-------------------------------
* `await agent.run("...")`  -> returns an AgentResponse (await it).
* `response.text`           -> the final assistant text.

NAMING NOTE (great interview trivia)
------------------------------------
Earlier MAF/docs called this `ChatAgent` and the memory object `AgentThread`.
In 1.7.x they are `Agent` and `AgentSession`. The *concepts* are identical.

RUN
---
    python examples/01_basic_agent.py
"""

import asyncio

from _shared import banner, build_chat_client


async def main() -> None:
    banner("01 — Basic Agent")

    chat_client = build_chat_client()

    # Instructions are the "system prompt": they shape behaviour for every turn.
    agent = chat_client.as_agent(
        name="Haiku-Bot",
        instructions="You are a poet. Always answer with a single, three-line haiku.",
    )

    response = await agent.run("Explain what an AI agent is.")
    print(response.text)


if __name__ == "__main__":
    asyncio.run(main())
