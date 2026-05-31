# -*- coding: utf-8 -*-
"""Canonical-path helpers for DART downloader scripts.

After Reorg #2, DART raw downloads live at:

  data/dart/FY<year>_Q<q>/raw/<leaf>/

with leaf naming:
  - 분기/반기 (A002/A003): `KR####_<name>`           — period dir disambiguates
  - 사업/감사 (A001/F):    `KR####_<name>_<rcept>`   — multiple annual filings per FY

For group holdings (회사 in DART but not in kics_disclosure), the helper falls
back to `<corp_code>_<name>` prefix.

These helpers replace the OLD layout the batch scripts used to write to:
  data/dart/raw/<canonical>_<rcept_no>/
  data/dart/raw_history/<canonical>/<YYYY.QQ>/
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
KICS_JSON = REPO / "kics_disclosure.json"
DART_ROOT = REPO / "data" / "dart"


# K-ICS name → KR code overrides for cases where the kics_disclosure file
# doesn't carry the name we get from upstream (e.g. AUDIT_REPORT_ANNUAL
# foreign-affiliate insurers are EXCLUDED from kics so they don't appear
# in the disclosure JSON, but they DO have KR codes in data/ir/_kr_map.json).
# Keep this small — it only covers cases where kics lookup fails AND we
# know the code from another source.
_KICS_NAME_OVERRIDES: dict[str, str] = {
    # AUDIT_REPORT_ANNUAL (외부감사 only) — codes confirmed via _kr_map.json
    "라이나생명보험": "KR0074",
    "메트라이프생명보험": "KR0095",
    "에이아이에이생명보험": "KR0080",
    "하나생명보험": "KR0097",
    "처브라이프생명보험": "KR0100",
    # 한화생명 — kics uses '한화생명' but other sources may pass '한화생명보험'
    "한화생명보험": "KR0068",
}


@lru_cache(maxsize=1)
def _kics_name_to_kr() -> dict[str, str]:
    """Build {원수사명: KR_code} from kics_disclosure.json (cached)."""
    data = json.loads(KICS_JSON.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for row in data:
        name = row.get("원수사명")
        code = (row.get("원보험사코드") or row.get("원수사코드")
                or row.get("회사코드"))
        if name and code:
            # First non-empty wins (kics file may have multiple rows per company)
            out.setdefault(name, code)
    out.update(_KICS_NAME_OVERRIDES)
    return out


def kr_for_kics_name(kics_name: str | None) -> str | None:
    """Look up KR code by 원수사명 (kics_disclosure key).

    Returns None for group holdings or unknown names so caller can fall back
    to corp_code prefix.
    """
    if not kics_name:
        return None
    table = _kics_name_to_kr()
    if kics_name in table:
        return table[kics_name]
    # Common suffix drift: kics has "삼성생명보험" but resolve_corp returns "삼성생명".
    # Try adding "보험" suffix if missing.
    if not kics_name.endswith("보험") and (kics_name + "보험") in table:
        return table[kics_name + "보험"]
    return None


_PERIOD_RE = re.compile(r"^(20\d{2})\.([1-4])Q$")


def period_label_to_dir(period_label: str) -> str:
    """'2023.1Q' -> 'FY2023_Q1'."""
    m = _PERIOD_RE.match(period_label.strip())
    if not m:
        raise ValueError(f"unexpected period label: {period_label!r}")
    return f"FY{m.group(1)}_Q{m.group(2)}"


def annual_period_dir_for_rcept(rcept_no: str) -> str:
    """For 사업보고서/감사보고서: filing year - 1 -> 'FY{year}_Q4'."""
    if len(rcept_no) < 4 or not rcept_no[:4].isdigit():
        raise ValueError(f"unexpected rcept_no: {rcept_no!r}")
    filing_year = int(rcept_no[:4])
    return f"FY{filing_year - 1}_Q4"


def _leaf_prefix(
    kr_code: str | None,
    kics_name: str | None,
    corp_code: str | None,
) -> str:
    """Pick prefix: explicit KR > KR looked up from kics_name > corp_code > empty."""
    if kr_code:
        return kr_code
    looked_up = kr_for_kics_name(kics_name)
    if looked_up:
        return looked_up
    return corp_code or ""


def quarterly_raw_dir(
    *,
    canonical_name: str,
    period_label: str,
    kr_code: str | None = None,
    kics_name: str | None = None,
    corp_code: str | None = None,
) -> Path:
    """Canonical raw dir for 분기/반기 reports.

    Leaf = `<prefix>_<canonical_name>` (no rcept suffix — period dir
    disambiguates). canonical_name is the DART corp_name as returned by
    `resolve_corp`/`pick_corp`; this matches Reorg #2's leaf naming
    convention even when DART's spelling differs from the kics 원수사명
    (e.g. DART '삼성생명' vs kics '삼성생명보험').
    """
    prefix = _leaf_prefix(kr_code, kics_name, corp_code)
    leaf = f"{prefix}_{canonical_name}" if prefix else canonical_name
    return DART_ROOT / period_label_to_dir(period_label) / "raw" / leaf


def annual_raw_dir(
    *,
    canonical_name: str,
    rcept_no: str,
    kr_code: str | None = None,
    kics_name: str | None = None,
    corp_code: str | None = None,
) -> Path:
    """Canonical raw dir for 사업/감사보고서.

    Leaf = `<prefix>_<canonical_name>_<rcept_no>`. Year = filing_year - 1.
    rcept_no is appended because >1 annual filing per insurer per FY is
    possible (별도 + 연결). canonical_name follows DART corp_name (see
    `quarterly_raw_dir` docstring).
    """
    prefix = _leaf_prefix(kr_code, kics_name, corp_code)
    if prefix:
        leaf = f"{prefix}_{canonical_name}_{rcept_no}"
    else:
        leaf = f"{canonical_name}_{rcept_no}"
    return DART_ROOT / annual_period_dir_for_rcept(rcept_no) / "raw" / leaf
