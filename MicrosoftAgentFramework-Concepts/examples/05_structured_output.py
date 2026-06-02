"""
05 — Structured Output (Typed Results)
======================================

CONCEPT
-------
Often you don't want free-form text — you want a typed object you can use in
code (e.g. to store in a DB or pass to another system). MAF lets you declare a
Pydantic model as the `response_format`; the framework instructs the model to
emit conforming JSON and parses it for you.

KEY API
-------
* Define a `pydantic.BaseModel`.
* Pass it as `default_options={"response_format": MyModel}` when building the
  agent (or `options={...}` per run).
* Read the parsed object from `response.value` (and the raw text from `.text`).

Interview soundbite:
  "response_format binds the model's output to a schema. response.value gives you
   the validated, typed object — no brittle regex parsing of free text."

RUN
---
    python examples/05_structured_output.py
"""

import asyncio

from pydantic import BaseModel, Field

from _shared import banner, build_chat_client


class Recipe(BaseModel):
    title: str = Field(description="Name of the dish")
    servings: int
    ingredients: list[str]
    steps: list[str]


async def main() -> None:
    banner("05 — Structured Output")

    agent = build_chat_client().as_agent(
        name="Chef",
        instructions="You are a chef. Produce a recipe matching the requested schema.",
        default_options={"response_format": Recipe},
    )

    response = await agent.run("Give me a simple recipe for masala chai for 2 people.")

    recipe = response.value  # already a Recipe instance
    print("Parsed object type:", type(recipe).__name__)
    print("Title   :", recipe.title)
    print("Servings:", recipe.servings)
    print("Ingredients:")
    for ing in recipe.ingredients:
        print("   -", ing)
    print("Steps:")
    for i, step in enumerate(recipe.steps, 1):
        print(f"  {i}. {step}")


if __name__ == "__main__":
    asyncio.run(main())
