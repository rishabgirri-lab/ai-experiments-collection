"""
Researcher agent — gathers facts on a topic using Grok.
Runs on http://localhost:8001
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from common.a2a_protocol import AgentCard, AgentSkill, grok_chat, make_a2a_server

CARD = AgentCard(
    name="researcher",
    description="Gathers facts, context, and key points on a given topic.",
    url="http://localhost:8001",
    skills=[
        AgentSkill(
            id="research_topic",
            name="research_topic",
            description="Given a topic, returns a structured bulleted list of "
                        "the most important facts, history, and current state.",
            tags=["research", "facts", "summarize", "background"],
        )
    ],
)

SYSTEM_PROMPT = (
    "You are a meticulous research assistant. Given a topic, produce a "
    "concise but information-dense brief in this format:\n"
    "  TOPIC: <one-line topic>\n"
    "  KEY FACTS:\n"
    "    - fact 1\n    - fact 2\n    ...\n"
    "  CONTEXT: <2-3 sentence background>\n"
    "  NOTABLE FIGURES / EVENTS: <bulleted list>\n"
    "Do not write a polished article — just the structured brief. "
    "Stick to widely-accepted information."
)


def handle(text: str) -> str:
    print(f"\n[researcher] received request: {text[:120]}...")
    out = grok_chat(SYSTEM_PROMPT, text, temperature=0.3)
    print(f"[researcher] produced {len(out)} chars")
    return out


app = make_a2a_server(CARD, handle)


if __name__ == "__main__":
    print("Researcher agent starting on http://localhost:8001")
    print("Agent card: http://localhost:8001/.well-known/agent.json")
    uvicorn.run(app, host="0.0.0.0", port=8001)
