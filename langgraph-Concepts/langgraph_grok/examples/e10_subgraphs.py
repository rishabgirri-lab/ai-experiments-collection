"""
10 — Subgraphs & Composition
============================

A compiled graph can be used AS A NODE inside a parent graph. This version LOGS
each subgraph invocation and PRINTS all three graphs (research, writing, parent)
so you can see the composition.

Run:
    python -m langgraph_grok.examples.e10_subgraphs
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph, START, END

from langgraph_grok.config import get_llm
from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


# ---- Subgraph 1: RESEARCH -------------------------------------------------
class ResearchState(TypedDict):
    topic: str
    findings: str


def gather(state: ResearchState) -> dict:
    log.info("SUBGRAPH research / NODE gather | topic=%r", state["topic"])
    resp = get_llm().invoke(f"List 3 key facts about: {state['topic']}")
    return {"findings": resp.content}


def build_research_subgraph():
    b = StateGraph(ResearchState)
    b.add_node("gather", gather)
    b.add_edge(START, "gather")
    b.add_edge("gather", END)
    return b.compile()


# ---- Subgraph 2: WRITING --------------------------------------------------
class WritingState(TypedDict):
    findings: str
    article: str


def write(state: WritingState) -> dict:
    log.info("SUBGRAPH writing / NODE write | composing from findings")
    resp = get_llm().invoke("Write a tight 100-word paragraph using these facts:\n" + state["findings"])
    return {"article": resp.content}


def build_writing_subgraph():
    b = StateGraph(WritingState)
    b.add_node("write", write)
    b.add_edge(START, "write")
    b.add_edge("write", END)
    return b.compile()


# ---- Parent graph ---------------------------------------------------------
class ParentState(TypedDict):
    topic: str
    findings: str
    article: str


def build_parent():
    research = build_research_subgraph()
    writing = build_writing_subgraph()

    def run_research(state: ParentState) -> dict:
        log.info("PARENT / NODE research | delegating to research subgraph")
        out = research.invoke({"topic": state["topic"]})
        return {"findings": out["findings"]}

    def run_writing(state: ParentState) -> dict:
        log.info("PARENT / NODE writing | delegating to writing subgraph")
        out = writing.invoke({"findings": state["findings"]})
        return {"article": out["article"]}

    b = StateGraph(ParentState)
    b.add_node("research", run_research)
    b.add_node("writing", run_writing)
    b.add_edge(START, "research")
    b.add_edge("research", "writing")
    b.add_edge("writing", END)
    log.info("Parent graph composed from 2 subgraphs")
    return b.compile(), research, writing


def main() -> None:
    parent, research, writing = build_parent()
    print_graph(research, "e10 research subgraph")
    print_graph(writing, "e10 writing subgraph")
    print_graph(parent, "e10 PARENT graph")

    banner("Running composed pipeline")
    result = parent.invoke({"topic": "the Roman aqueducts"})
    print("\nFindings:\n", result["findings"])
    print("\nArticle:\n", result["article"])


if __name__ == "__main__":
    main()
