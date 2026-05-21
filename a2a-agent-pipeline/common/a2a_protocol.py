"""
Minimal A2A-protocol-shaped helpers.

We follow the Agent2Agent protocol *shape*:
  - GET  /.well-known/agent.json   -> returns an Agent Card
  - POST /                         -> JSON-RPC 2.0 endpoint, method "message/send"

This avoids depending on the official a2a-sdk (which has had breaking parameter
changes between minor versions). Instead we implement just what is needed so the
demo is fully self-contained and runnable on any machine with Python 3.10+.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()

XAI_API_KEY = os.getenv("XAI_API_KEY", "")
GROK_MODEL = os.getenv("GROK_MODEL", "grok-4-fast")
XAI_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.x.ai/v1")


# ---------- LLM client ----------

def get_grok_client() -> OpenAI:
    """Grok is OpenAI-compatible — we just point the OpenAI SDK at api.x.ai."""
    if not XAI_API_KEY:
        raise RuntimeError(
            "XAI_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return OpenAI(api_key=XAI_API_KEY, base_url=XAI_BASE_URL)


def grok_chat(system_prompt: str, user_prompt: str, temperature: float = 0.4) -> str:
    """One-shot text completion via Grok."""
    client = get_grok_client()
    resp = client.chat.completions.create(
        model=GROK_MODEL,
        temperature=temperature,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return resp.choices[0].message.content or ""


# ---------- Agent Card ----------

class AgentSkill(BaseModel):
    id: str
    name: str
    description: str
    tags: list[str] = []


class AgentCard(BaseModel):
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    skills: list[AgentSkill]
    capabilities: dict[str, bool] = {"streaming": False}


# ---------- A2A server factory ----------

def make_a2a_server(card: AgentCard, handler) -> FastAPI:
    """
    Create a FastAPI app that exposes:
      GET  /.well-known/agent.json   -> the agent card
      POST /                          -> JSON-RPC message/send

    `handler` is a callable `(text_input: str) -> str` that runs the agent's logic.
    """
    app = FastAPI(title=card.name)

    @app.get("/.well-known/agent.json")
    def agent_card():
        return card.model_dump()

    # Health-check / convenience
    @app.get("/")
    def root():
        return {"agent": card.name, "ok": True, "card": "/.well-known/agent.json"}

    @app.post("/")
    async def jsonrpc(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse(
                {"jsonrpc": "2.0", "id": None,
                 "error": {"code": -32700, "message": "Parse error"}},
                status_code=400,
            )

        req_id = body.get("id")
        method = body.get("method")
        params = body.get("params") or {}

        if method != "message/send":
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        # A2A spec: params.message.parts[*].text
        message = params.get("message") or {}
        parts = message.get("parts") or []
        text_input = "\n".join(
            p.get("text", "") for p in parts if p.get("kind", "text") == "text"
        ).strip()

        if not text_input:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32602, "message": "No text input in message.parts"},
            }

        try:
            output_text = handler(text_input)
        except Exception as e:
            return {
                "jsonrpc": "2.0", "id": req_id,
                "error": {"code": -32000, "message": f"Agent error: {e}"},
            }

        # Return an A2A-shaped Message result
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "kind": "message",
                "messageId": str(uuid.uuid4()),
                "role": "agent",
                "parts": [{"kind": "text", "text": output_text}],
            },
        }

    return app


# ---------- A2A client helpers ----------

async def fetch_agent_card(base_url: str, timeout: float = 5.0) -> AgentCard:
    """Discover an agent by fetching its Agent Card."""
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{base_url.rstrip('/')}/.well-known/agent.json")
        r.raise_for_status()
        return AgentCard(**r.json())


async def call_agent(base_url: str, text: str, timeout: float = 120.0) -> str:
    """Send a text message to an A2A agent and return its text reply."""
    payload: dict[str, Any] = {
        "jsonrpc": "2.0",
        "id": str(uuid.uuid4()),
        "method": "message/send",
        "params": {
            "message": {
                "messageId": str(uuid.uuid4()),
                "role": "user",
                "parts": [{"kind": "text", "text": text}],
            }
        },
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.post(base_url.rstrip("/") + "/", json=payload)
        r.raise_for_status()
        data = r.json()

    if "error" in data:
        raise RuntimeError(f"Agent error: {data['error']}")

    result = data.get("result") or {}
    parts = result.get("parts") or []
    return "\n".join(
        p.get("text", "") for p in parts if p.get("kind", "text") == "text"
    ).strip()
