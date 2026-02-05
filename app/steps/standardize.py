from app.core.artifacts import Artifact, TaskContext
from app.services.ffmpeg import standardize_to_wav, FFmpegError, is_available as ffmpeg_available
from app.services.media_probe import probe_duration_seconds, is_ffprobe_available


class StandardizeStep:
    """
    Normalize all inputs into a standard WAV format:
    - audio extracted from video if needed
    - mono channel
    - 48kHz sample rate
    """

    name = "standardize"

    def run(self, artifact: Artifact, ctx: TaskContext) -> Artifact:
        # ensure workspace exists
        ctx.ensure_dirs()

        # If there is no input file yet, skip and pass through
        if not artifact.path or not artifact.path.strip():
            ctx.debug.setdefault("standardize", {}).update({"skipped": True, "reason": "no input"})
            return artifact

        # Optional: probe input media duration for debugging/metrics
        try:
            if is_ffprobe_available():
                dur = probe_duration_seconds(artifact.path)
                ctx.debug.setdefault("input_media", {})["duration_seconds"] = dur
        except Exception:
            # ignore probe errors; keep pipeline robust
            pass

        output_path = ctx.path("standardized.wav")

        # Run ffmpeg standardization if available; else pass through
        if not ffmpeg_available():
            ctx.debug.setdefault("standardize", {}).update({"skipped": True, "reason": "ffmpeg unavailable"})
            return artifact

        try:
            standardize_to_wav(
                input_path=artifact.path,
                output_path=output_path,
            )
        except FFmpegError as e:
            ctx.debug.setdefault("errors", []).append({
                "step": self.name,
                "error": str(e),
                "type": e.__class__.__name__,
            })
            # On failure, pass through original artifact
            return artifact

        # register intermediate artifact
        ctx.register(output_path)

        return Artifact(
            path=output_path,
            mime="audio/wav",
            meta={
                "sample_rate": 48000,
                "channels": 1,
                "source": artifact.path,
            }
        )