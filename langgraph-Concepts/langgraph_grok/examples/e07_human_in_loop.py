"""
07 — Human-in-the-Loop with interrupt() and Command(resume=...)
===============================================================

Pause the graph for human approval/edit before an irreversible action, then
resume exactly where it left off. This version LOGS the pause and resume points
and PRINTS the graph.

Flow:
    START -> draft -> review[interrupt -> wait for human] -> act -> END

Run:
    python -m langgraph_grok.examples.e07_human_in_loop
"""

from __future__ import annotations

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command

from langgraph_grok.config import get_llm
from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


class State(TypedDict):
    request: str
    draft: str
    approved: bool
    sent: str


def draft_email(state: State) -> dict:
    log.info("NODE draft_email | drafting for request=%r", state["request"][:60])
    resp = get_llm().invoke(
        "Draft a SHORT professional email for this request. Body only.\n\n" + state["request"]
    )
    return {"draft": resp.content}


def human_review(state: State) -> dict:
    log.info("NODE human_review | PAUSING via interrupt() for human decision")
    decision = interrupt({
        "action": "Please review this draft email",
        "draft": state["draft"],
        "instructions": "Resume with 'approve', 'reject', or replacement text.",
    })
    # Execution continues HERE only after Command(resume=...) is supplied.
    log.info("NODE human_review | RESUMED with decision=%r", decision)
    if decision == "approve":
        return {"approved": True}
    if decision == "reject":
        return {"approved": False}
    return {"approved": True, "draft": decision}  # treat anything else as an edit


def act(state: State) -> dict:
    if state.get("approved"):
        log.info("NODE act | approved -> sending")
        return {"sent": f"EMAIL SENT:\n{state['draft']}"}
    log.info("NODE act | rejected -> cancelling")
    return {"sent": "Cancelled by human reviewer."}


def build_graph():
    log.info("Building HITL graph (requires a checkpointer)")
    builder = StateGraph(State)
    builder.add_node("draft", draft_email)
    builder.add_node("review", human_review)
    builder.add_node("act", act)
    builder.add_edge(START, "draft")
    builder.add_edge("draft", "review")
    builder.add_edge("review", "act")
    builder.add_edge("act", END)
    compiled = builder.compile(checkpointer=MemorySaver())
    log.info("Graph compiled (checkpointer attached)")
    return compiled


def main() -> None:
    graph = build_graph()
    print_graph(graph, "e07 human-in-the-loop")
    cfg = {"configurable": {"thread_id": "hitl-1"}}

    banner("First invoke: runs until interrupt(), then returns control")
    result = graph.invoke(
        {"request": "Ask my landlord to fix the leaking kitchen tap this week."}, cfg
    )
    payload = result["__interrupt__"][0].value
    print("=== GRAPH PAUSED — human input needed ===")
    print("Draft:\n", payload["draft"])

    human_decision = input("Enter 'approve', 'reject', or an edited draft to resume: ") 
    # banner("Human responds 'approve' -> resume from the same checkpoint")
    log.info("Resuming with Command(resume='human_decision')")
    final = graph.invoke(Command(resume=human_decision), cfg)
    print(final["sent"])


if __name__ == "__main__":
    main()
