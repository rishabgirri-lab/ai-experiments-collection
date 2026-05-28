"""
12 — Prebuilt agent, streaming modes & visualization
=====================================================

A) create_react_agent — the one-line prebuilt agent loop.
B) Streaming modes — updates / values / messages.
C) Visualization — print_graph() shows ASCII + Mermaid.

This version LOGS the streaming steps and PRINTS the prebuilt agent's graph.

Run:
    python -m langgraph_grok.examples.e12_prebuilt_streaming
"""

from __future__ import annotations

from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent

from langgraph_grok.config import get_llm
from langgraph_grok.logging_utils import get_logger, banner, print_graph

log = get_logger(__name__)


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city (mock data for the demo)."""
    log.info("TOOL get_weather(%r)", city)
    fake = {"paris": "18C, light rain", "tokyo": "26C, clear", "delhi": "39C, hazy"}
    return fake.get(city.lower(), "Weather data unavailable for that city.")


@tool
def word_count(text: str) -> int:
    """Count the number of words in a piece of text."""
    log.info("TOOL word_count(len=%d)", len(text))
    return len(text.split())


def build_agent():
    log.info("Building prebuilt agent via create_react_agent()")
    agent = create_react_agent(get_llm(), tools=[get_weather, word_count])
    log.info("Prebuilt agent ready")
    return agent


def main() -> None:
    agent = build_agent()
    print_graph(agent, "e12 prebuilt ReAct agent")

    banner("stream_mode='updates' (per-node deltas)")
    inp = {"messages": [HumanMessage("What's the weather in Tokyo right now?")]}
    for chunk in agent.stream(inp, {"configurable": {"thread_id": "s1"}}, stream_mode="updates"):
        for node, delta in chunk.items():
            last = delta["messages"][-1]
            tag = "tool_call" if getattr(last, "tool_calls", None) else "text"
            log.info("STREAM updates | node=%s kind=%s", node, tag)
            print(f"  [{node}/{tag}] {str(last.content)[:120]}")

    banner("stream_mode='messages' (token streaming)")
    inp2 = {"messages": [HumanMessage("In one sentence, why is Tokyo a fun city?")]}
    for token, meta in agent.stream(inp2, {"configurable": {"thread_id": "s2"}}, stream_mode="messages"):
        if token.content:
            print(token.content, end="", flush=True)
    print()


if __name__ == "__main__":
    main()
