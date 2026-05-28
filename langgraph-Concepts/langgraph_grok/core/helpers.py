"""Small utilities reused by examples: message pretty-printing and graph
visualization. Kept dependency-light on purpose.
"""

from __future__ import annotations

from typing import Iterable


def print_messages(messages: Iterable) -> None:
    """Pretty-print a list of LangChain messages, showing tool calls explicitly
    so the ReAct reasoning trace is visible.
    """
    for m in messages:
        kind = m.__class__.__name__
        tool_calls = getattr(m, "tool_calls", None)
        if tool_calls:
            names = [tc["name"] for tc in tool_calls]
            print(f"  [{kind}] tool_calls={names}")
        else:
            content = str(getattr(m, "content", ""))
            print(f"  [{kind}] {content[:200]}")


def to_mermaid(compiled_graph) -> str:
    """Return a Mermaid diagram string for a compiled graph.

    Paste the result into https://mermaid.live or any Markdown renderer to see
    the graph's nodes and edges.
    """
    return compiled_graph.get_graph().draw_mermaid()
