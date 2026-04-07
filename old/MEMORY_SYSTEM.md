# Memory System (File-Based) — OpenClaw Workspace Implementation

> Goal: **high-efficiency, low-maintenance memory** for an agent running in a container.
> Principles: **simple files, clear rules, automated TTL, minimal tokens**.
>
> This document describes the *entire* memory system we implemented in this workspace.

---

## 0) What You Get (TL;DR)

- **MEMORY.md** — curated long-term memory (P0/P1/P2)
- **SESSION-STATE.md** — current task buffer (kept fresh via update_session_state.py)
- **memory/YYYY-MM-DD.md** — daily raw log (L2)
- **memory/.abstract** — tiny index (~100 tokens) (L0)
- **memory/lessons/*.jsonl** — executable lessons / rules
- **scripts/** — automation scripts (daily template, janitor, update_abstracts, add_lesson, search_lessons)
- **Cron jobs** — daily maintenance

---

## 1) Directory Layout (Workspace)

```
workspace/
├── MEMORY.md
├── SESSION-STATE.md
├── memory/
│   ├── .abstract
│   ├── YYYY-MM-DD.md
│   ├── insights/
│   │   ├── .abstract
│   │   └── YYYY-MM.md
│   ├── lessons/
│   │   ├── .abstract
│   │   └── operational-lessons.jsonl
│   └── archive/
│       └── YYYY-MM.md
└── scripts/
    ├── daily_log.sh
    ├── memory_janitor.py
    ├── update_abstracts.py
    ├── update_session_state.py
    ├── add_lesson.py
    └── search_lessons.py
```

---

## 2) File Roles & Rules

### 2.1 `memory/.abstract` (L0)
**Purpose:** A tiny index to avoid reading big files most of the time.

**Rule:** Keep it small (~100 tokens). It points to where things are.

---

### 2.2 `MEMORY.md` (Curated)
**Purpose:** The agent reads this first to regain stable context.

**Must be short:** ideally <= 200 lines.

#### Priority & TTL
- **P0**: permanent, never expires
- **P1**: 90-day TTL (must include date)
- **P2**: 30-day TTL (must include date)

#### Entry Format (required)
- `- [P0] <text>`
- `- [P1][YYYY-MM-DD] <text>`
- `- [P2][YYYY-MM-DD] <text>`

#### Decision Framework (Q1/Q2/Q3)
- **Q1:** Next time the agent wakes up, if it *doesn’t* know this, will it do the wrong thing? → **P0**
- **Q2:** Might we need to look this up within 1–3 months? → **P1**
- **Q3:** Otherwise → keep in daily log, do NOT promote to MEMORY.md

---

### 2.3 `SESSION-STATE.md` (Work Buffer)
**Purpose:** Prevent losing “current plan / current state” when conversation gets compacted.

**Rule:**
- Keep it short and actionable
- Update when the task changes phase / new blocker / next steps decided
- We run a daily `--touch` to keep a "Last updated" timestamp fresh

---

### 2.4 `memory/YYYY-MM-DD.md` (L2 Daily Logs)
**Purpose:** Raw daily events, no polishing required.

**Recommended 6 sections** (copy/paste template):
1. Session Intent
2. **Files Modified (REQUIRED)** — 最容易漏，哪怕没有也写 `None`
3. Decisions Made
4. Lessons Learned
5. Patterns
6. Open Items

---

### 2.5 `memory/insights/YYYY-MM.md` (L1 Monthly)
**Purpose:** Compressed memory layer. In v1 we keep it **simple & reliable**:
- 每天从“昨天”的 daily log **规则抽取 6 sections**（每节最多 N 行）
- 追加到当月 `insights/YYYY-MM.md`

> Later we can swap in LLM reflection summarization (true 10:1 compression).

---

### 2.6 `memory/lessons/*.jsonl`
**Purpose:** Executable “don’t repeat mistakes” memory.

**When to write a lesson:**
- you hit a pitfall you never want to repeat
- it’s a high-risk action (config, permissions, deletion, external messaging)

**Format (JSONL, one per line):**
```json
{"date":"2026-03-01","category":"browserwing","lesson":"...","severity":"high"}
```

---

## 3) Reading / Recall Flow (Text Flowchart)

```
Start turn / new task
  |
  v
[L0] read memory/.abstract
  |
  v
read MEMORY.md
  |
  v
read SESSION-STATE.md
  |
  +--> if high-risk operation: consult lessons/*.jsonl first
  |
  +--> if need history details:
        -> read insights/YYYY-MM.md (L1)
        -> if still insufficient: read daily logs (L2)
  |
  v
Do work
  |
  v
Write back:
  - update SESSION-STATE.md
  - append daily log
  - promote to MEMORY.md only if Q1/Q2 says so
```

---

## 4) Automation Scripts

### 4.1 `scripts/daily_log.sh`
**Purpose:** Ensure today’s daily log exists (UTC).

Run:
```bash
bash scripts/daily_log.sh
```

---

### 4.2 `scripts/memory_janitor.py`
**Purpose:** Daily maintenance.

Runs daily via cron (UTC 00:15):
- TTL cleanup (P1/P2 -> archive)
- Append yesterday -> monthly insights (6-section extraction)
- Update .abstract indexes (calls `scripts/update_abstracts.py`)

---

### 4.3 `scripts/add_lesson.py`
**Purpose:** Append one executable lesson into `memory/lessons/operational-lessons.jsonl`.

Run:
```bash
python3 scripts/add_lesson.py --category cron --severity high "cron 必须加 timeout，否则进程堆积"
```

Fields:
- `date` (auto, UTC)
- `category` (required)
- `severity` (low|medium|high|critical)
- `lesson` (text)


Does:
1) TTL cleanup: move expired P1/P2 entries from MEMORY.md to archive
2) Append yesterday’s daily log into monthly insights (rule-based 6-section extraction, no LLM)

Run:
```bash
python3 scripts/memory_janitor.py

# Dry run
python3 scripts/memory_janitor.py --dry-run
```

---

## 5) Cron Jobs (OpenClaw Gateway Cron)

We created cron jobs (UTC):

1) **memory-daily-log** — 00:05 UTC
- Ensures today’s daily log exists
- delivery: none

2) **memory-janitor** — 00:15 UTC
- Runs TTL + insights append
- delivery: announce to Telegram

3) **session-state-touch** — 00:20 UTC
- Updates SESSION-STATE.md Last updated timestamp
- delivery: none

> If you want a different timezone (e.g. Asia/Shanghai), update the cron tz.

---

## 6) Operational Tips

- Keep **MEMORY.md** small; push details down to daily logs.
- Put stable rules into **lessons** (they are reusable + searchable).
- Use **SESSION-STATE.md** as short-term “RAM” to survive compaction.
- For dangerous operations, always check lessons first.

---

## 7) Next Upgrades (Optional)

- LLM reflection: summarize daily logs into concise monthly insights (10:1 compression)
- Auto-generate memory/insights/.abstract (currently manual placeholder)
- Auto-generate memory/lessons/.abstract (top categories + most recent high severity)
- Add a `memory_search` wrapper that searches lessons + MEMORY.md
