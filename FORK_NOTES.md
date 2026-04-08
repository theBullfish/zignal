<div align="center">

# From MemPalace to Zignal

### How we got here, what we changed, and why

</div>

---

## The Short Version

[MemPalace](https://github.com/milla-jovovich/mempalace) by Milla Jovovich and Ben Sigman is brilliant. They built the highest-scoring AI memory system ever benchmarked — **96.6% on LongMemEval** — and open-sourced it. That takes guts and generosity.

We forked it because we needed something different. Not better at what MemPalace does — better at what *we* do.

We build hardware-software systems where an AI needs to remember six months of architecture decisions, track which FPGA build worked, know that a specific kernel flag crashes a specific card, and carry that knowledge across machines and sessions without losing nuance. MemPalace gave us the storage engine. We rebuilt the cognition layer on top of it.

**Zignal is MemPalace's retrieval engine + signal-chain cognition + trust-weighted knowledge.**

---

## Thank You

Milla and Ben — you built something real. The raw verbatim approach is correct. The palace metaphor is elegant. The local-first principle is non-negotiable. We kept all of that because it works.

You also did something rare in open source: when the community found problems in your claims, you [wrote an honest correction](https://github.com/milla-jovovich/mempalace#a-note-from-milla--ben--april-7-2026) within hours. That's integrity. We respect it.

MemPalace is MIT licensed. Zignal maintains MIT. Everything we build on your foundation stays open.

---

## What We Kept

These are the things MemPalace got right. We didn't touch them.

| Component | Why It Stays |
|---|---|
| **Raw verbatim storage** | The 96.6% score comes from keeping everything. No summarization, no extraction, no lossy compression. This is the right call. |
| **ChromaDB persistence** | Local vector store, no cloud dependency. Fast, embedded, battle-tested. |
| **SQLite knowledge graph** | Temporal triples with validity windows. Simple, portable, correct. |
| **Palace metaphor** | Wings, halls, rooms, drawers — it's intuitive and it maps cleanly to how humans organize knowledge. |
| **4-layer memory stack** | L0 identity → L1 essential → L2 on-demand → L3 deep search. Elegant context budgeting. |
| **Local-first principle** | Everything runs on your machine. Zero external APIs for core features. Non-negotiable. |
| **MCP server pattern** | 19-tool integration that works with Claude Code, and adaptable to any MCP client. |

---

## What We Changed

These are the places where our needs diverged from MemPalace's design.

### AAAK → Signal Notation

**MemPalace**: AAAK dialect — entity codes (`ALC=Alice`), emotion markers (`*warm*`), pipe-separated fields. Marketed as "30x lossless compression" but independently benchmarked at 84.2% vs raw mode's 96.6%. Lossy.

**Zignal**: [Signal Notation](https://github.com/theBullfish/zignal-notation) — a structured context format with modulation-weighted signal states, confidence scoring on every extraction, and trust weights that never reach 0 or 1. Compatible with `.zdx` module format. Honest about what it compresses and what it loses.

```
S:flow[0.70]--resonate-->clarity[0.85]--cascade-->momentum[0.90]
```

**Why**: We needed a format that could express *how confident* the system is about each piece of context, track emotional state transitions (not just labels), and integrate with our hardware description language. AAAK couldn't do that.

### Static Wings → Fuzzy Wing Vectors

**MemPalace**: A drawer belongs to one wing, assigned at mine time by keyword matching.

**Zignal**: A drawer gets a weight vector across all wings. A conversation about "TRISA running on Goya hardware" might be `{technical: 0.8, hardware: 0.6, identity: 0.2}`.

**Why**: Real knowledge doesn't fit in one box. Binary assignment forces false choices and loses cross-domain signal.

### Flat Emotions → Signal-Chain Modulations

**MemPalace**: Plutchik-derived emotion codes. A memory is tagged "happy" or "sad."

**Zignal**: Signal states with weights and modulation transitions. A memory encodes `fear[0.6]--invert-->hope[0.7]--resonate-->conviction[0.85]` — the *trajectory*, not just the endpoint.

**Why**: In our domain, the path matters more than the destination. A user going from confused to confident is different from a user who was always confident. The modulation captures that.

### BFS Traversal → Coherence-Weighted Signal Paths

**MemPalace**: Graph traversal uses breadth-first search. All edges are equal.

**Zignal**: Traversal follows signal strength. High-coherence paths are explored first. Cross-domain "tunnels" (rooms that span multiple wings) are weighted by how strongly they connect domains.

**Why**: When you're debugging a hardware issue that touches three different subsystems, you don't want BFS — you want the path that carries the most signal.

### No Confidence → Trust Weights Everywhere

**MemPalace**: Facts are stored. They're either there or not.

**Zignal**: Every triple in the knowledge graph carries a confidence score and a trust weight. Weights are asymptotic — they approach but never reach 0 or 1. This is Brad's Balance: nothing is ever absolutely certain, and nothing is ever completely dismissed.

**Why**: We work with hardware. Things we "know" turn out to be wrong. A fact extracted from a crashed kernel session should carry lower confidence than one from a clean test run. The system needs to know the difference.

### Immutable Drawers → Annotation Overlays

**MemPalace**: Drawers are write-once. The verbatim content is the only layer.

**Zignal**: The verbatim content is sacred and immutable. But we add an annotation overlay — interpretive notes, corrections, links — that sits on top without modifying the original.

**Why**: Six months from now, we might understand a conversation differently. The original words shouldn't change. The interpretation should evolve.

---

## Architecture Mapping

For contributors coming from MemPalace, here's how concepts translate:

| MemPalace | Zignal | Notes |
|---|---|---|
| Wing | Wing (fuzzy) | Now carries weight vectors, not binary assignment |
| Hall | Hall | Memory type classifier — unchanged |
| Room | Room | Addressing node — unchanged |
| Tunnel | Signal Path | Weighted by coherence instead of just existence |
| Drawer | Drawer + Overlay | Verbatim base + annotation layer |
| Closet | Drawer | Renamed for clarity |
| AAAK | [Signal Notation](https://github.com/theBullfish/zignal-notation) | Complete replacement |
| L0 Identity | L0 Root Constraint | Now enforces Brad's Balance trust model |
| L1 Essential | L1 Hot Path | Dynamically recomputes based on current focus |
| L2 On-Demand | L2 Path-Aware | Retrieval follows signal coherence, not flat search |
| L3 Search | L3 Trust-Weighted | Results ranked by trust weight × similarity |

---

## What's Next

Zignal is the memory layer for a larger system. It sits alongside:

- **CFA** (Codex Fractal Addressing) — the addressing scheme for navigating knowledge topology
- **TRISA** — delta-first preprocessing for hardware-accelerated inference
- **MDE** (Model Decomposition Engine) — structured decomposition of complex systems

These are separate projects under [NAC Research Foundation](https://github.com/theBullfish) / Codex Labs. Zignal is the piece that remembers.

---

<div align="center">

*If you're building on MemPalace — go use MemPalace. It's excellent.*
*If you need signal-chain cognition, trust-weighted knowledge, and hardware-aware context — come build with us.*

**[theBullfish/zignal](https://github.com/theBullfish/zignal)** · **[zignal-notation](https://github.com/theBullfish/zignal-notation)**

</div>
