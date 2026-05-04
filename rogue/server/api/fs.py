"""Native OS file picker proxy for the local web UI.

Browsers can't expose absolute filesystem paths from ``<input type="file">``,
but ``rogue-ai web`` runs on the user's own machine — so the server process
opens the native file dialog (Finder / GNOME Files / Windows Explorer) and
hands the absolute path back to the SPA.

All helpers are spawned argv-style (no shell). The two helpers that build
script literals — AppleScript on macOS, PowerShell on Windows — escape ``\\``
and ``"`` in ``prompt`` so a stray quote doesn't break the literal.
"""

from __future__ import annotations

import asyncio
import platform
from typing import List, Optional, Sequence

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ...common.logging import get_logger

router = APIRouter(prefix="/fs", tags=["fs"])
logger = get_logger(__name__)

# Bounded so a forgotten dialog doesn't hold resources forever.
_PICK_TIMEOUT_SECONDS = 600


class PickFileRequest(BaseModel):
    extensions: Optional[List[str]] = None
    prompt: str = "Select a file"


class PickedFile(BaseModel):
    """``path`` is None when the user dismissed the dialog."""

    path: Optional[str] = None


def _escape_for_script_literal(raw: str) -> str:
    """Escape ``\\`` and ``"`` so the prompt is a valid AppleScript / PowerShell
    double-quoted literal. Both languages use the same escape rules."""
    return raw.replace("\\", "\\\\").replace('"', '\\"')


def _normalise_extensions(raw: Optional[Sequence[str]]) -> List[str]:
    """Strip leading dots / whitespace; drop empties. No format restriction."""
    if not raw:
        return []
    out: List[str] = []
    for e in raw:
        if not isinstance(e, str):
            continue
        cleaned = e.strip().lstrip(".")
        if cleaned:
            out.append(cleaned)
    return out


async def _spawn(
    argv: Sequence[str],
    timeout: int = _PICK_TIMEOUT_SECONDS,
) -> tuple[int, str, str]:
    """Run ``argv`` argv-style (no shell). Returns ``(rc, stdout, stderr)``."""
    proc = await asyncio.create_subprocess_exec(
        *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        out_b, err_b = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError as e:
        proc.kill()
        await proc.wait()
        raise asyncio.TimeoutError("picker dialog timed out") from e
    return (
        proc.returncode or 0,
        out_b.decode("utf-8", errors="replace"),
        err_b.decode("utf-8", errors="replace"),
    )


async def _pick_macos(prompt: str, extensions: List[str]) -> Optional[str]:
    """AppleScript ``choose file``. Cancellation → returncode 1."""
    safe_prompt = _escape_for_script_literal(prompt)
    type_clause = (
        " of type {"
        + ", ".join(f'"{_escape_for_script_literal(e)}"' for e in extensions)
        + "}"
        if extensions
        else ""
    )
    script = f'POSIX path of (choose file with prompt "{safe_prompt}"{type_clause})'
    rc, out, err = await _spawn(["osascript", "-e", script])
    if rc != 0:
        # AppleScript exits with code 1 (`-128`) on user cancel, locale
        # independent. Use the numeric exit code rather than scraping stderr.
        if rc == 1:
            return None
        raise HTTPException(
            status_code=500,
            detail=f"osascript failed: {err.strip() or out.strip()}",
        )
    return out.strip() or None


async def _pick_linux(prompt: str, extensions: List[str]) -> Optional[str]:
    """Try zenity first, then kdialog. Either may not be installed."""
    helper = "zenity"
    args: List[str] = ["zenity", "--file-selection", "--title", prompt]
    if extensions:
        # Zenity expects a *named* filter ("Name | pat1 pat2") otherwise the
        # dropdown shows a blank label.
        pattern = " ".join(f"*.{e}" for e in extensions)
        label = "/".join(f".{e}" for e in extensions)
        args.extend(["--file-filter", f"{label} | {pattern}"])
    try:
        rc, out, err = await _spawn(args)
    except FileNotFoundError:
        helper = "kdialog"
        args = ["kdialog", "--title", prompt, "--getopenfilename", "."]
        if extensions:
            args.append(" ".join(f"*.{e}" for e in extensions))
        try:
            rc, out, err = await _spawn(args)
        except FileNotFoundError as exc:
            raise HTTPException(
                status_code=503,
                detail="No native picker available (install zenity or kdialog).",
            ) from exc
    if rc != 0:
        # Both zenity and kdialog use exit code 1 for "user cancelled"
        # (signal-killed children would be 128+N). Treating the numeric
        # exit code is more reliable than scraping stderr — empty stderr
        # could be a SIGSEGV under Wayland that the user shouldn't see as
        # "you cancelled".
        if rc == 1:
            return None
        raise HTTPException(
            status_code=500,
            detail=f"{helper} failed (rc={rc}): {err.strip() or '(no stderr)'}",
        )
    return out.strip() or None


async def _pick_windows(prompt: str, extensions: List[str]) -> Optional[str]:
    """PowerShell + WinForms OpenFileDialog."""
    safe_prompt = _escape_for_script_literal(prompt)
    if extensions:
        pat = ";".join(f"*.{e}" for e in extensions)
        kind = "/".join(f".{e}" for e in extensions)
        ps_filter = _escape_for_script_literal(
            f"Allowed ({kind})|{pat}|All files (*.*)|*.*",
        )
    else:
        ps_filter = "All files (*.*)|*.*"
    script = (
        "Add-Type -AssemblyName System.Windows.Forms; "
        "$d = New-Object System.Windows.Forms.OpenFileDialog; "
        f'$d.Title = "{safe_prompt}"; '
        f'$d.Filter = "{ps_filter}"; '
        "if ($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) "
        "{ Write-Output $d.FileName }"
    )
    rc, out, err = await _spawn(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
    )
    if rc != 0:
        raise HTTPException(
            status_code=500,
            detail=f"powershell failed: {err.strip()}",
        )
    return out.strip() or None


@router.post("/pick-file", response_model=PickedFile)
async def pick_file(request: PickFileRequest) -> PickedFile:
    """Open the OS-native file dialog on the server's display and return the
    absolute path the user selected.

    Returns ``{path: null}`` when the user cancels. Errors when the OS picker
    helper isn't available (e.g. headless Linux without zenity) — clients
    should fall back to manual path entry.
    """
    system = platform.system()
    extensions = _normalise_extensions(request.extensions)
    prompt = request.prompt or "Select a file"

    try:
        if system == "Darwin":
            path = await _pick_macos(prompt, extensions)
        elif system == "Linux":
            path = await _pick_linux(prompt, extensions)
        elif system == "Windows":
            path = await _pick_windows(prompt, extensions)
        else:
            raise HTTPException(
                status_code=501,
                detail=f"Native file picker not implemented for {system}",
            )
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Native picker helper missing: {exc.filename or exc}",
        ) from exc
    except asyncio.TimeoutError:
        return PickedFile(path=None)

    return PickedFile(path=path)
