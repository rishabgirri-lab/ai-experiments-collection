# Architecture

## Pipeline Overview

```
        User task
           |
           v
   +--------------+
   |  Planner     |   chooses which specialists to invoke (returns JSON)
   +--------------+
           |
           v
   +-------------------------------------+
   |  Specialists (in parallel)          |
   |  Researcher | Coder | Analyst | ... |
   +-------------------------------------+
           |
           v
   +--------------+
   | Synthesizer  |   merges outputs into final answer
   +--------------+
           |
           v
        Final answer
```

## Layers and Responsibilities

| Layer | Module | Responsibility |
|-------|--------|----------------|
| Config | `orchestrator/config/` | Load env vars into a typed `Settings` object. Nothing else touches `os.environ`. |
| LLM | `orchestrator/llm/` | Abstract `LLMClient` + concrete providers (Anthropic, OpenAI, Mock) + factory. |
| Agents | `orchestrator/agents/` | `Agent` base class, specialists, Planner, Synthesizer, registry. |
| Core | `orchestrator/core/` | `Orchestrator` pipeline + `build_default_orchestrator()` wiring. |
| Entry | `orchestrator/__main__.py` | CLI. |

## Key Design Choices

### Dependency Injection
The `Orchestrator` takes already-constructed agents in its constructor. It never calls a factory itself. This keeps it testable (you inject fakes in unit tests).

### Provider abstraction
`LLMClient` is an ABC. Adding a new provider = a new class + one line in `factory.py`. The agents never import provider-specific code.

### Mock provider
A first-class `MockClient` makes it possible to exercise the whole pipeline with no key. Useful for CI and for new users who haven't picked a provider yet.

### Parallel execution
Specialists run in a `ThreadPoolExecutor`. This is appropriate because LLM calls are I/O-bound (network-bound). For very large agent counts, swap to `asyncio` + provider async clients.

### Defensive Planner parsing
LLMs sometimes wrap JSON in markdown fences or include preamble. The Planner strips fences, validates against known agent names, and falls back to a default plan if anything goes wrong — the pipeline never crashes because of a malformed plan.

## Adding a New Specialist

1. Subclass `Agent` in `agents/specialists.py`, set `NAME` and `SYSTEM_PROMPT`.
2. Register it in `agents/registry.py` by adding it to `_SPECIALIST_CLASSES`.
3. (Optional) Mention it in the Planner's system prompt (`agents/planner.py`) so the planner knows when to pick it.

Or do it at runtime — see `examples/custom_agent.py`.

## Adding a New LLM Provider

1. Create `orchestrator/llm/<name>_client.py` implementing `LLMClient`.
2. Add an `if settings.provider == "<name>"` branch in `factory.py`.
3. Add the env-var handling to `config/settings.py`.

## Testing Strategy

- Settings: env-var parsing and validation.
- Agents: each agent class tested with a `FakeLLM` that returns prerecorded responses.
- Planner: JSON parsing, fence stripping, fallback behavior, unknown-agent filtering.
- Orchestrator: full pipeline with a `FakeLLM`, plus a partial-failure test that ensures one broken agent doesn't sink the whole run.
