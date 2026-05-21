"""
Orchestrator — discovers A2A agents dynamically, asks Grok to build an
execution plan, then runs each step, piping each agent's output to the next.

Runs on http://localhost:8000
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
import asyncio
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from common.a2a_protocol import (
    AgentCard,
    call_agent,
    fetch_agent_card,
    grok_chat,
)

# === Registered agent endpoints ===
# Adding a new agent? Just spin up a server that serves /.well-known/agent.json
# and add its URL here. No other code change needed — the orchestrator will
# auto-discover its skills and the planner will start using it.
AGENT_REGISTRY: list[str] = [
    "http://localhost:8001",  # researcher
    "http://localhost:8002",  # writer
    "http://localhost:8003",  # critic
]

# Populated at startup. Maps agent name -> (url, AgentCard)
DISCOVERED: dict[str, tuple[str, AgentCard]] = {}


PLANNER_SYSTEM_PROMPT = """You are an orchestrator that plans how to fulfill a user request using a team of specialised agents.

You will be given:
  1. The list of available agents and their skills.
  2. The user's request.

You must output a JSON array describing the plan. Each element has:
  - "agent": the exact agent name from the available list
  - "input": the text to send to that agent

Rules:
  - Use the literal token <prev_output> inside an "input" field where you want the previous step's full output substituted in.
  - You may combine <prev_output> with extra instructions, e.g. "Critique the following article:\\n\\n<prev_output>"
  - Only use agent names from the available list. Do not invent agents.
  - Keep the plan minimal — use only the agents needed for the goal.
  - Output ONLY the JSON array. No prose, no markdown fences.

Example output:
[
  {"agent": "researcher", "input": "history of espresso machines"},
  {"agent": "writer", "input": "Write a short article based on these notes:\\n\\n<prev_output>"},
  {"agent": "critic", "input": "Critique this article:\\n\\n<prev_output>"}
]
"""


def build_agent_catalog() -> str:
    """Render the discovered agents into a string the planner LLM can read."""
    if not DISCOVERED:
        return "(no agents discovered)"
    lines = []
    for name, (_url, card) in DISCOVERED.items():
        lines.append(f"- {name}: {card.description}")
        for skill in card.skills:
            tags = ", ".join(skill.tags) if skill.tags else ""
            lines.append(f"    skill `{skill.id}` — {skill.description}  [tags: {tags}]")
    return "\n".join(lines)


def extract_json_array(text: str) -> list[dict[str, Any]]:
    """Robustly pull a JSON array out of the planner's response."""
    # Strip markdown code fences if the model added them
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)
    # Find the first [ ... ] block
    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    if not match:
        raise ValueError(f"Planner did not return a JSON array. Got:\n{text}")
    return json.loads(match.group(0))


async def plan_execution(user_goal: str) -> list[dict[str, str]]:
    catalog = build_agent_catalog()
    user_prompt = (
        f"AVAILABLE AGENTS:\n{catalog}\n\n"
        f"USER REQUEST:\n{user_goal}\n\n"
        f"Produce the JSON plan now."
    )
    # grok_chat is sync; run in thread so we don't block the event loop
    raw = await asyncio.to_thread(grok_chat, PLANNER_SYSTEM_PROMPT, user_prompt, 0.2)
    plan = extract_json_array(raw)
    # Validate agent names
    for step in plan:
        if step.get("agent") not in DISCOVERED:
            raise ValueError(
                f"Planner referenced unknown agent '{step.get('agent')}'. "
                f"Known: {list(DISCOVERED)}"
            )
    return plan


async def execute_plan(plan: list[dict[str, str]]) -> dict[str, Any]:
    """Run each step, piping <prev_output> from the previous result."""
    transcript: list[dict[str, str]] = []
    prev_output = ""

    for i, step in enumerate(plan, start=1):
        agent_name = step["agent"]
        input_template = step["input"]
        resolved_input = input_template.replace("<prev_output>", prev_output)

        url, _card = DISCOVERED[agent_name]
        print(f"\n[orchestrator] step {i}: calling '{agent_name}' at {url}")
        print(f"[orchestrator]   input preview: {resolved_input[:120]}...")

        output = await call_agent(url, resolved_input)
        print(f"[orchestrator]   <- {len(output)} chars from {agent_name}")

        transcript.append({
            "step": str(i),
            "agent": agent_name,
            "input": resolved_input,
            "output": output,
        })
        prev_output = output

    return {"final_output": prev_output, "transcript": transcript}


# ---------- FastAPI app ----------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("\n[orchestrator] discovering registered agents...")
    for url in AGENT_REGISTRY:
        try:
            card = await fetch_agent_card(url)
            DISCOVERED[card.name] = (url, card)
            print(f"[orchestrator]   ✓ {card.name} @ {url} — skills: "
                  f"{[s.id for s in card.skills]}")
        except Exception as e:
            print(f"[orchestrator]   ✗ {url} unreachable: {e}")
    if not DISCOVERED:
        print("[orchestrator] WARNING: no agents discovered. "
              "Start the agent servers first.")
    yield


app = FastAPI(title="A2A Orchestrator", lifespan=lifespan)


class RunRequest(BaseModel):
    goal: str


async def _discover_now() -> None:
    """Re-discover on demand (e.g. if agents started after the orchestrator)."""
    for url in AGENT_REGISTRY:
        try:
            card = await fetch_agent_card(url)
            DISCOVERED[card.name] = (url, card)
        except Exception:
            pass


@app.get("/")
def root():
    return {
        "service": "orchestrator",
        "discovered_agents": {
            name: {"url": url, "skills": [s.id for s in card.skills]}
            for name, (url, card) in DISCOVERED.items()
        },
    }


@app.get("/agents")
def list_agents():
    return {name: card.model_dump() for name, (_u, card) in DISCOVERED.items()}


@app.post("/run")
async def run(req: RunRequest):
    if not DISCOVERED:
        # try discovery again on demand
        await _discover_now()
    print(f"\n{'=' * 60}\n[orchestrator] new goal: {req.goal}\n{'=' * 60}")
    plan = await plan_execution(req.goal)
    print(f"[orchestrator] plan ({len(plan)} steps):")
    for i, s in enumerate(plan, 1):
        print(f"  {i}. {s['agent']} <- {s['input'][:80]}...")
    result = await execute_plan(plan)
    return {"goal": req.goal, "plan": plan, **result}


if __name__ == "__main__":
    print("Orchestrator starting on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
