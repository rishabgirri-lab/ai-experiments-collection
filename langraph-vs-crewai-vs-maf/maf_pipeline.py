"""
maf_pipeline.py
===============
Microsoft Agent Framework (MAF) — the unified successor to AutoGen and
Semantic Kernel (1.0 GA, April 2026). Mental model: production-grade agents
plus an explicit, typed orchestration layer.

You create `ChatAgent`s bound to a chat client, then either chain their
`.run()` calls (shown here) or compose them with `WorkflowBuilder` /
orchestration patterns (sequential, concurrent, handoff, group-chat,
magentic). The pitch is "same concepts and APIs across Python AND .NET,"
with built-in OpenTelemetry tracing, middleware, durable workflows, and
governance hooks.

WHEN MAF SHINES
---------------
* You're a Microsoft / Azure shop, or you need Python + .NET parity.
* Production concerns matter: observability, middleware, durable/long-running
  workflows, human-in-the-loop, governance (Purview), enterprise support.
* You want typed workflows (executors + edges) with checkpointing.

WHERE IT FIGHTS YOU
-------------------
* Heavier than CrewAI for a quick prototype; more ceremony than a few roles.
* Younger ecosystem than LangChain/LangGraph; docs still settling.

Below we use the simplest correct MAF pattern: a chain of ChatAgent.run()
calls (matches the official "sequential workflow" sample). See the comment
at the bottom for the WorkflowBuilder equivalent.

Run real:  pip install agent-framework && export OPENAI_API_KEY=sk-... && python maf_pipeline.py
Run mock:  python maf_pipeline.py     # no key needed, prints a simulation
"""

from __future__ import annotations

import asyncio

from shared import TOPIC, MODEL, API_KEY, BASE_URL, PROVIDER, HAS_LLM, banner, llm_complete


async def _run_async(topic: str) -> str:
    from agent_framework import ChatAgent
    from agent_framework.openai import OpenAIChatClient

    # Provider-aware client. For OpenAI, base_url is None (SDK default).
    # For Groq, we pass Groq's OpenAI-compatible endpoint + key.
    client_kwargs = {"model_id": MODEL, "api_key": API_KEY}
    if BASE_URL:
        client_kwargs["base_url"] = BASE_URL  # Groq endpoint
    client = OpenAIChatClient(**client_kwargs)

    researcher = ChatAgent(
        chat_client=client,
        name="Researcher",
        instructions="Produce 4-6 terse factual bullets. No preamble.",
    )
    writer = ChatAgent(
        chat_client=client,
        name="Writer",
        instructions="Write a tight ~150 word article. No headings, no fluff.",
    )
    reviewer = ChatAgent(
        chat_client=client,
        name="Reviewer",
        instructions="Reply 'APPROVE' or 'REVISE: <one fix>'.",
    )

    def text(resp) -> str:
        return getattr(resp, "text", str(resp))

    research = text(await researcher.run(f"Research: {topic}"))
    draft = text(await writer.run(f"Write a ~150 word article from:\n{research}"))
    verdict = text(await reviewer.run(f"Review:\n{draft}"))
    print(f"[maf] reviewer verdict: {verdict}")
    return draft


def run(topic: str = TOPIC, verbose: bool = False) -> str:
    try:
        import agent_framework  # noqa: F401
    except Exception:
        return _simulate(topic, reason="agent-framework not installed")

    if not HAS_LLM:
        return _simulate(topic, reason="no API key set")

    try:
        return asyncio.run(_run_async(topic))
    except TypeError as e:
        # Some agent-framework versions may not accept base_url on the client.
        # Don't crash the demo — fall back to the (still real-model) sim path.
        if BASE_URL:
            print(f"[maf] this agent-framework build rejected base_url ({e}); "
                  f"falling back to the shared client.")
            return _simulate(topic, reason="MAF client lacks base_url for Groq")
        raise


def _simulate(topic: str, reason: str) -> str:
    """Pure-Python mirror of the MAF sequential-agent chain."""
    print(f"[maf] SIMULATION ({reason}) — install agent-framework + set a key for the real run.")
    research = llm_complete("researcher", f"Research: {topic}")
    draft = llm_complete("writer", f"Write a ~150 word article from:\n{research}")
    verdict = llm_complete("reviewer", f"Review:\n{draft}")
    print(f"[maf] reviewer verdict: {verdict}")
    return draft


if __name__ == "__main__":
    banner("Microsoft Agent Framework — sequential ChatAgent chain")
    print(run(verbose=True))


# ---------------------------------------------------------------------------
# WorkflowBuilder equivalent (MAF's typed graph layer), for reference:
#
#   from agent_framework import WorkflowBuilder, executor, WorkflowContext
#   from typing_extensions import Never
#
#   @executor(id="writer")
#   async def writer_exec(task: str, ctx: WorkflowContext[str]) -> None:
#       await ctx.send_message(f"Draft: {task}")
#
#   @executor(id="reviewer")
#   async def reviewer_exec(draft: str, ctx: WorkflowContext[Never, str]) -> None:
#       await ctx.yield_output(draft)
#
#   workflow = (
#       WorkflowBuilder(start_executor=writer_exec)
#       .add_edge(writer_exec, reviewer_exec)
#       .build()
#   )
#
# Use this when you want checkpointing, streaming events, sub-workflows, or
# the handoff / concurrent / magentic orchestration patterns.
# ---------------------------------------------------------------------------
