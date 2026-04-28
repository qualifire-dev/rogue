"""JSON-per-job persistence layer for evaluation and red-team services.

One file per job at ``<workdir>/jobs/<bucket>/<job_id>.json``:

- Atomic writes via ``os.replace`` (write to ``.tmp`` then rename)
- On startup, jobs left in ``pending`` / ``running`` are flipped to
  ``failed`` with a clear reason — the previous server process died mid-run
  and there's no way to resume an evaluation across processes.
- Workdir resolves from the ``ROGUE_WORKDIR`` env var (set by
  ``rogue/__main__.py``); falls back to ``~/.rogue`` when the server is
  invoked standalone.
"""

from __future__ import annotations

import contextlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Generic, Type, TypeVar

from loguru import logger
from pydantic import BaseModel
from rogue_sdk.types import EvaluationStatus

T = TypeVar("T", bound=BaseModel)


def resolve_workdir() -> Path:
    raw = os.environ.get("ROGUE_WORKDIR")
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / ".rogue").resolve()


class JobStore(Generic[T]):
    def __init__(self, bucket: str, model: Type[T]):
        self._dir = resolve_workdir() / "jobs" / bucket
        self._dir.mkdir(parents=True, exist_ok=True)
        self._model = model
        self._bucket = bucket

    @property
    def directory(self) -> Path:
        return self._dir

    def load_all(self) -> dict[str, T]:
        out: dict[str, T] = {}
        for path in sorted(self._dir.glob("*.json")):
            try:
                data = json.loads(path.read_text())
                job = self._model.model_validate(data)
            except Exception as exc:
                logger.warning(
                    f"job_store[{self._bucket}]: skipping unreadable file "
                    f"{path.name}: {exc}",
                )
                continue
            self._fail_if_in_flight(job)
            job_id = getattr(job, "job_id", None)
            if not job_id:
                continue
            out[job_id] = job
        if out:
            logger.info(
                f"job_store[{self._bucket}]: loaded {len(out)} jobs "
                f"from {self._dir}",
            )
        return out

    @staticmethod
    def _fail_if_in_flight(job: BaseModel) -> None:
        status = getattr(job, "status", None)
        if status is None:
            return
        value = status.value if hasattr(status, "value") else status
        if value not in ("pending", "running"):
            return
        # Mutate the job in place — Pydantic models are mutable by default.
        try:
            job.status = EvaluationStatus.FAILED  # type: ignore[attr-defined]
        except Exception:
            return
        # Best-effort field updates — different job models may not share
        # every attribute, so silently skip when assignment fails.
        if hasattr(job, "error_message"):
            with contextlib.suppress(Exception):
                job.error_message = (  # type: ignore[attr-defined]
                    "Server restarted while the job was in progress."
                )
        if hasattr(job, "completed_at"):
            with contextlib.suppress(Exception):
                job.completed_at = datetime.now(  # type: ignore[attr-defined]
                    timezone.utc,
                )

    def save(self, job: T) -> None:
        job_id = getattr(job, "job_id", None)
        if not job_id:
            return
        path = self._dir / f"{job_id}.json"
        tmp = path.with_suffix(".json.tmp")
        try:
            tmp.write_text(job.model_dump_json(indent=2))
            os.replace(tmp, path)
        except Exception as exc:
            logger.warning(
                f"job_store[{self._bucket}]: failed to persist {job_id}: {exc}",
            )
            with contextlib.suppress(Exception):
                tmp.unlink(missing_ok=True)

    def delete(self, job_id: str) -> None:
        with contextlib.suppress(Exception):
            (self._dir / f"{job_id}.json").unlink(missing_ok=True)
