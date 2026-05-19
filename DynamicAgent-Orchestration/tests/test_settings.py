"""Tests for the Settings module."""
from __future__ import annotations

import pytest

from orchestrator.config.settings import Settings, reset_settings


def test_default_provider_is_mock(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    reset_settings()
    s = Settings()
    assert s.provider == "mock"


def test_provider_lowercased(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "ANTHROPIC")
    s = Settings()
    assert s.provider == "anthropic"


def test_validate_missing_anthropic_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    s = Settings()
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        s.validate()


def test_validate_missing_openai_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    s = Settings()
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        s.validate()


def test_validate_unknown_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "weirdprovider")
    s = Settings()
    with pytest.raises(RuntimeError, match="Unknown LLM_PROVIDER"):
        s.validate()


def test_mock_provider_needs_no_key(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    s = Settings()
    s.validate()  # should not raise
