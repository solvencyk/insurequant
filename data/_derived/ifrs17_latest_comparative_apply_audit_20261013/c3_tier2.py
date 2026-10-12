"""Tier-2 verification of applied PL cells via current-period calibration. usage: c3_tier2.py KR0008"""
import sys, os, csv, re, json, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib_tier2 import *
here = os.path.dirname(os.path.abspath(__file__))
src = os.path.dirname(here) + "/ifrs17_latest_comparative_apply_20261012/"
code = sys.argv[1]
master = {}
for r in json.load(open(REPO + "/PL_breakdown.json", encoding="utf-8")):
    master[(r["원보험사코드"], r["공시분기"], r["항목번호"])] = r
def mval(q, it):
    r = master.get((code, q, it))
    try: return float(r["값"])
    except Exception: return None
applied = [r for r in csv.DictReader(open(src + "applied_cells.csv", encoding="utf-8-sig")) if r["master"] == "PL_breakdown" and r["code"] == code and r["kind"] == "latest_comparative" and 2 <= int(r["item"]) <= 14]
new = {(r["quarter"], int(r["item"])): float(r["new"]) for r in applied}
fil = {}
for r in applied:
    m = re.search(r"later filing (FY\d{4}_Q\d)", r["source_ref"]) or re.search(r"\((FY\d{4}_Q\d)\)", r["source_ref"])
    fil[r["quarter"]] = m.group(1)
# the filing folder for this company/quarter (use the same rcept as the tier-1 cells of the block when available)
def xml_for(fyq):
    ps = find_xml(code, fyq)
    return ps[0] if len(ps) == 1 else ps[0]
out = open(here + f"/c3_tier2_{code}.txt", "w", encoding="utf-8")
SPEC = {3: ("장기", 2), 4: ("장기", 1), 5: ("장기", 1), 6: ("장기", 3), 8: ("장기", 2), 9: ("장기", 2), 10: ("장기", 2), 11: ("장기", 3), 13: ("자동차", 4), 14: ("일반", 4)}
cur_of = {"2023.1Q": "2024.1Q", "2023.2Q": "2024.2Q", "2023.3Q": "2024.3Q"}
filings = {q: fil[q] for q in cur_of if q in fil}
data = {}
for q, fyq in filings.items():
    nts = note_tables(xml_for(fyq))
    ty = pairs(nts)
    # sections: split by idx gap
    secs = []; cur = []
    for t in ty:
        if cur and t[0]["idx"] - cur[-1][0]["idx"] > 60: secs.append(cur); cur = []
        cur.append(t)
    if cur: secs.append(cur)
    data[q] = secs
    out.write(f"{q} {fyq}: sections {[ [ (t[0]['idx'], t[1]['idx'] if t[1] else None) for t in s] for s in secs]}\n")
# per section index, discover recipes using each available filing's current calibration
nsec = min(len(data[q]) for q in data)
for si in range(nsec):
    out.write(f"--- section {si}\n")
    for it, (col, mt) in SPEC.items():
        per = []
        for q in data:
            sec = data[q][si]
            # restrict to pairs (cur,prior) complete
            tgt = mval(cur_of[q], it)
            if tgt is None: continue
            rs = recipe_search(sec, tgt, col, maxterms=mt, allowed=(r'^(합계|소계)$' if it in (13, 14) else None))
            per.append((q, set(rs), sec))
        if not per: continue
        common = set.intersection(*[p[1] for p in per]) if per else set()
        out.write(f" item{it} calib cur masters {[mval(cur_of[q], it) for q in data]} recipes/filing {[len(p[1]) for p in per]} common {len(common)}\n")
        for rc in list(common)[:3]:
            vals = {}
            for q, _, sec in per:
                vals[q] = eval_recipe(sec, rc, col, 1)
            out.write(f"     recipe {[(k, s) for k, s in rc]} -> prior {vals} | plan {[new.get((q, it)) for q in vals]}\n")
