"""PL_breakdown coverage census: expected (company x quarter) grid vs master vs DART raw.

Classifies every expected cell as:
  a_in_master  - company/quarter present in PL_breakdown.json
  b_raw_no_pl  - DART raw filing exists on disk but no PL rows in master (parser gap)
  c_no_source  - no raw filing on disk (issuer did not file / downloader gap)

Run:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
      scripts/_probes/probe_20260901_pl_coverage_census.py
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
MASTER = ROOT / "PL_breakdown.json"
DART = ROOT / "data" / "dart"
OUT = ROOT / "data" / "_derived" / "pl_coverage_census_20260901.json"

QUARTERS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)]
QUARTERS = [q for q in QUARTERS if "2023.1Q" <= q <= "2026.2Q"]


def load_master():
    recs = json.loads(MASTER.read_text(encoding="utf-8"))
    cells = collections.defaultdict(int)
    names, kinds = {}, {}
    for r in recs:
        code = r["원보험사코드"]
        names[code] = r["원수사명"]
        kinds[code] = r.get("생손보여부")
        cells[(code, r["공시분기"])] += 1
    return recs, cells, names, kinds


def scan_raw():
    """Return {(code, quarter): [info, ...]} for every raw company dir on disk.

    NOTE: meta.json is OPTIONAL. Annual (사업보고서) dirs are named
    ``KR####_<name>_<rcept>`` and carry no meta.json at all — an earlier version of
    this probe globbed ``*/meta.json`` and therefore misclassified real raw filings
    (e.g. AIA FY2023_Q4 / FY2024_Q4) as "no source". Glob the dirs, not the metas.
    """
    raw = collections.defaultdict(list)
    for comp_dir in DART.glob("FY*/raw/*"):
        if not comp_dir.is_dir():
            continue
        code = comp_dir.name.split("_")[0]
        meta = {}
        mp = comp_dir / "meta.json"
        if mp.exists():
            try:
                meta = json.loads(mp.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                meta = {"_error": str(exc)}
        period = meta.get("period")
        if not period:
            # fall back to the FY dir name: FY2025_Q2 -> 2025.2Q
            fy = comp_dir.parent.parent.name
            year, q = fy.replace("FY", "").split("_Q")
            period = f"{year}.{q}Q"
        xmls = sorted(p.name for p in comp_dir.rglob("*.xml"))
        rcept = meta.get("rcept_no")
        if not rcept:
            tail = comp_dir.name.rsplit("_", 1)[-1]
            if tail.isdigit() and len(tail) == 14:
                rcept = tail
        raw[(code, period)].append(
            {
                "dir": str(comp_dir.relative_to(ROOT)).replace("\\", "/"),
                "no_filing": bool(meta.get("no_filing")),
                "report_kind": meta.get("report_kind"),
                "rcept_no": rcept,
                "has_meta": mp.exists(),
                "n_xml": len(xmls),
                "has_zip": (comp_dir / "document.zip").exists(),
            }
        )
    return raw


def main():
    recs, cells, names, kinds = load_master()
    raw = scan_raw()

    # company universe = master companies + any company that has raw on disk
    codes = set(names) | {c for c, _ in raw}
    for code, _q in raw:
        names.setdefault(code, "?")

    grid = {}
    per_company = {}
    tally = collections.Counter()
    for code in sorted(codes):
        row = {}
        for q in QUARTERS:
            rs = raw.get((code, q)) or []
            # a dir counts as real source only if it actually holds a document
            live = [r for r in rs if not r["no_filing"] and (r["n_xml"] > 0 or r["has_zip"])]
            r = live[0] if live else (rs[0] if rs else None)
            if (code, q) in cells:
                verdict = "a_in_master"
            elif live:
                verdict = "b_raw_no_pl"
            elif not rs:
                verdict = "c_no_source_nodir"
            elif any(x["no_filing"] for x in rs):
                verdict = "c_no_source_nofiling"
            else:
                verdict = "c_no_source_emptydir"
            row[q] = {
                "verdict": verdict,
                "n_rows": cells.get((code, q), 0),
                "raw": r,
                "raw_all": rs,
            }
            tally[verdict] += 1
        grid[code] = row
        per_company[code] = {
            "name": names[code],
            "kind": kinds.get(code),
            "n_quarters_in_master": sum(1 for q in QUARTERS if row[q]["verdict"] == "a_in_master"),
            "n_b_raw_no_pl": sum(1 for q in QUARTERS if row[q]["verdict"] == "b_raw_no_pl"),
            "b_quarters": [q for q in QUARTERS if row[q]["verdict"] == "b_raw_no_pl"],
            "min_quarter": min([q for q in QUARTERS if row[q]["verdict"] == "a_in_master"], default=None),
        }

    print(f"master records={len(recs)} companies={len(names)} quarters={len(QUARTERS)}")
    print(f"expected grid = {len(codes)} x {len(QUARTERS)} = {len(codes)*len(QUARTERS)} cells")
    for k in sorted(tally):
        print(f"  {k:24s} {tally[k]:5d}")
    print()
    print(f"{'code':7s} {'name':22s} {'kind':6s} {'inMst':>5s} {'B':>3s}  min_q     b_quarters")
    for code in sorted(codes, key=lambda c: (per_company[c]["n_quarters_in_master"], c)):
        pc = per_company[code]
        if pc["n_quarters_in_master"] == len(QUARTERS) and pc["n_b_raw_no_pl"] == 0:
            continue
        print(
            f"{code:7s} {pc['name'][:22]:22s} {str(pc['kind'])[:6]:6s} "
            f"{pc['n_quarters_in_master']:5d} {pc['n_b_raw_no_pl']:3d}  "
            f"{str(pc['min_quarter']):9s} {','.join(pc['b_quarters'])}"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generated": "20260901",
                "quarters": QUARTERS,
                "tally": dict(tally),
                "per_company": per_company,
                "grid": grid,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nwrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
