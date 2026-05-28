"""Reusable tools shared across examples.

A tool's docstring and type hints ARE its schema — the model decides whether to
call a tool based on this text, so keep descriptions clear and specific.
"""

from __future__ import annotations

from langchain_core.tools import tool


@tool
def add(a: float, b: float) -> float:
    """Add two numbers and return the sum."""
    return a + b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return the product."""
    return a * b


@tool
def web_search(query: str) -> str:
    """Search the web for current information. Use for facts you don't know.

    Falls back gracefully (no crash) if the network or the search package is
    unavailable, so graphs that bind this tool still run offline.
    """
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=3))
        if not hits:
            return "No results found."
        return "\n".join(f"- {h['title']}: {h['body']}" for h in hits)
    except Exception as e:  # network/deps unavailable -> degrade, don't crash
        return f"web_search unavailable ({e}). Answer from your own knowledge."


# A sensible default tool belt that examples can bind in one line.
DEFAULT_TOOLS = [add, multiply, web_search]
