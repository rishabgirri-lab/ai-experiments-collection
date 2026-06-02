# Microsoft Agent Framework — Interview Q&A

~50 questions covering the concepts an interviewer is likely to probe. Each
answer is something you can say out loud in 20–60 seconds. Where a concept has a
runnable demo in this pack, the example number is noted like `(→ ex 03)`.

Sections:
1. Fundamentals & positioning
2. Agents, tools & memory
3. Structured output, middleware & guardrails
4. Multi‑agent orchestration
5. Workflows (the graph engine)
6. Human‑in‑the‑loop, durability & checkpointing
7. Providers, MCP & interoperability
8. Observability, evaluation & production
9. Design judgement / scenario questions

---

## 1. Fundamentals & positioning

**Q1. What is the Microsoft Agent Framework?**
An open‑source, multi‑language (Python + .NET) SDK from Microsoft for building
production‑grade AI agents and multi‑agent workflows. It gives you agent
abstractions, tool/function calling, memory, multi‑agent orchestration, a
graph‑based workflow engine, durable state, human‑in‑the‑loop, and built‑in
OpenTelemetry observability.

**Q2. Where did it come from — how does it relate to Semantic Kernel and AutoGen?**
Microsoft previously shipped two overlapping things: **Semantic Kernel** (an
enterprise‑friendly SDK with connectors and a stable surface) and **AutoGen** (a
research‑driven multi‑agent orchestration library). MAF unifies them: it takes
SK's enterprise/runtime strengths and AutoGen's multi‑agent patterns into one
SDK, and adds graph workflows and durability. It's positioned as the long‑term
successor that carries you from prototype to production without rewrites.

**Q3. What problem does it actually solve?**
"Framework roulette" and the demo‑to‑production gap. Picking a foundation is the
hard part; MAF gives one provider‑agnostic SDK that scales from a single chat
agent to durable, observable, multi‑agent systems — so you don't rewrite when you
move from a notebook to a deployed service.

**Q4. What is an "AI agent" in this context?**
A system that pairs an LLM (reasoning/decision‑making) with context awareness and
the ability to *act* — by calling tools/APIs — usually in a loop until a goal is
met. An agent = model + instructions + (optionally) tools + memory.

**Q5. Is it Python‑only?**
No. MAF has parallel, first‑class implementations in **Python and .NET** that
share the same concepts and design patterns while respecting each language's
idioms. This pack uses Python; the .NET API mirrors it (e.g. `AIAgent`,
`WorkflowBuilder`, `AddEdge`, `AsAIAgent`).

**Q6. Is it production‑ready today?**
It launched in public preview as the unified successor and has been adding
production features (durable workflows, hosting, A2A, observability). Treat it as
fast‑moving: pin versions, because types get renamed between minor releases.

---

## 2. Agents, tools & memory

**Q7. How do you create the simplest agent?** *(→ ex 01)*
Wrap a chat client: `agent = chat_client.as_agent(name=..., instructions=...)`,
then `resp = await agent.run("..."); print(resp.text)`. Instructions are the
system prompt that shapes behaviour every turn.

**Q8. Streaming vs non‑streaming?** *(→ ex 02)*
`await agent.run(x)` returns one `AgentResponse`. `agent.run(x, stream=True)`
returns an async‑iterable `ResponseStream`; you `async for update in stream` and
read incremental `update.text`. Same method, two return shapes.

**Q9. How do tools / function calling work?** *(→ ex 03)*
Decorate a Python function with `@tool`; its signature + docstring become the
JSON schema the model sees. Pass `tools=[fn]` to the agent. The framework runs
the loop: model proposes a call → framework executes the function → result is fed
back → repeat until the model gives a final answer. This is the core agentic
loop.

**Q10. How does the framework know a tool's parameters?**
From type hints and the docstring, which it turns into a JSON schema
automatically. Good hints and docstrings = better tool selection. You can also
pass an explicit Pydantic `schema=` to `@tool`.

**Q11. What is a session and why does it matter?** *(→ ex 04)*
A **session** (`AgentSession`, formerly `AgentThread`) holds the running
conversation history. Without one, each `run` is stateless (single turn). Create
`session = agent.create_session()` and pass it into every `run` to get coherent
multi‑turn memory.

**Q12. Session vs context provider vs long‑term memory — what's the difference?**
A *session* is the in‑conversation transcript. A *context provider* injects extra
context into each turn (e.g. retrieved documents, user profile, "memories") —
it's the hook for RAG and personalization. Long‑term memory stores persist facts
across sessions. In MAF you attach `context_providers=[...]` to an agent; a
provider can read the incoming messages and add relevant context before the model
runs.

**Q13. How would you do RAG with MAF?**
Either (a) a tool that does retrieval on demand (the model decides when to
search), or (b) a context provider that retrieves relevant chunks and injects
them every turn, or (c) a provider/hosted tool like file search/vector store.
Pattern (a) gives the model control; (b) guarantees grounding context is always
present.

**Q14. Can an agent use another agent?** *(→ ex 07)*
Yes — "agent as a tool." Wrap a specialist agent in a `@tool` that calls
`await specialist.run(...)`. The parent delegates explicitly via function calling.
It's the simplest multi‑agent composition and a stepping stone to orchestration.

---

## 3. Structured output, middleware & guardrails

**Q15. How do you get typed/structured output instead of free text?** *(→ ex 05)*
Define a Pydantic `BaseModel` and pass it as `response_format` (e.g.
`default_options={"response_format": MyModel}`). The framework constrains the
model to emit conforming JSON and parses it; read the validated object from
`response.value`. No fragile regex parsing.

**Q16. What is middleware in MAF and what are the levels?** *(→ ex 06)*
Middleware is composable, cross‑cutting logic wrapped around execution — the
onion/pipeline pattern. Three levels:
- `@agent_middleware` wraps the whole `agent.run` invocation,
- `@function_middleware` wraps each tool call,
- `@chat_middleware` wraps each raw model call.
Each is `async def mw(context, next)`: do work, `await next()` to continue (or
skip it to short‑circuit), then inspect/modify `context.result`.

**Q17. Give concrete uses for each middleware level.**
Agent: timing, auth, request/response logging, retries. Function: argument
validation, blocking destructive tools, mocking in tests, caching tool results.
Chat: token counting, prompt redaction, model‑level rate limiting, response
post‑processing.

**Q18. How do you implement a guardrail that blocks a dangerous tool?** *(→ ex 06)*
A `@function_middleware` that inspects `context.function.name`/`context.arguments`
and either raises `MiddlewareTermination` or sets a safe `context.result` and
returns without calling `next()`. That vetoes the tool while keeping the
conversation alive.

**Q19. How do you put a human in front of a *tool* call?**
Set `approval_mode="always_require"` on a `@tool` (or MCP tool). The run surfaces
an approval request (`response.user_input_requests`) that you approve/deny before
the tool executes. For workflow‑level approvals, use `request_info` (→ ex 16).

---

## 4. Multi‑agent orchestration

**Q20. What orchestration patterns does MAF provide and when do you use each?**
- **Sequential** *(→ ex 08)* — fixed pipeline; each agent refines the prior
  output (draft → edit → headline).
- **Concurrent** *(→ ex 09)* — fan‑out the same input to independent agents in
  parallel, then aggregate (researcher + marketer + skeptic).
- **Group chat** *(→ ex 10)* — turn‑based shared conversation; an orchestrator
  picks the next speaker; ends on a termination condition / max rounds.
- **Handoff** *(→ ex 11)* — dynamic, model‑decided routing to specialists
  (support triage → billing/tech).
- **Magentic** *(→ ex 12)* — a manager maintains a task ledger (facts + plan),
  delegates, tracks progress and stalls; for open‑ended goals.

**Q21. Sequential vs Concurrent — the key difference?**
Sequential is *serial and dependent* (output flows down the chain). Concurrent is
*parallel and independent* (same input, agents don't see each other), then merged
by an aggregator. Concurrent is lower latency for independent perspectives.

**Q22. Concurrent vs Group chat?**
Concurrent agents run simultaneously and don't read each other's outputs. Group
chat is turn‑based and *shared* — each agent sees the conversation so far and
builds on it. Use group chat for debate/collaboration, concurrent for independent
opinions.

**Q23. How does Handoff decide where to route?**
The LLM decides, via tool‑call‑style handoffs you declare with `add_handoff(src,
[targets])`. You define the allowed edges (who can route to whom) and a start
agent; the model chooses the path at runtime. Specialists can hand back to triage.

**Q24. A gotcha you hit with Handoff in 1.7.x?**
Every participant must be created with
`require_per_service_call_history_persistence=True`, or `build()` raises. It keeps
local history consistent across the handoff tool‑call short‑circuits.

**Q25. What is the Magentic pattern, briefly?**
Manager‑led orchestration (from Microsoft's Magentic‑One research). A manager
agent builds and updates a task ledger (facts + plan), assigns sub‑tasks to
specialists, monitors progress, detects stalls/resets, and decides completion.
It's the most autonomous pattern — good for open‑ended tasks where the plan isn't
known up front.

**Q26. Are the orchestration builders separate engines?**
No — they're convenience wrappers that compile down to the same **workflow graph
engine** (executors + edges). Concurrent literally builds a dispatcher → fan‑out →
participants → fan‑in → aggregator graph. Understanding workflows means you
understand orchestration.

---

## 5. Workflows (the graph engine)

**Q27. What is a workflow in MAF?** *(→ ex 13)*
A typed, directed graph of **executors** (units of work) connected by **edges**
(data flow). The runtime handles execution order, message passing, type
validation, and error propagation. Executors can be functions, classes, *or
agents*, so you mix deterministic code with LLM steps in one graph.

**Q28. Executor vs edge?**
An **executor** is a node that receives a message, does work, and either forwards
a message (`ctx.send_message`) or yields a final output (`ctx.yield_output`). An
**edge** connects two executors and optionally carries a **condition** controlling
whether the message travels.

**Q29. What does `WorkflowContext[T]` mean?**
It's how the engine knows your executor's I/O types for validation.
`WorkflowContext[T]` = this executor *sends* messages of type `T`;
`WorkflowContext[Never, U]` = it *yields workflow output* of type `U` (and sends
nothing). Annotating these enables compile‑time‑style edge validation.

**Q30. How do you build and run a workflow?** *(→ ex 13)*
`WorkflowBuilder(start_executor=first).add_edge(a, b).build()`, then
`result = await workflow.run(input)`; read `result.get_outputs()`.

**Q31. How do you do branching / conditional routing?** *(→ ex 15)*
Put a predicate on the edge: `add_edge(src, target, condition=lambda msg: ...)`.
The emitted message is offered to each outgoing edge and only travels where the
predicate passes. For many mutually‑exclusive branches there's
`add_switch_case_edge_group(src, [Case(...), Default(...)])`.

**Q32. How do you run steps in parallel inside a workflow?** *(→ ex 14)*
Fan‑out/fan‑in: `add_fan_out_edges(src, [t1, t2, t3])` broadcasts to several
executors that run concurrently; `add_fan_in_edges([t1, t2, t3], join)` waits for
all of them and delivers their outputs as a **list** to the join executor.

**Q33. Why use the workflow engine instead of just calling agents in Python?**
You get typed validation, structured event streams (executor invoked/completed,
outputs, request‑info), built‑in fan‑out/fan‑in, conditional routing, **durable
checkpointing**, human‑in‑the‑loop, and observability — for free and consistently.
Plain Python gives you none of that plumbing.

**Q34. Can an agent be used directly as an executor?**
Yes. Agents implement the run protocol the workflow expects, so you can drop an
agent into the graph as a node and wire edges to/from it — that's exactly how the
orchestration builders embed agents.

---

## 6. Human‑in‑the‑loop, durability & checkpointing

**Q35. How does workflow‑level human‑in‑the‑loop work?** *(→ ex 16)*
An executor calls `await ctx.request_info(data, ResponseType)`, which emits a
typed request and **pauses** the workflow. You read pending requests via
`result.get_request_info_events()` (each has a `request_id` and `data`), get a
human answer, and **resume** with `await workflow.run(responses={request_id:
answer})`. A `@response_handler` method handles the answer and continues.

**Q36. `@handler` vs `@response_handler`?**
On a class‑based `Executor`: `@handler` handles a normal incoming message;
`@response_handler` is invoked specifically when a previously requested human/
external response arrives (it receives the original request and the response).

**Q37. What is checkpointing and why does it matter?**
Checkpointing persists workflow state so a long‑running or paused workflow can
**survive a process restart** and resume later — possibly on another machine.
You pass a `CheckpointStorage` (e.g. `InMemoryCheckpointStorage`,
`FileCheckpointStorage`) to the builder. Combined with `request_info`, a human
approval can take days without holding a process open.

**Q38. What are "durable workflows"?**
Workflows designed to run for minutes/hours/days with persisted state and
recovery. MAF added a durable workflow programming model (executors wired into a
directed graph, with a runner) plus hosting options; durability + observability +
checkpointing are what make multi‑step agents production‑safe rather than demos.

---

## 7. Providers, MCP & interoperability

**Q39. How does MAF stay provider‑agnostic?**
The `ChatClient` is an adapter over a model API. Swap the client (or just its
`base_url`) and every higher‑level concept keeps working. OpenAI, Azure OpenAI,
Azure AI Foundry, Ollama, vLLM, LM Studio, Groq, OpenRouter — all reachable.

**Q40. OpenAIChatClient vs OpenAIChatCompletionClient?**
`OpenAIChatClient` targets the newer OpenAI **Responses** API (richest hosted
tools: code interpreter, file search, web search, hosted MCP, image gen).
`OpenAIChatCompletionClient` targets the **Chat Completions** API for broad
compatibility. Many third‑party providers (including Groq) only implement Chat
Completions, so this pack uses `OpenAIChatCompletionClient` with `base_url`.

**Q41. How did you connect MAF to Groq specifically?** *(→ ex `_shared.py`)*
`OpenAIChatCompletionClient(model="llama-3.3-70b-versatile",
api_key="gsk_…", base_url="https://api.groq.com/openai/v1")`. Groq is
OpenAI‑compatible Chat Completions, so MAF talks to it unchanged — only the
base URL, key and model name differ.

**Q42. What is MCP and why does MAF support it?** *(→ ex 18)*
**Model Context Protocol** is an open standard for connecting agents to external
tool/data servers. Instead of hand‑writing tools, you point an agent at an MCP
server and it auto‑discovers the tools. MAF supports MCP over **stdio**
(`MCPStdioTool`), **HTTP** (`MCPStreamableHTTPTool`), and **websocket**
(`MCPWebsocketTool`). It's "USB‑C for tools": write a connector once, reuse
everywhere.

**Q43. What is A2A?**
**Agent‑to‑Agent** protocol — a standard for agents (possibly built with
different frameworks/vendors) to communicate. MAF ships an A2A package so your
agents can interoperate across systems, not just call functions within one
process.

**Q44. How are MAF agents hosted/deployed?**
As normal services: ASP.NET Core, Azure Functions, containers, or via Azure AI
Foundry Agent Service for managed/hosted agents. The same agent code runs locally
or hosted; you choose a chat client (e.g. a Foundry project client) accordingly.

**Q45. What is DevUI?**
A lightweight local developer UI for running and inspecting agents/workflows
during development — useful for stepping through tool calls and workflow events
without building your own front‑end.

---

## 8. Observability, evaluation & production

**Q46. How do you observe an agent in production?** *(→ ex 17)*
MAF is instrumented with **OpenTelemetry** using the `gen_ai` semantic
conventions. Call `configure_otel_providers(...)` + `enable_instrumentation()` and
every agent run, tool call, and workflow step emits spans/metrics/logs. Point an
exporter at the console (dev) or Jaeger/Azure Monitor/any OTLP backend (prod) to
get traces, latencies, and token usage.

**Q47. Why is observability non‑negotiable for agents?**
Agents are non‑deterministic and multi‑step. When something goes wrong you must
see *which* tool was called, with *what* arguments, how long each model call took,
token cost, and where it failed — to debug, control cost, and meet SLOs. Traces
turn a black box into something you can reason about.

**Q48. How do you test/evaluate agents?**
Unit‑test tools as plain functions; mock the model or tool layer with middleware
for deterministic tests; and use MAF's evaluation utilities (`evaluate_agent`,
`evaluate_workflow`, evaluators / checks like tool‑called and keyword checks) to
score behaviour against expectations. Combine with traces for regression
analysis.

**Q49. How do you control runaway loops / cost?**
Cap iterations (`max_iterations` on workflows, `max_rounds`/`max_round_count` on
group‑chat/Magentic), set token/temperature options, use middleware for
rate‑limiting and budget enforcement, and gate dangerous/expensive tools behind
approval. Always bound autonomous loops.

---

## 9. Design judgement / scenario questions

**Q50. "Build a customer‑support bot that routes billing vs technical and asks a
human before issuing refunds." Which MAF pieces?**
Use a **Handoff** orchestration (triage → billing/tech). Make refunds a tool with
`approval_mode="always_require"` (or model it as a workflow `request_info` step) so
a human approves before money moves. Attach a **session** per customer for
context, **context providers** for the customer's account data, **middleware** for
logging/PII redaction, and **OpenTelemetry** for traces. Add **checkpointing** so
a pending refund approval survives restarts.

**Q51. "Summarize 50 documents, fact‑check, then write a report." Which pattern?**
A **workflow**: fan‑out the documents to parallel summarizer executors (ex 14),
fan‑in to a fact‑checker agent, then a writer agent node produces the report;
gate the final publish behind a human `request_info` approval. Use concurrent
fan‑out for throughput and the graph for the dependency between stages.

**Q52. When would you NOT use MAF / an agent at all?**
If the task is a single deterministic transform or a simple one‑shot prompt with
no tools, memory, or branching, a plain model call (or even non‑LLM code) is
cheaper and more reliable. Agents shine when you need reasoning + action +
orchestration; don't add agentic machinery you don't need.

**Q53. How do you keep a multi‑agent system from being slow/expensive?**
Parallelize independent work (concurrent / fan‑out), use smaller/faster models for
simple steps and reserve large models for hard reasoning (model routing), cache
tool results via middleware, bound rounds/iterations, stream to improve perceived
latency, and watch token‑usage metrics in your traces to find hotspots.

**Q54. What's the single most important thing to remember about MAF versions?**
It evolves fast and **renames public types between minor versions** (e.g.
`ChatAgent`→`Agent`, `AgentThread`→`AgentSession`, orchestration moved to
`agent_framework.orchestrations`). Always pin the version, and recognise that the
*concepts* are stable even when the *names* shift.

---

### 60‑second whiteboard summary (memorize this)

> MAF is Microsoft's unified, provider‑agnostic SDK (Python + .NET) that merges
> Semantic Kernel and AutoGen. The atoms are **ChatClients** (model adapters) and
> **Agents** (model + instructions + tools + memory). Agents gain capabilities via
> **tools** (`@tool`, MCP), **sessions** (memory), **context providers** (RAG),
> **structured output** (Pydantic), and **middleware** (guardrails/observability).
> For many agents you pick an **orchestration** pattern — sequential, concurrent,
> group‑chat, handoff, or magentic — all of which compile to the **workflow
> engine**: a typed graph of executors and edges supporting branching, parallel
> fan‑out/fan‑in, **human‑in‑the‑loop** (`request_info`), and **durable
> checkpointing**. Everything is observable via **OpenTelemetry** and deployable
> from laptop to Azure AI Foundry, interoperating over **MCP** and **A2A**.
