"""Read-only: IFRS17_BS.json KR0073 items per quarter (equity, AOCI), next to PL item 24/25 (live and candidate)."""
import json, sys
from pathlib import Path
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant"); HERE = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
cand = json.loads((HERE / "sim/cand_pl.json").read_text(encoding="utf-8"))
QORD = lambda q: int(q[:4]) * 10 + int(q[5])
names, B = {}, {}
for r in bs:
    if r["원보험사코드"] == "KR0073":
        names[r["항목번호"]] = r["항목명"]; B.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
print("BS items:", {k: v for k, v in sorted(names.items())})
def pv(rows):
    d = {}
    for r in rows:
        if r["원보험사코드"] == "KR0073" and r["항목번호"] in (24, 25):
            d.setdefault(r["공시분기"], {})[r["항목번호"]] = (r.get("값"), r.get("값_당분기"))
    return d
P0, P1 = pv(pl), pv(cand)
f = lambda v: "None" if v is None else f"{v:,.0f}"
print(f"{'q':8s} {'BS자본(3)':>14s} {'BS AOCI(4)':>14s} | PL24 YTD old/new | PL25 YTD old/new | PL25 당분기 old/new")
for q in sorted(B, key=QORD):
    if QORD(q) > 20252: continue
    a, b = P0.get(q, {}), P1.get(q, {})
    print(f"{q:8s} {f(B[q].get(3)):>14s} {f(B[q].get(4)):>14s} | {f(a.get(24,(None,))[0])}/{f(b.get(24,(None,))[0])} | {f(a.get(25,(None,))[0])}/{f(b.get(25,(None,))[0])} | {f(a.get(25,(None,None))[1])}/{f(b.get(25,(None,None))[1])}")
