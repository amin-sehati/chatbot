#!/bin/zsh
set -euo pipefail

# Load local env for Python (OPENAI_API_KEY, etc.)
if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Ensure a modern Node (install user-local Node 20 if needed)
export N_PREFIX="$HOME/.local/n"
export PATH="$N_PREFIX/bin:$PATH"
if ! command -v node >/dev/null 2>&1 || [ "$(node -v | sed 's/v//; s/\..*//')" -lt 18 ]; then
  npm install -g n --silent
  n 20
  hash -r
fi

# Start Python API
uv run uvicorn api.chat:app --host 127.0.0.1 --port 8000 --reload --no-access-log --log-level warning --loop uvloop --http httptools &
PY_PID=$!

# Start Next.js (dev proxy will call the Python API)
PORT="${PORT:-3001}"
node node_modules/next/dist/bin/next dev -p "$PORT" &
NEXT_PID=$!

cleanup() {
  kill "$PY_PID" "$NEXT_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT
wait


