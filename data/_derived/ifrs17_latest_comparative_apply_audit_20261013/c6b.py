import csv
rows = list(csv.DictReader(open("c6_kr0011_t2.csv", encoding="utf-8-sig")))
with open("c6b.txt", "w", encoding="utf-8") as f:
    for r in rows:
        d = abs(float(r["mine(prior col recipe)"]) - float(r["post-apply master"]))
        if d > 0.5: f.write(f"{r['quarter']} item{r['item']} mine={r['mine(prior col recipe)']} master={r['post-apply master']} applied={r['applied_new']} diff={d}\n")
