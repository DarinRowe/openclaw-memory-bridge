# openclaw-memory-bridge

Bridges file-based memory into OpenClaw agent context. Install and go, with conservative defaults to avoid prompt bloat.

## How It Works

```
  User sends message
        │
        ▼
┌───────────────────┐     ┌──────────────────────────┐
│ before_prompt_build│────▶│ Read SESSION-STATE.md      │
│                   │     │ Read LESSONS.md (high/crit) │
│                   │     │ Truncate to safe limits     │
│                   │     │ Inject into agent context   │
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
│   command:new     │────▶│ Ensure today's daily log  │
│                   │     │ memory/YYYY-MM-DD.md      │
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
          "workspace": "~/.openclaw/workspace",
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

Notes:

- `workspace` overrides the OpenClaw workspace path for this plugin only.
- `maxSessionStateChars` caps the injected `SESSION-STATE.md` block per turn.
- `maxHighRiskLessons` limits how many `high`/`critical` lessons are injected.
- `maxLessonChars` caps the total injected lessons block per turn.
- If a block exceeds its limit, the plugin truncates it and appends `[truncated]`.

## Bundled Scripts

Use standalone or let the plugin call them automatically.

```bash
# Add a lesson
python3 scripts/add_lesson.py --category devops --severity high "always backup before upgrade"

# Search lessons
python3 scripts/search_lessons.py "backup"

# Sort/dedupe lessons
# Date desc, severity critical first
python3 scripts/render_lessons_md.py

# Update session state
python3 scripts/update_session_state.py --focus "deploy v2" --next "run tests"

# Create today's log
bash scripts/daily_log.sh

# Run cleanup manually
python3 scripts/memory_janitor.py --dry-run

# Run the plugin smoke test
npm run smoke
```

Scripts use `$OPENCLAW_WORKSPACE` when set. Otherwise they fall back to the plugin's local workspace root, which is useful for local development and smoke tests.

## License

MIT
