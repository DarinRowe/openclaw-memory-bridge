# openclaw-memory-bridge

Bridges file-based memory into OpenClaw agent context. No config needed — install and go.

## How It Works

```
  User sends message
        │
        ▼
┌───────────────────┐     ┌──────────────────────────┐
│ before_prompt_build│────▶│ Read SESSION-STATE.md    │
│                   │     │ Read LESSONS.md (high/crit)│
│                   │     │ Inject into agent context  │
└───────────────────┘     └──────────────────────────┘
        │
        ▼
   Agent runs...
        │
        ▼
┌───────────────────┐     ┌──────────────────────────┐
│    agent_end      │────▶│ Append run summary to    │
│                   │     │ memory/YYYY-MM-DD.md     │
└───────────────────┘     └──────────────────────────┘

  User runs /new
        │
        ▼
┌───────────────────┐     ┌──────────────────────────┐
│   command:new     │────▶│ Create today's daily log │
│                   │     │ memory/YYYY-MM-DD.md     │
└───────────────────┘     └──────────────────────────┘

  Gateway starts / every day 00:15 UTC
        │
        ▼
┌───────────────────┐     ┌──────────────────────────┐
│   Auto Janitor    │────▶│ Archive expired P1/P2    │
│                   │     │ from MEMORY.md           │
│                   │     │ Ensure daily log exists  │
└───────────────────┘     └──────────────────────────┘
```

## File Layout

```
~/.openclaw/workspace/
├── MEMORY.md              ◀── Curated long-term memory
│                               P0 = permanent
│                               P1 = 90-day TTL
│                               P2 = 30-day TTL
│
├── SESSION-STATE.md       ◀── Injected every turn
│                               Current Focus / Next Step / Blockers
│
├── LESSONS.md             ◀── high/critical injected to system prompt
│                               - [date][severity][category] text
│
└── memory/
    ├── YYYY-MM-DD.md      ◀── Auto-created & appended by plugin
    └── archive/           ◀── Expired entries moved here by janitor
```

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

All features are **on** by default. Turn off what you don't need:

```json
{
  "plugins": {
    "entries": {
      "memory-bridge": {
        "config": {
          "injectSessionState": true,
          "injectHighRiskLessons": true,
          "autoDailyLog": true,
          "maxSessionStateChars": 4000,
          "maxHighRiskLessons": 5,
          "maxLessonChars": 1200
        }
      }
    }
  }
}
```

## Bundled Scripts

Use standalone or let the plugin call them automatically.

```bash
# Add a lesson
python3 scripts/add_lesson.py --category devops --severity high "always backup before upgrade"

# Search lessons
python3 scripts/search_lessons.py "backup"

# Sort/dedupe lessons
python3 scripts/render_lessons_md.py

# Update session state
python3 scripts/update_session_state.py --focus "deploy v2" --next "run tests"

# Create today's log
bash scripts/daily_log.sh

# Run cleanup manually
python3 scripts/memory_janitor.py --dry-run
```

Scripts use `$OPENCLAW_WORKSPACE` (default: `~/.openclaw/workspace`).

## License

MIT
