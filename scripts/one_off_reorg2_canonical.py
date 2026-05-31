#!/usr/bin/env python3
"""One-off reorg #2: apply <source>/<period>/raw/KR####_<name> to DART + KIDI;
rename data/assoc/ -> data/_derived/.

Why this exists (2026-05-30j): the 2026-05-30g workflow reorg only touched
data/disclosure/ + data/ir/. The user then pointed out that DART/KIDI were
left in their per-source legacy conventions and that data/assoc/ holds
derived outputs (not raw data) so its name is misleading.

This script:
  1. Moves data/assoc/ -> data/_derived/ (verbatim copy of contents).
  2. KIDI: data/kidi/raw/<stamp>/KR####_<YYYYMM>.json
          -> data/kidi/FY<year>_Q<q>/raw/KR####_<YYYYMM>.json
     (YYYYMM month 03/06/09/12 -> Q1/Q2/Q3/Q4)
  3. DART raw_history: data/dart/raw_history/<name>/<YYYY.QQ>/document.zip
          -> data/dart/FY<year>_Q<q>/raw/KR####_<name>/document.zip
     (period notation '2025.4Q' -> 'FY2025_Q4')
  4. DART raw (annual): data/dart/raw/<name>[_consolidated]_<rcept>/...
          -> data/dart/FY<rcept_year-1>_Q4/raw/KR####_<name>[__cons]/...
     (rcept YYYYMMDDxxxxxx; year-1 is the report period)

Archive root: data/_archive/20260530T120000Z_reorg2/

Logs every move to data/_archive/20260530T120000Z_reorg2/_reorg2.log.

Idempotent: skips moves where the source no longer exists. Verifies destination
parent exists before mv.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")

STAMP = "20260530T120000Z_reorg2"
ARCHIVE_ROOT = ROOT / "data" / "_archive" / STAMP
LOG_PATH = ARCHIVE_ROOT / "_reorg2.log"

DRY_RUN = False  # set True for plan-only

# ---------------------------------------------------------------------------
# KR ↔ name mappings
# ---------------------------------------------------------------------------

KICS_PATH = ROOT / "kics_disclosure.json"
_kics = json.loads(KICS_PATH.read_text(encoding="utf-8"))
KR_TO_KICS_NAME: dict[str, str] = {}
KICS_NAME_TO_KR: dict[str, str] = {}
for row in _kics:
    kr, nm = row.get("원보험사코드"), row.get("원수사명")
    if kr and nm and kr not in KR_TO_KICS_NAME:
        KR_TO_KICS_NAME[kr] = nm
        KICS_NAME_TO_KR[nm] = kr

# DART raw uses some short aliases vs kics full names
DART_TO_KICS_ALIAS: dict[str, str] = {
    "삼성생명": "삼성생명보험",
    "미래에셋생명": "미래에셋생명보험",
    "코리안리": "코리안리재보험",
    "케이비라이프생명보험": "KB라이프생명",
    "에이아이지손해보험": "AIG손해보험",
}
# Reverse for kics -> dart raw name (where they diverge)
KICS_TO_DART_ALIAS = {v: k for k, v in DART_TO_KICS_ALIAS.items()}

# Non-K-ICS entity (AIA carries no KR but has DART filings)
AIA_DART_NAME = "에이아이에이생명보험"
AIA_KR = "AIA"

# KIDI cbCmp code -> KR (read from script MAPPING via import)
sys.path.insert(0, str(ROOT))
from scripts.ingest_kidi_monthly_premium import MAPPING as KIDI_MAPPING  # noqa: E402

KIDI_CBCMP_TO_KR: dict[str, str] = {}
for kr, (cbcmp, table) in KIDI_MAPPING.items():
    KIDI_CBCMP_TO_KR[cbcmp] = kr


def dart_name_to_kr(dart_name: str) -> str | None:
    """Return KR code (or 'AIA') for a DART raw directory name token."""
    kics = DART_TO_KICS_ALIAS.get(dart_name, dart_name)
    if kics == AIA_DART_NAME:
        return AIA_KR
    return KICS_NAME_TO_KR.get(kics)


def kics_name_to_dart_name(kics: str) -> str:
    return KICS_TO_DART_ALIAS.get(kics, kics)


# ---------------------------------------------------------------------------
# Move log
# ---------------------------------------------------------------------------

_log_lines: list[str] = []


def _log(msg: str) -> None:
    print(msg, flush=True)
    _log_lines.append(msg)


def _do_move(src: Path, dst: Path, kind: str) -> bool:
    if not src.exists():
        _log(f"  SKIP-MISSING {kind} {src}")
        return False
    if dst.exists():
        _log(f"  SKIP-DST-EXISTS {kind} {src} -> {dst}")
        return False
    if DRY_RUN:
        _log(f"  PLAN {kind} {src} -> {dst}")
        return True
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(dst))
    _log(f"  MV {kind} {src} -> {dst}")
    return True


# ---------------------------------------------------------------------------
# 1. data/assoc/ -> data/_derived/
# ---------------------------------------------------------------------------

def step_rename_assoc() -> int:
    src = ROOT / "data" / "assoc"
    dst = ROOT / "data" / "_derived"
    if not src.exists():
        _log(f"[step1] assoc already moved (src missing)")
        return 0
    if dst.exists():
        # merge file-by-file
        moves = 0
        for f in src.iterdir():
            tgt = dst / f.name
            if _do_move(f, tgt, "assoc->derived"):
                moves += 1
        # remove empty assoc
        try:
            src.rmdir()
        except OSError:
            _log(f"  WARN assoc dir not empty after merge")
        return moves
    if DRY_RUN:
        _log(f"  PLAN rename {src} -> {dst}")
        return 1
    shutil.move(str(src), str(dst))
    _log(f"  MV-DIR {src} -> {dst}")
    return 1


# ---------------------------------------------------------------------------
# 2. KIDI: data/kidi/raw/<stamp>/KR####_<YYYYMM>.json
#      -> data/kidi/FY<year>_Q<q>/raw/KR####_<YYYYMM>.json
# ---------------------------------------------------------------------------

def yyyymm_to_period(yyyymm: str) -> str | None:
    if len(yyyymm) != 6:
        return None
    year, mm = yyyymm[:4], yyyymm[4:]
    if mm == "03": q = 1
    elif mm == "06": q = 2
    elif mm == "09": q = 3
    elif mm == "12": q = 4
    else: return None
    return f"FY{year}_Q{q}"


def step_kidi_reorg() -> int:
    raw_root = ROOT / "data" / "kidi" / "raw"
    if not raw_root.exists():
        _log("[step2] no data/kidi/raw")
        return 0
    moves = 0
    for stamp_dir in raw_root.iterdir():
        if not stamp_dir.is_dir():
            continue
        for f in stamp_dir.iterdir():
            if not f.is_file() or f.suffix != ".json":
                continue
            # filename: KR####_<YYYYMM>.json  (or AIA_<YYYYMM>.json)
            stem = f.stem  # KR0008_202503
            parts = stem.rsplit("_", 1)
            if len(parts) != 2:
                _log(f"  SKIP-PARSE {f}")
                continue
            kr_code, yyyymm = parts
            period = yyyymm_to_period(yyyymm)
            if not period:
                _log(f"  SKIP-PERIOD {f} (yyyymm={yyyymm})")
                continue
            dst = ROOT / "data" / "kidi" / period / "raw" / f.name
            if _do_move(f, dst, "kidi"):
                moves += 1
        # Remove stamp_dir if empty
        try:
            if not any(stamp_dir.iterdir()):
                stamp_dir.rmdir()
                _log(f"  RMDIR {stamp_dir}")
        except OSError:
            pass
    # Try to remove data/kidi/raw if now empty
    try:
        if raw_root.exists() and not any(raw_root.iterdir()):
            raw_root.rmdir()
            _log(f"  RMDIR {raw_root}")
    except OSError:
        pass
    return moves


# ---------------------------------------------------------------------------
# 3. DART raw_history: <name>/<YYYY.QQ>/document.zip
#     -> data/dart/FY<year>_Q<q>/raw/KR####_<name>/document.zip
# ---------------------------------------------------------------------------

def hist_period_to_canonical(p: str) -> str | None:
    # '2025.4Q' -> 'FY2025_Q4'
    if "." not in p or not p.endswith("Q"):
        return None
    year, q = p.split(".", 1)
    qnum = q.rstrip("Q")
    return f"FY{year}_Q{qnum}"


def step_dart_raw_history() -> int:
    hist_root = ROOT / "data" / "dart" / "raw_history"
    if not hist_root.exists():
        _log("[step3] no data/dart/raw_history")
        return 0
    moves = 0
    for co_dir in list(hist_root.iterdir()):
        if not co_dir.is_dir():
            continue
        dart_name = co_dir.name
        kr = dart_name_to_kr(dart_name)
        if not kr:
            _log(f"  SKIP-NO-KR raw_history/{dart_name}")
            continue
        for period_dir in list(co_dir.iterdir()):
            if not period_dir.is_dir():
                continue
            period_canon = hist_period_to_canonical(period_dir.name)
            if not period_canon:
                _log(f"  SKIP-PERIOD raw_history/{dart_name}/{period_dir.name}")
                continue
            dst_dir = ROOT / "data" / "dart" / period_canon / "raw" / f"{kr}_{dart_name}"
            if _do_move(period_dir, dst_dir, "dart-hist"):
                moves += 1
        # Remove empty co_dir
        try:
            if not any(co_dir.iterdir()):
                co_dir.rmdir()
                _log(f"  RMDIR {co_dir}")
        except OSError:
            pass
    try:
        if hist_root.exists() and not any(hist_root.iterdir()):
            hist_root.rmdir()
            _log(f"  RMDIR {hist_root}")
    except OSError:
        pass
    return moves


# ---------------------------------------------------------------------------
# 4. DART raw (annual): <name>[_consolidated]_<rcept>
#     -> data/dart/FY<year>_Q4/raw/KR####_<name>[__cons]
#     (where <year> = int(rcept[:4]) - 1 for annual reports)
# ---------------------------------------------------------------------------

CORPCODE_XML = "CORPCODE.xml"  # API artifact, not a rcept dir


def step_dart_raw_annual() -> int:
    raw_root = ROOT / "data" / "dart" / "raw"
    if not raw_root.exists():
        _log("[step4] no data/dart/raw")
        return 0
    moves = 0
    skip = []
    for entry in list(raw_root.iterdir()):
        if entry.is_file() and entry.name == CORPCODE_XML:
            # Keep CORPCODE.xml at data/dart/raw/ (API artifact, will be re-located)
            continue
        if not entry.is_dir():
            continue
        # Parse name_[consolidated_]rcept
        name = entry.name
        # rcept is last underscore-separated token, 14-digit numeric
        parts = name.rsplit("_", 1)
        if len(parts) != 2 or not (parts[1].isdigit() and len(parts[1]) == 14):
            _log(f"  SKIP-PARSE raw/{name}")
            skip.append(name)
            continue
        body, rcept = parts
        variant = ""
        if body.endswith("_consolidated"):
            body = body[: -len("_consolidated")]
            variant = "__cons"
        dart_name = body
        kr = dart_name_to_kr(dart_name)
        if not kr:
            _log(f"  SKIP-NO-KR raw/{name}")
            skip.append(name)
            continue
        # rcept first 4 digits = filing year; FY = filing_year - 1 (for annual reports)
        filing_year = int(rcept[:4])
        report_year = filing_year - 1
        period = f"FY{report_year}_Q4"
        dst = ROOT / "data" / "dart" / period / "raw" / f"{kr}_{dart_name}{variant}_{rcept}"
        if _do_move(entry, dst, "dart-annual"):
            moves += 1
    # Move CORPCODE.xml into data/dart/ (top-level alongside raw)
    cc = raw_root / CORPCODE_XML
    if cc.exists():
        dst = ROOT / "data" / "dart" / CORPCODE_XML
        if not dst.exists():
            if not DRY_RUN:
                shutil.move(str(cc), str(dst))
            _log(f"  MV-FILE {cc} -> {dst}")
    try:
        if raw_root.exists() and not any(raw_root.iterdir()):
            raw_root.rmdir()
            _log(f"  RMDIR {raw_root}")
    except OSError:
        pass
    if skip:
        _log(f"  ({len(skip)} skipped — review manually)")
    return moves


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)
    _log(f"=== Reorg #2 starting (DRY_RUN={DRY_RUN}) ===")

    _log("\n[Step 1] data/assoc/ -> data/_derived/")
    n1 = step_rename_assoc()
    _log(f"  -> {n1} ops")

    _log("\n[Step 2] data/kidi/raw/<stamp>/ -> data/kidi/<period>/raw/")
    n2 = step_kidi_reorg()
    _log(f"  -> {n2} moves")

    _log("\n[Step 3] data/dart/raw_history/<name>/<YYYY.QQ>/ -> data/dart/<period>/raw/KR####_<name>/")
    n3 = step_dart_raw_history()
    _log(f"  -> {n3} moves")

    _log("\n[Step 4] data/dart/raw/<name>_<rcept>/ -> data/dart/<period>/raw/KR####_<name>[__cons]_<rcept>/")
    n4 = step_dart_raw_annual()
    _log(f"  -> {n4} moves")

    LOG_PATH.write_text("\n".join(_log_lines) + "\n", encoding="utf-8")
    _log(f"\nLog written: {LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
