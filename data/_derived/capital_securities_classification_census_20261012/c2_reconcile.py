"""c2_reconcile.py (parser-kics, ticket 20261012T1230Z) -- READ ONLY.

Step 2: does the per-bond inventory (c1) explain the K-ICS master's own capital-securities items in EVERY quarter 2023.1Q-2026.2Q?
  item 53 = (기발행 신종자본증권) of the issuer's 공통적용 경과조치 표   <- pre-2023 hybrids (legacy / TFI)
  item 54 = (기발행 후순위채무)   of the same table                      <- pre-2023 subordinated debt
  item 6  = 자본항목 중 보통주 이외의 자본증권 (BS 계상액, 한도 적용 전)  <- all hybrids (+ preferred shares ...)
Per (company, quarter): list-implied amount = sum of face (억원) of inventory securities of that kind issued on/before the cut-off and
NOT yet redeemed at the quarter end (redemption date = the call date when the list shows outstanding 0; unknown otherwise = assumed outstanding).
A gap with the master that the inventory cannot explain = a security missing from the inventory (e.g. redeemed before the 2025-12-31 snapshot)
or an issuer-side difference (장부금액 vs 액면, 외화 환산, 우선주 등).
Output: census_reconcile.csv / census_reconcile.txt in this directory.

Run (repo root): C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/c2_reconcile.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
inv = json.loads((HERE / "census_inventory.json").read_text(encoding="utf-8"))["rows"]
kd = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))

QUARTERS = [f"{y}.{n}Q" for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]
QEND = {f"{y}.{n}Q": f"{y}-{[3, 6, 9, 12][n - 1]:02d}-{[31, 30, 30, 31][n - 1]}" for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)}


def f(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


T: dict[tuple[str, str], dict[int, float]] = defaultdict(dict)
names = {}
for r in kd:
    if r["항목번호"] in (6, 13, 14, 49, 53, 54):
        v = f(r.get("값"))
        if v is not None:
            T[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = v
        names[r["원보험사코드"]] = r.get("원수사명")

by_code = defaultdict(list)
for r in inv:
    by_code[r["code"]].append(r)


def redeemed_by(r, qend):
    """True when the security is known/assumed redeemed on or before the quarter end."""
    if r["outstanding_eok"] == 0:
        # listed with 0 outstanding at the snapshot: redeemed at/after the call date (best available proxy)
        return bool(r["call_date"]) and r["call_date"] <= qend
    return False


def implied(code, tier, cutoff, q):
    qend = QEND[q]
    tot, parts = 0.0, []
    for r in by_code.get(code, []):
        if r["tier"] != tier or not r["issue_date"] or r["issue_date"] > cutoff or r["issue_date"] > qend:
            continue
        if redeemed_by(r, qend):
            continue
        amt = r["face_eok"] if r["face_eok"] is not None else (r["outstanding_eok"] or 0.0)
        tot += amt
        parts.append(f"{r['issue_date']}:{amt:g}")
    return round(tot, 2), parts


rows_out = []
codes = sorted({c for c, _ in T} | set(by_code))
lines = []
for code in codes:
    have_bonds = code in by_code
    i53s = [T.get((code, q), {}).get(53) for q in QUARTERS]
    i54s = [T.get((code, q), {}).get(54) for q in QUARTERS]
    i6s = [T.get((code, q), {}).get(6) for q in QUARTERS]
    if not have_bonds and not any((x or 0) > 0 for x in i53s + i54s + i6s):
        continue
    lines.append(f"== {code} {names.get(code)} | bonds in inventory: {len(by_code.get(code, []))}")
    for q in QUARTERS:
        v = T.get((code, q))
        if v is None:
            continue
        h_leg, hp = implied(code, "hybrid", "2022-12-31", q)
        s_leg, sp = implied(code, "subordinated", "2022-12-31", q)
        h_all, _ = implied(code, "hybrid", "9999-12-31", q)
        row = {"code": code, "company": names.get(code), "quarter": q, "item6": v.get(6), "item13": v.get(13), "item49": v.get(49),
               "item14": v.get(14), "item53": v.get(53), "item54": v.get(54), "list_hybrid_legacy": h_leg, "list_sub_legacy": s_leg,
               "list_hybrid_all": h_all,
               "gap53": None if v.get(53) is None else round(v.get(53) - h_leg, 2),
               "gap54": None if v.get(54) is None else round(v.get(54) - s_leg, 2),
               "gap6": None if v.get(6) is None else round(v.get(6) - h_all, 2)}
        rows_out.append(row)
        flag53 = "" if row["gap53"] is None or abs(row["gap53"]) <= max(5.0, 0.02 * max(h_leg, 1)) else "  <== 53 GAP"
        flag54 = "" if row["gap54"] is None or abs(row["gap54"]) <= max(5.0, 0.03 * max(s_leg, 1)) else "  <== 54 GAP"
        flag6 = "" if row["gap6"] is None or abs(row["gap6"]) <= max(5.0, 0.02 * max(h_all, 1)) else "  <== 6 GAP"
        lines.append(f"  {q}: i6={v.get(6)} (list {h_all}, gap {row['gap6']}){flag6} | i53={v.get(53)} (list-legacy {h_leg}, gap {row['gap53']}){flag53} | i54={v.get(54)} (list-legacy {s_leg}, gap {row['gap54']}){flag54}")

(HERE / "census_reconcile.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
with open(HERE / "census_reconcile.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows_out[0]))
    w.writeheader()
    w.writerows(rows_out)
print("\n".join(lines))
