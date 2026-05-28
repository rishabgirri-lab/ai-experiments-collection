# LangGraph Interview Concepts

A focused study guide that pairs with the runnable examples in this repo. Each
section gives the **mental model**, the **why**, and the **gotcha** — the things
interviewers actually probe. Code references point to the matching `eNN` file.

---

## 1. What is LangGraph, and why not just LangChain chains (LCEL)?

**Mental model:** LangGraph models an application as a **directed graph** of
nodes that share a **typed state**, executed by a Pregel-style engine. A LangChain
LCEL chain is a **DAG of transforms** — linear data flow, no native loops, no
shared mutable state, no built-in persistence.

**Use LangGraph when you need:** cycles (agent ↔ tools loops), branching on
model output, shared state across steps, persistence/memory, human-in-the-loop,
or long-running/durable execution. **Use a plain chain when** the flow is a
straight pipeline with no loops or pausing.

**One-liner:** *Chains are for pipelines; graphs are for agents and stateful
workflows.*

---

## 2. State, nodes, and edges (`e01`)

- **State** is a schema (usually a `TypedDict`) — the single shared object every
  node reads from and writes to.
- **Node** is a function `state -> partial-update-dict`. It returns only the keys
  it changes; LangGraph merges that into the state.
- **Edge** decides what runs next. **Normal** edges are deterministic
  (`add_edge`); **conditional** edges call a router (`add_conditional_edges`).
- **`START` / `END`** are sentinels for entry and exit.
- You must **`.compile()`** the builder before running — compile does validation
  (connectivity, reducer/channel setup) and injects the checkpointer.

**Gotcha:** nodes return **partial** updates, not the whole state. Returning the
full state isn't required and can clobber other keys if you're not careful.

---

## 3. Reducers — the most misunderstood concept (`e03`)

**Default behaviour:** a node returning `{"k": v}` **overwrites** `state["k"]`.

A **reducer** changes how an update is *merged* with the existing value. You
attach it in the schema with `Annotated`:

```python
log: Annotated[list[str], operator.add]   # concatenate instead of overwrite
messages: Annotated[list, add_messages]    # append + de-dupe by message id
```

**Why it matters:** two reasons —
1. **Accumulation** (chat history grows instead of being replaced).
2. **Parallelism** — when multiple nodes write the same key in one super-step,
   the reducer is the *merge rule*. Without it you get `InvalidUpdateError`.

**`add_messages`** is the special reducer behind `MessagesState`. It appends new
messages and de-duplicates by message ID (so re-emitting a message updates it
rather than duplicating).

**Interview trap:** "Why did my parallel nodes crash with InvalidUpdateError?"
→ Two writers to one key with no reducer.

---

## 4. Super-steps & parallelism (`e04`)

LangGraph executes in discrete **super-steps** (Pregel/BSP model). All nodes
that are runnable at the same time execute **in parallel** within one super-step.
A node with multiple parents waits until **all** parents finish (fan-in barrier).

- **Fan-out:** multiple edges leaving one node → those targets run in parallel.
- **Fan-in:** multiple edges into one node → it runs once, after all complete.
- Concurrent writes to a shared key **require a reducer** (see §3).

---

## 5. Conditional edges & routing (`e02`)

```python
builder.add_conditional_edges("classify", route, {"math": "math", ...})
```

- The **router** reads state and returns a **key** (or a node name, or a list of
  `Send`s). It must **not** mutate state.
- The **path_map** maps router output → next node. Values must be real node names.
- This is how you build branches, retries, and "the agent decides" behaviour.

---

## 6. Tool calling & the ReAct loop (`e05`, `e12`)

**ReAct = Reason + Act.** The model alternates between thinking and calling
tools until it can answer.

- `@tool` turns a Python function into a tool; its **docstring + type hints**
  become the schema the model sees. Write them well — the model chooses tools by
  these descriptions.
- `llm.bind_tools(tools)` lets the model emit **tool calls** in its `AIMessage`.
- `ToolNode(tools)` is a prebuilt node that executes whatever the model
  requested and appends `ToolMessage`s back to state.
- `tools_condition` is a prebuilt router: → `"tools"` if there are tool calls,
  else `END`.
- The **cycle** `agent → tools → agent` is what makes this a graph; a chain can't
  express the loop.

**Two levels to know:**
- **Low-level** `StateGraph` (build the loop yourself) — full control.
- **High-level** `create_react_agent(model, tools)` — one line, sensible defaults.
Interviewers like: *"When would you drop from `create_react_agent` to raw
`StateGraph`?"* → When you need custom routing, extra nodes (guardrails,
reflection), custom state, or non-standard control flow.

---

## 7. Persistence, checkpointers, threads & memory (`e06`)

A **checkpointer** snapshots state after **every super-step**. This one feature
unlocks: memory, durable execution, human-in-the-loop, and time travel.

- **`thread_id`** (in `config["configurable"]`) identifies an independent
  conversation/run. Same graph + different `thread_id` = isolated memories.
- **Savers:** `MemorySaver` (RAM, dev/tests) → `SqliteSaver` (durable, single
  process) → `PostgresSaver` (production, multi-instance / horizontal scaling).
- **Short-term vs long-term memory:** the checkpointer is **short-term**
  (thread-scoped state). For **long-term**, cross-thread memory (facts about a
  user across conversations), LangGraph provides the **Store** (`BaseStore`),
  which is separate from checkpointing.
- `get_state(config)` reads the current snapshot (`.values`, `.next`).

**Gotcha:** human-in-the-loop and time travel **require** a checkpointer.

---

## 8. Human-in-the-loop (`e07`)

```python
decision = interrupt({"draft": draft})       # pauses, surfaces payload
...
graph.invoke(Command(resume="approve"), cfg) # re-enters the node; interrupt() returns "approve"
```

- `interrupt(payload)` **pauses** the graph and returns control to your app; the
  paused state is checkpointed.
- `Command(resume=value)` **resumes**: the node re-executes and `interrupt()` now
  **returns** `value` instead of pausing.
- Patterns: **approve / reject / edit** before irreversible actions; collecting
  missing input mid-run.

**Gotcha:** the node containing `interrupt()` runs again from the top on resume,
so keep side effects after the interrupt, not before.

---

## 9. Time travel (`e08`)

- `get_state_history(config)` yields every past checkpoint (newest first); each
  has `.values`, `.next`, and a `.config` carrying a `checkpoint_id`.
- **Replay:** invoke with an old checkpoint's config to re-run from that point.
- **Fork:** `update_state(old_config, new_values)` writes a *new* checkpoint —
  an alternate timeline branching from the past one. The original is untouched.

**Why interviewers care:** it's the debugging superpower — "what did state look
like right before the agent went wrong, and what if I change X and rerun?"

---

## 10. Structured output (`e09`)

`llm.with_structured_output(PydanticModel)` forces the model to emit data that
matches your schema, validated by Pydantic. Inside a graph, one node emits clean
typed fields that routers and downstream nodes can rely on, instead of parsing
free text. Use `Literal`/enums to constrain choices and `Field(description=...)`
to guide extraction.

---

## 11. Subgraphs & composition (`e10`)

A compiled graph can be used **as a node** in a parent graph.

- **Shared state:** if parent and subgraph share state keys, add the compiled
  subgraph directly as a node — state flows through.
- **Different state:** wrap the subgraph in a function node that translates the
  parent's state to the subgraph's input and back (the decoupled, reusable
  style).

Benefits: encapsulation, reuse, independent testing, and multi-agent
architectures (each agent is a subgraph).

---

## 12. The Send API — dynamic map-reduce (`e11`)

When the number of parallel branches is **unknown until runtime**, a routing
function returns a **list of `Send` objects**:

```python
return [Send("summarize_one", {"document": d}) for d in state["documents"]]
```

- Each `Send` invokes the target node with its **own isolated payload** (its own
  state slice).
- Results merge back via a **reducer** on the shared key.
- This is the canonical **map (per-item) → reduce (aggregate)** pattern, e.g.
  "summarize each of N documents, then combine."

**Contrast with §4:** plain parallel edges = *fixed* fan-out; `Send` = *dynamic*
fan-out.

---

## 13. Streaming modes (`e12`)

`graph.stream(input, config, stream_mode=...)`:

- `"updates"` — the **delta** each node produces (good for logging/progress).
- `"values"` — the **full state** after each step.
- `"messages"` — **token-by-token** LLM output (good for chat UIs).
- `"custom"` — values you emit yourself via a stream writer.

You can pass a list of modes to get several at once.

---

## 14. Reliability: recursion, retries, errors

- **Recursion limit:** cyclic graphs stop after `recursion_limit` super-steps
  (default **25**) to prevent infinite loops. Override per-run:
  `config={"recursion_limit": 50}`. A `GraphRecursionError` means the loop never
  hit its exit condition.
- **Retries:** attach a `retry_policy` per node (or as a graph default) to retry
  transient failures (e.g. network/tool errors).
- **Timeouts:** per-node `timeout`. **Caching:** per-node `cache_policy` to skip
  recomputation of identical inputs.
- **Durable resume after failure (`e13`):** with a checkpointer, state is saved
  after every successful super-step. If a node raises, the graph stops but the
  last good checkpoint survives. Re-invoking the same `thread_id` with
  `invoke(None, cfg)` resumes from the pending (failed) node — earlier completed
  nodes do NOT re-run. Check `get_state(cfg).next` to see which node is pending.
  **Key subtlety:** resume is at the super-step boundary, so the failed node
  re-runs *from its start*, not from the exact line that threw. Therefore nodes
  should be **idempotent** (safe to re-run) — put irreversible side effects where
  a re-run won't duplicate them. This is also why `retry_policy` works: a retry
  is just re-running the node from the top.

---

## 15. Quick-fire Q&A

**Q: Node returns `{"messages": [msg]}` but history keeps getting wiped. Why?**
A: The `messages` key has no `add_messages` reducer, so each write overwrites.

**Q: Difference between `MemorySaver` and `SqliteSaver`/`PostgresSaver`?**
A: `MemorySaver` is in-RAM (lost on restart) — dev only. The others persist to
disk/DB, enabling durable execution and multi-instance scaling.

**Q: How does a graph "decide" what runs next?**
A: Normal edges (static) or conditional edges (a router function reads state and
returns the next node / a key / a list of `Send`s).

**Q: `create_react_agent` vs raw `StateGraph`?**
A: Prebuilt = fast defaults for the standard agent loop. Raw = full control over
state, routing, and extra nodes. Start prebuilt; drop down when you outgrow it.

**Q: What makes human-in-the-loop possible?**
A: Checkpointing. `interrupt()` pauses and persists state; `Command(resume=...)`
continues from the exact checkpoint.

**Q: Why did parallel nodes raise `InvalidUpdateError`?**
A: Multiple nodes wrote the same state key in one super-step with no reducer to
merge them.

**Q: Short-term vs long-term memory in LangGraph?**
A: Short-term = checkpointer (thread-scoped state). Long-term = the Store
(`BaseStore`), cross-thread, for durable user/app facts.

**Q: What execution model does LangGraph use?**
A: Pregel / bulk-synchronous-parallel "super-steps": gather runnable nodes →
run them (in parallel) → apply updates via channels/reducers → repeat.

**Q: A node crashed halfway through a graph. Do I have to start over?**
A: No — if a checkpointer is attached, state is saved after each successful
super-step. Re-invoke the same `thread_id` with `invoke(None, cfg)` and it
resumes from the failed node; already-completed nodes don't re-run. But the
failed node re-runs *from its start* (resume is at the super-step boundary, not
mid-node), so nodes must be idempotent. See example `e13`.
