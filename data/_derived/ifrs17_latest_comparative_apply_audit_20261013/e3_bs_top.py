import csv, re
rows = list(csv.DictReader(open("e1_bs.csv", encoding="utf-8-sig")))
txt = open("e1_bs.txt", encoding="utf-8").read()
tops = {}
for m in re.finditer(r"===== (KR\d+) (\d{4}\.\dQ) FY\d{4}_Q\d \d+: top (\[.*\])", txt):
    tops[(m.group(1), m.group(2))] = eval(m.group(3))
with open("e3_bs_top.txt", "w", encoding="utf-8") as f:
    low = 0
    for r in rows:
        t = tops[(r["code"], r["quarter"])]
        best = t[0][1] if False else t[0][1]
        top_score = t[0][1]  # tuple: (idx, score, n, scale)
        ok_top = (r["table"] == str(t[0][0]))
        if not ok_top or int(r["anchor"]) < 3:
            low += 1
            f.write(f"{r['code']} {r['quarter']} item{r['item']}: matched table {r['table']} anchor {r['anchor']} ; tops={t[:3]}\n")
    f.write(f"cells needing a second look (not top table or anchor<3): {low}\n")
