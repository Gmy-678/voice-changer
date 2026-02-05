#!/usr/bin/env python
"""
测试搞怪音色处理功能
"""
import os
import sys
import tempfile
import wave
import struct
import math

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.providers.funny_voice import FunnyVoiceProvider


def create_test_audio(path: str, duration_sec: float = 2.0, sr: int = 44100):
    """创建测试音频文件"""
    freq = 440.0  # A4 音符
    nframes = int(sr * duration_sec)
    ampl = 16000
    
    with wave.open(path, "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        for i in range(nframes):
            # 添加一些谐波使声音更丰富
            t = i / sr
            v = int(ampl * (
                0.5 * math.sin(2 * math.pi * freq * t) +
                0.25 * math.sin(2 * math.pi * freq * 2 * t) +
                0.125 * math.sin(2 * math.pi * freq * 3 * t)
            ))
            w.writeframes(struct.pack("<h", max(-32768, min(32767, v))))
    
    print(f"✅ 创建测试音频: {path} ({duration_sec}秒, {sr}Hz)")


def test_funny_voices():
    """测试所有搞怪音色"""
    provider = FunnyVoiceProvider()
    
    # 创建临时测试音频
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        test_audio_path = tmp.name
    
    try:
        create_test_audio(test_audio_path)
        
        print("\n🎭 测试美国热搜榜音色:\n")
        
        for voice_id in FunnyVoiceProvider.SUPPORTED_VOICES:
            try:
                result = provider.convert(
                    voice_id=voice_id,
                    audio_path=test_audio_path,
                    output_format="wav"
                )
                
                print(f"  🎤 {voice_id}:")
                print(f"     效果: {result.meta.get('effect', 'N/A')}")
                print(f"     原始时长: {result.meta.get('original_duration_ms', 0)}ms")
                print(f"     处理后时长: {result.meta.get('processed_duration_ms', 0)}ms")
                print(f"     输出大小: {len(result.audio_bytes)} bytes")
                print()
                
                # 保存处理后的音频用于人工检查
                output_path = f"/tmp/funny_voice_{voice_id}.wav"
                with open(output_path, "wb") as f:
                    f.write(result.audio_bytes)
                print(f"     ✅ 已保存到: {output_path}")
                print()
                
            except Exception as e:
                print(f"  ❌ {voice_id}: 处理失败 - {e}")
                print()
        
        print("🎉 测试完成!")
        print("\n💡 提示: 可以播放 /tmp/funny_voice_*.wav 文件来听效果")
        
    finally:
        if os.path.exists(test_audio_path):
            os.unlink(test_audio_path)


if __name__ == "__main__":
    test_funny_voices()
