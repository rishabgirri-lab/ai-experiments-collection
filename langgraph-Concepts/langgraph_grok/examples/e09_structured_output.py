"""
09 — Structured Output (typed, validated model results)
=======================================================

with_structured_output forces the model to return data matching a Pydantic
schema. This version LOGS the parsed fields and the routing decision, and
PRINTS the graph.

Flow:
    START -> extract(structured) -> route on sentiment/priority -> reply -> END

Run:
    python -m langgraph_grok.examples.e09_structured_output
"""

from __future__ import annotations

from typing import Literal, Optional, TypedDict

from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from langgraph_grok.config import get_llm
from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


class Ticket(BaseModel):
    summary: str = Field(description="One-sentence summary of the customer issue")
    sentiment: Literal["positive", "neutral", "negative"] = Field(
        description="Overall emotional tone of the message")
    priority: Literal["low", "medium", "high"] = Field(
        description="Urgency based on impact and tone")
    product: Optional[str] = Field(default=None, description="Product mentioned, if any")


class State(TypedDict):
    message: str
    ticket: Ticket
    reply: str


def extract(state: State) -> dict:
    log.info("NODE extract | forcing structured Ticket output")
    structured_llm = get_llm().with_structured_output(Ticket)
    ticket: Ticket = structured_llm.invoke(
        "Extract a structured support ticket from this customer message:\n\n" + state["message"]
    )
    log.info("NODE extract | sentiment=%s priority=%s product=%s",
             ticket.sentiment, ticket.priority, ticket.product)
    return {"ticket": ticket}


def route(state: State) -> Literal["urgent", "normal"]:
    t = state["ticket"]
    target = "urgent" if (t.priority == "high" or t.sentiment == "negative") else "normal"
    log.info("ROUTER route | priority=%s sentiment=%s -> %s", t.priority, t.sentiment, target)
    return target


def urgent_reply(state: State) -> dict:
    log.info("NODE urgent | escalating")
    return {"reply": f"[ESCALATED -> on-call] {state['ticket'].summary}"}


def normal_reply(state: State) -> dict:
    log.info("NODE normal | queueing")
    return {"reply": f"[Queued normally] {state['ticket'].summary}"}


def build_graph():
    log.info("Building graph: extract -> route -> {urgent, normal}")
    builder = StateGraph(State)
    builder.add_node("extract", extract)
    builder.add_node("urgent", urgent_reply)
    builder.add_node("normal", normal_reply)
    builder.add_edge(START, "extract")
    builder.add_conditional_edges("extract", route, {"urgent": "urgent", "normal": "normal"})
    builder.add_edge("urgent", END)
    builder.add_edge("normal", END)
    compiled = builder.compile()
    log.info("Graph compiled successfully")
    return compiled


def main() -> None:
    graph = build_graph()
    print_graph(graph, "e09 structured output")

    msg = ("Your app crashed and I lost two hours of work on the Pro plan export. "
           "This is the third time this week and I am furious.")
    banner(f"MESSAGE: {msg}")
    result = graph.invoke({"message": msg})
    t = result["ticket"]
    print("\nParsed Ticket (validated Pydantic object):")
    print(f"  summary  : {t.summary}")
    print(f"  sentiment: {t.sentiment}")
    print(f"  priority : {t.priority}")
    print(f"  product  : {t.product}")
    print("\nRouting decision ->", result["reply"])


if __name__ == "__main__":
    main()
