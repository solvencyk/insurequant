# -*- coding: utf-8 -*-
"""Post-load check (read-only): the LIVE masters now equal the independent reading of the FY2024 annual report's FY2023 comparative column for EVERY 2023.4Q item
(except the two documented rounding keeps: item 6 stays 51,324 [printed 51,323] and item 7 is its residual, item 15 has no printed row) and the CSM vector; and the single quarters are what the plan says."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import kr0003_verify as V   # noqa: E402  (own stdlib-only reader; main() is not executed on import)

sys.stdout.reconfigure(encoding="utf-8")
ROOT, CODE, Q = V.ROOT, V.CODE, V.Q
pl = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))}
csm = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r for r in json.loads((ROOT / "CSM_waterfall.json").read_text(encoding="utf-8"))}
s24 = V.Stmt("A24")
t24, _ = V.tier1(s24, 1)
lob = V.lob_items(V.F["A24"], "전")
it = lob["items"]
want = {i: t24[i]["val"] for i in t24}
for i in (2, 3, 4, 5, 6, 8, 9, 10, 11, 13, 14):
    want[i] = it[i]["val"]
want[6] = pl[(CODE, 6, Q)]["값"]                       # rounding-only difference: kept (existing value)
want[7] = it[3]["val"] - (it[4]["val"] + it[5]["val"] + want[6])
want[12] = it[8]["val"] - (it[9]["val"] + it[10]["val"] + it[11]["val"])
bad, n = [], 0
out = []
for i in sorted(want):
    live = pl[(CODE, i, Q)]["값"]
    ok = live is not None and abs(live - want[i]) <= 5e-7
    n += 1
    if not ok:
        bad.append((i, live, want[i]))
    out.append(f"  PL item {i:2d}: live {live!s:>18}  independent {want[i]:>18.6f}  {'OK' if ok else 'DIFF'}")
cts = [t for t in V.csm_tables(V.F["A24"]) if t["gubun"] == "전" and t["title"].startswith("5.")]
cv = V.csm_vector(cts[0], V.F["A24"])
for i in range(1, 7):
    sv = V.stored1(cv["vec"][i - 1])
    live = csm[(CODE, i, Q)]["값"]
    ok = abs(sv - live) <= 1e-9
    n += 1
    if not ok:
        bad.append(("CSM", i, live, sv))
    out.append(f"  CSM item {i}: live {live}  independent stored {sv} (exact {cv['vec'][i - 1]:.2f})  {'OK' if ok else 'DIFF'}")
# single quarters
nd = {c[2] for c in V.PLAN["apply_contract"]["null_dangi_add"]}
for i in sorted(nd):
    d = pl[(CODE, i, Q)]["값_당분기"]
    ok = d is None
    n += 1
    if not ok:
        bad.append(("dangi", i, d))
    out.append(f"  PL single quarter item {i:2d}: {d!s} (planned blank) {'OK' if ok else 'DIFF'}")
for i in (3, 4, 5, 6):
    live = csm[(CODE, i, Q)]["값_당분기"]
    q3 = csm[(CODE, i, "2023.3Q")]["값"]
    exp = csm[(CODE, i, Q)]["값"] if i == 6 else round(csm[(CODE, i, Q)]["값"] - q3, 6)
    ok = abs(live - exp) <= 1e-6
    n += 1
    if not ok:
        bad.append(("csm_dangi", i, live, exp))
    out.append(f"  CSM single quarter item {i}: {live}  derived (4Q cumulative - 3Q cumulative) {exp}  {'OK' if ok else 'DIFF'}")
out.append(f"RESULT: {n} comparisons, {len(bad)} differences {bad[:4]}")
(HERE / "kr0003_postload_check.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
sys.exit(0 if not bad else 1)
