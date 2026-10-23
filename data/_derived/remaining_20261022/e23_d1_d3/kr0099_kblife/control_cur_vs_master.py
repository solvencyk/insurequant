# -*- coding: utf-8 -*-
"""KR0099 control (read-only): apply the SAME statement reader (blank-aware Stmt23 + read_tier1 + life_is_items + presence_015) to the CURRENT-period cumulative column of the filings whose
quarter the live master already carries from the production path (FY2023 Q3 / Q4-orig, FY2024 Q1 / Q2 / Q3).  If the reader's definitions match the master's, every item must agree (rounding band 1 mn).
This proves the item definitions (17 in the Q1 layout, 30 / 32 split, 19, 21, 15) are the master's, independent of the later-filing prior column the load uses."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife")
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e23_read as X  # noqa: E402
import e21_life as L  # noqa: E402
import e21_plan_lib as P  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
master = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in json.loads(open(ROOT + "/PL_breakdown.json", encoding="utf-8").read()) if r["원보험사코드"] == "KR0099"}
CFG = dict(names_extra={1: ["보험영업손익"], 17: ["투자영업손익"]})
cases = [("FY2023_Q3", "2023.3Q"), ("FY2024_Q1", "2024.1Q"), ("FY2024_Q2", "2024.2Q"), ("FY2024_Q3", "2024.3Q"), ("FY2023_Q4", "2023.4Q"), ("FY2024_Q4", "2024.4Q")]
tot_bad = 0
for fy, q in cases:
    try:
        st = X.Stmt23("KR0099", fy)
    except Exception as e:  # noqa: BLE001
        print(fy, q, "cannot open statement:", repr(e)[:160])
        continue
    try:
        t1 = X.read_tier1(st, "cur", "cum", CFG)
    except Exception as e:  # noqa: BLE001
        print(fy, q, "read_tier1 failed:", repr(e)[:200])
        continue
    vals = {i: t1[i]["val"] for i in P.TIER1}
    p15 = X.presence_015(st, "cur", "cum", insurance_only=True)
    vals[15] = p15["val"]
    lr = L.life_is_items("KR0099", fy, "cur", "cum", st=st)
    vals[3], vals[8] = lr[3]["val"], lr[8]["val"]
    vals[2] = vals[3] + vals[8]
    bad = []
    rows = []
    for i in sorted(vals):
        m = master.get(("KR0099", i, q))
        v = vals[i]
        if m is None:
            rows.append((i, v, m, "master empty"))
            continue
        d = v - m
        flag = "ok" if abs(d) <= 1.0001 else "DIFF"
        if flag == "DIFF":
            bad.append(i)
        rows.append((i, v, m, flag if abs(d) < 1e-9 else f"{flag} d={d:+.1f}"))
    print("=" * 90)
    print(fy, q, st.rel, "unit", st.unit, "| DIFF items:", bad)
    print("   " + "; ".join(f"i{i}:{v:g} vs {m}{'' if f == 'ok' else ' <' + f + '>'}" for i, v, m, f in rows))
    tot_bad += len(bad)
print("TOTAL DIFF items", tot_bad)
