# -*- coding: utf-8 -*-
"""Read-only, independent of the applier: cell-level diff of every file the 롯데손해보험 D2 load writes vs the PRE-LOAD state.
Pre-load state = backup_before_apply/kr0003_lotte/ (this chain's earlier company KB라이프 KR0099 is already inside that state; the backup is verified byte-equal to the KB라이프 manifest's after_sha256).
Asserts: PL master changed rows only of KR0003, only fields 값 / 값_당분기; 값 changes == the 18 plan cells (plan values, plan 'was' values); every changed 값_당분기 is a planned null_dangi cell and is now blank;
CSM master the same (5 cells, plus the derived single quarters of FY2023.4Q); gold: appended entries == plan, nothing existing touched, null_dangi gained exactly the 12 plan cells + one doc key,
set_dangi untouched; ledger / baseline files byte-equal; provenance: only KR0003 2023.4Q blocks + merge note keys; test file: only the census declaration (+ comment) and the TAX22 lines.
Also: KR0099 (previous company of the chain) rows are untouched.  Writes kr0003_diff_vs_backup.txt next to this file."""
import difflib
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = Path(__file__).resolve().parent
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0003_lotte"
sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((OUT / "e23_plan_lotte.json").read_text(encoding="utf-8"))
C = PLAN["apply_contract"]
CODE = PLAN["code"]
KB_MAN = json.loads((ROOT / "data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife/apply_manifest_e23_kblife.json").read_text(encoding="utf-8"))


def pre(rel):
    return (BK / rel).read_bytes().replace(b"\r\n", b"\n")


def live(rel):
    return (ROOT / rel).read_bytes().replace(b"\r\n", b"\n")


out, ok = [], True


def chk(name, cond, extra=""):
    global ok
    ok = ok and bool(cond)
    out.append(f"[{'PASS' if cond else 'FAIL'}] {name} {extra}")


key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])  # noqa: E731


def prevq(q):
    return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"


# ------------------------------------------------------------------------------------------------ the backup is the pre-load state of the chain
for rel, h in KB_MAN["after_sha256"].items():
    chk(f"backup {rel} == KB라이프 manifest after_sha256 (= state right before this load)", hashlib.sha256((BK / rel).read_bytes()).hexdigest() == h)
# ------------------------------------------------------------------------------------------------ PL master
h = json.loads(pre("PL_breakdown.json").decode("utf-8"))
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
chk("no changed row outside KR0003 (KR0099 and all others untouched)", not outside, f"({len(outside)})")
chk("no changed field other than 값 / 값_당분기", not other_field, f"({other_field[:3]})")
planned = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_new"] + C["gold_replace"]}
chk(f"값 changed cells == the {len(planned)} plan cells", set(chg_val) == set(planned), f"(changed {len(chg_val)}, plan {len(planned)})")
chk("every changed 값 equals the plan value", all(lm[k]["값"] == planned[k]["value"] for k in chg_val if k in planned))
chk("every planned cell had the plan 'was' value before", all(((hm[k]["값"] is None) if e["was"] is None else abs((hm[k]["값"] or 0) - e["was"]) <= 5e-4) for k, e in planned.items()))
nd_plan = {(c, i, q) for c, q, i in C["null_dangi_add"]}
chk("값_당분기 changed cells == the null_dangi plan cells", set(chg_dangi) == nd_plan, f"(changed {len(chg_dangi)}, plan {len(nd_plan)})")
chk("every changed 값_당분기 is now blank (None) while its 값 is non-blank", all(lm[k]["값_당분기"] is None and lm[k]["값"] is not None for k in chg_dangi))
chk("the 값_당분기 of every other KR0003 2023.4Q cell is unchanged", all(lm[k].get("값_당분기") == hm[k].get("값_당분기") for k in lm if k[0] == CODE and k[2] == "2023.4Q" and k not in nd_plan))
out.append(f"   값 changed items {sorted(k[1] for k in chg_val)} (quarters {sorted({k[2] for k in chg_val})}); 값_당분기 blanked items {sorted(k[1] for k in chg_dangi)}")
hb, lb = (BK / "PL_breakdown.json").read_bytes(), (ROOT / "PL_breakdown.json").read_bytes()
chk("PL file keeps the newline convention and the ending", (b"\r\n" in hb) == (b"\r\n" in lb) and hb[-3:] == lb[-3:])
# ------------------------------------------------------------------------------------------------ PL gold
hg = json.loads(pre("data/_gold/user_pl_cells.json").decode("utf-8"))
lg = json.loads(live("data/_gold/user_pl_cells.json").decode("utf-8"))
gk = lambda e: (e["원보험사코드"], e["항목번호"], e["공시분기"])  # noqa: E731
n0 = len(hg["set"])
chk("gold: all existing set entries untouched (same order)", lg["set"][:n0] == hg["set"])
added = lg["set"][n0:]
chk("gold: appended entries == plan new entries (order, 값, was, note)", [(gk(e), e["값"], e["was"], e["note"]) for e in added] == [((e["code"], e["item"], e["quarter"]), e["value"], e["was"], e["note"]) for e in C["gold_new"]], f"({len(added)} appended)")
chk("gold: every appended entry has keys 원보험사코드/항목번호/공시분기/값/was/note only", all(set(e) == {"원보험사코드", "항목번호", "공시분기", "값", "was", "note"} for e in added))
chk("gold: set_dangi untouched", lg["set_dangi"] == hg["set_dangi"])
nd0, nd1 = hg["null_dangi"], lg["null_dangi"]
chk("gold: null_dangi cells == old cells + the 12 plan cells (appended in plan order)", nd1["cells"] == nd0["cells"] + [list(x) for x in C["null_dangi_add"]], f"({len(nd0['cells'])} -> {len(nd1['cells'])})")
chk("gold: null_dangi other keys untouched, exactly one doc key added", {k: v for k, v in nd1.items() if k not in ("cells", "_doc_e23_kr0003_20261023")} == {k: v for k, v in nd0.items() if k != "cells"} and "_doc_e23_kr0003_20261023" in nd1)
chk("gold: other top-level keys untouched", all(lg[k] == hg[k] for k in hg if k not in ("set", "null_dangi")) and set(lg) == set(hg))
# ------------------------------------------------------------------------------------------------ CSM master + gold + provenance
ch = json.loads(pre("CSM_waterfall.json").decode("utf-8"))
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
chk("CSM: no changed row outside KR0003, no other field", not couts and not coth, f"({couts[:3]} {coth[:3]})")
chk(f"CSM: 값 changed cells == the {len(cplanned)} plan cells with the plan values", set(cval) == set(cplanned) and all(clm[k]["값"] == cplanned[k]["value"] for k in cval), f"({len(cval)})")
chk("CSM: every planned cell had the plan 'was' value before", all(abs(chm[k]["값"] - e["was"]) <= 1e-9 for k, e in cplanned.items()))
bad = []
for k in cdangi:
    code, item, q = k
    v = clm[k]["값"]
    if item == 6:
        exp = v
    elif item == 1:
        exp = clm.get((code, 6, prevq(q)), {}).get("값") if prevq(q) else v
    else:
        pv = clm.get((code, item, prevq(q)), {}).get("값") if prevq(q) else 0.0
        exp = None if pv is None else v - (pv if prevq(q) else 0.0)
    if exp is None or abs(clm[k]["값_당분기"] - exp) > 1e-5:
        bad.append((k, clm[k]["값_당분기"], exp))
out.append(f"   CSM 값_당분기 changed {len(cdangi)} cells: {sorted((k[1], k[2], chm[k]['값_당분기'], clm[k]['값_당분기']) for k in cdangi)}")
chk("CSM: 값_당분기 changes only in 2023.4Q items of KR0003 and each equals the derivation from the live cumulative cells", all(k[0] == CODE and k[2] == "2023.4Q" for k in cdangi) and not bad, f"({len(cdangi)} cells, {bad[:3]})")
hcg = json.loads(pre("data/_gold/user_csm_cells.json").decode("utf-8"))
lcg = json.loads(live("data/_gold/user_csm_cells.json").decode("utf-8"))
m0 = len(hcg["set"])
chk("CSM gold: all existing set entries untouched", lcg["set"][:m0] == hcg["set"])
cadded = lcg["set"][m0:]
chk("CSM gold: appended entries == plan new entries", [(gk(e), e["값"], e["was"], e["why"]) for e in cadded] == [((e["code"], e["item"], e["quarter"]), e["value"], e["was"], e["why"]) for e in C["csm_gold_new"]], f"({len(cadded)} appended)")
chk("CSM gold: other top-level keys untouched", all(lcg[k] == hcg[k] for k in hcg if k != "set") and set(lcg) == set(hcg))
hcp = json.loads(pre("CSM_waterfall_provenance.json").decode("utf-8"))
lcp = json.loads(live("CSM_waterfall_provenance.json").decode("utf-8"))
ck = lambda c: (c["company_code"], c["quarter"], c["item_block"])  # noqa: E731
chk("CSM provenance: same block keys and order", [ck(c) for c in hcp["cells"]] == [ck(c) for c in lcp["cells"]])
hcm, lcm = {ck(c): c for c in hcp["cells"]}, {ck(c): c for c in lcp["cells"]}
cdif = sorted(k for k in lcm if hcm[k] != lcm[k])
want_blocks = {(e["code"], e["quarter"], "csm_waterfall") for e in C["csm_gold_new"] + C["csm_gold_replace"]}
chk("CSM provenance: changed blocks only gained owner_override=True and belong to the touched (company, quarter)", all(k in want_blocks and {f for f in lcm[k] if lcm[k][f] != hcm[k].get(f)} <= {"owner_override"} and lcm[k].get("owner_override") for k in cdif), f"({len(cdif)} blocks: {cdif})")
chk("CSM provenance: every touched block carries owner_override", all(lcm[k].get("owner_override") for k in want_blocks))
cnew = sorted(set(lcp) - set(hcp))
chk("CSM provenance: only the new merge note key added", cnew == ["merge_note_20261023_e23_kr0003_lotte_csm"] and all(lcp[k] == hcp[k] for k in hcp if k != "cells"), f"({cnew})")
# ------------------------------------------------------------------------------------------------ files that must not change
for rel in ("data/_gold/gold_overlay_ledger.json", "data/_gold/pl_bridge_baseline.json", "data/_gold/pl_csm_amort_missing_ledger.json", "scripts/validate_master_tables.py", "scripts/validate_data_contract.py",
            "scripts/pl_breakdown/companies.py", "insurequant_master_tables.xlsx", "NB_CSM_multiple.json", "data/dart/viz/pl_breakdown_master.json"):
    p = ROOT / rel
    headb = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout
    chk(f"{rel}: equal to git HEAD (not touched by the chain so far or by this load)", p.read_bytes().replace(b"\r\n", b"\n") == headb.replace(b"\r\n", b"\n"))
# ------------------------------------------------------------------------------------------------ PL provenance
hp = json.loads(pre("PL_breakdown_provenance.json").decode("utf-8"))
lp = json.loads(live("PL_breakdown_provenance.json").decode("utf-8"))
pk = lambda c: (c["company_code"], c["quarter"], c["item_block"])  # noqa: E731
hpm, lpm = {pk(c): c for c in hp["cells"]}, {pk(c): c for c in lp["cells"]}
dif = sorted(k for k in lpm if hpm.get(k) != lpm[k])
inserted = sorted(set(lpm) - set(hpm))
chk("provenance: no block removed", not (set(hpm) - set(lpm)))
chk("provenance: the surviving blocks keep their relative order", [pk(c) for c in hp["cells"]] == [pk(c) for c in lp["cells"] if pk(c) in hpm])
chk("provenance: changed or inserted blocks only of KR0003 2023.4Q", all(k[0] == CODE and k[1] == "2023.4Q" for k in dif), f"({len(dif)} blocks: {[k[2] for k in dif]}; inserted {[k[1:] for k in inserted]})")
newkeys = sorted(set(lp) - set(hp))
chk("provenance: only the new merge note key added at top level, others untouched", newkeys == ["merge_note_20261023_e23_kr0003_lotte"] and all(lp[k] == hp[k] for k in hp if k != "cells"), f"({newkeys})")
cover = {(k[0], k[1]) for k in dif}
unc = sorted(k for k in set(chg_val) if (k[0], k[2]) not in cover)
chk("provenance: every cell whose 값 changed belongs to a re-emitted (company, quarter) block", not unc, f"({len(unc)} cells in unchanged blocks: {unc[:4]})")
for k in dif:
    out.append(f"   provenance block re-emitted: {k}; keys {sorted(lpm[k].keys())[:8]}")
# ------------------------------------------------------------------------------------------------ test file
ht = pre("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
lt = live("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
d = [x for x in difflib.unified_diff(ht, lt, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
chk("test file: only the census declaration (+1 comment) and the TAX22 lines changed", 0 < len(d) <= 12, f"({len(d)} differing lines, lines {len(ht)} -> {len(lt)})")
for x in d:
    out.append("   " + x[:260])
out.append("   " + [x for x in lt if x.startswith("GOLD_OVERLAY_CENSUS")][0])
out.append("ALL PASS" if ok else "SOME FAIL")
(OUT / "kr0003_diff_vs_backup.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
sys.exit(0 if ok else 1)
