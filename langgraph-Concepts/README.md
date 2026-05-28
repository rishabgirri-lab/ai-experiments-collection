# LangGraph + Groq — Complete Concepts Project

A ready-to-run reference project that implements **every core LangGraph concept**
as a small, self-contained, heavily-commented example — all wired to **Groq's
fast inference** (Llama models) via `langchain-groq`. Every example **logs what
it's doing node-by-node** and **prints its graph** (ASCII + Mermaid). Built and
verified against **LangGraph 1.2** on **Python 3.11+**.

> **Important — Groq vs Grok.** This project uses **Groq** (console.groq.com,
> keys start with `gsk_`), a fast-inference company that runs open models like
> Llama. That is a *different product* from **Grok** (xAI's model, keys start
> with `xai-`). If your key starts with `gsk`, you're in the right place.

Companion doc: **[`INTERVIEW_CONCEPTS.md`](./INTERVIEW_CONCEPTS.md)** — interview Q&A and mental models.

---

## 1. What this project is

Most tutorials demonstrate one feature in isolation. This repository is a
**concept map you can execute**: each of the 12 numbered files isolates exactly
one LangGraph idea so you can read it, run it, and modify it. Inline comments
explain not just *how* an API is used but *why* it exists.

Two things make it easy to actually *see* what's happening:

- **Logging everywhere.** Every node logs when it runs, what it received, and
  what it produced. Routers log the branch they chose. Tools log their calls.
- **Graph printing.** Every example prints its compiled graph as a node/edge
  list, an ASCII diagram, and Mermaid source (paste into <https://mermaid.live>).

---

## 2. Architecture

```
                       ┌──────────────────────────────────────────┐
                       │                  YOU                      │
                       │   python -m langgraph_grok.examples.eNN   │
                       │   python run_all.py                       │
                       └───────────────────┬──────────────────────┘
                                           │ invoke / stream
                                           ▼
        ┌────────────────────────────────────────────────────────────────┐
        │                      EXAMPLES  (01–12)                          │
        │   each builds a StateGraph, prints it, compiles, runs it        │
        │   — and LOGS every node as it executes                          │
        └───────┬─────────────────────┬───────────────────────┬──────────┘
                │ imports model        │ imports shared parts   │ logging
                ▼                      ▼                        ▼
   ┌────────────────────┐  ┌────────────────────┐  ┌────────────────────────┐
   │   config.py        │  │   core/            │  │   logging_utils.py     │
   │   get_llm()→ChatGroq│ │   state/tools/help │  │   get_logger()         │
   │   reads GROQ_API_KEY│ │                    │  │   print_graph()        │
   └─────────┬──────────┘  └────────────────────┘  └────────────────────────┘
             │ HTTPS
             ▼
   ┌────────────────────┐
   │   Groq API         │
   │   Llama models     │
   │   gsk_ key          │
   └────────────────────┘

   Persistence layer (examples 06 / 07 / 08):
        MemorySaver (RAM) → SqliteSaver (file) → PostgresSaver (prod)
        snapshots state after every super-step → memory, resume, time travel
```

### The LangGraph execution model

```
   define State (TypedDict + reducers)
            │
            ▼
   add nodes  ──►  add edges (normal + conditional)
            │
            ▼
   builder.compile(checkpointer?)   ← validates topology, wires channels
            │
            ▼
   graph.invoke(input, config)      ← runs the Pregel "super-step" loop:
            │
            ▼
   ┌───────────────────────────────────────────────┐
   │  SUPER-STEP LOOP                                │
   │  1. find all runnable nodes                     │
   │  2. run them (in parallel if >1)                │
   │  3. merge their updates via reducers            │
   │  4. checkpoint the new state (if checkpointer)  │
   │  5. follow edges → repeat until END             │
   └───────────────────────────────────────────────┘
            │
            ▼
        final State
```

---

## 3. The concept map

| #  | File | Concept | Key APIs |
|----|------|---------|----------|
| 01 | `e01_basics.py` | State, nodes, edges, build→compile→invoke | `StateGraph`, `add_node`, `add_edge`, `START`, `END` |
| 02 | `e02_conditional.py` | Conditional edges & routing | `add_conditional_edges`, router fn |
| 03 | `e03_reducers.py` | Reducers & chat memory | `Annotated[..., reducer]`, `operator.add`, `add_messages` |
| 04 | `e04_parallel.py` | Parallel fan-out / fan-in | parallel edges, reducers |
| 05 | `e05_tools_react.py` | Tools + ReAct loop (cycle) | `@tool`, `bind_tools`, `ToolNode`, `tools_condition` |
| 06 | `e06_checkpointing.py` | Persistence, threads, memory | `MemorySaver`/`SqliteSaver`, `thread_id`, `get_state` |
| 07 | `e07_human_in_loop.py` | Human-in-the-loop | `interrupt()`, `Command(resume=...)` |
| 08 | `e08_time_travel.py` | History, replay, forking | `get_state_history`, `update_state` |
| 09 | `e09_structured_output.py` | Typed validated output | `with_structured_output`, Pydantic |
| 10 | `e10_subgraphs.py` | Composition: graphs as nodes | nested compiled graphs |
| 11 | `e11_send_map_reduce.py` | Dynamic map-reduce | `Send` API |
| 12 | `e12_prebuilt_streaming.py` | Prebuilt agent, streaming, viz | `create_react_agent`, `stream_mode` |
| 13 | `e13_failure_resume.py` | Failure & durable resume from the failed node | `get_state` (`.next`), `invoke(None, cfg)`, checkpointer |

---

## 4. Repository layout

```
langgraph-grok/
├── README.md                     # this file
├── INTERVIEW_CONCEPTS.md         # interview Q&A + mental models
├── requirements.txt              # LangGraph 1.2.x, langchain-groq, grandalf …
├── .env.example                  # copy to .env, add your GROQ_API_KEY
├── run_all.py                    # run any / all examples (logging on)
└── langgraph_grok/
    ├── __init__.py
    ├── config.py                 # get_llm() → the single Groq model factory
    ├── logging_utils.py          # get_logger(), print_graph(), banner()
    ├── core/                     # reusable building blocks
    │   ├── __init__.py
    │   ├── state.py              # ChatState, AccumulatingState (+ reducers)
    │   ├── tools.py              # add, multiply, web_search, DEFAULT_TOOLS
    │   └── helpers.py            # print_messages, to_mermaid
    └── examples/                 # the 12 concept examples (all with logging)
        ├── __init__.py
        └── e01_basics.py … e12_prebuilt_streaming.py, e13_failure_resume.py
```

---

## 5. How to execute — step by step

### Step 1 — Code + virtual environment

```bash
unzip langgraph-grok.zip
cd langgraph-grok
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### Step 2 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 3 — Add your Groq API key

```bash
cp .env.example .env
```

Open `.env` and paste your key (the value after `GROQ_API_KEY=`). Get one at
<https://console.groq.com>:

```
GROQ_API_KEY=gsk_your_real_key_here
GROQ_MODEL=llama-3.3-70b-versatile      # capable, general purpose
GROQ_FAST_MODEL=llama-3.1-8b-instant    # cheap/fast (classifiers, summaries)
GROQ_TEMPERATURE=0
LOG_LEVEL=INFO                          # DEBUG for very verbose output
```

> Your key starts with `gsk` — that's the Groq format, and it's correct for this
> project. (An `xai-` key is for xAI's Grok, a different product, and won't work
> here. The config will warn you if it sees one.)

### Step 4 — Run

```bash
# One concept (watch the logs + graph print):
python -m langgraph_grok.examples.e01_basics

# Everything (smoke test):
python run_all.py

# Just a couple by number:
python run_all.py 5 9
```

### Step 5 (optional) — Verify the runtime *without* a key

Examples **08** (time travel) and **13** (failure & resume) make no LLM calls,
so they run offline and show the logging + graph printing in action before you
add a key:

```bash
python -m langgraph_grok.examples.e08_time_travel
python -m langgraph_grok.examples.e13_failure_resume   # crash mid-graph, then resume from the failed node
```

---

## 6. What the output looks like

Each example prints its graph and logs each node. For example, `e08` prints:

```
----- e08 time travel: ASCII diagram -----
+-----------+
| __start__ |
+-----------+
      *
   +---------+
   | add_ten |
   +---------+
      *
   ...

12:35:55 | INFO | __main__ | NODE add_ten | 5 + 10
12:35:55 | INFO | __main__ | NODE double  | 15 * 2
12:35:55 | INFO | __main__ | NODE square  | 30 ** 2
```

Logs are timestamped and tagged with the module, so in `run_all.py` you can see
exactly which example and which node produced each line. Set `LOG_LEVEL=DEBUG`
in `.env` for more detail; third-party HTTP logs are muted by default.

---

## 7. How Groq plugs in

All model construction lives in **one** place — `langgraph_grok/config.py`:

```python
from langchain_groq import ChatGroq
ChatGroq(model="llama-3.3-70b-versatile", api_key=...)  # reads GROQ_API_KEY
```

`ChatGroq` speaks the full standard LangChain interface (`invoke`, `stream`,
`batch`, `bind_tools`, `with_structured_output`, async variants), so every
concept works identically to any other provider. To swap providers, change this
one file. Use the fast model per-node where it helps:

```python
get_llm()                # default: llama-3.3-70b-versatile
get_llm(model="fast")    # llama-3.1-8b-instant for classifiers / summaries
```

---

## 8. Production notes

- **Persistence:** `MemorySaver` is RAM-only (dev/tests). Use `SqliteSaver`
  (durable, single process) or `PostgresSaver` (multi-instance). See the
  commented swap in `e06`.
- **Observability:** set `LANGSMITH_TRACING=true` + `LANGSMITH_API_KEY` in
  `.env` to trace every node, tool call, and token in LangSmith — on top of the
  built-in logging.
- **Recursion limit:** cyclic graphs stop after `recursion_limit` super-steps
  (default 25). Override per run: `config={"recursion_limit": 50}`.
- **Retries / timeouts / caching:** set per node via `add_node` or as graph-wide
  defaults at `StateGraph(...)` construction.

---

## 9. License

MIT — use freely for learning, demos, or as a starter for your own agents.
