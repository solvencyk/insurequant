import sys, os, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_kics import *
here = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(REPO + "/data/_derived/kics_latest_prior_apply_20261012/applied_blocks.csv", encoding="utf-8-sig")))
blocks = []
for r in rows:
    b = (r["code"], r["quarter"])
    if b not in blocks: blocks.append(b)
out = open(here + "/a4b_pages.txt", "w", encoding="utf-8")
for code, q in blocks:
    out.write(f"===== {code} {q}\n")
    for lab, n in (("own", 0), ("F+1", 1), ("F+2", 2), ("F+3", 3)):
        fq = qadd(q, n)
        if fq is None or not os.path.isdir(f"{REPO}/data/disclosure/FY{fq[:4]}_Q{fq[5]}"):
            out.write(f"  [{lab}] {fq}: no such filing dir\n"); continue
        pdfs = filing_pdfs(code, fq)
        if not pdfs: out.write(f"  [{lab}] {fq}: no pdf\n")
        for pdf in pdfs:
            doc = fitz.open(pdf)
            hp = []
            for p in range(1, len(doc) + 1):
                pg = read_page(doc, p)
                if pg: hp.append((p, pg["phase"], [h[1] for h in pg["heads"]]))
            out.write(f"  [{lab}] {fq} {os.path.basename(pdf)} ({len(doc)}pp): {len(hp)} headline page(s)\n")
            for h in hp: out.write(f"       p{h[0]} {h[1]!r} heads={h[2]}\n")
