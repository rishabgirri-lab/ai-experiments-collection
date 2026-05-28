"""Run every example end-to-end. Useful as a smoke test of your setup.

Usage:
    python run_all.py            # run all
    python run_all.py 5 9        # run only examples 05 and 09

Logging is configured up front so you see node-by-node logs for every example.
Set LOG_LEVEL=DEBUG in your .env for even more detail.
"""

from __future__ import annotations

import importlib
import sys
import traceback

from langgraph_grok.logging_utils import configure_logging, banner, get_logger

EXAMPLES = [
    ("01", "e01_basics", "StateGraph fundamentals"),
    ("02", "e02_conditional", "Conditional edges & routing"),
    ("03", "e03_reducers", "Reducers & MessagesState"),
    ("04", "e04_parallel", "Parallel fan-out / fan-in"),
    ("05", "e05_tools_react", "Tools & ReAct loop"),
    ("06", "e06_checkpointing", "Checkpointing, threads, memory"),
    ("07", "e07_human_in_loop", "Human-in-the-loop"),
    ("08", "e08_time_travel", "Time travel & forking"),
    ("09", "e09_structured_output", "Structured output (Pydantic)"),
    ("10", "e10_subgraphs", "Subgraphs & composition"),
    ("11", "e11_send_map_reduce", "Send API dynamic map-reduce"),
    ("12", "e12_prebuilt_streaming", "Prebuilt agent, streaming, viz"),
    ("13", "e13_failure_resume", "Failure & durable resume from failed node"),
]


def main() -> None:
    configure_logging()
    log = get_logger("run_all")

    wanted = {w.zfill(2) for w in sys.argv[1:]}

    for num, module, title in EXAMPLES:
        if wanted and num not in wanted:
            continue
        banner(f"EXAMPLE {num}: {title}")
        try:
            mod = importlib.import_module(f"langgraph_grok.examples.{module}")
            mod.main()
        except Exception:
            log.error("Example %s raised an error:", num)
            traceback.print_exc()


if __name__ == "__main__":
    main()
