import json, sys
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
live = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): (r["값"], r.get("값_당분기")) for r in M.jload(M.ROOT / "PL_breakdown.json")}
snap = {(r["원보험사코드"], r["공시분기"], str(r["항목번호"])): (r["값"], r.get("값_당분기")) for r in M.jload(M.SNAP / "PL_breakdown.json")}
for it in (17, 19, 20, 22, 23, 24, 25, 27):
    k = ("KR0083", "2024.4Q", str(it))
    k3 = ("KR0083", "2024.3Q", str(it))
    print(f"item {it}: 4Q YTD live={live[k][0]} | 4Q single snapshot={snap[k][1]} live={live[k][1]} | 3Q YTD snapshot={snap[k3][0]} live={live[k3][0]}")
