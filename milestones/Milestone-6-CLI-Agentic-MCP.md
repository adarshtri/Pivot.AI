# Milestone 6: CLI-First Agentic Engine with MCP & Skills

## 🎯 Objective
Pivot the system from a multi-user web application to a personalized, single-user CLI tool. Introduce agentic AI capabilities using the Model Context Protocol (MCP), where the CLI acts as an agent that can discover and use "Skills" and "Tools" to manage the career intelligence pipeline.

## 🛠️ Strategic Pillars
1.  **Rust-Based CLI**: High-performance, memory-safe engine using `Clap` and `Tokio`.
2.  **Agentic AI & Sub-agents**: The CLI can spawn and manage multiple sub-agents for specialized tasks.
3.  **Unified Control**: CLI manages all admin and system settings (single-user focus).
4.  **Single-User Personalization**: Removal of multi-tenant complexity.
5.  **MCP Foundation**: Using MCP (in Rust) for tool and skill discovery/invocation.
6.  **Skill Support**: Modular, complex logic encapsulated as "Skills."
7.  **Agent Definitions**: Formalizing agent personalities, tools, and skills.
8.  **Repurposed Integrations**: Convert existing Python logic into MCP Tools.

## 🧱 Components to Build

### 1. The `pivot-ai-cli` (Rust)
- Initialize Rust project: `cargo init cli`.
- CLI structure with `clap` and async `tokio` support.
- Sub-agent spawning logic (Process/Thread management).

### 2. Python MCP Server
- Wrap existing Python logic in an MCP server.
- Expose `ingest`, `score`, and `match` as tools.

### 3. Agent Execution Engine
- Integration with an LLM (GPT-4 or Claude-3) to drive the CLI agent.
- Support for "Agent Definitions" (YAML-based).

### 4. Skills Library
- First set of skills: `AdvancedResumeTailoring`, `MarketPulse`, `AutoApply`.

## 🗓️ Expected Delivery
- A working `pivot` CLI that can run a full pipeline via natural language.
- A library of MCP tools and at least two functional "Skills."
- Transition from MongoDB-based settings to local, agent-managed configuration.

## 🚀 Vision Alignment
- **Agility**: CLI-first allows for faster iteration and direct automation.
- **Intelligence**: Agents with MCP tools make the system proactive rather than reactive.
- **Privacy/Personalization**: Single-user focus simplifies data handling and deepens personalization.
