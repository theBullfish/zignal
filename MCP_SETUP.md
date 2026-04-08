# Zignal MCP Setup for Claude Code

## Quick Setup (one command per machine)

```bash
curl -fsSL https://raw.githubusercontent.com/theBullfish/zignal/main/setup.sh | bash
```

Or clone and run manually:
```bash
git clone https://github.com/theBullfish/zignal.git ~/zignal
cd ~/zignal
pip install -e ".[dev]" --break-system-packages
zignal init ~/.zignal
claude mcp add zignal -- python -m zignal.mcp_server
```

## Manual MCP Config

If `claude mcp add` doesn't work, add this to `~/.claude.json`:

```json
{
  "mcpServers": {
    "zignal": {
      "command": "python",
      "args": ["-m", "zignal.mcp_server"],
      "env": {}
    }
  }
}
```

## Identity File

Edit `~/.zignal/identity.txt` — this is L0, always loaded (~100 tokens). Make it yours:

```
I am Blue, a distributed cognitive system for Brad Svenson.
Core: TRISA, MDE, CFA.
People: Brad (creator), Finnley (first use case).
Traits: signal-chain thinker, never linearize, match Brad's register.
Trust model: Brad's Balance — nothing reaches 0 or 1.
```

## Available MCP Tools

Once registered, Claude Code can use these tools in any session:

### Read Tools
| Tool | What it does |
|---|---|
| `zignal_status` | Palace overview — total drawers, wings, rooms |
| `zignal_list_wings` | All wings with drawer counts |
| `zignal_list_rooms` | Rooms within a wing |
| `zignal_get_taxonomy` | Full wing → room → count tree |
| `zignal_search` | Semantic search with optional wing/room filter |
| `zignal_check_duplicate` | Check if content already exists before filing |
| `zignal_traverse_graph` | Walk the palace graph from a room |
| `zignal_find_tunnels` | Find cross-domain connections between wings |
| `zignal_graph_stats` | Palace graph statistics |

### Write Tools
| Tool | What it does |
|---|---|
| `zignal_add_drawer` | File verbatim content into a wing/room |
| `zignal_delete_drawer` | Remove a drawer by ID |

### Knowledge Graph Tools
| Tool | What it does |
|---|---|
| `zignal_kg_query` | Query entity relationships with time filtering |
| `zignal_kg_add` | Add a fact (subject → predicate → object) |
| `zignal_kg_invalidate` | Mark a fact as no longer true |
| `zignal_kg_timeline` | Chronological fact history for an entity |
| `zignal_kg_stats` | Knowledge graph statistics |

### Diary Tools
| Tool | What it does |
|---|---|
| `zignal_diary_write` | Agent writes a diary entry |
| `zignal_diary_read` | Read recent diary entries |

## Mining Conversations

Export your Claude conversations from claude.ai (Settings → Export Data), then:

```bash
# Mine exported conversations
zignal mine ~/Downloads/claude-export --mode convos

# Mine a project directory
zignal mine ~/projects/mde-core

# Mine with a specific wing name
zignal mine ~/projects/trisa --mode convos --wing trisa
```

## Wake-Up (inject context into sessions)

```bash
# Full wake-up (L0 + L1)
zignal wake-up

# Project-specific wake-up
zignal wake-up --wing trisa

# Deep search
zignal search "crosspoint analog compute"
```

## Multi-Machine Sync

Zignal stores everything in `~/.zignal/` — SQLite + ChromaDB files. To sync across your Dell Precision and Blue Conductor:

Option A: Put `~/.zignal/` on a shared ZFS dataset
Option B: rsync periodically: `rsync -avz ~/.zignal/ blue-conductor:~/.zignal/`
Option C: Symlink to your blue-mind Optane pool when it's set up
