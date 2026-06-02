# Microsoft Agent Framework — Mastery & Interview Pack

A single, runnable project that teaches **every core concept of the Microsoft
Agent Framework (MAF)** through 18 small, heavily‑commented examples, plus an
[`INTERVIEW.md`](./INTERVIEW.md) with ~50 Q&A. Work through it once and you'll be
ready to discuss MAF confidently in an interview — and to build with it.

Everything is wired to run on **Groq** (free, fast, OpenAI‑compatible) using an
API key that starts with `gsk_`, so you can run the LLM examples for free.

---

## What is the Microsoft Agent Framework?

MAF is Microsoft's open‑source, multi‑language SDK (Python **and** .NET) for
building production‑grade **AI agents** and **multi‑agent workflows**. It unifies
the two libraries Microsoft used to ship separately — **Semantic Kernel**
(enterprise SDK, connectors, stable surface) and **AutoGen** (multi‑agent
orchestration) — and adds first‑class **graph‑based workflows**, **durable
state/checkpointing**, **human‑in‑the‑loop**, and **OpenTelemetry observability**.
It is provider‑agnostic: anything OpenAI‑compatible (OpenAI, Azure OpenAI, Groq,
Ollama, vLLM…) works.

The mental model, smallest to largest:

```
ChatClient  ->  Agent  ->  (tools, sessions, middleware)  ->  Orchestration  ->  Workflows
  (model)     (LLM+rules)        (capabilities/memory)        (multi-agent)      (typed graphs)
```

> **Note on this project (Python, v1.7.0):** MAF moves fast and renames things
> between minor versions. This pack is written and **verified against
> `agent-framework==1.7.0`**, where the key types are `Agent` (older docs:
> `ChatAgent`), `AgentSession` (older docs: `AgentThread`), and the orchestration
> builders live in `agent_framework.orchestrations`. The *concepts* are identical
> across versions; the names are flagged in each example so you recognise both.

> **About the API key:** a key starting with `gsk_` is a **Groq** key (the
> inference provider). It is *not* "Grok" from xAI (those start with `xai-`).
> This project targets Groq's OpenAI‑compatible endpoint. To use any other
> provider, change `GROQ_BASE_URL`/model in `examples/_shared.py`.

---

## Setup (5 minutes)

**1. Python 3.10+** is required. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate          # macOS/Linux
# .venv\Scripts\activate           # Windows PowerShell
```

**2. Install dependencies:**

```bash
pip install -r requirements.txt
```

**3. Get a free Groq key** at <https://console.groq.com/keys> (it starts with
`gsk_`), then put it in a `.env` file:

```bash
cp .env.example .env               # then paste your key into .env
```

That's it — the examples **auto-load `.env`** from the project root (via
python-dotenv, which ships with agent-framework), so you don't need to export
anything. A plain `.env` file is otherwise *not* read automatically by Python.

If you prefer environment variables instead of a `.env` file:

```bash
export GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxx      # macOS/Linux
# $env:GROQ_API_KEY="gsk_xxxx"                # Windows PowerShell
```

---

## Running the examples

Each example is standalone and self‑describing. Run any one directly:

```bash
cd examples
python 01_basic_agent.py
python 08_orchestration_sequential.py
```

Or run them all (LLM ones are skipped automatically if no key is set):

```bash
python run_all.py            # everything
python run_all.py 03 08 16   # just these
```

**No key? You can still run the workflow‑engine examples 13–16** — they use pure
Python executors (no LLM) and run fully offline. Start there to learn the graph
engine, then add a key for the rest.

---

## The 18 examples (your concept checklist)

| #  | File | Concept | Needs key? |
|----|------|---------|:---------:|
| 01 | `01_basic_agent.py` | Agent = model + instructions; `run()`/`.text` | yes |
| 02 | `02_streaming.py` | Streaming token deltas with `stream=True` | yes |
| 03 | `03_function_tools.py` | `@tool` function calling (the agentic loop) | yes |
| 04 | `04_conversation_memory.py` | Multi‑turn memory via `AgentSession` | yes |
| 05 | `05_structured_output.py` | Typed output with Pydantic `response_format` / `.value` | yes |
| 06 | `06_middleware.py` | agent / function / chat middleware (guardrails, logging) | yes |
| 07 | `07_agent_as_tool.py` | Agent composition (one agent calls another) | yes |
| 08 | `08_orchestration_sequential.py` | Sequential pipeline of agents | yes |
| 09 | `09_orchestration_concurrent.py` | Concurrent fan‑out/fan‑in agents | yes |
| 10 | `10_orchestration_groupchat.py` | Turn‑based group‑chat collaboration | yes |
| 11 | `11_orchestration_handoff.py` | Dynamic handoff/routing to specialists | yes |
| 12 | `12_orchestration_magentic.py` | Manager‑led planning (Magentic) | yes |
| 13 | `13_workflow_executors_edges.py` | Workflow graph: executors + edges | **no** |
| 14 | `14_workflow_fanout_fanin.py` | Parallel fan‑out / fan‑in in a workflow | **no** |
| 15 | `15_workflow_conditional.py` | Conditional routing / branching edges | **no** |
| 16 | `16_workflow_human_in_the_loop.py` | Pause & resume (`request_info`/`response_handler`) | **no** |
| 17 | `17_observability.py` | OpenTelemetry tracing & metrics | yes |
| 18 | `18_mcp_tools.py` | MCP tool servers (auto‑discovered tools) | yes (+npx) |

Recommended path: **01 → 07** (single agent), then **08 → 12** (multi‑agent
orchestration), then **13 → 16** (the workflow engine underneath), then **17–18**
(observability & MCP). Read [`INTERVIEW.md`](./INTERVIEW.md) alongside.

---

## How the pieces relate (the one diagram to remember)

- A **ChatClient** wraps a model/provider. `OpenAIChatCompletionClient` + a
  `base_url` talks to any OpenAI‑compatible API (here, Groq).
- An **Agent** = ChatClient + instructions, optionally with **tools**,
  **middleware**, **context providers**, and a **session** (memory).
- **Orchestration builders** (`Sequential`, `Concurrent`, `GroupChat`, `Handoff`,
  `Magentic`) are pre‑built multi‑agent patterns. They *compile down to* …
- … the **Workflow engine**: a typed, directed graph of **executors** joined by
  **edges**, supporting branching, parallelism, human‑in‑the‑loop and
  checkpointing. Agents can be nodes in a workflow, so you freely mix
  deterministic code with LLM steps.
- **Observability** (OpenTelemetry) and **middleware** cut across all of it.

---

## Troubleshooting

- **`GROQ_API_KEY is not set`** — export the key (see Setup step 3).
- **`model has been decommissioned` / 400 model error** — Groq rotated models;
  set `GROQ_MODEL` to a current one from <https://console.groq.com/docs/models>
  (e.g. `llama-3.1-8b-instant`).
- **Rate limits (free tier)** — Groq's free tier is per‑minute limited; wait a
  moment or space out runs.
- **Import errors / different attribute names** — make sure you installed the
  pinned version: `pip install -r requirements.txt` (this pack targets `1.7.0`).
- **Example 18 says npx not found** — install Node.js (<https://nodejs.org>);
  MCP's reference server is launched via `npx`. The other examples don't need it.

---

## Files

```
maf-mastery/
├── README.md              # you are here
├── INTERVIEW.md           # ~50 interview questions & answers
├── requirements.txt       # pinned deps (agent-framework==1.7.0)
├── .env.example           # GROQ_API_KEY / GROQ_MODEL template
├── run_all.py             # run all / selected examples
└── examples/
    ├── _shared.py         # Groq-backed ChatClient factory (imported by all)
    ├── 01_basic_agent.py … 18_mcp_tools.py
```

Happy building — and good luck in the interview.
