import csv, os
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
rows = [r for r in csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")) if r["master"] == "IFRS17_BS"]
out = open(here + "/a1_bs_list.txt", "w", encoding="utf-8")
for r in rows:
    out.write(f"{r['code']} {r['company']} {r['quarter']} item{r['item']} {r['item_name']} {r['old']} -> {r['new']} | {r['source_ref'][:140]} | {r['printed'][:120]}\n")
