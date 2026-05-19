"""Abstract LLM client interface.

Every concrete provider (Anthropic, OpenAI, Mock) implements this contract.
The rest of the system depends only on this interface — never on a concrete
client — which keeps providers swappable.
"""
from __future__ import annotations

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for LLM clients."""

    @abstractmethod
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Send a prompt to the LLM and return the text response.

        Args:
            system_prompt: System-level instructions (the agent's "role").
            user_prompt:   The user-facing message to respond to.

        Returns:
            The model's text completion.

        Raises:
            LLMError: On any provider-side failure (network, auth, rate limit).
        """
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name, used in logging."""
        ...


class LLMError(Exception):
    """Raised when an LLM call fails."""
