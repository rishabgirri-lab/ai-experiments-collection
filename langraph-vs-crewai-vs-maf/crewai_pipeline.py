"""
crewai_pipeline.py
==================
CrewAI's mental model: a CREW of role-playing agents.

You describe each agent the way you'd describe a teammate — a role, a goal,
and a backstory — hand them tasks, and let the framework run them as a
process (sequential here). You do NOT wire up a graph or manage state by
hand; CrewAI infers the flow from the task order and `context` links.

WHEN CREWAI SHINES
------------------
* You can frame the work as "a team of specialists collaborating."
* You want to go from idea to working multi-agent prototype in ~20 lines.
* The flow is mostly linear or hierarchical (a manager delegating).
* You value readable, role-based prompts over explicit control flow.

WHERE IT FIGHTS YOU
-------------------
* Complex branching, loops, or "go back and redo step 2" logic — Crews are
  not graphs. (CrewAI's separate `Flows` API exists for that, but then you're
  writing control flow anyway.)
* Fine-grained, deterministic control over every transition.

Run real:   pip install crewai && export OPENAI_API_KEY=sk-...  &&  python crewai_pipeline.py
Run mock:   python crewai_pipeline.py        # no key needed, prints a simulation
"""

from __future__ import annotations

from shared import TOPIC, CREWAI_LLM, HAS_LLM, banner, llm_complete


def run(topic: str = TOPIC, verbose: bool = False) -> str:
    """Research -> write -> review using a CrewAI sequential crew."""
    try:
        from crewai import Agent, Task, Crew, Process
    except Exception:
        return _simulate(topic, reason="crewai not installed")

    if not HAS_LLM:
        return _simulate(topic, reason="no API key set")

    # ---- Real CrewAI ----
    # Agents are defined by persona; the LLM string is routed via LiteLLM.
    researcher = Agent(
        role="Research Analyst",
        goal=f"Surface the key facts about {topic}",
        backstory="You distill messy topics into a handful of sharp, factual bullets.",
        llm=CREWAI_LLM,
        allow_delegation=False,
        verbose=verbose,
    )
    writer = Agent(
        role="Technical Writer",
        goal="Turn research into a tight ~150 word article",
        backstory="You write clearly and never pad. No headings, no fluff.",
        llm=CREWAI_LLM,
        allow_delegation=False,
        verbose=verbose,
    )
    editor = Agent(
        role="Editor",
        goal="Judge whether the article is clear and accurate",
        backstory="You are strict and concise.",
        llm=CREWAI_LLM,
        allow_delegation=False,
        verbose=verbose,
    )

    # Tasks. `context=[...]` feeds an upstream task's output into the next.
    research_task = Task(
        description=f"Research: {topic}. Produce 4-6 terse factual bullets.",
        expected_output="A short bulleted list of facts.",
        agent=researcher,
    )
    write_task = Task(
        description="Write a ~150 word article from the research.",
        expected_output="A single tight paragraph (~150 words).",
        agent=writer,
        context=[research_task],
    )
    review_task = Task(
        description="Review the article. Reply 'APPROVE' or 'REVISE: <fix>'.",
        expected_output="One line verdict.",
        agent=editor,
        context=[write_task],
    )

    crew = Crew(
        agents=[researcher, writer, editor],
        tasks=[research_task, write_task, review_task],
        process=Process.sequential,  # tasks run top-to-bottom; output chains forward
        verbose=verbose,
    )
    result = crew.kickoff(inputs={"topic": topic})
    return str(getattr(result, "raw", result))


def _simulate(topic: str, reason: str) -> str:
    """Pure-Python mirror of the crew's shape, so the file always runs.

    Note the structure: there is NO graph and NO shared state object. Each
    'agent' is just a role; output flows linearly from one to the next. That
    linearity IS the CrewAI sequential model.
    """
    print(f"[crewai] SIMULATION ({reason}) — install crewai + set a key for the real run.")
    research = llm_complete("researcher", f"Research: {topic}")
    draft = llm_complete("writer", f"Write a ~150 word article from:\n{research}")
    verdict = llm_complete("reviewer", f"Review this article:\n{draft}")
    print(f"[crewai] editor verdict: {verdict}")
    return draft


if __name__ == "__main__":
    banner("CrewAI — role-based crew, sequential process")
    print(run(verbose=True))
