"""
06 — Checkpointing, Persistence, Threads & Memory
=================================================

A CHECKPOINTER snapshots state after every super-step, unlocking memory,
durable resume, human-in-the-loop, and time travel. This version LOGS each
thread's activity and PRINTS the graph, plus inspects a saved checkpoint.

Run:
    python -m langgraph_grok.examples.e06_checkpointing
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langgraph_grok.config import get_llm
from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


class State(TypedDict):
    messages: Annotated[list, add_messages]


def chat(state: State) -> dict:
    log.info("NODE chat | %d messages in thread history", len(state["messages"]))
    return {"messages": [get_llm().invoke(state["messages"])]}


def build_graph(checkpointer):
    log.info("Building graph WITH checkpointer=%s", type(checkpointer).__name__)
    builder = StateGraph(State)
    builder.add_node("chat", chat)
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)
    compiled = builder.compile(checkpointer=checkpointer)
    log.info("Graph compiled (persistence enabled)")
    return compiled


def main() -> None:
    # Swap MemorySaver for SqliteSaver to persist across process restarts:
    #   from langgraph.checkpoint.sqlite import SqliteSaver
    #   with SqliteSaver.from_conn_string("checkpoints.db") as saver: ...
    graph = build_graph(MemorySaver())
    print_graph(graph, "e06 chat with memory")

    alice = {"configurable": {"thread_id": "alice"}}
    bob = {"configurable": {"thread_id": "bob"}}

    banner("Thread 'alice' — teach a fact, then recall it")
    log.info("Invoking thread=alice (telling it her name)")
    graph.invoke({"messages": [HumanMessage("My name is Alice. Remember it.")]}, alice)
    log.info("Invoking thread=alice (asking her name back)")
    r = graph.invoke({"messages": [HumanMessage("What is my name?")]}, alice)
    print("alice ->", r["messages"][-1].content)

    banner("Thread 'bob' — separate memory, never saw Alice")
    log.info("Invoking thread=bob (asking his name)")
    r = graph.invoke({"messages": [HumanMessage("What is my name?")]}, bob)
    print("bob ->", r["messages"][-1].content)

    banner("Inspecting alice's checkpoint with get_state()")
    snap = graph.get_state(alice)
    log.info("alice thread stored messages=%d next=%s", len(snap.values["messages"]), snap.next or "(END)")


if __name__ == "__main__":
    main()
