"""
CrewAI Complete Demo Project
============================
Entry point that wires together Agents, Tasks, Tools, a Crew, and a Process.
Uses Groq (or any OpenAI-compatible LLM) as the backend.

Run examples:
  python main.py --mode sequential   --topic "AI in healthcare"
  python main.py --mode hierarchical --topic "AI in healthcare"
  python main.py --mode async        --topic "AI in healthcare"
  python main.py --mode all          --topic "AI in healthcare"   # run all three
"""

import argparse
import sys
import time

from dotenv import load_dotenv

# Load environment variables from a .env file if present (GROK_API_KEY, etc.)
load_dotenv()

from src.crew_demo.logger import get_logger
from src.crew_demo.crew import ResearchWritingCrew

log = get_logger("main")

MODES = ("sequential", "hierarchical", "async")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="CrewAI demo: research + writing crew. Test all 3 process modes."
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="sequential",
        choices=(*MODES, "all"),
        help=(
            "Process mode. 'sequential' = linear pipeline; 'hierarchical' = "
            "manager delegates; 'async' = two parallel research tasks via "
            "async_execution; 'all' = run all three back-to-back for comparison."
        ),
    )
    parser.add_argument(
        "--topic",
        type=str,
        default="The impact of AI agents on software engineering",
        help="The topic the crew will research and write about.",
    )
    parser.add_argument(
        "--audience",
        type=str,
        default="technical professionals",
        help="Target audience for the final article.",
    )
    return parser.parse_args()


def run_one(mode: str, topic: str, audience: str) -> dict:
    """Run a single mode and return a summary dict for comparison."""
    log.info("=" * 70)
    log.info("RUN | mode=%s", mode.upper())
    log.info("Topic:    %s", topic)
    log.info("Audience: %s", audience)
    log.info("=" * 70)

    start = time.time()
    crew = ResearchWritingCrew(mode=mode).build()

    log.info("Kicking off the crew. This calls the LLM for each task...")
    result = crew.kickoff(inputs={"topic": topic, "audience": audience})
    elapsed = time.time() - start

    log.info("Mode '%s' finished in %.1fs", mode, elapsed)
    log.info("-" * 70)
    log.info("FINAL OUTPUT (mode=%s)", mode)
    log.info("-" * 70)
    print("\n" + str(result) + "\n")

    token_usage = getattr(result, "token_usage", None)
    if token_usage:
        log.info("Token usage [%s]: %s", mode, token_usage)

    return {"mode": mode, "elapsed_s": round(elapsed, 1), "token_usage": token_usage}


def main() -> int:
    args = parse_args()
    modes = MODES if args.mode == "all" else (args.mode,)

    summaries = []
    try:
        for mode in modes:
            summaries.append(run_one(mode, args.topic, args.audience))

        # Comparison summary (only meaningful when running multiple modes)
        if len(summaries) > 1:
            log.info("=" * 70)
            log.info("COMPARISON SUMMARY")
            log.info("=" * 70)
            for s in summaries:
                log.info(
                    "  %-13s | %5.1fs | tokens=%s",
                    s["mode"], s["elapsed_s"], s["token_usage"],
                )
        return 0
    except Exception as exc:  # noqa: BLE001
        log.exception("Crew run failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
