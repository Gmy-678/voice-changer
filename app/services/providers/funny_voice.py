"""
本地搞怪音色处理服务
使用 pydub 和 numpy 实现5种搞怪音效:
- chipmunk: 花栗鼠 (高音加速)
- robot: 机器人 (音频环调制)
- ghost: 幽灵 (低沉回声)
- giant: 巨人 (低音减速)
- helium: 氦气少女 (高音变调)
"""

from __future__ import annotations
import os
import tempfile
import numpy as np
from typing import Optional
from dataclasses import dataclass


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
        
        # 导入音频处理库
        try:
            from pydub import AudioSegment
        except ImportError:
            raise RuntimeError("pydub is required for funny voice effects. Install with: pip install pydub")
        
        # 加载音频
        audio = AudioSegment.from_file(audio_path)
        
        # 根据音色 ID 应用不同效果 - 美国热搜榜音色
        if voice_id == 'anime_uncle':
            processed = self._apply_anime_uncle(audio)
        elif voice_id == 'uwu_anime':
            processed = self._apply_uwu_anime(audio)
        elif voice_id == 'gender_swap':
            processed = self._apply_gender_swap(audio)
        elif voice_id == 'mamba':
            processed = self._apply_mamba(audio)
        elif voice_id == 'nerd_bro':
            processed = self._apply_nerd_bro(audio)
        else:
            processed = audio
        
        # 导出为字节
        with tempfile.NamedTemporaryFile(suffix=f".{output_format}", delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            processed.export(tmp_path, format=output_format)
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
        
        return FunnyVoiceResult(
            audio_bytes=audio_bytes,
            meta={
                "voice_id": voice_id,
                "effect": self._get_effect_name(voice_id),
                "original_duration_ms": len(audio),
                "processed_duration_ms": len(processed),
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
    
    def _apply_anime_uncle(self, audio) -> 'AudioSegment':
        """
        动漫大叔效果: 夸张的低沉声音 + 轻微回声
        模仿日本动漫中夸张的大叔配音风格 "NANI?!"
        """
        # 降低音调 0.75 倍，让声音更低沉
        new_sample_rate = int(audio.frame_rate * 0.75)
        lowered = audio._spawn(
            audio.raw_data,
            overrides={'frame_rate': new_sample_rate}
        ).set_frame_rate(audio.frame_rate)
        
        # 增加一点音量让声音更有力
        lowered = lowered + 3
        
        # 添加轻微回声增加戏剧感
        delay_ms = 80
        silence = type(audio).silent(duration=delay_ms)
        delayed = silence + lowered - 8
        
        if len(delayed) > len(lowered):
            lowered = lowered + type(audio).silent(duration=len(delayed) - len(lowered))
        else:
            delayed = delayed + type(audio).silent(duration=len(lowered) - len(delayed))
        
        return lowered.overlay(delayed)
    
    def _apply_uwu_anime(self, audio) -> 'AudioSegment':
        """
        二次元萌音效果: 高音调 + 甜美感
        Kawaii desu~ UwU 风格
        """
        # 提高音调 1.4 倍，让声音更尖细可爱
        new_sample_rate = int(audio.frame_rate * 1.4)
        
        high_pitched = audio._spawn(
            audio.raw_data,
            overrides={'frame_rate': new_sample_rate}
        ).set_frame_rate(audio.frame_rate)
        
        # 轻微增加音量
        result = high_pitched + 2
        
        return result
    
    def _apply_gender_swap(self, audio) -> 'AudioSegment':
        """
        跨性别变声效果: 男声转女声
        提高音调让声音更女性化
        """
        # 提高音调 1.25 倍，适度提高不会太假
        new_sample_rate = int(audio.frame_rate * 1.25)
        
        feminized = audio._spawn(
            audio.raw_data,
            overrides={'frame_rate': new_sample_rate}
        ).set_frame_rate(audio.frame_rate)
        
        # 轻微柔化处理
        samples = np.array(feminized.get_array_of_samples())
        
        # 简单的平滑处理让声音更柔和
        kernel_size = 3
        kernel = np.ones(kernel_size) / kernel_size
        smoothed = np.convolve(samples, kernel, mode='same').astype(np.int16)
        
        result = feminized._spawn(
            smoothed.tobytes(),
            overrides={'frame_rate': feminized.frame_rate}
        )
        
        return result
    
    def _apply_mamba(self, audio) -> 'AudioSegment':
        """
        科比曼巴效果: 沉稳有力的声音
        模仿科比那种自信、有力的说话风格
        """
        # 略微降低音调 0.9 倍，让声音更沉稳
        new_sample_rate = int(audio.frame_rate * 0.9)
        
        deep_voice = audio._spawn(
            audio.raw_data,
            overrides={'frame_rate': new_sample_rate}
        ).set_frame_rate(audio.frame_rate)
        
        # 增加音量让声音更有力量感
        result = deep_voice + 4
        
        # 添加轻微压缩效果（通过限幅模拟）
        samples = np.array(result.get_array_of_samples())
        max_val = np.max(np.abs(samples)) * 0.85
        compressed = np.clip(samples, -max_val, max_val).astype(np.int16)
        
        result = result._spawn(
            compressed.tobytes(),
            overrides={'frame_rate': result.frame_rate}
        )
        
        return result
    
    def _apply_nerd_bro(self, audio) -> 'AudioSegment':
        """
        书呆子老哥效果: 略带鼻音的书呆子风格
        "Actually..." *pushes glasses* 那种感觉
        """
        # 轻微提高音调 1.1 倍
        new_sample_rate = int(audio.frame_rate * 1.1)
        
        nasally = audio._spawn(
            audio.raw_data,
            overrides={'frame_rate': new_sample_rate}
        ).set_frame_rate(audio.frame_rate)
        
        # 添加轻微的「鼻音」效果 - 通过低频调制模拟
        samples = np.array(nasally.get_array_of_samples())
        sample_rate = nasally.frame_rate
        
        # 创建轻微的调制
        t = np.arange(len(samples)) / sample_rate
        mod_freq = 120  # 鼻腔共振频率
        modulator = 0.85 + 0.15 * np.sin(2 * np.pi * mod_freq * t)
        
        modulated = (samples * modulator).astype(np.int16)
        
        result = nasally._spawn(
            modulated.tobytes(),
            overrides={'frame_rate': sample_rate}
        )
        
        return result
