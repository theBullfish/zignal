# Contributing to Zignal

Welcome. Whether you're fixing a typo or adding a new retrieval strategy, we're glad you're here.

Zignal is forked from [MemPalace](https://github.com/milla-jovovich/mempalace) and maintained by [NAC Research Foundation](https://github.com/theBullfish) / Codex Labs. It's MIT licensed — your contributions stay open.

---

## Getting Started

```bash
git clone https://github.com/theBullfish/zignal.git
cd zignal
pip install -e ".[dev]"
pytest tests/ -v
```

All tests must pass. No API keys or network access required.

## Project Structure

```
zignal/             ← core package
├── cli.py          ← command-line interface
├── config.py       ← SignalConfig and palace paths
├── mcp_server.py   ← MCP tool definitions (19 tools)
├── miner.py        ← project file miner
├── convo_miner.py  ← conversation import miner
├── searcher.py     ← semantic search engine
├── knowledge_graph.py  ← temporal KG with trust weights
├── palace_graph.py     ← graph traversal and tunnels
├── layers.py       ← L0-L3 memory stack
├── entity_detector.py  ← entity extraction from text
├── room_detector_local.py  ← room detection from file structure
└── normalize.py    ← text normalization

benchmarks/         ← reproducible benchmark runners
tests/              ← test suite (pytest)
examples/           ← usage examples and tutorials
hooks/              ← Claude Code integration hooks
```

## How to Contribute

### Small Fixes

Just open a PR. Typos, docs, test coverage — no issue needed.

### New Features

Open an issue first. Describe what you want to build and why. We'll discuss the approach before you write code. This saves everyone time.

### Bug Reports

Include:
- What you expected
- What happened
- Steps to reproduce
- Python version and OS

## Pull Request Process

1. Fork and create a branch: `git checkout -b feat/my-thing`
2. Write code + tests
3. Run `pytest tests/ -v` — everything passes
4. Run `ruff check zignal/` — no lint errors
5. Commit with a clear message:
   - `feat: add Notion export format`
   - `fix: handle empty transcript files`
   - `docs: update MCP tool descriptions`
6. Open a PR against `main`

## Code Style

- **Formatter**: [Ruff](https://docs.astral.sh/ruff/) — 100-char line limit (configured in `pyproject.toml`)
- **Naming**: `snake_case` for functions/variables, `PascalCase` for classes
- **Type hints**: where they improve readability
- **Dependencies**: minimize. Don't add new deps without discussion.

## Design Principles

These are non-negotiable. PRs that violate them will be declined.

1. **Verbatim first** — Never summarize or extract from user content. Store exact words. The 96.6% score depends on this.

2. **Local first** — Everything runs on the user's machine. No cloud dependencies. No data leaving the box.

3. **Zero API by default** — Core features work without any API key. Period.

4. **Trust weights** — Nothing reaches 0 or 1. All confidence and trust values are asymptotic (Brad's Balance). If you're adding a scoring mechanism, it must follow this principle.

5. **Signal over noise** — Prefer coherence-weighted paths over exhaustive search. Quality of recall matters more than quantity.

## Good First Issues

Great places to start:

- **Chat formats** — Add import support for Cursor, Copilot, Gemini, or other AI tool exports
- **Room detection** — Improve semantic clustering in `room_detector_local.py`
- **Test coverage** — Especially `knowledge_graph.py`, `palace_graph.py`, and `layers.py`
- **Entity detection** — Better name disambiguation in `entity_detector.py`
- **Signal notation** — Improve extraction quality in [zignal-notation](https://github.com/theBullfish/zignal-notation)

## Related Projects

- **[zignal-notation](https://github.com/theBullfish/zignal-notation)** — The signal-chain context format. Contributions welcome there too.
- **[MemPalace](https://github.com/milla-jovovich/mempalace)** — The upstream project. If your contribution is to the raw retrieval engine, consider contributing upstream too.

## License

MIT. Your contributions are released under the same license.
