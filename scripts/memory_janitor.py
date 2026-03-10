#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import List, Tuple

ENTRY_RE = re.compile(r"^- \[(P[012])\](?:\[(\d{4}-\d{2}-\d{2})\])?\s+(.*)$")
TTL_DAYS = {"P1": 90, "P2": 30}


class ArchiveItem(Tuple[str, str]):
    pass


def workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent


def memory_file() -> Path:
    return workspace_root() / "MEMORY.md"


def archive_dir() -> Path:
    return workspace_root() / "memory" / "archive"


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def archive_path(entry_date: str) -> Path:
    ym = entry_date[:7] if re.match(r"\d{4}-\d{2}-\d{2}", entry_date) else today_utc().isoformat()[:7]
    return archive_dir() / f"{ym}.md"


def read_lines(path: Path) -> List[str]:
    if not path.exists():
        return []
    return path.read_text(encoding="utf-8").splitlines()


def expired(priority: str, entry_date: str | None) -> bool:
    if priority not in TTL_DAYS or not entry_date:
        return False
    try:
        dt = date.fromisoformat(entry_date)
    except ValueError:
        return False
    return dt + timedelta(days=TTL_DAYS[priority]) < today_utc()


def cleanup_memory(dry_run: bool) -> List[str]:
    path = memory_file()
    lines = read_lines(path)
    if not lines:
        return []

    keep: List[str] = []
    archived: List[tuple[str, str]] = []

    for line in lines:
        match = ENTRY_RE.match(line)
        if not match:
            keep.append(line)
            continue
        priority, entry_date, _text = match.groups()
        if expired(priority, entry_date):
            archived.append((entry_date or today_utc().isoformat(), line))
        else:
            keep.append(line)

    actions = []
    if archived:
        actions.append(f"archive {len(archived)} expired memory entries")

    if not dry_run and archived:
        archive_dir().mkdir(parents=True, exist_ok=True)
        grouped: dict[Path, List[str]] = {}
        for entry_date, line in archived:
            grouped.setdefault(archive_path(entry_date), []).append(line)
        stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        for target, bucket in grouped.items():
            existing = target.read_text(encoding="utf-8") if target.exists() else f"# Archive — {target.stem}\n\n"
            chunk = [f"## Archived from MEMORY.md at {stamp}", ""]
            chunk.extend(bucket)
            chunk.append("")
            target.write_text(existing.rstrip() + "\n\n" + "\n".join(chunk), encoding="utf-8")
        path.write_text("\n".join(keep).rstrip() + "\n", encoding="utf-8")

    return actions


def run_script(rel_path: str, dry_run: bool) -> str | None:
    if dry_run:
        return f"run {rel_path}"
    script = workspace_root() / rel_path
    subprocess.run(["python3", str(script)] if rel_path.endswith(".py") else ["bash", str(script)], check=True)
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily memory maintenance")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    actions = []
    actions.extend(cleanup_memory(args.dry_run))

    for rel in ["scripts/daily_log.sh"]:
        action = run_script(rel, args.dry_run)
        if action:
            actions.append(action)

    if args.dry_run:
        if actions:
            print("\n".join(actions))
        else:
            print("no changes")
    else:
        print("memory janitor complete")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
