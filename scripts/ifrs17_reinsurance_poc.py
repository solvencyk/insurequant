# -*- coding: utf-8 -*-
"""Skim 5 PoC companies annual filings for A4 reinsurance rollforward."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings
from src.ifrs17.reinsurance_extractor import extract_reinsurance_tables, to_jsonable

POC_DIRS = [
    ("메리츠화재해상보험_20250331003145", "메리츠화재"),
    ("삼성화재해상보험_20250311001055", "삼성화재"),
    ("DB손해보험_20250313001342", "DB손해보험"),
    ("한화생명_20250312000939", "한화생명"),
    ("삼성생명_20250312001063", "삼성생명"),
]


def _count_attr(tables, attr):
    out = {}
    for t in tables:
        k = getattr(t, attr)
        out[k] = out.get(k, 0) + 1
    return out


def _count_attr_objs(tables, attr):
    out = {}
    for t in tables:
        k = t.get(attr, "unknown")
        out[k] = out.get(k, 0) + 1
    return out


def main():
    settings.ensure_dirs()
    summary = []
    for dirname, company_name in POC_DIRS:
        d = settings.raw_dir / dirname
        if not d.is_dir():
            print(f"[skip] {dirname} not on disk")
            continue
        all_tables = []
        per_xml = []
        for xml in sorted(d.glob("*.xml")):
            tables = extract_reinsurance_tables(xml, company_name=company_name)
            per_xml.append({
                "xml": xml.name,
                "tables": len(tables),
                "by_block": _count_attr(tables, "block_type"),
                "by_slice": _count_attr(tables, "slice_label"),
            })
            for t in tables:
                obj = to_jsonable(t)
                obj["_source_xml"] = xml.name
                all_tables.append(obj)
        out = settings.extracted_dir / f"{dirname}_reinsurance.json"
        out.write_text(json.dumps(all_tables, ensure_ascii=False, indent=2), encoding="utf-8")
        summary.append({
            "dir": dirname,
            "company_name": company_name,
            "tables": len(all_tables),
            "by_block": _count_attr_objs(all_tables, "block_type"),
            "by_slice": _count_attr_objs(all_tables, "slice_label"),
            "by_xml": per_xml,
            "out": str(out),
        })
        print(f"\n=== {company_name} ({dirname}) ===")
        print(f"  total tables: {len(all_tables)}")
        for x in per_xml:
            if x["tables"]:
                print(f"   - {x['xml']:50s}  {x['tables']:3}  block={x['by_block']} slice={x['by_slice']}")
        if all_tables:
            top = all_tables[0]
            print(f"  top: score={top['score']} block={top['block_type']} slice={top['slice_label']}")
            print(f"       caption: {top['caption'][:80]}...")
        print(f"  written: {out}")

    out_summary = settings.extracted_dir / "_reinsurance_poc_summary.json"
    out_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[wrote] {out_summary}")


if __name__ == "__main__":
    main()