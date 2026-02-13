#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-5173}"
PID_FILE="${PID_FILE:-tmp/vite.pid}"
LOG_FILE="${LOG_FILE:-tmp/vite.log}"

mkdir -p "$(dirname "$PID_FILE")"

if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${old_pid:-}" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "Already running (pid=$old_pid)."
    exit 0
  fi
  rm -f "$PID_FILE"
fi

# Try to free the port if something else is listening.
if command -v lsof >/dev/null 2>&1; then
  lsof -ti tcp:"$PORT" | xargs -r kill -9 || true
fi

if [[ ! -d "frontend/node_modules" ]]; then
  echo "frontend/node_modules missing; run: (cd frontend && npm ci)"
fi

cd frontend
nohup npm run dev -- --host "$HOST" --port "$PORT" --strictPort \
  > "$ROOT_DIR/$LOG_FILE" 2>&1 < /dev/null &

new_pid=$!
echo "$new_pid" > "$ROOT_DIR/$PID_FILE"
disown 2>/dev/null || true

echo "Started (pid=$new_pid) -> http://$HOST:$PORT"
echo "Logs: $LOG_FILE"

# Best-effort readiness
if command -v curl >/dev/null 2>&1; then
  for _ in {1..50}; do
    if curl -sS --max-time 1 "http://$HOST:$PORT/" >/dev/null 2>&1; then
      echo "Ready: / ok"
      exit 0
    fi
    sleep 0.1
  done
  echo "Warning: dev server started but not ready yet"
fi
