#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# Mind the Gap — Daily Podcast Runner
# Schedule with cron:
#   0 5 * * 1-5 /path/to/mind/podcast/run_daily.sh >> /var/log/mind_podcast.log 2>&1
# (runs Mon–Fri at 5 AM — episode publishes at 6 AM via Transistor)
# ─────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/output/logs"
mkdir -p "$LOG_DIR"

DATE=$(date +%Y-%m-%d)
LOGFILE="$LOG_DIR/${DATE}.log"

echo "──────────────────────────────────────────"
echo "Mind the Gap — $(date)"
echo "──────────────────────────────────────────"

cd "$SCRIPT_DIR"

# Activate virtual environment if it exists
if [ -f "$SCRIPT_DIR/.venv/bin/activate" ]; then
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

python generate_podcast.py 2>&1 | tee -a "$LOGFILE"
EXIT_CODE=${PIPESTATUS[0]}

if [ "$EXIT_CODE" -eq 0 ]; then
    echo "✓ Episode generated and published successfully — $DATE"
else
    echo "✗ Pipeline failed with exit code $EXIT_CODE — check $LOGFILE"
    exit "$EXIT_CODE"
fi
