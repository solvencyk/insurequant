"""Read-only: KR0073 PL_breakdown.json 32-item YTD vectors per quarter, builder output vs root, PL gold overlay and provenance.

Usage: python dump_pl_kr0073.py [out_txt]
"""
import json
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
CODE = "KR0073"
QORD = lambda q: int(q[:4]) * 10 + int(q[5])
out_lines = []


def emit(s=""):
    out_lines.append(s)
    print(s)


root = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
bld = json.loads((ROOT / "data/dart/viz/pl_breakdown_master.json").read_text(encoding="utf-8"))
gold = json.loads((ROOT / "data/_gold/user_pl_cells.json").read_text(encoding="utf-8"))
prov = json.loads((ROOT / "PL_breakdown_provenance.json").read_text(encoding="utf-8"))

R = {}
for r in root:
    if r["원보험사코드"] == CODE:
        R.setdefault(r["공시분기"], {})[r["항목번호"]] = (r.get("값"), r.get("값_당분기"), r.get("항목명"))
B = {}
for r in bld:
    if r["원보험사코드"] == CODE:
        B.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
G = {}
for e in gold.get("set", []):
    if e.get("원보험사코드") == CODE:
        G[(e["공시분기"], e["항목번호"])] = e

names = {i: R["2023.1Q"][i][2] for i in range(1, 33) if i in R.get("2023.1Q", {})}
qs = [q for q in sorted(R, key=QORD) if QORD(q) <= 20242]
emit(f"quarters in scope: {qs}")
emit("")
emit("== root PL_breakdown.json YTD 값 (백만원); '*' = a PL gold overlay cell exists for it; '~' = root != builder output pl_breakdown_master.json")
hdr = "item name".ljust(26) + "".join(q.rjust(14) for q in qs)
emit(hdr)
for i in range(1, 33):
    row = f"{i:2d} {names.get(i, '')[:22]}".ljust(26)
    for q in qs:
        v = R.get(q, {}).get(i, (None,))[0]
        flag = ("*" if (q, i) in G else "") + ("~" if (B.get(q, {}).get(i) != v) else "")
        row += (("None" if v is None else f"{v:,.1f}") + flag).rjust(14)
    emit(row)
emit("")
emit("== KR0073 PL gold overlay cells (data/_gold/user_pl_cells.json)")
for (q, i), e in sorted(G.items(), key=lambda x: (QORD(x[0][0]), x[0][1])):
    emit(f"   {q} item{i}: 값={e.get('값')} was={e.get('was')} note/why={str(e.get('note') or e.get('why'))[:110]}")
emit("")
emit("== provenance cells for KR0073 (PL_breakdown_provenance.json)")
for c in prov["cells"]:
    if c["company_code"] == CODE and QORD(c["quarter"]) <= 20242:
        emit("   " + json.dumps(c, ensure_ascii=False)[:420])
if len(sys.argv) > 1:
    Path(sys.argv[1]).write_text("\n".join(out_lines) + "\n", encoding="utf-8", newline="\n")
