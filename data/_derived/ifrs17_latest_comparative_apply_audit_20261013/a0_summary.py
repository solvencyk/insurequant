import csv, collections, os
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
rows = list(csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")))
out = open(here + "/a0_summary.txt", "w", encoding="utf-8")
out.write(f"rows {len(rows)} cols {list(rows[0].keys())}\n")
for k in ("master", "kind", "unit"):
    out.write(f"{k}: {collections.Counter(r[k] for r in rows)}\n")
blk = collections.Counter((r["master"], r["block"], r["kind"]) for r in rows)
for k, v in sorted(blk.items()): out.write(f"  {k}: {v}\n")
out.write("source_ref kinds:\n")
c = collections.Counter((r["master"], r["kind"], r["source_ref"][:60]) for r in rows)
for k, v in sorted(c.items()): out.write(f"  {k}: {v}\n")
