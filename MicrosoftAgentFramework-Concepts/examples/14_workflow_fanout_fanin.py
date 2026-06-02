"""
14 — Workflows: Fan-out / Fan-in (Parallelism)
==============================================

CONCEPT
-------
Workflows can split work to run in parallel (fan-out) and then join the results
(fan-in). This is the building block the high-level ConcurrentBuilder uses, but
here you author it explicitly with your own executors.

KEY API
-------
* `.add_fan_out_edges(source, [t1, t2, ...])` — source -> many in parallel.
* `.add_fan_in_edges([s1, s2, ...], target)`  — many -> one join executor.
* A fan-in executor receives a LIST of the upstream messages.

Interview soundbite:
  "Fan-out broadcasts one message to N executors run concurrently; fan-in waits
   for all of them and delivers their outputs as a list to a join node."

RUN (no LLM needed — pure code)
-------------------------------
    python examples/14_workflow_fanout_fanin.py
"""

import asyncio

from typing_extensions import Never

from agent_framework import WorkflowBuilder, WorkflowContext, executor

from _shared import banner


@executor(id="dispatch")
async def dispatch(number: int, ctx: WorkflowContext[int]) -> None:
    """Broadcast the same number to all parallel workers."""
    await ctx.send_message(number)


@executor(id="square")
async def square(n: int, ctx: WorkflowContext[dict]) -> None:
    await ctx.send_message({"op": "square", "value": n * n})


@executor(id="cube")
async def cube(n: int, ctx: WorkflowContext[dict]) -> None:
    await ctx.send_message({"op": "cube", "value": n * n * n})


@executor(id="negate")
async def negate(n: int, ctx: WorkflowContext[dict]) -> None:
    await ctx.send_message({"op": "negate", "value": -n})


@executor(id="aggregate")
async def aggregate(results: list[dict], ctx: WorkflowContext[Never, dict]) -> None:
    """Fan-in: receives a LIST of all worker outputs."""
    merged = {r["op"]: r["value"] for r in results}
    await ctx.yield_output(merged)


async def main() -> None:
    banner("14 — Workflows: Fan-out / Fan-in")

    workflow = (
        WorkflowBuilder(start_executor=dispatch)
        .add_fan_out_edges(dispatch, [square, cube, negate])
        .add_fan_in_edges([square, cube, negate], aggregate)
        .build()
    )

    result = await workflow.run(5)
    print("Aggregated parallel results for input 5:")
    print(result.get_outputs())


if __name__ == "__main__":
    asyncio.run(main())
