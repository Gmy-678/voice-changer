from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Set
import os
import shutil


@dataclass
class Artifact:
    """
    Pipeline artifact, typically a file produced by a step.
    Keep it minimal: path + mime + metadata.
    """
    path: str
    mime: str = "application/octet-stream"
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskContext:
    """
    Owns the lifecycle for a single voice changer task.

    What it provides:
    - Stable request parameters (voice_id, stability/similarity, output_format, preset_id, webhook_url)
    - Unified file path helpers (ctx.path(...))
    - Track generated files for cleanup (ctx.register / ctx.register_output)
    - Extensible fields for future features (options, debug)
    """

    # identity / workspace
    task_id: str
    task_dir: str

    # request params (stable contract)
    voice_id: str
    stability: int                 # 1-10 integer (step=1)
    similarity: int                # 1-10 integer (step=1)
    output_format: str             # "mp3" | "wav"
    preset_id: Optional[str] = None
    webhook_url: Optional[str] = None

    # extensibility hooks
    options: Dict[str, Any] = field(default_factory=dict)   # future: noise, chunking, provider, etc.
    debug: Dict[str, Any] = field(default_factory=dict)     # future: metrics, timing, request ids, etc.

    # cleanup policy
    cleanup_mode: str = "none"
    """
    cleanup_mode:
      - "none": keep everything (good for local debug)
      - "intermediates": delete intermediate files, keep registered outputs
      - "all": delete the entire task_dir (useful after uploading to object storage)
    """

    # internal tracking
    _generated_files: Set[str] = field(default_factory=set, init=False)
    _output_files: Set[str] = field(default_factory=set, init=False)

    def __post_init__(self) -> None:
        """
        Normalize and ensure the task directory exists early.
        """
        self.task_dir = os.path.abspath(self.task_dir)
        os.makedirs(self.task_dir, exist_ok=True)

    def _resolve_in_task_dir(self, filename: str) -> str:
        """
        Resolve a filename within task_dir and prevent directory traversal.
        """
        candidate = os.path.abspath(os.path.join(self.task_dir, filename))
        if not candidate.startswith(self.task_dir + os.sep):
            raise ValueError("Filename escapes task_dir: " + filename)
        return candidate

    def ensure_dirs(self) -> None:
        """Ensure task_dir exists."""
        os.makedirs(self.task_dir, exist_ok=True)

    def path(self, filename: str) -> str:
        """Get a safe path inside task_dir for a given filename."""
        return self._resolve_in_task_dir(filename)

    def register(self, file_path: str) -> None:
        """Register a file generated during the task (only within task_dir)."""
        abs_path = os.path.abspath(file_path)
        if abs_path.startswith(self.task_dir + os.sep):
            self._generated_files.add(abs_path)

    def register_output(self, file_path: str) -> None:
        """
        Register a file as a final output.
        This will be kept when cleanup_mode='intermediates'.
        """
        abs_path = os.path.abspath(file_path)
        if abs_path.startswith(self.task_dir + os.sep):
            self._output_files.add(abs_path)
            self.register(abs_path)

    def list_generated_files(self) -> Set[str]:
        return set(self._generated_files)

    def list_output_files(self) -> Set[str]:
        return set(self._output_files)

    def cleanup(self) -> None:
        """Cleanup files according to cleanup_mode."""
        mode = (self.cleanup_mode or "none").lower().strip()

        if mode == "none":
            return

        if mode == "all":
            shutil.rmtree(self.task_dir, ignore_errors=True)
            return

        if mode == "intermediates":
            # delete generated files except outputs
            for p in list(self._generated_files):
                ap = os.path.abspath(p)
                if ap in self._output_files:
                    continue
                try:
                    if os.path.isfile(ap):
                        os.remove(ap)
                except Exception:
                    # Never fail task because cleanup failed
                    pass
            return

        # unknown mode -> do nothing (fail-safe)
        return

    def to_public_dict(self) -> Dict[str, Any]:
        """
        Public-friendly task summary.
        Avoid returning internal file paths here if you plan to expose it externally later.
        """
        return {
            "task_id": self.task_id,
            "voice_id": self.voice_id,
            "stability": self.stability,
            "similarity": self.similarity,
            "output_format": self.output_format,
            "preset_id": self.preset_id,
            "webhook_url": self.webhook_url,
            "options": self.options,
        }