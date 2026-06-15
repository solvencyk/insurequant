# -*- coding: utf-8 -*-
"""Extract CSM sensitivity from the restored FY2025 annual/audit raw (owner
20260615T0435Z) into data/dart/extracted/<canonical>_<rcept>_sensitivity.json.

Source = data/dart/FY2025_Q4/raw/KR####_<canonical>_<rcept>/*.xml. Companies with
two filings (audit 별도/연결, e.g. 라이나/AIA/메트라이프/하나생명/AIG) are merged into
ONE extracted file per company (all XMLs across its dirs), keyed by the max rcept,
so the panel sees one FY2025 entry per company. The panel then dedups FY2024-vs-FY2025
by latest rcept. Read raw only; does NOT rebuild any master.
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

from src.ifrs17.sensitivity_extractor import extract_sensitivity_tables, to_jsonable  # noqa: E402

RAW_ROOT = ROOT / "data" / "dart" / "FY2025_Q4" / "raw"
EXTRACTED = ROOT / "data" / "dart" / "extracted"
DIR_RE = re.compile(r"^KR\d+_(.+)_(\d{14})$")


def main() -> None:
    by_company: dict[str, list[Path]] = defaultdict(list)
    for d in sorted(RAW_ROOT.iterdir()):
        if not d.is_dir():
            continue
        m = DIR_RE.match(d.name)
        if not m:
            print(f"  skip (name): {d.name}")
            continue
        by_company[m.group(1)].append(d)

    summary = []
    for canonical, dirs in sorted(by_company.items()):
        rcepts = [DIR_RE.match(d.name).group(2) for d in dirs]
        rcept = max(rcepts)  # keyed by the latest rcept
        xmls = sorted(x for d in dirs for x in d.glob("*.xml"))
        all_tables, errs = [], []
        for xml in xmls:
            try:
                for t in extract_sensitivity_tables(xml, company_name=canonical):
                    o = to_jsonable(t)
                    o["_source_xml"] = xml.name
                    all_tables.append(o)
            except Exception as exc:  # noqa: BLE001
                errs.append({"xml": xml.name, "error": str(exc)})
        n_sa = sum(1 for t in all_tables if str(t.get("table_kind")) == "sensitivity_analysis")
        out = EXTRACTED / f"{canonical}_{rcept}_sensitivity.json"
        out.write_text(json.dumps(all_tables, ensure_ascii=False, indent=2), encoding="utf-8")
        rec = {"company": canonical, "rcept": rcept, "dirs": len(dirs),
               "xmls": len(xmls), "tables": len(all_tables), "sensitivity_analysis": n_sa,
               "errors": errs, "out": out.name}
        summary.append(rec)
        print(f"  {canonical:22s} rcept={rcept} dirs={len(dirs)} xml={len(xmls)} "
              f"tables={len(all_tables)} SA={n_sa}{' ERR' if errs else ''}")

    (EXTRACTED / "_batch_sensitivity_fy2025_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[done] {len(summary)} companies; SA-bearing="
          f"{sum(1 for r in summary if r['sensitivity_analysis'] > 0)}")


if __name__ == "__main__":
    main()
