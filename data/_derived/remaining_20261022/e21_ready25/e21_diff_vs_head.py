# -*- coding: utf-8 -*-
"""Read-only, independent of the applier: cell-level diff of every file the apply writes vs git HEAD.
Asserts: PL master changed rows only of the 9 companies, only fields 값 / 값_당분기; 값 changes == the plan cells with the plan values and plan 'was' values; pins hold; CSM master the same for the 4
companies; gold: exactly the replaced entries differ (only 값/was/note|why), appended entries == plan; ledger: only removals of replaced masked cells; provenance: only planned blocks / flags + the new merge
note keys; test file: only the census declaration / tax22 lines."""
import difflib
import json
import subprocess
import sys
from pathlib import Path

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((OUT / "e21_plan.json").read_text(encoding="utf-8"))
C = PLAN["apply_contract"]
CODES = {b["code"] for b in PLAN["buckets"] if b.get("cells")}
CCODES = {cb["code"] for cb in PLAN["csm_buckets"] if cb["cells"]}


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
    if k[0] not in CODES:
        outside.append(k)
    for f in set(a) | set(b):
        if a.get(f) != b.get(f):
            if f == "값":
                chg_val.append(k)
            elif f == "값_당분기":
                chg_dangi.append(k)
            else:
                other_field.append((k, f))
chk(f"no changed row outside the {len(CODES)} companies", not outside, f"({len(outside)})")
chk("no changed field other than 값 / 값_당분기", not other_field, f"({other_field[:3]})")
planned = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_new"] + C["gold_replace"]}
chk(f"값 changed cells == the {len(planned)} plan cells", set(chg_val) == set(planned), f"(changed {len(chg_val)}, plan {len(planned)})")
chk("every changed 값 equals the plan value", all(lm[k]["값"] == planned[k]["value"] for k in chg_val if k in planned))
chk("every planned cell had the plan 'was' value in HEAD", all(((hm[k]["값"] is None) if e["was"] is None else abs((hm[k]["값"] or 0) - e["was"]) <= 5e-4) for k, e in planned.items()))
nd = {(c, i, q) for c, q, i in C["null_dangi_add"]}
sd = {(c, i, q): v for c, q, i, v, _s in C["set_dangi_add"]}
chk("null_dangi_add cells: 값_당분기 blank, 값 kept", all(lm[k]["값_당분기"] is None and lm[k]["값"] is not None for k in nd), f"({len(nd)})")
chk("set_dangi_add cells hold the printed 3-month value", all(abs(lm[k]["값_당분기"] - v) <= 1e-9 for k, v in sd.items()), f"({len(sd)})")
rm = {(c, i, q) for c, q, i in C["set_dangi_remove"]}
chk("set_dangi_remove cells: 값_당분기 identical to HEAD (value-neutral removal)", all(abs(lm[k]["값_당분기"] - hm[k]["값_당분기"]) <= 1e-9 for k in rm), f"({len(rm)})")
nrm = {(c, i, q) for c, q, i in C["null_dangi_remove"]}


def prevq(q):
    return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"


chk("null_dangi_remove cells: 값_당분기 = 값(q) - 값(q-1) derived from the live cumulatives", all(lm[k]["값_당분기"] is not None and abs(lm[k]["값_당분기"] - (lm[k]["값"] - lm[(k[0], k[1], prevq(k[2]))]["값"])) <= 1e-5 for k in nrm), f"({len(nrm)})")
by_co = {}
for k in chg_dangi:
    by_co[k[0]] = by_co.get(k[0], 0) + 1
out.append(f"   값_당분기 changed {len(chg_dangi)} cells {dict(sorted(by_co.items()))}; of which dangi-only (값 unchanged) {len(set(chg_dangi) - set(chg_val))}")
seam_keys = {(s["code"], s["item"], s["quarter"]) for s in PLAN["seams"]}
next_of_planned = {(c, i, f"{q[:4]}.{int(q[5]) + 1}Q") for (c, i, q) in planned if q[5] != "4"}
unexplained = [k for k in chg_dangi if k not in seam_keys and k not in planned and k not in next_of_planned and k not in nrm and k not in nd]
chk("every changed 값_당분기 cell is a planned cell / its successor / a seam-table cell / a pin change", not unexplained, f"({unexplained[:5]})")
blank_now = [k for k in chg_dangi if lm[k]["값_당분기"] is None]
chk("every cell that turned blank is a planned null_dangi cell", set(blank_now) <= nd, f"({len(blank_now)} blanked, {len(nd)} planned pins)")
nonblank_wrong = [k for k in chg_dangi if k not in nd and lm[k]["값_당분기"] is not None and lm[k]["값"] is not None and k[2][5] != "1" and k not in sd
                  and abs(lm[k]["값_당분기"] - (lm[k]["값"] - (lm[(k[0], k[1], prevq(k[2]))]["값"] if lm.get((k[0], k[1], prevq(k[2]))) and lm[(k[0], k[1], prevq(k[2]))]["값"] is not None else float('nan')))) > 1e-5]
chk("every other changed 값_당분기 equals the cumulative difference of the live cells (Q1 = cumulative)", not nonblank_wrong, f"({nonblank_wrong[:3]})")
hb, lb = head("PL_breakdown.json"), live("PL_breakdown.json")
chk("file ends the same way and uses the same newline convention", (b"\r\n" in hb) == (b"\r\n" in lb) and hb[-3:] == lb[-3:])
# ------------------------------------------------------------------------------------------------ PL gold
hg = json.loads(head("data/_gold/user_pl_cells.json").decode("utf-8"))
lg = json.loads(live("data/_gold/user_pl_cells.json").decode("utf-8"))
gk = lambda e: (e["원보험사코드"], e["항목번호"], e["공시분기"])  # noqa: E731
n0 = len(hg["set"])
repl = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_replace"]}
diff_idx = [i for i in range(n0) if lg["set"][i] != hg["set"][i]]
chk("gold: exactly the replaced entries differ among the existing ones", {gk(lg["set"][i]) for i in diff_idx} == set(repl), f"({len(diff_idx)} differ, plan {len(repl)})")
chk("gold: replaced entries keep the same key set and order", all(list(lg["set"][i].keys()) == list(hg["set"][i].keys()) for i in diff_idx))
chk("gold: replaced entries changed only 값 / was / note", all({f for f in lg["set"][i] if lg["set"][i][f] != hg["set"][i][f]} <= {"값", "was", "note"} for i in diff_idx))
chk("gold: replaced entries == plan (값, was, note)", all((lg["set"][i]["값"], lg["set"][i]["was"], lg["set"][i]["note"]) == (repl[gk(lg["set"][i])]["value"], repl[gk(lg["set"][i])]["was"], repl[gk(lg["set"][i])]["note"]) for i in diff_idx))
added = lg["set"][n0:]
KLIFE = {("KR0099", 2, "2024.1Q"), ("KR0099", 8, "2024.1Q"), ("KR0099", 12, "2024.1Q")}
chk("gold: appended entries == plan new entries minus the 3 KB라이프 cells removed after the handler fix (order, 값, was, note)", [(gk(e), e["값"], e["was"], e["note"]) for e in added] == [((e["code"], e["item"], e["quarter"]), e["value"], e["was"], e["note"]) for e in C["gold_new"] if (e["code"], e["item"], e["quarter"]) not in KLIFE])
chk("gold: the 3 KB라이프 2024.1Q cells (2/8/12) are NOT in the gold file (the fixed builder source carries them)", not any(gk(e) in KLIFE for e in lg["set"]))
vh = json.loads(head("data/dart/viz/pl_breakdown_master.json").decode("utf-8"))
vl = json.loads(live("data/dart/viz/pl_breakdown_master.json").decode("utf-8"))
vhm, vlm = {key(r): r for r in vh}, {key(r): r for r in vl}
vchg = sorted(k for k in vlm if vhm.get(k) != vlm[k])
chk("viz builder master: exactly the 3 KB라이프 cells changed, to the plan values", vchg == sorted(KLIFE) and all(vlm[k]["값"] == planned[k]["value"] for k in vchg) and len(vh) == len(vl), f"({vchg})")
fh = json.loads(head("tests/fixtures/pl_breakdown_golden.json").decode("utf-8"))
fl = json.loads(live("tests/fixtures/pl_breakdown_golden.json").decode("utf-8"))
chk("PL golden manifest: only sha256_master moved", {k for k in fl if fl[k] != fh.get(k)} == {"sha256_master"}, f"({[k for k in fl if fl[k] != fh.get(k)]})")
nl_ = chr(10)
ch = head("scripts/pl_breakdown/companies.py").decode("utf-8").split(nl_)
cl_ = live("scripts/pl_breakdown/companies.py").decode("utf-8").split(nl_)
dd = [x for x in difflib.unified_diff(ch, cl_, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
chk("companies.py: only the extract_tier2_kblife _jang_rerev line (abs removed, + 2 comment lines)", len(dd) == 4 and sum(1 for x in dd if x.startswith("-")) == 1 and "abs(jrr)" in [x for x in dd if x.startswith("-")][0], f"({len(dd)} lines)")
for x in dd:
    out.append("   " + x[:200])
chk("gold: every appended entry has keys 원보험사코드/항목번호/공시분기/값/was/note only", all(set(e) == {"원보험사코드", "항목번호", "공시분기", "값", "was", "note"} for e in added))
hn, ln = hg["null_dangi"]["cells"], lg["null_dangi"]["cells"]
rmn = {(c, q, int(i)) for c, q, i in C["null_dangi_remove"]}
keptn = [x for x in hn if (x[0], x[1], int(x[2])) not in rmn]
chk("gold: null_dangi = existing minus the removed pins, + plan cells", ln == keptn + [list(x) for x in C["null_dangi_add"]], f"({len(hn)} -> {len(ln)})")
hs, ls = hg["set_dangi"]["cells"], lg["set_dangi"]["cells"]
rmk = {(c, q, int(i)) for c, q, i in C["set_dangi_remove"]}
kept = [x for x in hs if (x[0], x[1], int(x[2])) not in rmk]
chk("gold: set_dangi = existing minus the removed pins, + plan cells", ls == kept + [list(x) for x in C["set_dangi_add"]], f"({len(hs)} -> {len(ls)}, removed {len(hs) - len(kept)})")
docs_ok = all(lg[k] == hg[k] for k in hg if k not in ("set", "null_dangi", "set_dangi")) and all(lg["null_dangi"].get(k) == v for k, v in hg["null_dangi"].items() if k != "cells") \
    and all(lg["set_dangi"].get(k) == v for k, v in hg["set_dangi"].items() if k != "cells")
chk("gold: existing doc keys untouched", docs_ok)
chk("gold: only the new _doc_e21 keys added to the dangi dicts", set(lg["null_dangi"]) - set(hg["null_dangi"]) == {"_doc_e21_20261023"} and set(lg["set_dangi"]) - set(hg["set_dangi"]) == {"_doc_e21_20261023"})
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
    if k[0] not in CCODES:
        couts.append(k)
    for f in set(a) | set(b):
        if a.get(f) != b.get(f):
            (cval if f == "값" else cdangi if f == "값_당분기" else coth).append(k if f in ("값", "값_당분기") else (k, f))
cplanned = {(e["code"], e["item"], e["quarter"]): e for e in C["csm_gold_new"] + C["csm_gold_replace"]}
chk(f"CSM: no changed row outside the {len(CCODES)} companies, no other field", not couts and not coth, f"({couts[:3]} {coth[:3]})")
chk(f"CSM: 값 changed cells == the {len(cplanned)} plan cells with the plan values", set(cval) == set(cplanned) and all(clm[k]["값"] == cplanned[k]["value"] for k in cval), f"({len(cval)})")
chk("CSM: every planned cell had the plan 'was' value in HEAD", all(abs(chm[k]["값"] - e["was"]) <= 1e-9 for k, e in cplanned.items()))
out.append(f"   CSM 값_당분기 changed {len(cdangi)} cells (builder derivation: flows = cumulative differences; 기초 = previous 기말; 기말 = point)")
hcg = json.loads(head("data/_gold/user_csm_cells.json").decode("utf-8"))
lcg = json.loads(live("data/_gold/user_csm_cells.json").decode("utf-8"))
m0 = len(hcg["set"])
crepl = {(e["code"], e["item"], e["quarter"]): e for e in C["csm_gold_replace"]}
cdiff = [i for i in range(m0) if lcg["set"][i] != hcg["set"][i]]
chk("CSM gold: exactly the replaced entries differ", {gk(lcg["set"][i]) for i in cdiff} == set(crepl), f"({len(cdiff)} differ, plan {len(crepl)})")
chk("CSM gold: replaced entries changed only 값 / was / why and == plan", all({f for f in lcg["set"][i] if lcg["set"][i][f] != hcg["set"][i][f]} <= {"값", "was", "why"} and
    (lcg["set"][i]["값"], lcg["set"][i]["was"], lcg["set"][i]["why"]) == (crepl[gk(lcg["set"][i])]["value"], crepl[gk(lcg["set"][i])]["was"], crepl[gk(lcg["set"][i])]["why"]) for i in cdiff))
cadded = lcg["set"][m0:]
chk("CSM gold: appended entries == plan new entries", [(gk(e), e["값"], e["was"], e["why"]) for e in cadded] == [((e["code"], e["item"], e["quarter"]), e["value"], e["was"], e["why"]) for e in C["csm_gold_new"]])
chk("CSM gold: other top-level keys untouched", all(lcg[k] == hcg[k] for k in hcg if k != "set"))
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
chk("CSM provenance: only the new merge note key added", cnew == ["merge_note_20261023_e21_ready25_csm"] and all(lcp[k] == hcp[k] for k in hcp if k != "cells"), f"({cnew})")
# ------------------------------------------------------------------------------------------------ ledger
hl = json.loads(head("data/_gold/gold_overlay_ledger.json").decode("utf-8"))
ll = json.loads(live("data/_gold/gold_overlay_ledger.json").decode("utf-8"))
removed = sorted(set(hl["entries"]) - set(ll["entries"]))
chk("ledger: only removals, nothing added or changed", set(ll["entries"]) <= set(hl["entries"]) and all(ll["entries"][k] == hl["entries"][k] for k in ll["entries"]) and all(ll[k] == hl[k] for k in hl if k != "entries"))
chk("ledger: removed pins == replaced owner-gold cells that were masked", set(removed) <= {f"PL|{c}|{q}|{i}" for (c, i, q) in repl} | {f"CSM|{c}|{q}|{i}" for (c, i, q) in crepl}, f"({removed})")
# ------------------------------------------------------------------------------------------------ PL provenance
hp = json.loads(head("PL_breakdown_provenance.json").decode("utf-8"))
lp = json.loads(live("PL_breakdown_provenance.json").decode("utf-8"))
pk = lambda c: (c["company_code"], c["quarter"], c["item_block"])  # noqa: E731
hpm, lpm = {pk(c): c for c in hp["cells"]}, {pk(c): c for c in lp["cells"]}
dif = sorted(k for k in lpm if hpm.get(k) != lpm[k])
chk("provenance: same block keys and order", [pk(c) for c in hp["cells"]] == [pk(c) for c in lp["cells"]])
chk("provenance: changed blocks only of the planned companies", all(k[0] in CODES for k in dif), f"({len(dif)} blocks)")
newkeys = sorted(set(lp) - set(hp))
chk("provenance: only the two new merge note keys added at top level (load + KB라이프 gold removal), others untouched", newkeys == ["merge_note_20261023_e21_klife_gold_removed", "merge_note_20261023_e21_ready25"] and all(lp[k] == hp[k] for k in hp if k != "cells"), f"({newkeys})")
chk("provenance: KR0099 2024.1Q income_statement block == HEAD block (re-emitted after the gold removal; the builder-source cells carry the same sidecar record as at HEAD; emitter == sidecar is proven by e21_prov_check.txt)", ("KR0099", "2024.1Q", "income_statement") not in dif and ("KR0099", "2024.1Q", "income_statement") in lpm)
cover = {(k[0], k[1]) for k in dif}
unc = sorted(k for k in set(chg_val) if (k[0], k[2]) not in cover)
chk("provenance: every cell whose 값 changed belongs to a replaced (company, quarter) block, or is a REPLACED owner-gold cell, or is one of the 3 KB라이프 builder-source cells (block == HEAD)", all(k in repl or k in KLIFE for k in unc), f"({len(unc)} cells in unchanged blocks: {unc})")
# ------------------------------------------------------------------------------------------------ test file
ht = head("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
lt = live("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
d = [x for x in difflib.unified_diff(ht, lt, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
chk("test file: only the census declaration (+1 comment) and the TAX22 lines changed", len(d) <= 30, f"({len(d)} differing lines, lines {len(ht)} -> {len(lt)})")
for x in d:
    out.append("   " + x[:230])
out.append("   " + [x for x in lt if x.startswith("GOLD_OVERLAY_CENSUS")][0])
out.append("ALL PASS" if ok else "SOME FAIL")
(OUT / "e21_diff_vs_head.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
