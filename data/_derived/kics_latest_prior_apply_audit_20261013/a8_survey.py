import sys, os, csv, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_kics import *
here = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(REPO + "/data/_derived/kics_latest_prior_apply_20261012/applied_blocks.csv", encoding="utf-8-sig")))
blocks = []
for r in rows:
    b = (r["code"], r["quarter"])
    if b not in blocks: blocks.append(b)
out = open(here + "/a8_survey.txt", "w", encoding="utf-8")
cache = {}
for code, q in blocks:
    out.write(f"===== {code} {q}\n")
    for lab, n in (("own", 0), ("F+1", 1), ("F+2", 2), ("F+3", 3)):
        fq = qadd(q, n)
        if fq is None or not os.path.isdir(filing_dir(fq)):
            out.write(f"  [{lab}] {fq}: no filing dir\n"); continue
        for pdf in filing_pdfs(code, fq):
            if pdf not in cache: cache[pdf] = headline_pages(pdf)
            hp = cache[pdf]
            out.write(f"  [{lab}] {fq} {os.path.basename(pdf)}: " + ", ".join(f"p{p['page']}({p['phase']},cols={p['ncols']},hq={p['hq']},items={len(p['items'])})" for p in hp) + "\n")
