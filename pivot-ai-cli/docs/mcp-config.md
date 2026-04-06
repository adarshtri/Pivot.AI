# 🔌 MCP Server Configuration

Pivot.AI CLI uses a decentralized, multi-server architecture. Instead of hardcoding tools into the binary, it discovers them dynamically from any Model Context Protocol (MCP) compatible server.

## 📂 Configuration Path
Your skills registry is stored at:
`~/.pivot-ai/mcp.json`

The CLI creates a default version of this file on its first run.

---

## 🏗️ JSON Structure
The file contains an array of `servers`, where each server is defined by its name, command, and arguments.

```json
{
  "servers": [
    {
      "name": "pivot-core",
      "command": "pivot-mcp",
      "args": []
    },
    {
      "name": "filesystem-tools",
      "command": "python3",
      "args": ["/path/to/mcp/server.py"]
    }
  ]
}
```

### 🧩 Field Definitions
| Field | Type | Description |
| :--- | :--- | :--- |
| `name` | String | A unique identifier for the server (used in logs). |
| `command` | String | The binary or interpreter to execute (e.g., `python3`, `node`, `pivot-mcp`). |
| `args` | Array | Command-line arguments passed to the server to start it. |

---

## 🛠️ Adding New Skills
To add a new toolset to your Agent:
1.  Locate an MCP server (or build your own!).
2.  Add its execution command to the `servers` list in `mcp.json`.
3.  Restart `pivot-ai-cli`.
4.  The Agent will automatically perform a **Handshake** and **Discovery** to "learn" the new tools.

> [!TIP]
> You can test any MCP server independently by running its command in the terminal. If it starts without error and waits for input, it’s likely compatible with Pivot.AI!
