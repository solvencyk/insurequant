# -*- coding: utf-8 -*-
"""Read-only falsification probe for the 36_irr re-audit (KR0094 / KR0073 pinned buckets).

Q: is there ANY reading of the six 금리위험 순자산가치 columns (role permutation) or any
   variant of the aggregation formula that reproduces the disclosed item36 for the five
   pinned buckets WITHOUT breaking the buckets that currently close?

Read-only. Writes one UTF-8 report under artifacts/validation/.
"""
import itertools
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "validation" / "reaudit_20260824_irr_formula_search.txt"

K_CODE, K_NAME, K_NO, K_Q, K_V = "원보험사코드", "원수사명", "항목번호", "공시분기", "값"

recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
buckets = {}
names = {}
for r in recs:
    key = (r[K_CODE], r[K_Q])
    names[r[K_CODE]] = r.get(K_NAME)
    buckets.setdefault(key, {})[r[K_NO]] = r.get(K_V)


def num(x):
    if x is None:
        return None
    try:
        return float(str(x).replace(",", ""))
    except ValueError:
        return None


COMPLETE = []
for key, d in buckets.items():
    vals = {n: num(d.get(n)) for n in (36, 41, 42, 43, 44, 45, 46)}
    if all(v is not None for v in vals.values()):
        COMPLETE.append((key, vals))
COMPLETE.sort()

TARGETS = {("KR0073", "2025.2Q"), ("KR0094", "2024.2Q"), ("KR0094", "2024.4Q"),
           ("KR0094", "2025.2Q"), ("KR0094", "2025.4Q")}


def closes(disclosed, derived):
    if derived is None:
        return False
    return abs(disclosed - derived) <= max(2.0, abs(disclosed) * 0.005)


def aggregate(base, mr_i, up_i, dn_i, fl_i, st_i, v, agg, mrmode):
    up = max(base - v[up_i], 0.0)
    dn = max(base - v[dn_i], 0.0)
    fl = max(base - v[fl_i], 0.0)
    st = max(base - v[st_i], 0.0)
    a, b = max(up, dn), max(fl, st)
    if agg == "pyth":
        core = math.sqrt(a * a + b * b)
    elif agg == "sum":
        core = a + b
    else:
        core = max(a, b)
    raw_mr = base - v[mr_i]
    if mrmode == "signed":
        mr = raw_mr
    elif mrmode == "clip0":
        mr = max(raw_mr, 0.0)
    elif mrmode == "abs":
        mr = abs(raw_mr)
    else:
        mr = 0.0
    return core + mr


buf = []
buf.append("complete buckets (36 + 41-46 all present, 값 column): %d" % len(COMPLETE))
buf.append("pinned targets present among them: %s"
           % sorted(k for k, _ in COMPLETE if k in TARGETS))
buf.append("")

results = []
for base_i in (41, 42, 43, 44, 45, 46):
    rest = [i for i in (41, 42, 43, 44, 45, 46) if i != base_i]
    for perm in itertools.permutations(rest):
        mr_i, up_i, dn_i, fl_i, st_i = perm
        for agg in ("pyth", "sum", "max"):
            for mrmode in ("signed", "clip0", "abs", "none"):
                n_ok = 0
                n_target_ok = 0
                for key, v in COMPLETE:
                    d = aggregate(v[base_i], mr_i, up_i, dn_i, fl_i, st_i, v, agg, mrmode)
                    if closes(v[36], d):
                        n_ok += 1
                        if key in TARGETS:
                            n_target_ok += 1
                results.append((n_ok, n_target_ok, base_i, perm, agg, mrmode))

results.sort(key=lambda r: (-r[0], -r[1]))
buf.append("=== top 12 by total buckets closed (out of %d) ===" % len(COMPLETE))
buf.append("closed  pinned(of 5)  base  (mr,up,dn,flat,steep)  agg     mr-mode")
for n_ok, n_t, base_i, perm, agg, mrmode in results[:12]:
    buf.append("%6d  %12d  i%-3d  %-24s %-6s %s" % (n_ok, n_t, base_i, perm, agg, mrmode))
buf.append("")

cur = [r for r in results
       if (r[2], r[3], r[4], r[5]) == (41, (42, 43, 44, 45, 46), "pyth", "signed")][0]
buf.append("CURRENT RULE -> closed=%d  pinned_closed=%d" % (cur[0], cur[1]))
buf.append("")

for want in (5, 4, 3):
    cands = [r for r in results if r[1] == want]
    buf.append("variants closing exactly %d of the 5 pinned buckets: %d" % (want, len(cands)))
    for r in sorted(cands, key=lambda r: -r[0])[:10]:
        buf.append("   closed=%d (net vs current %+d)  base=i%d perm=%s agg=%s mr=%s"
                   % (r[0], r[0] - cur[0], r[2], r[3], r[4], r[5]))
buf.append("")

buf.append("=== per-target detail (current column mapping) ===")
for key, v in COMPLETE:
    if key not in TARGETS:
        continue
    base = v[41]
    up = max(base - v[43], 0.0)
    dn = max(base - v[44], 0.0)
    fl = max(base - v[45], 0.0)
    st = max(base - v[46], 0.0)
    a, b = max(up, dn), max(fl, st)
    mr = base - v[42]
    pyth = math.sqrt(a * a + b * b) + mr
    summ = a + b + mr
    buf.append("%s %s %s" % (key[0], key[1], names[key[0]]))
    buf.append("   i41 base=%12.2f  i42 mr-scen=%12.2f  i43 up=%12.2f  i44 dn=%12.2f  "
               "i45 flat=%12.2f  i46 steep=%12.2f" % (base, v[42], v[43], v[44], v[45], v[46]))
    buf.append("   shocks: up=%.2f dn=%.2f flat=%.2f steep=%.2f  평균회귀금액(signed)=%.2f"
               % (up, dn, fl, st, mr))
    buf.append("   disclosed item36 = %.2f" % v[36])
    buf.append("   pyth sqrt(a^2+b^2)+mr = %12.2f   resid %+10.2f (%+6.2f%%)"
               % (pyth, v[36] - pyth, (v[36] - pyth) / v[36] * 100))
    buf.append("   sum  a+b+mr           = %12.2f   resid %+10.2f (%+6.2f%%)"
               % (summ, v[36] - summ, (v[36] - summ) / v[36] * 100))
    buf.append("   disclosed lies strictly between the two readings: %s"
               % (min(pyth, summ) <= v[36] <= max(pyth, summ)))
    buf.append("")

buf.append("=== KR0094 every quarter with 41-46 complete (current rule) ===")
for key, v in COMPLETE:
    if key[0] != "KR0094":
        continue
    base = v[41]
    up = max(base - v[43], 0.0)
    dn = max(base - v[44], 0.0)
    fl = max(base - v[45], 0.0)
    st = max(base - v[46], 0.0)
    mr = base - v[42]
    d = math.sqrt(max(up, dn) ** 2 + max(fl, st) ** 2) + mr
    buf.append("   %s  i41=%14.2f  disclosed i36=%10.2f  derived=%10.2f  "
               "resid=%+10.2f (%+6.2f%%)  closes=%s"
               % (key[1], base, v[36], d, v[36] - d, (v[36] - d) / v[36] * 100,
                  closes(v[36], d)))
buf.append("")

buf.append("=== does the 2024 scope narrowing explain it? i41 2023.4Q -> 2024.2Q per company ===")
by = {}
for key, v in COMPLETE:
    by.setdefault(key[0], {})[key[1]] = v


def resid_pct(v):
    base = v[41]
    up = max(base - v[43], 0.0)
    dn = max(base - v[44], 0.0)
    fl = max(base - v[45], 0.0)
    st = max(base - v[46], 0.0)
    d = math.sqrt(max(up, dn) ** 2 + max(fl, st) ** 2) + (base - v[42])
    return (v[36] - d) / v[36] * 100


buf.append("%-8s%-22s%16s%16s%9s%14s%14s"
           % ("code", "name", "i41 2023.4Q", "i41 2024.2Q", "ratio", "resid% 23.4Q", "resid% 24.2Q"))
for code, qs in sorted(by.items()):
    if "2023.4Q" not in qs or "2024.2Q" not in qs:
        continue
    a, b = qs["2023.4Q"], qs["2024.2Q"]
    ratio = (b[41] / a[41]) if a[41] else float("nan")
    buf.append("%-8s%-22s%16.0f%16.0f%9.3f%14.2f%14.2f"
               % (code, (names.get(code) or "")[:20], a[41], b[41], ratio,
                  resid_pct(a), resid_pct(b)))

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(buf), encoding="utf-8")
print("wrote", OUT)
