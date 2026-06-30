# CrewAI vs LangGraph vs MAF — the same task, three frameworks

A small, **runnable** comparison of three multi-agent frameworks:

- **[CrewAI](https://github.com/crewAIInc/crewAI)** — role-playing agent crews
- **[LangGraph](https://github.com/langchain-ai/langgraph)** — stateful graphs (nodes + edges)
- **[MAF](https://github.com/microsoft/agent-framework)** — Microsoft Agent Framework, the unified successor to AutoGen + Semantic Kernel (1.0 GA, April 2026)

Every example solves the **same problem** — *research a topic → write a short article → review it* — so the only thing that changes between the files is **how each framework models agents and control flow**.

> **Runs with zero setup.** With no API key, the repo runs in deterministic **simulated** mode so you can see the structure and output immediately. Add a `GROQ_API_KEY` or `OPENAI_API_KEY` and install a framework to run it for real.

---

## ▶ Run it

### 1. Get the code

```bash
git clone <your-repo-url>
cd agent-frameworks-compared
```

### 2. Run immediately — no key, no installs (simulated mode)

```bash
python run_all.py
```

You should see all three frameworks run the same task and print a comparison + decision guide. Example (trimmed):

```
======================================================================
AI AGENT FRAMEWORKS COMPARED — CrewAI vs LangGraph vs MAF
======================================================================
Topic : the benefits and risks of multi-agent AI systems for startups
Mode  : SIMULATED (no API key)   (model: (simulated))

--- LangGraph  (stateful graph, conditional revise loop) ---
[langgraph] revisions taken: 2, final verdict: APPROVE
Multi-agent AI systems let a startup break a hard task into roles—one agent ...
```

### 3. Run a single framework

```bash
python crewai_pipeline.py
python langgraph_pipeline.py
python maf_pipeline.py
```

### 4. Run for real (auto-detects your provider)

Set **one** key — the repo picks the provider automatically:

```bash
# Option A — Groq (gsk_... keys; free tier, runs open models like Llama):
export GROQ_API_KEY=gsk_...

# Option B — OpenAI (sk-... keys):
export OPENAI_API_KEY=sk-...

# install the openai SDK + only the framework(s) you want to try:
pip install openai
pip install langgraph         # then: python langgraph_pipeline.py
pip install crewai            # then: python crewai_pipeline.py
pip install agent-framework   # then: python maf_pipeline.py
```

You do **not** need all three frameworks installed — each file falls back to a
pure-Python simulation of the same flow if its framework (or a key) is missing.

**Provider notes**

- With **Groq**, the default model is `llama-3.3-70b-versatile` and CrewAI uses the `groq/` LiteLLM prefix automatically. Groq is OpenAI-compatible (`base_url=https://api.groq.com/openai/v1`), so LangGraph and CrewAI work unchanged. For MAF, the client is pointed at Groq's endpoint; if your installed `agent-framework` build rejects a custom `base_url`, the file prints a note and falls back to a Groq-backed path rather than crashing.
- **Groq vs Grok:** a `gsk_` key is **Groq** (GroqCloud inference). **Grok** is xAI's model — those keys start with `xai-` and use `https://api.x.ai/v1`.

**Optional overrides**

```bash
export OAI_MODEL=openai/gpt-oss-20b        # any Groq-hosted model
export TOPIC="should small teams build their own RAG pipeline?"
```

### Requirements

- Python **3.10–3.13** (CrewAI requires `>=3.10,<3.14`).
- See `requirements.txt` (everything optional) and `.env.example` for keys.

---

## First, what does NOT separate these frameworks

It's easy to pick for the wrong reason. At the **feature** level these three have largely converged — a feature checklist will mislead you. All three can do:

- multi-agent orchestration, **loops, cycles, and conditional routing**
- tool / function calling and MCP
- any model provider (OpenAI, Azure OpenAI, Anthropic, Groq, local, …)
- human-in-the-loop, state, and checkpointing

So these are **not** real differentiators:

- ❌ *"LangGraph can loop but MAF can't."* False — MAF expresses the exact same review→revise loop with a conditional edge that points back to an earlier executor (see snippet below). In this repo LangGraph *demonstrates* the loop only as a teaching device; it isn't a capability boundary.
- ❌ *"Pick MAF to run on Azure / in Python."* Both LangGraph and CrewAI also call Azure OpenAI and deploy as ordinary Python services. Azure-on-Python is not unique to MAF.

---

## What actually decides it (in priority order)

### 1. Language / runtime — the only hard constraint
This is MAF's genuinely unique axis — but it's **.NET**, not Azure.

| You build in… | Pick |
|---|---|
| **C# / .NET** | **MAF** (the only one of the three with first-class .NET) |
| **JavaScript / TypeScript** | **LangGraph** (via LangGraph.js) |
| **Pure Python** | all three qualify → this axis decides nothing; go to #2 |

If you're Python-only, MAF's headline selling point doesn't apply to you. Set it aside.

### 2. Ecosystem you're plugging into — usually the real decider
- **LangGraph** inherits the whole **LangChain** ecosystem: hundreds of integrations, retrievers, vector stores, tools, plus **LangSmith** for tracing/eval. Largest integration + tutorial surface.
- **MAF** plugs into the **Microsoft** stack: Foundry agents, **Entra** identity, **Purview** data governance, **App Insights** via built-in OpenTelemetry — and it's the official **migration path from AutoGen + Semantic Kernel**, with Microsoft's enterprise-support/longevity story.
- **CrewAI** is deliberately **standalone** — no LangChain dependency, lean, least framework baggage.

### 3. The abstraction you think in — each framework's "soul"
- **CrewAI** → you think in **people**: roles, goals, backstories. Highest-level, fastest to write, least explicit control. Great when agents should self-organize; weaker when you need determinism.
- **LangGraph** → you think in a **state machine**: explicit nodes, edges, shared state. Most control and auditability, most verbose. The LLM only does what a node tells it.
- **MAF** → you think in **typed executors + a workflow graph**: more ceremony than CrewAI, built for production ops (durable/resumable runs, checkpoints, governance, observability).

---

## TL;DR — when to use which

| | **CrewAI** | **LangGraph** | **MAF (Microsoft)** |
|---|---|---|---|
| **Think in** | a team of roles | a state machine | typed executors + graph |
| **.NET support** | no | no | **yes** (unique) |
| **Ecosystem** | standalone | LangChain / LangSmith | Microsoft / Foundry / Entra / Purview |
| **Migration path from** | — | — | **AutoGen + Semantic Kernel** |
| **Strength** | fastest role-based prototype | most control + biggest integration base | enterprise governance + ops envelope |
| **Cost** | least conceptual overhead | most explicit/verbose | most production plumbing |
| **Loops / cycles** | ✅ (also via Flows) | ✅ | ✅ |
| **Lines to a first run** | ~20 | ~45 | ~25 |

**Decision in one line each**

- Pick **CrewAI** to ship a team-of-agents prototype fast, with the least conceptual overhead and no framework lock-in.
- Pick **LangGraph** when you want LangChain's ecosystem and **maximum explicit control** over flow, state, and auditing.
- Pick **MAF** when you're buying into Microsoft's **enterprise / governance / .NET** world, or you're **migrating from AutoGen or Semantic Kernel**.

For a **Python, provider-agnostic** project, the fork is really **#2 vs #3**: LangChain ecosystem + control (LangGraph) vs Microsoft envelope + AutoGen/SK lineage (MAF), with CrewAI as the "just get it working" option.

---

## The loop is the same in all three (proof)

The repo shows the review→revise loop in the **LangGraph** file purely to illustrate cyclic control flow. Here is the **identical loop in MAF** — a conditional edge from the reviewer back to the writer (MAF's superstep execution supports cycles, the condition guarantees termination):

```python
# MAF — same review -> revise loop, expressed as a conditional edge
workflow = (
    WorkflowBuilder(start_executor=research_exec)
    .add_edge(research_exec, write_exec)
    .add_edge(write_exec, review_exec)
    .add_edge(review_exec, write_exec, condition=needs_revision)  # <-- loop back
    .add_edge(review_exec, finish_exec, condition=is_done)
    .build()
)
```

```
all three:   research ──> write ──> review ──┐
                             ▲                │
                             └── REVISE ◀──────┘   (loop until APPROVE / max revisions)
```

The difference between the frameworks is **how you express** this loop, not **whether** you can — exactly the point of axes #2 and #3 above.

---

## Files

| File | What it shows |
|---|---|
| `shared.py` | The shared task + a single `llm_complete()` helper (real Groq/OpenAI **or** deterministic mock). Keeps the examples comparable. |
| `crewai_pipeline.py` | CrewAI `Agent` / `Task` / `Crew` with `Process.sequential` — the role-based abstraction. |
| `langgraph_pipeline.py` | LangGraph `StateGraph` with a **conditional edge** that loops review → rewrite — the state-machine abstraction. |
| `maf_pipeline.py` | MAF `ChatAgent` + `OpenAIChatClient` orchestration; `WorkflowBuilder` (incl. the conditional **loop** edge) shown in comments. |
| `run_all.py` | Runs all three on the same topic, prints the comparison + decision guide. |
| `requirements.txt` / `.env.example` | Optional deps and provider keys. |

> The three example files each **illustrate one pattern** for teaching clarity — they are not capability limits. Every framework here can do every pattern shown.

Each pipeline file degrades gracefully: if its framework isn't installed (or no API key is set), it runs a small **pure-Python simulation** of the same control flow so the file always works and you can still read the structure.

---

## How each framework expresses the task

**CrewAI** — describe teammates, hand them tasks, pick a process:

```python
researcher = Agent(role="Research Analyst", goal=..., backstory=..., llm="groq/llama-3.3-70b-versatile")
research_task = Task(description=..., expected_output=..., agent=researcher)
write_task    = Task(..., agent=writer, context=[research_task])   # output chains forward
crew = Crew(agents=[...], tasks=[...], process=Process.sequential)
crew.kickoff(inputs={"topic": topic})
```

**LangGraph** — define state, write nodes, wire edges (including a loop):

```python
g = StateGraph(State)
g.add_node("write", write_node); g.add_node("review", review_node)
g.add_edge(START, "research"); g.add_edge("research", "write"); g.add_edge("write", "review")
g.add_conditional_edges("review", route_after_review, {"revise": "write", "finish": "finish"})
graph = g.compile()
graph.invoke({"topic": topic, "revisions": 0})
```

**MAF** — agents on a chat client, then a typed workflow graph (loops included):

```python
client = OpenAIChatClient(model_id="...")
researcher = ChatAgent(chat_client=client, name="Researcher", instructions=...)

workflow = (
    WorkflowBuilder(start_executor=research_exec)
    .add_edge(research_exec, write_exec)
    .add_edge(write_exec, review_exec)
    .add_edge(review_exec, write_exec, condition=needs_revision)  # loop back
    .add_edge(review_exec, finish_exec, condition=is_done)
    .build()
)
```

---

## Caveats

- These frameworks move fast. Code targets **CrewAI** (`crewai`), **LangGraph** (`langgraph` 0.2+), and **MAF** (`agent-framework` 1.0). Pin versions for reproducibility.
- "Lines to a first run" is rough guidance, not a benchmark — always measure your own task and model.
- CrewAI routes models through LiteLLM, so the `llm=` string can point at OpenAI, Groq, Anthropic, a local Ollama model, etc. MAF and LangGraph similarly support many providers. This repo standardizes on an OpenAI-compatible endpoint (OpenAI **or** Groq) so a single key gets all three running.
