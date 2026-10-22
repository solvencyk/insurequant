"""Read-only: Kyobo ROE on compare.html (avg of prior-4Q equity and current equity) with master BS vs with the proposed 2023.4Q / 2024.4Q cells."""
import json, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
E = {r["공시분기"]: r["값"] for r in bs if r["원보험사코드"] == "KR0073" and r["항목번호"] == 3}
NI = {r["공시분기"]: r["값"] for r in pl if r["원보험사코드"] == "KR0073" and r["항목번호"] == 24}
E2 = dict(E); E2["2023.4Q"] = 9975755.359695          # FY2024 annual 제67기 column
panel = json.loads((ROOT / "data/compare/panel_compare.json").read_text(encoding="utf-8"))
print([k for k in panel.keys()][:10])
roe_screen = None
for m in panel.get("metrics", []):
    if m.get("id") == "roe":
        roe_screen = m
print("panel metric keys", list(roe_screen.keys()) if roe_screen else None)
lines = ["quarter  NI_ytd(mn)  E_prev4Q  E_cur   ROE_master  ROE_with_2023.4Q_restated  delta_pp"]
res = {}
for q in ["2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q"]:
    y, n = int(q[:4]), int(q[5])
    ni = NI.get(q)
    if ni is None: continue
    def roe(Ed):
        e0, e1 = Ed.get(f"{y-1}.4Q"), Ed.get(q)
        return ni * 4.0 / n / ((e0 + e1) / 2.0) * 100.0
    a, b = roe(E), roe(E2)
    res[q] = (round(a, 3), round(b, 3))
    lines.append(f"{q}  {ni:,.1f}  {E.get(f'{y-1}.4Q'):,.1f}  {E.get(q):,.1f}  {a:.2f}  {b:.2f}  {b-a:+.2f}")
print("\n".join(lines))
(ROOT / "data/_derived/remaining_20261022/b_bs_ilp/s17_roe_impact.txt").write_text("\n".join(lines), encoding="utf-8")
# screen values
if roe_screen:
    co = roe_screen.get("v", {}).get("KR0073")
    qs = panel.get("quarters") or panel.get("meta", {}).get("quarters")
    if co and qs: print("panel ROE KR0073:", {q: (None if v is None else round(v, 3)) for q, v in zip(qs, co)})
