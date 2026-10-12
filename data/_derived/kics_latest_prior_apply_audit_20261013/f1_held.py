import sys, os, csv, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_kics import *
here = os.path.dirname(os.path.abspath(__file__))
master = {}
for r in json.load(open(REPO + "/kics_disclosure.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
HELD = [("KR0070","2024.3Q",[22]),("KR0050","2023.1Q",[18]),("KR0051","2023.3Q",[11]),("KR0069","2023.2Q",[11,12]),("KR0069","2024.3Q",[23]),
        ("KR0083","2025.2Q",[4,7]),("KR0095","2024.3Q",[7]),("KR0099","2024.2Q",[22]),("KR0099","2024.4Q",[22]),("KR0100","2025.2Q",[5,11])]
cache = {}
def hp(pdf):
    if pdf not in cache: cache[pdf] = headline_pages(pdf)
    return cache[pdf]
def lookup(code, q, item, n):
    fq = qadd(q, n)
    if fq is None or not os.path.isdir(filing_dir(fq)): return "no-filing"
    res = []
    for pdf in filing_pdfs(code, fq):
        for pg in hp(pdf):
            if pg["phase"] == "post" or item not in pg["items"]: continue
            vals = pg["items"][item]
            if pg["hq"] and q in pg["hq"]: idx = pg["hq"].index(q)
            elif not pg["hq"]: idx = n
            else: continue
            if idx >= len(vals) or vals[idx] is None: continue
            res.append(f"{vals[idx]} [{os.path.basename(pdf)[:22]} p{pg['page']}{'' if pg['hq'] else ' pos'}]")
    return " | ".join(res) if res else "NOTFOUND"
out = open(here + "/f1_held.txt", "w", encoding="utf-8")
for code, q, items in HELD:
    out.write(f"===== {code} {q}\n")
    for it in items:
        m = master.get((code, q, it))
        out.write(f"  item{it} master_now pre={m.get('값') if m else None} post={m.get('값_적용후') if m else None}\n")
        for lab, n in (("own", 0), ("F+1", 1), ("F+2", 2)):
            out.write(f"     {lab}: {lookup(code, q, it, n)}\n")
