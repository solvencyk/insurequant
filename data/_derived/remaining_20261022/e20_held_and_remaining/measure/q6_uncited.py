import csv, sys
from collections import Counter
sys.stdout.reconfigure(encoding="utf-8")
M = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure/"
rows = [r for r in csv.DictReader(open(M + "ready_cells_ALL.csv", encoding="utf-8-sig")) if r["sheet"] == "PL" and not r["cite(label|line|text)"]]
print(len(rows))
print(Counter(r["how"] for r in rows).most_common())
print(Counter((r["code"], r["item"]) for r in rows).most_common(60))
