import csv, sys
sys.stdout.reconfigure(encoding="utf-8")
rows = list(csv.DictReader(open(sys.argv[1], encoding="utf-8-sig")))
q = sys.argv[2]
for r in rows:
    if r["quarter"] == q:
        cite = r["raw_cite"].replace("data/dart/", "")
        print(f"{r['quarter']} item{r['item']:>2s} {r['class']:7s} old={r['old'] or 'None':>16s} new={float(r['new']):>16,.2f} flags={r['flags'] or '-':16s} | {r['source_kind'][:22]:22s} | {cite[:150]}")
