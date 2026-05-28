r"""
04 — Parallel execution: fan-out / fan-in
=========================================

Nodes reachable at the same time run IN PARALLEL within one super-step. When
they write the same key, that key NEEDS a reducer. This version LOGS each
parallel branch and the merged result, and PRINTS the diamond-shaped graph.

Flow:
                  /-> optimist  -\
    START -> seed --> realist   ---> synthesize -> END
                  \-> pessimist -/

Run:
    python -m langgraph_grok.examples.e04_parallel
"""

from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from langgraph.graph import StateGraph, START, END

from langgraph_grok.config import get_llm
from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


class State(TypedDict):
    topic: str
    opinions: Annotated[list[str], operator.add]  # 3 parallel writers -> reducer
    synthesis: str


def seed(state: State) -> dict:
    log.info("NODE seed | initializing; fan-out to 3 personas next")
    return {"opinions": []}


def _opinion(persona: str, topic: str) -> str:
    log.info("NODE %s | generating opinion (runs in parallel)", persona)
    resp = get_llm().invoke(f"You are an extreme {persona}. In 2 sentences, give your take on: {topic}")
    return f"{persona}: {resp.content}"


def optimist(state: State) -> dict:
    return {"opinions": [_opinion("optimist", state["topic"])]}


def realist(state: State) -> dict:
    return {"opinions": [_opinion("realist", state["topic"])]}


def pessimist(state: State) -> dict:
    return {"opinions": [_opinion("pessimist", state["topic"])]}


def synthesize(state: State) -> dict:
    log.info("NODE synthesize | fan-in complete, merged %d opinions", len(state["opinions"]))
    joined = "\n".join(state["opinions"])
    resp = get_llm().invoke("Synthesize these three takes into one balanced paragraph:\n\n" + joined)
    return {"synthesis": resp.content}


def build_graph():
    log.info("Building diamond graph: seed -> {optimist, realist, pessimist} -> synthesize")
    builder = StateGraph(State)
    for name, fn in [("seed", seed), ("optimist", optimist),
                     ("realist", realist), ("pessimist", pessimist),
                     ("synthesize", synthesize)]:
        builder.add_node(name, fn)
    builder.add_edge(START, "seed")
    for p in ("optimist", "realist", "pessimist"):
        builder.add_edge("seed", p)       # fan-out
        builder.add_edge(p, "synthesize")  # fan-in
    builder.add_edge("synthesize", END)
    compiled = builder.compile()
    log.info("Graph compiled successfully")
    return compiled


def main() -> None:
    graph = build_graph()
    print_graph(graph, "e04 parallel")

    banner("Running 3 personas in parallel, then synthesizing")
    result = graph.invoke({"topic": "remote work for software teams", "opinions": []})
    print("\nCollected opinions:")
    for o in result["opinions"]:
        print(" -", o)
    print("\nSynthesis:\n", result["synthesis"])


if __name__ == "__main__":
    main()
