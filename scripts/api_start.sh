#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
LOG_LEVEL="${LOG_LEVEL:-info}"
PID_FILE="${PID_FILE:-tmp/uvicorn.pid}"
LOG_FILE="${LOG_FILE:-tmp/uvicorn.log}"

# Demo-only: allow unsupported voice_id (e.g. main-site voice library ids) to run through
# the local pipeline as passthrough/export when ELEVEN_API_KEY is not configured.
export VC_DEMO_ALLOW_UNSUPPORTED_VOICE_ID="${VC_DEMO_ALLOW_UNSUPPORTED_VOICE_ID:-1}"
# Demo strategy: map main-site voice ids to local funny voices so audio changes.
export VC_DEMO_UNSUPPORTED_VOICE_STRATEGY="${VC_DEMO_UNSUPPORTED_VOICE_STRATEGY:-map_to_funny}"

PY_BIN="${PY_BIN:-}"
if [[ -z "$PY_BIN" ]]; then
  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    PY_BIN="$ROOT_DIR/.venv/bin/python"
  else
    PY_BIN="python"
  fi
fi

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

# Detach from terminal: redirect stdin from /dev/null so job control won't suspend it.
nohup "$PY_BIN" -m uvicorn app.main:app \
  --host "$HOST" --port "$PORT" \
  --log-level "$LOG_LEVEL" \
  > "$LOG_FILE" 2>&1 < /dev/null &

new_pid=$!
echo "$new_pid" > "$PID_FILE"

# Best-effort (won't exist in non-interactive shells)
disown 2>/dev/null || true

echo "Started (pid=$new_pid) -> http://$HOST:$PORT"
echo "Logs: $LOG_FILE"

# Wait for readiness (best-effort)
if command -v curl >/dev/null 2>&1; then
  for _ in {1..30}; do
    if curl -sS --max-time 1 "http://$HOST:$PORT/healthz" >/dev/null 2>&1; then
      echo "Ready: /healthz ok"
      exit 0
    fi
    sleep 0.1
  done
  echo "Warning: server started but /healthz not ready yet"
fi