"""
16 — Workflows: Human-in-the-Loop (Pause & Resume)
==================================================

CONCEPT
-------
Production agents often must PAUSE for a human decision (approve a refund, sign
off a deployment) and RESUME later — possibly minutes or days later, in a
different process. MAF models this with `request_info`: an executor emits a
request, the workflow halts and surfaces it, and you resume by supplying the
response keyed by its request id. Pair with checkpointing for durability.

KEY API
-------
* Inside a class-based `Executor`:
    @handler             -> normal step; call `await ctx.request_info(data, RespType)`
    @response_handler    -> runs when the human's response arrives
* `result = await workflow.run(input)`        -> may pause
* `result.get_request_info_events()`          -> pending questions (id + data)
* `await workflow.run(responses={req_id: ans})` -> resume with the answer

Interview soundbite:
  "request_info is durable human-in-the-loop: the workflow yields a typed request
   and suspends; you resume it by mapping request ids to responses. With
   checkpointing the pause can outlive the process."

RUN (no LLM needed — pure code; we simulate the human)
------------------------------------------------------
    python examples/16_workflow_human_in_the_loop.py
"""

import asyncio
from dataclasses import dataclass

from typing_extensions import Never

from agent_framework import (
    Executor,
    WorkflowBuilder,
    WorkflowContext,
    handler,
    response_handler,
)

from _shared import banner


@dataclass
class ApprovalRequest:
    question: str
    amount: int


class RefundApprover(Executor):
    @handler
    async def start(self, amount: int, ctx: WorkflowContext) -> None:
        """Pause and ask a human to approve the refund."""
        req = ApprovalRequest(question=f"Approve a refund of ${amount}?", amount=amount)
        await ctx.request_info(req, bool)  # bool = the response type we expect

    @response_handler
    async def on_decision(
        self,
        request: ApprovalRequest,
        approved: bool,
        ctx: WorkflowContext[Never, str],
    ) -> None:
        """Runs once the human answers; produce the final outcome."""
        if approved:
            await ctx.yield_output(f"REFUND ISSUED for ${request.amount}.")
        else:
            await ctx.yield_output(f"REFUND DENIED for ${request.amount}.")


async def main() -> None:
    banner("16 — Workflows: Human-in-the-Loop")

    approver = RefundApprover(id="approver")
    workflow = WorkflowBuilder(start_executor=approver).build()

    # 1) Start the workflow — it will PAUSE on the approval request.
    result = await workflow.run(750)
    pending = result.get_request_info_events()
    req_event = pending[0]
    print(f"[paused] Human asked: {req_event.data.question}")
    print(f"[paused] request_id = {req_event.request_id}")

    # 2) A human (here: us) decides. Imagine this happens later / elsewhere.
    human_says_yes = True
    print(f"[human] responding with: {human_says_yes}")

    # 3) RESUME by mapping the request id to the human's answer.
    resumed = await workflow.run(responses={req_event.request_id: human_says_yes})
    print("[done] outputs:", resumed.get_outputs())


if __name__ == "__main__":
    asyncio.run(main())
