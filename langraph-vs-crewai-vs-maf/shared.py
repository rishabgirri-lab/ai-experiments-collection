"""
shared.py
=========
Common pieces used by all three pipeline examples so the ONLY thing that
differs between the files is the framework, not the task or the model call.

Every example solves the SAME problem:

    research a topic  ->  write a short article  ->  review it

PROVIDER AUTO-DETECTION (in priority order):
  1. GROQ_API_KEY   -> Groq (OpenAI-compatible), model llama-3.3-70b-versatile
  2. OPENAI_API_KEY -> OpenAI, model gpt-4o-mini
  3. neither        -> deterministic SIMULATED text (zero setup, zero cost)

Groq runs open models only (Llama / GPT-OSS / Qwen / ...), so the default
model differs by provider. Override either with:  export OAI_MODEL=...
Override the topic with:  export TOPIC="your topic here"
"""

from __future__ import annotations

import os
import textwrap

GROQ_KEY = os.getenv("GROQ_API_KEY")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# Is the openai SDK importable? (used as the OpenAI-compatible client for both)
try:
    import openai  # noqa: F401

    _OPENAI_SDK = True
except Exception:
    _OPENAI_SDK = False

if GROQ_KEY:
    PROVIDER = "groq"
    BASE_URL = "https://api.groq.com/openai/v1"
    API_KEY = GROQ_KEY
    MODEL = os.getenv("OAI_MODEL", "llama-3.3-70b-versatile")
    CREWAI_LLM = f"groq/{MODEL}"  # CrewAI/LiteLLM needs the groq/ prefix
elif OPENAI_KEY:
    PROVIDER = "openai"
    BASE_URL = None  # openai SDK uses its default endpoint
    API_KEY = OPENAI_KEY
    MODEL = os.getenv("OAI_MODEL", "gpt-4o-mini")
    CREWAI_LLM = MODEL
else:
    PROVIDER = None
    BASE_URL = None
    API_KEY = None
    MODEL = os.getenv("OAI_MODEL", "(simulated)")
    CREWAI_LLM = MODEL

HAS_LLM = bool(PROVIDER) and _OPENAI_SDK
MODE = f"REAL ({PROVIDER})" if HAS_LLM else "SIMULATED (no API key)"

TOPIC = os.getenv("TOPIC", "the benefits and risks of multi-agent AI systems for startups")


# --------------------------------------------------------------------------- #
# The one LLM entry point every framework example funnels through.
# --------------------------------------------------------------------------- #
def llm_complete(role: str, prompt: str) -> str:
    """Return text from `role` ("researcher" | "writer" | "reviewer")."""
    if HAS_LLM:
        return _real_complete(role, prompt)
    return _mock_complete(role, prompt)


_SYSTEM = {
    "researcher": "You are a sharp research analyst. Produce 4-6 terse, factual bullet points. No preamble.",
    "writer": "You are a clear technical writer. Write a tight ~150 word article. No headings, no fluff.",
    "reviewer": (
        "You are a strict editor. Reply with exactly one line: either "
        "'APPROVE' if the article is clear and accurate, or "
        "'REVISE: <one concrete instruction>' if it needs work."
    ),
}


def _real_complete(role: str, prompt: str) -> str:
    from openai import OpenAI

    # Same client for OpenAI and Groq; only base_url/api_key differ.
    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM[role]},
            {"role": "user", "content": prompt},
        ],
        temperature=0.4 if role != "writer" else 0.6,
    )
    return resp.choices[0].message.content.strip()


def _mock_complete(role: str, prompt: str) -> str:
    """Deterministic stand-in so the repo runs with no API key.

    The reviewer asks for one revision and then approves, so the LangGraph
    loop demonstrates a real cycle but still terminates.
    """
    topic = TOPIC
    if role == "researcher":
        return textwrap.dedent(
            f"""\
            - Multi-agent setups split a job across specialist agents (planner, worker, checker).
            - Upside for startups: faster iteration on complex tasks, clearer separation of concerns.
            - Risk: cost and latency multiply with every extra agent and tool call.
            - Risk: coordination failures (loops, dropped context) when roles are vague.
            - Most value shows up when tasks are genuinely multi-step, not for simple Q&A.
            (simulated research on: {topic})"""
        )
    if role == "writer":
        revise_hint = "REVISE" in prompt.upper()
        extra = (
            " This revision adds a concrete example: a 3-person startup using a "
            "research+draft+review crew to ship weekly briefs."
            if revise_hint
            else ""
        )
        return (
            f"Multi-agent AI systems let a startup break a hard task into roles—one agent "
            f"researches, another drafts, a third checks the work. The payoff is speed and "
            f"clarity on genuinely multi-step jobs. The catch is that every extra agent adds "
            f"cost, latency, and a new way for the system to get confused, so small teams "
            f"should reach for multiple agents only when a single well-prompted model "
            f"actually falls short.{extra} (simulated draft on: {topic})"
        )
    if role == "reviewer":
        if "revision adds a concrete example" in prompt:
            return "APPROVE"
        return "REVISE: add one concrete example of a small team using these agents."
    return "(no content)"


# --------------------------------------------------------------------------- #
# Tiny presentation helpers shared by the runners.
# --------------------------------------------------------------------------- #
def banner(title: str) -> None:
    line = "=" * 70
    print(f"\n{line}\n{title}\n{line}")


def section(title: str) -> None:
    print(f"\n--- {title} ---")
