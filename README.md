# Voice Changer API

Minimal FastAPI service exposing a `/voice-changer` endpoint.

## Quickstart

1. Create/activate your Python environment (optional).
2. Install dependencies:

```bash
/usr/bin/python3 -m pip install -r requirements.txt
```

3. Run the server (recommended via project venv):

```bash
/Users/noizer/voice-changer/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

4. Health check:

```bash
curl -sS http://127.0.0.1:8000/healthz
```

5. Multipart upload (mp3 output):

```bash
AUDIO_PATH=${AUDIO:-$HOME/Downloads/test.mp3}
[ -f "$AUDIO_PATH" ] || AUDIO_PATH="/Users/noizer/voice-changer/tmp/test.wav"

curl -sS -X POST "http://127.0.0.1:8000/voice-changer" \
  -F "file=@${AUDIO_PATH}" \
  -F 'payload={"voice_id":"test-voice","stability":7,"similarity":8,"output_format":"mp3","preset_id":null,"webhook_url":null,"options":{}};type=application/json' \
  | tee /tmp/resp_upload.json

/usr/bin/python3 -c 'import json; print(json.load(open("/tmp/resp_upload.json"))["output_url"])' \
  | xargs -I{} curl -sS -o /dev/null -w "GET %{http_code} -> http://127.0.0.1:8000{}\n" "http://127.0.0.1:8000{}"
```

6. JSON-only mode:

```bash
curl -sS -X POST http://127.0.0.1:8000/voice-changer \
  -H 'Content-Type: application/json' \
  -d '{"voice_id":"test-voice","stability":7,"similarity":8,"output_format":"wav","preset_id":null,"webhook_url":null,"options":{}}'
```

## Behavior & Fallbacks
- Without `ELEVEN_API_KEY`, voice change step will copy input WAV or synthesize a short WAV to ensure success.
- `ExportStep` publishes to `/outputs` and the route returns `output_url` based on actual produced format.
- If `ffmpeg` is unavailable or conversion fails, MP3 requests fall back to WAV (response reflects `.wav`).

## Configuration
- `ELEVEN_API_KEY`: enables the real provider path.
- `VC_FALLBACK_DURATION`: synthesized fallback WAV length in seconds (default `1.0`).

- `UPLOAD_MAX_BYTES`: max allowed upload size in bytes for multipart saves (default `10485760`, i.e., 10MB).
- `ALLOWED_CONTENT_TYPES`: comma-separated whitelist for multipart `file` content types. Defaults include `audio/wav`, `audio/x-wav`, `audio/mpeg`, `audio/mp3`, `application/octet-stream`, `video/mp4`.

```bash
export VC_FALLBACK_DURATION=0.5
export UPLOAD_MAX_BYTES=$((20*1024*1024)) # 20MB
export ALLOWED_CONTENT_TYPES='audio/wav,audio/x-wav,audio/mpeg,audio/mp3,application/octet-stream,video/mp4'
```

## Troubleshooting
- Use project venv to run the server; system Python may lack packages:

```bash
/Users/noizer/voice-changer/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- Curl error "Failed to open/read local data from file/application":
  - Ensure the path after `@` exists and is readable.
  - Use double quotes so `${AUDIO}` expands: `-F "file=@${AUDIO}"`.

- Curl exit code 7 (connection failed):
  - Server not listening; start with venv command above.

- MP3 output requires `ffmpeg` installed locally.

## Architecture

- API: FastAPI app and routes
  - [app/main.py](app/main.py): Creates FastAPI app, mounts routes, adds `/healthz`.
  - [app/api/routes.py](app/api/routes.py): `POST /voice-changer` runs pipeline; serves outputs via `/outputs`.
  - [app/api/schemas.py](app/api/schemas.py): `VoiceChangerRequest` and `VoiceChangerResponse` (Pydantic v2).
- Core: Context and pipeline
  - [app/core/artifacts.py](app/core/artifacts.py): `Artifact`, `TaskContext` with safe pathing, registration, cleanup.
  - [app/core/pipeline.py](app/core/pipeline.py): Sequential step execution with timing and error capture.
- Config & Services
  - [app/config/settings.py](app/config/settings.py): `RUNS_BASE_DIR` and `OUTPUTS_DIR`.
  - [app/services/ffmpeg.py](app/services/ffmpeg.py): `is_available()`, `convert_wav_to_mp3()`, `standardize_to_wav()`.
- Steps: Audio processing
  - [app/steps/standardize.py](app/steps/standardize.py): Standardizes input to mono 48k WAV (skips if no input or ffmpeg missing).
  - [app/steps/voice_change.py](app/steps/voice_change.py): Provider path or synthesized WAV fallback.
  - [app/steps/export.py](app/steps/export.py): Exports to requested format; uses ffmpeg for MP3 with WAV fallback.


## Cleanup

- Overview: Use [scripts/cleanup_runs.py](scripts/cleanup_runs.py) to remove old run directories and published output files.
- Safety: Only deletes UUID-named run directories and `.wav`/`.mp3` in outputs.
- Usage:

```bash
# Dry-run: outputs only
PYTHONPATH=. .venv/bin/python scripts/cleanup_runs.py --older-than-hours 0.5 --outputs-only

# Dry-run: runs only
PYTHONPATH=. .venv/bin/python scripts/cleanup_runs.py --older-than-hours 0.5 --runs-only

# Apply deletions: both (older than 24h)
PYTHONPATH=. .venv/bin/python scripts/cleanup_runs.py --older-than-hours 24 --apply
```

- Flags:
  - `--older-than-hours`: threshold age in hours
  - `--apply`: perform deletions (omit for dry-run)
  - `--runs-only`: only clean `runs/`
  - `--outputs-only`: only clean `runs/outputs/`

- Cron (macOS):

```bash
crontab -e
# Every day at 03:00, purge entries older than 72h
0 3 * * * cd /Users/noizer/voice-changer && PYTHONPATH=. /Users/noizer/voice-changer/.venv/bin/python scripts/cleanup_runs.py --older-than-hours 72 --apply >> /tmp/voice_changer_cleanup.log 2>&1
```

