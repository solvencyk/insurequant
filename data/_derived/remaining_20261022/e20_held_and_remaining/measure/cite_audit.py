import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
for scn in sys.argv[1:]:
    rows = list(csv.DictReader(open(f"ready_cells_{scn}.csv", encoding="utf-8-sig")))
    miss = [r for r in rows if not r["cite(label|line|text)"]]
    from collections import Counter
    print(scn, "cells", len(rows), "no-line", len(miss), Counter(r["item"] for r in miss).most_common(12))
    for r in miss[:0]:
        print(r["code"], r["quarter"], r["item"], r["how"])
