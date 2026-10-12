import csv, collections, os
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
rows = [r for r in csv.DictReader(open(src + "pdf_scan_final.csv", encoding="utf-8-sig")) if r["final_class"] in ("NOLABEL", "NONE")]
out = open(here + "/h2_undecided.txt", "w", encoding="utf-8")
out.write(f"{len(rows)} undecided\n")
c = collections.Counter((r["code"], r["name"]) for r in rows)
out.write(str(c) + "\n")
c2 = collections.Counter((r["quarter"]) for r in rows); out.write(str(c2) + "\n")
c3 = collections.Counter((r["item"]) for r in rows); out.write(str(c3) + "\n")
for r in rows: out.write(f"{r['code']} {r['quarter']} i{r['item']} master={r['master']} own={r['own_filing_pdf']} {r['final_class']} pdf={r['pdf'].split('/')[-3:]} detail={r['detail'][:80]}\n")
