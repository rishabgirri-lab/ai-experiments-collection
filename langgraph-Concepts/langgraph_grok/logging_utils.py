"""Project-wide logging + graph-printing helpers.

Every example calls `get_logger(__name__)` so output is consistent and tells you
exactly what is happening: which node ran, what it produced, which branch a
router chose, and so on. We also provide `print_graph()` which renders an
ASCII/Mermaid view of a compiled graph's topology.
"""

from __future__ import annotations

import logging
import os
import sys

_CONFIGURED = False


def configure_logging() -> None:
    """Configure root logging once. Level is controlled by LOG_LEVEL in .env
    (default INFO). Set LOG_LEVEL=DEBUG for very verbose output.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return

    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)-22s | %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )
    # Quiet down noisy third-party loggers so OUR logs stand out.
    for noisy in ("httpx", "httpcore", "groq", "urllib3", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for the given module name."""
    configure_logging()
    return logging.getLogger(name)


def banner(title: str) -> None:
    """Print a clear section banner to delimit examples / phases."""
    line = "=" * 72
    print(f"\n{line}\n{title}\n{line}")


def print_graph(compiled_graph, title: str = "GRAPH") -> None:
    """Print a compiled graph's structure two ways:

    1. An ASCII rendering of nodes + edges (always shown).
    2. The Mermaid source (paste into https://mermaid.live to view it).

    Both come straight from LangGraph's get_graph(), so they always reflect the
    real compiled topology.
    """
    g = compiled_graph.get_graph()

    print(f"\n----- {title}: nodes -----")
    for node in g.nodes:
        print(f"   • {node}")

    print(f"\n----- {title}: edges -----")
    for edge in g.edges:
        # Edge objects expose .source / .target; conditional edges add a label.
        label = f"  [{edge.data}]" if getattr(edge, "data", None) else ""
        conditional = "  (conditional)" if getattr(edge, "conditional", False) else ""
        print(f"   {edge.source} --> {edge.target}{label}{conditional}")

    print(f"\n----- {title}: ASCII diagram -----")
    try:
        # draw_ascii needs the optional 'grandalf' package; fall back gracefully.
        print(g.draw_ascii())
    except Exception as e:
        print(f"   (ASCII art unavailable: {e})")

    print(f"\n----- {title}: Mermaid (paste into https://mermaid.live) -----")
    print(g.draw_mermaid())
