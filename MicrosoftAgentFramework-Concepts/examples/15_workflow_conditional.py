"""
15 — Workflows: Conditional Routing (Branching)
===============================================

CONCEPT
-------
Edges can carry a **condition**: the message only travels down an edge if its
predicate returns True. This gives you if/else branching and content-based
routing inside a workflow graph.

KEY API
-------
* `.add_edge(source, target, condition=lambda msg: ...)`
  The message flows to `target` only when `condition(msg)` is truthy.
* For many mutually-exclusive branches there is also
  `.add_switch_case_edge_group(source, [Case(...), Default(...)])`.

Interview soundbite:
  "Conditional edges turn a workflow into a decision graph. The same emitted
   message is offered to each outgoing edge; only edges whose predicate passes
   forward it — enabling branching, routing and guards."

RUN (no LLM needed — pure code)
-------------------------------
    python examples/15_workflow_conditional.py
"""

import asyncio

from typing_extensions import Never

from agent_framework import WorkflowBuilder, WorkflowContext, executor

from _shared import banner


@executor(id="classify")
async def classify(amount: int, ctx: WorkflowContext[int]) -> None:
    """Emit the order amount; downstream edges decide where it goes."""
    print(f"[classify] order amount = {amount}")
    await ctx.send_message(amount)


@executor(id="auto_approve")
async def auto_approve(amount: int, ctx: WorkflowContext[Never, str]) -> None:
    await ctx.yield_output(f"AUTO-APPROVED order of ${amount} (small).")


@executor(id="manager_review")
async def manager_review(amount: int, ctx: WorkflowContext[Never, str]) -> None:
    await ctx.yield_output(f"ROUTED TO MANAGER: order of ${amount} (large).")


async def main() -> None:
    banner("15 — Workflows: Conditional Routing")

    THRESHOLD = 1000

    workflow = (
        WorkflowBuilder(start_executor=classify)
        # small orders -> auto approve
        .add_edge(classify, auto_approve, condition=lambda amt: amt < THRESHOLD)
        # large orders -> manager review
        .add_edge(classify, manager_review, condition=lambda amt: amt >= THRESHOLD)
        .build()
    )

    for amount in (250, 5000):
        result = await workflow.run(amount)
        print("  ->", result.get_outputs(), "\n")


if __name__ == "__main__":
    asyncio.run(main())
