# CrewAI Complete Demo — Research → Write → Edit Crew (Grok-powered)

A single, runnable project that demonstrates **every core CrewAI concept** in one
coherent workflow, plus a curated set of **CrewAI interview questions with answers**.
It is configured to run on **Grok (xAI)** since you have a Grok key.

---

## 1. What this project is

This project builds a small **AI "crew"** — a team of LLM-powered agents that
collaborate to produce a finished article on any topic you give them.

The crew has three agents working as a pipeline:

1. **Senior Research Analyst** — researches the topic and produces a bulleted brief.
2. **Technical Content Writer** — turns the brief into a ~400-word article for a target audience.
3. **Managing Editor** — polishes the article and verifies length using a tool.

Along the way it exercises the full CrewAI feature set: **Agents, Tasks, Tools,
Crew, Process, context passing between tasks, custom tools, structured expected
outputs, output files, rate limiting, optional memory, and a pluggable LLM
backend (Grok).** Rich logging shows exactly what happens at each step.

---

## 2. CrewAI concepts covered (and where to find them)

| Concept | What it is | File |
|---|---|---|
| **Agent** | An autonomous worker with role/goal/backstory | `src/crew_demo/agents.py` |
| **role / goal / backstory** | Fields that shape the agent's system prompt | `agents.py` |
| **Task** | A unit of work assigned to an agent | `src/crew_demo/tasks.py` |
| **expected_output** | The definition of "done" that guides the LLM | `tasks.py` |
| **context (task chaining)** | Feeding one task's output into the next | `tasks.py` |
| **output_file** | Persisting a task result to disk | `tasks.py` |
| **Custom Tool** | Action an agent can take, via `BaseTool` + Pydantic schema | `src/crew_demo/tools/custom_tools.py` |
| **Crew** | The container binding agents + tasks | `src/crew_demo/crew.py` |
| **Process** | Orchestration strategy (`sequential` here; `hierarchical` explained) | `crew.py` |
| **memory** | Optional recall across steps (toggle via env) | `crew.py` |
| **max_rpm / max_iter** | Cost & safety controls | `crew.py`, `agents.py` |
| **allow_delegation** | Whether an agent can hand work to others | `agents.py` |
| **LLM backend (Grok)** | OpenAI-compatible config via LiteLLM | `src/crew_demo/llm_config.py` |
| **kickoff inputs** | Runtime `{placeholders}` injected into tasks | `main.py` |
| **Logging** | Console + rotating file logging of our app flow | `src/crew_demo/logger.py` |

---

## 3. Architecture of the solution

```
                        ┌──────────────────────────┐
                        │         main.py          │
                        │  parses --topic/--audience│
                        │  loads .env, kicks off    │
                        └─────────────┬────────────┘
                                      │ inputs={topic, audience}
                                      ▼
                        ┌──────────────────────────┐
                        │  ResearchWritingCrew      │  crew.py
                        │  Process = sequential     │
                        │  max_rpm, memory(optional)│
                        └─────────────┬────────────┘
                                      │ assembles
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
       ┌────────────┐         ┌────────────┐          ┌────────────┐
       │  Researcher│         │   Writer   │          │   Editor   │
       │   Agent    │         │   Agent    │          │   Agent    │
       └──────┬─────┘         └──────┬─────┘          └──────┬─────┘
              │ Task 1               │ Task 2                │ Task 3
              │ research brief ─────►│ writes article ─────►│ edits + verifies
              │                      │ (context=Task1)       │ (context=Task2)
              │                      │ tool: keyword_extractor│ tools: word_counter,
              │                      │                        │        keyword_extractor
              ▼                      ▼                        ▼
        ┌──────────────────────────────────────────────────────────┐
        │            Grok LLM (xAI) via LiteLLM / OpenAI API         │  llm_config.py
        │            base_url = https://api.x.ai/v1                  │
        └──────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                 logs/final_article.md   +   logs/crew_demo.log
```

**Data flow:** `main.py` injects `{topic}` and `{audience}` → Researcher produces a
brief → Writer consumes the brief (via `context`) and drafts the article → Editor
consumes the draft, polishes it, checks word count with a tool, and writes the
final result to `logs/final_article_<mode>.md`. Every agent calls the LLM for
reasoning; deterministic tools (word count, keywords) run locally without the LLM.

**Three orchestration modes** are wired in (see `crew.py`), selectable with `--mode`:

```
sequential:   [Researcher] -> [Writer] -> [Editor]                    (linear)

async:        [Researcher]  ┐
                            ├─► [Writer] -> [Editor]   (fan-out / fan-in)
              [AudienceAna] ┘   (writer waits for both via context)

hierarchical: [Manager] dynamically delegates to {Researcher, Writer, Editor}
              and validates outputs before moving on.
```

---

## 4. How to run

### Prerequisites
- Python 3.10+
- A Grok (xAI) API key

### Step 1 — Install dependencies
```bash
cd crewai_project
python -m venv .venv && source .venv/bin/activate    # optional but recommended
pip install -r requirements.txt
```

### Step 2 — Configure your API key
```bash
cp .env.example .env
# then edit .env and set GROK_API_KEY
```

The variable is named `GROK_API_KEY` for historical reasons but works with **any OpenAI-compatible provider**. Two common cases:

- **Groq** (key starts with `gsk-`) — fast, cheap inference of open models. Use:
  - `GROK_BASE_URL=https://api.groq.com/openai/v1`
  - `GROK_MODEL=llama-3.3-70b-versatile` (or `openai/gpt-oss-120b`, `llama-3.1-8b-instant`)
- **xAI Grok** (key starts with `xai-`) — Use:
  - `GROK_BASE_URL=https://api.x.ai/v1`
  - `GROK_MODEL=grok-2-latest`

Optional: `ENABLE_MEMORY=true` to turn on CrewAI's memory (may trigger embedding API calls).

### Step 3 — Run

Pick a process mode with `--mode`:

```bash
# Linear pipeline: research -> write -> edit
python main.py --mode sequential   --topic "AI agents in healthcare"

# Two parallel research tasks (topic + audience) fan in to the writer
python main.py --mode async        --topic "AI agents in healthcare"

# A manager LLM dynamically delegates work to the right specialist
python main.py --mode hierarchical --topic "AI agents in healthcare"

# Run all three back-to-back and print a comparison summary at the end
python main.py --mode all          --topic "AI agents in healthcare"
```

**Inputs (CLI flags):**
| Flag | Required | Default | Meaning |
|---|---|---|---|
| `--mode` | no | `sequential` | One of `sequential`, `hierarchical`, `async`, `all` |
| `--topic` | no | "The impact of AI agents on software engineering" | Subject to research & write about |
| `--audience` | no | "technical professionals" | Who the article is written for |

**What each mode does**

| Mode | Process | Task shape | When to use |
|---|---|---|---|
| `sequential` | `Process.sequential` | research → write → edit; each task pinned to an agent | Known linear pipeline; cheapest and most predictable |
| `async` | `Process.sequential` + `async_execution=True` on two tasks | [topic_research ║ audience_research] → write → edit | Independent sub-tasks you want concurrent for speed |
| `hierarchical` | `Process.hierarchical` + `manager_agent` | Tasks have NO agent; manager delegates at runtime | Dynamic task allocation, quality gates, retries |

> CrewAI does **not** expose `Process.parallel` as a value. The correct way to parallelize is `async_execution=True` on tasks (what `--mode async` demonstrates) or use Flows for complex DAGs.

### Step 4 — See what happened
- **Console**: live logs from our app + CrewAI's verbose agent reasoning.
- **`logs/crew_demo.log`**: full rotating log file (DEBUG level).
- **`logs/final_article_<mode>.md`**: the finished article for each mode.

Example minimal run (uses all defaults — sequential mode):
```bash
python main.py
```

---

## 5. Project structure

```
crewai_project/
├── main.py                       # Entry point: CLI, kickoff, result handling
├── requirements.txt
├── .env.example                  # Copy to .env and add your Grok key
├── README.md
├── logs/                         # Created at runtime (logs + final article)
└── src/
    └── crew_demo/
        ├── logger.py             # Console + rotating-file logging
        ├── llm_config.py         # Grok LLM wiring (OpenAI-compatible)
        ├── agents.py             # The three agents
        ├── tasks.py              # The three tasks + context chaining
        ├── crew.py               # Crew + Process assembly
        └── tools/
            └── custom_tools.py   # WordCountTool, KeywordExtractorTool
```

---

## 6. CrewAI Interview Questions & Answers

**Q1. What is CrewAI?**
A framework for orchestrating multiple role-playing, autonomous AI agents that
collaborate to complete complex tasks. It sits on top of LLMs and adds the
abstractions of Agents, Tasks, Tools, and Crews.

**Q2. What are the core building blocks?**
*Agent* (an LLM persona with role/goal/backstory), *Task* (a unit of work with an
expected output), *Tool* (an action an agent can invoke), and *Crew* (the
orchestrator binding agents and tasks under a Process).

**Q3. What does role / goal / backstory actually do?**
They are injected into the agent's system prompt. `role` sets identity, `goal`
sets the objective the agent optimizes for, and `backstory` adds persona and
constraints that steer tone and behavior.

**Q4. What Process types exist and when do you use each?**
`Process.sequential` runs tasks in defined order, passing outputs downstream —
best when work has a clear dependency chain. `Process.hierarchical` introduces a
manager (LLM) that dynamically plans, delegates to agents, and reviews results —
best for open-ended or branching work.

**Q5. How do tasks share data?**
Through the `context` parameter (explicitly listing prior tasks whose outputs
should be fed in) and implicitly in sequential mode where later tasks see earlier
results. `expected_output` strongly shapes what each task hands off.

**Q6. How do you create a custom tool?**
Subclass `crewai.tools.BaseTool`, set `name`, `description`, an `args_schema`
(a Pydantic model), and implement `_run(...)`. The `description` is critical — the
LLM reads it to decide when to call the tool. (See `custom_tools.py`.)

**Q7. What is `allow_delegation`?**
When `True`, an agent can delegate sub-tasks or ask questions of other agents in
the crew rather than doing everything itself. Useful for manager/editor roles.

**Q8. How does CrewAI connect to different LLMs (including Grok)?**
Via the `crewai.LLM` wrapper, which uses LiteLLM under the hood. Any
OpenAI-compatible endpoint works by setting the model with an `openai/` prefix
plus a custom `base_url` and `api_key` — exactly how this project targets
`https://api.x.ai/v1`. (See `llm_config.py`.)

**Q9. What is CrewAI memory?**
Optional short/long-term memory that lets agents recall earlier context across
steps and runs. It can trigger embedding calls, so it is off by default here and
toggled via `ENABLE_MEMORY`.

**Q10. How do you control cost and runaway loops?**
`max_iter` caps an agent's reasoning iterations, `max_rpm` rate-limits requests
per minute at the crew level, and choosing `sequential` over `hierarchical`
reduces extra coordination LLM calls.

**Q11. What does `kickoff()` do, and what are inputs?**
`crew.kickoff(inputs={...})` starts execution and substitutes the `{placeholder}`
variables found in task descriptions / agent fields with the provided values,
returning a result object that also carries token usage.

**Q12. Crew vs. a single chained LLM call — why bother?**
Crews give you specialized personas, tool use, automatic context passing,
delegation, retries, and observability — structure that scales far better than a
single monolithic prompt for multi-step collaborative work.

**Q13. Agents vs. Flows in CrewAI?**
*Crews/Agents* are autonomous and decide their own steps; *Flows* (a newer
CrewAI construct) give you explicit, event-driven, deterministic control over the
sequence. You can combine them: a Flow can call Crews.

**Q14. How do you make output structured/parseable?**
Use a precise `expected_output`, optionally `output_json` / `output_pydantic` on a
Task to coerce results into a schema, and `output_file` to persist them.

**Q15. How do tools differ from agents?**
Agents reason with an LLM; tools are deterministic (or external) actions agents
call. In this project `WordCountTool` runs pure Python — no LLM — which is cheaper
and reliable for things LLMs do poorly (exact counting).

---

## 7. Troubleshooting

- **`GROK_API_KEY is not set`** → create `.env` from `.env.example` or export the var.
- **`Unable to initialize LLM ... LiteLLM fallback not installed`** → `pip install litellm` (already in `requirements.txt`).
- **Auth/401 errors** → verify your key and that `GROK_BASE_URL` is `https://api.x.ai/v1`.
- **Model not found** → set a valid `GROK_MODEL` (e.g. `grok-2-latest`).
```
