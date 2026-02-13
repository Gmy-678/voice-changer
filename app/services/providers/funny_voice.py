"""
本地搞怪音色处理服务
使用 ffmpeg 音频滤镜实现 5 种搞怪音效:
- chipmunk: 花栗鼠 (高音加速)
- robot: 机器人 (音频环调制)
- ghost: 幽灵 (低沉回声)
- giant: 巨人 (低音减速)
- helium: 氦气少女 (高音变调)
"""

from __future__ import annotations
import os
import tempfile
from dataclasses import dataclass

from app.services.ffmpeg import FFmpegError, is_available as ffmpeg_available, transcode_audio


@dataclass
class FunnyVoiceResult:
    audio_bytes: bytes
    meta: dict


class FunnyVoiceProvider:
    """本地搞怪音色处理 provider - 美国热搜榜音色"""
    
    # 支持的音色 ID 列表
    SUPPORTED_VOICES = ['anime_uncle', 'uwu_anime', 'gender_swap', 'mamba', 'nerd_bro']
    
    @classmethod
    def is_funny_voice(cls, voice_id: str) -> bool:
        """检查是否是搞怪音色"""
        return voice_id in cls.SUPPORTED_VOICES
    
    def convert(
        self,
        voice_id: str,
        audio_path: str,
        output_format: str = "wav",
        **kwargs
    ) -> FunnyVoiceResult:
        """
        转换音频为搞怪音色
        
        Args:
            voice_id: 音色ID (chipmunk/robot/ghost/giant/helium)
            audio_path: 输入音频路径
            output_format: 输出格式
            
        Returns:
            FunnyVoiceResult with audio bytes and metadata
        """
        if not os.path.isfile(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
        if voice_id not in self.SUPPORTED_VOICES:
            raise ValueError(f"Unsupported funny voice: {voice_id}")

        if not ffmpeg_available():
            raise RuntimeError("ffmpeg is required for funny voice effects. Please install ffmpeg.")

        # 统一采样率，便于 pitch shift 表达式稳定
        sample_rate = 48000

        # 根据音色 ID 应用不同效果 - 美国热搜榜音色
        afilters = self._get_ffmpeg_filters(voice_id=voice_id, sample_rate=sample_rate)

        with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            transcode_audio(
                in_path=audio_path,
                out_path=tmp_path,
                output_format=output_format,
                sample_rate=sample_rate,
                extra_afilters=afilters,
                timeout_sec=120,
            )
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()
        except FFmpegError as e:
            raise RuntimeError(str(e)) from e
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
            except Exception:
                pass
        
        return FunnyVoiceResult(
            audio_bytes=audio_bytes,
            meta={
                "voice_id": voice_id,
                "effect": self._get_effect_name(voice_id),
                "filters": afilters,
            }
        )
    
    def _get_effect_name(self, voice_id: str) -> str:
        """获取效果名称"""
        names = {
            'anime_uncle': 'Anime Uncle - 动漫大叔',
            'uwu_anime': 'UwU Anime - 二次元萌音',
            'gender_swap': 'Gender Swap - 跨性别变声',
            'mamba': 'Mamba Mode - 科比曼巴',
            'nerd_bro': 'Nerd Bro - 书呆子老哥',
        }
        return names.get(voice_id, voice_id)
    
    def _pitch_shift_filters(self, *, sample_rate: int, factor: float) -> list[str]:
        # 说明：asetrate 会同时改变 pitch+速度；再用 atempo 纠正速度，从而近似“只变调”。
        # atempo 支持 0.5~2.0，本项目 factor 都落在可用范围。
        return [
            f"asetrate={sample_rate}*{factor}",
            f"aresample={sample_rate}",
            f"atempo={1.0/factor:.6f}",
        ]

    def _get_ffmpeg_filters(self, *, voice_id: str, sample_rate: int) -> list[str]:
        if voice_id == "anime_uncle":
            # 低沉 + 轻微回声
            return [
                *self._pitch_shift_filters(sample_rate=sample_rate, factor=0.75),
                "volume=1.4",
                "aecho=0.8:0.88:80:0.25",
            ]

        if voice_id == "uwu_anime":
            return [
                *self._pitch_shift_filters(sample_rate=sample_rate, factor=1.4),
                "volume=1.2",
            ]

        if voice_id == "gender_swap":
            return [
                *self._pitch_shift_filters(sample_rate=sample_rate, factor=1.25),
                "highpass=f=120",
                "lowpass=f=12000",
            ]

        if voice_id == "mamba":
            return [
                *self._pitch_shift_filters(sample_rate=sample_rate, factor=0.9),
                "volume=1.5",
                "acompressor=threshold=-18dB:ratio=3:attack=20:release=200",
            ]

        if voice_id == "nerd_bro":
            return [
                *self._pitch_shift_filters(sample_rate=sample_rate, factor=1.1),
                "tremolo=f=120:d=0.15",
            ]

        return []
