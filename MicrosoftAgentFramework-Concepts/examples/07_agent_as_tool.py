"""
07 — Agent as a Tool (Composition)
==================================

CONCEPT
-------
A powerful pattern: let one agent call another *specialist* agent as if it were
a tool. The "orchestrator" agent stays high-level; specialists encapsulate
domain skill or a different model/persona. This is the simplest form of
multi-agent design and a stepping stone to full orchestration (examples 08-12).

HOW
---
Wrap a specialist agent inside a `@tool` function. The function just calls
`await specialist.run(...)` and returns the text. The orchestrator's model then
decides when to delegate.

Interview soundbite:
  "Agent-as-tool composes agents through the function-calling interface. It's
   explicit delegation: the parent chooses when to hand a sub-task to a child."

RUN
---
    python examples/07_agent_as_tool.py
"""

import asyncio

from agent_framework import tool

from _shared import banner, build_chat_client

# One shared client is fine; you could give each specialist a different model.
client = build_chat_client()

# A specialist that ONLY translates to French.
translator = client.as_agent(
    name="FrenchTranslator",
    instructions="You translate any input text into natural French. Output only the translation.",
)

# A specialist that ONLY writes marketing taglines.
copywriter = client.as_agent(
    name="Copywriter",
    instructions="You write punchy one-line marketing taglines. Output only the tagline.",
)


@tool
async def translate_to_french(text: str) -> str:
    """Translate the given text into French."""
    resp = await translator.run(text)
    return resp.text


@tool
async def write_tagline(product: str) -> str:
    """Write a catchy marketing tagline for the given product."""
    resp = await copywriter.run(f"Product: {product}")
    return resp.text


async def main() -> None:
    banner("07 — Agent as a Tool")

    orchestrator = client.as_agent(
        name="Manager",
        instructions=(
            "You coordinate specialists. Use your tools to build the final "
            "deliverable, then present it clearly."
        ),
        tools=[write_tagline, translate_to_french],
    )

    response = await orchestrator.run(
        "Create a catchy tagline for an eco-friendly water bottle, "
        "then give me the French version too."
    )
    print(response.text)


if __name__ == "__main__":
    asyncio.run(main())
