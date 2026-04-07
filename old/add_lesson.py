#!/usr/bin/env python3
"""add_lesson.py - append one lesson line into memory/lessons/operational-lessons.jsonl

Usage:
  python3 scripts/add_lesson.py \
    --category browserwing \
    --severity high \
    "中文字体缺失会导致截图中文不可见；安装 fonts-noto-cjk 后需重启 BrowserWing"

Notes:
- Writes JSONL (one JSON object per line)
- Auto-fills UTC date
- Creates directories/files if missing
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
LESSONS_PATH = WORKSPACE / "memory" / "lessons" / "operational-lessons.jsonl"


def main() -> int:
    p = argparse.ArgumentParser(description="Append a lesson to operational-lessons.jsonl")
    p.add_argument("--category", required=True, help="e.g. cron, browserwing, telegram, config")
    p.add_argument("--severity", default="medium", choices=["low", "medium", "high", "critical"])
    p.add_argument("--date", default=None, help="Override date (UTC) as YYYY-MM-DD")
    p.add_argument("lesson", help="Lesson text")
    args = p.parse_args()

    date = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    LESSONS_PATH.parent.mkdir(parents=True, exist_ok=True)

    obj = {
        "date": date,
        "category": args.category,
        "lesson": args.lesson.strip(),
        "severity": args.severity,
    }

    with LESSONS_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

    print(f"Appended lesson -> {LESSONS_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
