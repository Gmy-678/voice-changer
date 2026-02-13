from __future__ import annotations

import json
import os
import shutil
import uuid
import hashlib
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import FileResponse

from .schemas import (
    VoiceChangerRequest,
    VoiceChangerResponse,
    VoiceInfo,
    VoicesResponse,
    CapabilitiesResponse,
    TaskInfoResponse,
)

from app.config.settings import RUNS_BASE_DIR
from app.config.settings import OUTPUTS_DIR
from app.core.artifacts import Artifact, TaskContext
from app.core.pipeline import Pipeline
from app.steps.standardize import StandardizeStep
from app.steps.voice_change import VoiceChangeStep
from app.steps.export import ExportStep
from app.services.media_probe import probe_duration_seconds, MediaProbeError
from app.services.providers.funny_voice import FunnyVoiceProvider
from app.api.voice_library.routes import record_voice_used
from app.voice_library.user_voices import get_user_voices_by_ids


router = APIRouter(prefix="/voice-changer", tags=["voice-changer"])


def _demo_map_to_funny_voice_id(selected_voice_id: str) -> str:
    """Deterministically map an arbitrary voice id to a supported FunnyVoice id."""
    voices = list(FunnyVoiceProvider.SUPPORTED_VOICES)
    if not voices:
        return "anime_uncle"
    h = hashlib.md5(selected_voice_id.encode("utf-8"), usedforsecurity=False).hexdigest()
    idx = int(h[:8], 16) % len(voices)
    return voices[idx]


def _funny_voice_name(voice_id: str) -> str:
    for v in _funny_voice_infos():
        if v.id == voice_id:
            return v.name
    return voice_id


def _get_allowed_content_types() -> list[str]:
    allowed_default = {
        "audio/wav",
        "audio/x-wav",
        "audio/mpeg",
        "audio/mp3",
        "application/octet-stream",
        "video/mp4",
    }
    allowed_env = os.getenv("ALLOWED_CONTENT_TYPES")
    if allowed_env:
        try:
            allowed_set = {s.strip().lower() for s in allowed_env.split(",") if s.strip()}
            if allowed_set:
                return sorted(list(allowed_set))
        except Exception:
            pass
    return sorted(list(allowed_default))


def _get_upload_limits() -> tuple[int, float, float]:
    # bytes
    max_bytes_env = os.getenv("UPLOAD_MAX_BYTES", "10485760")
    try:
        max_bytes = int(max_bytes_env)
    except Exception:
        max_bytes = 10 * 1024 * 1024

    # duration
    min_dur_env = os.getenv("UPLOAD_MIN_DURATION_SEC", "5")
    max_dur_env = os.getenv("UPLOAD_MAX_DURATION_SEC", str(5 * 60))
    try:
        min_dur = float(min_dur_env)
    except Exception:
        min_dur = 5.0
    try:
        max_dur = float(max_dur_env)
    except Exception:
        max_dur = float(5 * 60)

    return max_bytes, min_dur, max_dur


def _funny_voice_infos() -> list[VoiceInfo]:
    # Keep this aligned with the React UI defaults.
    catalog: dict[str, dict[str, str]] = {
        "anime_uncle": {
            "name": "Anime Uncle",
            "role": "Overconfident Narrator",
            "description": "Lower + punchy + dramatic (funny \"uncle\" vibe)",
        },
        "uwu_anime": {
            "name": "UwU Anime",
            "role": "Cute & Sparkly",
            "description": "Higher pitch + brighter tone (classic anime \"uwu\")",
        },
        "gender_swap": {
            "name": "Gender Swap",
            "role": "Pitch Shift",
            "description": "A noticeable pitch shift (for quick voice flips)",
        },
        "mamba": {
            "name": "Mamba",
            "role": "Hype / Energy",
            "description": "Boosted presence + compression-like punch",
        },
        "nerd_bro": {
            "name": "Nerd Bro",
            "role": "Nasally / Snappy",
            "description": "Slightly nasal + tight (meme \"nerd bro\" tone)",
        },
    }

    voices: list[VoiceInfo] = []
    for vid in FunnyVoiceProvider.SUPPORTED_VOICES:
        info = catalog.get(vid, {"name": vid, "role": "", "description": ""})
        voices.append(
            VoiceInfo(
                id=vid,
                name=info.get("name", vid),
                role=info.get("role", ""),
                description=info.get("description", ""),
                category="public",
                is_verified=True,
                provider="funny_voice",
            )
        )
    return voices


@router.get("/voices", response_model=VoicesResponse)
async def list_voices() -> VoicesResponse:
    return VoicesResponse(voices=_funny_voice_infos())


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def capabilities() -> CapabilitiesResponse:
    max_bytes, min_dur, max_dur = _get_upload_limits()
    return CapabilitiesResponse(
        voices=_funny_voice_infos(),
        output_formats=["mp3", "wav"],
        upload_max_bytes=max_bytes,
        allowed_content_types=_get_allowed_content_types(),
        upload_min_duration_sec=min_dur,
        upload_max_duration_sec=max_dur,
        async_mode=False,
    )


@router.get("/tasks/{task_id}", response_model=TaskInfoResponse)
async def get_task(task_id: str) -> TaskInfoResponse:
    # Synchronous pipeline publishes outputs named {task_id}.(mp3|wav) in OUTPUTS_DIR.
    mp3_path = os.path.join(OUTPUTS_DIR, f"{task_id}.mp3")
    wav_path = os.path.join(OUTPUTS_DIR, f"{task_id}.wav")

    if os.path.isfile(mp3_path):
        return TaskInfoResponse(task_id=task_id, status="success", output_url=f"/outputs/{task_id}.mp3")
    if os.path.isfile(wav_path):
        return TaskInfoResponse(task_id=task_id, status="success", output_url=f"/outputs/{task_id}.wav")
    return TaskInfoResponse(task_id=task_id, status="not_found", output_url=None)


@router.post("", response_model=VoiceChangerResponse)
async def voice_changer(
    request: Request,
    file: Optional[UploadFile] = File(default=None),
    payload: Optional[str] = Form(default=None),
) -> VoiceChangerResponse:
    """
    Synchronous endpoint supporting two input modes:
    - JSON body: VoiceChangerRequest
    - multipart/form-data: fields 'file' (UploadFile) + 'payload' (JSON string)
    """
    task_id = str(uuid.uuid4())

    # Build task context early
    task_dir = os.path.join(RUNS_BASE_DIR, task_id)
    os.makedirs(task_dir, exist_ok=True)

    ctx = TaskContext(
        task_id=task_id,
        task_dir=task_dir,
        voice_id="",
        stability=7,
        similarity=8,
        output_format="mp3",
        preset_id=None,
        webhook_url=None,
        options={},
        debug={},
        cleanup_mode="none",  # keep outputs by default (you can change later)
    )

    # Parse input according to content type
    parsed: VoiceChangerRequest
    initial_artifact = Artifact(path="", mime="application/octet-stream", meta={"source": "none"})

    try:
        if file is not None or payload is not None:
            # multipart mode
            if not payload:
                raise HTTPException(status_code=400, detail="Missing payload in form data")

            data = json.loads(payload)
            parsed = VoiceChangerRequest.model_validate(data)

            if file is not None:
                ext = os.path.splitext(file.filename or "")[1].lower() or ".bin"
                in_path = os.path.join(task_dir, f"input{ext}")
                # Validate content type against whitelist
                allowed_set = set(_get_allowed_content_types())

                content_type = (file.content_type or "").lower()
                if content_type not in allowed_set:
                    raise HTTPException(
                        status_code=415,
                        detail={
                            "error": "unsupported_media_type",
                            "content_type": content_type or None,
                            "allowed": sorted(list(allowed_set)),
                            "suggestion": "Use audio/wav or audio/mpeg, or set ALLOWED_CONTENT_TYPES",
                        },
                    )
                # Stream save with size limit to avoid large memory usage
                max_bytes, min_dur, max_dur = _get_upload_limits()

                total = 0
                chunk_size = 1024 * 1024
                with open(in_path, "wb") as out_f:
                    # Use underlying spooled file for efficient streaming
                    while True:
                        chunk = file.file.read(chunk_size)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > max_bytes:
                            # Clean up partial file
                            try:
                                os.remove(in_path)
                            except Exception:
                                pass
                            raise HTTPException(
                                status_code=413,
                                detail={
                                    "error": "file_too_large",
                                    "received_bytes": total,
                                    "max_bytes": max_bytes,
                                    "suggestion": "Reduce file size or increase UPLOAD_MAX_BYTES",
                                },
                            )
                        out_f.write(chunk)

                # ---- duration limit (<= 5 min) ----
                try:
                    dur = probe_duration_seconds(in_path)
                except MediaProbeError as e:
                    raise HTTPException(status_code=400, detail=f"Cannot read media duration: {e}")

                # Require duration to be known to enforce limits.
                if dur is None:
                    raise HTTPException(
                        status_code=400,
                        detail="Cannot determine media duration. Please upload a valid audio file.",
                    )

                ctx.debug.setdefault("probe", {})
                ctx.debug["probe"].update(
                    {
                        "duration_sec": dur,
                        "min_duration_sec": min_dur,
                        "max_duration_sec": max_dur,
                    }
                )

                # Enforce strict bounds: duration must be > 5s and < 5min.
                if dur <= min_dur:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too short: {dur:.2f}s. Min is {min_dur:g}s (must be greater than {min_dur:g}s).",
                    )

                if dur >= max_dur:
                    raise HTTPException(
                        status_code=400,
                        detail=f"File too long: {dur:.2f}s. Max is {max_dur:g}s (must be less than {max_dur:g}s).",
                    )

                # register input as artifact
                ctx.register(in_path)
                initial_artifact = Artifact(
                    path=in_path,
                    mime=(file.content_type or "application/octet-stream"),
                    meta={"source": "upload", "filename": file.filename, "size": total},
                )

                ctx.debug.setdefault("upload", {})
                ctx.debug["upload"].update(
                    {
                        "filename": file.filename,
                        "size": total,
                        "content_type": file.content_type,
                        "max_bytes": max_bytes,
                        "allowed_content_types": sorted(list(allowed_set)),
                    }
                )
            else:
                # payload only (no file) - allow for debug usage
                ctx.debug.setdefault("upload", {})
                ctx.debug["upload"].update({"note": "payload provided but file missing"})
        else:
            # JSON mode
            data = await request.json()
            parsed = VoiceChangerRequest.model_validate(data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {e}")

    # Fill ctx from parsed
    selected_voice_id = str(parsed.voice_id or "")
    ctx.voice_id = selected_voice_id
    ctx.stability = int(parsed.stability)
    ctx.similarity = int(parsed.similarity)
    ctx.output_format = str(parsed.output_format).lower().strip()
    ctx.preset_id = parsed.preset_id
    ctx.webhook_url = parsed.webhook_url
    ctx.options = parsed.options or {}

    # Identify user once (used by recent-used + resolving user voices)
    user_id: Optional[str] = None
    try:
        user_id = request.headers.get("x-user-id")
        if not user_id:
            auth = request.headers.get("authorization")
            if auth:
                parts = auth.split()
                if len(parts) == 2 and parts[0].lower() == "bearer":
                    user_id = parts[1].strip() or None
    except Exception:
        user_id = None

    # If frontend selects a user-created voice (user_*), resolve it to a real conversion voice.
    # Keep the selected id for recent-used tracking.
    if selected_voice_id.startswith("user_"):
        if not user_id:
            raise HTTPException(status_code=401, detail="Unauthorized: X-User-Id required for user voices")
        found = get_user_voices_by_ids(user_id, [selected_voice_id])
        if not found:
            raise HTTPException(status_code=404, detail="User voice not found")
        meta = (found[0].get("meta") or {}) if isinstance(found[0], dict) else {}
        base_voice_id = None
        if isinstance(meta, dict):
            base_voice_id = (meta.get("base_voice_id") or meta.get("baseVoiceId") or "")
        base_voice_id = str(base_voice_id).strip() if base_voice_id is not None else ""
        if not base_voice_id:
            raise HTTPException(status_code=400, detail="User voice missing base_voice_id")
        if not FunnyVoiceProvider.is_funny_voice(base_voice_id):
            raise HTTPException(status_code=400, detail="User voice base_voice_id is not supported")
        ctx.options.setdefault("voice_library", {})
        ctx.options["voice_library"].update(
            {
                "selected_voice_id": selected_voice_id,
                "resolved_base_voice_id": base_voice_id,
            }
        )
        ctx.debug.setdefault("voice_resolution", {})
        ctx.debug["voice_resolution"].update({"selected": selected_voice_id, "resolved": base_voice_id})
        ctx.voice_id = base_voice_id

    # Best-effort recent-used tracking (only if caller provides an identity).
    # Supported headers:
    # - Authorization: Bearer <user_id>
    # - X-User-Id: <user_id>
    try:
        if user_id:
            # Track what the user actually selected (user_* id), not the resolved base id.
            await record_voice_used(user_id, selected_voice_id)
    except Exception:
        pass

    # Option key compatibility: frontend uses remove_noise; ElevenLabs provider uses remove_background_noise.
    # Keep both accepted.
    if isinstance(ctx.options, dict):
        if "remove_background_noise" not in ctx.options and "remove_noise" in ctx.options:
            ctx.options["remove_background_noise"] = ctx.options.get("remove_noise")

    if ctx.output_format not in ("mp3", "wav"):
        raise HTTPException(status_code=400, detail=f"Invalid output_format: {ctx.output_format}. Must be mp3/wav.")

    # If the selected voice isn't one of our built-in funny voices, we usually require a real provider.
    # Otherwise the pipeline would effectively passthrough and confuse users ("voice mismatch").
    #
    # For a minimal demo that can "use" main-site voice ids without integrating the real provider,
    # set VC_DEMO_ALLOW_UNSUPPORTED_VOICE_ID=1.
    # Strategy can be controlled via VC_DEMO_UNSUPPORTED_VOICE_STRATEGY:
    # - map_to_funny (default): map main-site voice_id -> local funny voice effect (audible change)
    # - passthrough: export/normalize only (no audible voice change)
    demo_allow_any_voice = str(os.getenv("VC_DEMO_ALLOW_UNSUPPORTED_VOICE_ID", "")).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    if not FunnyVoiceProvider.is_funny_voice(ctx.voice_id):
        if demo_allow_any_voice:
            strategy = str(os.getenv("VC_DEMO_UNSUPPORTED_VOICE_STRATEGY", "map_to_funny")).strip().lower()
            if strategy not in {"map_to_funny", "passthrough"}:
                strategy = "map_to_funny"

            ctx.debug.setdefault("demo", {})
            ctx.debug["demo"].update(
                {
                    "allow_unsupported_voice_id": True,
                    "strategy": strategy,
                    "selected_voice_id": selected_voice_id,
                    "voice_id_requested": ctx.voice_id,
                    "eleven_api_key_present": bool(os.getenv("ELEVEN_API_KEY")),
                }
            )

            if strategy == "passthrough":
                ctx.options.setdefault("demo", {})
                if isinstance(ctx.options.get("demo"), dict):
                    ctx.options["demo"].update({"force_passthrough": True})
                ctx.debug["demo"].update(
                    {
                        "force_passthrough": True,
                        "note": "Demo passthrough: unsupported voice_id cannot be applied by local backend.",
                    }
                )
            else:
                resolved = _demo_map_to_funny_voice_id(selected_voice_id)
                ctx.debug.setdefault("voice_resolution", {})
                ctx.debug["voice_resolution"].update({"selected": selected_voice_id, "resolved": resolved})
                ctx.options.setdefault("voice_library", {})
                if isinstance(ctx.options.get("voice_library"), dict):
                    ctx.options["voice_library"].update(
                        {
                            "selected_voice_id": selected_voice_id,
                            "resolved_base_voice_id": resolved,
                        }
                    )
                ctx.debug["demo"].update(
                    {
                        "mapped_to_funny": True,
                        "resolved_voice_id": resolved,
                        "resolved_voice_name": _funny_voice_name(resolved),
                        "note": "Demo mapping: main-site voice_id mapped to a local funny voice effect.",
                    }
                )
                ctx.voice_id = resolved
        elif not os.getenv("ELEVEN_API_KEY"):
            raise HTTPException(
                status_code=400,
                detail="Unsupported voice_id for this backend. Choose a built-in voice or configure ELEVEN_API_KEY.",
            )

    # Run pipeline
    pipeline = Pipeline([
        StandardizeStep(),
        VoiceChangeStep(),
        ExportStep(),
    ])

    try:
        final_artifact = pipeline.run(initial_artifact, ctx)
    except Exception as e:
        # Keep details in debug; return sanitized error
        ctx.debug.setdefault("errors", []).append({"where": "pipeline.run", "error": str(e)})
        raise HTTPException(status_code=500, detail="Pipeline failed")

    # Respect ExportStep's produced format and published outputs
    produced_format = (final_artifact.meta or {}).get("produced_format", ctx.output_format)
    public_name = (final_artifact.meta or {}).get("public_name", f"{task_id}.{produced_format}")
    output_url = (final_artifact.meta or {}).get("public_url", f"/outputs/{public_name}")

    # enrich artifact meta for response
    artifact_meta = dict(final_artifact.meta or {})
    artifact_meta.update(
        {
            "requested_format": ctx.output_format,
            "produced_format": produced_format,
            "public_name": public_name,
            "public_url": output_url,
        }
    )

    return VoiceChangerResponse(
        task_id=task_id,
        status="success",
        output_url=output_url,
        meta={
            "echo": parsed.model_dump(),
            "artifact": artifact_meta,
            "debug": ctx.debug,
        },
    )


@router.get("/files/{task_id}/{filename}")
async def download_file(task_id: str, filename: str):
    """
    Serve a file from RUNS_BASE_DIR securely (optional debug endpoint).
    NOTE: Primary public download should use /outputs via StaticFiles.
    """
    base = os.path.abspath(RUNS_BASE_DIR)
    candidate = os.path.abspath(os.path.join(base, task_id, filename))

    # Prevent traversal
    if not candidate.startswith(os.path.join(base, task_id) + os.sep):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not os.path.isfile(candidate):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(candidate)