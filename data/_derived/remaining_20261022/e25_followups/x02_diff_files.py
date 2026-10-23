# -*- coding: utf-8 -*-
"""READ-ONLY structural diff of the four files the e25 applier writes, OLD root vs NEW root (each root holds the files at their repo-relative paths).
usage: x02_diff_files.py OLD_ROOT NEW_ROOT [OUT_TXT]
Checks (printed as PASS/FAIL):
  PL_breakdown.json   same row list/order and fields; the changed cells are exactly the planned 값 cells + the derived 값_당분기 cells (planned set recomputed here from e25_plan.json and the previous-quarter rule)
  user_pl_cells.json  set: planned additions appended in plan order, planned replacements in place, nothing else changed; null_dangi / set_dangi and every _doc key identical
  provenance          only blocks of the planned companies changed; every changed block listed with its old/new published_items and source_files; the new merge-note key is the only new top-level key
  test file           only the GOLD_OVERLAY_CENSUS declaration (+ its comment line) changed"""
import difflib
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
OLD, NEW = Path(sys.argv[1]), Path(sys.argv[2])
OUT = sys.argv[3] if len(sys.argv) > 3 else None
EV = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e25_followups"
plan = json.load(open(f"{EV}/e25_plan.json", encoding="utf-8"))
C = plan["apply_contract"]
lines, fails = [], []


def P(s=""):
    print(s)
    lines.append(s)


def chk(cond, msg):
    P(("PASS  " if cond else "FAIL  ") + msg)
    if not cond:
        fails.append(msg)


def J(root, rel):
    return json.loads((root / rel).read_text(encoding="utf-8"))


def key(r):
    return (r["원보험사코드"], r["항목번호"], r["공시분기"])


# ---------------------------------------------------------------- PL master
o, n = J(OLD, "PL_breakdown.json"), J(NEW, "PL_breakdown.json")
chk(len(o) == len(n) and [key(r) for r in o] == [key(r) for r in n], f"PL_breakdown.json: same {len(o)} rows in the same order")
planned_val = {(e["code"], e["item"], e["quarter"]) for e in C["gold_new"] + C["gold_replace"]} | {(e["code"], e["item"], e["quarter"]) for e in C["drift_fix"]}
other_fields = [k for r, s in zip(o, n) for k in set(r) | set(s) if k not in ("값", "값_당분기") and r.get(k) != s.get(k)]
chk(not other_fields, f"PL_breakdown.json: no field other than 값 / 값_당분기 changed ({len(other_fields)} found)")
chg_val, chg_dangi = {}, {}
for r, s in zip(o, n):
    k = key(r)
    if r.get("값") != s.get("값"):
        chg_val[k] = (r.get("값"), s.get("값"))
    if r.get("값_당분기") != s.get("값_당분기"):
        chg_dangi[k] = (r.get("값_당분기"), s.get("값_당분기"))
chk(set(chg_val) == planned_val, f"PL_breakdown.json: 값 changed on exactly the {len(planned_val)} planned cells (found {len(chg_val)}; extra {sorted(set(chg_val) - planned_val)[:5]} missing {sorted(planned_val - set(chg_val))[:5]})")


def prev_q(q):
    return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"


def explained(k):
    c, i, q = k
    return k in planned_val or (c, i, prev_q(q)) in planned_val
unexpl = [k for k in chg_dangi if not explained(k)]
chk(not unexpl, f"PL_breakdown.json: every 값_당분기 change is explained by the same cell or the previous quarter's cumulative ({len(chg_dangi)} changes; unexplained {unexpl[:5]})")
nbycode = {}
for k in list(chg_val) + [k for k in chg_dangi if k not in chg_val]:
    nbycode[k[0]] = nbycode.get(k[0], 0) + 1
P(f"  changed cells per company: {nbycode}")
# derived single quarter must equal cum - previous cum for every changed cell
rowsN = {key(r): r for r in n}
bad = []
for k, (a, b) in chg_dangi.items():
    c, i, q = k
    cur = rowsN[k]["값"]
    pq = prev_q(q)
    exp = cur if pq is None else (None if (cur is None or rowsN.get((c, i, pq), {}).get("값") is None) else round(cur - rowsN[(c, i, pq)]["값"], 6))
    if (exp is None) != (b is None) or (exp is not None and abs(exp - b) > 1e-6):
        bad.append((k, b, exp))
chk(not bad, f"PL_breakdown.json: every changed 값_당분기 equals cumulative - previous cumulative of the NEW master ({bad[:3]})")
P("  --- 값 changes (old -> new):")
for k in sorted(chg_val, key=lambda x: (x[0], x[2], x[1])):
    P(f"     {k[0]} {k[2]} item {k[1]:>2}: {chg_val[k][0]} -> {chg_val[k][1]}")
P("  --- 값_당분기 changes (old -> new), only where 값 did not change itself:")
for k in sorted((k for k in chg_dangi if k not in chg_val), key=lambda x: (x[0], x[2], x[1])):
    P(f"     {k[0]} {k[2]} item {k[1]:>2}: {chg_dangi[k][0]} -> {chg_dangi[k][1]}")

# ---------------------------------------------------------------- gold
go, gn = J(OLD, "data/_gold/user_pl_cells.json"), J(NEW, "data/_gold/user_pl_cells.json")
chk(list(go.keys()) == list(gn.keys()), "user_pl_cells.json: same top-level keys")
for kk in go:
    if kk != "set":
        chk(go[kk] == gn[kk], f"user_pl_cells.json: '{kk}' identical")
so, sn = go["set"], gn["set"]
idx_old = {(e["원보험사코드"], e["항목번호"], e["공시분기"]): i for i, e in enumerate(so)}
rep = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_replace"]}
new_keys = [(e["code"], e["item"], e["quarter"]) for e in C["gold_new"]]
chk(len(sn) == len(so) + len(new_keys), f"user_pl_cells.json: set {len(so)} -> {len(sn)} (+{len(new_keys)})")
chk([ (e["원보험사코드"], e["항목번호"], e["공시분기"]) for e in sn[len(so):]] == new_keys, "user_pl_cells.json: the new entries are appended in plan order")
same_prefix = True
for i, (a, b) in enumerate(zip(so, sn[:len(so)])):
    k = (a["원보험사코드"], a["항목번호"], a["공시분기"])
    if k in rep:
        e = rep[k]
        same_prefix &= (b["값"] == e["value"] and b["was"] == e["was"] and b["note"] == e["note"] and all(b[f] == a[f] for f in a if f not in ("값", "was", "note")))
    else:
        same_prefix &= (a == b)
chk(same_prefix, "user_pl_cells.json: every old entry unchanged except the planned in-place replacement(s)")
for e, s in zip(C["gold_new"], sn[len(so):]):
    ok = s["값"] == e["value"] and s.get("was") == e["was"] and s["note"] == e["note"]
    if not ok:
        chk(False, f"user_pl_cells.json: new entry mismatch {e['code']} {e['quarter']} item {e['item']}")
chk(True, f"user_pl_cells.json: {len(C['gold_new'])} new entries carry the planned 값 / was / note")

# ---------------------------------------------------------------- provenance
po, pn = J(OLD, "PL_breakdown_provenance.json"), J(NEW, "PL_breakdown_provenance.json")
newtop = [k for k in pn if k not in po]
chk(len(newtop) == 1 and newtop[0].startswith("merge_note_20261024"), f"provenance: exactly one new top-level key {newtop}")
chk(all(po[k] == pn[k] for k in po if k not in ("cells",)), "provenance: all old top-level keys unchanged")
bo = {(c["company_code"], c["quarter"], c["item_block"]): c for c in po["cells"]}
bn = {(c["company_code"], c["quarter"], c["item_block"]): c for c in pn["cells"]}
chk(list(bo) == list(bn), f"provenance: same {len(bo)} blocks in the same order (no insertion)")
codes = sorted({e["code"] for e in C["gold_new"] + C["gold_replace"] + C["drift_fix"]})
changed = [k for k in bo if bo[k] != bn[k]]
chk(all(k[0] in codes for k in changed), f"provenance: changed blocks belong to the planned companies only ({sorted({k[0] for k in changed})})")
P(f"  provenance blocks changed: {len(changed)}")
for k in sorted(changed):
    a, b = bo[k], bn[k]
    P(f"     {k}: published_items {a.get('published_items')} -> {b.get('published_items')} | source_file {a.get('source_file')} -> {b.get('source_file')} | owner_override {a.get('owner_override')} -> {b.get('owner_override')}")
    sa = {(f['file'], f['how']): f['items'] for f in a.get("source_files", [])}
    sb = {(f['file'], f['how']): f['items'] for f in b.get("source_files", [])}
    for kk in sorted(set(sa) | set(sb), key=str):
        if sa.get(kk) != sb.get(kk):
            P(f"         {kk[1]:22s} {kk[0][-48:]}: {sa.get(kk)} -> {sb.get(kk)}")

# ---------------------------------------------------------------- test file
to = (OLD / "tests/test_rule_coverage_manifest.py").read_text(encoding="utf-8").splitlines()
tn = (NEW / "tests/test_rule_coverage_manifest.py").read_text(encoding="utf-8").splitlines()
d = [l for l in difflib.unified_diff(to, tn, lineterm="", n=0) if not l.startswith(("---", "+++", "@@"))]
chk(len(d) <= 4 and any("GOLD_OVERLAY_CENSUS" in l for l in d), f"test file: {len(d)} changed lines, only the census declaration + comment")
for l in d:
    P("     " + l[:260])
P("\nRESULT: " + ("ALL PASS" if not fails else f"{len(fails)} FAIL"))
if OUT:
    Path(OUT).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
sys.exit(1 if fails else 0)
