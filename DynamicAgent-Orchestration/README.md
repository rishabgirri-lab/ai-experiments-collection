# Dynamic Agent Orchestrator

A production-style multi-agent orchestration system in Python. A **Planner** dynamically selects which specialist agents to run (Researcher, Coder, Analyst, Writer), they execute **in parallel**, and a **Synthesizer** merges their outputs into a single coherent answer.

Built to demonstrate **separation of concerns**, **dependency injection**, and **provider-agnostic LLM integration** — runnable with Anthropic, OpenAI, OpenAI-compatible providers (Groq, OpenRouter, Ollama), or a built-in mock mode that needs no API key.

## Features

- Dynamic agent selection via an LLM Planner
- Parallel specialist execution (`ThreadPoolExecutor`)
- Pluggable LLM providers behind a single interface
- Built-in mock mode — run end-to-end with zero setup
- Full pytest suite with stub LLMs (no API calls in CI)
- Clean package layout, type hints, structured logging
- CLI plus programmatic API

## Project Structure

```
dynamic-agent-orchestrator/
├── src/
│   └── orchestrator/
│       ├── __init__.py
│       ├── __main__.py              # CLI entry point
│       ├── logging_setup.py
│       ├── config/
│       │   ├── __init__.py
│       │   └── settings.py          # env-var loading, validation
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── base.py              # LLMClient ABC + LLMError
│       │   ├── anthropic_client.py
│       │   ├── openai_client.py
│       │   ├── mock_client.py
│       │   └── factory.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py              # Agent + AgentResult
│       │   ├── specialists.py       # Researcher, Coder, Analyst, Writer
│       │   ├── planner.py           # PlannerAgent + Plan
│       │   ├── synthesizer.py
│       │   └── registry.py
│       └── core/
│           ├── __init__.py
│           ├── orchestrator.py      # the pipeline
│           └── builder.py           # wires everything together
├── tests/
│   ├── conftest.py
│   ├── test_settings.py
│   ├── test_agents.py
│   └── test_orchestrator.py
├── examples/
│   ├── run_basic.py
│   └── custom_agent.py
├── docs/
│   └── ARCHITECTURE.md
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

## Quickstart

### 1. Clone & install

```bash
git clone https://github.com/YOUR_USERNAME/dynamic-agent-orchestrator.git
cd dynamic-agent-orchestrator
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

### 2. Run with no API key (mock mode)

```bash
python -m orchestrator "Explain how solar panels work for a kid"
```

This uses canned responses so you can verify the full pipeline (Planner → parallel agents → Synthesizer) without spending a cent.

### 3. Run with a real LLM

Copy the env template and fill in:

```bash
cp .env.example .env
# edit .env, then load it:
export $(grep -v '^#' .env | xargs)
python -m orchestrator "Your task here"
```

Or just export the vars inline:

```bash
export LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python -m orchestrator "Your task here"
```

## Where to Get API Keys

I can't share API keys — they're tied to billing accounts and forbidden to share by every provider's terms. Sign up for your own (most have free tiers or trial credits):

| Provider | Free tier? | Sign up |
|---|---|---|
| **Anthropic Claude** | Free credits on signup | https://console.anthropic.com/ |
| **OpenAI** | $5 minimum prepay | https://platform.openai.com/api-keys |
| **Groq** | Free tier, very fast | https://console.groq.com |
| **OpenRouter** | Has free models | https://openrouter.ai/keys |
| **Together AI** | Free credits | https://api.together.xyz |
| **Ollama** | Fully local, $0 | https://ollama.com |

Groq, OpenRouter, Together, and Ollama are OpenAI-API-compatible — use them by setting `LLM_PROVIDER=openai` and `OPENAI_BASE_URL` to their endpoint. See `.env.example` for URLs.

## Programmatic Use

```python
from orchestrator.core import build_default_orchestrator

orch = build_default_orchestrator()
result = orch.run("Compare REST vs GraphQL for a startup backend")

print(result.plan.agents)         # which specialists ran
print(result.final_answer)         # synthesized answer
for r in result.specialist_results:
    print(r.agent_name, r.latency_seconds, r.success)
```

## Adding Your Own Agent

Two options:

**Static** (the proper way for a permanent agent): edit `src/orchestrator/agents/specialists.py` and `src/orchestrator/agents/registry.py`.

**Dynamic** (good for experimentation): see `examples/custom_agent.py`.

Full walkthrough in [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## Tests

```bash
pytest                  # all tests, no API calls (uses FakeLLM)
pytest --cov            # with coverage
```

The test suite never touches a real LLM — it uses a `FakeLLM` stub configured per test.

## Environment Variables

| Var | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `mock` | `anthropic` \| `openai` \| `mock` |
| `ANTHROPIC_API_KEY` | — | Required when provider is `anthropic` |
| `OPENAI_API_KEY` | — | Required when provider is `openai` |
| `OPENAI_BASE_URL` | — | Optional, for OpenAI-compatible providers |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5` | Anthropic model name |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model name |
| `MAX_TOKENS` | `1024` | Max completion tokens |
| `TEMPERATURE` | `0.7` | Sampling temperature |
| `MAX_PARALLEL_AGENTS` | `4` | Worker pool size |
| `LOG_LEVEL` | `INFO` | `DEBUG` / `INFO` / `WARNING` / `ERROR` |

## How It Works (Pipeline)

```
User task
    │
    ▼
┌─────────────┐
│  Planner    │  reads task, returns JSON: which agents to run
└─────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│  Specialists (parallel)             │
│  Researcher │ Coder │ Analyst │ ... │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────┐
│ Synthesizer │  merges outputs into final answer
└─────────────┘
    │
    ▼
Final answer
```

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for design rationale.

## License

MIT — see [LICENSE](LICENSE).
