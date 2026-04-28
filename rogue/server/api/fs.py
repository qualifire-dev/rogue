"""Native OS file picker proxy for the local web UI.

Browsers refuse to expose absolute filesystem paths from ``<input type="file">``
or the File System Access API — that's a hard security boundary. But ``rogue-ai
web`` runs on the user's own machine, so the server process *can* open a native
file dialog (Finder / GNOME Files / Windows Explorer) on the user's display and
hand the absolute path back to the SPA. The picker UX feels native because it
*is* native; only the trigger is a small HTTP call.

Caveats:
- The dialog appears on the server process's display. That's the user's own
  display when the server is launched locally (the only supported deployment),
  but if you ever expose this server remotely the dialog would pop on the
  server side — useless and surprising. Default bind is 127.0.0.1.
- Each platform shells out to its native helper. If the helper isn't on PATH
  (e.g. headless Linux without zenity) we return 503 so the SPA can fall back
  to manual path entry.
- The HTTP request blocks until the user picks or cancels — sometimes minutes.
  We declare the route as a sync `def` so FastAPI dispatches it on a worker
  thread instead of blocking the event loop.
"""

from __future__ import annotations

import platform
import subprocess  # noqa: S404
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...common.logging import get_logger

router = APIRouter(prefix="/fs", tags=["fs"])
logger = get_logger(__name__)

# A user pondering their choice in a Finder dialog can take a while. Bigger
# than the typical HTTP idle timeout but bounded so the worker thread frees up
# eventually if the dialog is forgotten.
_PICK_TIMEOUT_SECONDS = 600


class PickFileRequest(BaseModel):
    extensions: Optional[List[str]] = None
    prompt: str = "Select a file"


class PickedFile(BaseModel):
    """``path`` is None when the user dismissed the dialog."""

    path: Optional[str] = None


def _normalise_extensions(extensions: Optional[List[str]]) -> List[str]:
    if not extensions:
        return []
    return [e.lstrip(".").strip() for e in extensions if e and e.strip()]


def _pick_macos(prompt: str, extensions: List[str]) -> Optional[str]:
    """AppleScript ``choose file``. Cancellation → returncode 1 (-128)."""
    if extensions:
        type_clause = " of type {" + ", ".join(f'"{e}"' for e in extensions) + "}"
    else:
        type_clause = ""
    # Hardcoded shape — only `prompt` and `type_clause` interpolate, both are
    # tightly controlled (prompt is wrapped in quotes, ext list is alnum-only
    # in practice). osascript receives `-e <script>` argv-style, no shell.
    safe_prompt = prompt.replace('"', '\\"')
    script = f'POSIX path of (choose file with prompt "{safe_prompt}"{type_clause})'
    proc = subprocess.run(  # noqa: S603
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=_PICK_TIMEOUT_SECONDS,
    )
    if proc.returncode != 0:
        # Cancellation prints `User canceled. (-128)` to stderr — treat as None.
        if "-128" in proc.stderr or "canceled" in proc.stderr.lower():
            return None
        raise HTTPException(
            status_code=500,
            detail=f"osascript failed: {proc.stderr.strip() or proc.stdout.strip()}",
        )
    path = proc.stdout.strip()
    return path or None


def _pick_linux(prompt: str, extensions: List[str]) -> Optional[str]:
    """Try zenity first, then kdialog. Either may not be installed."""
    args: List[str]
    helper = "zenity"
    args = ["zenity", "--file-selection", "--title", prompt]
    if extensions:
        pattern = " ".join(f"*.{e}" for e in extensions)
        args.extend(["--file-filter", pattern])
    try:
        proc = subprocess.run(  # noqa: S603
            args,
            capture_output=True,
            text=True,
            timeout=_PICK_TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        helper = "kdialog"
        args = ["kdialog", "--getopenfilename", "."]
        if extensions:
            args.append(" ".join(f"*.{e}" for e in extensions))
        try:
            proc = subprocess.run(  # noqa: S603
                args,
                capture_output=True,
                text=True,
                timeout=_PICK_TIMEOUT_SECONDS,
            )
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=503,
                detail="No native picker available (install zenity or kdialog).",
            ) from exc
    if proc.returncode != 0:
        # Both helpers exit non-zero on cancel.
        if not proc.stderr.strip():
            return None
        raise HTTPException(
            status_code=500,
            detail=f"{helper} failed: {proc.stderr.strip()}",
        )
    path = proc.stdout.strip()
    return path or None


def _pick_windows(prompt: str, extensions: List[str]) -> Optional[str]:
    """PowerShell + WinForms OpenFileDialog."""
    if extensions:
        # "Python files (*.py)|*.py|All files (*.*)|*.*"
        pat = ";".join(f"*.{e}" for e in extensions)
        kind = "/".join(f".{e}" for e in extensions)
        ps_filter = f"Allowed ({kind})|{pat}|All files (*.*)|*.*"
    else:
        ps_filter = "All files (*.*)|*.*"
    safe_prompt = prompt.replace('"', '`"')
    safe_filter = ps_filter.replace('"', '`"')
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$d = New-Object System.Windows.Forms.OpenFileDialog; "
        f'$d.Title = "{safe_prompt}"; '
        f'$d.Filter = "{safe_filter}"; '
        "if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) "
        "{ Write-Output $d.FileName }"
    )
    proc = subprocess.run(  # noqa: S603
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True,
        text=True,
        timeout=_PICK_TIMEOUT_SECONDS,
    )
    if proc.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"powershell failed: {proc.stderr.strip()}",
        )
    path = proc.stdout.strip()
    return path or None


@router.post("/pick-file", response_model=PickedFile)
def pick_file(request: PickFileRequest) -> PickedFile:
    """Open the OS-native file dialog on the server's display and return the
    absolute path the user selected.

    Returns ``{path: null}`` when the user cancels. Errors when the OS picker
    helper isn't available (e.g. headless Linux without zenity) — clients
    should fall back to manual path entry.
    """
    system = platform.system()
    extensions = _normalise_extensions(request.extensions)
    prompt = (request.prompt or "Select a file").strip() or "Select a file"

    try:
        if system == "Darwin":
            path = _pick_macos(prompt, extensions)
        elif system == "Linux":
            path = _pick_linux(prompt, extensions)
        elif system == "Windows":
            path = _pick_windows(prompt, extensions)
        else:
            raise HTTPException(
                status_code=501,
                detail=f"Native file picker not implemented for {system}",
            )
    except FileNotFoundError as exc:
        # macOS / Windows helpers are guaranteed-present on their OS, but be
        # defensive: report the missing binary clearly.
        raise HTTPException(
            status_code=503,
            detail=f"Native picker helper missing: {exc.filename or exc}",
        ) from exc
    except subprocess.TimeoutExpired:
        return PickedFile(path=None)

    return PickedFile(path=path)
