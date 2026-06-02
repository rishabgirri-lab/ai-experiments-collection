"""
04 — Conversation Memory (AgentSession)
=======================================

CONCEPT
-------
By default each `agent.run(...)` is stateless — the model forgets the previous
turn. To hold a multi-turn conversation you attach a **session** (formerly called
a "thread"). The session stores the running message history and is passed back
into each call.

KEY API
-------
* `session = agent.create_session()`
* `await agent.run("...", session=session)`  (reuse the same session object)

Without a session the agent cannot answer "what did I just say?"; with one it can.

Interview soundbite:
  "A session is the conversation's memory boundary. Stateless run = single turn;
   pass a session and the agent accumulates context across turns. In 1.7.x the
   type is AgentSession (it used to be AgentThread)."

RUN
---
    python examples/04_conversation_memory.py
"""

import asyncio

from _shared import banner, build_chat_client


async def main() -> None:
    banner("04 — Conversation Memory")

    agent = build_chat_client().as_agent(
        name="Memo",
        instructions="You are a friendly assistant with a good memory.",
    )

    session = agent.create_session()

    r1 = await agent.run("My name is Aditi and I love mountains.", session=session)
    print("Turn 1:", r1.text, "\n")

    # Because we reuse the same session, the agent remembers turn 1.
    r2 = await agent.run("What's my name and what do I love?", session=session)
    print("Turn 2:", r2.text, "\n")

    # Contrast: a brand-new run WITHOUT the session has no memory.
    r3 = await agent.run("What's my name?")
    print("Turn 3 (no session):", r3.text)


if __name__ == "__main__":
    asyncio.run(main())
