r"""
02 — Conditional Edges & Routing
================================

Conditional edges let a router function inspect the state and decide which node
runs next. This version LOGS the classification and the routing decision so you
can see the branch being chosen, and PRINTS the branching graph.

Flow:
                          /-> math    -\
    START -> classify --->  -> code    ---> summarize -> END
                          \-> general -/

Run:
    python -m langgraph_grok.examples.e02_conditional
"""

from __future__ import annotations

from typing import Literal, TypedDict

from langgraph.graph import StateGraph, START, END

from langgraph_grok.config import get_llm
from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


class State(TypedDict):
    question: str
    category: str
    answer: str


def classify(state: State) -> dict:
    log.info("NODE classify | question=%r", state["question"][:60])
    llm = get_llm(model="fast")  # cheap model is fine for classification
    resp = llm.invoke(
        "Classify the question into exactly one word: MATH, CODE, or GENERAL.\n"
        "Reply with ONLY that word.\n\n"
        f"Question: {state['question']}"
    )
    category = resp.content.strip().upper()
    if category not in {"MATH", "CODE", "GENERAL"}:
        log.warning("classify | unexpected label %r, defaulting to GENERAL", category)
        category = "GENERAL"
    log.info("NODE classify | category=%s", category)
    return {"category": category}


def route(state: State) -> Literal["math", "code", "general"]:
    target = {"MATH": "math", "CODE": "code", "GENERAL": "general"}[state["category"]]
    log.info("ROUTER route | category=%s -> next node=%s", state["category"], target)
    return target


def math_node(state: State) -> dict:
    log.info("NODE math | solving")
    resp = get_llm().invoke("You are a precise math tutor. Solve step by step:\n" + state["question"])
    return {"answer": resp.content}


def code_node(state: State) -> dict:
    log.info("NODE code | answering with code")
    resp = get_llm().invoke("You are a senior engineer. Code + brief explanation:\n" + state["question"])
    return {"answer": resp.content}


def general_node(state: State) -> dict:
    log.info("NODE general | answering")
    resp = get_llm().invoke(state["question"])
    return {"answer": resp.content}


def summarize(state: State) -> dict:
    log.info("NODE summarize | tagging answer with category=%s", state["category"])
    return {"answer": f"[{state['category']}] {state['answer']}"}


def build_graph():
    log.info("Building branching graph with a conditional edge after classify")
    builder = StateGraph(State)
    builder.add_node("classify", classify)
    builder.add_node("math", math_node)
    builder.add_node("code", code_node)
    builder.add_node("general", general_node)
    builder.add_node("summarize", summarize)
    builder.add_edge(START, "classify")
    builder.add_conditional_edges(
        "classify", route, {"math": "math", "code": "code", "general": "general"}
    )
    builder.add_edge("math", "summarize")
    builder.add_edge("code", "summarize")
    builder.add_edge("general", "summarize")
    builder.add_edge("summarize", END)
    compiled = builder.compile()
    log.info("Graph compiled successfully")
    return compiled


def main() -> None:
    graph = build_graph()
    print_graph(graph, "e02 router")

    for q in [
        "What is the derivative of x^2 * sin(x)?",
        "How do I reverse a linked list in Python?",
        "Why is the sky blue?",
    ]:
        banner(f"QUESTION: {q}")
        result = graph.invoke({"question": q})
        print("\nAnswer:", result["answer"][:400])


if __name__ == "__main__":
    main()
