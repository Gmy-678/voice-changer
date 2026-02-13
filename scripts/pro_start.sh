#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-3000}"
PID_FILE="${PID_FILE:-tmp/voice-changer-pro.pid}"
LOG_FILE="${LOG_FILE:-tmp/voice-changer-pro.log}"

mkdir -p "$(dirname "$PID_FILE")"

if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"

  # If something is already listening on the port, treat it as running and
  # refresh PID_FILE to the actual listener PID.
  if command -v lsof >/dev/null 2>&1; then
    listen_pid="$(lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
    if [[ -n "${listen_pid:-}" ]]; then
      echo "$listen_pid" > "$PID_FILE"
      echo "Already running (pid=$listen_pid)."
      exit 0
    fi
  fi

  if [[ -n "${old_pid:-}" ]] && kill -0 "$old_pid" 2>/dev/null; then
    echo "Already running (pid=$old_pid)."
    exit 0
  fi
  rm -f "$PID_FILE"
fi

if command -v lsof >/dev/null 2>&1; then
  lsof -ti tcp:"$PORT" | xargs -r kill -9 || true
fi

if [[ ! -d "voice-changer-pro/node_modules" ]]; then
  echo "voice-changer-pro/node_modules missing; run: (cd voice-changer-pro && npm ci)"
fi

cd voice-changer-pro
nohup npm run dev -- --host "$HOST" --port "$PORT" --strictPort \
  > "$ROOT_DIR/$LOG_FILE" 2>&1 < /dev/null &

launcher_pid=$!
echo "$launcher_pid" > "$ROOT_DIR/$PID_FILE"
disown 2>/dev/null || true

echo "Started (pid=$launcher_pid) -> http://$HOST:$PORT"
echo "Logs: $LOG_FILE"

if command -v curl >/dev/null 2>&1; then
  for _ in {1..50}; do
    if curl -sS --max-time 1 "http://$HOST:$PORT/" >/dev/null 2>&1; then
      echo "Ready: / ok"

      # Record the actual listening PID (npm may spawn node with a different pid).
      if command -v lsof >/dev/null 2>&1; then
        listen_pid="$(lsof -ti tcp:"$PORT" -sTCP:LISTEN 2>/dev/null | head -n 1 || true)"
        if [[ -n "${listen_pid:-}" ]]; then
          echo "$listen_pid" > "$ROOT_DIR/$PID_FILE"
        fi
      fi

      exit 0
    fi
    sleep 0.1
  done
  echo "Warning: dev server started but not ready yet"
fi
