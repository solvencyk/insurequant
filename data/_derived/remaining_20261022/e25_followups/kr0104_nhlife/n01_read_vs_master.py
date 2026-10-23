# -*- coding: utf-8 -*-
"""READ-ONLY (ticket 20261023T0600Z, KR0104 농협생명 2024.1Q-2024.3Q): read the FULL Tier-1 vector (items 1, 16..32) from the LATER filing's prior-period cumulative column
(separate basis) for 2024.1Q (FY2025_Q1), 2024.2Q (FY2025_Q2), 2024.3Q (FY2025_Q3) and 2024.4Q (FY2025_Q4), compare with the live master, and print the prior 3-month column for
the single-quarter seam check.  Own use of the e21 statement reader (4-2 포괄손익계산서 = separate basis); the cells are re-read independently in n02_verify.py."""
import json
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
CODE = "KR0104"
live = {(r["공시분기"], r["항목번호"]): r for r in json.load(open(f"{ROOT}/PL_breakdown.json", encoding="utf-8")) if r["원보험사코드"] == CODE}
PAIRS = [("2024.1Q", "FY2025_Q1"), ("2024.2Q", "FY2025_Q2"), ("2024.3Q", "FY2025_Q3"), ("2024.4Q", "FY2025_Q4")]
out = {}
for q, fy in PAIRS:
    st = R.Stmt(CODE, fy)
    print(f"##### {q} from {fy} {st.rel} fmt={st.fmt} unit={st.unit}")
    v = R.read_vector(st, "prior", "cum")
    cur = R.read_vector(st, "cur", "cum")
    try:
        v3 = R.read_vector(st, "prior", "3m", want={1, 17, 20, 21, 22, 24})
    except Exception as e:  # noqa: BLE001
        v3 = {}
        print("   (no prior 3m column:", type(e).__name__, str(e)[:100], ")")
    for it in sorted(k for k in v if isinstance(k, int)):
        m = live.get((q, it))
        mv = None if m is None else m.get("값")
        nv = v[it]["val"]
        flag = "" if (mv is not None and abs(mv - nv) <= 5e-4) else ("  <-- DIFF" if mv is not None else "  <-- master blank")
        p3 = v3.get(it)
        extra = f"  | prior3m {p3['val']:.6f} (L{p3['parts'][0].line})" if p3 and p3["parts"] else ""
        print(f"  item {it:>2}: master {mv!s:>18} | prior-cum {nv:>18.6f} (L{','.join(str(p.line) for p in v[it]['parts'][:3])}; printed {[p.printed for p in v[it]['parts'][:3]]}){flag}{extra}")
    out[q] = {it: dict(val=v[it]["val"], master=(live.get((q, it)) or {}).get("값"), lines=[p.line for p in v[it]["parts"]]) for it in v if isinstance(it, int)}
json.dump(out, open("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups/kr0104_nhlife/n01_read_vs_master.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
