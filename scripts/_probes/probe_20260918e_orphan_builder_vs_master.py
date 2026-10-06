# -*- coding: utf-8 -*-
"""Compare, for the 29 orphan buckets, three views:
  A) data/dart/viz/pl_breakdown_master.json  (the BUILDER's own last output)
  B) PL_breakdown.json                       (the merged root master, what validation measured)
  C) a fresh assemble() from today's parse   (what a rebuild would produce)

Read-only. Writes one diagnostic JSON into data/_derived/.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import build_pl_breakdown as B  # noqa: E402

BUCKETS = [
    ("KR0002", "2023.1Q"), ("KR0002", "2023.2Q"),
    ("KR0003", "2023.2Q"), ("KR0003", "2023.3Q"),
    ("KR0004", "2023.4Q"), ("KR0004", "2024.4Q"), ("KR0004", "2025.4Q"),
    ("KR0005", "2023.2Q"),
    ("KR0029", "2023.4Q"), ("KR0029", "2024.4Q"), ("KR0029", "2025.4Q"),
    ("KR0068", "2023.1Q"), ("KR0068", "2023.2Q"),
    ("KR0069", "2023.1Q"), ("KR0069", "2023.2Q"),
    ("KR0071", "2023.1Q"), ("KR0071", "2023.2Q"),
    ("KR0073", "2023.1Q"), ("KR0073", "2023.2Q"),
    ("KR0074", "2023.4Q"),
    ("KR0075", "2023.4Q"),
    ("KR0083", "2023.1Q"), ("KR0083", "2023.2Q"),
    ("KR0094", "2023.1Q"), ("KR0094", "2023.2Q"),
    ("KR0095", "2023.4Q"),
    ("KR0097", "2023.4Q"),
    ("KR0104", "2023.1Q"), ("KR0104", "2023.2Q"),
]


def load_cells(path):
    with open(path, encoding="utf-8") as fh:
        rows = json.load(fh)
    out = {}
    for r in rows:
        out.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]
    return out


A = load_cells(ROOT / "data" / "dart" / "viz" / "pl_breakdown_master.json")
Bm = load_cells(ROOT / "PL_breakdown.json")

uni = B.load_universe()
filings = B.discover_filings()

report = {}
for code, q in BUCKETS:
    name, life_flag = uni.get(code, (code, None))
    is_life = (life_flag == "생명보험")
    dirs = filings.get(code, {}).get(q)
    fresh = {}
    recon = None
    if dirs:
        t1_html, t2 = B.parse_filing(dirs, is_life, code=code, name=name, quarter=q)
        t1_api = B._fs_tier1(name, q, code)
        t1 = t1_api if t1_api else t1_html
        if t1 is not None or t2 is not None:
            v = B.assemble(t1, t2, is_life, zero_fill_ok=None)
            recon = v.get("_reconciled")
            fresh = {n: v[n] for n in range(1, 25)}
    a = A.get((code, q), {})
    b = Bm.get((code, q), {})
    print(f"=== {code} {name} {q}   _reconciled={recon} ===")
    hdr = f"{'item':>5} {'builder(A)':>14} {'master(B)':>14} {'fresh(C)':>14}"
    print(hdr)
    for n in list(range(1, 15)):
        va, vb, vc = a.get(n), b.get(n), fresh.get(n)
        def f(x):
            return "None" if x is None else f"{x:,.1f}"
        mark = ""
        if vb is not None and va is None:
            mark = "  <-- master-only (merge resurrection)"
        if vc is not None and vb is None:
            mark += "  <== FRESH HAS VALUE, master null"
        print(f"{n:>5} {f(va):>14} {f(vb):>14} {f(vc):>14}{mark}")
    print()
    report[f"{code}|{q}"] = {
        "reconciled": recon,
        "builder": {str(k): v for k, v in a.items() if k <= 14},
        "master": {str(k): v for k, v in b.items() if k <= 14},
        "fresh": {str(k): v for k, v in fresh.items() if k <= 14},
    }

dest = ROOT / "data" / "_derived" / "_probe_20260918_orphan_builder_vs_master.json"
dest.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print("written:", dest)
