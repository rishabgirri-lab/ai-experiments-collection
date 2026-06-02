"""
02 — Streaming Responses
========================

CONCEPT
-------
Instead of waiting for the whole answer, you can stream tokens as they are
produced. This is what powers "typing" UIs and lowers perceived latency.

KEY API
-------
* `agent.run("...", stream=True)` returns a **ResponseStream** (do NOT await it).
* Iterate it with `async for update in stream:` — each `update` is an
  AgentResponseUpdate whose `.text` holds the incremental chunk.

Interview soundbite:
  "Non-streaming `run` returns an awaitable; streaming `run(stream=True)` returns
   an async-iterable of update deltas. Same method, two shapes."

RUN
---
    python examples/02_streaming.py
"""

import asyncio

from _shared import banner, build_chat_client


async def main() -> None:
    banner("02 — Streaming")

    agent = build_chat_client().as_agent(
        name="Storyteller",
        instructions="You are a concise storyteller.",
    )

    print("Streaming answer:\n")
    stream = agent.run(
        "Tell me a 4-sentence story about a robot learning to paint.",
        stream=True,
    )
    async for update in stream:
        # Print each delta as it arrives, no newline, flush immediately.
        if update.text:
            print(update.text, end="", flush=True)
    print("\n")


if __name__ == "__main__":
    asyncio.run(main())
