#!/usr/bin/env python3
"""Consolidate per-company IR series.json (data/ir/series/*.json) into one
normalized IR-disclosed NB-CSM-multiple reference: data/ir/disclosed_csm_multiple.json.

Companies use different schemas (삼성=multiple_wolcho, 메리츠/한화=multiple_total,
롯데=multiple_derived). Normalize each period to a single 'multiple' with a 'basis'
tag (disclosed vs derived). Re-runnable as agents add more series files.
"""
import json
import glob
import os
import re
from datetime import datetime, timezone
from pathlib import Path

SERIES_DIR = Path("data/ir/series")
OUT = Path("data/ir/disclosed_csm_multiple.json")

# priority of keys that represent the whole-company disclosed multiple
DISCLOSED_KEYS = ["multiple_total", "multiple_wolcho", "multiple_disclosed", "multiple"]
DERIVED_KEYS = ["multiple_derived_ytd", "multiple_derived"]


def pick_multiple(rec: dict):
    for k in DISCLOSED_KEYS:
        v = rec.get(k)
        if isinstance(v, (int, float)):
            return float(v), ("disclosed:" + k)
    for k in DERIVED_KEYS:
        v = rec.get(k)
        if isinstance(v, (int, float)):
            return float(v), ("derived:" + k)
    return None, None


def main():
    out_companies = []
    for f in sorted(glob.glob(str(SERIES_DIR / "*.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        kr_raw = d.get("kr") or d.get("kr_code") or d.get("kr_dir") or os.path.basename(f)
        m = re.match(r"(KR\d+)", str(kr_raw))
        kr = m.group(1) if m else str(kr_raw)
        ser_in = d.get("series") or {}
        ser_out = {}
        n_disc = n_der = 0
        for per, rec in ser_in.items():
            if not isinstance(rec, dict):
                continue
            mult, basis = pick_multiple(rec)
            row = {
                "multiple": mult,
                "basis": basis,
                "nb_csm_eok": rec.get("nb_csm_eok"),
                "source": rec.get("source_file") or (rec.get("source_files") or [None])[0],
            }
            # passthrough secondary views when present (e.g. Samsung Fire discloses single-Q
            # 배수 but we also keep a YTD-derived value comparable to the KIDI-computed series)
            for extra in ("multiple_derived_ytd", "multiple_disclosed", "premium_eok"):
                if isinstance(rec.get(extra), (int, float)) and rec.get(extra) != mult:
                    row[extra] = rec[extra]
            if rec.get("multiple_by_product"):
                row["by_product"] = rec["multiple_by_product"]
            ser_out[per] = row
            if basis and basis.startswith("disclosed"):
                n_disc += 1
            elif basis and basis.startswith("derived"):
                n_der += 1
        out_companies.append({
            "kr": kr,
            "company": d.get("company"),
            "sector": d.get("sector"),
            "n_disclosed": n_disc,
            "n_derived": n_der,
            "n_periods": len(ser_out),
            "series": dict(sorted(ser_out.items(),
                                  key=lambda kv: (kv[0][:4], kv[0][5:]) if re.match(r"\d{4}\.\dQ", kv[0]) else (kv[0], ""))),
        })
    out_companies.sort(key=lambda c: c["kr"])
    payload = {
        "_meta": {
            "purpose": "IR-disclosed NB CSM multiple per company/quarter (normalized).",
            "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "build_script": "scripts/build_ir_disclosed_multiples.py",
            "company_count": len(out_companies),
        },
        "companies": out_companies,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}  ({len(out_companies)} companies)")
    for c in out_companies:
        tag = f"disclosed {c['n_disclosed']}q" if c['n_disclosed'] else (
            f"derived {c['n_derived']}q" if c['n_derived'] else "no multiple")
        # show FY2024 + FY2025 annual-ish points if present
        pts = {p: r["multiple"] for p, r in c["series"].items() if r["multiple"] is not None}
        print(f"  {c['kr']:8} {str(c['company']):16} [{tag}]  e.g. " +
              " ".join(f"{p}:{v}" for p, v in list(pts.items())[-4:]))


if __name__ == "__main__":
    main()
