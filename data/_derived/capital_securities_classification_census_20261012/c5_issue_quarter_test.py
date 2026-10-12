"""c5_issue_quarter_test.py (parser-kics, ticket 20261012T1230Z) -- READ ONLY.

Issuer-treatment test for every post-2022 hybrid (issue date >= 2023-01-01), using ONLY the issuer's own K-ICS tables in kics_disclosure.json:
  item 6  = 자본항목 중 보통주 이외의 자본증권 (BS amount)              -> must jump by about the face in the issue quarter (else the bond is not in item 6 / wrong quarter)
  item 47 = 보완자본 한도 적용 전 (공통적용 경과조치 표, 해약환급금 초과분 49 별도)  -> jumps by about the face when the bond is booked as 보완자본 (tier2-type)
  X       = item 13 - item 49  (보완자본으로 재분류하는 항목 중 해약환급금 초과분 외)  -> second, noisier view of the same thing
  cap10   = 0.10 x item 14 (총요구자본, 경과조치 적용 전)  -> a tier1-type bond only moves into 보완자본 by the part above this cap
For each bond:  d6, d47, dX  (issue quarter vs the quarter before),  and the two textbook predictions
  tier2-type  : d47 ~ +face (all of it is 보완자본)
  tier1-type  : d47 ~ + (excess over cap10 of the new-type hybrids issued so far)  (0 while the pool stays under the cap)
The verdict word is only a reading aid ("t2-like"/"t1-like"/"ambiguous"); the census grade decision is made in c7 (c9 is the quantified successor of this eyeball test).
Output: census_issue_quarter_test.csv / .txt (utf-8-sig csv).

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/c5_issue_quarter_test.py
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


def f(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


T = defaultdict(dict)
for r in kd:
    if r["항목번호"] in (6, 13, 14, 47, 49):
        v = f(r.get("값"))
        if v is not None:
            T[(r["원보험사코드"], r["공시분기"])][r["항목번호"]] = v


def qkey(q):
    y, p = q.split(".")
    return int(y), int(p[0])


def prev_q(q):
    y, n = qkey(q)
    return f"{y - 1}.4Q" if n == 1 else f"{y}.{n - 1}Q"


def q_of(date):
    y, m, _ = date.split("-")
    return f"{y}.{(int(m) - 1) // 3 + 1}Q"


def n0(x):
    return "NA" if x is None else str(round(x))


def x_of(v):
    return None if v is None or v.get(13) is None or v.get(49) is None else v[13] - v[49]


rows = []
# the post-2022 hybrids of the inventory + the one the registry knows but the bond file lacks (Hana non-life 2026.2Q, +999)
bonds = [(r["code"], r["issue_date"], r["face_eok"], r["name"][:34]) for r in inv if r["tier"] == "hybrid" and (r["issue_date"] or "") >= "2023-01-01"]
bonds.append(("KR0050", "2026-06-30", 999.0, "(registry only) 2026.2Q new hybrid, not in bond file"))
bonds.sort()
pool_by_code_q = defaultdict(float)
out_lines = []
for code, d, face, name in bonds:
    q = q_of(d)
    p = prev_q(q)
    v1, v0 = T.get((code, q), {}), T.get((code, p), {})
    d6 = None if v1.get(6) is None or v0.get(6) is None else v1[6] - v0[6]
    d47 = None if v1.get(47) is None or v0.get(47) is None else v1[47] - v0[47]
    x1, x0 = x_of(v1), x_of(v0)
    dx = None if x1 is None or x0 is None else x1 - x0
    cap = None if v1.get(14) is None else 0.10 * v1[14]
    # pool of new-type hybrids of this company issued up to and including this bond (face), vs cap
    pool = sum(fc for c, dd, fc, _ in bonds if c == code and dd <= d)
    excess_now = None if cap is None else max(0.0, pool - cap)
    prev_pool = pool - face
    cap0 = None if v0.get(14) is None else 0.10 * v0[14]
    excess_prev = None if cap0 is None else max(0.0, prev_pool - cap0)
    pred_t1 = None if excess_now is None or excess_prev is None else excess_now - excess_prev
    verdict = "n/a"
    if d47 is not None and face:
        near_t2 = abs(d47 - face) <= 0.25 * face
        near_t1 = pred_t1 is not None and abs(d47 - pred_t1) <= 0.25 * face
        verdict = "t2-like" if near_t2 and not near_t1 else ("t1-like" if near_t1 and not near_t2 else ("ambiguous(both)" if near_t2 and near_t1 else "neither"))
    row = {"code": code, "issue_date": d, "face_eok": face, "quarter": q, "d_item6": d6, "d_item47": d47, "d_X(13-49)": dx, "cap10": None if cap is None else round(cap, 1),
           "pred_d47_if_tier2": face, "pred_d47_if_tier1": None if pred_t1 is None else round(pred_t1, 1), "verdict_47": verdict, "name": name}
    rows.append(row)
    out_lines.append(f"{code} {d} face {face:>8g} {q}: d6={n0(d6):>6} d47={n0(d47):>6} dX={n0(dx):>6} | "
                     f"cap10={row['cap10']} pred47 t2={face:g} t1={row['pred_d47_if_tier1']} -> {verdict}  | {name}")

with open(HERE / "census_issue_quarter_test.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
(HERE / "census_issue_quarter_test.txt").write_text("\n".join(out_lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out_lines))
