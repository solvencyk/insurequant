"""a3: for every changed cell of the 26 candidate blocks print master / own-filing / F+1 prev col / F+2 prev2 col (READ-ONLY)."""
import csv, io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
D = "data/_derived/kics_latest_prior_precedence_dryrun_20261012/"
core = json.load(open(D + "core_extract_all.json", encoding="utf-8"))
rows = list(csv.DictReader(open(D + "block_verdicts.csv", encoding="utf-8-sig")))
cand = [r for r in rows if r["ticket_category"] == "채택 후보"]
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
def qadd(q, n):
    i = QS.index(q) + n
    return QS[i] if 0 <= i < len(QS) else None
def per(q): return f"FY{q[:4]}_Q{q[5]}"
def get(code, q_filing, col, item):
    rec = core.get(f"{per(q_filing)}|{code}")
    if not rec: return "NOREC"
    if rec["status"] not in ("OK", "VISION_ONLY"): return rec["status"]
    v = rec["cols"].get(col, {}).get(str(item))
    if v is None: return "-"
    return v[0]
def pages(code, q_filing):
    rec = core.get(f"{per(q_filing)}|{code}")
    return None if not rec else (rec["pdf"].split("/")[-1], rec.get("pages"))
for r in cand:
    code, q = r["code"], r["quarter"]
    plan = json.load(open(D + "plans/" + r["id"] + ".json", encoding="utf-8"))
    items = sorted({e["item"] for e in plan["edits"]})
    q1, q2 = qadd(q, 1), qadd(q, 2)
    print(f"{r['id']} {r['company']}  own-filing={pages(code, q)}  F+1({q1})={pages(code, q1) if q1 else None}  F+2({q2})={pages(code, q2) if q2 else None}")
    for it in items:
        e = [x for x in plan["edits"] if x["item"] == it and x["field"] == "값"][0]
        print(f"    item{it:>2}  master={e['old']!s:>9}  own(cur)={get(code,q,'cur',it)!s:>9}  F+1(prev)={get(code,q1,'prev',it) if q1 else 'NA'!s:>9}  F+2(prev2)={get(code,q2,'prev2',it) if q2 else 'NA'!s:>9}  -> new={e['new']}")
