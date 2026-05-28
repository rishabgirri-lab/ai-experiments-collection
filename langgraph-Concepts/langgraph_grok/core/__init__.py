"""langgraph_grok.core — shared building blocks used across examples.

This package holds the reusable pieces that real projects factor out of
individual graphs:

    state.py    -> common TypedDict state schemas + reducers
    tools.py    -> reusable @tool definitions (math, web search)
    helpers.py  -> small utilities (pretty-printing messages, mermaid dump)

The numbered examples in `langgraph_grok.examples` stay self-contained for
teaching, but they import from here where it avoids duplication, so you can see
both styles: inline (for learning) and factored-out (for production).
"""

from langgraph_grok.core.state import ChatState, AccumulatingState
from langgraph_grok.core.tools import add, multiply, web_search, DEFAULT_TOOLS
from langgraph_grok.core.helpers import print_messages, to_mermaid

__all__ = [
    "ChatState",
    "AccumulatingState",
    "add",
    "multiply",
    "web_search",
    "DEFAULT_TOOLS",
    "print_messages",
    "to_mermaid",
]
