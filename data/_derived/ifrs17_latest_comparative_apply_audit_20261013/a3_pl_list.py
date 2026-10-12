import csv, os
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
rows = [r for r in csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")) if r["master"] != "IFRS17_BS"]
out = open(here + "/a3_pl_list.txt", "w", encoding="utf-8")
for r in rows:
    out.write(f"{r['master'][:3]} {r['code']} {r['quarter']} i{r['item']} {r['item_name']} {r['unit']} {r['old']} -> {r['new']} [{r['kind'][:6]}] {r['source_ref'][:100]}\n")
