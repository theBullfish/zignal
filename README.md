<div align="center">

# Zignal

### Give your AI a memory. No API key required.

<br>

Every conversation you have with an AI disappears when the session ends. Months of decisions, debugging sessions, architecture debates — gone. You start over every time.

Zignal fixes this. **Store everything verbatim. Make it findable. Let the AI remember.**

Built on the palace metaphor: wings (domains), rooms (ideas), drawers (content). Raw verbatim storage in ChromaDB with semantic search. A temporal knowledge graph for structured facts. Signal-chain-aware notation for compressed context transfer between sessions.

**Local-first. No cloud. No subscription. No data leaves your machine.**

<br>

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-3.0.0-orange.svg)](https://github.com/theBullfish/zignal/releases)

<br>

[Quick Start](#quick-start) · [Architecture](#architecture) · [Signal Notation](#signal-notation) · [MCP Tools](#mcp-tools) · [Benchmarks](#benchmarks) · [Lineage](#lineage)

</div>

---

## What's Different

Zignal is forked from [MemPalace](https://github.com/milla-jovovich/mempalace) — the highest-scoring AI memory system ever benchmarked (96.6% LongMemEval R@5). We kept the raw verbatim retrieval that earned that score. We rebuilt everything else.

| MemPalace | Zignal | Why |
|---|---|---|
| AAAK dialect (lossy, marketed as lossless) | [**Zignal Notation**](https://github.com/theBullfish/zignal-notation) | Signal-chain modulation weights, .zdx compatible, honest about what it is |
| Static binary wing assignment | **Fuzzy wing vectors** | A drawer can belong 0.7 to `technical` and 0.3 to `identity` |
| Flat Plutchik emotion codes | **Signal-chain emotion graph** | States modulate: `flow[0.7]--resonate-->clarity[0.85]` |
| BFS graph traversal | **Coherence-weighted signal paths** | Walks follow signal strength, not hop count |
| No confidence scoring | **Trust weights on everything** | Brad's Balance — nothing reaches 0 or 1, all weights asymptotic |
| Immutable drawers | **Annotation overlays** | Interpret without corrupting the verbatim original |
| Static L1 context | **Dynamic L1** | Essential story recomputes based on current focus |

---

## Quick Start

```bash
# One command
curl -fsSL https://raw.githubusercontent.com/theBullfish/zignal/main/setup.sh | bash

# Or manually
git clone https://github.com/theBullfish/zignal.git ~/zignal
cd ~/zignal
pip install -e ".[dev]"
signal init ~/projects/my-app
signal mine ~/projects/my-app
signal search "why did we switch to GraphQL"
```

### Claude Code MCP Integration

```bash
claude mcp add zignal -- python -m zignal.mcp_server
```

Or add to `~/.claude.json`:

```json
{
  "mcpServers": {
    "zignal": {
      "command": "python",
      "args": ["-m", "zignal.mcp_server"]
    }
  }
}
```

Once registered, Claude Code gets 19 tools: search, knowledge graph, diary, graph traversal, and more. See [MCP_SETUP.md](MCP_SETUP.md) for the full tool reference.

---

## Architecture

### The Palace

```
Palace
├── Wing (fuzzy domain — technical, identity, family, ...)
│   ├── Hall (memory type — facts, events, preferences, ...)
│   │   ├── Room (specific idea — gpu-pricing, auth-flow, ...)
│   │   │   ├── Drawer (verbatim content + annotation overlay)
│   │   │   └── Drawer
│   │   └── Room
│   └── Hall
└── Wing
```

**Drawers** store your actual text — no summarization, no extraction, no lossy compression. The 96.6% retrieval score comes from keeping everything and letting semantic search do its job.

**Wings** are fuzzy. A drawer about "TRISA running on Goya hardware" might weight `technical: 0.8, hardware: 0.6, identity: 0.2`. Not binary. Not forced into one box.

### 4-Layer Memory Stack

| Layer | What | Tokens | When |
|---|---|---|---|
| **L0** | Identity constraint | ~100 | Always loaded |
| **L1** | Essential story (dynamic) | ~600-900 | Session start |
| **L2** | On-demand path-aware retrieval | Variable | When asked |
| **L3** | Deep trust-weighted search | Variable | Deep recall |

### Knowledge Graph

Temporal triples with validity windows and trust weights:

```
Brad → founded → Codex Labs  [from: 2025-01, confidence: 0.95, trust: 0.82]
Goya HL-1000 → connects_via → TB4  [from: 2026-02, confidence: 0.90, trust: 0.75]
```

Facts can be invalidated, not deleted. The contradiction graph links what changed to why.

---

## Signal Notation

**[zignal-notation](https://github.com/theBullfish/zignal-notation)** — a model-agnostic structured context format. The AI's native tongue.

Any LLM reads it without a decoder. It encodes:

- **Signal states** with weights: `flow[0.70]`, `clarity[0.85]`, `resonance[0.60]`
- **Modulations** between states: `--resonate-->`, `--dampen-->`, `--invert-->`, `--cascade-->`
- **Confidence scoring** on every extraction (0.01–0.99)
- **Trust weight propagation** — asymptotic, never reaches 0 or 1
- **Flags**: ORIGIN, CORE, SENSITIVE, PIVOT, GENESIS, DECISION, TECHNICAL

```
SIG|0|Brad|2026-04-07|goya-discovery|TF0.50
ST|[technical:0.80,hardware:0.70,identity:0.20]
N:0|Brad,Goya|tensor,processor,delta|"The Goya HL-1000 is a complete tensor processor"|W0.85|C0.90
S:flow[0.70]--resonate-->clarity[0.85]--cascade-->momentum[0.90]
F:0|TECHNICAL
F:0|GENESIS
```

Replaces AAAK. Honest about compression trade-offs. Compatible with .zdx module format.

---

## MCP Tools

19 tools available to any MCP-compatible AI client:

### Read
| Tool | What |
|---|---|
| `zignal_status` | Palace overview — drawers, wings, rooms |
| `zignal_list_wings` | All wings with counts |
| `zignal_list_rooms` | Rooms within a wing |
| `zignal_get_taxonomy` | Full wing → room → count tree |
| `zignal_search` | Semantic search with optional filters |
| `zignal_check_duplicate` | Duplicate detection before filing |
| `zignal_traverse_graph` | Walk the palace graph from a room |
| `zignal_find_tunnels` | Cross-domain connections between wings |
| `zignal_graph_stats` | Palace graph statistics |

### Write
| Tool | What |
|---|---|
| `zignal_add_drawer` | File verbatim content into a wing/room |
| `zignal_delete_drawer` | Remove a drawer by ID |

### Knowledge Graph
| Tool | What |
|---|---|
| `zignal_kg_query` | Query entity relationships with time filtering |
| `zignal_kg_add` | Add a fact (subject → predicate → object) |
| `zignal_kg_invalidate` | Mark a fact as no longer true |
| `zignal_kg_timeline` | Chronological fact history |
| `zignal_kg_stats` | Knowledge graph statistics |

### Diary
| Tool | What |
|---|---|
| `zignal_diary_write` | Agent writes a session entry |
| `zignal_diary_read` | Read recent entries |

---

## Mining

```bash
# Mine a project directory
signal mine ~/projects/my-app

# Mine exported Claude/ChatGPT conversations
signal mine ~/exports/claude --mode convos

# Mine with a specific wing name
signal mine ~/projects/trisa --wing trisa

# Split mega-files first if needed
signal split ~/exports/claude
signal mine ~/exports/claude --mode convos
```

---

## Benchmarks

Zignal inherits MemPalace's raw-mode retrieval engine. Benchmark runners are in [`benchmarks/`](benchmarks/).

| Benchmark | Score | Mode | Notes |
|---|---|---|---|
| LongMemEval R@5 | **96.6%** | Raw verbatim | 500 questions, zero API calls |
| LoCoMo | See [results](benchmarks/BENCHMARKS.md) | Raw | Multi-session coherence |
| ConvoMem | See [results](benchmarks/BENCHMARKS.md) | Raw | Conversation-specific recall |

The 96.6% is from **raw verbatim mode** — no compression, no summarization. That's the foundation Zignal builds on. Signal notation and fuzzy wings are additive layers; raw retrieval is untouched.

---

## Lineage

Zignal is forked from **[MemPalace](https://github.com/milla-jovovich/mempalace)** by Milla Jovovich and Ben Sigman. MemPalace is MIT licensed. Zignal maintains MIT license.

We kept what works — raw verbatim storage, ChromaDB persistence, the palace metaphor, local-first principle. We rebuilt the context format, emotion model, wing assignment, graph traversal, and confidence system around signal-chain cognition and trust-weighted retrieval.

Full accounting of what changed: [FORK_NOTES.md](FORK_NOTES.md)

---

## Related

- **[zignal-notation](https://github.com/theBullfish/zignal-notation)** — Signal-chain context format for AI memory systems
- **[MemPalace](https://github.com/milla-jovovich/mempalace)** — The upstream project this was forked from

---

<div align="center">

**NAC Research Foundation / Codex Labs LLC**

*Store everything. Trust nothing absolutely. Let the signal find the path.*

</div>
