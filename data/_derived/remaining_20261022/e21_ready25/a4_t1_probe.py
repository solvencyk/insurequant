"""a4_t1_probe: compare the Tier-1 candidate cells (READY_all) with an independent statement read (STEP 1's e20_read.py, own code) of the LATER filing's separate prior cumulative column. READ-ONLY."""
import json, sys
from collections import defaultdict
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_read as R
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
d = json.loads(open(M + "cands_READY_all.json", encoding="utf-8").read())
T1 = {1, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32}
by = defaultdict(dict)
for c in d["pl_cells"]:
    if c["item"] in T1:
        by[(c["code"], c["q"])][c["item"]] = c["new"]
tot = ok = 0
for (code, q), cells in sorted(by.items()):
    fy = f"FY{int(q[:4]) + 1}_Q{q[5]}"
    try:
        st = R.Stmt(code, fy)
        vec = R.read_vector(st, "prior", "cum")
    except Exception as e:  # noqa: BLE001
        print(f"{code} {q} {fy}: READ ERROR {type(e).__name__}: {str(e)[:150]}")
        continue
    bad = []
    for it, new in sorted(cells.items()):
        tot += 1
        v = vec.get(it, {}).get("val")
        if v is not None and abs(v - new) < 1e-3:
            ok += 1
        else:
            bad.append((it, new, None if v is None else round(v, 6)))
    print(f"{code} {q} {fy} {st.fmt} unit={st.unit}: cells {len(cells)} match {len(cells) - len(bad)}; mismatch {bad}")
print("TOTAL", tot, "match", ok)
