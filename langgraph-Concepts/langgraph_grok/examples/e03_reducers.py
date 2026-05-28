"""
03 — Reducers, Annotated state, and MessagesState
==================================================

A REDUCER tells LangGraph how to COMBINE the old value of a state key with a
node's update (instead of overwriting). This version LOGS each node and the
running state so you can SEE the list accumulate vs. the scalar overwrite.

Run:
    python -m langgraph_grok.examples.e03_reducers
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langgraph_grok.config import get_llm
from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


# --- Part A: a custom reducer with operator.add ----------------------------
class CounterState(TypedDict):
    log: Annotated[list[str], operator.add]  # CONCATENATED across nodes
    count: int                               # OVERWRITTEN (last write wins)


def step_one(state: CounterState) -> dict:
    log.info("NODE step_one | before: count=%s log=%s", state.get("count", 0), state.get("log", []))
    return {"log": ["step_one ran"], "count": state.get("count", 0) + 1}


def step_two(state: CounterState) -> dict:
    log.info("NODE step_two | before: count=%s log=%s", state["count"], state["log"])
    return {"log": ["step_two ran"], "count": state["count"] + 1}


def demo_reducer() -> None:
    builder = StateGraph(CounterState)
    builder.add_node("one", step_one)
    builder.add_node("two", step_two)
    builder.add_edge(START, "one")
    builder.add_edge("one", "two")
    builder.add_edge("two", END)
    graph = builder.compile()
    print_graph(graph, "e03 reducer demo")

    result = graph.invoke({"log": [], "count": 0})
    log.info("RESULT | log accumulated via operator.add = %s", result["log"])
    log.info("RESULT | count overwritten each time = %s", result["count"])


# --- Part B: MessagesState + add_messages ----------------------------------
class ChatState(TypedDict):
    messages: Annotated[list, add_messages]


def chat_node(state: ChatState) -> dict:
    log.info("NODE chat | history has %d messages", len(state["messages"]))
    ai = get_llm().invoke(state["messages"])
    log.info("NODE chat | appending 1 AI message (add_messages keeps history)")
    return {"messages": [ai]}


def demo_messages() -> None:
    builder = StateGraph(ChatState)
    builder.add_node("chat", chat_node)
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)
    graph = builder.compile()

    state = {"messages": [HumanMessage("Name a primary color.")]}
    state = graph.invoke(state)
    state["messages"].append(HumanMessage("Now name its complement."))
    state = graph.invoke(state)

    for m in state["messages"]:
        role = "USER" if isinstance(m, HumanMessage) else "AI"
        print(f"{role}: {m.content}")


def main() -> None:
    banner("Part A: operator.add reducer (list accumulates, count overwrites)")
    demo_reducer()
    banner("Part B: add_messages reducer (chat memory accumulates)")
    demo_messages()


if __name__ == "__main__":
    main()
