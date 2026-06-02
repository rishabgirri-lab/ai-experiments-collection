"""
13 — Workflows: Executors & Edges (the graph engine)
====================================================

CONCEPT
-------
Below the high-level orchestration builders sits MAF's **workflow engine**: a
graph of **executors** (units of work) connected by **edges** (data flow). You
define each step, wire them together, and the runtime handles execution, message
passing, and typed validation. Executors can be plain functions, classes, OR
agents — letting you mix deterministic code with LLM steps.

KEY API
-------
* `@executor(id="...")` turns an `async def fn(data, ctx)` into a node.
* `ctx.send_message(x)` forwards `x` to the next executor along an edge.
* `ctx.yield_output(x)` emits a final workflow output.
* `WorkflowContext[T]`        -> sends messages of type T
  `WorkflowContext[Never, U]` -> yields workflow output of type U
* Build with `WorkflowBuilder(start_executor=first).add_edge(a, b).build()`.

Interview soundbite:
  "Workflows are typed, directed graphs of executors. Orchestration patterns are
   pre-built graphs; the builder lets you author arbitrary ones — deterministic
   code and agents as nodes in the same graph."

RUN
---
    python examples/13_workflow_executors_edges.py
"""

import asyncio

from typing_extensions import Never

from agent_framework import WorkflowBuilder, WorkflowContext, executor

from _shared import banner


@executor(id="to_upper")
async def to_upper(text: str, ctx: WorkflowContext[str]) -> None:
    """Step 1: uppercase, then forward to the next executor."""
    await ctx.send_message(text.upper())


@executor(id="add_excitement")
async def add_excitement(text: str, ctx: WorkflowContext[str]) -> None:
    """Step 2: add emphasis, then forward."""
    await ctx.send_message(text + "!!!")


@executor(id="reverse")
async def reverse_text(text: str, ctx: WorkflowContext[Never, str]) -> None:
    """Step 3: reverse and yield the final output."""
    await ctx.yield_output(text[::-1])


async def main() -> None:
    banner("13 — Workflows: Executors & Edges")

    workflow = (
        WorkflowBuilder(start_executor=to_upper)
        .add_edge(to_upper, add_excitement)
        .add_edge(add_excitement, reverse_text)
        .build()
    )

    result = await workflow.run("hello agent framework")
    print("Outputs:", result.get_outputs())
    # NOTE: this example uses NO LLM — it runs fully offline (no API key needed),
    # proving workflows can orchestrate pure deterministic code too.


if __name__ == "__main__":
    asyncio.run(main())
