"""Read-only post-processing of pdf_vs_master.csv (s111): for every MISMATCH, test the two column-confusion hypotheses against the PDF itself.

  near_prior : master ~ the PDF's printed prior-year column (2nd number of the row)         -> wrong-year / prior-column load
  near_3m    : master ~ PDF cumulative(Q) - PDF cumulative(Q-1) of the same company/FY        -> 3-month column loaded as cumulative
  (both with tolerance max(150, 1.5 %) - the PDF is in 억원)
Everything else is a plain level difference (감독회계 vs 재무제표 basis / restated vintage / own-vs-amended PDF) and is NOT a column confusion.
Output pdf_classified.csv, printed summary of the candidates.
"""
import csv
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
HERE = Path(__file__).resolve().parent
rows = list(csv.DictReader(open(HERE / "pdf_vs_master.csv", encoding="utf-8-sig")))


def num(t):
    t = (t or "").strip().replace(",", "").replace("+", "")
    neg = (t.startswith("(") and t.endswith(")")) or t.startswith("-") or t.startswith("△")
    t = t.strip("()-△")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def toks_of(detail):
    m = re.search(r"\[(.*?)\]", detail)
    if not m:
        return []
    return [x.strip().strip("'") for x in m.group(1).split(",")]


cur = {}
prior = {}
for r in rows:
    if r["item"] == "" or r["cls"] not in ("MATCH", "MISMATCH"):
        continue
    it = int(r["item"])
    tk = toks_of(r["detail"])
    c1 = num(tk[0]) if tk else None
    c2 = num(tk[1]) if len(tk) > 1 else None
    key = (r["code"], r["quarter"], it)
    cur[key] = c1 * 100 if c1 is not None else None
    prior[key] = c2 * 100 if c2 is not None else None


def prevq(q):
    y, n = int(q[:4]), int(q[5])
    return None if n == 1 else f"{y}.{n - 1}Q"


out = []
for r in rows:
    if r["cls"] != "MISMATCH":
        continue
    it = int(r["item"])
    m = float(r["master"])
    ma = abs(m) if it in (16, 23) else m
    key = (r["code"], r["quarter"], it)
    tol = max(150.0, 0.015 * abs(ma))
    c1, c2 = cur.get(key), prior.get(key)
    sg = (lambda v: abs(v)) if it in (16, 23) else (lambda v: v)
    near_prior = c2 is not None and abs(ma - sg(c2)) <= tol
    near_3m = False
    p = prevq(r["quarter"])
    three_m = None
    if p and c1 is not None and cur.get((r["code"], p, it)) is not None:
        three_m = sg(c1) - sg(cur[(r["code"], p, it)])
        near_3m = abs(ma - three_m) <= tol
    out.append({**{k: r[k] for k in ("code", "name", "quarter", "item", "master", "printed_cur", "diff")}, "near_prior": near_prior, "near_3m": near_3m,
                "pdf_3m": "" if three_m is None else round(three_m, 1), "detail": r["detail"][:120]})
with open(HERE / "pdf_classified.csv", "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0].keys()))
    w.writeheader()
    w.writerows(out)
print("MISMATCH rows:", len(out), "| near_prior:", sum(o["near_prior"] for o in out), "| near_3m:", sum(o["near_3m"] for o in out))
print("--- candidates (near_prior or near_3m):")
for o in out:
    if (o["near_prior"] or o["near_3m"]) and int(o["item"]) in (16, 22, 23, 24):
        print(o["code"], o["name"][:7], o["quarter"], "item", o["item"], "master", o["master"], "pdf_cur", o["printed_cur"], "pdf_3m", o["pdf_3m"], "prior" if o["near_prior"] else "", "3M" if o["near_3m"] else "", "|", o["detail"][:80])
print("--- other items (1/17/20/21) candidates:")
for o in out:
    if (o["near_prior"] or o["near_3m"]) and int(o["item"]) not in (16, 22, 23, 24):
        print(o["code"], o["name"][:7], o["quarter"], "item", o["item"], "master", o["master"], "pdf_cur", o["printed_cur"], "pdf_3m", o["pdf_3m"], "prior" if o["near_prior"] else "", "3M" if o["near_3m"] else "")
