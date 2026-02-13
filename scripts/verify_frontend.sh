#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

WEB_HOST="${WEB_HOST:-127.0.0.1}"
WEB_PORT="${WEB_PORT:-3000}"
API_HOST="${API_HOST:-127.0.0.1}"
API_PORT="${API_PORT:-8000}"
USER_ID="${USER_ID:-demo_user}"

WEB_BASE="http://${WEB_HOST}:${WEB_PORT}"
API_BASE="http://${API_HOST}:${API_PORT}"

PYTHON_BIN="${PYTHON_BIN:-}" # optional override

if [[ -z "$PYTHON_BIN" ]]; then
  if [[ -x "$ROOT_DIR/.venv/bin/python" ]]; then
    PYTHON_BIN="$ROOT_DIR/.venv/bin/python"
  else
    PYTHON_BIN="python3"
  fi
fi

say() {
  printf "%s\n" "$*"
}

fail() {
  say "FAIL: $*" >&2
  exit 1
}

http_code() {
  # $1 url, $2 optional extra curl args
  local url="$1"
  shift || true
  curl -sS -o /dev/null -w "%{http_code}" "$@" "$url" || true
}

require_200() {
  local url="$1"
  shift || true
  local code
  code="$(http_code "$url" "$@")"
  if [[ "$code" != "200" ]]; then
    fail "$url -> HTTP $code (expected 200)"
  fi
}

say "== Frontend verification (React 3000) =="
say "WEB_BASE: $WEB_BASE"
say "API_BASE: $API_BASE"
say "USER_ID:  $USER_ID"
say "PYTHON:   $PYTHON_BIN"
say

say "[1/6] Check backend healthz..."
require_200 "$API_BASE/healthz"
say "OK"
say

say "[2/6] Check web (3000) reachable..."
require_200 "$WEB_BASE/"
say "OK"
say

say "[3/6] Voice list via web proxy: top-fixed-voices?language=zh ..."
json="$(curl -sS "$WEB_BASE/api/v1/voice-library/top-fixed-voices?language=zh")"

# Validate: has data.voices[0].voice_id and data.voices[0].url
printf '%s' "$json" | ${PYTHON_BIN} -c 'import json,sys; j=json.load(sys.stdin); voices=(j.get("data") or {}).get("voices") or []; assert isinstance(voices,list) and len(voices)>0, "no voices returned"; v=voices[0]; vid=str(v.get("voice_id") or "").strip(); url=str(v.get("url") or "").strip(); assert vid, "voice_id missing"; assert url, "url missing"; print(f"OK: voice_id={vid} url={url}")'

# Extract one preview url and normalize to absolute
preview_rel="$(printf '%s' "$json" | ${PYTHON_BIN} -c 'import json,sys; j=json.load(sys.stdin); v=(j.get("data") or {}).get("voices") or []; print(((v[0].get("url") or "").strip()) if v else "")')"

if [[ "$preview_rel" == /* ]]; then
  preview_url="$WEB_BASE$preview_rel"
else
  preview_url="$preview_rel"
fi

say "OK"
say

say "[4/6] Preview mp3 accessible (through 3000 proxy)..."
# Use GET with Range to avoid downloading whole file.
code="$(curl -sS -o /dev/null -w "%{http_code}" -H "Range: bytes=0-1023" "$preview_url" || true)"
if [[ "$code" != "206" && "$code" != "200" ]]; then
  fail "$preview_url -> HTTP $code (expected 200 or 206)"
fi
ct="$(curl -sS -I "$preview_url" | tr -d '\r' | awk -F': ' 'tolower($1)=="content-type"{print tolower($2)}' | head -n 1)"
if [[ "$ct" != audio/mpeg* ]]; then
  fail "content-type not audio/mpeg: $ct"
fi
say "OK: $preview_url ($ct)"
say

say "[5/6] Check favorites & recent-used endpoints (need user id header)..."
require_200 "$API_BASE/api/v1/voice-library/favorites?limit=5" -H "X-User-Id: $USER_ID"
require_200 "$API_BASE/api/v1/voice-library/recent-used?limit=5" -H "X-User-Id: $USER_ID"
say "OK"
say

say "[6/6] Optional: run /voice-changer once and check output url..."
# Generate a short wav (6s) to satisfy min duration.
ref_wav="$ROOT_DIR/tmp/verify_frontend_ref.wav"
mkdir -p "$(dirname "$ref_wav")"
${PYTHON_BIN} - "$ref_wav" <<'PY'
import sys
import wave,struct,math
p=sys.argv[1]
sr=48000
dur=6.0
freq=220.0
amp=0.15
n=int(sr*dur)
with wave.open(p,'wb') as wf:
  wf.setnchannels(1)
  wf.setsampwidth(2)
  wf.setframerate(sr)
  for i in range(n):
    t=i/sr
    v=amp*math.sin(2*math.pi*freq*t)
    wf.writeframesraw(struct.pack('<h', int(max(-1,min(1,v))*32767)))
print(p)
PY
>/dev/null

payload='{"voice_id":"mamba","output_format":"mp3"}'
resp="$(curl -sS -X POST "$API_BASE/voice-changer" \
  -F "file=@${ref_wav};type=audio/wav" \
  -F "payload=${payload}" )"

out_url="$(printf '%s' "$resp" | ${PYTHON_BIN} -c 'import json,sys; j=json.load(sys.stdin); url=(j.get("output_url") or (j.get("data") or {}).get("output_url") or ((j.get("meta") or {}).get("artifact") or {}).get("public_url") or ""); print(url)')"

if [[ -z "$out_url" ]]; then
  fail "voice-changer did not return output_url"
fi

# output_url may be relative (/outputs/...) or absolute
if [[ "$out_url" == /* ]]; then
  out_abs="$API_BASE$out_url"
else
  out_abs="$out_url"
fi

require_200 "$out_abs"
say "OK: output_url=$out_abs"
say

say "ALL OK"
