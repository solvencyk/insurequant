"""Multi-level PDF verification.

Levels (best to worst):

- ``verified_full``  : magic + read + size + ``지급여력비율`` keyword
                       + pypdf first-page parse all succeed
- ``verified_basic`` : magic + read + size all succeed (image-only PDFs
                       legitimately end here, e.g. KB손해보험)
- ``failed``         : at least one of the basic checks failed

The harness considers ``verified_basic`` and ``verified_full`` both as
"green" but routes ``verified_basic`` files into a separate "needs
manual review for keyword presence" list so the operator knows which
files would fail downstream text extraction.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)


PDF_MAGIC = b"%PDF-"
KEYWORD = "지급여력비율"


class VerificationLevel(str, enum.Enum):
    FAILED = "failed"
    VERIFIED_BASIC = "verified_basic"
    VERIFIED_FULL = "verified_full"


@dataclasses.dataclass
class VerificationResult:
    path: Path
    level: VerificationLevel
    size_bytes: int
    has_magic: bool
    user_can_read: bool
    has_keyword: bool | None
    pypdf_ok: bool | None
    reasons: list[str]

    @property
    def ok(self) -> bool:
        return self.level is not VerificationLevel.FAILED


def _check_magic(path: Path) -> bool:
    try:
        with path.open("rb") as fp:
            return fp.read(5) == PDF_MAGIC
    except OSError:
        return False


def _check_user_read(path: Path) -> bool:
    """Try opening the file the way a desktop double-click would.

    ``Path.open("rb")`` honours the file's ACL on Windows - if the
    current user lacks Read it raises ``PermissionError``, which is
    exactly the failure mode the user reported.
    """
    try:
        with path.open("rb") as fp:
            fp.read(1024)
        return True
    except PermissionError:
        return False
    except OSError:
        return False


def _check_keyword(path: Path) -> bool | None:
    """Best-effort: extract page 1 text and look for ``지급여력비율``.

    Returns ``None`` when pypdf is unavailable so callers can distinguish
    "missing dependency" from "checked and not found".
    """
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(str(path))
        if not reader.pages:
            return False
        text_parts: list[str] = []
        for page in reader.pages[:3]:
            try:
                text_parts.append(page.extract_text() or "")
            except Exception:
                continue
        text = "\n".join(text_parts)
        return KEYWORD in text
    except Exception:
        return False


def _check_pypdf(path: Path) -> bool | None:
    try:
        from pypdf import PdfReader
    except ImportError:
        return None
    try:
        reader = PdfReader(str(path))
        if not reader.pages:
            return False
        # Accessing the first page exercises the cross-reference table
        _ = reader.pages[0]
        return True
    except Exception:
        return False


def verify_pdf(path: Path) -> VerificationResult:
    """Verify one PDF and return a structured result."""
    reasons: list[str] = []

    if not path.exists():
        return VerificationResult(
            path=path,
            level=VerificationLevel.FAILED,
            size_bytes=0,
            has_magic=False,
            user_can_read=False,
            has_keyword=None,
            pypdf_ok=None,
            reasons=["file does not exist"],
        )

    size = path.stat().st_size
    if size <= 0:
        reasons.append("size is zero")

    user_can_read = _check_user_read(path)
    if not user_can_read:
        reasons.append("PermissionError on open(rb)")

    has_magic = _check_magic(path) if user_can_read else False
    if not has_magic and user_can_read:
        reasons.append("magic bytes are not %PDF-")

    basic_ok = size > 0 and user_can_read and has_magic

    if not basic_ok:
        return VerificationResult(
            path=path,
            level=VerificationLevel.FAILED,
            size_bytes=size,
            has_magic=has_magic,
            user_can_read=user_can_read,
            has_keyword=None,
            pypdf_ok=None,
            reasons=reasons or ["unknown basic-check failure"],
        )

    has_keyword = _check_keyword(path)
    pypdf_ok = _check_pypdf(path)

    full_ok = bool(has_keyword) and bool(pypdf_ok)
    level = VerificationLevel.VERIFIED_FULL if full_ok else VerificationLevel.VERIFIED_BASIC

    if level is VerificationLevel.VERIFIED_BASIC:
        if has_keyword is False:
            reasons.append("no keyword (likely image-only PDF)")
        elif has_keyword is None:
            reasons.append("pypdf not installed; keyword check skipped")
        if pypdf_ok is False:
            reasons.append("pypdf could not parse first page")

    return VerificationResult(
        path=path,
        level=level,
        size_bytes=size,
        has_magic=has_magic,
        user_can_read=user_can_read,
        has_keyword=has_keyword,
        pypdf_ok=pypdf_ok,
        reasons=reasons,
    )


def verify_directory(
    root: Path, *, glob: str = "*.pdf"
) -> list[VerificationResult]:
    """Verify every PDF directly under ``root`` (non-recursive by default)."""
    results: list[VerificationResult] = []
    if not root.exists():
        return results
    for path in sorted(root.glob(glob)):
        if not path.is_file():
            continue
        results.append(verify_pdf(path))
    return results


def to_table_rows(
    results: Iterable[VerificationResult],
) -> list[dict[str, object]]:
    """Render results into a JSON-friendly list of dicts."""
    return [
        {
            "path": str(r.path),
            "level": r.level.value,
            "size_bytes": r.size_bytes,
            "has_magic": r.has_magic,
            "user_can_read": r.user_can_read,
            "has_keyword": r.has_keyword,
            "pypdf_ok": r.pypdf_ok,
            "reasons": r.reasons,
        }
        for r in results
    ]
