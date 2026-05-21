"""
Critic agent — reviews an article and suggests concrete improvements.
Runs on http://localhost:8003
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from common.a2a_protocol import AgentCard, AgentSkill, grok_chat, make_a2a_server

CARD = AgentCard(
    name="critic",
    description="Reviews written articles and gives concrete, actionable feedback.",
    url="http://localhost:8003",
    skills=[
        AgentSkill(
            id="critique_article",
            name="critique_article",
            description="Given an article, returns a short critique with "
                        "ratings on clarity, accuracy, and engagement, plus "
                        "2-4 concrete suggestions for improvement.",
            tags=["review", "critique", "feedback", "edit", "improve"],
        )
    ],
)

SYSTEM_PROMPT = (
    "You are a sharp but constructive editor. Review the article you receive "
    "and respond in this exact structure:\n\n"
    "STRENGTHS:\n  - <point>\n  - <point>\n\n"
    "WEAKNESSES:\n  - <point>\n  - <point>\n\n"
    "RATINGS (1-10):\n"
    "  Clarity: <n>\n  Accuracy: <n>\n  Engagement: <n>\n\n"
    "SUGGESTED IMPROVEMENTS:\n  1. <concrete suggestion>\n  2. <...>\n  3. <...>\n\n"
    "Be specific. Quote short phrases from the article when relevant. "
    "Do not rewrite the article."
)


def handle(text: str) -> str:
    print(f"\n[critic] received {len(text)} chars of input")
    out = grok_chat(SYSTEM_PROMPT, text, temperature=0.4)
    print(f"[critic] produced {len(out)} chars")
    return out


app = make_a2a_server(CARD, handle)


if __name__ == "__main__":
    print("Critic agent starting on http://localhost:8003")
    print("Agent card: http://localhost:8003/.well-known/agent.json")
    uvicorn.run(app, host="0.0.0.0", port=8003)
