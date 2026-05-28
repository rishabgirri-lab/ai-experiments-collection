"""
08 — Time Travel: state history, replay, and forking
=====================================================

Every super-step is checkpointed, so you can inspect history, rewind, and FORK
an alternate timeline. This version (no LLM calls -> runs offline) LOGS each
step, PRINTS the graph, and shows the original vs forked timelines.

Run:
    python -m langgraph_grok.examples.e08_time_travel
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


class State(TypedDict):
    value: int
    note: str


def add_ten(state: State) -> dict:
    log.info("NODE add_ten | %s + 10", state["value"])
    return {"value": state["value"] + 10, "note": "added 10"}


def double(state: State) -> dict:
    log.info("NODE double | %s * 2", state["value"])
    return {"value": state["value"] * 2, "note": "doubled"}


def square(state: State) -> dict:
    log.info("NODE square | %s ** 2", state["value"])
    return {"value": state["value"] ** 2, "note": "squared"}


def build_graph():
    log.info("Building graph: add_ten -> double -> square (with checkpointer)")
    builder = StateGraph(State)
    builder.add_node("add_ten", add_ten)
    builder.add_node("double", double)
    builder.add_node("square", square)
    builder.add_edge(START, "add_ten")
    builder.add_edge("add_ten", "double")
    builder.add_edge("double", "square")
    builder.add_edge("square", END)
    compiled = builder.compile(checkpointer=MemorySaver())
    log.info("Graph compiled (persistence enabled)")
    return compiled


def main() -> None:
    graph = build_graph()
    print_graph(graph, "e08 time travel")
    cfg = {"configurable": {"thread_id": "tt-1"}}

    banner("Original run: 5 -> +10 -> x2 -> ^2")
    final = graph.invoke({"value": 5, "note": "start"}, cfg)
    log.info("Original final value=%s", final["value"])  # 900

    banner("Full checkpoint history (newest first)")
    history = list(graph.get_state_history(cfg))
    for snap in history:
        nxt = snap.next or ("END",)
        value = snap.values.get("value", "—")
        note = snap.values.get("note", "—")
        log.info("checkpoint value=%-6s note=%-10s next=%s", value, note, nxt)

    banner("Fork the timeline from BEFORE 'double' ran")
    target = next(s for s in history if s.next == ("double",))
    log.info("Forking at checkpoint where value=%s", target.values["value"])
    forked_cfg = graph.update_state(target.config, {"value": 100})
    forked_final = graph.invoke(None, forked_cfg)  # invoke(None,...) = resume
    log.info("Forked final value=%s (100 -> x2 -> ^2)", forked_final["value"])  # 40000
    print("\nOriginal:", final["value"], "| Forked:", forked_final["value"])
    print("Both timelines coexist in history; the original is untouched.")


if __name__ == "__main__":
    main()
