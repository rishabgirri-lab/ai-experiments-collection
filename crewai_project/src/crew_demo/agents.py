"""
Agents.
=======
An Agent is an autonomous unit with a role, goal, and backstory. These three
fields shape the system prompt the LLM receives, steering its behavior.

Key agent concepts shown here:
  - role / goal / backstory      -> identity and motivation
  - llm                          -> which model powers the agent (Grok / Groq)
  - tools                        -> actions the agent can take
  - allow_delegation             -> can it hand work to other agents
  - verbose                      -> stream reasoning to console
  - max_iter                     -> cap on reasoning loops (cost/safety)
"""

from crewai import Agent

from src.crew_demo.llm_config import get_grok_llm
from src.crew_demo.logger import get_logger
from src.crew_demo.tools import WordCountTool, KeywordExtractorTool

log = get_logger("agents")


def build_agents() -> dict[str, Agent]:
    """Create and return the set of agents used by the crew.

    We build FOUR specialists:
      - researcher       -> topic research
      - audience_analyst -> audience profiling (used by async mode for fan-out)
      - writer           -> drafts the article
      - editor           -> polishes + verifies length

    All modes share these agents. Hierarchical mode adds a separate manager
    (see crew.py) that is NOT included in this dict.
    """
    llm = get_grok_llm()
    log.info("Building agents...")

    researcher = Agent(
        role="Senior Research Analyst",
        goal="Uncover accurate, relevant, and current facts about {topic}.",
        backstory=(
            "You are a meticulous analyst known for distilling complex subjects "
            "into clear, well-organized findings. You never fabricate facts and "
            "you flag uncertainty when it exists."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )

    audience_analyst = Agent(
        role="Audience Insights Analyst",
        goal=(
            "Profile the target audience '{audience}' for an article about "
            "'{topic}': what they care about, their level of expertise, and the "
            "tone that will resonate with them."
        ),
        backstory=(
            "You are a content strategist who specializes in audience research. "
            "You produce concise audience profiles that writers can act on."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )

    writer = Agent(
        role="Technical Content Writer",
        goal="Craft an engaging, well-structured article about {topic} for {audience}.",
        backstory=(
            "You are an award-winning writer who turns raw research into compelling "
            "narratives. You adapt tone and complexity to the target audience and "
            "always lead with the most important insight."
        ),
        llm=llm,
        tools=[KeywordExtractorTool()],
        verbose=True,
        allow_delegation=False,
        max_iter=5,
    )

    editor = Agent(
        role="Managing Editor",
        goal="Ensure the final article is accurate, polished, and the right length.",
        backstory=(
            "You are a sharp-eyed editor who enforces clarity, correct grammar, "
            "and factual consistency. You use tools to verify length and keywords."
        ),
        llm=llm,
        tools=[WordCountTool(), KeywordExtractorTool()],
        verbose=True,
        allow_delegation=True,
        max_iter=5,
    )

    log.info("Built 4 agents: researcher, audience_analyst, writer, editor")
    return {
        "researcher": researcher,
        "audience_analyst": audience_analyst,
        "writer": writer,
        "editor": editor,
    }


def build_manager_agent() -> Agent:
    """Build a manager agent used by hierarchical mode.

    The manager is a separate, dedicated agent: it does not appear in the
    `agents` list passed to the Crew (CrewAI requires this — see crew.py).
    It is responsible for planning, delegating, and validating worker output.
    """
    llm = get_grok_llm()
    log.info("Building manager agent for hierarchical mode...")

    manager = Agent(
        role="Editorial Project Manager",
        goal=(
            "Coordinate the team to deliver a polished, audience-appropriate "
            "article about {topic} for {audience}. Delegate research, drafting, "
            "and editing to the right specialists, review their outputs, and "
            "send work back if it does not meet the bar."
        ),
        backstory=(
            "You are a seasoned editorial PM who has shipped hundreds of "
            "high-quality articles. You break work into clear sub-tasks, pick "
            "the right specialist for each, and ruthlessly enforce quality."
        ),
        llm=llm,
        verbose=True,
        allow_delegation=True,
        max_iter=10,
    )
    return manager
