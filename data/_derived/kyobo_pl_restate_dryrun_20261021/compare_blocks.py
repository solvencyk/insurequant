"""Read-only: compare restated blocks (restated_blocks.json) with the live PL master, and the harness reproduction with the live master.

Prints per quarter a 32-item table: current root 값, restated 값, delta, class (SAME / CHANGED / FILL / LOST / BOTH_NONE).
Writes pl_compare.json (machine-readable) for the later steps.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
sys.stdout.reconfigure(encoding="utf-8")
TOL = 5e-4          # 백만원 (builder rounds to 6 decimals; FS-API is exact to 1e-6)
QORD = lambda q: int(q[:4]) * 10 + int(q[5])

res = json.loads((HERE / "restated_blocks.json").read_text(encoding="utf-8"))
root = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
names, cur = {}, {}
for r in root:
    if r["원보험사코드"] == "KR0073":
        names[r["항목번호"]] = r["항목명"]
        cur.setdefault(r["공시분기"], {})[r["항목번호"]] = r.get("값")


def classify(old, new):
    if old is None and new is None:
        return "BOTH_NONE"
    if old is None:
        return "FILL"
    if new is None:
        return "LOST"
    return "SAME" if abs(old - new) <= TOL else "CHANGED"


def fmt(v):
    return "None" if v is None else f"{v:,.2f}"


summary = {}
out = {}
print("=== A. harness fidelity: production-mode block of the later filing vs live master (same quarter)")
for later, rec in sorted(res["_production_reproduction"].items(), key=lambda x: QORD(x[0])):
    blk = rec["block"]
    diffs = []
    for i in range(1, 33):
        c = classify(cur.get(later, {}).get(i), blk.get(str(i)) if str(i) in blk else blk.get(i))
        if c not in ("SAME", "BOTH_NONE"):
            diffs.append((i, c, cur.get(later, {}).get(i), blk.get(str(i))))
    print(f"  {later}: {32 - len(diffs)}/32 items equal; differing: " + "; ".join(f"item{i} {c} master={fmt(a)} harness={fmt(b)}" for i, c, a, b in diffs[:8]) + (" ..." if len(diffs) > 8 else ""))
print()
print("=== B. restated (latest comparative) block vs live master")
for q in sorted((k for k in res if not k.startswith("_")), key=QORD):
    rb = res[q]["restated"]
    rows = []
    cnt = {"SAME": 0, "CHANGED": 0, "FILL": 0, "LOST": 0, "BOTH_NONE": 0}
    for i in range(1, 33):
        old = cur.get(q, {}).get(i)
        new = rb.get(str(i))
        c = classify(old, new)
        cnt[c] += 1
        rows.append({"item": i, "name": names.get(i), "old": old, "new": new, "cls": c})
    out[q] = {"later": res[q]["later"], "counts": cnt, "rows": rows, "reconciled": rb.get("_reconciled"), "t1_src": res[q]["t1_src"]}
    print(f"--- {q}  (from filing {res[q]['later']}, Tier-1 {res[q]['t1_src']}, reconciled={rb.get('_reconciled')})  {cnt}")
    for r in rows:
        if r["cls"] in ("CHANGED", "FILL", "LOST"):
            d = "" if r["old"] is None or r["new"] is None else f"  delta {r['new'] - r['old']:+,.2f}"
            print(f"    item{r['item']:2d} {str(r['name'])[:18]:18s} {r['cls']:7s} old={fmt(r['old']):>16s} new={fmt(r['new']):>16s}{d}")
(HERE / "pl_compare.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
