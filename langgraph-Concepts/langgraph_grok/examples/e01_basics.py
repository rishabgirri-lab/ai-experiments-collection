"""
01 — StateGraph fundamentals: State, Nodes, Edges, START, END
=============================================================

Mental model:
    A graph is a set of NODES (functions) that read from and write to a shared
    STATE object, connected by EDGES that decide what runs next.

This version LOGS every node as it runs and PRINTS the compiled graph so you can
see the topology and the live execution side by side.

Run:
    python -m langgraph_grok.examples.e01_basics
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from langgraph_grok.config import get_llm
from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


class State(TypedDict):
    topic: str
    joke: str
    critique: str
    final: str


def write_joke(state: State) -> dict:
    log.info("NODE write_joke | topic=%r", state["topic"])
    llm = get_llm()
    resp = llm.invoke(f"Write a short, clever one-line joke about: {state['topic']}")
    log.info("NODE write_joke | produced joke (%d chars)", len(resp.content))
    return {"joke": resp.content}


def critique_joke(state: State) -> dict:
    log.info("NODE critique_joke | critiquing the joke")
    llm = get_llm()
    resp = llm.invoke(
        "You are a tough comedy editor. In ONE sentence, critique this joke:\n\n"
        f"{state['joke']}"
    )
    log.info("NODE critique_joke | critique=%r", resp.content[:80])
    return {"critique": resp.content}


def improve_joke(state: State) -> dict:
    log.info("NODE improve_joke | rewriting to address critique")
    llm = get_llm()
    resp = llm.invoke(
        "Rewrite the joke to fix the critique. Return ONLY the improved joke.\n\n"
        f"Joke: {state['joke']}\nCritique: {state['critique']}"
    )
    log.info("NODE improve_joke | done")
    return {"final": resp.content}


def build_graph():
    log.info("Building graph: write -> critique -> improve")
    builder = StateGraph(State)
    builder.add_node("write", write_joke)
    builder.add_node("critique", critique_joke)
    builder.add_node("improve", improve_joke)
    builder.add_edge(START, "write")
    builder.add_edge("write", "critique")
    builder.add_edge("critique", "improve")
    builder.add_edge("improve", END)
    compiled = builder.compile()
    log.info("Graph compiled successfully")
    return compiled


def main() -> None:
    graph = build_graph()
    print_graph(graph, "e01 pipeline")

    banner(".stream(): watch each node fire")
    for step in graph.stream({"topic": "coding"}):
        for node_name, update in step.items():
            log.info("STREAM step | node=%s keys=%s", node_name, list(update))

    banner(".invoke(): final state")
    result = graph.invoke({"topic": "coding"})
    print("\nFinal joke:", result["final"])


if __name__ == "__main__":
    main()
