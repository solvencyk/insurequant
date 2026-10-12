"""c2b_sub_reconcile.py (parser-kics, ticket 20261012T1230Z) -- READ ONLY.

c2 compared item 54 (기발행 후순위채무 of the issuer's 공통적용 경과조치 표) only with the subordinated bonds issued before 2023-01-01.  Heungkuk Life shows
that item 54 follows ALL outstanding subordinated bonds (4,132 vs 400 + 2,000 + 1,100 + 600 outstanding), so this step re-runs the comparison against the
subordinated bonds of every issue date still outstanding at the quarter end (redeemed = call date passed while the list shows outstanding 0, same convention as c2).
A remaining gap = subordinated debt of the issuer's table that the bond lists do not contain (or a different recognition basis: the face may be amortised 20% a year
in the last 5 years before maturity -> `list_sub_amortised`).
Output: census_reconcile_sub.csv / census_reconcile_sub.txt.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe data/_derived/capital_securities_classification_census_20261012/c2b_sub_reconcile.py
"""
from __future__ import annotations

import csv
import io
import json
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
inv = json.loads((HERE / "census_inventory.json").read_text(encoding="utf-8"))["rows"]
kd = json.loads((REPO / "kics_disclosure.json").read_text(encoding="utf-8"))
QUARTERS = [f"{y}.{n}Q" for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]
QEND = {f"{y}.{n}Q": f"{y}-{[3, 6, 9, 12][n - 1]:02d}-{[31, 30, 30, 31][n - 1]}" for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)}

I54 = defaultdict(dict)
names = {}
for r in kd:
    if r["항목번호"] == 54:
        try:
            I54[r["원보험사코드"]][r["공시분기"]] = float(str(r.get("값")).replace(",", ""))
        except (TypeError, ValueError):
            pass
        names[r["원보험사코드"]] = r.get("원수사명")

subs = defaultdict(list)
for r in inv:
    if r["tier"] == "subordinated" and r["issue_date"]:
        subs[r["code"]].append(r)


def todate(s):
    y, m, d = (int(x) for x in s.split("-"))
    return date(y, m, d)


def redeemed(r, qend):
    return r["outstanding_eok"] == 0 and bool(r["call_date"]) and r["call_date"] <= qend


def amortised(face, maturity, qend):
    """K-ICS 보완자본 후순위: remaining maturity < 5 years -> 20% less for every year (or part) short of 5 years."""
    if not maturity:
        return face
    rem = (todate(maturity) - todate(qend)).days / 365.25
    if rem >= 5:
        return face
    cut = min(1.0, 0.2 * (int(5 - rem) + 1)) if rem > 0 else 1.0
    return face * (1 - cut)


rows, lines = [], []
for code in sorted(set(I54) | set(subs)):
    if not any((v or 0) > 0 for v in I54.get(code, {}).values()) and code not in subs:
        continue
    lines.append(f"== {code} {names.get(code)} | subordinated bonds in inventory: {len(subs.get(code, []))}")
    for q in QUARTERS:
        v = I54.get(code, {}).get(q)
        if v is None:
            continue
        qend = QEND[q]
        face = amort = 0.0
        for r in subs.get(code, []):
            if r["issue_date"] > qend or redeemed(r, qend):
                continue
            f = r["face_eok"] if r["face_eok"] is not None else (r["outstanding_eok"] or 0.0)
            face += f
            amort += amortised(f, r["legal_maturity"], qend)
        gap_face, gap_am = round(v - face, 2), round(v - amort, 2)
        tol = max(5.0, 0.03 * max(v, face, 1))
        flag = "" if min(abs(gap_face), abs(gap_am)) <= tol else "  <== GAP"
        rows.append({"code": code, "company": names.get(code), "quarter": q, "item54": v, "list_sub_face": round(face, 2), "list_sub_amortised": round(amort, 2),
                     "gap_face": gap_face, "gap_amortised": gap_am, "flag": flag.strip()})
        lines.append(f"  {q}: i54={v} | list face {face:g} (gap {gap_face:g}) | list amortised {amort:.0f} (gap {gap_am:g}){flag}")

with open(HERE / "census_reconcile_sub.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
(HERE / "census_reconcile_sub.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

# compact view: latest quarter + how many quarters are inside tolerance, per company
by = defaultdict(list)
for r in rows:
    by[r["code"]].append(r)
print("code  company | quarters with i54 | quarters within tolerance (face or amortised) | latest quarter: i54 / list face / list amortised")
for code, rs in sorted(by.items()):
    ok = sum(1 for r in rs if not r["flag"])
    last = rs[-1]
    print(f"{code} {str(last['company'])[:12]:<12} | {len(rs):>2} | {ok:>2} | {last['quarter']}: {last['item54']:g} / {last['list_sub_face']:g} / {last['list_sub_amortised']:g}")
