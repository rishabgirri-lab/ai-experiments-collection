r"""
05 — Tools & a hand-built ReAct loop (cyclic graph)
===================================================

The model decides whether to call a TOOL; if it does, we run the tool, feed the
result back, and loop until it answers without a tool call. This version LOGS
each turn (tool calls vs. final answer) and PRINTS the cyclic graph so you can
see the agent -> tools -> agent loop.

Flow:
    START -> agent -> (tools_condition?) -> tools -> agent (loop)
                                         \-> END

Run:
    python -m langgraph_grok.examples.e05_tools_react
"""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from langgraph_grok.config import get_llm
from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return the product."""
    log.info("TOOL multiply(%s, %s)", a, b)
    return a * b


@tool
def add(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    log.info("TOOL add(%s, %s)", a, b)
    return a + b


@tool
def web_search(query: str) -> str:
    """Search the web for current information. Use for facts you don't know."""
    log.info("TOOL web_search(%r)", query)
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=3))
        return "\n".join(f"- {h['title']}: {h['body']}" for h in hits) or "No results."
    except Exception as e:
        log.warning("web_search unavailable: %s", e)
        return f"web_search unavailable ({e}). Answer from your own knowledge."


TOOLS = [multiply, add, web_search]


class State(TypedDict):
    messages: Annotated[list, add_messages]


def agent(state: State) -> dict:
    log.info("NODE agent | thinking with %d messages in context", len(state["messages"]))
    llm = get_llm().bind_tools(TOOLS)
    ai = llm.invoke(state["messages"])
    if getattr(ai, "tool_calls", None):
        log.info("NODE agent | requested tools: %s", [tc["name"] for tc in ai.tool_calls])
    else:
        log.info("NODE agent | produced FINAL answer (no tool calls)")
    return {"messages": [ai]}


def build_graph():
    log.info("Building cyclic ReAct graph: agent <-> tools")
    builder = StateGraph(State)
    builder.add_node("agent", agent)
    builder.add_node("tools", ToolNode(TOOLS))
    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", tools_condition)  # -> tools or END
    builder.add_edge("tools", "agent")                       # the cycle
    compiled = builder.compile()
    log.info("Graph compiled successfully")
    return compiled


def main() -> None:
    graph = build_graph()
    print_graph(graph, "e05 ReAct loop")

    q = "What is 23 * 17, and then add 100 to that result?"
    banner(f"QUESTION: {q}")
    result = graph.invoke({"messages": [HumanMessage(q)]})

    print("\nConversation trace:")
    for m in result["messages"]:
        kind = m.__class__.__name__
        if getattr(m, "tool_calls", None):
            print(f"  [{kind}] tool_calls={[tc['name'] for tc in m.tool_calls]}")
        else:
            print(f"  [{kind}] {str(m.content)[:200]}")
    print("\nFinal answer:", result["messages"][-1].content)


if __name__ == "__main__":
    main()
