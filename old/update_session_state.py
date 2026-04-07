#!/usr/bin/env python3
"""update_session_state.py - simplest session-state updater

Goal: Keep SESSION-STATE.md useful without manual gardening.

What it does:
- Ensures file exists
- Updates the "Last updated" timestamp
- Optionally sets Current/Next from CLI

Usage:
  python3 scripts/update_session_state.py --current "Doing X" --next "Then Y"
  python3 scripts/update_session_state.py --touch

Notes:
- This is intentionally minimal (no LLM).
- You can still edit SESSION-STATE.md manually; this just keeps it fresh.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

WS = Path(__file__).resolve().parents[1]
PATH = WS / "SESSION-STATE.md"


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def ensure_exists() -> None:
    if PATH.exists():
        return
    PATH.write_text(
        "# SESSION-STATE.md\n\n"
        "> 当前任务缓冲（防止长对话被压缩后丢失关键上下文）。\n\n"
        "## Current\n- \n\n"
        "## Next\n- \n\n"
        "## Last updated\n- (never)\n",
        encoding="utf-8",
    )


def set_section(text: str, header: str, bullets: list[str]) -> str:
    lines = text.splitlines()
    out = []
    i = 0
    in_section = False
    replaced = False
    while i < len(lines):
        line = lines[i]
        if line.strip() == f"## {header}":
            out.append(line)
            # write new bullets
            for b in bullets:
                out.append(f"- {b}" if not b.startswith("-") else b)
            # skip old bullets until next header
            i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                i += 1
            replaced = True
            continue
        out.append(line)
        i += 1

    if not replaced:
        # append section if missing
        if out and out[-1].strip() != "":
            out.append("")
        out.append(f"## {header}")
        out.extend([f"- {b}" if not b.startswith("-") else b for b in bullets])

    return "\n".join(out).rstrip() + "\n"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--current", default=None, help="Set Current section (single line)")
    p.add_argument("--next", default=None, help="Set Next section (single line)")
    p.add_argument("--touch", action="store_true", help="Only update Last updated")
    args = p.parse_args()

    ensure_exists()
    text = PATH.read_text(encoding="utf-8")

    if args.current is not None:
        text = set_section(text, "Current", [args.current])

    if args.next is not None:
        text = set_section(text, "Next", [args.next])

    # Always update last updated
    text = set_section(text, "Last updated", [utc_now()])

    PATH.write_text(text, encoding="utf-8")
    print(f"Updated {PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
