# 🚀 Pivot.AI Agentic CLI: Documentation Overview

The Pivot.AI CLI is a powerful, decentralized **Career Intelligence Hub**. Unlike traditional tools, it uses a **"Plain-File Playbook"** architecture—meaning you can expand the Agent's skills and knowledge simply by editing Markdown files.

## 🏁 Getting Started
Start here to understand how to configure and run your personal AI Agent:

1.  **[MCP Server Configuration](mcp-config.md)**: How to connect the CLI to toolsets (Skills).
2.  **[Dynamic Resources (Knowledge Cache)](resources.md)**: How to give the Agent personal context using `~/.pivot-ai/resources/`.
3.  **[Dynamic SOPs (Standard Operating Procedures)](sops.md)**: How to define guided workflows using slash commands in `~/.pivot-ai/sops/`.

---

## 🛠️ The Trifecta of Agentic Power

| Feature | Concept | Analogy | Where to Edit |
| :--- | :--- | :--- | :--- |
| **Tools/Skills** | Executable Actions | **The Hands** | `~/.pivot-ai/mcp.json` |
| **Resources** | Searchable Knowledge | **The Memory** | `~/.pivot-ai/resources/` |
| **SOPs** | Guided Workflows | **The Playbook** | `~/.pivot-ai/sops/` |

---

## 💡 Troubleshooting & Tips
*   **Log Files**: All conversational history is stored in `~/.pivot-ai/sessions/` for your review.
*   **Tool Errors**: Use the `health_check` tool to verify your connection to the MCP backend.
*   **Variable Names**: In SOPs, always use `{{snake_case}}` for placeholders.

> [!TIP]
> This CLI is designed to evolve WITH your career. As you gain more skills or target new roles, simply update your Markdown files, and the Agent's intelligence will grow accordingly.
