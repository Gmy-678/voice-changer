import argparse
import time
from urllib import request, error


def try_get(url: str, timeout_sec: float = 3.0) -> tuple[int, str]:
    try:
        with request.urlopen(url, timeout=timeout_sec) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, body
    except error.HTTPError as e:
        try:
            body = e.read().decode("utf-8")
        except Exception:
            body = str(e)
        return e.code, body
    except Exception as e:
        return 0, f"Error: {e}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Wait until /healthz is ready")
    parser.add_argument(
        "--url",
        default="http://127.0.0.1:8000/healthz",
        help="Health check URL (default: http://127.0.0.1:8000/healthz)",
    )
    parser.add_argument(
        "--timeout-sec",
        type=float,
        default=30.0,
        help="Max seconds to wait before failing (default: 30)",
    )
    parser.add_argument(
        "--interval-sec",
        type=float,
        default=0.25,
        help="Polling interval seconds (default: 0.25)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print intermediate failures",
    )

    args = parser.parse_args()

    deadline = time.monotonic() + args.timeout_sec
    attempt = 0
    last = None

    while time.monotonic() < deadline:
        attempt += 1
        status, body = try_get(args.url)
        if status == 200:
            if not args.quiet:
                print(f"ready: {args.url}")
                print(body)
            return 0

        last = (status, body)
        if not args.quiet:
            preview = body if len(body) <= 200 else body[:200] + "..."
            print(f"attempt {attempt}: status={status} body={preview}")
        time.sleep(args.interval_sec)

    if last is None:
        print("timeout: no attempts executed")
        return 1

    status, body = last
    print(f"timeout: last status={status} body={body}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
