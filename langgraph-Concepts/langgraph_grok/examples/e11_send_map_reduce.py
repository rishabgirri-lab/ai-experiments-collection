"""
11 — Dynamic map-reduce with the Send API
==========================================

When the number of parallel branches is unknown until runtime, a router returns
a LIST of Send objects -> dynamic fan-out. This version LOGS the map dispatch
and the reduce step, and PRINTS the graph.

Flow:
    START -> split -> [Send("summarize_one", item) per doc] (MAP) -> reduce -> END

Run:
    python -m langgraph_grok.examples.e11_send_map_reduce
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from langgraph_grok.config import get_llm
from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


class OverallState(TypedDict):
    documents: list[str]
    summaries: Annotated[list[str], operator.add]
    digest: str


class ItemState(TypedDict):
    document: str


def split(state: OverallState) -> dict:
    log.info("NODE split | %d documents to map over", len(state["documents"]))
    return {}


def map_documents(state: OverallState):
    log.info("ROUTER map_documents | dispatching %d parallel Send()s", len(state["documents"]))
    return [Send("summarize_one", {"document": doc}) for doc in state["documents"]]


def summarize_one(state: ItemState) -> dict:
    log.info("NODE summarize_one | doc=%r", state["document"][:50])
    resp = get_llm(model="fast").invoke("Summarize in one sentence:\n" + state["document"])
    return {"summaries": [resp.content]}


def reduce(state: OverallState) -> dict:
    log.info("NODE reduce | combining %d summaries", len(state["summaries"]))
    joined = "\n".join(f"- {s}" for s in state["summaries"])
    resp = get_llm().invoke("Combine these summaries into a single digest:\n" + joined)
    return {"digest": resp.content}


def build_graph():
    log.info("Building map-reduce graph with the Send API")
    builder = StateGraph(OverallState)
    builder.add_node("split", split)
    builder.add_node("summarize_one", summarize_one)
    builder.add_node("reduce", reduce)
    builder.add_edge(START, "split")
    builder.add_conditional_edges("split", map_documents, ["summarize_one"])
    builder.add_edge("summarize_one", "reduce")
    builder.add_edge("reduce", END)
    compiled = builder.compile()
    log.info("Graph compiled successfully")
    return compiled


def main() -> None:
    docs = [
        "The Apollo program landed twelve astronauts on the Moon between 1969 and 1972.",
        "Photosynthesis converts sunlight, water, and CO2 into glucose and oxygen.",
        "The TCP three-way handshake uses SYN, SYN-ACK, and ACK to open a connection.",
    ]
    graph = build_graph()
    print_graph(graph, "e11 map-reduce")

    banner("Mapping over documents in parallel, then reducing")
    result = graph.invoke({"documents": docs, "summaries": []})
    print("\nPer-document summaries:")
    for s in result["summaries"]:
        print(" -", s)
    print("\nCombined digest:\n", result["digest"])


if __name__ == "__main__":
    main()
