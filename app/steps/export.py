from __future__ import annotations

import os
import shutil

from app.core.artifacts import Artifact, TaskContext
from app.services.ffmpeg import convert_wav_to_mp3, is_available as ffmpeg_available, FFmpegError
from app.config.settings import OUTPUTS_DIR


class ExportStep:
	name = "export"

	def run(self, artifact: Artifact, ctx: TaskContext) -> Artifact:
		# We only have WAV right now; if mp3 requested, still output WAV
		requested = (ctx.output_format or "wav").lower()
		src = os.path.abspath(artifact.path)
		if not os.path.isfile(src):
			raise FileNotFoundError(f"Export source missing: {src}")

		if requested == "mp3":
			out_name = "output.mp3"
			out_path = ctx.path(out_name)
			if not ffmpeg_available():
				# Fallback to WAV copy if ffmpeg unavailable
				fallback = ctx.path("output.wav")
				shutil.copyfile(src, fallback)
				# Also copy to public outputs directory for static serving
				public_name = f"{ctx.task_id}.wav"
				public_path = os.path.join(OUTPUTS_DIR, public_name)
				shutil.copyfile(fallback, public_path)
				ctx.register_output(fallback)
				meta = {
					"requested_format": requested,
					"produced_format": "wav",
					"note": "ffmpeg not available; produced WAV instead",
					"public_name": public_name,
					"public_url": f"/outputs/{public_name}",
				}
				return Artifact(path=fallback, mime="audio/wav", meta=meta)
			try:
				convert_wav_to_mp3(src, out_path)
				# Copy final MP3 to public outputs directory
				public_name = f"{ctx.task_id}.mp3"
				public_path = os.path.join(OUTPUTS_DIR, public_name)
				shutil.copyfile(out_path, public_path)
				ctx.register_output(out_path)
				meta = {
					"requested_format": requested,
					"produced_format": "mp3",
					"public_name": public_name,
					"public_url": f"/outputs/{public_name}",
				}
				return Artifact(path=out_path, mime="audio/mpeg", meta=meta)
			except FFmpegError as e:
				# On conversion failure, fall back to WAV
				fallback = ctx.path("output.wav")
				shutil.copyfile(src, fallback)
				public_name = f"{ctx.task_id}.wav"
				public_path = os.path.join(OUTPUTS_DIR, public_name)
				shutil.copyfile(fallback, public_path)
				ctx.register_output(fallback)
				meta = {
					"requested_format": requested,
					"produced_format": "wav",
					"error": str(e),
					"public_name": public_name,
					"public_url": f"/outputs/{public_name}",
				}
				return Artifact(path=fallback, mime="audio/wav", meta=meta)

		# default: produce WAV
		out_name = "output.wav"
		out_path = ctx.path(out_name)
		shutil.copyfile(src, out_path)
		public_name = f"{ctx.task_id}.wav"
		public_path = os.path.join(OUTPUTS_DIR, public_name)
		shutil.copyfile(out_path, public_path)
		ctx.register_output(out_path)
		meta = {
			"requested_format": requested,
			"produced_format": "wav",
			"public_name": public_name,
			"public_url": f"/outputs/{public_name}",
		}
		return Artifact(path=out_path, mime="audio/wav", meta=meta)
