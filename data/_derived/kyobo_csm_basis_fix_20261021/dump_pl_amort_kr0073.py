"""Read-only: PL_breakdown.json KR0073 CSM-amortization rows vs CSM_waterfall item 5, per quarter."""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")

with open(ROOT / "PL_breakdown.json", "r", encoding="utf-8") as f:
    pl = json.load(f)
print("PL rows:", len(pl), "keys of first:", list(pl[0].keys()))
kr = [r for r in pl if r.get("원보험사코드") == "KR0073"]
print("KR0073 PL rows:", len(kr))
names = {}
for r in kr:
    names.setdefault((r.get("항목번호"), r.get("항목명")), 0)
    names[(r.get("항목번호"), r.get("항목명"))] += 1
for k in sorted(names, key=lambda x: (x[0] if isinstance(x[0], int) else 999)):
    print("  item", k, names[k])

QORD = lambda q: int(q[:4]) * 10 + int(q[5])
print()
print("quarter | PL item rows containing 'CSM' (값 | 값_당분기)")
for r in sorted(kr, key=lambda r: (QORD(r["공시분기"]), r.get("항목번호", 0))):
    nm = r.get("항목명", "")
    if "CSM" in nm or "상각" in nm:
        print(f"  {r['공시분기']} item{r['항목번호']} {nm}: 값={r.get('값')} 값_당분기={r.get('값_당분기')}")
