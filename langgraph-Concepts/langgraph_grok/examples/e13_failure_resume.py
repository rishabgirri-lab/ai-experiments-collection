"""
13 — Failure & Durable Resume (restart from the node that failed)
=================================================================

This is the example that PROVES LangGraph's durable execution. We build a graph
A -> B -> C with a checkpointer, make node B FAIL the first time it runs, watch
the graph stop, then re-invoke the SAME thread and watch it resume from B — with
A's earlier result still intact and A NOT re-running.

Concepts shown here:
  * A checkpointer snapshots state after every successful super-step.
  * When a node raises, the graph stops; the last GOOD checkpoint is preserved
    (here: the state right after A succeeded).
  * Re-invoking the same thread_id with input=None RESUMES from the pending
    work (node B) instead of starting over.
  * IMPORTANT: resume is at the SUPER-STEP boundary, not mid-node. A failed node
    re-runs FROM ITS START on resume — so nodes must be safe to re-run
    (idempotent). This is why A (already checkpointed) does not run again, but B
    (which never completed) runs again from the top.

How we make B "fail once": a tiny external flag (a mutable holder) flips after
the first attempt. This simulates a transient failure — a network blip, a rate
limit, a pod restart — that succeeds on retry. No API key needed; this runs
entirely offline.

Run:
    python -m langgraph_grok.examples.e13_failure_resume
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


class State(TypedDict):
    value: int
    trail: list[str]   # which nodes have run (so we can SEE A doesn't re-run)


# A small mutable flag we can flip to control whether B fails. In a real system
# the "failure" would be an exception from a network/tool/db call.
class Flaky:
    def __init__(self) -> None:
        self.should_fail = True


FLAKY = Flaky()


def node_a(state: State) -> dict:
    log.info("NODE A | running (value=%s) — this should run ONCE only", state["value"])
    return {"value": state["value"] + 1, "trail": state["trail"] + ["A"]}


def node_b(state: State) -> dict:
    log.info("NODE B | running (value=%s)", state["value"])
    if FLAKY.should_fail:
        # Flip the flag so the RETRY (next invoke) will succeed, then raise.
        FLAKY.should_fail = False
        log.error("NODE B | simulating a transient failure -> raising RuntimeError")
        raise RuntimeError("Simulated transient failure in node B (will succeed on retry)")
    log.info("NODE B | succeeded this time")
    return {"value": state["value"] * 10, "trail": state["trail"] + ["B"]}


def node_c(state: State) -> dict:
    log.info("NODE C | running (value=%s)", state["value"])
    return {"value": state["value"] + 100, "trail": state["trail"] + ["C"]}


def build_graph(checkpointer):
    log.info("Building graph A -> B -> C WITH checkpointer (required for resume)")
    builder = StateGraph(State)
    builder.add_node("A", node_a)
    builder.add_node("B", node_b)
    builder.add_node("C", node_c)
    builder.add_edge(START, "A")
    builder.add_edge("A", "B")
    builder.add_edge("B", "C")
    builder.add_edge("C", END)
    compiled = builder.compile(checkpointer=checkpointer)
    log.info("Graph compiled (persistence enabled)")
    return compiled


def main() -> None:
    saver = MemorySaver()
    graph = build_graph(saver)
    print_graph(graph, "e13 failure & resume")

    cfg = {"configurable": {"thread_id": "resume-demo"}}

    # ---- Attempt 1: B fails. The run stops; A's result stays checkpointed. ----
    banner("ATTEMPT 1 — node B fails partway through")
    try:
        graph.invoke({"value": 5, "trail": []}, cfg)
    except RuntimeError as e:
        log.warning("Caught the failure at the top level: %s", e)

    # Inspect what survived. A succeeded, so the checkpoint sits ready to run B.
    snap = graph.get_state(cfg)
    log.info("After failure | saved value=%s trail=%s", snap.values["value"], snap.values["trail"])
    log.info("After failure | NEXT node to run on resume = %s", snap.next)
    print(f"\nState was checkpointed after A. trail so far = {snap.values['trail']}")
    print(f"Graph is paused with next = {snap.next}  (i.e. it will resume at B)")

    # ---- Attempt 2: resume the SAME thread. invoke(None,...) continues. ----
    banner("ATTEMPT 2 — resume the same thread (FLAKY now succeeds)")
    log.info("Resuming with graph.invoke(None, cfg) — picks up the pending work")
    result = graph.invoke(None, cfg)

    print(f"\nFinal value = {result['value']}")
    print(f"Execution trail = {result['trail']}")
    print(
        "\nNotice the trail is ['A', 'B', 'C'] — node A appears ONCE.\n"
        "A did NOT re-run on resume (its result was already checkpointed).\n"
        "B re-ran from its start (it never completed the first time) and then C ran.\n"
        "That is durable execution: resume from the failed super-step, not from the beginning."
    )

    # Sanity check we can assert in tests / smoke runs.
    assert result["trail"] == ["A", "B", "C"], result["trail"]
    assert result["value"] == (5 + 1) * 10 + 100  # A:+1 -> 6, B:*10 -> 60, C:+100 -> 160
    log.info("Verified: trail=['A','B','C'] and value=160 — A ran exactly once")


if __name__ == "__main__":
    main()
