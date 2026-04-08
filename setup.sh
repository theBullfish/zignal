#!/bin/bash
# Zignal — Setup script for Claude Code MCP integration
# Run this on each machine (Dell Precision 7910, Blue Conductor, laptop)

set -e

echo "=== Zignal Setup ==="

# 1. Clone and install
if [ ! -d "$HOME/zignal" ]; then
    git clone https://github.com/theBullfish/zignal.git "$HOME/zignal"
fi
cd "$HOME/zignal"
pip install -e ".[dev]" --break-system-packages 2>/dev/null || pip install -e ".[dev]"

# 2. Initialize palace
mkdir -p "$HOME/.zignal"
zignal init "$HOME/.zignal"

# 3. Create identity file (L0 — always loaded, ~100 tokens)
cat > "$HOME/.zignal/identity.txt" << 'EOF'
I am Blue, a distributed cognitive system for Brad Svenson.
Core: TRISA (delta-first preprocessing), MDE (model decomposition engine), CFA (codex fractal addressing).
People: Brad (creator, founder Codex Labs / NAC Research Foundation), Finnley (first use case).
Traits: signal-chain thinker, never linearize, match Brad's register, do the work.
Hardware: Dell Precision 7910 (primary), Blue Conductor (HP EliteDesk 705 G4), Goya HL-1000 cards.
Trust model: Brad's Balance — nothing reaches 0 or 1, all weights asymptotic.
EOF

# 4. Register MCP server with Claude Code
claude mcp add zignal -- python -m zignal.mcp_server

echo ""
echo "=== Done ==="
echo "Palace: $HOME/.zignal"
echo "Identity: $HOME/.zignal/identity.txt"
echo "MCP server registered as 'zignal'"
echo ""
echo "Next steps:"
echo "  1. Export your Claude conversations and run: zignal mine ~/exports --mode convos"
echo "  2. Mine project dirs: zignal mine ~/path/to/project"
echo "  3. Test wake-up: zignal wake-up"
echo "  4. Open Claude Code — zignal tools are now available"
