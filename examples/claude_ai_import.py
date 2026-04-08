#!/usr/bin/env python3
"""
prep_for_zignal.py — Convert Claude.ai privacy export to zignal-ready format.

Claude.ai exports use `sender` (human/assistant) + `content` (list of blocks).
Zignal's normalize.py expects `role` (user/human/assistant) + `content`.

This script:
  1. Reads conversations.json from the Claude.ai ZIP export
  2. Splits into one JSON file per conversation
  3. Maps sender → role so normalize.py picks them up
  4. Names files with date + conversation name for room detection

Usage:
  python prep_for_zignal.py conversations.json ./claude-convos/
  signal mine ./claude-convos/ --mode convos --wing claude
"""

import json
import os
import re
import sys
from pathlib import Path


def slugify(text: str, max_len: int = 80) -> str:
    """Turn a conversation name into a safe filename."""
    if not text:
        return "untitled"
    text = re.sub(r'[^\w\s-]', '', text.lower())
    text = re.sub(r'[\s_]+', '-', text.strip())
    return text[:max_len].rstrip('-') or "untitled"


def convert_message(msg: dict) -> dict:
    """Map Claude.ai export message to zignal-compatible format."""
    sender = msg.get("sender", "")
    role_map = {"human": "human", "assistant": "assistant"}
    role = role_map.get(sender, sender)

    return {
        "role": role,
        "content": msg.get("content", []),
        "created_at": msg.get("created_at", ""),
    }


def main():
    if len(sys.argv) < 3:
        print("Usage: python prep_for_zignal.py <conversations.json> <output_dir>")
        sys.exit(1)

    src = sys.argv[1]
    out_dir = Path(sys.argv[2])
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(src, "r", encoding="utf-8") as f:
        convos = json.load(f)

    print(f"Loaded {len(convos)} conversations")

    written = 0
    skipped = 0

    for convo in convos:
        msgs = convo.get("chat_messages", [])
        if not msgs:
            skipped += 1
            continue

        # Convert messages
        converted = [convert_message(m) for m in msgs]

        # Build filename: date_slug.json
        created = convo.get("created_at", "")[:10] or "nodate"
        name = slugify(convo.get("name", "") or convo.get("summary", "") or "")
        filename = f"{created}_{name}.json"

        # Wrap in the format normalize.py expects (flat messages list)
        out_data = {"chat_messages": converted}

        out_path = out_dir / filename
        # Handle collisions
        counter = 1
        while out_path.exists():
            out_path = out_dir / f"{created}_{name}_{counter}.json"
            counter += 1

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(out_data, f, ensure_ascii=False)

        written += 1

    print(f"Written: {written} | Skipped (empty): {skipped}")
    print(f"Output: {out_dir}")
    print(f"\nNext step:")
    print(f"  signal mine {out_dir} --mode convos --wing claude")


if __name__ == "__main__":
    main()
