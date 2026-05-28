"""Central configuration + the shared Groq chat model.

Every example imports `get_llm()` from here, so there is exactly ONE place that
knows about the Groq API key. This mirrors a real codebase: model construction
lives behind a factory, not scattered across nodes.

NOTE on naming: "Groq" (this project, console.groq.com, keys start with `gsk_`)
is a fast-inference company running open models like Llama. It is NOT the same
as "Grok" (xAI's model, keys start with `xai-`). Confusing, but different.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv
from langchain_groq import ChatGroq

from langgraph_grok.logging_utils import get_logger

# Load variables from a local .env file if present. In production you'd rely on
# real environment variables / a secrets manager instead.
load_dotenv()

log = get_logger(__name__)


@dataclass(frozen=True)
class Settings:
    """Typed view over the environment. Frozen so it can't be mutated by accident."""

    groq_api_key: str
    model: str
    fast_model: str
    temperature: float

    @staticmethod
    def from_env() -> "Settings":
        key = os.getenv("GROQ_API_KEY", "").strip()
        if not key or key == "gsk-your-key-here":
            raise RuntimeError(
                "GROQ_API_KEY is not set. Copy .env.example to .env and add your "
                "key, or export GROQ_API_KEY in your shell. Get one at "
                "https://console.groq.com"
            )
        if not key.startswith("gsk"):
            # Not fatal (formats can change), but warn loudly — this is the most
            # common setup mistake (pasting an xAI 'xai-' key here).
            log.warning(
                "GROQ_API_KEY does not start with 'gsk' (got '%s...'). Groq keys "
                "usually start with 'gsk_'. If this is an xAI/Grok 'xai-' key it "
                "will NOT work here — those need the langchain-xai package.",
                key[:4],
            )
        return Settings(
            groq_api_key=key,
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip(),
            fast_model=os.getenv("GROQ_FAST_MODEL", "llama-3.1-8b-instant").strip(),
            temperature=float(os.getenv("GROQ_TEMPERATURE", "0")),
        )


settings: Settings | None = None  # populated lazily by get_llm


@lru_cache(maxsize=8)
def get_llm(model: str | None = None, temperature: float | None = None) -> ChatGroq:
    """Return a (cached) Groq chat model.

    ChatGroq speaks the full standard LangChain interface: .invoke / .stream /
    .batch / .bind_tools / .with_structured_output, plus async variants. That's
    why every concept in this repo "just works" the same way it would with any
    other provider.

    Pass model="fast" to use the cheaper/faster model for high-volume nodes
    (classifiers, summaries) without hardcoding the model name in examples.
    """
    global settings
    if settings is None:
        settings = Settings.from_env()

    if model == "fast":
        chosen = settings.fast_model
    else:
        chosen = model or settings.model

    temp = settings.temperature if temperature is None else temperature

    log.info("Creating ChatGroq model=%s temperature=%s", chosen, temp)
    return ChatGroq(
        model=chosen,
        temperature=temp,
        api_key=settings.groq_api_key,
        max_retries=2,
        timeout=60,
    )
