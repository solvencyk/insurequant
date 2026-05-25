# -*- coding: utf-8 -*-
"""Batch B5 sensitivity rollforward on cached annual filings (23 operational insurers)."""

from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings
from src.ifrs17.sensitivity_extractor import extract_sensitivity_tables, to_jsonable
from src.ifrs17.universe import is_excluded

SUMMARY_IN = settings.extracted_dir / "_batch_all_summary.json"
SUMMARY_OUT = settings.extracted_dir / "_batch_sensitivity_summary.json"


def main():
    settings.ensure_dirs()
    if not SUMMARY_IN.is_file():
        raise SystemExit(f"missing {SUMMARY_IN} — run ifrs17_batch_all.py first")

    csm_summary = json.loads(SUMMARY_IN.read_text(encoding="utf-8"))
    targets = [r for r in csm_summary if r.get("status") == "ok" and not is_excluded(r.get("kics_name", ""))]
    print(f"[start] {len(targets)} operational insurers with cached CSM filings")

    summary = []
    for i, row in enumerate(targets, 1):
        kics = row["kics_name"]
        canonical = row["canonical"]
        rcept_no = row["rcept_no"]
        raw_dir = settings.raw_dir / f"{canonical}_{rcept_no}"
        print(f"\n[{i}/{len(targets)}] {kics} -> {raw_dir.name}")
        if not raw_dir.is_dir():
            summary.append({"kics_name": kics, "status": "no_raw_cache", "dir": str(raw_dir)})
            continue
        all_tables = []
        mvp_tables = []
        parse_errors = []
        for xml in sorted(raw_dir.glob("*.xml")):
            try:
                tables = extract_sensitivity_tables(xml, company_name=kics)
            except Exception as exc:
                parse_errors.append({"xml": xml.name, "error": str(exc)})
                continue
            for t in tables:
                obj = to_jsonable(t)
                obj["_source_xml"] = xml.name
                all_tables.append(obj)
                if t.mvp_candidate:
                    mvp_tables.append(obj)
        out_json = settings.extracted_dir / f"{canonical}_{rcept_no}_sensitivity.json"
        out_json.write_text(json.dumps(all_tables, ensure_ascii=False, indent=2), encoding="utf-8")
        mvp_json = settings.extracted_dir / f"{canonical}_{rcept_no}_sensitivity_mvp.json"
        mvp_json.write_text(json.dumps(mvp_tables, ensure_ascii=False, indent=2), encoding="utf-8")
        rec = {
            "kics_name": kics,
            "canonical": canonical,
            "rcept_no": rcept_no,
            "status": "ok" if all_tables else "no_table",
            "tables_total": len(all_tables),
            "tables_mvp": len(mvp_tables),
            "by_block": _count(all_tables, "block_type"),
            "by_slice": _count(all_tables, "slice_label"),
            "parse_errors": parse_errors,
            "json_out": str(out_json),
            "mvp_out": str(mvp_json),
        }
        summary.append(rec)
        print(json.dumps({k: rec[k] for k in ("status", "tables_total", "tables_mvp", "by_slice")}, ensure_ascii=False))

    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in summary if r.get("status") == "ok")
    mvp_ok = sum(1 for r in summary if r.get("tables_mvp", 0) > 0)
    print(f"\n[summary] total={len(summary)} ok={ok} with_mvp={mvp_ok}")
    print(f"[wrote] {SUMMARY_OUT}")


def _count(rows, key):
    out = {}
    for r in rows:
        k = r.get(key, "unknown")
        out[k] = out.get(k, 0) + 1
    return out


if __name__ == "__main__":
    main()
