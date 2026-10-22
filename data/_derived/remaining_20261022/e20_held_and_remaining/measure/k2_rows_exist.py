"""k2: do master rows exist (value null) or are they absent? (READ-ONLY, snapshot)"""
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M

sys.stdout.reconfigure(encoding="utf-8")
rows = M.jload(M.SNAP / "PL_breakdown.json")
code = sys.argv[1]
qs = sys.argv[2].split(",")
for q in qs:
    present = sorted({M.itn(r["항목번호"]) for r in rows if r["원보험사코드"] == code and r["공시분기"] == q}, key=lambda x: (isinstance(x, str), str(x).zfill(3)))
    nulls = sorted({M.itn(r["항목번호"]) for r in rows if r["원보험사코드"] == code and r["공시분기"] == q and r["값"] is None}, key=lambda x: (isinstance(x, str), str(x).zfill(3)))
    print(code, q, "rows:", len(present), "present items:", present)
    print("   null-valued:", nulls)
    print("   keys of one row:", [k for k in rows[0].keys()])
