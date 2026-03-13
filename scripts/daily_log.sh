#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
WORKSPACE=${OPENCLAW_WORKSPACE:-$(cd "$SCRIPT_DIR/.." && pwd)}
MEMORY_DIR="$WORKSPACE/memory"
DATE_UTC=$(date -u +%F)
NOW_UTC=$(date -u +%FT%TZ)
LOG_FILE="$MEMORY_DIR/$DATE_UTC.md"

mkdir -p "$MEMORY_DIR" "$MEMORY_DIR/archive"

if [[ ! -f "$LOG_FILE" ]]; then
  cat > "$LOG_FILE" <<EOF
# Daily Log — $DATE_UTC (UTC)

Created (UTC): $NOW_UTC
Last updated (UTC): $NOW_UTC

## Session Intent
- None

## Files Modified
- None

## Decisions Made
- None

## Lessons Learned
- None

## Patterns
- None

## Open Items
- None
EOF
  echo "created: $LOG_FILE"
else
  echo "exists: $LOG_FILE"
fi
