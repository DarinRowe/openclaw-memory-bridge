#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

SECTIONS = ["Current Focus", "Next Step", "Blockers", "Notes"]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def workspace_root() -> Path:
    return Path(__file__).resolve().parent.parent


def state_path() -> Path:
    return workspace_root() / "SESSION-STATE.md"


def default_state() -> Dict[str, List[str]]:
    return {
        "Current Focus": ["- None"],
        "Next Step": ["- None"],
        "Blockers": ["- None"],
        "Notes": ["- None"],
    }


def parse_existing(path: Path) -> Dict[str, List[str]]:
    data = default_state()
    if not path.exists():
        return data

    current = None
    bucket: List[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("## "):
            if current:
                data[current] = normalize_lines(bucket)
            title = raw[3:].strip()
            current = title if title in data else None
            bucket = []
            continue
        if current is not None:
            bucket.append(raw)

    if current:
        data[current] = normalize_lines(bucket)
    return data


def normalize_lines(lines: List[str]) -> List[str]:
    cleaned = [line.rstrip() for line in lines if line.strip()]
    return cleaned if cleaned else ["- None"]


def bullets(text: str) -> List[str]:
    pieces = [part.strip() for part in text.splitlines() if part.strip()]
    if not pieces:
        return ["- None"]
    out = []
    for item in pieces:
        out.append(item if item.startswith("- ") else f"- {item}")
    return out


def render(data: Dict[str, List[str]]) -> str:
    lines = [
        "# SESSION-STATE.md",
        "",
        f"Last updated (UTC): {utc_now()}",
        "",
    ]
    for section in SECTIONS:
        lines.append(f"## {section}")
        lines.extend(data[section])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create or update SESSION-STATE.md")
    parser.add_argument("--focus", help="Replace Current Focus")
    parser.add_argument("--next", dest="next_step", help="Replace Next Step")
    parser.add_argument("--blockers", help="Replace Blockers")
    parser.add_argument("--note", action="append", default=[], help="Append a note bullet")
    parser.add_argument("--reset", action="store_true", help="Reset all sections to None")
    parser.add_argument("--touch", action="store_true", help="Only refresh the timestamp")
    args = parser.parse_args()

    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    data = default_state() if args.reset else parse_existing(path)

    if args.focus:
        data["Current Focus"] = bullets(args.focus)
    if args.next_step:
        data["Next Step"] = bullets(args.next_step)
    if args.blockers:
        data["Blockers"] = bullets(args.blockers)
    if args.note:
        existing = [] if data["Notes"] == ["- None"] else data["Notes"][:]
        existing.extend(bullets("\n".join(args.note)))
        data["Notes"] = existing if existing else ["- None"]

    path.write_text(render(data), encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
