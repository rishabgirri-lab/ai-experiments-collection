"""
Custom Tools.
=============
Demonstrates the CrewAI custom tool pattern using BaseTool + a Pydantic
args schema. Tools let agents take ACTIONS beyond pure text generation.

Here we provide:
  - WordCountTool: deterministic utility (no LLM needed) to count words.
  - KeywordExtractorTool: simple frequency-based keyword extractor.

These are intentionally dependency-free so the project runs anywhere.
"""

import re
from collections import Counter
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.crew_demo.logger import get_logger

log = get_logger("tools")

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "is", "are", "was", "were", "to",
    "of", "in", "on", "for", "with", "as", "by", "at", "from", "this", "that",
    "it", "its", "be", "has", "have", "will", "can", "we", "you", "they",
}


class WordCountInput(BaseModel):
    text: str = Field(..., description="Text whose words should be counted.")


class WordCountTool(BaseTool):
    name: str = "word_counter"
    description: str = (
        "Counts the number of words in a piece of text. "
        "Input must be the text to analyze."
    )
    args_schema: Type[BaseModel] = WordCountInput

    def _run(self, text: str) -> str:
        count = len(text.split())
        log.info("WordCountTool invoked | words=%d", count)
        return f"The text contains {count} words."


class KeywordInput(BaseModel):
    text: str = Field(..., description="Text to extract keywords from.")
    top_n: int = Field(5, description="How many top keywords to return.")


class KeywordExtractorTool(BaseTool):
    name: str = "keyword_extractor"
    description: str = (
        "Extracts the most frequent meaningful keywords from text. "
        "Useful for SEO and summarization. Returns a comma-separated list."
    )
    args_schema: Type[BaseModel] = KeywordInput

    def _run(self, text: str, top_n: int = 5) -> str:
        words = re.findall(r"[a-zA-Z]{3,}", text.lower())
        filtered = [w for w in words if w not in _STOPWORDS]
        common = Counter(filtered).most_common(top_n)
        keywords = ", ".join(w for w, _ in common) or "none found"
        log.info("KeywordExtractorTool invoked | keywords=%s", keywords)
        return f"Top keywords: {keywords}"
