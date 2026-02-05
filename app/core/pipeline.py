from __future__ import annotations

from typing import List, Protocol
import time
import traceback

from app.core.artifacts import Artifact, TaskContext


class Step(Protocol):
    """
    All pipeline steps must implement this interface.
    """

    name: str

    def run(self, artifact: Artifact, ctx: TaskContext) -> Artifact:
        ...


class Pipeline:
    """
    Linear execution pipeline.

    Responsibilities:
    - Execute steps sequentially
    - Pass Artifact between steps
    - Record timing/debug info
    - Let caller decide cleanup strategy
    """

    def __init__(self, steps: List[Step]):
        self.steps = steps

    def run(self, initial_artifact: Artifact, ctx: TaskContext) -> Artifact:
        current = initial_artifact

        for step in self.steps:
            step_name = getattr(step, "name", step.__class__.__name__)
            start_ts = time.perf_counter()

            try:
                result = step.run(current, ctx)
                if not isinstance(result, Artifact):
                    raise TypeError(f"Step '{step_name}' returned {type(result).__name__}, expected Artifact")
                current = result
            except Exception as e:
                # record failure context
                ctx.debug.setdefault("errors", []).append({
                    "step": step_name,
                    "error": str(e),
                    "type": e.__class__.__name__,
                    "traceback": traceback.format_exc(),
                })
                raise

            elapsed = time.perf_counter() - start_ts
            ctx.debug.setdefault("timing", {})[step_name] = elapsed

        return current