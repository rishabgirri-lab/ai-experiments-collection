"""
Tasks.
======
Three task pipelines, one per mode:

  build_sequential_tasks()   -> research -> write -> edit
                                Tasks pinned to specific agents. Used by
                                Process.sequential.

  build_async_tasks()        -> [research_topic ║ research_audience]
                                          ↓ fan-in
                                       write -> edit
                                Two research tasks run in PARALLEL via
                                async_execution=True; writer waits for both
                                (via `context`) before drafting. Still uses
                                Process.sequential — parallelism is a Task-
                                level feature, not a Process type.

  build_hierarchical_tasks() -> research -> write -> edit
                                Tasks are NOT pinned to agents; the manager
                                LLM decides who does what at runtime.

All three exercise the same {topic} and {audience} placeholders injected by
crew.kickoff(inputs=...).
"""

from crewai import Agent, Task

from src.crew_demo.logger import get_logger

log = get_logger("tasks")


# ---------------------------------------------------------------------------
# SEQUENTIAL: classic pipeline, each task assigned to a specific agent.
# ---------------------------------------------------------------------------
def build_sequential_tasks(agents: dict[str, Agent]) -> list[Task]:
    log.info("Building SEQUENTIAL tasks (research -> write -> edit)...")

    research_task = Task(
        description=(
            "Research the topic: '{topic}'.\n"
            "Identify 5-7 key points, recent developments, and any important "
            "caveats. Organize findings as a concise bulleted brief."
        ),
        expected_output=(
            "A bulleted research brief with 5-7 key points about {topic}, "
            "each point one or two sentences."
        ),
        agent=agents["researcher"],
    )

    writing_task = Task(
        description=(
            "Using the research brief, write a ~400-word article about '{topic}' "
            "tailored to {audience}. Use a clear intro, body, and conclusion. "
            "You may use the keyword_extractor tool to check focus keywords."
        ),
        expected_output=(
            "A well-structured ~400-word article with a title, intro, body, "
            "and conclusion, appropriate for {audience}."
        ),
        agent=agents["writer"],
        context=[research_task],
    )

    editing_task = Task(
        description=(
            "Review and polish the article. Verify it reads well for {audience}, "
            "fix any grammar or clarity issues, and use the word_counter tool to "
            "confirm length is reasonable (300-500 words). Return the final, "
            "publication-ready article."
        ),
        expected_output=(
            "The final, polished article ready for publication, preceded by a "
            "one-line note stating the verified word count."
        ),
        agent=agents["editor"],
        context=[writing_task],
        output_file="logs/final_article_sequential.md",
    )

    return [research_task, writing_task, editing_task]


# ---------------------------------------------------------------------------
# ASYNC: fan-out two parallel research tasks, fan-in to the writer.
# ---------------------------------------------------------------------------
def build_async_tasks(agents: dict[str, Agent]) -> list[Task]:
    """Two research tasks run concurrently; writer waits on both.

    `async_execution=True` makes a task run on its own thread so multiple
    async tasks can be in flight at the same time. The next *synchronous*
    task blocks until all preceding async tasks finish, which is exactly the
    fan-in we want here.
    """
    log.info(
        "Building ASYNC tasks (parallel: topic + audience research, then write -> edit)..."
    )

    # --- Fan-out: these two run in parallel ---
    topic_research_task = Task(
        description=(
            "Research the topic: '{topic}'. Identify 5-7 key points, recent "
            "developments, and any important caveats."
        ),
        expected_output=(
            "A bulleted research brief with 5-7 key points about {topic}."
        ),
        agent=agents["researcher"],
        async_execution=True,  # <-- runs concurrently with the next async task
    )

    audience_research_task = Task(
        description=(
            "Profile the target audience: '{audience}'. Describe what they care "
            "about, their assumed background knowledge, common questions, and "
            "the tone that will resonate with them."
        ),
        expected_output=(
            "A short audience profile (5-8 bullets) covering interests, "
            "expertise level, common questions, and recommended tone."
        ),
        agent=agents["audience_analyst"],
        async_execution=True,  # <-- runs in parallel with the topic research
    )

    # --- Fan-in: sync task; CrewAI waits for BOTH async tasks above ---
    writing_task = Task(
        description=(
            "Combine the topic research and the audience profile to write a "
            "~400-word article about '{topic}' tailored to {audience}. Use a "
            "clear intro, body, and conclusion. Adapt tone based on the "
            "audience profile."
        ),
        expected_output=(
            "A well-structured ~400-word article with a title, intro, body, "
            "and conclusion, calibrated to {audience}."
        ),
        agent=agents["writer"],
        context=[topic_research_task, audience_research_task],
    )

    editing_task = Task(
        description=(
            "Review and polish the article. Use the word_counter tool to "
            "confirm length (300-500 words). Return the final article."
        ),
        expected_output=(
            "The final, polished article preceded by a one-line note stating "
            "the verified word count."
        ),
        agent=agents["editor"],
        context=[writing_task],
        output_file="logs/final_article_async.md",
    )

    return [topic_research_task, audience_research_task, writing_task, editing_task]


# ---------------------------------------------------------------------------
# HIERARCHICAL: NO agent= on the tasks; the manager picks who runs what.
# ---------------------------------------------------------------------------
def build_hierarchical_tasks() -> list[Task]:
    """Tasks for hierarchical mode are NOT pre-assigned to agents.

    The manager (configured on the Crew via `manager_agent` or `manager_llm`)
    reads each task and dynamically delegates it to the most appropriate
    worker based on role/goal/backstory.
    """
    log.info(
        "Building HIERARCHICAL tasks (manager will delegate at runtime)..."
    )

    research_task = Task(
        description=(
            "Research the topic '{topic}' and produce a concise bulleted brief "
            "with 5-7 key points. Also note who the audience is: {audience}."
        ),
        expected_output=(
            "A bulleted research brief with 5-7 key points about {topic}."
        ),
        # No agent= -> manager decides
    )

    writing_task = Task(
        description=(
            "Using the research brief, write a ~400-word article about '{topic}' "
            "tailored to {audience}. Clear intro, body, and conclusion."
        ),
        expected_output=(
            "A well-structured ~400-word article appropriate for {audience}."
        ),
        context=[research_task],
        # No agent= -> manager decides
    )

    editing_task = Task(
        description=(
            "Review and polish the article. Use the word_counter tool to "
            "confirm length (300-500 words). Return the final article."
        ),
        expected_output=(
            "The final, polished article preceded by a one-line note stating "
            "the verified word count."
        ),
        context=[writing_task],
        output_file="logs/final_article_hierarchical.md",
        # No agent= -> manager decides
    )

    return [research_task, writing_task, editing_task]
