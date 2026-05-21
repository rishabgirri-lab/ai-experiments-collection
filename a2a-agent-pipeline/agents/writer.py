"""
Writer agent — turns a research brief into a polished article.
Runs on http://localhost:8002
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import uvicorn
from common.a2a_protocol import AgentCard, AgentSkill, grok_chat, make_a2a_server

CARD = AgentCard(
    name="writer",
    description="Transforms a research brief or raw notes into a polished article.",
    url="http://localhost:8002",
    skills=[
        AgentSkill(
            id="write_article",
            name="write_article",
            description="Given a research brief, key facts, or raw notes, "
                        "produces a coherent, engaging short-form article "
                        "(150-250 words) with a clear intro, body, and closing line.",
            tags=["writing", "article", "compose", "narrative", "prose"],
        )
    ],
)

SYSTEM_PROMPT = (
    "You are a skilled non-fiction writer. Given research notes or a brief, "
    "produce a polished article of about 150-250 words. Requirements:\n"
    "  - Strong opening sentence that hooks the reader.\n"
    "  - 2-4 short paragraphs of flowing prose (NOT bullet points).\n"
    "  - Use the facts faithfully, but write in your own engaging voice.\n"
    "  - End with a closing line that resonates.\n"
    "Return ONLY the article text, no preface or meta-commentary."
)


def handle(text: str) -> str:
    print(f"\n[writer] received {len(text)} chars of input")
    out = grok_chat(SYSTEM_PROMPT, text, temperature=0.6)
    print(f"[writer] produced {len(out)} chars")
    return out


app = make_a2a_server(CARD, handle)


if __name__ == "__main__":
    print("Writer agent starting on http://localhost:8002")
    print("Agent card: http://localhost:8002/.well-known/agent.json")
    uvicorn.run(app, host="0.0.0.0", port=8002)
