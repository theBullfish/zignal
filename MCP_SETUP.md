# Zignal MCP Setup

Connect Zignal to Claude Code (or any MCP-compatible AI client) and get 19 memory tools in every session.

---

## Quick Setup

```bash
# One command — installs Zignal and registers the MCP server
curl -fsSL https://raw.githubusercontent.com/theBullfish/zignal/main/setup.sh | bash
```

Or step by step:

```bash
git clone https://github.com/theBullfish/zignal.git ~/zignal
cd ~/zignal
pip install -e ".[dev]"
signal init ~/my-project        # detect rooms from your project structure
claude mcp add zignal -- python -m zignal.mcp_server
```

That's it. Open Claude Code — Zignal tools are now available.

---

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

### Remote Server Setup (SSH)

Run Zignal on a server and access it from your laptop:

```json
{
  "mcpServers": {
    "zignal": {
      "command": "ssh",
      "args": ["user@your-server", "python3 -m zignal.mcp_server"]
    }
  }
}
```

Requires SSH key authentication (no password prompts).

---

## Identity File

Edit `~/.signal/identity.txt` — this is **L0**, always loaded into every session (~100 tokens). Make it yours:

```
I am a research assistant for the Acme robotics team.
Core projects: perception pipeline, SLAM, motor control.
Team: Alice (lead), Bob (firmware), Carol (ML).
Style: precise, technical, cite sources.
```

Keep it short. This is the root constraint — who the AI is in your context.

---

## Available Tools

### Read Tools

| Tool | What It Does |
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

| Tool | What It Does |
|---|---|
| `zignal_add_drawer` | File verbatim content into a wing/room |
| `zignal_delete_drawer` | Remove a drawer by ID |

### Knowledge Graph Tools

| Tool | What It Does |
|---|---|
| `zignal_kg_query` | Query entity relationships with time filtering |
| `zignal_kg_add` | Add a fact (subject → predicate → object) |
| `zignal_kg_invalidate` | Mark a fact as no longer true |
| `zignal_kg_timeline` | Chronological fact history for an entity |
| `zignal_kg_stats` | Knowledge graph statistics |

### Diary Tools

| Tool | What It Does |
|---|---|
| `zignal_diary_write` | Agent writes a session entry |
| `zignal_diary_read` | Read recent diary entries |

---

## Mining Content

Before the AI can remember anything, you need to mine content into the palace:

```bash
# Mine a project directory (code, docs, notes)
signal mine ~/projects/my-app

# Mine exported AI conversations (Claude, ChatGPT)
signal mine ~/exports/claude --mode convos

# Mine with a specific wing name
signal mine ~/projects/robotics --wing robotics

# Split concatenated mega-files first if needed
signal split ~/exports/claude
signal mine ~/exports/claude --mode convos
```

### Exporting Conversations

- **Claude**: Settings → Export Data → download ZIP
- **ChatGPT**: Settings → Data controls → Export data

Unzip, then `signal mine <folder> --mode convos`.

---

## Wake-Up Context

Inject memory context into a new session:

```bash
# Full wake-up (L0 identity + L1 essential story)
signal wake-up

# Project-specific wake-up
signal wake-up --wing robotics

# Deep search
signal search "why did we switch from ROS1 to ROS2"
```

---

## Multi-Machine Sync

Zignal stores everything in `~/.signal/` — SQLite database + ChromaDB vector store. To sync across machines:

**Option A**: Shared network storage (NFS, ZFS dataset)
```bash
ln -s /mnt/shared/signal ~/.signal
```

**Option B**: Periodic rsync
```bash
rsync -avz ~/.signal/ server:~/.signal/
```

**Option C**: Git (for the knowledge graph only — not recommended for ChromaDB binary files)

The simplest reliable option is rsync on a cron job, or putting `~/.signal/` on shared storage.

---

## Troubleshooting

**"No palace found"** — Run `signal init <dir>` then `signal mine <dir>` to create and populate the palace.

**MCP server not appearing in Claude Code** — Restart Claude Code after adding the MCP config. Check `~/.claude.json` for syntax errors.

**ChromaDB segfault on macOS ARM64** — Known upstream issue. Pin `chromadb<0.6` or use `chroma-hnswlib` from conda-forge.

**Import errors** — Make sure `~/zignal` is on your Python path or installed with `pip install -e .`

---

## Related

- **[Zignal README](README.md)** — Full architecture and feature overview
- **[zignal-notation](https://github.com/theBullfish/zignal-notation)** — The signal-chain context format
- **[FORK_NOTES.md](FORK_NOTES.md)** — How Zignal differs from MemPalace
