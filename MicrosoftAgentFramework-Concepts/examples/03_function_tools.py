"""
03 — Function Tools (Function Calling)
======================================

CONCEPT
-------
Tools turn a "chat model" into an "agent that can act". You expose plain Python
functions; the model decides *when* to call them and *with what arguments*; the
framework runs the function and feeds the result back to the model — looping
until the model produces a final answer. This loop is the heart of agentic AI.

KEY API
-------
* Decorate a function with `@tool`. The docstring + type hints become the JSON
  schema the model sees, so write them well.
* Pass tools to the agent: `as_agent(..., tools=[fn1, fn2])`.
* `approval_mode="always_require"` would pause for human approval before the
  tool runs (human-in-the-loop). Default is to run automatically.

Interview soundbite:
  "The @tool decorator auto-generates the function-calling JSON schema from the
   signature and docstring. The framework owns the call→execute→observe loop."

RUN
---
    python examples/03_function_tools.py
"""

import asyncio

from agent_framework import tool

from _shared import banner, build_chat_client


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    # In real life you'd call an API. We fake it deterministically.
    fake = {"paris": "18°C, light rain", "tokyo": "26°C, sunny", "cairo": "33°C, clear"}
    return fake.get(city.lower(), f"No data for {city}, assume 20°C and cloudy.")


@tool
def convert_currency(amount: float, frm: str, to: str) -> str:
    """Convert an amount of money from one currency to another."""
    rates = {("usd", "eur"): 0.92, ("eur", "usd"): 1.09, ("usd", "inr"): 83.0}
    rate = rates.get((frm.lower(), to.lower()))
    if rate is None:
        return f"No rate available for {frm}->{to}."
    return f"{amount} {frm.upper()} = {round(amount * rate, 2)} {to.upper()}"


async def main() -> None:
    banner("03 — Function Tools")

    agent = build_chat_client().as_agent(
        name="Assistant",
        instructions="You are a helpful assistant. Use tools when they help.",
        tools=[get_weather, convert_currency],
    )

    # The model should call BOTH tools to answer this, then summarise.
    response = await agent.run(
        "What's the weather in Tokyo, and how much is 50 USD in EUR?"
    )
    print(response.text)


if __name__ == "__main__":
    asyncio.run(main())
