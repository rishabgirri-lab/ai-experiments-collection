"""
08 — Sequential Orchestration
=============================

CONCEPT
-------
Sequential orchestration chains agents in a fixed order, passing the growing
conversation from one to the next: a pipeline. Classic uses: draft -> edit ->
fact-check, or write -> translate -> review.

KEY API
-------
    from agent_framework.orchestrations import SequentialBuilder
    workflow = SequentialBuilder(participants=[a1, a2, a3]).build()
    result = await workflow.run("the task")
    outputs = result.get_outputs()    # final conversation / messages

The high-level orchestration builders compile down to the same Workflow engine
you'll meet in examples 13-16 — they're convenience wrappers over the graph.

Interview soundbite:
  "Sequential = deterministic pipeline. Each participant sees the prior output
   and refines it. It's the multi-agent analogue of Unix pipes."

RUN
---
    python examples/08_orchestration_sequential.py
"""

import asyncio

from agent_framework.orchestrations import SequentialBuilder

from _shared import banner, build_chat_client


def chunk_text(obj) -> str:
    """Pull text from a message/delta, tolerating None on .text and content parts."""
    t = getattr(obj, "text", None)
    if t:
        return t
    out = []
    for p in getattr(obj, "contents", None) or []:
        pt = getattr(p, "text", None)
        if pt:
            out.append(pt)
    return "".join(out)


async def main() -> None:
    banner("08 — Sequential Orchestration")

    client = build_chat_client()

    writer = client.as_agent(
        name="Writer",
        instructions="Write a short, rough first draft (3-4 sentences) on the topic.",
    )
    editor = client.as_agent(
        name="Editor",
        instructions="Improve clarity and flow of the draft you receive. Keep it short.",
    )
    headline = client.as_agent(
        name="Headliner",
        instructions=(
            "You will receive an edited paragraph as the last message. "
            "Respond with a punchy title on the first line, then a blank line, "
            "then reproduce that edited paragraph. Always produce output."
        ),
    )

    workflow = SequentialBuilder(participants=[writer, editor, headline]).build()

    # Each agent's text arrives as streaming deltas inside 'executor_completed'
    # events. Attribute text only to the executor that produced it (author == id)
    # so the Writer's words aren't re-counted in later accumulated conversations.
    results: dict[str, str] = {}
    order: list[str] = []

    async for event in workflow.run(
        "The benefits of walking 30 minutes a day.", stream=True
    ):
        if event.type != "executor_completed":
            continue
        eid = getattr(event, "executor_id", None)
        data = getattr(event, "data", None)
        if not isinstance(data, (list, tuple)):
            continue
        text = "".join(chunk_text(m) for m in data
                        if getattr(m, "author_name", None) == eid)
        if text:
            if eid not in results:
                order.append(eid)
            results[eid] = text   # last completed snapshot wins

    print("Final pipeline output:\n")
    for eid in order:
        print(f"[{eid}]\n{results[eid]}\n")


if __name__ == "__main__":
    asyncio.run(main())
