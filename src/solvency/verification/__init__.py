"""PDF verification + filesystem ACL normalisation utilities.

The harness gates downloaded PDFs on three things:

1. magic bytes (it's a real PDF)
2. the *current* user can actually open the file (so a downstream
   double-click in Edge doesn't trip "파일에 대한 액세스가 거부되었습니다")
3. file size > 0

Optional richer checks (Korean keyword presence, ``pypdf`` first-page
parse) are best-effort and only used to upgrade a PDF from
``verified_basic`` to ``verified_full``. Image-only PDFs (e.g. KB손보)
intentionally stop at ``verified_basic``.
"""

from .acl import normalize_file_acl, normalize_tree
from .pdf_check import (
    VerificationLevel,
    VerificationResult,
    verify_pdf,
    verify_directory,
)

__all__ = [
    "VerificationLevel",
    "VerificationResult",
    "verify_pdf",
    "verify_directory",
    "normalize_file_acl",
    "normalize_tree",
]
