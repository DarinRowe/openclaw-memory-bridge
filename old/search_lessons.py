#!/usr/bin/env python3
"""search_lessons.py - quick search in memory/lessons/*.jsonl

Usage:
  python3 scripts/search_lessons.py keyword
  python3 scripts/search_lessons.py --category cron timeout

Returns matching JSONL lines.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
LESSONS_DIR = WORKSPACE / "memory" / "lessons"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--category", default=None)
    p.add_argument("keyword")
    args = p.parse_args()

    kw = args.keyword.lower()
    cat = args.category

    files = sorted(LESSONS_DIR.glob("*.jsonl"))
    if not files:
        return 0

    for fp in files:
        for line in fp.read_text(encoding="utf-8").splitlines():
            line_stripped = line.strip()
            if not line_stripped:
                continue
            try:
                obj = json.loads(line_stripped)
            except Exception:
                # fallback raw match
                if kw in line_stripped.lower():
                    print(f"{fp.name}: {line_stripped}")
                continue

            text = (obj.get("lesson", "") or "").lower()
            obj_cat = obj.get("category")
            if cat and obj_cat != cat:
                continue
            if kw in text or kw in line_stripped.lower():
                print(f"{fp.name}: {line_stripped}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
