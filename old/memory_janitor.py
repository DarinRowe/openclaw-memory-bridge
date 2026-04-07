#!/usr/bin/env python3
"""memory_janitor.py - 极简、高效的文件系统记忆维护器

功能（默认都很轻量）：
1) TTL：清理 MEMORY.md 中过期的 P1/P2 条目 -> 迁移到 memory/archive/YYYY-MM.md
2) L0：刷新 memory/.abstract 的小索引（可选：这里保持固定模板）
3) Insights（月度）：把「昨天」的 daily log 抽取 6 个 section（每节最多 N 行）追加到当月 insights（规则抽取，不调用 LLM）

约定：
- P1 90 天过期；P2 30 天过期；P0 永不过期
- 条目格式：- [P1][YYYY-MM-DD] ... / - [P2][YYYY-MM-DD] ...

安全：
- 只改 workspace 内文件
"""

from __future__ import annotations

import argparse
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

WORKSPACE = Path(__file__).resolve().parents[1]
MEMORY_MD = WORKSPACE / "MEMORY.md"
ARCHIVE_DIR = WORKSPACE / "memory" / "archive"
INSIGHTS_DIR = WORKSPACE / "memory" / "insights"
DAILY_DIR = WORKSPACE / "memory"
ABSTRACT = WORKSPACE / "memory" / ".abstract"

RE_ITEM = re.compile(r"^\s*-\s*\[(P0|P1|P2)\](?:\[(\d{4}-\d{2}-\d{2})\])?\s*(.*)$")


def utc_today() -> datetime:
    return datetime.now(timezone.utc)


def ensure_dirs() -> None:
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    INSIGHTS_DIR.mkdir(parents=True, exist_ok=True)


def ttl_days(priority: str) -> int | None:
    if priority == "P0":
        return None
    if priority == "P1":
        return 90
    if priority == "P2":
        return 30
    return None


def parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def run_ttl(dry_run: bool = False) -> tuple[int, Path | None]:
    """Return (moved_count, archive_path)"""
    if not MEMORY_MD.exists():
        return (0, None)

    today = utc_today()
    keep: list[str] = []
    expired: list[str] = []

    for line in MEMORY_MD.read_text(encoding="utf-8").splitlines():
        m = RE_ITEM.match(line)
        if not m:
            keep.append(line)
            continue

        prio, date_s, rest = m.group(1), m.group(2), m.group(3)
        days = ttl_days(prio)
        if days is None:
            keep.append(line)
            continue

        dt = parse_date(date_s)
        # 如果 P1/P2 没有日期，默认保留（避免误删）
        if dt is None:
            keep.append(line)
            continue

        if today - dt > timedelta(days=days):
            expired.append(line)
        else:
            keep.append(line)

    if not expired:
        return (0, None)

    archive_path = ARCHIVE_DIR / f"{today.strftime('%Y-%m')}.md"

    if not dry_run:
        MEMORY_MD.write_text("\n".join(keep).rstrip() + "\n", encoding="utf-8")
        with archive_path.open("a", encoding="utf-8") as f:
            f.write(f"\n## TTL moved on {today.strftime('%Y-%m-%d')} (UTC)\n")
            for l in expired:
                f.write(l + "\n")

    return (len(expired), archive_path)


SECTION_ORDER = [
    "Session Intent",
    "Files Modified",
    "Decisions Made",
    "Lessons Learned",
    "Patterns",
    "Open Items",
]

# Section heading aliases (daily templates may add suffixes like "(REQUIRED)")
SECTION_ALIASES = {
    "Files Modified (REQUIRED)": "Files Modified",
}


def _extract_sections_markdown(md: str, max_lines_per_section: int = 3) -> str:
    """Extract up to N lines for each of the 6 sections from a daily log.

    We keep this rule-based (no LLM) for reliability and cost.
    """
    out: list[str] = []
    # Normalize headings like "## Session Intent"
    blocks: dict[str, list[str]] = {k: [] for k in SECTION_ORDER}

    current = None
    for raw in md.splitlines():
        line = raw.rstrip("\n")
        m = re.match(r"^##\s+(.+?)\s*$", line)
        if m:
            title = m.group(1).strip()
            title = SECTION_ALIASES.get(title, title)
            current = title if title in blocks else None
            continue
        if current and line.strip():
            blocks[current].append(line.strip())

    for title in SECTION_ORDER:
        out.append(f"### {title}")
        lines = blocks.get(title, [])
        if not lines:
            out.append("- (empty)")
        else:
            for l in lines[:max_lines_per_section]:
                # ensure bullet-ish readability
                out.append(l if l.startswith("-") else f"- {l}")
    return "\n".join(out)


def append_yesterday_to_monthly_insights(dry_run: bool = False, max_lines_per_section: int = 3) -> Path | None:
    """Simple compounding: append an extracted 6-section summary of yesterday.

    This is intentionally dumb+reliable. Later we can swap in LLM summarization.
    """
    today = utc_today()
    y = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    daily = DAILY_DIR / f"{y}.md"
    if not daily.exists():
        return None

    month_file = INSIGHTS_DIR / f"{y[:7]}.md"
    md = daily.read_text(encoding="utf-8").strip()
    if not md:
        return None

    summary = _extract_sections_markdown(md, max_lines_per_section=max_lines_per_section)

    if not dry_run:
        with month_file.open("a", encoding="utf-8") as f:
            f.write(f"\n\n## {y}\n")
            f.write(summary)
            f.write("\n")

    return month_file


def refresh_abstract(dry_run: bool = False) -> None:
    # 这里保持固定模板即可（L0 轻量，不做扫描避免复杂）
    if not ABSTRACT.exists():
        return


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-insights", action="store_true")
    args = p.parse_args()

    ensure_dirs()

    moved, archive_path = run_ttl(dry_run=args.dry_run)

    insights_path = None
    if not args.no_insights:
        insights_path = append_yesterday_to_monthly_insights(dry_run=args.dry_run)

    refresh_abstract(dry_run=args.dry_run)

    # Update .abstract files (token-friendly indexes)
    if not args.dry_run:
        try:
            from subprocess import run

            run(["python3", str(WORKSPACE / "scripts" / "update_abstracts.py")], check=False)
        except Exception:
            pass

    print("memory_janitor.py done")
    print(f"- TTL moved: {moved}")
    if archive_path:
        print(f"- TTL archive: {archive_path}")
    if insights_path:
        print(f"- insights appended: {insights_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
