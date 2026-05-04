"""Hatch build hook that ensures the web SPA is built before the wheel ships.

The hook runs ``pnpm install --frozen-lockfile && pnpm build`` inside
``packages/web`` only when the dist is missing or stale. If pnpm is not
installed, the hook degrades gracefully: it warns and continues, so the wheel
build still succeeds for contributors who don't need the web UI. CI is
expected to run ``pnpm --filter web build`` explicitly before ``uv build`` so
the published wheel always carries ``dist/``.
"""

from __future__ import annotations

import os
import shutil
import subprocess  # noqa: S404
import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class WebBuildHook(BuildHookInterface):
    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        repo_root = Path(self.root)
        web_dir = repo_root / "packages" / "web"
        dist_dir = web_dir / "dist"
        dist_index = dist_dir / "index.html"
        src_dir = web_dir / "src"

        skip_build = bool(os.environ.get("ROGUE_SKIP_WEB_BUILD"))
        if skip_build:
            self.app.display_info("ROGUE_SKIP_WEB_BUILD set; skipping web build.")

        if not skip_build and web_dir.is_dir():
            needs_build = not dist_index.is_file() or _is_stale(dist_index, src_dir)
            if needs_build:
                pnpm = shutil.which("pnpm")
                if pnpm is None:
                    if dist_index.is_file():
                        self.app.display_warning(
                            "pnpm not found; reusing existing packages/web/dist "
                            "(may be stale).",
                        )
                    else:
                        self.app.display_warning(
                            "pnpm not found and packages/web/dist is missing. "
                            "The wheel will not include the web UI. "
                            "Install Node + pnpm and rebuild, or run "
                            "`cd packages/web && pnpm install && pnpm build` manually.",
                        )
                else:
                    self.app.display_info("Building web SPA via pnpm...")
                    try:
                        subprocess.run(  # noqa: S603
                            [pnpm, "install", "--frozen-lockfile"],
                            cwd=str(web_dir),
                            check=True,
                        )
                        subprocess.run(  # noqa: S603
                            [pnpm, "run", "build"],
                            cwd=str(web_dir),
                            check=True,
                        )
                    except subprocess.CalledProcessError as e:
                        self.app.display_error(f"pnpm build failed: {e}")
                        sys.exit(1)

        # Force-include the web dist only when it actually exists, so installs
        # in environments without pnpm (and without a prebuilt dist) don't fail
        # on a missing forced-include path. This replaces the static
        # `[tool.hatch.build.targets.*.force-include]` tables in pyproject.toml.
        if dist_dir.is_dir():
            target = self.target_name
            if target == "wheel":
                build_data.setdefault("force_include", {})[str(dist_dir)] = (
                    "rogue/web_dist"
                )
            elif target == "sdist":
                build_data.setdefault("force_include", {})[str(dist_dir)] = (
                    "packages/web/dist"
                )


def _is_stale(dist_index: Path, src_dir: Path) -> bool:
    if not src_dir.is_dir():
        return False
    dist_mtime = dist_index.stat().st_mtime
    for path in src_dir.rglob("*"):
        if path.is_file() and path.stat().st_mtime > dist_mtime:
            return True
    return False
