import csv, collections, os
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
rows = list(csv.DictReader(open(src + "pdf_scan_final.csv", encoding="utf-8-sig")))
out = open(here + "/h1_pdfscan.txt", "w", encoding="utf-8")
out.write(f"cols {list(rows[0].keys())}\n")
for k in rows[0].keys():
    if k in ("code", "name", "detail", "master", "printed", "pdf"): continue
    c = collections.Counter(r[k] for r in rows)
    if len(c) < 15: out.write(f"{k}: {dict(c)}\n")
