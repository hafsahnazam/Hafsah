#!/usr/bin/env python3
"""Print the user's own prompts from local Claude Code transcripts.

Usage: collect_prompts.py [--days N] [--limit N]

Reads ~/.claude/projects/**/*.jsonl and prints one line per user-typed
prompt (newest last), skipping tool results and system-injected messages.
"""
import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path


def iter_prompts(root, since):
    for path in root.rglob("*.jsonl"):
        if path.stat().st_mtime < since:
            continue
        with path.open(encoding="utf-8", errors="ignore") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") != "user" or event.get("isMeta"):
                    continue
                content = event.get("message", {}).get("content")
                if isinstance(content, list):
                    content = " ".join(
                        part.get("text", "") for part in content
                        if isinstance(part, dict) and part.get("type") == "text"
                    )
                if not isinstance(content, str):
                    continue
                text = " ".join(content.split())
                if not text or text.startswith("<"):
                    continue
                yield event.get("timestamp", ""), path.parent.name, text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--days", type=int, default=14)
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()

    root = Path.home() / ".claude" / "projects"
    if not root.exists():
        print("No transcripts found at", root)
        return
    since = time.time() - args.days * 86400
    prompts = sorted(iter_prompts(root, since))[-args.limit:]
    for ts, project, text in prompts:
        day = ts[:10] or datetime.now(timezone.utc).date().isoformat()
        print(f"[{day}] ({project}) {text[:300]}")


if __name__ == "__main__":
    main()
