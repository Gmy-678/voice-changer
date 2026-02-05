from __future__ import annotations

import json
import os
import shutil
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Form
from fastapi.responses import FileResponse

from .schemas import VoiceChangerRequest, VoiceChangerResponse

from app.config.settings import RUNS_BASE_DIR
from app.core.artifacts import Artifact, TaskContext
from app.core.pipeline import Pipeline
from app.steps.standardize import StandardizeStep
from app.steps.voice_change import VoiceChangeStep
from app.steps.export import ExportStep
from app.services.media_probe import probe_duration_seconds, MediaProbeError


router = APIRouter(prefix="/voice-changer", tags=["voice-changer"])


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
                        if not allowed_set:
                            allowed_set = allowed_default
                    except Exception:
                        allowed_set = allowed_default
                else:
                    allowed_set = allowed_default

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
                max_bytes_env = os.getenv("UPLOAD_MAX_BYTES", "10485760")  # 10 MB default
                try:
                    max_bytes = int(max_bytes_env)
                except Exception:
                    max_bytes = 10 * 1024 * 1024

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

                if dur is not None:
                    ctx.debug.setdefault("probe", {})
                    ctx.debug["probe"].update({"duration_sec": dur})

                    if dur > 5 * 60:
                        raise HTTPException(
                            status_code=400,
                            detail=f"File too long: {dur:.2f}s. Max is 300s (5 minutes).",
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
    ctx.voice_id = parsed.voice_id
    ctx.stability = int(parsed.stability)
    ctx.similarity = int(parsed.similarity)
    ctx.output_format = str(parsed.output_format).lower().strip()
    ctx.preset_id = parsed.preset_id
    ctx.webhook_url = parsed.webhook_url
    ctx.options = parsed.options or {}

    if ctx.output_format not in ("mp3", "wav"):
        raise HTTPException(status_code=400, detail=f"Invalid output_format: {ctx.output_format}. Must be mp3/wav.")

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