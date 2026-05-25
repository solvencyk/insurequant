"""Filesystem ACL normalisation for downloaded PDFs.

Background: when the downloader runs in an elevated / domain-account
context (e.g. ``MS+sangwook.cho``) and writes into a folder owned by
``BUILTIN\\Administrators``, the resulting PDFs end up unreadable by the
local desktop session (``sangwook.cho``). Edge/Chrome surface this as
"파일에 대한 액세스가 거부되었습니다".

Fix: after a download we

1. ``takeown`` the file so the current local user owns it
2. ``icacls /reset`` to drop the explicit Administrators-only ACE and
   re-inherit the parent directory's ACL
3. ``icacls /grant *S-1-1-0:(R)`` as a final safety net so the file is
   at least world-readable for the local session

All three steps are best-effort. Failures are logged but never abort
the download - manifest writing and verification still happen so the
caller can decide what to do.

On non-Windows hosts every function is a no-op.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)


_IS_WINDOWS = sys.platform == "win32"


def _icacls() -> str | None:
    return shutil.which("icacls")


def _takeown() -> str | None:
    return shutil.which("takeown")


def _run(cmd: list[str], *, label: str) -> None:
    """Run a Windows-only ACL helper, swallowing any error.

    The helpers themselves are noisy on stdout/stderr - we capture both
    and only emit a log line when the return code is non-zero so a
    healthy normalisation pass produces no noise.
    """
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        logger.warning("%s failed: %s", label, exc)
        return
    if result.returncode != 0:
        logger.warning(
            "%s returned %d: %s",
            label,
            result.returncode,
            (result.stderr or result.stdout).strip()[:240],
        )


def normalize_file_acl(path: Path) -> None:
    """Make ``path`` readable by the current local user.

    Sequence: ``takeown`` -> ``icacls /reset`` -> ``icacls /grant Everyone:(R)``.
    No-ops on non-Windows hosts so callers can use the same code path
    regardless of platform.
    """
    if not _IS_WINDOWS:
        return
    if not path.exists():
        return

    str_path = str(path)
    icacls_bin = _icacls()
    takeown_bin = _takeown()

    if takeown_bin:
        _run(
            [takeown_bin, "/F", str_path],
            label=f"takeown {path.name}",
        )
    if icacls_bin:
        _run(
            [icacls_bin, str_path, "/reset", "/C", "/Q"],
            label=f"icacls reset {path.name}",
        )
        _run(
            [icacls_bin, str_path, "/grant", "*S-1-1-0:(R)", "/C", "/Q"],
            label=f"icacls grant Everyone {path.name}",
        )

    try:
        os.chmod(path, 0o644)
    except OSError as exc:
        logger.debug("chmod failed for %s: %s", path.name, exc)


def normalize_tree(root: Path, *, glob: str = "**/*") -> int:
    """Normalise the ACL of every file under ``root`` recursively.

    Returns the number of files we touched. Used by ``--stage pdf`` to
    fix legacy LIFE downloads (owner = Administrators) without a full
    re-download.
    """
    if not _IS_WINDOWS:
        return 0
    if not root.exists():
        return 0

    touched = 0
    for path in _iter_files(root, glob):
        normalize_file_acl(path)
        touched += 1
    return touched


def _iter_files(root: Path, glob: str) -> Iterable[Path]:
    for entry in root.glob(glob):
        if entry.is_file():
            yield entry
