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
# Tip: --reload can be expensive if it watches large folders like runs/.
# Use --reload-dir to limit watching to the backend code.
/Users/noizer/voice-changer/.venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 --port 8000 \
  --reload --reload-dir app --reload-exclude runs --reload-exclude tmp

If you keep hitting terminal/job-control issues (e.g. Ctrl+C killing the wrong process), use the helper scripts:

```bash
scripts/api_start.sh
scripts/api_status.sh
scripts/api_stop.sh
```

Frontend helper scripts (optional, stable dev server without terminal conflicts):

```bash
scripts/web_start.sh
scripts/web_status.sh
scripts/web_stop.sh
```
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

- Voice Library (optional): Redis-backed cache + favorites + recent-used
  - Set `VOICE_LIBRARY_REDIS_URL` (or `REDIS_URL`) to a Redis TCP URL like `redis://:password@host:6379/0`.
  - If unset (or Redis is unavailable), the service falls back to in-process TTL cache + local JSON state under `tmp/voice_library/`.

- Voice Library (optional): Postgres-backed voice catalog/search
  - Set `VOICE_LIBRARY_DB_URL` (or `DATABASE_URL`) to a Postgres URL like `postgresql://user:pass@host:5432/db`.
  - Initialize schema with [scripts/voice_library_init_db.sql](scripts/voice_library_init_db.sql).
  - If unset (or DB is unavailable), the service falls back to the built-in funny voices catalog.

- Voice Library (future): Semantic fallback (Milvus) framework
  - Disabled by default.
  - `VOICE_LIBRARY_SEMANTIC_ENABLED=true` enables the semantic fallback code path (only triggers when exact token-AND search returns 0).
  - `VOICE_LIBRARY_SEMANTIC_TOP_K=50` controls candidate size.
  - `VOICE_LIBRARY_SEMANTIC_MODE=fuzzy` currently uses fuzzy lexical matching (no embeddings). When Milvus/embedding is available later, this plug-in can be replaced.
  - Synonyms (optional, for fuzzy mode):
    - `VOICE_LIBRARY_SYNONYMS_ENABLED=true` (default) enables keyword synonym expansion.
    - `VOICE_LIBRARY_SYNONYMS_JSON='{"开心":["快乐","高兴"],"女声":["女性"]}'` adds/overrides synonyms.
    - `VOICE_LIBRARY_SYNONYMS_MODE=merge|replace` controls whether env JSON merges into defaults or replaces them.

```bash
export VC_FALLBACK_DURATION=0.5
export UPLOAD_MAX_BYTES=$((20*1024*1024)) # 20MB
export ALLOWED_CONTENT_TYPES='audio/wav,audio/x-wav,audio/mpeg,audio/mp3,application/octet-stream,video/mp4'
export VOICE_LIBRARY_REDIS_URL='redis://localhost:6379/0'
export VOICE_LIBRARY_DB_URL='postgresql://postgres:postgres@127.0.0.1:5432/voice_changer'
export VOICE_LIBRARY_SEMANTIC_ENABLED='false'
export VOICE_LIBRARY_SEMANTIC_TOP_K='50'
```

## Voice Library API (Public)

### GET `/api/v1/voice-library/explore`

**URL**

`GET /api/v1/voice-library/explore`

**功能**

- 浏览公共音色库，支持多维度搜索 / 筛选 / 排序。
- 当 `keyword` 搜索且结果为 0 时，如果启用了语义兜底（`VOICE_LIBRARY_SEMANTIC_ENABLED=true`），会触发语义候选集兜底。
- 响应中的 `voices[].url` 提供 mp3 预览音频地址，前端可直接播放。

**认证**

- 不需要登录即可使用（公共接口）。
- 如果希望返回 `is_favorited`（收藏状态），可选带上用户标识：
  - `X-User-Id: <user_id>`（推荐；前端本地生成即可）
  - 或 `Authorization: Bearer <user_id>`（占位方案）

**查询参数**

- `keyword`：关键词（可空）。
- `voice_ids`：逗号分隔的 voice_id 列表（可空）。
- `language_type`：语言筛选（例如 `en`/`zh`/`ja`）。
- `age`：`young` / `middle_age` / `old`。
- `gender`：`male` / `female` / `unknown`。
- `scene`：逗号分隔（例如 `Social Video,Podcast`）。
- `emotion`：逗号分隔（例如 `joyful,Calm`）。
- `sort`：排序（默认 `mostUsers`；也可用 `latest`）。
- `skip`：分页偏移（默认 0）。
- `limit`：分页大小（默认 20，最大 100）。

**返回结构（Envelope）**

- `code`: 0 表示成功
- `message`: `success`
- `data.total_count`: 总数
- `data.voices[]`: 音色数组，常用字段：
  - `voice_id`, `display_name`, `voice_type`(built-in/user), `language`, `age`, `gender`, `scene[]`, `emotion[]`
  - `is_favorited`（仅当提供 user id 时有意义）
  - `url`：mp3 预览音频（例如 `/api/v1/voice-library/preview/mamba.mp3`）

**示例**

```bash
curl -sS 'http://127.0.0.1:8000/api/v1/voice-library/explore?language_type=zh&age=young&scene=Social%20Video&emotion=joyful&skip=0&limit=20' \
  -H 'X-User-Id: demo_user'
```

### GET `/api/v1/voice-library/top-fixed-voices`

**URL**

`GET /api/v1/voice-library/top-fixed-voices?language=zh`

**功能**

- 获取“精选/置顶”音色列表（按语言分组），用于 Featured tab。
- 返回结构与 `explore` 一致（`data.voices[]`），同样包含 `url`（mp3 预览）。

**认证**

- 不需要登录。
- 可选带 `X-User-Id` 以返回 `is_favorited`。

**参数**

- `language`：必填，`en`/`zh`/`ja`。

**示例**

```bash
curl -sS 'http://127.0.0.1:8000/api/v1/voice-library/top-fixed-voices?language=zh' \
  -H 'X-User-Id: demo_user'
```

### GET|HEAD `/api/v1/voice-library/preview/{voice_id}.mp3`

**URL**

`GET /api/v1/voice-library/preview/mamba.mp3`

**功能**

- 返回某个音色的 mp3 预览音频（首次访问会懒生成并缓存）。

**认证**

- 内置音色：不需要登录。
- `user_*` 音色：列表接口返回的 `url` 会指向其 `base_voice_id` 的预览（无需登录也能播放）。

**示例**

```bash
curl -I 'http://127.0.0.1:8000/api/v1/voice-library/preview/mamba.mp3'
```

### GET `/api/v1/voice-library/get-voices-by-ids`

**URL**

`GET /api/v1/voice-library/get-voices-by-ids?voice_ids=mamba,uwu_anime`

**功能**

- 按 `voice_id` 批量获取音色详情（用于前端“已知 ids -> 回填卡片信息”场景）。

**认证**

- 不需要登录。
- 可选带 `X-User-Id` 以返回 `is_favorited`。

**参数**

- `voice_ids`：必填，逗号分隔。

**示例**

```bash
curl -sS 'http://127.0.0.1:8000/api/v1/voice-library/get-voices-by-ids?voice_ids=mamba,uwu_anime' \
  -H 'X-User-Id: demo_user'
```

### GET `/api/v1/voice-library/favorites`

**URL**

`GET /api/v1/voice-library/favorites`

**功能**

- 获取用户收藏的音色列表（支持与 `explore` 类似的筛选参数）。

**认证**

- 需要用户标识：`X-User-Id: <user_id>`。

**常用参数**

- `keyword`, `voice_ids`, `language_type`, `age`, `gender`, `scene`, `emotion`, `sort`, `skip`, `limit`

**示例**

```bash
curl -sS 'http://127.0.0.1:8000/api/v1/voice-library/favorites?skip=0&limit=50' \
  -H 'X-User-Id: demo_user'
```

### POST `/api/v1/voice-library/favorites`

**URL**

`POST /api/v1/voice-library/favorites`

**功能**

- 批量收藏/取消收藏。

**认证**

- 需要用户标识：`X-User-Id: <user_id>`。

**请求体**

```json
{"voice_ids":["mamba","uwu_anime"],"is_favorite":true}
```

**返回**

- `success_count`, `failed_count`, `failed_voice_ids`

**示例**

```bash
curl -sS -X POST 'http://127.0.0.1:8000/api/v1/voice-library/favorites' \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: demo_user' \
  -d '{"voice_ids":["mamba"],"is_favorite":true}'
```

### GET `/api/v1/voice-library/recent-used`

**URL**

`GET /api/v1/voice-library/recent-used?limit=5`

**功能**

- 获取用户最近使用的音色（用于 UI 的 Recent Used）。

**认证**

- 需要用户标识：`X-User-Id: <user_id>`。

**参数**

- `limit`：默认 5，最大 50。

**示例**

```bash
curl -sS 'http://127.0.0.1:8000/api/v1/voice-library/recent-used?limit=5' \
  -H 'X-User-Id: demo_user'
```

### GET `/api/v1/voice-library/my-voices`

**URL**

`GET /api/v1/voice-library/my-voices`

**功能**

- 获取“我的音色”（用户创建的 `user_*` 音色元数据列表）。

**认证**

- 需要用户标识：`X-User-Id: <user_id>`。

**参数**

- 与 `explore` 类似（`keyword`/筛选/分页）。

**示例**

```bash
curl -sS 'http://127.0.0.1:8000/api/v1/voice-library/my-voices?skip=0&limit=50' \
  -H 'X-User-Id: demo_user'
```

### POST `/api/v1/voice-library/my-voices`

**URL**

`POST /api/v1/voice-library/my-voices`

**功能**

- 创建一个“我的音色”（当前为元数据创建；可立即用于变声，后端会通过 `meta.base_voice_id` 解析到可用的内置音色）。

**认证**

- 需要用户标识：`X-User-Id: <user_id>`。

**请求体（示例）**

```json
{
  "display_name": "我的旁白",
  "voice_description": "for demo",
  "is_public": false,
  "language_type": "zh",
  "age": "young",
  "gender": "female",
  "scene": ["Social Video"],
  "emotion": ["joyful"],
  "meta": {"base_voice_id": "anime_uncle"}
}
```

**返回**

- `data.voice`：创建后的音色对象（`voice_id` 通常为 `user_*`）。

**示例**

```bash
curl -sS -X POST 'http://127.0.0.1:8000/api/v1/voice-library/my-voices' \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: demo_user' \
  -d '{"display_name":"我的旁白","is_public":false,"language_type":"zh","meta":{"base_voice_id":"anime_uncle"}}'
```

## Troubleshooting
- Use project venv to run the server; system Python may lack packages:

```bash
/Users/noizer/voice-changer/.venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 --port 8000 \
  --reload --reload-dir app --reload-exclude runs --reload-exclude tmp
```

- If `uvicorn` exits with code `137` when using `--reload`:
  - This is commonly caused by the reloader watching too many files (e.g. lots of entries under `runs/`).
  - Use the command above with `--reload-dir app` and `--reload-exclude runs`.

## Frontend UI

This repo includes a React + Vite frontend in `voice-changer-pro/`.

Local dev (two terminals):

1) Backend:

```bash
/Users/noizer/voice-changer/.venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 --port 8000 \
  --reload --reload-dir app --reload-exclude runs --reload-exclude tmp
```

2) Frontend:

```bash
cd voice-changer-pro
npm install
npm run dev
```

Production deploy notes are in `voice-changer-pro/README.md`.

## UI Acceptance Checklist (Manual)

Pre-reqs:

```bash
# Backend
scripts/api_start.sh

# Frontend
scripts/web_start.sh
```

Open: http://127.0.0.1:5173/

Checklist (3 steps):

1) **Create My Voice**
   - Go to **My voices** tab
   - Create a voice (should generate a `user_*` voice_id)

2) **Use it for conversion**
   - Select the newly created `user_*` voice
   - Upload an audio file and run conversion
   - Verify playback works and download is available

3) **Verify state sync**
   - **Recently used** shows the `user_*` voice you selected
   - Toggle **favorite** and confirm it appears in **Saved**

## Troubleshooting (Common)

- **Upload rejected: “File too short … Min is 5s”**
  - The backend enforces strict duration bounds: duration must be **>** `UPLOAD_MIN_DURATION_SEC` (default 5s) and **<** `UPLOAD_MAX_DURATION_SEC`.
  - Use a longer clip or adjust env vars.

- **401 Unauthorized for My voices / favorites / recent-used**
  - Requests must include `X-User-Id` (frontend generates/persists one automatically).

- **Frontend can’t reach backend in dev**
  - Vite proxy is configured for `/api` -> `http://127.0.0.1:8000` and `/outputs` passthrough.
  - Confirm backend is up: `scripts/api_status.sh`.

- **Port already in use (8000/5173)**
  - Use `scripts/api_stop.sh` or `scripts/web_stop.sh`.
  - The start scripts attempt to free the port using `lsof` if available.

- Curl error "Failed to open/read local data from file/application":
  - Ensure the path after `@` exists and is readable.
  - Use double quotes so `${AUDIO}` expands: `-F "file=@${AUDIO}"`.

- Curl exit code 7 (connection failed):
  - Server not listening; start with venv command above.
  - If you start the backend in the background and want a reliable readiness check, use:
    - `PYTHONPATH=. .venv/bin/python scripts/wait_for_healthz.py --timeout-sec 30`

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

