# \# ai-experiments-collection

A hub for AI proof‑of‑concepts and experiments, showcasing diverse projects from RAG chatbots to agentic AI frameworks, AutoGen orchestration, and CrewAI collaboration. Designed as a sandbox for innovation, it provides modular, practical examples to explore the evolving landscape of intelligent systems



**# My POCs**



A collection of proof-of-concept projects exploring different AI and software ideas.



**## Projects**



\- \[`dynamic-agent-orchestrator/`](./dynamic-agent-orchestrator/) — Multi-agent LLM orchestration with dynamic agent selection.\n

\- \[`a2a-agent-pipeline/`] — Three specialised AI agents (Researcher → Writer → Critic) that discover each other via the A2A protocol, with Grok / Groq as the LLM backend. The orchestrator dynamically plans and chains agent output — each agent's response becomes the next agent's input — with no hard-coded execution order.

\- \[`langgraph-Concepts/`] — This is a runnable LangGraph concept map with 12 self-contained examples that demonstrate core graph patterns, state handling, routing, tools, checkpointing, and recovery. It is wired to Groq Llama inference via langchain-groq, logs each node execution, and prints the graph in ASCII/Mermaid form.



**## Layout**



Each subfolder is a self-contained project with its own README, dependencies, and setup instructions.

