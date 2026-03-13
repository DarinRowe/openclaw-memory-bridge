#!/usr/bin/env python3
"""Sort/refresh LESSONS.md"""
import argparse
import os
import re
from pathlib import Path


def workspace_root() -> Path:
    raw = os.environ.get("OPENCLAW_WORKSPACE")
    if raw:
        return Path(raw).expanduser()
    return Path(__file__).resolve().parent.parent


def lessons_path() -> Path:
    return workspace_root() / "LESSONS.md"


def parse_entry(line: str) -> tuple | None:
    """Parse a lesson line like '- [2026-03-10][high][category] lesson text'"""
    match = re.match(r"- \[(\d{4}-\d{2}-\d{2})\]\[(\w+)\]\[(\w+)\] (.+)", line.strip())
    if match:
        return (match.group(1), match.group(2), match.group(3), match.group(4))
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Sort LESSONS.md")
    parser.add_argument("--limit", type=int, default=200, help="Max entries to keep")
    args = parser.parse_args()

    path = lessons_path()
    if not path.exists():
        print("# LESSONS.md\n\n- No lessons yet.")
        return 0

    lines = path.read_text(encoding="utf-8").splitlines()

    # Extract entries
    entries = []
    seen = set()
    for line in lines:
        parsed = parse_entry(line)
        if parsed:
            if parsed in seen:
                continue
            seen.add(parsed)
            entries.append(parsed)

    # Sort by date desc, then severity priority with critical first.
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    entries.sort(key=lambda e: (e[0], -severity_order.get(e[1], 4)), reverse=True)

    # Limit
    entries = entries[:args.limit] if args.limit > 0 else entries

    # Rebuild
    output = ["# LESSONS.md", "", "> Operational lessons - manually maintained.", ""]
    for date, severity, category, lesson in entries:
        output.append(f"- [{date}][{severity}][{category}] {lesson}")

    path.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"Kept {len(entries)} lessons")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
