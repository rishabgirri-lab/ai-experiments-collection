"""
langgraph_pipeline.py
=====================
LangGraph's mental model: a STATE MACHINE / graph.

You define a shared State (a TypedDict), write nodes that read and update it,
and wire them with edges. The thing LangGraph does that the other two don't
do naturally is CONDITIONAL EDGES and CYCLES: a node can decide where to go
next, including looping back. That's exactly what we use below — the reviewer
can send the draft back to the writer to be revised.

WHEN LANGGRAPH SHINES
---------------------
* The flow has branching, loops, retries, or "it depends" routing.
* You want explicit, deterministic, debuggable control over every transition.
* You need durable state, checkpointing, or human-in-the-loop pauses.
* You're already in the LangChain ecosystem.

WHERE IT FIGHTS YOU
-------------------
* Simple linear "team does these 3 steps" jobs feel verbose — you're hand-
  building a graph for something a Crew expresses in a few lines.
* More concepts to learn up front (state, reducers, nodes, edges, compile).

This file runs with NO API key (mock) using only:  pip install langgraph
Add OPENAI_API_KEY for a real run.
"""

from __future__ import annotations

from typing import TypedDict

from shared import TOPIC, banner, llm_complete

MAX_REVISIONS = 2


class State(TypedDict):
    topic: str
    research: str
    draft: str
    verdict: str
    revisions: int
    final: str


def research_node(state: State) -> dict:
    return {"research": llm_complete("researcher", f"Research: {state['topic']}")}


def write_node(state: State) -> dict:
    prompt = f"Write a ~150 word article from this research:\n{state['research']}"
    if state.get("verdict", "").startswith("REVISE"):
        # Feed the editor's instruction back in — this only happens on a loop.
        prompt += f"\n\nEditor asked you to {state['verdict']}"
    return {"draft": llm_complete("writer", prompt), "revisions": state.get("revisions", 0) + 1}


def review_node(state: State) -> dict:
    return {"verdict": llm_complete("reviewer", f"Review this article:\n{state['draft']}")}


def route_after_review(state: State) -> str:
    """The conditional edge: approve/finish, or loop back to the writer."""
    approved = state["verdict"].strip().upper().startswith("APPROVE")
    if approved or state["revisions"] >= MAX_REVISIONS:
        return "finish"
    return "revise"


def finish_node(state: State) -> dict:
    return {"final": state["draft"]}


def build_graph():
    from langgraph.graph import StateGraph, START, END

    g = StateGraph(State)
    g.add_node("research", research_node)
    g.add_node("write", write_node)
    g.add_node("review", review_node)
    g.add_node("finish", finish_node)

    g.add_edge(START, "research")
    g.add_edge("research", "write")
    g.add_edge("write", "review")
    # The differentiator: branch on the review result, possibly looping back.
    g.add_conditional_edges("review", route_after_review, {"revise": "write", "finish": "finish"})
    g.add_edge("finish", END)
    return g.compile()


def run(topic: str = TOPIC, verbose: bool = False) -> str:
    try:
        graph = build_graph()
    except Exception:
        return _simulate(topic)

    result = graph.invoke({"topic": topic, "revisions": 0})
    if verbose:
        print(f"[langgraph] revisions taken: {result['revisions']}, "
              f"final verdict: {result.get('verdict')}")
    return result["final"]


def _simulate(topic: str) -> str:
    """If langgraph isn't installed, run the same graph logic by hand."""
    print("[langgraph] SIMULATION (langgraph not installed) — pip install langgraph for the real run.")
    state: State = {"topic": topic, "research": "", "draft": "", "verdict": "",
                    "revisions": 0, "final": ""}
    state.update(research_node(state))
    while True:
        state.update(write_node(state))
        state.update(review_node(state))
        if route_after_review(state) == "finish":
            break
    state.update(finish_node(state))
    print(f"[langgraph] revisions taken: {state['revisions']}, final verdict: {state['verdict']}")
    return state["final"]


if __name__ == "__main__":
    banner("LangGraph — stateful graph with a conditional revise loop")
    print(run(verbose=True))
