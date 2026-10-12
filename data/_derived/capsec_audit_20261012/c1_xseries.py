# -*- coding: utf-8 -*-
"""c1: quarterly series of the issuer's K-ICS cells needed for the per-security X test (read-only).

For the 10 companies named by the coordinator plus the other registry-listed hybrid issuers.
X_t = item13_t - item49_t (pre-TFI column `값`), L_t = item53_t (legacy 신종 incl.), cap10 = 0.10 * item14_t(pre).
Independent of the implementation: reads kics_disclosure.json only.
Output: c1_xseries.csv, c1_xseries.txt
"""
import csv
import json
from collections import defaultdict

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = ROOT + "/data/_derived/capsec_audit_20261012/"
QUARTERS = ["%d.%dQ" % (y, n) for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3, 4)][:14]
CODES = ["KR0050", "KR1000", "KR0097", "KR0073", "KR0068", "KR0005", "KR0072", "KR0104", "KR0083", "KR0032",
         "KR0011", "KR0002", "KR0071", "KR0076", "KR0001", "KR0003", "KR0099"]
ITEMS = [1, 2, 3, 6, 12, 13, 14, 47, 48, 49, 53, 54]


def num(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if s in ("", "-", "—", "–", "nan", "None"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


d = json.load(open(ROOT + "/kics_disclosure.json", encoding="utf-8"))
S = defaultdict(dict)    # (code,item,'pre'|'post') -> {quarter: val}
names = {}
allq = set()
for r in d:
    k = r.get("항목번호")
    if k not in ITEMS:
        continue
    q = r["공시분기"]
    allq.add(q)
    names[r["원보험사코드"]] = r["원수사명"]
    S[(r["원보험사코드"], k, "pre")][q] = num(r.get("값"))
    S[(r["원보험사코드"], k, "post")][q] = num(r.get("값_적용후"))
print("quarters present", sorted(allq))


def g(code, item, q, col="pre"):
    return S.get((code, item, col), {}).get(q)


rows = []
for code in CODES:
    for q in QUARTERS:
        i13 = g(code, 13, q)
        i49 = g(code, 49, q)
        x = None if (i13 is None or i49 is None) else i13 - i49
        l53 = g(code, 53, q)
        i14 = g(code, 14, q)
        rows.append({
            "code": code, "name": names.get(code), "q": q,
            "i6": g(code, 6, q), "i53": l53, "i54": g(code, 54, q), "i14pre": i14, "i14post": g(code, 14, q, "post"),
            "cap10": None if i14 is None else round(0.10 * i14, 2),
            "i13": i13, "i49": i49, "X": None if x is None else round(x, 2),
            "X_minus_L": None if (x is None) else round(x - (l53 or 0.0), 2),
            "i47pre": g(code, 47, q), "i47post": g(code, 47, q, "post"), "i48pre": g(code, 48, q),
            "i3pre": g(code, 3, q), "i3post": g(code, 3, q, "post"), "i2pre": g(code, 2, q), "i2post": g(code, 2, q, "post"),
        })

cols = list(rows[0].keys())
with open(OUT + "c1_xseries.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)


def f1(v):
    return "." if v is None else ("%.1f" % v)


with open(OUT + "c1_xseries.txt", "w", encoding="utf-8", newline="\n") as f:
    for code in CODES:
        f.write("== %s %s\n" % (code, names.get(code)))
        f.write("  qtr     i6      L53    i14pre   cap10      i13     i49       X     X-L   i47pre  i47post  i3pre-49\n")
        for r in [x for x in rows if x["code"] == code]:
            i3m49 = None if (r["i3pre"] is None or r["i49"] is None) else r["i3pre"] - r["i49"]
            f.write("  %s %8s %8s %8s %8s %8s %8s %8s %8s %8s %8s %8s\n" % (
                r["q"], f1(r["i6"]), f1(r["i53"]), f1(r["i14pre"]), f1(r["cap10"]), f1(r["i13"]), f1(r["i49"]),
                f1(r["X"]), f1(r["X_minus_L"]), f1(r["i47pre"]), f1(r["i47post"]), f1(i3m49)))
print("done")
