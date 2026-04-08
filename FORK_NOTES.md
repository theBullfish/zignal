# Signal — Fork Notes

**Forked from:** [MemPalace](https://github.com/milla-jovovich/mempalace) by Milla Jovovich & Ben Sigman
**Fork date:** 2026-04-07
**Owner:** NAC Research Foundation / Codex Labs LLC
**Author:** Brad Svenson (@theBullfish)

## Lineage

Signal is inspired by and forked from MemPalace's architecture. The palace metaphor (wings/halls/rooms/drawers) is retained but rebuilt around CFA topology, signal-chain cognition, and trust-weighted retrieval.

MemPalace is MIT licensed. Signal maintains MIT license.

## What We Kept

- **ChromaDB persistence** — local vector store, no cloud dependency
- **SQLite knowledge graph** — temporal triples with validity windows
- **Palace metaphor** — wings/halls/rooms/drawers hierarchy
- **4-layer memory stack** — L0 identity, L1 essential, L2 on-demand, L3 deep search
- **Local-first principle** — everything runs on your machine, zero external APIs
- **MCP server foundation** — 19-tool integration pattern

## What We Gutted

| Component | Why |
|---|---|
| **AAAK dialect** | Lossy summarization marketed as lossless. Replaced with signal notation compatible with .zdx modules |
| **Static room detection** | Keyword-based (13 words = "technical"). Replaced with semantic clustering |
| **Static wing assignment** | Binary assignment at mine time. Replaced with fuzzy wing weight vectors |
| **Immutable drawers** | No annotation layer. Added overlay annotations that preserve verbatim original |
| **BFS traversal** | Unweighted graph walk. Replaced with signal-path-aware coherence-weighted traversal |
| **Flat emotion codes** | Plutchik derivatives, no modulation. Replaced with signal-chain emotion graph |

## What We Added

1. **Fuzzy wing vectors** — drawers get weight vectors across wings, not binary assignment
2. **Signal notation** — .zdx-compatible structured context format with modulation weights
3. **Confidence scoring** — every extraction tagged with reliability weight
4. **Annotation overlays** — interpretive layer over immutable drawers
5. **Signal-path traversal** — coherence-weighted graph walk, not BFS
6. **Retrieval feedback loop** — rate retrievals, system learns what matters
7. **Dynamic L1** — essential story recomputes based on current focus
8. **Trust weights** — Brad's Balance asymptotic trust on every triple
9. **Contradiction graph** — expired facts link to what contradicted them
10. **Adversarial context** — surface uncertainty alongside facts

## Architecture Mapping

| MemPalace | Signal | CFA Equivalent |
|---|---|---|
| Wing | Wing (fuzzy) | Domain topology |
| Hall | Hall | Memory type classifier |
| Room | Room | Addressing node |
| Tunnel | Signal Path | Crystallized cross-domain link |
| Drawer | Drawer + Annotation | Verbatim + interpretive overlay |
| AAAK | Signal Notation | .zdx state serialization |
| L0 Identity | L0 Root Constraint | Brad's Balance |
| L1 Essential | L1 Hot Path (dynamic) | Authenticated session context |
| L2 On-Demand | L2 Path-Aware | CFA path-filtered retrieval |
| L3 Search | L3 Trust-Weighted | Cold storage with auth gate |
