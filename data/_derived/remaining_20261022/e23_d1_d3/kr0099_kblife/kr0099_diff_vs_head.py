# -*- coding: utf-8 -*-
"""Read-only, independent of the applier: cell-level diff of every file the KB라이프 D1-B load writes vs git HEAD (d5077c7b + nothing else).
Asserts: PL master changed rows only of KR0099, only fields 값 / 값_당분기; 값 changes == the 60 plan cells with plan values and plan 'was' values; every other 값_당분기 change is a derived cumulative
difference; CSM master the same (15 cells); gold: appended entries == plan, nothing existing touched, null_dangi / set_dangi untouched; ledger byte-equal; provenance: only KR0099 blocks + merge note
keys; test file: only the census declaration (+ comment) and the TAX22 lines.  Writes kr0099_diff_vs_head.txt next to this file."""
import difflib
import json
import subprocess
import sys
from pathlib import Path

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((OUT / "e23_plan_kblife.json").read_text(encoding="utf-8"))
C = PLAN["apply_contract"]
CODE = PLAN["code"]


def head(rel):
    return subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout


def live(rel):
    return open(f"{ROOT}/{rel}", "rb").read().replace(b"\r\n", b"\n")   # working tree is CRLF (core.autocrlf=true), git blobs are LF


out, ok = [], True


def chk(name, cond, extra=""):
    global ok
    ok = ok and bool(cond)
    out.append(f"[{'PASS' if cond else 'FAIL'}] {name} {extra}")


key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])  # noqa: E731


def prevq(q):
    return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"


# ------------------------------------------------------------------------------------------------ PL master
h = json.loads(head("PL_breakdown.json").decode("utf-8"))
l = json.loads(live("PL_breakdown.json").decode("utf-8"))
chk("PL rows count equal and same key order", len(h) == len(l) and [key(r) for r in h] == [key(r) for r in l], f"({len(h)} rows)")
hm, lm = {key(r): r for r in h}, {key(r): r for r in l}
chg_val, chg_dangi, other_field, outside = [], [], [], []
for k in lm:
    a, b = hm[k], lm[k]
    if a == b:
        continue
    if k[0] != CODE:
        outside.append(k)
    for f in set(a) | set(b):
        if a.get(f) != b.get(f):
            if f == "값":
                chg_val.append(k)
            elif f == "값_당분기":
                chg_dangi.append(k)
            else:
                other_field.append((k, f))
chk("no changed row outside KR0099", not outside, f"({len(outside)})")
chk("no changed field other than 값 / 값_당분기", not other_field, f"({other_field[:3]})")
planned = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_new"] + C["gold_replace"]}
chk(f"값 changed cells == the {len(planned)} plan cells", set(chg_val) == set(planned), f"(changed {len(chg_val)}, plan {len(planned)})")
chk("every changed 값 equals the plan value", all(lm[k]["값"] == planned[k]["value"] for k in chg_val if k in planned))
chk("every planned cell had the plan 'was' value in HEAD", all(((hm[k]["값"] is None) if e["was"] is None else abs((hm[k]["값"] or 0) - e["was"]) <= 5e-4) for k, e in planned.items()))
by_q = {}
for k in chg_val:
    by_q[k[2]] = by_q.get(k[2], 0) + 1
out.append(f"   값 changed per quarter {dict(sorted(by_q.items()))}")
by_dq = {}
for k in chg_dangi:
    by_dq[k[2]] = by_dq.get(k[2], 0) + 1
out.append(f"   값_당분기 changed {len(chg_dangi)} cells per quarter {dict(sorted(by_dq.items()))}; dangi-only (값 unchanged) {len(set(chg_dangi) - set(chg_val))}")
next_of_planned = {(c, i, f"{q[:4]}.{int(q[5]) + 1}Q") for (c, i, q) in planned if q[5] != "4"}
unexplained = [k for k in chg_dangi if k not in planned and k not in next_of_planned]
chk("every changed 값_당분기 cell is a planned cell or the successor quarter of a planned cell", not unexplained, f"({unexplained[:5]})")
bad = []
for k in chg_dangi:
    v = lm[k]["값"]
    d = lm[k]["값_당분기"]
    if v is None or d is None:
        bad.append((k, "blank"))
        continue
    if k[2][5] == "1":
        exp = v
    else:
        pv = lm.get((k[0], k[1], prevq(k[2])), {}).get("값")
        exp = None if pv is None else v - pv
    if exp is None or abs(d - exp) > 1e-5:
        bad.append((k, d, exp))
chk("every changed 값_당분기 equals the cumulative difference of the live cells (Q1 = cumulative); none is blank", not bad, f"({bad[:3]})")
hb, lb = head("PL_breakdown.json"), live("PL_breakdown.json")
chk("file ends the same way and uses the same newline convention", (b"\r\n" in hb) == (b"\r\n" in lb) and hb[-3:] == lb[-3:])
# ------------------------------------------------------------------------------------------------ PL gold
hg = json.loads(head("data/_gold/user_pl_cells.json").decode("utf-8"))
lg = json.loads(live("data/_gold/user_pl_cells.json").decode("utf-8"))
gk = lambda e: (e["원보험사코드"], e["항목번호"], e["공시분기"])  # noqa: E731
n0 = len(hg["set"])
chk("gold: all existing set entries untouched (same order)", lg["set"][:n0] == hg["set"])
added = lg["set"][n0:]
chk("gold: appended entries == plan new entries (order, 값, was, note)", [(gk(e), e["값"], e["was"], e["note"]) for e in added] == [((e["code"], e["item"], e["quarter"]), e["value"], e["was"], e["note"]) for e in C["gold_new"]], f"({len(added)} appended)")
chk("gold: every appended entry has keys 원보험사코드/항목번호/공시분기/값/was/note only", all(set(e) == {"원보험사코드", "항목번호", "공시분기", "값", "was", "note"} for e in added))
chk("gold: null_dangi, set_dangi and every other top-level key untouched", all(lg[k] == hg[k] for k in hg if k != "set") and set(lg) == set(hg))
# ------------------------------------------------------------------------------------------------ CSM master + gold + provenance
ch = json.loads(head("CSM_waterfall.json").decode("utf-8"))
cl = json.loads(live("CSM_waterfall.json").decode("utf-8"))
chk("CSM rows count equal and same key order", len(ch) == len(cl) and [key(r) for r in ch] == [key(r) for r in cl], f"({len(ch)} rows)")
chm, clm = {key(r): r for r in ch}, {key(r): r for r in cl}
cval, cdangi, coth, couts = [], [], [], []
for k in clm:
    a, b = chm[k], clm[k]
    if a == b:
        continue
    if k[0] != CODE:
        couts.append(k)
    for f in set(a) | set(b):
        if a.get(f) != b.get(f):
            (cval if f == "값" else cdangi if f == "값_당분기" else coth).append(k if f in ("값", "값_당분기") else (k, f))
cplanned = {(e["code"], e["item"], e["quarter"]): e for e in C["csm_gold_new"] + C["csm_gold_replace"]}
chk("CSM: no changed row outside KR0099, no other field", not couts and not coth, f"({couts[:3]} {coth[:3]})")
chk(f"CSM: 값 changed cells == the {len(cplanned)} plan cells with the plan values", set(cval) == set(cplanned) and all(clm[k]["값"] == cplanned[k]["value"] for k in cval), f"({len(cval)})")
chk("CSM: every planned cell had the plan 'was' value in HEAD", all(abs(chm[k]["값"] - e["was"]) <= 1e-9 for k, e in cplanned.items()))
out.append(f"   CSM 값_당분기 changed {len(cdangi)} cells per quarter {dict(sorted({q: sum(1 for k in cdangi if k[2] == q) for q in {k[2] for k in cdangi}}.items()))}")
cunexp = [k for k in cdangi if k[2] not in ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q")]
chk("CSM: 값_당분기 changes only inside FY2023 (2023.1Q-2023.4Q)", not cunexp, f"({cunexp[:3]})")
hcg = json.loads(head("data/_gold/user_csm_cells.json").decode("utf-8"))
lcg = json.loads(live("data/_gold/user_csm_cells.json").decode("utf-8"))
m0 = len(hcg["set"])
chk("CSM gold: all existing set entries untouched", lcg["set"][:m0] == hcg["set"])
cadded = lcg["set"][m0:]
chk("CSM gold: appended entries == plan new entries", [(gk(e), e["값"], e["was"], e["why"]) for e in cadded] == [((e["code"], e["item"], e["quarter"]), e["value"], e["was"], e["why"]) for e in C["csm_gold_new"]], f"({len(cadded)} appended)")
chk("CSM gold: other top-level keys untouched", all(lcg[k] == hcg[k] for k in hcg if k != "set") and set(lcg) == set(hcg))
hcp = json.loads(head("CSM_waterfall_provenance.json").decode("utf-8"))
lcp = json.loads(live("CSM_waterfall_provenance.json").decode("utf-8"))
ck = lambda c: (c["company_code"], c["quarter"], c["item_block"])  # noqa: E731
chk("CSM provenance: same block keys and order", [ck(c) for c in hcp["cells"]] == [ck(c) for c in lcp["cells"]])
hcm, lcm = {ck(c): c for c in hcp["cells"]}, {ck(c): c for c in lcp["cells"]}
cdif = sorted(k for k in lcm if hcm[k] != lcm[k])
want_blocks = {(e["code"], e["quarter"], "csm_waterfall") for e in C["csm_gold_new"] + C["csm_gold_replace"]}
chk("CSM provenance: changed blocks only gained owner_override=True and belong to the touched (company, quarter)s", all(k in want_blocks and {f for f in lcm[k] if lcm[k][f] != hcm[k].get(f)} <= {"owner_override"} and lcm[k].get("owner_override") for k in cdif), f"({len(cdif)} blocks)")
chk("CSM provenance: every touched block carries owner_override", all(lcm[k].get("owner_override") for k in want_blocks))
cnew = sorted(set(lcp) - set(hcp))
chk("CSM provenance: only the new merge note key added", cnew == ["merge_note_20261023_e23_kr0099_kblife_csm"] and all(lcp[k] == hcp[k] for k in hcp if k != "cells"), f"({cnew})")
# ------------------------------------------------------------------------------------------------ ledger
chk("ledger: byte-equal to HEAD (no replaced / vanished masked gold cell, no pin added)", head("data/_gold/gold_overlay_ledger.json") == live("data/_gold/gold_overlay_ledger.json"))
# ------------------------------------------------------------------------------------------------ PL provenance
hp = json.loads(head("PL_breakdown_provenance.json").decode("utf-8"))
lp = json.loads(live("PL_breakdown_provenance.json").decode("utf-8"))
pk = lambda c: (c["company_code"], c["quarter"], c["item_block"])  # noqa: E731
hpm, lpm = {pk(c): c for c in hp["cells"]}, {pk(c): c for c in lp["cells"]}
dif = sorted(k for k in lpm if hpm.get(k) != lpm[k])
inserted = sorted(set(lpm) - set(hpm))
chk("provenance: no block removed", not (set(hpm) - set(lpm)))
chk("provenance: the surviving blocks keep their relative order", [pk(c) for c in hp["cells"]] == [pk(c) for c in lp["cells"] if pk(c) in hpm])
chk("provenance: changed or inserted blocks only of KR0099 2023.1Q-2023.3Q", all(k[0] == CODE and k[1] in ("2023.1Q", "2023.2Q", "2023.3Q") for k in dif), f"({len(dif)} blocks: {[k[1:] for k in dif]}; inserted {[k[1:] for k in inserted]})")
newkeys = sorted(set(lp) - set(hp))
chk("provenance: only the new merge note key added at top level, others untouched", newkeys == ["merge_note_20261023_e23_kr0099_kblife"] and all(lp[k] == hp[k] for k in hp if k != "cells"), f"({newkeys})")
cover = {(k[0], k[1]) for k in dif}
unc = sorted(k for k in set(chg_val) if (k[0], k[2]) not in cover)
chk("provenance: every cell whose 값 changed belongs to a re-emitted (company, quarter) block", not unc, f"({len(unc)} cells in unchanged blocks: {unc[:4]})")
# ------------------------------------------------------------------------------------------------ test file
ht = head("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
lt = live("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
d = [x for x in difflib.unified_diff(ht, lt, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
chk("test file: only the census declaration (+1 comment) and the TAX22 lines changed", len(d) <= 30, f"({len(d)} differing lines, lines {len(ht)} -> {len(lt)})")
for x in d:
    out.append("   " + x[:260])
out.append("   " + [x for x in lt if x.startswith("GOLD_OVERLAY_CENSUS")][0])
out.append("ALL PASS" if ok else "SOME FAIL")
(OUT / "kr0099_diff_vs_head.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
sys.exit(0 if ok else 1)
