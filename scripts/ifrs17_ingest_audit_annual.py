# -*- coding: utf-8 -*-
"""F11: ingest annual CSM tables for foreign-affiliate life insurers whose
only disclosure channel is the DART 외부감사 audit report (pblntf_ty="F").

These 5 insurers (src.ifrs17.universe.AUDIT_REPORT_ANNUAL) file no periodic
사업보고서, so ifrs17_batch_all skips them as ``no_annual_filing``. Their
standalone 감사보고서 carries the same IFRS17 보험계약 주석 (CSM amort schedule),
which the existing csm_extractor parses unchanged.

Also runs the measurement / insurance-P&L / sensitivity extractors on the
same XMLs so the glob-driven viz builders (waterfall, panels, bubble) pick
the 5 up automatically — same artifact names the per-tier batch scripts emit.

Artifacts (canonical layout, Reorg #2):
  data/dart/FY<year>_Q4/raw/<KR####>_<canonical>_<rcept_no>/...
  data/dart/extracted/<canonical>_<rcept_no>_csm.json
  data/dart/extracted/<canonical>_<rcept_no>_measurement(.|_mvp.)json
  data/dart/extracted/<canonical>_<rcept_no>_insurance_pl(.|_mvp.)json
  data/dart/extracted/<canonical>_<rcept_no>_sensitivity(.|_mvp.)json
  data/dart/extracted/_audit_annual_summary.json

Usage:
  python scripts/ifrs17_ingest_audit_annual.py            # latest audit report
  python scripts/ifrs17_ingest_audit_annual.py --year 2024
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.csm_extractor import extract_csm_tables, to_jsonable  # noqa: E402
from src.ifrs17.insurance_pl_extractor import (  # noqa: E402
    extract_insurance_pl_tables,
    to_jsonable as pl_to_jsonable,
)
from src.ifrs17.measurement_extractor import (  # noqa: E402
    extract_measurement_tables,
    to_jsonable as meas_to_jsonable,
)
from src.ifrs17.opendart_client import OpenDARTClient, OpenDARTError  # noqa: E402
from src.ifrs17.sensitivity_extractor import (  # noqa: E402
    extract_sensitivity_tables,
    to_jsonable as sens_to_jsonable,
)
from src.ifrs17.universe import AUDIT_REPORT_ANNUAL  # noqa: E402
from scripts.ifrs17_batch_all import NAME_ALIASES  # noqa: E402

# Canonical raw-path helper (post-Reorg #2): FY<y>_Q4/raw/<KR>_<name>_<rcept>/.
from scripts._dart_path_helpers import annual_raw_dir  # noqa: E402

# Tier extractors that mirror the per-tier batch scripts. Each emits a full
# artifact (<canonical>_<rcept>_<suffix>.json) plus an _mvp.json subset.
TIER_EXTRACTORS = [
    ("measurement", extract_measurement_tables, meas_to_jsonable),
    ("insurance_pl", extract_insurance_pl_tables, pl_to_jsonable),
    ("sensitivity", extract_sensitivity_tables, sens_to_jsonable),
]


def pick_corp(client: OpenDARTClient, name: str) -> dict | None:
    query = NAME_ALIASES.get(name, name)
    ms = client.find_corp_codes_by_name(query)
    exact = [m for m in ms if m["corp_name"] == query]
    return exact[0] if exact else (ms[0] if ms else None)


def pick_audit_filing(filings: list[dict]) -> dict | None:
    """Latest standalone 감사보고서 (exclude 연결감사보고서)."""
    standalone = [
        f for f in filings
        if f.get("report_nm", "").startswith("감사보고서")
        and "연결" not in f.get("report_nm", "")
    ]
    standalone.sort(key=lambda f: f.get("rcept_dt", ""), reverse=True)
    return standalone[0] if standalone else None


def run_one(client: OpenDARTClient, name: str, year: int) -> dict:
    chosen = pick_corp(client, name)
    if not chosen:
        return {"kics_name": name, "status": "no_corp_match"}
    corp_code, canonical = chosen["corp_code"], chosen["corp_name"]

    filings = client.list_filings(
        corp_code, f"{year}0101", f"{year + 1}1231", pblntf_ty="F"
    )
    target = pick_audit_filing(filings)
    if not target:
        return {"kics_name": name, "canonical": canonical,
                "corp_code": corp_code, "status": "no_audit_report"}
    rcept_no = target["rcept_no"]

    out_dir = annual_raw_dir(
        canonical_name=canonical,
        rcept_no=rcept_no,
        kics_name=name,
        corp_code=corp_code,
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / "document.zip"
    if not zip_path.is_file():
        try:
            client.fetch_document_xml(rcept_no, zip_path)
        except OpenDARTError as exc:
            return {"kics_name": name, "canonical": canonical,
                    "corp_code": corp_code, "rcept_no": rcept_no,
                    "status": f"download_error: {exc}"}
    try:
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(out_dir)
    except zipfile.BadZipFile as exc:
        return {"kics_name": name, "canonical": canonical,
                "corp_code": corp_code, "rcept_no": rcept_no,
                "status": f"bad_zip: {exc}"}

    xmls = sorted(out_dir.glob("*.xml"))

    # Tier A2 — CSM amort schedule (csm_extractor; no company_name arg).
    full: list[dict] = []
    parse_errors: list[dict] = []
    for xml in xmls:
        try:
            tables = extract_csm_tables(xml)
        except Exception as exc:  # noqa: BLE001
            parse_errors.append({"xml": xml.name, "error": str(exc)})
            continue
        for t in tables:
            d = to_jsonable(t)
            d["_source_xml"] = xml.name
            full.append(d)

    out_json = settings.extracted_dir / f"{canonical}_{rcept_no}_csm.json"
    out_json.write_text(json.dumps(full, ensure_ascii=False, indent=2),
                        encoding="utf-8")

    # Tiers A1 / A3 / B5 — measurement, insurance P&L, sensitivity. Same
    # artifact naming the per-tier batch scripts use so the viz builders
    # (waterfall globs *_measurement.json, panels glob *_<tier>_mvp.json)
    # pick these up with no further wiring.
    tier_counts: dict[str, int] = {}
    for suffix, extract_fn, jsonable in TIER_EXTRACTORS:
        all_tables: list[dict] = []
        mvp_tables: list[dict] = []
        for xml in xmls:
            try:
                tables = extract_fn(xml, company_name=name)
            except Exception as exc:  # noqa: BLE001
                parse_errors.append(
                    {"xml": xml.name, "tier": suffix, "error": str(exc)}
                )
                continue
            for t in tables:
                obj = jsonable(t)
                obj["_source_xml"] = xml.name
                all_tables.append(obj)
                if getattr(t, "mvp_candidate", False):
                    mvp_tables.append(obj)
        (settings.extracted_dir / f"{canonical}_{rcept_no}_{suffix}.json").write_text(
            json.dumps(all_tables, ensure_ascii=False, indent=2), encoding="utf-8")
        (settings.extracted_dir / f"{canonical}_{rcept_no}_{suffix}_mvp.json").write_text(
            json.dumps(mvp_tables, ensure_ascii=False, indent=2), encoding="utf-8")
        tier_counts[suffix] = len(all_tables)
        tier_counts[f"{suffix}_mvp"] = len(mvp_tables)

    return {
        "kics_name": name, "canonical": canonical, "corp_code": corp_code,
        "rcept_no": rcept_no, "report_nm": target.get("report_nm"),
        "rcept_dt": target.get("rcept_dt"),
        "status": "ok" if full else "no_csm_table_found",
        "csm_tables_found": len(full),
        "tier_counts": tier_counts,
        "parse_errors": parse_errors,
        "json_out": str(out_json.relative_to(REPO)),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="F11 audit-report annual CSM ingest")
    ap.add_argument("--year", type=int, default=2024,
                    help="fiscal year (audit report filed the next year)")
    args = ap.parse_args()

    settings.ensure_dirs()
    client = OpenDARTClient.from_settings()
    names = sorted(AUDIT_REPORT_ANNUAL)
    print(f"[audit-annual] {len(names)} insurers, FY{args.year}")

    summary = []
    for i, name in enumerate(names, 1):
        print(f"\n[{i}/{len(names)}] === {name} ===")
        r = run_one(client, name, args.year)
        tc = r.get("tier_counts") or {}
        print(f"  {r.get('canonical')} {r.get('status')} "
              f"csm={r.get('csm_tables_found', '-')} "
              f"meas={tc.get('measurement', '-')} "
              f"pl_mvp={tc.get('insurance_pl_mvp', '-')} "
              f"sens_mvp={tc.get('sensitivity_mvp', '-')}")
        summary.append(r)

    out = settings.extracted_dir / "_audit_annual_summary.json"
    out.write_text(json.dumps({"fy": args.year, "results": summary},
                              ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in summary if r.get("status") == "ok")
    print(f"\n[summary] ok={ok}/{len(summary)}  wrote {out.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
