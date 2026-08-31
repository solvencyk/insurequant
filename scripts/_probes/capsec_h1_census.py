# -*- coding: utf-8 -*-
"""Census: for each of the 39 K-ICS companies, does a FY2026_Q2 (반기보고서) raw filing
exist, and per FY2025 baseline did that company have capital securities at all?
Diagnostic only — writes a report to stdout (utf-8) and a JSON summary to scratch.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]

fy25 = json.loads((ROOT / "data" / "bonds" / "capital_securities_fy2025.json").read_text(encoding="utf-8"))
fy25_by_code = {c["code"]: c for c in fy25["companies"]}

raw_dir = ROOT / "data" / "dart" / "FY2026_Q2" / "raw"
company_dirs = {}
for d in sorted(raw_dir.iterdir()):
    if not d.is_dir():
        continue
    code = d.name.split("_", 1)[0]
    company_dirs[code] = d

all_codes = sorted(set(fy25_by_code) | set(company_dirs))
rows = []
for code in all_codes:
    fy = fy25_by_code.get(code)
    d = company_dirs.get(code)
    if d is None:
        filing_status = "NO_DIR"
        xml_files = []
    else:
        meta_p = d / "meta.json"
        meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
        xml_files = sorted(p.name for p in d.glob("*.xml"))
        if meta.get("no_filing"):
            filing_status = "NO_FILING"
        elif xml_files:
            filing_status = "FILED:" + meta.get("report_kind", "?")
        else:
            filing_status = "DIR_NO_XML"
    rows.append({
        "code": code,
        "company": (fy or {}).get("company", (d.name.split("_", 1)[1] if d else "?")),
        "fy25_has_capsec": (fy or {}).get("has_capital_securities"),
        "fy25_n_bonds": len((fy or {}).get("bonds", [])) if fy else None,
        "h1_filing_status": filing_status,
        "h1_xml_files": xml_files,
    })

for r in rows:
    print(f"{r['code']:7} {str(r['company'])[:16]:17} fy25_capsec={str(r['fy25_has_capsec']):5} "
          f"fy25_bonds={str(r['fy25_n_bonds']):4} h1={r['h1_filing_status']}")

n_filed = sum(1 for r in rows if r["h1_filing_status"].startswith("FILED"))
n_nofiling = sum(1 for r in rows if r["h1_filing_status"] == "NO_FILING")
n_nodir = sum(1 for r in rows if r["h1_filing_status"] == "NO_DIR")
n_filed_and_capsec = sum(1 for r in rows if r["h1_filing_status"].startswith("FILED") and r["fy25_has_capsec"])
print(f"\ntotal={len(rows)} filed={n_filed} no_filing={n_nofiling} no_dir={n_nodir}")
print(f"filed AND fy25_has_capsec=True -> real extraction targets: {n_filed_and_capsec}")
print("\n[targets]")
for r in rows:
    if r["h1_filing_status"].startswith("FILED") and r["fy25_has_capsec"]:
        print(f"  {r['code']} {r['company']}")

out = ROOT / "data" / "_derived" / "_probe_capsec_h1_census.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n[wrote] {out.relative_to(ROOT)}")
