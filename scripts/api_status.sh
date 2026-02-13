#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

HOST="${HOST:-127.0.0.1}"
PORT="${PORT:-8000}"
PID_FILE="${PID_FILE:-tmp/uvicorn.pid}"

if [[ -f "$PID_FILE" ]]; then
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
else
  pid=""
fi

echo "PID file: $PID_FILE"
if [[ -n "${pid:-}" ]] && kill -0 "$pid" 2>/dev/null; then
  echo "Running: pid=$pid"
else
  echo "Not running"
fi

echo "Healthz:"
if command -v curl >/dev/null 2>&1; then
  curl -sS --max-time 2 "http://$HOST:$PORT/healthz" || true
  echo
else
  echo "curl not found"
fi