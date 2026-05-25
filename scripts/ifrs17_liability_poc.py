# -*- coding: utf-8 -*-
"""Skim 5 PoC companies' annual filings for the 보험계약부채 detail tables.

Per user decision (docs/claude-agent-ifrs17.md §10, Candidate C):
  raw structural capture only; no per-company YAML mapping.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.config import settings  # noqa: E402
from src.ifrs17.liability_extractor import (  # noqa: E402
    extract_liability_tables, to_jsonable,
)


POC_DIRS = [
    "메리츠화재해상보험_20250331003145",
    "삼성화재해상보험_20250311001055",
    "DB손해보험_20250313001342",
    "한화생명_20250312000939",
    "삼성생명_20250312001063",
]


def main():
    settings.ensure_dirs()
    summary = []
    for dirname in POC_DIRS:
        d = settings.raw_dir / dirname
        if not d.is_dir():
            print(f"[skip] {dirname} not on disk")
            continue
        all_tables = []
        per_xml = []
        for xml in sorted(d.glob("*.xml")):
            tables = extract_liability_tables(xml)
            per_xml.append({
                "xml": xml.name,
                "tables": len(tables),
                "by_kind": _by_kind(tables),
            })
            for t in tables:
                d_obj = to_jsonable(t)
                d_obj["_source_xml"] = xml.name
                all_tables.append(d_obj)
        out = settings.extracted_dir / f"{dirname}_liability.json"
        out.write_text(json.dumps(all_tables, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        summary.append({
            "dir": dirname,
            "tables": len(all_tables),
            "by_kind": _by_kind_objs(all_tables),
            "by_xml": per_xml,
            "out": str(out),
        })
        print(f"\n=== {dirname} ===")
        print(f"  total tables: {len(all_tables)}")
        for x in per_xml:
            print(f"   - {x['xml']:50s}  {x['tables']:3} tables  {x['by_kind']}")
        print(f"  written: {out}")

    out_summary = settings.extracted_dir / "_liability_poc_summary.json"
    out_summary.write_text(json.dumps(summary, ensure_ascii=False, indent=2),
                            encoding="utf-8")
    print(f"\n[wrote] {out_summary}")


def _by_kind(tables):
    out = {}
    for t in tables:
        out[t.kind] = out.get(t.kind, 0) + 1
    return out


def _by_kind_objs(tables):
    out = {}
    for t in tables:
        k = t.get("kind", "unknown")
        out[k] = out.get(k, 0) + 1
    return out


if __name__ == "__main__":
    main()
