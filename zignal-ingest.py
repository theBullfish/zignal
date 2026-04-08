#!/usr/bin/env python3
"""
zignal-ingest.py — Drop-folder watcher for Zignal Palace.

Drop any supported file into ~/zignal-inbox/ and walk away.
Handles: Claude.ai ZIP exports, conversations.json, ChatGPT exports,
         Claude Code JSONL, Slack JSON, plain text transcripts.

Runs as a systemd service on Blue Conductor.
"""

import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# ── Config ──────────────────────────────────────────────────────────────
INBOX = Path.home() / "zignal-inbox"
STAGING = Path.home() / "zignal-inbox" / ".staging"
ARCHIVE = Path.home() / "zignal-inbox" / ".archive"
LOG = Path.home() / "zignal-inbox" / ".ingest.log"
DEFAULT_WING = "claude"
SETTLE_SECONDS = 3  # wait for file to finish writing

# ── Logging ─────────────────────────────────────────────────────────────

def log(msg: str):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    with open(LOG, "a") as f:
        f.write(line + "\n")


# ── Processing ──────────────────────────────────────────────────────────

def unpack_zip(zip_path: Path) -> list[Path]:
    """Extract ZIP, return list of ingestable files."""
    dest = STAGING / zip_path.stem
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(dest)
    # Find all JSON/JSONL/TXT files
    files = []
    for ext in ("*.json", "*.jsonl", "*.txt", "*.md"):
        files.extend(dest.rglob(ext))
    return files


def detect_wing(filepath: Path) -> str:
    """Try to guess a wing name from the file or its contents."""
    name = filepath.stem.lower()
    if "chatgpt" in name:
        return "chatgpt"
    if "slack" in name:
        return "slack"
    if "claude" in name or "conversation" in name:
        return "claude"
    return DEFAULT_WING


def is_multi_convo_export(filepath: Path) -> bool:
    """Check if this is a Claude.ai privacy export with multiple conversations."""
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return "chat_messages" in data[0]
    except (json.JSONDecodeError, OSError):
        pass
    return False


def split_multi_convo(filepath: Path) -> Path:
    """Split a multi-conversation export into per-conversation files."""
    import re

    def slugify(text, max_len=80):
        if not text:
            return "untitled"
        text = re.sub(r'[^\w\s-]', '', text.lower())
        text = re.sub(r'[\s_]+', '-', text.strip())
        return text[:max_len].rstrip('-') or "untitled"

    out_dir = STAGING / f"{filepath.stem}-split"
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(filepath, "r", encoding="utf-8") as f:
        convos = json.load(f)

    count = 0
    for convo in convos:
        msgs = convo.get("chat_messages", [])
        if not msgs:
            continue

        # Map sender → role for normalize.py compatibility
        converted = []
        for m in msgs:
            converted.append({
                "role": m.get("role", "") or m.get("sender", ""),
                "content": m.get("content", []),
                "created_at": m.get("created_at", ""),
            })

        created = convo.get("created_at", "")[:10] or "nodate"
        name = slugify(convo.get("name", "") or convo.get("summary", "") or "")
        out_path = out_dir / f"{created}_{name}.json"

        counter = 1
        while out_path.exists():
            out_path = out_dir / f"{created}_{name}_{counter}.json"
            counter += 1

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"chat_messages": converted}, f, ensure_ascii=False)
        count += 1

    log(f"  Split into {count} conversation files")
    return out_dir


def ingest(path: Path):
    """Run signal mine on a file or directory."""
    wing = detect_wing(path)
    target = str(path)

    cmd = ["signal", "mine", target, "--mode", "convos", "--wing", wing]
    log(f"  Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            log(f"  ✓ Ingested → wing:{wing}")
            if result.stdout.strip():
                for line in result.stdout.strip().split("\n")[-3:]:
                    log(f"    {line}")
        else:
            log(f"  ✗ Failed (exit {result.returncode})")
            if result.stderr.strip():
                log(f"    {result.stderr.strip()[:200]}")
    except subprocess.TimeoutExpired:
        log("  ✗ Timed out after 300s")
    except FileNotFoundError:
        log("  ✗ 'signal' command not found — is zignal installed?")


def archive(path: Path):
    """Move processed file to archive."""
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = ARCHIVE / f"{ts}_{path.name}"
    shutil.move(str(path), str(dest))
    log(f"  Archived → {dest.name}")


def process_file(filepath: Path):
    """Full pipeline for one dropped file."""
    log(f"Processing: {filepath.name}")

    if filepath.suffix.lower() == ".zip":
        extracted = unpack_zip(filepath)
        log(f"  Extracted {len(extracted)} files from ZIP")
        for f in extracted:
            if f.name == "conversations.json" and is_multi_convo_export(f):
                split_dir = split_multi_convo(f)
                ingest(split_dir)
            elif f.suffix.lower() in (".json", ".jsonl", ".txt", ".md"):
                ingest(f)
        # Clean staging
        staging_dir = STAGING / filepath.stem
        if staging_dir.exists():
            shutil.rmtree(staging_dir)
        archive(filepath)

    elif filepath.suffix.lower() in (".json", ".jsonl"):
        if is_multi_convo_export(filepath):
            split_dir = split_multi_convo(filepath)
            ingest(split_dir)
            shutil.rmtree(split_dir)
        else:
            ingest(filepath)
        archive(filepath)

    elif filepath.suffix.lower() in (".txt", ".md"):
        ingest(filepath)
        archive(filepath)

    else:
        log(f"  Skipped (unsupported: {filepath.suffix})")


# ── Watcher ─────────────────────────────────────────────────────────────

class InboxHandler(FileSystemEventHandler):
    """Watch for new files in the inbox."""

    def __init__(self):
        self.pending = {}

    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        # Ignore hidden files and staging/archive
        if path.name.startswith("."):
            return
        if ".staging" in str(path) or ".archive" in str(path):
            return
        # Queue with settle delay
        self.pending[str(path)] = time.time()

    def on_modified(self, event):
        # Reset settle timer on writes
        if not event.is_directory:
            path = str(event.src_path)
            if path in self.pending:
                self.pending[path] = time.time()

    def check_pending(self):
        """Process files that have settled."""
        now = time.time()
        ready = [p for p, t in self.pending.items() if now - t >= SETTLE_SECONDS]
        for p in ready:
            del self.pending[p]
            path = Path(p)
            if path.exists():
                try:
                    process_file(path)
                except Exception as e:
                    log(f"  ✗ Error: {e}")


# ── Startup scan ────────────────────────────────────────────────────────

def scan_existing():
    """Process anything already sitting in the inbox."""
    for item in sorted(INBOX.iterdir()):
        if item.name.startswith("."):
            continue
        if item.is_file():
            try:
                process_file(item)
            except Exception as e:
                log(f"  ✗ Error processing {item.name}: {e}")


# ── Main ────────────────────────────────────────────────────────────────

def main():
    # Ensure dirs exist
    INBOX.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    ARCHIVE.mkdir(parents=True, exist_ok=True)

    log("=" * 50)
    log("Zignal Ingest Watcher starting")
    log(f"Inbox: {INBOX}")
    log("=" * 50)

    # Process anything already there
    scan_existing()

    # Watch for new drops
    handler = InboxHandler()
    observer = Observer()
    observer.schedule(handler, str(INBOX), recursive=False)
    observer.start()
    log("Watching for new files...")

    try:
        while True:
            handler.check_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        log("Shutting down")
    observer.join()


if __name__ == "__main__":
    main()
