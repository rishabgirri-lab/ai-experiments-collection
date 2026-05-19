"""Application settings loaded from environment variables.

Centralizes all configuration so the rest of the codebase never reads
os.environ directly. This makes testing easier (you can monkeypatch one
object) and keeps the surface area for misconfiguration small.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Settings:
    """Immutable application settings."""

    # Which LLM backend to use: "anthropic", "openai", or "mock"
    provider: str = field(default_factory=lambda: os.getenv("LLM_PROVIDER", "mock").lower())

    # API keys (only the one for the chosen provider needs to be set)
    anthropic_api_key: str | None = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    openai_api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))

    # Optional: override the base URL (useful for Groq / OpenRouter / Ollama,
    # which are OpenAI-API-compatible). Leave unset to use the default endpoint.
    openai_base_url: str | None = field(default_factory=lambda: os.getenv("OPENAI_BASE_URL"))

    # Model selection (provider-specific defaults are used if these are None)
    anthropic_model: str = field(default_factory=lambda: os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4o-mini"))

    # Generation parameters
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "1024")))
    temperature: float = field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.7")))

    # Orchestration parameters
    max_parallel_agents: int = field(default_factory=lambda: int(os.getenv("MAX_PARALLEL_AGENTS", "4")))
    request_timeout: int = field(default_factory=lambda: int(os.getenv("REQUEST_TIMEOUT", "60")))

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO").upper())

    def validate(self) -> None:
        """Raise a clear error if the chosen provider is missing its key."""
        if self.provider == "anthropic" and not self.anthropic_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=anthropic but ANTHROPIC_API_KEY is not set. "
                "Get a key at https://console.anthropic.com/"
            )
        if self.provider == "openai" and not self.openai_api_key:
            raise RuntimeError(
                "LLM_PROVIDER=openai but OPENAI_API_KEY is not set. "
                "Get a key at https://platform.openai.com/api-keys"
            )
        if self.provider not in {"anthropic", "openai", "mock"}:
            raise RuntimeError(
                f"Unknown LLM_PROVIDER={self.provider!r}. Use 'anthropic', 'openai', or 'mock'."
            )


# Singleton-style accessor — call get_settings() anywhere you need config
_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the global Settings instance, creating it on first call."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset the cached settings (used by tests)."""
    global _settings
    _settings = None
