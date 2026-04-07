#!/bin/bash
set -euo pipefail

WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATE="$(date -u +%Y-%m-%d)"
FILE="$WS/memory/${DATE}.md"

mkdir -p "$WS/memory"

if [ -f "$FILE" ]; then
  echo "Already exists: $FILE"
  exit 0
fi

cat > "$FILE" << EOF
# ${DATE} (UTC)

## Session Intent
- 

## Files Modified (REQUIRED)
- (必须填写：本次会话改了哪些文件；若无也写 "- None")

## Decisions Made
- 

## Lessons Learned
- 

## Patterns
- 

## Open Items
- 
EOF

echo "Created: $FILE"
