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
        if os.environ.get("ROGUE_SKIP_WEB_BUILD"):
            self.app.display_info("ROGUE_SKIP_WEB_BUILD set; skipping web build.")
            return

        repo_root = Path(self.root)
        web_dir = repo_root / "packages" / "web"
        dist_index = web_dir / "dist" / "index.html"
        src_dir = web_dir / "src"

        if not web_dir.is_dir():
            return  # Source-distribution install without the web tree.

        if dist_index.is_file() and not _is_stale(dist_index, src_dir):
            return

        pnpm = shutil.which("pnpm")
        if pnpm is None:
            if dist_index.is_file():
                self.app.display_warning(
                    "pnpm not found; reusing existing packages/web/dist "
                    "(may be stale).",
                )
                return
            self.app.display_warning(
                "pnpm not found and packages/web/dist is missing. "
                "The wheel will not include the web UI. "
                "Install Node + pnpm and rebuild, or run "
                "`cd packages/web && pnpm install && pnpm build` manually.",
            )
            return

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


def _is_stale(dist_index: Path, src_dir: Path) -> bool:
    if not src_dir.is_dir():
        return False
    dist_mtime = dist_index.stat().st_mtime
    for path in src_dir.rglob("*"):
        if path.is_file() and path.stat().st_mtime > dist_mtime:
            return True
    return False
