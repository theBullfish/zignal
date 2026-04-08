# MCP Integration — Claude Code

## Setup

Run the MCP server:

```bash
python -m zignal.mcp_server
```

Or add it to Claude Code:

```bash
claude mcp add zignal -- python -m zignal.mcp_server
```

## Available Tools

The server exposes the full Zignal MCP toolset. Common entry points include:

- **zignal_status** — palace stats (wings, rooms, drawer counts)
- **zignal_search** — semantic search across all memories
- **zignal_list_wings** — list all projects in the palace

## Usage in Claude Code

Once configured, Claude Code can search your memories directly during conversations.
