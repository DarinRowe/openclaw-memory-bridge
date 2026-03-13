#!/usr/bin/env python3
"""Search LESSONS.md by keyword, category, or severity."""
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Search operational lessons")
    parser.add_argument("query", nargs="?", default="")
    parser.add_argument("--category")
    parser.add_argument("--severity")
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args()

    path = lessons_path()
    if not path.exists():
        print("No lessons found.")
        return 0

    q = args.query.lower().strip()
    pattern = re.compile(r"- \[(\d{4}-\d{2}-\d{2})\]\[(\w+)\]\[(\w+)\] (.+)")
    matches = []

    for line in path.read_text(encoding="utf-8").splitlines():
        m = pattern.match(line.strip())
        if not m:
            continue
        date, severity, category, lesson = m.groups()
        hay = f"{date} {severity} {category} {lesson}".lower()
        if q and q not in hay:
            continue
        if args.category and category != args.category:
            continue
        if args.severity and severity != args.severity:
            continue
        matches.append(line.strip())

    for entry in matches[:args.limit]:
        print(entry)

    if not matches:
        print("No matching lessons.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
