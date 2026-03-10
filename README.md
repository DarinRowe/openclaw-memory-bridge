# openclaw-memory-bridge

Bridges file-based memory into OpenClaw agent context.

## What it does

| Hook | Function |
|------|----------|
| `before_prompt_build` | Injects SESSION-STATE.md + high-risk lessons into context |
| `command:new` | Ensures daily log exists on `/new` |
| `agent_end` | Appends run summary to daily log |

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

## Bundled Scripts

Standalone CLI tools for memory management:

| Script | Usage |
|--------|-------|
| `scripts/add_lesson.py` | `python3 add_lesson.py --category <cat> --severity <level> "text"` |
| `scripts/search_lessons.py` | `python3 search_lessons.py [query] [--category X] [--severity Y]` |
| `scripts/render_lessons_md.py` | `python3 render_lessons_md.py [--limit N]` |
| `scripts/update_session_state.py` | `python3 update_session_state.py --focus "text" --next "text"` |
| `scripts/daily_log.sh` | `bash daily_log.sh` |
| `scripts/memory_janitor.py` | `python3 memory_janitor.py [--dry-run]` |

Scripts use `$OPENCLAW_WORKSPACE` (default: `~/.openclaw/workspace`).

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

## License

MIT
