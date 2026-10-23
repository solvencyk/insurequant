# -*- coding: utf-8 -*-
"""e23 probe (read-only): can the e21 statement reader read the prior-year cumulative columns of the D1-D3 companies' FY2024 filings?  Compare with the e20 candidate cells."""
import json
import sys
from pathlib import Path

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
MEAS = ROOT / "data/_derived/remaining_20261022/e20_held_and_remaining/measure"
SPEC = [("KR0099", "2023.1Q"), ("KR0099", "2023.2Q"), ("KR0099", "2023.3Q"),
        ("KR0003", "2023.4Q"),
        ("KR0070", "2023.1Q"), ("KR0070", "2023.2Q"), ("KR0070", "2023.3Q"), ("KR0070", "2023.4Q"),
        ("KR0072", "2023.1Q"), ("KR0072", "2023.2Q"), ("KR0072", "2023.3Q"), ("KR0072", "2023.4Q"),
        ("KR0009", "2023.1Q"), ("KR0009", "2023.2Q"), ("KR0009", "2023.3Q"), ("KR0009", "2023.4Q")]
cands = {}
for s in ("N2_KBlife_B", "N7_Lotte_FY2023Q4", "N4_ABL_FY2023", "N5_KDB_FY2023", "N6c_HD_FY2023_IRlegs"):
    d = json.loads((MEAS / f"cands_{s}.json").read_text(encoding="utf-8"))
    for c in d["pl_cells"]:
        cands[(c["code"], c["q"], c["item"])] = c
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
M = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in pl}
for code, q in SPEC:
    fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
    print("=" * 100)
    print(code, q, fy)
    try:
        st = R.Stmt(code, fy)
    except Exception as e:  # noqa: BLE001
        print("   Stmt ERROR", type(e).__name__, e)
        continue
    print(f"   file {st.rel} fmt={st.fmt} unit={st.unit} rows={len(st.rows)} title_line={st.title}")
    try:
        v = R.read_vector(st, "prior", "cum")
    except Exception as e:  # noqa: BLE001
        print("   read_vector ERROR", type(e).__name__, str(e)[:300])
        labs = [(r.raw, r.line, [(c['text'], (c['ctx'] or '')[:18]) for c in r.cells][:5]) for r in st.rows[:12]]
        for l in labs:
            print("      ", l)
        continue
    out = []
    for i in sorted(k for k in v if isinstance(k, int)):
        val = sum(p.sign * p.val_mn for p in v[i]["parts"]) if v[i]["parts"] else v[i]["val"]
        old = M.get((code, i, q))
        cd = cands.get((code, q, i))
        flag = ""
        if cd is not None:
            flag = f" CAND={cd['new']}" + ("" if abs(cd["new"] - val) <= 1e-3 else " <<DIFF>>")
        elif old is None or abs(old - val) > 1.5:
            flag = " (not in cand!)"
        out.append(f"   i{i:>2} old={old} read={round(val, 6)}{flag}")
    print("\n".join(out))
