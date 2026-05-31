#!/usr/bin/env bash
# Mine Claude Code sessions into Zignal palace — run hourly via cron.
set -e
ZIGNAL_DIR="/home/z13/zignal"
SESSIONS_DIR="/home/z13/.claude/projects/-home-z13"
cd "$ZIGNAL_DIR"
.venv/bin/python -c "
from zignal.convo_miner import mine_convos
from zignal.config import SignalConfig
mine_convos(
    '$SESSIONS_DIR',
    palace_path=SignalConfig().palace_path,
    wing='claude_code',
    agent='z13_cron',
)
" >> /tmp/zignal_mine.log 2>&1
