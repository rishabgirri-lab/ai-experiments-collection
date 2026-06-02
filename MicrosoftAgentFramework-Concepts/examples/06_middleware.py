"""
06 — Middleware (Cross-cutting Concerns)
========================================

CONCEPT
-------
Middleware lets you wrap agent behaviour with reusable, composable logic —
logging, timing, auth, rate-limiting, input/output guarding, caching — WITHOUT
touching the agent's core logic. It is the classic "onion"/pipeline pattern:
each middleware can run code before and after calling `next`.

THREE LEVELS (all are just `async def fn(context, next)`):
  * @agent_middleware    — wraps the whole agent.run() invocation
  * @function_middleware — wraps each tool/function call (validate, block, mock)
  * @chat_middleware     — wraps each raw call to the underlying chat client

KEY POINTS
----------
* Call `await next()` to continue down the pipeline; skip it to short-circuit.
* Inspect/modify `context` (messages, arguments, result, metadata).
* Raise `MiddlewareTermination` from function middleware to veto a tool call.

Interview soundbite:
  "Middleware is aspect-oriented programming for agents. agent/function/chat
   levels let you intercept at the invocation, the tool call, or the raw model
   call respectively — for observability, governance and guardrails."

RUN
---
    python examples/06_middleware.py
"""

import asyncio
import time

from agent_framework import (
    agent_middleware,
    chat_middleware,
    function_middleware,
    tool,
)

from _shared import banner, build_chat_client


@tool
def delete_database(name: str) -> str:
    """Permanently delete a database by name. DANGEROUS."""
    return f"Database '{name}' deleted."  # (we will never actually let this run)


# --- Agent-level: time the whole invocation -------------------------------
@agent_middleware
async def timing_mw(context, next):
    start = time.perf_counter()
    print(f"[agent-mw] agent '{context.agent.name}' starting...")
    await next()
    elapsed = (time.perf_counter() - start) * 1000
    print(f"[agent-mw] finished in {elapsed:.0f} ms")


# --- Function-level: block dangerous tool calls ---------------------------
@function_middleware
async def guardrail_mw(context, next):
    print(f"[fn-mw] tool requested: {context.function.name} args={context.arguments}")
    if context.function.name == "delete_database":
        # Veto: do not call next(); instead set a safe result.
        context.result = "BLOCKED by guardrail middleware: destructive tool denied."
        print("[fn-mw] -> blocked destructive call")
        return
    await next()


# --- Chat-level: see the raw model call -----------------------------------
@chat_middleware
async def chat_logger_mw(context, next):
    print(f"[chat-mw] -> model='{context.options.get('model')}', "
          f"messages={len(context.messages)}")
    await next()


async def main() -> None:
    banner("06 — Middleware")

    agent = build_chat_client().as_agent(
        name="Guarded-Agent",
        instructions="You are an ops assistant. Use tools to fulfil requests.",
        tools=[delete_database],
        middleware=[timing_mw, guardrail_mw, chat_logger_mw],
    )

    response = await agent.run("Please delete the database called 'prod'.")
    print("\nFinal answer:\n", response.text)


if __name__ == "__main__":
    asyncio.run(main())
