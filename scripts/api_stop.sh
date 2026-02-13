#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PID_FILE="${PID_FILE:-tmp/uvicorn.pid}"

if [[ ! -f "$PID_FILE" ]]; then
  echo "Not running (no pid file at $PID_FILE)."
  exit 0
fi

pid="$(cat "$PID_FILE" 2>/dev/null || true)"
if [[ -z "${pid:-}" ]]; then
  echo "Pid file empty; removing $PID_FILE."
  rm -f "$PID_FILE"
  exit 0
fi

if ! kill -0 "$pid" 2>/dev/null; then
  echo "Process not found (pid=$pid); removing $PID_FILE."
  rm -f "$PID_FILE"
  exit 0
fi

echo "Stopping (pid=$pid)..."
kill "$pid" 2>/dev/null || true

# Wait up to ~5s
for _ in {1..50}; do
  if ! kill -0 "$pid" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "Stopped."
    exit 0
  fi
  sleep 0.1
done

echo "Force killing (pid=$pid)..."
kill -9 "$pid" 2>/dev/null || true
rm -f "$PID_FILE"
echo "Stopped."