"""Read-only: ILP master (KR0073, items 10/13/14/15, 억원) vs own-filing reading and vs latest comparative reading (prior-period table of the same quarter one year later)."""
import json, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
D = ROOT / "data/_derived/remaining_20261022/b_bs_ilp"
sys.stdout.reconfigure(encoding="utf-8")
R = json.loads((D / "s9_ilp_all.json").read_text(encoding="utf-8"))
ilp = json.loads((ROOT / "insurance_liability_portfolio.json").read_text(encoding="utf-8"))
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
M = {(r["공시분기"], r["항목번호"]): r["값"] for r in ilp if r["원보험사코드"] == "KR0073"}
B20 = {r["공시분기"]: r["값"] for r in bs if r["원보험사코드"] == "KR0073" and r["항목번호"] == 20}
QS = sorted({q for q, _ in M}, key=lambda q: (int(q[:4]), int(q[5])))
def fy_of(q): return f"FY{q[:4]}_Q{q[5]}"
def later(q):
    y, n = int(q[:4]), int(q[5]); return f"FY{y+1}_Q{n}"
rows = []; lines = []
lines.append("quarter  item  master          own_cur(ILP engine)   latest_comparative(filing)        diff(master->latest)   BS20/100(master)")
for q in QS:
    own = R.get(f"{fy_of(q)}|cur", {})
    lt = later(q); comp = R.get(f"{lt}|prior")
    for it, key in ((10, "lic"), (13, "lic"), (14, "lrc"), (15, "total")):
        m = M.get((q, it))
        if m is None: continue
        o = own.get(key); c = comp.get(key) if comp else None
        diff = None if c is None else round(c - m, 2)
        rows.append({"quarter": q, "item": it, "master": m, "own_filing_reading": o, "latest_comparative": c, "latest_filing": lt if c is not None else None, "diff": diff})
        lines.append(f"{q}  {it:>3}  {m:>14,.2f}  {('%.2f' % o) if o is not None else '-':>14}   {('%.2f' % c) if c is not None else '-':>14} ({lt if c is not None else '-'})  {('%+.2f' % diff) if diff is not None else '-':>12}   {B20.get(q, 0)/100:,.2f}")
(D / "s13_ilp_compare.txt").write_text("\n".join(lines), encoding="utf-8")
(D / "s13_ilp_compare.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
print("\n".join(lines))
