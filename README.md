# \# ai-experiments-collection

A hub for AI proof‑of‑concepts and experiments, showcasing diverse projects from RAG chatbots to agentic AI frameworks, AutoGen orchestration, and CrewAI collaboration. Designed as a sandbox for innovation, it provides modular, practical examples to explore the evolving landscape of intelligent systems



**# My POCs**



A collection of proof-of-concept projects exploring different AI and software ideas.



**## Projects**



\- \[`dynamic-agent-orchestrator/`](./dynamic-agent-orchestrator/) — Multi-agent LLM orchestration with dynamic agent selection.\n

\- \[`a2a-agent-pipeline/`] — Three specialised AI agents (Researcher → Writer → Critic) that discover each other via the A2A protocol, with Grok / Groq as the LLM backend. The orchestrator dynamically plans and chains agent output — each agent's response becomes the next agent's input — with no hard-coded execution order.

\- \[`langgraph-Concepts/`] — This is a runnable LangGraph concept map with 12 self-contained examples that demonstrate core graph patterns, state handling, routing, tools, checkpointing, and recovery. It is wired to Groq Llama inference via langchain-groq, logs each node execution, and prints the graph in ASCII/Mermaid form.

\- \[`CrewAI-Concepts/`] — Lightweight prototype demonstrating CrewAI concepts: modular LLM-based agents, task orchestration, and custom tool integration. Includes example agents, task runners, logging, and configurable LLM settings to quickly prototype multi-agent workflows.

\- \[`MicrosoftAgentFramework_Concepts/`] — This repo contains example Python scripts demonstrating Microsoft Agent Framework concepts like agents, streaming, function tools, conversation memory, middleware, orchestration, workflow patterns, and observability. It is organized as a lightweight collection of runnable samples under examples plus setup info in README.md and requirements.txt.

\- \[`langraph-vs-crewai-vs-maf/`] — Three agent frameworks (CrewAI, LangGraph, MAF), one identical task, so the real differences in how they model agents and control flow stand out. Comes with a "when to use which" guide and runs out of the box in simulated mode — add a Groq or OpenAI key to run it live.


**## Layout**



Each subfolder is a self-contained project with its own README, dependencies, and setup instructions.

