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
from typing import Generic, Optional, Type, TypeVar

from loguru import logger
from pydantic import BaseModel

from rogue_sdk.types import EvaluationStatus

T = TypeVar("T", bound=BaseModel)


def resolve_workdir() -> Path:
    raw = os.environ.get("ROGUE_WORKDIR")
    if raw:
        return Path(raw).expanduser().resolve()
    return (Path.home() / ".rogue").resolve()


def _pid_alive(pid: int, expected_create_time: Optional[float] = None) -> bool:
    """Best-effort liveness probe for the cross-process advisory marker.

    PID-reuse is the well-known failure mode of plain ``os.kill(pid, 0)``:
    a recycled PID assigned to an unrelated process reads as "alive". When
    the marker carries a process start-time hint, we cross-check it via
    psutil so a recycled PID with a later start-time is detected as a
    fresh process (i.e. the original holder is gone).
    """
    try:
        os.kill(pid, 0)
    except (PermissionError, ProcessLookupError, OSError):
        return False
    if expected_create_time is None:
        return True
    try:
        import psutil

        actual = psutil.Process(pid).create_time()
    except Exception:
        # If we can't introspect the process, fall back to "yes alive".
        return True
    # Allow a small tolerance — psutil rounds to ms on some platforms.
    return abs(actual - expected_create_time) < 1.0


def _retention_cap() -> int | None:
    """Per-bucket retention cap from ``ROGUE_JOB_RETENTION``.

    Set to a positive integer to keep at most N most-recent jobs on disk;
    older files are pruned during ``save()``. Default ``None`` keeps the
    historical behaviour (unbounded) so users with existing workdirs see
    no surprise data loss after upgrade.
    """
    raw = os.environ.get("ROGUE_JOB_RETENTION", "").strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        return None
    return n if n > 0 else None


class JobStore(Generic[T]):
    def __init__(self, bucket: str, model: Type[T]):
        self._dir = resolve_workdir() / "jobs" / bucket
        self._dir.mkdir(parents=True, exist_ok=True)
        self._model = model
        self._bucket = bucket
        self._retention = _retention_cap()
        # Single-process advisory marker. If the marker file already exists
        # AND points at a live PID, log a warning so an operator running
        # two ``rogue-ai web`` instances against the same workdir at least
        # sees something in the log.
        self._marker_path = self._dir / ".live"
        self._mark_active()

    def _mark_active(self) -> None:
        # Refuse to follow a symlink for the marker — without this, a
        # hostile pre-created ``.live -> ~/.ssh/authorized_keys`` would
        # cause us to write our PID over an attacker-chosen file.
        existing = ""
        try:
            if self._marker_path.exists() and not self._marker_path.is_symlink():
                existing = self._marker_path.read_text().strip()
        except Exception:
            existing = ""
        if existing:
            existing_pid = -1
            existing_create: Optional[float] = None
            parts = existing.split(":", 1)
            try:
                existing_pid = int(parts[0])
                if len(parts) == 2:
                    existing_create = float(parts[1])
            except ValueError:
                existing_pid = -1
            if (
                existing_pid > 0
                and existing_pid != os.getpid()
                and _pid_alive(existing_pid, existing_create)
            ):
                logger.warning(
                    f"job_store[{self._bucket}]: another process (pid {existing_pid}) "
                    "is already using this workdir — concurrent writers are not "
                    "supported and may clobber each other.",
                )
        # Write our PID + start-time so the next process can detect a
        # PID-reuse rather than mistaking a recycled PID for "still alive".
        own_pid = os.getpid()
        own_create: Optional[float] = None
        try:
            import psutil

            own_create = psutil.Process(own_pid).create_time()
        except Exception:
            own_create = None
        marker_value = (
            f"{own_pid}:{own_create}" if own_create is not None else str(own_pid)
        )
        # Defence-in-depth against symlink redirection: refuse to write if
        # the marker is currently a symlink.
        with contextlib.suppress(Exception):
            if self._marker_path.is_symlink():
                self._marker_path.unlink(missing_ok=True)
            self._marker_path.write_text(marker_value)

    @property
    def directory(self) -> Path:
        return self._dir

    def load_all(self) -> dict[str, T]:
        out: dict[str, T] = {}
        quarantine_dir = self._dir / ".quarantine"
        # Refuse to operate when ``.quarantine`` is a symlink — could be
        # an attacker-pre-created redirect to another path.
        if quarantine_dir.is_symlink():
            logger.error(
                f"job_store[{self._bucket}]: refusing to use {quarantine_dir} "
                "(symlink). Remove or replace with a real directory.",
            )
            quarantine_dir = None  # type: ignore[assignment]
        for path in sorted(self._dir.glob("*.json")):
            # Skip symlinks — same trust concern as above.
            if path.is_symlink():
                logger.warning(
                    f"job_store[{self._bucket}]: skipping symlinked job file "
                    f"{path.name}",
                )
                continue
            try:
                data = json.loads(path.read_text())
                job = self._model.model_validate(data)
            except Exception as exc:
                # Move corrupt / schema-incompatible files into a sibling
                # quarantine directory so the next boot doesn't keep
                # tripping on them — and so the user has a recovery hint.
                logger.warning(
                    f"job_store[{self._bucket}]: quarantining unreadable file "
                    f"{path.name}: {exc}",
                )
                if quarantine_dir is not None:
                    with contextlib.suppress(Exception):
                        quarantine_dir.mkdir(parents=True, exist_ok=True)
                        path.rename(quarantine_dir / path.name)
                continue
            self._fail_if_in_flight(job)
            job_id = getattr(job, "job_id", None)
            if not job_id:
                continue
            out[job_id] = job
        if out:
            logger.info(
                f"job_store[{self._bucket}]: loaded {len(out)} jobs from {self._dir}",
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
        # Use setattr so ty doesn't try to resolve attributes it can't see on
        # the bare BaseModel parameter (the concrete subclasses do define them).
        try:
            setattr(job, "status", EvaluationStatus.FAILED)
        except Exception:
            return
        # Best-effort field updates — different job models may not share
        # every attribute, so silently skip when assignment fails.
        if hasattr(job, "error_message"):
            with contextlib.suppress(Exception):
                setattr(
                    job,
                    "error_message",
                    "Server restarted while the job was in progress.",
                )
        if hasattr(job, "completed_at"):
            with contextlib.suppress(Exception):
                setattr(job, "completed_at", datetime.now(timezone.utc))

    def save(self, job: T) -> None:
        import tempfile

        job_id = getattr(job, "job_id", None)
        if not job_id:
            return
        path = self._dir / f"{job_id}.json"
        # Per-write unique tmp filename — without this, two concurrent
        # save() calls for the same job (eval-status update + chat-update
        # arriving in the same tick) can truncate each other's in-flight
        # tempfile mid-write.
        tmp_fd, tmp_path_str = tempfile.mkstemp(
            prefix=f".{job_id}.",
            suffix=".json.tmp",
            dir=str(self._dir),
        )
        tmp = Path(tmp_path_str)
        try:
            with os.fdopen(tmp_fd, "w") as fp:
                fp.write(job.model_dump_json(indent=2))
            os.replace(tmp, path)
        except Exception as exc:
            logger.warning(
                f"job_store[{self._bucket}]: failed to persist {job_id}: {exc}",
            )
            with contextlib.suppress(Exception):
                tmp.unlink(missing_ok=True)
        else:
            self._maybe_prune()

    def _maybe_prune(self) -> None:
        """Drop the oldest jobs once the bucket exceeds ``ROGUE_JOB_RETENTION``."""
        cap = self._retention
        if cap is None:
            return
        try:
            files = sorted(
                self._dir.glob("*.json"),
                key=lambda p: p.stat().st_mtime,
            )
        except Exception:
            return
        excess = len(files) - cap
        if excess <= 0:
            return
        for victim in files[:excess]:
            with contextlib.suppress(Exception):
                victim.unlink()
        logger.info(
            f"job_store[{self._bucket}]: pruned {excess} old job(s) (cap={cap})",
        )

    def delete(self, job_id: str) -> None:
        with contextlib.suppress(Exception):
            (self._dir / f"{job_id}.json").unlink(missing_ok=True)
