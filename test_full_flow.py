#!/usr/bin/env python3
from fastapi.testclient import TestClient
from app.main import app
import json
import os

client = TestClient(app)
path = '/Users/noizer/voice-changer/tmp/test.wav'

# ElevenLabs 示例 voice_id（Rachel）
voice_id = "21m00Tcm4TlvDq8ikWAM"

payload = {
    "voice_id": voice_id,
    "stability": 7,
    "similarity": 8,
    "output_format": "mp3",
    "preset_id": None,
    "webhook_url": None,
    "options": {}
}
files = {
    'file': ('test.wav', open(path, 'rb'), 'application/octet-stream')
}
print(f"Testing with voice_id={voice_id}")
resp = client.post('/voice-changer', files=files, data={'payload': json.dumps(payload)})
print('status=', resp.status_code)
js = resp.json()

if resp.status_code == 200:
    print('output_url=', js.get('output_url'))
    vc_debug = js.get('meta', {}).get('debug', {}).get('voice_change', {})
    print('provider=', vc_debug.get('provider', 'N/A'))
    print('latency_ms=', vc_debug.get('latency_ms', 'N/A'))
else:
    print('error=', js)
