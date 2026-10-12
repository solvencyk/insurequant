"""Independent re-read of the applied cells (field 값 = pre-transition headline table). Own PDF read; csv only supplies the cell list."""
import sys, os, csv, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_kics import *
here = os.path.dirname(os.path.abspath(__file__))
rows = list(csv.DictReader(open(REPO + "/data/_derived/kics_latest_prior_apply_20261012/applied_blocks.csv", encoding="utf-8-sig")))
cells = [r for r in rows if r["field"] == "값" and int(r["item"]) <= 26]
cache = {}
def hp(pdf):
    if pdf not in cache: cache[pdf] = headline_pages(pdf)
    return cache[pdf]
def num(t):
    if t is None: return None
    if t in DASHES: return 0.0
    return to_num(t)
def lookup(code, q, item, n):
    """print of quarter q's item in filing q+n; returns list of (pdfname, page, token, colinfo)"""
    fq = qadd(q, n)
    res = []
    if fq is None or not os.path.isdir(filing_dir(fq)): return None
    for pdf in filing_pdfs(code, fq):
        for pg in hp(pdf):
            if pg["phase"] == "post": continue
            if item not in pg["items"]: continue
            vals = pg["items"][item]
            if pg["hq"] and q in pg["hq"]:
                idx = pg["hq"].index(q)
            elif not pg["hq"]:
                idx = n
            else:
                continue
            if idx >= len(vals) or vals[idx] is None: continue
            res.append((os.path.basename(pdf), pg["page"], vals[idx], "hq" if pg["hq"] else "pos"))
    return res
out = open(here + "/a9_eval65.txt", "w", encoding="utf-8")
csvout = csv.writer(open(here + "/a9_eval65.csv", "w", encoding="utf-8-sig", newline=""))
csvout.writerow(["block", "item", "old", "new", "own_print(file p)", "F+1_print", "F+2_print", "F+3_has_Q", "verdict"])
nok = 0
for r in cells:
    code, q, item = r["code"], r["quarter"], int(r["item"])
    old, new = float(r["old"]), float(r["new"])
    prints = {}
    for lab, n in (("own", 0), ("F+1", 1), ("F+2", 2)):
        prints[lab] = lookup(code, q, item, n)
    def fmt(v):
        if v is None: return "no-filing"
        if not v: return "NOTFOUND"
        return " | ".join(f"{t}({f[:18]} p{p},{how})" for f, p, t, how in v)
    latest_n = 2 if prints["F+2"] is not None else 1
    latest = prints["F+2" if latest_n == 2 else "F+1"]
    vals_latest = sorted({num(t) for _, _, t, _ in (latest or [])})
    ok_new = bool(latest) and all(abs(v - new) < 0.51 for v in vals_latest) if latest else False
    verdict = "MATCH" if ok_new else "CHECK"
    out.write(f"{r['block_id']} item{item} old={r['old']} new={r['new']} -> latest(F+{latest_n}) {vals_latest}  {verdict}\n")
    for lab in ("own", "F+1", "F+2"):
        out.write(f"     {lab}: {fmt(prints[lab])}\n")
    csvout.writerow([r["block_id"], item, r["old"], r["new"], fmt(prints["own"]), fmt(prints["F+1"]), fmt(prints["F+2"]), "", verdict])
    nok += (verdict == "MATCH")
out.write(f"\nMATCH {nok} / {len(cells)}\n")
