"""Pre-change snapshot: KR0070 items 1-16 for 2024.4Q/2025.1Q from both pl_breakdown_master.json
(PL_SRC, pre-overlay) and root PL_breakdown.json (PL_OUT, post-overlay/deployed), for
inbox/parser/20260829T1100Z. Read-only.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
     scripts/_probes/abl_2024q4_2025q1_pre_state.py
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
REPO = Path(__file__).resolve().parents[2]
CODE = "KR0070"
QS = ("2024.4Q", "2025.1Q")


def dump(path, label):
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    print(f"=== {label} ({path}) ===")
    for q in QS:
        print(f"-- {q} --")
        sub = [r for r in rows if r["원보험사코드"] == CODE and r["공시분기"] == q]
        for r in sorted(sub, key=lambda r: r["항목번호"]):
            v = r.get("값")
            vd = r.get("값_당분기")
            vs = f"{v:,.2f}" if isinstance(v, (int, float)) else str(v)
            vds = f"{vd:,.2f}" if isinstance(vd, (int, float)) else str(vd)
            print(f"  item{r['항목번호']:<3d} {r.get('항목명',''):20s} 값={vs:>14s}  값_당분기={vds:>14s}")
    print()


dump(REPO / "data/dart/viz/pl_breakdown_master.json", "PL_SRC (pl_breakdown_master.json)")
dump(REPO / "PL_breakdown.json", "PL_OUT (root, deployed)")
