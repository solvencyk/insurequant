"""Read-only: item 6 (예실차) / item 7 under the default reader vs the alternate row label, original vs restated vintage."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
alt = json.loads((HERE / "restated_blocks_alt.json").read_text(encoding="utf-8"))
root = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
cur = {}
for r in root:
    if r["원보험사코드"] == "KR0073":
        cur.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")
QORD = lambda q: int(q[:4]) * 10 + int(q[5])
f = lambda v: "None" if v is None else f"{v:,.2f}"

print("=== original vintage (production mode, current column) — convention check")
for q, rec in sorted(alt["_orig"].items()):
    b, ba = rec["block"], rec["block_alt"]
    print(f"{q}: master item6={f(cur[q].get(6))} item7={f(cur[q].get(7))} | harness default item6={f(b.get('6'))} item7={f(b.get('7'))} | alt-label item6={f(ba.get('6'))} item7={f(ba.get('7'))}")
    print(f"      rev rows {rec['rev_rows']}")
    print(f"      cost rows {rec['cost_rows']}")
print()
print("=== restated vintage (prior cumulative column of the later filing)")
for q in sorted((k for k in alt if not k.startswith("_")), key=QORD):
    rec = alt[q]
    b, ba = rec["restated"], rec["restated_alt"]
    print(f"{q} (from {rec['later']}): master item6={f(cur[q].get(6))} item7={f(cur[q].get(7))} | default item6={f(b.get('6'))} item7={f(b.get('7'))} | alt-label item6={f(ba.get('6'))} item7={f(ba.get('7'))}")
    print(f"      rev rows  {rec['rev_rows']}")
    print(f"      cost rows {rec['cost_rows']}")
print()
print("=== restated 2024.4Q vs master (corp-code fix)")
b = alt["2024.4Q"]["restated"]
diff = [(i, cur["2024.4Q"].get(i), b.get(str(i))) for i in range(1, 33)
        if not ((cur["2024.4Q"].get(i) is None and b.get(str(i)) is None) or (cur["2024.4Q"].get(i) is not None and b.get(str(i)) is not None and abs(cur["2024.4Q"][i] - b[str(i)]) <= 5e-4))]
print("differing items:", [(i, f(o), f(n)) for i, o, n in diff])
print("t1 source:", alt["2024.4Q"]["t1_src"])
