"""Read-only: AOCI series (IFRS17_BS item 4) master vs SOCE-restated (later filing prior-year column) vs PL OCI single quarter (PL item 25 값_당분기)."""
import json, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
A = {r["공시분기"]: r["값"] for r in bs if r["원보험사코드"] == "KR0073" and r["항목번호"] == 4}
OCI = {r["공시분기"]: r.get("값_당분기") for r in pl if r["원보험사코드"] == "KR0073" and r["항목번호"] == 25}
# restated AOCI at quarter end (million won), printed in the SOCE prior-year column of the following year's filing (separate statement); source line in comments
R = {
 "2022.4Q*": 2591806.661085,   # FY2024_Q3 SOCE L38088 기초자본(변경후) 2023.01.01 (policy-change basis; FY2024_Q1/Q2 same 2,591,806.661085)
 "2023.1Q": 2028147.851069,    # FY2024_Q1 SOCE L36934
 "2023.2Q": 2188202.559965,    # FY2024_Q2 SOCE L40072
 "2023.3Q": 2135572.607360,    # FY2024_Q3 SOCE L38739
 "2023.4Q": 1670167.445676,    # FY2024_Q4 SOCE L53156
 "2024.1Q": 354872.139601,     # FY2025_Q1 SOCE L35906
 "2024.2Q": -1005746.644036,   # FY2025_Q2 SOCE L38929
 "2024.3Q": -1411756.365928,   # FY2025_Q3 SOCE L32451
 "2024.4Q": -2204529.204683,   # FY2025_Q4 BS L46757
 "2025.1Q": -3147529.446039,   # FY2026_Q1 SOCE L34265
 "2025.2Q": -3129858.437041,   # FY2026_Q2 SOCE L32013
}
order = ["2022.4Q*", "2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q", "2024.1Q", "2024.2Q", "2024.3Q", "2024.4Q", "2025.1Q", "2025.2Q"]
print("q  AOCI_master  AOCI_restated  d_master  d_restated  PL25_dangi  resid_master  resid_restated")
lines = []
for i in range(1, len(order)):
    q, p = order[i], order[i - 1]
    am, ap = A.get(q), A.get(p)
    dm = None if am is None or ap is None else am - ap
    dr = R[q] - R[p]
    o = OCI.get(q)
    lines.append(f"{q}  {am:,.1f}  {R[q]:,.1f}  {('%.1f' % dm) if dm is not None else '-'}  {dr:,.1f}  {('%.1f' % o) if o is not None else '-'}  {('%.1f' % (dm - o)) if dm is not None and o is not None else '-'}  {('%.1f' % (dr - o)) if o is not None else '-'}")
print("\n".join(lines))
(ROOT / "data/_derived/remaining_20261022/b_bs_ilp/s20_aoci_tie.txt").write_text("\n".join(lines), encoding="utf-8")
