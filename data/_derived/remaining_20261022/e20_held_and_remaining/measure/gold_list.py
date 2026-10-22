import json, sys, csv
sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M
sys.stdout.reconfigure(encoding="utf-8")
rows = []
for scn in sys.argv[1:]:
    d = json.loads((M.MEASURE / f"cands_{scn}.json").read_text(encoding="utf-8"))
    for kind, cells in (("PL", d["pl_cells"]), ("CSM", d["csm_cells"])):
        for c in cells:
            if c.get("gold") is not None:
                rows.append({"scenario": scn, "sheet": kind, "code": c["code"], "quarter": c["q"], "item": c["item"], "gold_value": c["gold"], "gold_was_builder": c.get("gold_was"), "candidate_new": c["new"], "master_old": c["old"]})
with open(M.MEASURE / "gold_cells_replaced.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader(); w.writerows(rows)
from collections import Counter
print(len(rows), Counter((r["scenario"], r["sheet"]) for r in rows))
for r in rows:
    print(f"{r['scenario']:<18} {r['sheet']:<3} {r['code']} {r['quarter']} item{r['item']:>2} gold={r['gold_value']} (builder was {r['gold_was_builder']}) -> {r['candidate_new']}")
