"""
LLM configuration (Grok / xAI).
===============================
CrewAI uses LiteLLM under the hood, so any OpenAI-compatible endpoint works.
Grok exposes one at https://api.x.ai/v1. We point CrewAI's LLM wrapper there.

Environment variables (see .env.example):
    GROK_API_KEY   -> your xAI key (required)
    GROK_MODEL     -> e.g. grok-2-latest, grok-beta (optional, has default)
    GROK_BASE_URL  -> defaults to https://api.x.ai/v1
"""

import os

from crewai import LLM

from src.crew_demo.logger import get_logger

log = get_logger("llm")


def get_grok_llm() -> LLM:
    """Build a CrewAI LLM object backed by Grok."""
    api_key = os.getenv("GROK_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROK_API_KEY is not set. Copy .env.example to .env and fill it in, "
            "or export GROK_API_KEY in your shell."
        )

    model = os.getenv("GROK_MODEL", "grok-2-latest")
    base_url = os.getenv("GROK_BASE_URL", "https://api.x.ai/v1")

    # The "openai/" prefix tells LiteLLM to treat this as an OpenAI-compatible
    # provider while using our custom base_url + key. This is the key trick
    # for using Grok with CrewAI.
    litellm_model = f"openai/{model}"

    log.info("Configuring Grok LLM | model=%s | base_url=%s", model, base_url)

    llm = LLM(
        model=litellm_model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
    )
    return llm
