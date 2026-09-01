# -*- coding: utf-8 -*-
"""One-off: generate *_insurance_pl_mvp.json (+ full *_insurance_pl.json) for the 3
companies newly added to PL_breakdown.json (owner-approved 2026-09-01) --
하나손해보험(KR0050) / 아이엠라이프생명보험(KR0076) / 카카오페이손해보험(KR1098).

Ticket: inbox/parser/20260901T2000Z__orchestrator__MULTI__inspl_mvp_missing_3_new_companies.md

Why a one-off script instead of re-running an existing batch entry point:
  - scripts/ifrs17_batch_all.py drives CSM extraction from the FULL kics_disclosure.json
    universe (no exclusion list) -- that is why *_csm.json already exists for all 3.
  - The P&L-panel batch (archived scripts/archive/2026-07_unreferenced_scripts/
    ifrs17_batch_insurance_pl.py) filters its targets through
    src.ifrs17.universe.is_excluded(), and NON_LISTED_SKIP names all 3 of these companies
    (2026-05-24 Q1 decision: "no periodic pblntf_ty=A disclosure"). That assumption is
    stale for these 3 -- their FY2022-FY2025 사업보고서 (DOCUMENT-NAME ACODE=00760) raw XML
    is on disk, which is exactly how the PL master's own discover_filings() (no skip-list,
    scans data/dart/FY*/raw/ directly) found them. See ticket 답변 for the full root-cause
    writeup and recommendation -- not fixed here (blast radius: is_excluded() also gates
    the LIVE ifrs17_batch_{measurement,sensitivity,historical}.py, out of this ticket's
    scope of "mvp extract + viz panel only").
  - That archived script also targets the PRE-Reorg#2 flat raw layout
    (settings.raw_dir = data/dart/raw/), so it would not find these files even if unblocked.

This script instead calls the same extractor (src.ifrs17.insurance_pl_extractor) directly
against the canonical (Reorg #2) raw dir, exactly mirroring the pattern
scripts/ifrs17_ingest_audit_annual.py uses for its 5 special-cased companies -- extraction
only, no universe gate.

min_score note (하나손해보험 only): the default extract_insurance_pl_tables(min_score=5) found
ZERO mvp_candidate rows for KR0050 -- its real "보험손익 상세내역" note (주석29, the same table
scripts/pl_breakdown/companies.py::_hana_sonbo_csm_amort() already validated against
CSM_waterfall.json: 21,885,413천원 CSM상각 for 2025.4Q, matching 218.9억 within tolerance)
scores exactly 4, one point under the cutoff. Verified this isn't a noise problem: rescanning
all 3 companies at min_score=0 and keeping only rows the EXISTING is_mvp_table() structural
gate (slice_label/block_type/reinsurance checks, unaffected by score) accepts yields the
IDENTICAL 8/5 candidates already found for 아이엠라이프/카카오페이 (score>=5 already), and
exactly the 2 (당기/전기) correct rows for 하나손해 -- no extra junk. So the mvp file is built
from a min_score=0 pass + the gate; the full companion file keeps the conventional min_score=5
signal-bearing dump (matches every other company's *_insurance_pl.json), so for 하나손해 the mvp
file is (correctly) not a strict subset of the full file -- documented here, not a bug.

Scope: latest annual filing (FY2025, rcept filed 2026) only, one mvp file per company --
matching how every OTHER non-AUDIT_REPORT_ANNUAL company in data/dart/extracted/ is
represented in this panel (build_panel in viz_build_ifrs17_panels.py picks a single BEST
(status, rcept) file per company; earlier years would just be shadowed, not additive --
the panel is a single-snapshot "원표" view, not a time series like csm_amort_schedule).
The income-statement note itself carries 당기/전기 columns, so FY2025's filing already
covers the FY2024 comparative too.

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260901_insurance_pl_mvp_3new.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.insurance_pl_extractor import (  # noqa: E402
    extract_insurance_pl_tables,
    to_jsonable,
)
from scripts._dart_path_helpers import annual_raw_dir  # noqa: E402

# (kics_name / canonical DART corp_name -- identical for all 3, verified against
# PL_breakdown.json's 원수사명 column, kr_code, rcept_no of the FY2025 annual filing)
TARGETS = [
    ("하나손해보험", "KR0050", "20260325000538"),
    ("아이엠라이프생명보험", "KR0076", "20260406004393"),
    ("카카오페이손해보험", "KR1098", "20260323001537"),
]


def main() -> None:
    summary = []
    for name, kr_code, rcept_no in TARGETS:
        raw_dir = annual_raw_dir(canonical_name=name, rcept_no=rcept_no, kr_code=kr_code)
        if not raw_dir.is_dir():
            rec = {"company": name, "kr_code": kr_code, "status": "no_raw_dir", "dir": str(raw_dir)}
            summary.append(rec)
            print(json.dumps(rec, ensure_ascii=False))
            continue

        all_tables: list[dict] = []
        mvp_tables: list[dict] = []
        parse_errors = []
        xmls = sorted(raw_dir.glob("*.xml"))
        for xml in xmls:
            # Full dump: conventional min_score=5 (matches every other company's
            # *_insurance_pl.json -- a signal-bearing candidate list, not a raw kitchen sink).
            try:
                tables = extract_insurance_pl_tables(xml, company_name=name)
            except Exception as exc:  # noqa: BLE001
                parse_errors.append({"xml": xml.name, "error": str(exc)})
                continue
            for t in tables:
                obj = to_jsonable(t)
                obj["_source_xml"] = xml.name
                all_tables.append(obj)

            # MVP dump: min_score=0 + the existing is_mvp_table() structural gate (see
            # module docstring -- verified clean/non-noisy for all 3 companies; only
            # 하나손해보험 actually gains a row this way, its real target scores 4).
            try:
                scan = extract_insurance_pl_tables(xml, company_name=name, min_score=0)
            except Exception as exc:  # noqa: BLE001
                parse_errors.append({"xml": xml.name, "error": f"mvp_scan: {exc}"})
                continue
            for t in scan:
                if t.mvp_candidate:
                    obj = to_jsonable(t)
                    obj["_source_xml"] = xml.name
                    mvp_tables.append(obj)

        out_full = settings.extracted_dir / f"{name}_{rcept_no}_insurance_pl.json"
        out_full.write_text(json.dumps(all_tables, ensure_ascii=False, indent=2), encoding="utf-8")
        out_mvp = settings.extracted_dir / f"{name}_{rcept_no}_insurance_pl_mvp.json"
        out_mvp.write_text(json.dumps(mvp_tables, ensure_ascii=False, indent=2), encoding="utf-8")

        rec = {
            "company": name,
            "kr_code": kr_code,
            "rcept_no": rcept_no,
            "raw_dir": str(raw_dir),
            "xml_count": len(xmls),
            "status": "ok" if all_tables else "no_table",
            "tables_total": len(all_tables),
            "tables_mvp": len(mvp_tables),
            "mvp_captions": [t["caption"][:60] for t in mvp_tables],
            "parse_errors": parse_errors,
            "full_out": str(out_full),
            "mvp_out": str(out_mvp),
        }
        summary.append(rec)
        print(json.dumps(
            {k: rec[k] for k in ("company", "status", "tables_total", "tables_mvp", "mvp_captions")},
            ensure_ascii=False,
        ))

    print("\n[summary]")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
