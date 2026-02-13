from __future__ import annotations

import os
import shutil
import wave
import struct
import math

from app.core.artifacts import Artifact, TaskContext
from app.services.providers.elevenlabs import ElevenLabsVoiceChangerHTTP, ElevenLabsProviderError
from app.services.providers.funny_voice import FunnyVoiceProvider


class VoiceChangeStep:
    name = "voice_change"

    def _synthesize_wav(self, path: str, duration_sec: float = 1.0, sr: int = 16000) -> None:
        freq = 440.0
        nframes = int(sr * duration_sec)
        ampl = 16000
        with wave.open(path, "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            for i in range(nframes):
                v = int(ampl * math.sin(2 * math.pi * freq * (i / sr)))
                w.writeframes(struct.pack("<h", v))

    def _run_funny_voice(
        self, 
        artifact: Artifact, 
        ctx: TaskContext, 
        input_path: str, 
        converted_path: str,
        fallback_dur: float
    ) -> Artifact:
        """使用本地搞怪音色处理"""
        input_missing = not input_path or not os.path.isfile(input_path)
        
        if input_missing:
            # 没有输入文件，生成一个占位音频
            self._synthesize_wav(converted_path, duration_sec=fallback_dur)
            ctx.register(converted_path)
            meta = dict(artifact.meta or {})
            meta.update({
                "provider": "funny_voice",
                "provider_status": "no_input",
                "note": "No input file provided, generated placeholder.",
            })
            ctx.debug.setdefault("provider", {})
            ctx.debug["provider"].update({
                "name": "funny_voice",
                "status": "no_input",
            })
            return Artifact(path=converted_path, mime="audio/wav", meta=meta)
        
        try:
            provider = FunnyVoiceProvider()
            result = provider.convert(
                voice_id=ctx.voice_id,
                audio_path=input_path,
                output_format="wav",
            )
            
            with open(converted_path, "wb") as f:
                f.write(result.audio_bytes)
            
            ctx.register(converted_path)
            
            meta = dict(artifact.meta or {})
            meta.update(result.meta or {})
            meta.update({
                "provider": "funny_voice",
                "provider_status": "ok",
                "converted_path": converted_path,
            })
            ctx.debug.setdefault("provider", {})
            ctx.debug["provider"].update({
                "name": "funny_voice", 
                "status": "ok",
                "effect": result.meta.get("effect", ctx.voice_id),
            })
            
            return Artifact(path=converted_path, mime="audio/wav", meta=meta)
            
        except Exception as e:
            # 出错时直接复制原文件
            shutil.copyfile(input_path, converted_path)
            ctx.register(converted_path)
            ctx.debug.setdefault("provider", {})
            ctx.debug["provider"].update({
                "name": "funny_voice",
                "status": "error",
                "error": str(e),
            })
            ctx.debug.setdefault("errors", []).append({
                "step": self.name,
                "error": str(e),
            })
            meta = dict(artifact.meta or {})
            meta.update({
                "provider": "funny_voice",
                "provider_status": "error_fallback",
                "note": str(e),
            })
            return Artifact(path=converted_path, mime="audio/wav", meta=meta)

    def run(self, artifact: Artifact, ctx: TaskContext) -> Artifact:
        ctx.ensure_dirs()

        input_path = artifact.path
        converted_path = ctx.path("converted.wav")

        fallback_dur = 1.0
        try:
            fallback_dur = float(os.getenv("VC_FALLBACK_DURATION", "1.0"))
        except Exception:
            pass

        # Demo mode: force passthrough for unsupported voice ids so the pipeline still produces
        # a usable output (matching duration) without requiring a real provider.
        force_passthrough = False
        try:
            opts = ctx.options or {}
            demo = opts.get("demo") if isinstance(opts, dict) else None
            if isinstance(demo, dict) and demo.get("force_passthrough"):
                force_passthrough = True
        except Exception:
            force_passthrough = False

        if force_passthrough:
            input_missing = not input_path or not os.path.isfile(input_path)
            if input_missing:
                self._synthesize_wav(converted_path, duration_sec=fallback_dur)
            else:
                shutil.copyfile(input_path, converted_path)
            ctx.register(converted_path)
            ctx.debug.setdefault("provider", {})
            ctx.debug["provider"].update({"name": "passthrough", "status": "demo_force_passthrough"})
            meta = dict(artifact.meta or {})
            meta.update(
                {
                    "provider": "passthrough",
                    "provider_status": "demo_force_passthrough",
                    "note": "Demo mode passthrough: voice not applied.",
                }
            )
            return Artifact(path=converted_path, mime="audio/wav", meta=meta)

        # 检查是否是搞怪音色，优先使用本地处理
        if FunnyVoiceProvider.is_funny_voice(ctx.voice_id):
            return self._run_funny_voice(artifact, ctx, input_path, converted_path, fallback_dur)

        # If provider disabled or input missing, synthesize a WAV fallback
        provider_disabled = not os.getenv("ELEVEN_API_KEY")
        input_missing = not input_path or not os.path.isfile(input_path)

        if provider_disabled or input_missing:
            if input_missing:
                self._synthesize_wav(converted_path, duration_sec=fallback_dur)
            else:
                shutil.copyfile(input_path, converted_path)
            ctx.register(converted_path)

            meta = dict(artifact.meta or {})
            meta.update(
                {
                    "provider": "mock" if provider_disabled else "passthrough",
                    "provider_status": "disabled_no_api_key" if provider_disabled else "no_input",
                    "note": "ELEVEN_API_KEY not set; bypassed voice conversion." if provider_disabled else "No input; synthesized/used fallback.",
                }
            )
            ctx.debug.setdefault("provider", {})
            ctx.debug["provider"].update({
                "name": "mock" if provider_disabled else "passthrough",
                "status": "disabled_no_api_key" if provider_disabled else "no_input",
            })
            return Artifact(path=converted_path, mime="audio/wav", meta=meta)

        # Real provider path
        try:
            provider = ElevenLabsVoiceChangerHTTP()
            opts = ctx.options or {}
            remove_bg = opts.get("remove_background_noise")
            if remove_bg is None:
                remove_bg = opts.get("remove_noise")

            result = provider.convert(
                voice_id=ctx.voice_id,
                audio_path=input_path,
                model_id=getattr(ctx, "model_id", None),
                stability=ctx.stability,
                similarity=ctx.similarity,
                output_format="wav",
                remove_background_noise=remove_bg if remove_bg is not None else None,
                extra=None,
            )

            with open(converted_path, "wb") as f:
                f.write(result.audio_bytes)

            ctx.register(converted_path)

            meta = dict(artifact.meta or {})
            meta.update(result.meta or {})
            meta.update(
                {
                    "provider": "elevenlabs",
                    "provider_status": "ok",
                    "converted_path": converted_path,
                }
            )
            ctx.debug.setdefault("provider", {})
            ctx.debug["provider"].update({"name": "elevenlabs", "status": "ok"})

            return Artifact(path=converted_path, mime="audio/wav", meta=meta)

        except ElevenLabsProviderError as e:
            # Fallback to synthesized audio on provider error
            self._synthesize_wav(converted_path, duration_sec=fallback_dur)
            ctx.register(converted_path)
            ctx.debug.setdefault("provider", {})
            ctx.debug["provider"].update({"name": "elevenlabs", "status": "error", "error": str(e)})
            ctx.debug.setdefault("errors", []).append({"step": self.name, "error": str(e)})
            meta = dict(artifact.meta or {})
            meta.update({
                "provider": "elevenlabs",
                "provider_status": "error_fallback",
                "note": str(e),
            })
            return Artifact(path=converted_path, mime="audio/wav", meta=meta)