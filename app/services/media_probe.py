from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Optional


class MediaProbeError(RuntimeError):
    pass


def is_ffprobe_available() -> bool:
    """Return True if ffprobe is available on PATH."""
    try:
        subprocess.run(["ffprobe", "-version"], check=True, capture_output=True)
        return True
    except Exception:
        return False


def probe_duration_seconds(path: str, timeout_sec: int = 10) -> Optional[float]:
    """
    Return duration in seconds if available, else None.
    Uses ffprobe (ffmpeg).
    """
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        path,
    ]
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_sec)
    except FileNotFoundError as e:
        raise MediaProbeError("ffprobe not found. Please install ffmpeg.") from e
    except subprocess.TimeoutExpired as e:
        raise MediaProbeError("ffprobe timed out.") from e

    if p.returncode != 0:
        raise MediaProbeError(f"ffprobe failed: {p.stderr.strip() or p.stdout.strip()}")

    try:
        data = json.loads(p.stdout)
        dur = data.get("format", {}).get("duration")
        if dur is None:
            return None
        return float(dur)
    except Exception:
        return None


def _print_err(message: str) -> None:
    print(message, file=sys.stderr)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Probe media duration using ffprobe.")
    parser.add_argument("path", help="Path to media file")
    parser.add_argument("--timeout", type=int, default=10, help="Timeout seconds for ffprobe (default: 10)")
    args = parser.parse_args()

    if not is_ffprobe_available():
        _print_err("ffprobe not found on PATH. Please install ffmpeg.")
        sys.exit(1)

    if not os.path.exists(args.path):
        _print_err(f"Input file does not exist: {args.path}")
        sys.exit(2)

    try:
        duration = probe_duration_seconds(args.path, timeout_sec=args.timeout)
    except MediaProbeError as exc:
        _print_err(f"Probe error: {exc}")
        sys.exit(1)

    result = {
        "path": args.path,
        "duration_seconds": duration,
    }
    print(json.dumps(result))
    sys.exit(0)
