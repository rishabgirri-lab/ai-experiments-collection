"""
run_all.py
==========
Runs all three frameworks on the SAME task so you can see them side by side,
then prints a decision guide. Works with zero setup (simulated output); add
OPENAI_API_KEY and install the frameworks for real runs.

    python run_all.py
"""

from __future__ import annotations

from shared import TOPIC, MODE, MODEL, banner, section
import crewai_pipeline
import langgraph_pipeline
import maf_pipeline


COMPARISON = """\
                 CrewAI                 LangGraph              MAF (Microsoft)
 mental model    a team of roles        a state machine        production agents +
                                        (nodes + edges)        typed orchestration
 control flow    sequential /           explicit graph:        sequential / concurrent /
                 hierarchical           branches + loops       handoff / group / magentic
 you write       roles, goals, tasks    state, nodes, edges    agents + workflow builder
 loops / retries awkward (use Flows)    native + easy          via workflow executors
 best for        fast role-based        branching, cycles,     enterprise, Py+.NET parity,
                 prototypes             human-in-the-loop      observability, governance
 lines to start  ~20                    ~45                    ~25
 ecosystem       standalone             LangChain              Azure / Microsoft
"""

DECISION = """\
PICK CrewAI when ...
  * the work is naturally "a team of specialists doing steps in order"
  * you want a working multi-agent prototype today, with minimal ceremony
  * the flow is linear or a manager-delegates-to-workers hierarchy

PICK LangGraph when ...
  * the flow branches, loops, retries, or routes on "it depends"
  * you need deterministic, debuggable control over every transition
  * you want durable state, checkpoints, or human-in-the-loop pauses
  * (in this repo, LangGraph is the one with the reviewer -> rewrite LOOP)

PICK MAF (Microsoft Agent Framework) when ...
  * you're in the Microsoft/Azure world or need Python + .NET parity
  * production matters: tracing (OpenTelemetry), middleware, governance,
    durable long-running workflows, enterprise support
  * you want typed orchestration patterns (handoff / concurrent / magentic)

Rule of thumb:
  CrewAI  = fastest to express collaboration
  LangGraph = most control over flow
  MAF     = most production/enterprise plumbing built in
"""


def main() -> None:
    banner("AI AGENT FRAMEWORKS COMPARED — CrewAI vs LangGraph vs MAF")
    print(f"Topic : {TOPIC}")
    print(f"Mode  : {MODE}   (model: {MODEL})")
    print("\n" + COMPARISON)

    banner("SAME TASK, THREE FRAMEWORKS")

    section("CrewAI  (role-based, sequential)")
    print(crewai_pipeline.run(TOPIC))

    section("LangGraph  (stateful graph, conditional revise loop)")
    print(langgraph_pipeline.run(TOPIC, verbose=True))

    section("MAF  (sequential ChatAgent chain)")
    print(maf_pipeline.run(TOPIC, verbose=True))

    banner("WHEN TO USE WHICH")
    print(DECISION)


if __name__ == "__main__":
    main()
