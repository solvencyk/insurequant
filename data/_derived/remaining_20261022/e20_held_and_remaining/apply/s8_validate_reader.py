#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 8: validate the generic statement reader (e20_read.py) -> s8_validate_reader.txt
For each (company, quarter, original FY, later FY): read the ORIGINAL filing's current cumulative vector and the LATER filing's prior cumulative vector,
compare both with the live PL_breakdown.json master (all items 1,16..32) and with the census FS-API prior (d5_buckets.json).
Regression buckets (already adopted in round 18): later == master expected for every item."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e20_read as R  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = R.X.ROOT
ITEMS = [1, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]
PAIRS = [
    # new buckets
    ("KR0087", "2024.4Q", "FY2024_Q4", "FY2025_Q4"), ("KR0087", "2025.1Q", "FY2025_Q1", "FY2026_Q1"), ("KR0087", "2025.2Q", "FY2025_Q2", "FY2026_Q2"),
    ("KR0104", "2024.4Q", "FY2024_Q4", "FY2025_Q4"), ("KR0104", "2025.1Q", "FY2025_Q1", "FY2026_Q1"), ("KR0104", "2025.2Q", "FY2025_Q2", "FY2026_Q2"),
    ("KR0069", "2025.1Q", "FY2025_Q1", "FY2026_Q1"), ("KR0069", "2025.2Q", "FY2025_Q2", "FY2026_Q2"),
    ("KR0094", "2025.2Q", "FY2025_Q2", "FY2026_Q2"),
    ("KR0070", "2025.1Q", "FY2025_Q1", "FY2026_Q1"), ("KR0070", "2025.2Q", "FY2025_Q2", "FY2026_Q2"),
    ("KR0072", "2024.4Q", "FY2024_Q4", "FY2025_Q4"),
    ("KR0068", "2024.4Q", "FY2024_Q4", "FY2025_Q4"), ("KR0068", "2025.1Q", "FY2025_Q1", "FY2026_Q1"), ("KR0068", "2025.2Q", "FY2025_Q2", "FY2026_Q2"),
    ("KR0071", "2025.1Q", "FY2025_Q1", "FY2026_Q1"), ("KR0071", "2025.2Q", "FY2025_Q2", "FY2026_Q2"),
    ("KR0083", "2024.3Q", "FY2024_Q3", "FY2025_Q3"),
    # regression buckets (round 18, master == later expected)
    ("KR0087", "2024.1Q", "FY2024_Q1", "FY2025_Q1"), ("KR0087", "2024.2Q", "FY2024_Q2", "FY2025_Q2"), ("KR0087", "2024.3Q", "FY2024_Q3", "FY2025_Q3"),
    ("KR0083", "2024.1Q", "FY2024_Q1", "FY2025_Q1"), ("KR0083", "2024.2Q", "FY2024_Q2", "FY2025_Q2"),
    ("KR0104", "2023.3Q", "FY2023_Q3", "FY2024_Q3"),
    ("KR0070", "2024.1Q", "FY2024_Q1", "FY2025_Q1"), ("KR0070", "2024.2Q", "FY2024_Q2", "FY2025_Q2"), ("KR0070", "2024.3Q", "FY2024_Q3", "FY2025_Q3"),
    ("KR0082", "2023.3Q", "FY2023_Q3", "FY2024_Q3"),
]
live = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in live}
d5 = {(b["code"], b["q"]): b for b in json.loads((ROOT / "data/_derived/remaining_20261022/d_census/d5_buckets.json").read_text(encoding="utf-8"))}
L = []
res = {}
for code, q, ofy, lfy in PAIRS:
    L.append(f"===== {code} {q}  orig {ofy}  later {lfy}")
    try:
        so, sl = R.Stmt(code, ofy), R.Stmt(code, lfy)
        vo = R.read_vector(so, "cur", "cum")
        vl = R.read_vector(sl, "prior", "cum")
    except Exception as e:  # noqa: BLE001
        L.append(f"   READER ERROR: {type(e).__name__}: {e}")
        continue
    L.append(f"   orig: {so.rel} fmt={so.fmt} unit={so.unit} title L{so.title};  later: {sl.rel} fmt={sl.fmt} unit={sl.unit} title L{sl.title}")
    cen = d5.get((code, q), {}).get("its", {})
    n_me_eq_o = n_ml_eq = 0
    for it in ITEMS:
        m = M.get((code, it, q))
        o, l = vo[it]["val"], vl[it]["val"]
        fp = cen.get(str(it), {}).get("prior")
        tolo = 1.0 if so.unit == "백만원" else 2e-5
        toll = 1.0 if sl.unit == "백만원" else 2e-5
        flag = ""
        if m is not None:
            eo = abs(m - o) <= max(tolo, 1.01 if so.unit == "백만원" else 0)
            el = abs(m - l) <= max(toll, 1.01 if sl.unit == "백만원" else 0)
            flag = f"master==orig {'Y' if eo else 'N'}  master==later {'Y' if el else 'N'}"
        fsd = "" if fp is None else f"fsapi_prior_diff {l - fp:+.6f}"
        L.append(f"   i{it:>2} master={'-' if m is None else format(m, '.6f'):>20}  orig={o:>20.6f}  later={l:>20.6f}  d(later-master)={'-' if m is None else format(l - m, '+.6f'):>16}  {flag}  {fsd}")
    res[f"{code}|{q}"] = {str(it): dict(master=M.get((code, it, q)), orig=vo[it]["val"], later=vl[it]["val"]) for it in ITEMS}
    for nm, v in (("orig", vo), ("later", vl)):
        d = lambda a: v[a]["val"]  # noqa: E731
        ids = [("20-(1+17)", d(20) - d(1) - d(17)), ("22-(20+21)", d(22) - d(20) - d(21)), ("|22-24|-|23|", abs(d(22) - d(24)) - abs(d(23))), ("31-(24+25)", d(31) - d(24) - d(25)),
               ("25-leafsum", d(25) - v["_leaf_all_sum"]), ("17-(18+19)", d(17) - d(18) - d(19))]
        L.append(f"   identities {nm}: " + "; ".join(f"{k}={x:+.4f}" for k, x in ids))
(HERE / "s8_validate_reader.txt").write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
(HERE / "s8_validate_reader.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(len(L))
