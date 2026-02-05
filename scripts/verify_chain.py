import json
import os
import sys
import time
from urllib import request, parse, error

BASE = "http://127.0.0.1:8000"


def get(url: str) -> (int, str):
    try:
        with request.urlopen(url, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8")
    except error.URLError as e:
        return 0, f"URLError: {e}"
    except Exception as e:
        return 0, f"Error: {e}"


def post_json(url: str, payload: dict) -> (int, str):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except error.URLError as e:
        return 0, f"URLError: {e}"
    except Exception as e:
        return 0, f"Error: {e}"


def download(url: str, out_filename: str) -> bool:
    try:
        request.urlretrieve(url, out_filename)
        return os.path.isfile(out_filename)
    except Exception:
        return False


def main():
    # Wait a moment for server to be ready
    time.sleep(1)

    # 1) Health
    status, body = get(BASE + "/healthz")
    print("health_status:", status)
    print("health_body:", body)

    # 2) POST voice-changer
    payload = {
        "voice_id": "test-voice",
        "stability": 7,
        "similarity": 8,
        "output_format": "mp3",
        "preset_id": None,
        "webhook_url": None,
        "options": {}
    }
    status, body = post_json(BASE + "/voice-changer", payload)
    print("post_status:", status)
    print("post_body:", body)

    try:
        data = json.loads(body)
    except Exception:
        print("json_parse_error")
        sys.exit(1)

    out_url = data.get("output_url")
    print("output_url:", out_url)
    if not out_url:
        print("no_output_url")
        sys.exit(1)

    full_url = BASE + out_url
    fname = os.path.basename(out_url)
    ok = download(full_url, fname)
    print("download_ok:", ok)
    if ok:
        print("downloaded:", fname, os.path.getsize(fname))
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
