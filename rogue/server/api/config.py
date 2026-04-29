"""Read/write the shared user-level config TOML.

The TUI persists user-level configuration to
``<UserConfigDir>/rogue/config.toml`` (see
``packages/tui/internal/screens/config/persistence.go``). This endpoint
exposes the same file so the web client can keep itself in sync — both
clients edit the same TOML and read the same values.

- ``GET /api/v1/config`` returns the parsed TOML as JSON (empty object
  when the file does not yet exist).
- ``PUT /api/v1/config`` accepts a JSON object, merges it into the
  existing TOML (existing keys not present in the request are preserved),
  writes atomically, and returns the merged result.

Web-only fields (provider/model selections that pre-date the TUI's
config struct) are stored alongside the TUI-known fields; the TUI's TOML
unmarshal silently ignores unknown fields.
"""

from __future__ import annotations

import contextlib
import os
import sys
from pathlib import Path
from typing import Any

import tomli_w
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

if sys.version_info >= (3, 11):
    import tomllib  # noqa: F401
else:  # pragma: no cover
    import tomli as tomllib  # type: ignore[no-redef]

from ...common.logging import get_logger

router = APIRouter(prefix="/config", tags=["config"])
logger = get_logger(__name__)


def _config_dir() -> Path:
    """Mirror Go's ``os.UserConfigDir()`` for the rogue/config.toml lookup."""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    elif sys.platform == "win32":  # pragma: no cover
        appdata = os.environ.get("APPDATA")
        base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    else:
        xdg = os.environ.get("XDG_CONFIG_HOME")
        base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "rogue"


def _config_path() -> Path:
    return _config_dir() / "config.toml"


def _read_config() -> dict[str, Any]:
    path = _config_path()
    if not path.is_file():
        return {}
    try:
        with path.open("rb") as fp:
            return tomllib.load(fp)
    except Exception as exc:
        logger.warning(f"config: failed to read {path}: {exc}")
        return {}


def _write_config(data: dict[str, Any]) -> None:
    import tempfile

    path = _config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Unique tmp filename per write so concurrent PUTs can't truncate each
    # other's in-flight tempfile. ``os.replace`` is per-file atomic, so the
    # final file is always one or the other writer's content (last wins),
    # never a torn mix.
    tmp_fd, tmp_path_str = tempfile.mkstemp(
        prefix=".toml.",
        suffix=".tmp",
        dir=str(path.parent),
    )
    tmp = Path(tmp_path_str)
    try:
        with os.fdopen(tmp_fd, "wb") as fp:
            tomli_w.dump(data, fp)
        os.replace(tmp, path)
    except Exception as exc:
        logger.error(f"config: failed to write {path}: {exc}")
        with contextlib.suppress(Exception):
            tmp.unlink(missing_ok=True)
        raise


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge ``overlay`` into ``base``; ``overlay`` wins on conflicts."""
    out = dict(base)
    for key, value in overlay.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


class ConfigResponse(BaseModel):
    config: dict[str, Any]
    path: str


@router.get("", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    return ConfigResponse(config=_read_config(), path=str(_config_path()))


@router.put("", response_model=ConfigResponse)
async def put_config(payload: dict[str, Any]) -> ConfigResponse:
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400,
            detail="Request body must be a JSON object.",
        )
    current = _read_config()
    merged = _deep_merge(current, payload)
    try:
        _write_config(merged)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write config: {exc}",
        )
    return ConfigResponse(config=merged, path=str(_config_path()))
