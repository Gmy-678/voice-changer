import os, math, wave, struct, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.ffmpeg import is_available, convert_wav_to_mp3

print("ffmpeg_available:", is_available())

sr=16000
n=sr//2
wav_path="tmp_test.wav"
mp3_path="tmp_test.mp3"

with wave.open(wav_path, "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(sr)
    for i in range(n):
        s=int(0.3*32767*math.sin(2*math.pi*440*i/sr))
        w.writeframes(struct.pack('<h', s))

if is_available():
    try:
        convert_wav_to_mp3(wav_path, mp3_path)
        print("mp3_exists:", os.path.isfile(mp3_path))
    except Exception as e:
        print("conversion_error:", str(e))
else:
    print("ffmpeg not available; skipping conversion")

print("wav_exists:", os.path.isfile(wav_path))
