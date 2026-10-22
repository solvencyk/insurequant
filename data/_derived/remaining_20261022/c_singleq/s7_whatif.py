# -*- coding: utf-8 -*-
"""What-if (read-only, nothing written except s7_whatif.txt): replace the 2023.2Q CSM vector of Hanwha (KR0068) and
Meritz (KR0001) by the restated H1 comparative printed in the FY2024 Q2 report (values read by s5_ctx.py from raw)
and re-evaluate SQ_CSM_ROLL for 2023.2Q/2023.3Q, WFY, and the YTD CSM_AMORT_IDENTITY against the current PL item 4."""
import json, subprocess, pathlib
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
def show(f):
    return json.loads(subprocess.run(["git", "show", f"HEAD:{f}"], capture_output=True, check=True, cwd=ROOT).stdout.decode("utf-8"))
wf = show("CSM_waterfall.json"); pl = show("PL_breakdown.json")
cv = {}
for r in wf:
    cv[(r["원보험사코드"], r["공시분기"], int(r["항목번호"]))] = r.get("값")
p4 = {(r["원보험사코드"], r["공시분기"]): r.get("값") for r in pl if str(r["항목번호"]) == "4"}
p41 = {(r["원보험사코드"], r["공시분기"]): r.get("값") for r in pl if str(r["항목번호"]) == "4-1"}
# restated 2023 H1 (백만원 -> 억원), raw: FY2024_Q2 <전반기>/2) 전반기 tables (s5_ctx dumps)
RESTATED_H1 = {
    # Hanwha 20240813000860.xml L78126-78328: open 9,762,946 new 1,164,313 adj -523,439 amort -451,416 int 170,291 close 10,122,695
    "KR0068": {1: 97629.46, 2: 11643.13, 3: 1702.91, 4: -5234.39, 5: -4514.16, 6: 101226.95},
    # Meritz 20240814003013.xml L26025-26375 (sum of 3 CSM columns): open 9,637,639 new 809,694
    # int 66,790+30,218+43,818 adj -(246,434+91,861+33,306) amort -515,014 close 9,701,544
    "KR0001": {1: 96376.39, 2: 8096.94, 3: 1408.26, 4: -3716.01, 5: -5150.14, 6: 97015.44},
}
out = []; P = out.append
for c, h1 in RESTATED_H1.items():
    s = sum(h1[i] for i in range(1, 6)) - h1[6]
    P(f"{c} restated H1 self-roll residual {s:+.2f}억")
    cur2 = {i: cv[(c, '2023.2Q', i)] for i in range(1, 7)}
    cur3 = {i: cv[(c, '2023.3Q', i)] for i in range(1, 7)}
    P(f"   master 2023.2Q {cur2}")
    P(f"   master 2023.3Q {cur3}")
    # single-quarter roll after the swap
    d3 = {1: h1[6], 6: cur3[6]}
    for i in (2, 3, 4, 5):
        d3[i] = cur3[i] - h1[i]
    gap3 = sum(d3[i] for i in range(1, 6)) - d3[6]
    P(f"   after swap: SQ roll 2023.3Q gap {gap3:+.2f}억 (before: see s1_sim)")
    c1 = {i: cv[(c, '2023.1Q', i)] for i in range(1, 7)}
    d2 = {1: c1[6], 6: h1[6]}
    for i in (2, 3, 4, 5):
        d2[i] = h1[i] - c1[i]
    gap2 = sum(d2[i] for i in range(1, 6)) - d2[6]
    P(f"   after swap (2023.1Q NOT swapped): SQ roll 2023.2Q gap {gap2:+.2f}억 -> 2023.1Q must be refreshed too (FY2024 Q1 comparative)")
    P(f"   WFY 2023 opens after swap: 1Q {c1[1]} 2Q {h1[1]} 3Q {cur3[1]}")
    pl2 = p4.get((c, "2023.2Q")); pl2r = p41.get((c, "2023.2Q"))
    plside = (abs(pl2) + (abs(pl2r) if pl2r else 0)) / 100 if pl2 is not None else None
    P(f"   CSM_AMORT_IDENTITY 2023.2Q: PL item4(+4-1) {plside}억 vs WF amort now {abs(cur2[5])} / after swap {abs(h1[5])} "
      f"-> residual now {None if plside is None else round(plside - abs(cur2[5]), 2)} after {None if plside is None else round(plside - abs(h1[5]), 2)}")
(HERE / "s7_whatif.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print("\n".join(out))
