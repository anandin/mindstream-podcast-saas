#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────
# Mind the Gap — Start the control panel dashboard
# ─────────────────────────────────────────────────────────
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f .venv/bin/activate ]; then
  source .venv/bin/activate
fi

PORT=${PORT:-8080}
echo "Starting Mind the Gap control panel on http://localhost:$PORT"
uvicorn server:app --host 0.0.0.0 --port "$PORT" --reload
