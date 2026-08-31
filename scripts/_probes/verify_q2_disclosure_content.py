#!/usr/bin/env python3
"""Content-verify FY2026_Q2 정기경영공시 downloads.

Supersedes check_q2_disclosure_freshness.py, which only hash-compared against
FY2026_Q1. A hash difference alone does NOT prove you got the right quarter --
a re-rendered 1Q file, a 2025 결산 file, or a DART 사업보고서 all differ from
the Q1 baseline while being the wrong document (this repo has hit the last one:
see changelog 2026-08-21, KR0005/KR0071 wrong-document).

So this asserts three independent things about the actual PDF bytes:

  1. freshness  -- SHA256 differs from the FY2026_Q1 file for the same KR code
  2. period     -- the document text names 2026 2분기/상반기 or a 2026-06-30
                   as-of date, and does NOT read as a 1분기/03-31 document
  3. doctype    -- it reads as a K-ICS 정기경영공시 (지급여력 / 경영공시 /
                   보험업감독규정), not some other filing

A file passes only if all three pass. Anything else is reported, never
silently accepted.

Usage:
  python scripts/_probes/verify_q2_disclosure_content.py [KR0050 ...]
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import fitz  # PyMuPDF

ROOT = Path(__file__).resolve().parents[2]
Q1_DIR = ROOT / "data" / "disclosure" / "FY2026_Q1" / "raw"
Q2_DIR = ROOT / "data" / "disclosure" / "FY2026_Q2" / "pdf"
META_DIR = ROOT / "data" / "disclosure" / "_meta" / "FY2026_Q2"
OUT = META_DIR / "content_verification.json"

# as-of / period evidence
Q2_ASOF = re.compile(
    r"2026\s*[.\-년]\s*0?6\s*[.\-월]\s*3?0?\s*일?|"
    r"2026\s*[.\-년]?\s*2\s*/?\s*4?\s*분기|"
    r"2026[^0-9]{0,8}상반기|"
    r"FY\s*2026\s*2\s*/\s*4\s*분기|FY\s*26\s*2\s*분기"
)
Q1_ASOF = re.compile(
    r"2026\s*[.\-년]\s*0?3\s*[.\-월]\s*3?1?\s*일?|"
    r"2026\s*[.\-년]?\s*1\s*/?\s*4?\s*분기|"
    r"FY\s*2026\s*1\s*/\s*4\s*분기|FY\s*26\s*1\s*분기"
)
DOCTYPE = re.compile(r"지급여력|경영공시|경영통일공시|보험업감독규정|K-ICS|킥스")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def head_text(path: Path, pages: int = 8) -> tuple[str, int]:
    with fitz.open(path) as doc:
        n = doc.page_count
        txt = "\n".join(doc[i].get_text() for i in range(min(pages, n)))
    return txt, n


def verify(kr: str, q2_path: Path, q1_by_kr: dict[str, Path]) -> dict:
    rec: dict = {"kr": kr, "file": q2_path.name, "bytes": q2_path.stat().st_size}
    checks: dict[str, bool | None] = {}

    # 1. freshness
    h2 = sha256(q2_path)
    rec["sha256"] = h2
    q1 = q1_by_kr.get(kr)
    if q1 is None:
        checks["freshness"] = None
        rec["freshness_note"] = "no FY2026_Q1 baseline for this KR"
    else:
        checks["freshness"] = sha256(q1) != h2
        rec["q1_baseline"] = q1.name
        if not checks["freshness"]:
            rec["freshness_note"] = f"IDENTICAL to {q1.name} -- stale re-download"

    # 2/3. period + doctype, from the bytes themselves
    try:
        txt, npages = head_text(q2_path)
        rec["pages"] = npages
        flat = re.sub(r"\s+", " ", txt)
        q2_hits = Q2_ASOF.findall(flat)
        q1_hits = Q1_ASOF.findall(flat)
        rec["q2_asof_hits"] = list(dict.fromkeys(q2_hits))[:8]
        rec["q1_asof_hits"] = list(dict.fromkeys(q1_hits))[:8]
        checks["period_is_q2"] = bool(q2_hits) and len(q2_hits) >= len(q1_hits)
        checks["doctype_is_disclosure"] = bool(DOCTYPE.search(flat))
        rec["text_chars_first8p"] = len(txt)
        if len(txt) < 200:
            rec["text_note"] = (
                "near-zero text layer -- likely a raster/scanned PDF; "
                "period claim NOT verifiable by text search (see changelog "
                "2026-08-21 KR0005: fitz keyword 0 hits was a false alarm)"
            )
    except Exception as exc:
        rec["error"] = f"{type(exc).__name__}: {exc}"
        checks["period_is_q2"] = False
        checks["doctype_is_disclosure"] = False

    rec["checks"] = checks
    hard = [v for v in checks.values() if v is not None]
    rec["verdict"] = "accept" if all(hard) else "reject"
    return rec


def main() -> int:
    only = set(sys.argv[1:]) or None
    q1_by_kr = {p.name.split("_", 1)[0]: p for p in Q1_DIR.glob("*.pdf")}
    files = sorted(p for p in Q2_DIR.glob("*") if p.is_file())
    if only:
        files = [p for p in files if p.name.split("_", 1)[0] in only]
    if not files:
        print("[verify] no FY2026_Q2 files present -- nothing to verify")
        return 0

    results = []
    for p in files:
        kr = p.name.split("_", 1)[0]
        rec = verify(kr, p, q1_by_kr)
        results.append(rec)
        print(f"[{kr}] {rec['verdict'].upper():<7} {rec['file']}")
        print(f"      pages={rec.get('pages','?')} bytes={rec['bytes']:,} checks={rec['checks']}")
        print(f"      q2_asof={rec.get('q2_asof_hits')} q1_asof={rec.get('q1_asof_hits')}")
        for k in ("freshness_note", "text_note", "error"):
            if rec.get(k):
                print(f"      {k}: {rec[k]}")

    META_DIR.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    n_ok = sum(1 for r in results if r["verdict"] == "accept")
    print(f"\n[summary] accept={n_ok}/{len(results)} -> {OUT}")
    return 0 if n_ok == len(results) else 2


if __name__ == "__main__":
    raise SystemExit(main())
