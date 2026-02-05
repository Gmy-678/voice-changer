from __future__ import annotations

import argparse
import os
import time
from typing import List, Tuple
import uuid as _uuid

from app.config.settings import RUNS_BASE_DIR, OUTPUTS_DIR


def _iter_old_paths(base_dir: str, older_than_seconds: int) -> List[Tuple[str, float]]:
    """
    Return [(path, mtime)] for entries in base_dir whose mtime is older than threshold.
    """
    now = time.time()
    threshold = now - older_than_seconds

    if not os.path.isdir(base_dir):
        return []

    out: List[Tuple[str, float]] = []
    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        try:
            st = os.stat(path)
        except FileNotFoundError:
            continue
        mtime = st.st_mtime
        if mtime < threshold:
            out.append((path, mtime))
    return out


def _rm_tree(path: str) -> None:
    # local tiny rmtree to avoid importing shutil if you prefer; shutil.rmtree is fine too
    import shutil
    shutil.rmtree(path, ignore_errors=True)


def _rm_file(path: str) -> None:
    try:
        os.remove(path)
    except FileNotFoundError:
        pass


def cleanup(older_than_seconds: int, apply: bool, runs_only: bool = False, outputs_only: bool = False) -> None:
    print(f"[cleanup] RUNS_BASE_DIR={RUNS_BASE_DIR}")
    print(f"[cleanup] OUTPUTS_DIR={OUTPUTS_DIR}")
    print(f"[cleanup] older_than_seconds={older_than_seconds} apply={apply} runs_only={runs_only} outputs_only={outputs_only}")

    # 1) cleanup runs/<task_id>/ directories
    if not outputs_only:
        old_runs = _iter_old_paths(RUNS_BASE_DIR, older_than_seconds)
        runs_dirs = []
        skipped_runs = 0
        for (p, m) in old_runs:
            if os.path.isdir(p):
                name = os.path.basename(p)
                # Only consider directories that look like UUIDs (extra safety)
                try:
                    _uuid.UUID(name)
                    runs_dirs.append((p, m))
                except Exception:
                    skipped_runs += 1
        if runs_dirs:
            print(f"[cleanup] candidates: {len(runs_dirs)} run dirs")
        for path, mtime in sorted(runs_dirs, key=lambda x: x[1]):
            age_hours = (time.time() - mtime) / 3600
            print(f"  - RUN dir: {path}  age={age_hours:.2f}h")
            if apply:
                _rm_tree(path)
        if skipped_runs:
            print(f"[cleanup] skipped non-UUID dirs under runs: {skipped_runs}")

    # 2) cleanup outputs files (mp3/wav)
    if not runs_only:
        old_outs = _iter_old_paths(OUTPUTS_DIR, older_than_seconds)
        out_files = []
        for (p, m) in old_outs:
            if os.path.isfile(p):
                ext = os.path.splitext(p)[1].lower()
                # Only consider typical audio outputs to avoid accidental deletes
                if ext in {".wav", ".mp3"}:
                    out_files.append((p, m))
        if out_files:
            print(f"[cleanup] candidates: {len(out_files)} output files")
        for path, mtime in sorted(out_files, key=lambda x: x[1]):
            age_hours = (time.time() - mtime) / 3600
            size = os.path.getsize(path) if os.path.exists(path) else 0
            print(f"  - OUT file: {path}  age={age_hours:.2f}h size={size}")
            if apply:
                _rm_file(path)

    print("[cleanup] done")


def main() -> None:
    parser = argparse.ArgumentParser(description="Cleanup old runs/outputs.")
    parser.add_argument("--older-than-hours", type=float, default=24.0, help="Delete entries older than N hours.")
    parser.add_argument("--apply", action="store_true", help="Actually delete. Without this flag, dry-run only.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--runs-only", action="store_true", help="Only clean runs directories.")
    group.add_argument("--outputs-only", action="store_true", help="Only clean outputs files.")
    args = parser.parse_args()

    older_than_seconds = int(args.older_than_hours * 3600)
    cleanup(
        older_than_seconds=older_than_seconds,
        apply=args.apply,
        runs_only=getattr(args, "runs_only", False),
        outputs_only=getattr(args, "outputs_only", False),
    )


if __name__ == "__main__":
    main()