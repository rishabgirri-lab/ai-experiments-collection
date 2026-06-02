"""
_shared.py
==========
A tiny helper that every example imports. It builds a Microsoft Agent Framework
chat client that talks to **Groq** (the fast inference provider) through Groq's
OpenAI-compatible Chat Completions endpoint.

Why OpenAIChatCompletionClient (and not OpenAIChatClient)?
---------------------------------------------------------
Agent Framework ships two OpenAI clients:
  * OpenAIChatClient            -> targets the OpenAI *Responses* API
  * OpenAIChatCompletionClient  -> targets the OpenAI *Chat Completions* API

Groq only implements the Chat Completions API, so we must use
`OpenAIChatCompletionClient` and point its `base_url` at Groq. The same trick
works for any OpenAI-compatible endpoint (Ollama, vLLM, LM Studio, OpenRouter…).

Interview soundbite:
  "Agent Framework is provider-agnostic. A ChatClient is just an adapter; point
   its base_url at any OpenAI-compatible server and every higher-level concept
   (agents, tools, sessions, orchestration, workflows) keeps working unchanged."
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from agent_framework.openai import OpenAIChatCompletionClient

# --- Auto-load the project's .env so you don't have to export anything --------
# A .env file is NOT read by Python automatically; something has to load it.
# We load the .env that sits at the project root (one level above examples/),
# and also any .env in the current directory, so `python examples/01_...py`
# works no matter where you run it from.
try:
    from dotenv import load_dotenv  # ships with agent-framework

    _PROJECT_ROOT = Path(__file__).resolve().parent.parent  # maf-mastery/
    load_dotenv(_PROJECT_ROOT / ".env")                     # maf-mastery/.env
    load_dotenv()                                           # ./.env if present
except Exception:
    # python-dotenv missing or unreadable .env — fall back to real env vars.
    pass
# -----------------------------------------------------------------------------

# Groq's OpenAI-compatible base URL. Do NOT add a trailing path beyond /openai/v1.
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# A current Groq *production* model that supports tool/function calling.
# Override with the GROQ_MODEL env var if Groq deprecates it (they rotate models).
# Good alternatives: "llama-3.1-8b-instant", "openai/gpt-oss-120b".
DEFAULT_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")


def get_api_key() -> str:
    key = os.environ.get("GROQ_API_KEY", "").strip()
    if not key:
        sys.exit(
            "\n[!] GROQ_API_KEY is not set.\n"
            "    1. Get a free key at https://console.groq.com/keys (starts with 'gsk_').\n"
            "    2. Copy .env.example to .env and paste your key, then:\n"
            "         export $(grep -v '^#' .env | xargs)   # macOS/Linux\n"
            "       or just:  export GROQ_API_KEY=gsk_...\n"
        )
    if not key.startswith("gsk_"):
        print(
            "[warn] Your key does not start with 'gsk_'. Groq keys start with 'gsk_'. "
            "(Note: xAI 'Grok' keys start with 'xai-' and will NOT work here.)"
        )
    return key


def build_chat_client(model: str | None = None) -> OpenAIChatCompletionClient:
    """Return a MAF chat client wired to Groq."""
    return OpenAIChatCompletionClient(
        model=model or DEFAULT_MODEL,
        api_key=get_api_key(),
        base_url=GROQ_BASE_URL,
    )


def banner(title: str) -> None:
    line = "=" * 70
    print(f"\n{line}\n  {title}\n{line}")
