#!/usr/bin/env python3
"""update_abstracts.py - simplest auto-maintenance for .abstract files

Generates/updates:
- memory/.abstract
- memory/insights/.abstract
- memory/lessons/.abstract

Design goals:
- Very small output (token-friendly)
- Pure file scanning (no LLM)
- Safe: workspace-only

Run:
  python3 scripts/update_abstracts.py
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json

WS = Path(__file__).resolve().parents[1]
MEM_DIR = WS / "memory"
INS_DIR = MEM_DIR / "insights"
LES_DIR = MEM_DIR / "lessons"


def _utc_now_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _list_recent_daily(n: int = 7) -> list[str]:
    files = sorted(MEM_DIR.glob("????-??-??.md"), reverse=True)
    return [f.name for f in files[:n]]


def _list_recent_monthly_insights(n: int = 6) -> list[str]:
    files = sorted(INS_DIR.glob("????-??.md"), reverse=True)
    return [f.name for f in files[:n]]


def _lessons_summary(n: int = 5) -> list[str]:
    # Simple: show last N lessons across all jsonl files (by file order + line order)
    jsonls = sorted(LES_DIR.glob("*.jsonl"))
    items: list[dict] = []
    for fp in jsonls:
        for line in fp.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                obj["_file"] = fp.name
                items.append(obj)
            except Exception:
                continue

    # sort by date if present, fallback keep order
    def key(o: dict):
        return (o.get("date") or "", o.get("severity") or "")

    items.sort(key=key, reverse=True)
    out = []
    for o in items[:n]:
        out.append(f"- {o.get('date','?')} [{o.get('severity','?')}] ({o.get('category','?')}): {str(o.get('lesson',''))[:80]}")
    return out


def write_memory_abstract() -> None:
    MEM_DIR.mkdir(parents=True, exist_ok=True)
    p = MEM_DIR / ".abstract"
    daily = _list_recent_daily(7)
    insights = _list_recent_monthly_insights(6)

    content = [
        "# memory/.abstract (L0)",
        "",
        "> Tiny index (~100 tokens). Read this first.",
        "",
        f"Updated: {_utc_now_str()}",
        "",
        "Core:",
        "- MEMORY.md (P0/P1/P2 long-term)",
        "- SESSION-STATE.md (current task buffer)",
        "",
        "Recent daily logs:",
    ]
    content += [f"- {name}" for name in daily] or ["- (none)"]
    content += ["", "Recent monthly insights:"]
    content += [f"- insights/{name}" for name in insights] or ["- (none)"]
    content += ["", "Lessons:", "- lessons/operational-lessons.jsonl", ""]

    p.write_text("\n".join(content), encoding="utf-8")


def write_insights_abstract() -> None:
    INS_DIR.mkdir(parents=True, exist_ok=True)
    p = INS_DIR / ".abstract"
    insights = _list_recent_monthly_insights(12)

    content = [
        "# memory/insights/.abstract (L1)",
        "",
        f"Updated: {_utc_now_str()}",
        "",
        "Files:",
    ]
    content += [f"- {name}" for name in insights] or ["- (none)"]
    content.append("")

    p.write_text("\n".join(content), encoding="utf-8")


def write_lessons_abstract() -> None:
    LES_DIR.mkdir(parents=True, exist_ok=True)
    p = LES_DIR / ".abstract"

    content = [
        "# memory/lessons/.abstract (L1)",
        "",
        f"Updated: {_utc_now_str()}",
        "",
        "Recent lessons:",
    ]
    content += _lessons_summary(5) or ["- (none)"]
    content.append("")

    p.write_text("\n".join(content), encoding="utf-8")


def main() -> int:
    write_memory_abstract()
    write_insights_abstract()
    write_lessons_abstract()
    print("update_abstracts.py done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
