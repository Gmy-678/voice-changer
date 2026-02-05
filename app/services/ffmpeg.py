from __future__ import annotations

import subprocess
from typing import List, Optional


class FfmpegError(RuntimeError):
    pass


def is_available() -> bool:
    """Return True if ffmpeg is available on PATH."""
    try:
        subprocess.run(["ffmpeg", "-version"], check=True, capture_output=True)
        return True
    except Exception:
        return False


def transcode_audio(
    *,
    in_path: str,
    out_path: str,
    output_format: str,
    sample_rate: Optional[int] = None,
    bitrate: Optional[str] = None,
    extra_afilters: Optional[List[str]] = None,
    timeout_sec: int = 60,
) -> None:
    fmt = output_format.lower().strip()
    if fmt not in ("mp3", "wav"):
        raise ValueError(f"output_format must be mp3 or wav, got: {output_format!r}")

    # 音频滤镜：拼接为 -af filter1,filter2
    afilters: List[str] = []
    if extra_afilters:
        afilters.extend([f for f in extra_afilters if f])

    cmd: List[str] = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", in_path]

    if sample_rate:
        cmd += ["-ar", str(int(sample_rate))]

    if afilters:
        cmd += ["-af", ",".join(afilters)]

    if fmt == "mp3":
        # 默认 mp3 编码参数：先给稳妥值，后续可通过 options 调整
        cmd += ["-codec:a", "libmp3lame"]
        cmd += ["-b:a", bitrate or "192k"]
        cmd += ["-f", "mp3", out_path]
    else:
        # wav：PCM 16-bit
        cmd += ["-codec:a", "pcm_s16le", "-f", "wav", out_path]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout_sec)
    except subprocess.TimeoutExpired as e:
        raise FfmpegError(f"ffmpeg timeout after {timeout_sec}s: {e}") from e
    except subprocess.CalledProcessError as e:
        raise FfmpegError(f"ffmpeg failed: {e.stderr or e.stdout or str(e)}") from e


# Backward-compatible API expected by steps
def standardize_to_wav(*, input_path: str, output_path: str, sample_rate: int = 48000, mono: bool = True) -> None:
    filters: List[str] = []
    if mono:
        # Prefer channel layout normalization for wide compatibility
        filters.append("aformat=channel_layouts=mono")
    transcode_audio(
        in_path=input_path,
        out_path=output_path,
        output_format="wav",
        sample_rate=sample_rate,
        extra_afilters=filters,
    )


def convert_wav_to_mp3(input_path: str, output_path: str, *, bitrate: str = "192k", sample_rate: Optional[int] = None) -> None:
    transcode_audio(
        in_path=input_path,
        out_path=output_path,
        output_format="mp3",
        sample_rate=sample_rate,
        bitrate=bitrate,
    )


# Alias to old exception name used by steps
FFmpegError = FfmpegError