# openclaw-memory-bridge

Bridges file-based memory into OpenClaw agent context.

## Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     OpenClaw Gateway                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              memory-bridge Plugin                    │   │
│  │                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │   │
│  │  │ before_prompt│  │ command:new  │  │agent_end │  │   │
│  │  │   _build     │  │              │  │          │  │   │
│  │  └──────┬───────┘  └──────┬───────┘  └────┬─────┘  │   │
│  │         │                 │                │         │   │
│  │         ▼                 ▼                ▼         │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │   │
│  │  │SESSION-STATE │  │ daily log    │  │ daily log│  │   │
│  │  │   + lessons  │  │   (create)   │  │ (append) │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │   │
│  │                                                      │   │
│  │  ┌──────────────────────────────────────────────┐  │   │
│  │  │           Auto Janitor (daily)                │  │   │
│  │  │  • Cleanup expired MEMORY.md (P1/P2)         │  │   │
│  │  │  • Rebuild LESSONS.md index                  │  │   │
│  │  └──────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌────────────────────────┐
              │  ~/.openclaw/workspace │
              │  ├── SESSION-STATE.md  │
              │  ├── LESSONS.md        │
              │  ├── MEMORY.md         │
              │  └── memory/           │
              │      └── YYYY-MM-DD.md │
              └────────────────────────┘
```

## What it does

| Hook | Function |
|------|----------|
| `before_prompt_build` | Injects SESSION-STATE.md + high-risk lessons into context |
| `command:new` | Ensures daily log exists on `/new` |
| `agent_end` | Appends run summary to daily log |
| `gateway_start` | Schedules daily janitor (runs after 00:15 UTC) |

## Install

```bash
openclaw plugins install @darinrowe/openclaw-memory-bridge
openclaw gateway restart
```

Or link locally:

```bash
git clone https://github.com/DarinRowe/openclaw-memory-bridge
openclaw plugins install -l ./openclaw-memory-bridge
openclaw gateway restart
```

## Config (optional)

```json
{
  "plugins": {
    "entries": {
      "memory-bridge": {
        "config": {
          "injectSessionState": true,
          "injectHighRiskLessons": true,
          "autoDailyLog": true
        }
      }
    }
  }
}
```

## File Layout

```
~/.openclaw/workspace/
├── MEMORY.md              # Curated long-term (P0/P1/P2 with TTL)
├── SESSION-STATE.md       # Short-term RAM (focus/next/blockers)
├── LESSONS.md             # Operational lessons
└── memory/
    ├── YYYY-MM-DD.md      # Daily logs
    └── archive/           # Expired entries
```

### MEMORY.md Format

```markdown
- [P0] Permanent memory
- [P1][2026-03-10] 90-day TTL memory
- [P2][2026-03-10] 30-day TTL memory
```

### LESSONS.md Format

```markdown
- [YYYY-MM-DD][severity][category] lesson text
```

Severity: `critical`, `high`, `medium`, `low`

## Bundled Scripts

| Script | Usage |
|--------|-------|
| `scripts/add_lesson.py` | `python3 add_lesson.py --category <cat> --severity <level> "text"` |
| `scripts/search_lessons.py` | `python3 search_lessons.py [query] [--category X] [--severity Y]` |
| `scripts/render_lessons_md.py` | `python3 render_lessons_md.py [--limit N]` |
| `scripts/update_session_state.py` | `python3 update_session_state.py --focus "text" --next "text"` |
| `scripts/daily_log.sh` | `bash daily_log.sh` |
| `scripts/memory_janitor.py` | `python3 memory_janitor.py [--dry-run]` |

Scripts use `$OPENCLAW_WORKSPACE` (default: `~/.openclaw/workspace`).

## License

MIT
