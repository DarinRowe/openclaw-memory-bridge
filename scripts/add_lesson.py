#!/usr/bin/env python3
"""Add a new lesson to LESSONS.md"""
import argparse
import os
from datetime import datetime, timezone
from pathlib import Path

SEVERITIES = {"low", "medium", "high", "critical"}


def workspace_root() -> Path:
    raw = os.environ.get("OPENCLAW_WORKSPACE")
    if raw:
        return Path(raw).expanduser()
    return Path(__file__).resolve().parent.parent


def lessons_path() -> Path:
    return workspace_root() / "LESSONS.md"


def utc_date() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def main() -> int:
    parser = argparse.ArgumentParser(description="Add one operational lesson")
    parser.add_argument("--category", required=True)
    parser.add_argument("--severity", default="medium")
    parser.add_argument("lesson")
    args = parser.parse_args()

    severity = args.severity.lower().strip()
    if severity not in SEVERITIES:
        raise SystemExit(f"invalid severity: {severity}")

    path = lessons_path()
    entry = f"- [{utc_date()}][{severity}][{args.category.strip()}] {args.lesson.strip()}"

    # Append to file
    with path.open("a", encoding="utf-8") as fh:
        fh.write(entry + "\n")

    print(entry)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
