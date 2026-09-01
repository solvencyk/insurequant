# -*- coding: utf-8 -*-
"""Phase-2 provenance emission for kics_rate_sensitivity.json — validation inbox
20260803T0520Z__validation__MULTI__rate_sensitivity_provenance_sidecar.md (UH-8).

`kics_rate_sensitivity` was in Env.MASTER_FILES (mtime watch only) but had no sidecar, so
validate_data_contract.py CHECK 2 never looked at its as-of / source axis at all — a stale
quarter could render with the gate silent (same class as PM-2026-06-16). This emits the
sidecar so validation can wire the 2a(iv) axis; per the ticket the order matters (publish
first, wire second), otherwise CHECK 2 red-outs immediately and blocks push.

Join key: this master carries `원보험사코드`, so `company_code` is the KR code (no name-join
trap like sensitivity_heatmap) and `quarter` is `공시분기` verbatim ("2025.4Q").

source_file: the Docling MD the extractor actually read. Resolved by importing
extract_kics_rate_sensitivity.pick_md rather than re-implementing the glob — the picker has
real logic (prefers `_amended`, then largest file) and a copy here would drift the moment the
extractor changes. Falls back to the raw PDF (data/disclosure/<period>/{raw,pdf}/ — see
scripts/_disclosure_pdf_paths.py) when no MD is on disk, which happens for cells loaded from
the owner gold sheet (scripts/build_apply_user_ratesens_gold.py) rather than from a converted MD.

Both md_inbox/ and data/disclosure/ are gitignored, so source_file resolves on the machine that
runs the pipeline — same convention as the sensitivity_heatmap sidecar's DART raw XML paths.

Usage: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
           scripts/emit_rate_sensitivity_provenance.py [--dry-run]
"""
from __future__ import annotations

import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from extract_kics_rate_sensitivity import pick_md  # noqa: E402  (needs REPO on sys.path)
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402

SRC = REPO / "kics_rate_sensitivity.json"
OUT = REPO / "kics_rate_sensitivity_provenance.json"

_QUARTER_END = {1: "-03-31", 2: "-06-30", 3: "-09-30", 4: "-12-31"}


def quarter_to_period(q: str) -> str:
    """'2025.4Q' -> 'FY2025_Q4' (the md_inbox / data/disclosure directory name)."""
    year, qq = q.split(".")
    return f"FY{year}_Q{qq[0]}"


def quarter_to_as_of(q: str) -> str:
    """'2025.4Q' -> '2025-12-31'. The gate REDs (STALE_AS_OF) unless as_of_date's quarter
    equals `quarter`, so this must be the quarter END, not the filing date."""
    year, qq = q.split(".")
    return f"{year}{_QUARTER_END[int(qq[0])]}"


def resolve_source(code: str, quarter: str):
    """-> (repo-relative source_file, kind) or (None, None)."""
    period = quarter_to_period(quarter)
    md = pick_md(code, period)
    if md:
        return Path(md).relative_to(REPO).as_posix(), "md"
    pdfs = disclosure_pdfs(period, code)
    if pdfs:
        amended = [p for p in pdfs if "_amended" in p.name]
        pdf = max(amended or pdfs, key=lambda p: p.stat().st_size)
        return pdf.relative_to(REPO).as_posix(), "pdf"
    return None, None


def main() -> int:
    dry = "--dry-run" in sys.argv
    rows = json.loads(SRC.read_text(encoding="utf-8"))

    pairs = sorted({(r["원보험사코드"], r["공시분기"]) for r in rows})
    names = {r["원보험사코드"]: r.get("원수사명", r["원보험사코드"]) for r in rows}

    cells, unresolved = [], []
    kinds = {"md": 0, "pdf": 0}
    for code, quarter in pairs:
        source_file, kind = resolve_source(code, quarter)
        if not source_file:
            unresolved.append((code, names.get(code, code), quarter))
            continue
        kinds[kind] += 1
        cells.append({
            "company_code": code,
            "quarter": quarter,
            "item_block": "rate_sensitivity",
            "source_id": "DISCLOSURE_MD",
            "as_of_date": quarter_to_as_of(quarter),
            "source_file": source_file,
        })

    doc = {
        "master": "kics_rate_sensitivity",
        "generated_at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"),
        "emitter": "parser",
        "cells": cells,
    }

    print(f"kics_rate_sensitivity: rows={len(rows)} (회사,분기)={len(pairs)} cells={len(cells)} "
          f"(md={kinds['md']} pdf-fallback={kinds['pdf']})")
    if unresolved:
        print(f"  UNRESOLVED source_file ({len(unresolved)}) — 게이트 MISSING_PROVENANCE 후보:")
        for code, name, quarter in unresolved:
            print(f"    {code} {name} {quarter}")
    if dry:
        print("(dry-run; no write)")
        return 0
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  wrote {OUT.name}")
    return 1 if unresolved else 0


if __name__ == "__main__":
    raise SystemExit(main())
