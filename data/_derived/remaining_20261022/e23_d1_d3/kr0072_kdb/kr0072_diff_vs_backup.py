# -*- coding: utf-8 -*-
"""Read-only, independent of the applier: cell-level diff of every file the 케이디비생명보험 D3 load writes vs the PRE-LOAD state.
Pre-load state = backup_before_apply/kr0072_kdb/ (this chain's earlier companies KB라이프, 롯데손해보험 and ABL are already inside that state; the backup is verified byte-equal to the ABL manifest's after_sha256).
The POST state is read from KR0072_POST_ROOT (default: the repo root = after --apply; set it to the --out-dir folder to check the simulation BEFORE applying; files absent there fall back to the repo).
Asserts: PL master changed rows only of KR0072 FY2023 quarters, only fields 값 / 값_당분기; 값 changes == the 65 plan cells, each equal to the plan value AND to the independently re-read value
(kr0072_verify_values.json written by kr0072_verify.py); every changed 값_당분기 equals the derivation (cum - previous cum of the post master) or the pinned printed 3-month column (8 set_dangi cells) and
follows a changed cumulative; CSM the same (20 cells + derived single quarters); gold: PL appended entries == plan, the 4 replaced entries == plan, 8 set_dangi cells appended, nothing else touched; CSM gold:
2 chain-forced entries removed, 5 class-A entries replaced in place, 13 appended, everything else untouched; ledger: exactly the 3 pins of the replaced masked CSM gold cells removed; provenance: only KR0072
FY2023 blocks + merge note keys; the files that must not change are byte-equal to git HEAD; test file: only the census declaration and its comment.
Writes kr0072_diff_vs_backup.txt (or _sim.txt) next to this file."""
import difflib
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("C:/Users/sangwook.cho/Desktop/insurequant")
OUT = Path(__file__).resolve().parent
BK = ROOT / "data/_derived/remaining_20261022/e23_d1_d3/backup_before_apply/kr0072_kdb"
POST = Path(os.environ.get("KR0072_POST_ROOT", str(ROOT)))
TAG = os.environ.get("KR0072_DIFF_TAG", "")
sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((OUT / "e23_plan_kdb_final.json").read_text(encoding="utf-8"))
C = PLAN["apply_contract"]
CODE = PLAN["code"]
VALS = json.loads((OUT / "kr0072_verify_values.json").read_text(encoding="utf-8"))
ABL_MAN = json.loads((ROOT / "data/_derived/remaining_20261022/e23_d1_d3/kr0070_abl/apply_manifest_e23_abl.json").read_text(encoding="utf-8"))
QS = ("2023.1Q", "2023.2Q", "2023.3Q", "2023.4Q")
PINS3 = ["CSM|KR0072|2023.1Q|6", "CSM|KR0072|2023.2Q|4", "CSM|KR0072|2023.2Q|5"]


def pre(rel):
    return (BK / rel).read_bytes().replace(b"\r\n", b"\n")


def live(rel):
    p = POST / rel
    if not p.exists():
        p = ROOT / rel
    return p.read_bytes().replace(b"\r\n", b"\n")


out, ok = [], True


def chk(name, cond, extra=""):
    global ok
    ok = ok and bool(cond)
    out.append(f"[{'PASS' if cond else 'FAIL'}] {name} {extra}")


key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])  # noqa: E731


def prevq(q):
    return None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"


out.append(f"post state read from: {POST}")
# ------------------------------------------------------------------------------------------------ the backup is the pre-load state of the chain
for rel, h in ABL_MAN["after_sha256"].items():
    chk(f"backup {rel} == ABL manifest after_sha256 (= state right before this load)", hashlib.sha256((BK / rel).read_bytes()).hexdigest() == h)
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
    if k[0] != CODE or k[2] not in QS:
        outside.append(k)
    for f in set(a) | set(b):
        if a.get(f) != b.get(f):
            if f == "값":
                chg_val.append(k)
            elif f == "값_당분기":
                chg_dangi.append(k)
            else:
                other_field.append((k, f))
chk("no changed row outside KR0072 2023.1Q-2023.4Q (KR0099, KR0003, KR0070 and all others untouched)", not outside, f"({len(outside)})")
chk("no changed field other than 값 / 값_당분기", not other_field, f"({other_field[:3]})")
planned = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_new"] + C["gold_replace"]}
chk(f"값 changed cells == the {len(planned)} plan cells", set(chg_val) == set(planned), f"(changed {len(chg_val)}, plan {len(planned)})")
chk("every changed 값 equals the plan value", all(lm[k]["값"] == planned[k]["value"] for k in chg_val if k in planned))
chk("every changed 값 equals the INDEPENDENTLY re-read value (kr0072_verify_values.json; items 7 / 12 / 15 are derived from the live legs there too)", all(abs(lm[k]["값"] - VALS["pl"][k[2]][str(k[1])]) <= 2e-6 for k in chg_val), f"({len(chg_val)} cells)")
chk("every planned cell had the plan 'old' value before (live master value, not the gold value)", all(((hm[(b['code'], c['item'], b['quarter'])]['값'] is None) if c['old'] is None else abs((hm[(b['code'], c['item'], b['quarter'])]['값'] or 0) - c['old']) <= 5e-4)
                                                                                                    for b in PLAN["buckets"] for c in b["cells"]))
pins = {(e[0], e[1], int(e[2])): float(e[3]) for e in C["set_dangi_add"]}
pins = {(c, i, q): v for (c, q, i), v in pins.items()}
bad_d = []
for k in chg_dangi:
    code, item, q = k
    pq = prevq(q)
    cum = lm[k]["값"]
    exp = cum if pq is None else (None if lm[(code, item, pq)]["값"] is None or cum is None else cum - lm[(code, item, pq)]["값"])
    if k in pins:
        exp = pins[k]
    got = lm[k]["값_당분기"]
    if exp is None:
        if got is not None:
            bad_d.append((k, got, exp))
    elif got is None or abs(got - exp) > 1e-6:
        bad_d.append((k, got, exp))
chk("every changed 값_당분기 equals cum - previous-quarter cum of the post master, or the pinned printed 3-month column", not bad_d, f"({len(chg_dangi)} cells; bad {bad_d[:3]})")
chk("every pinned cell (8) holds its printed 3-month value in the post master", all(abs(lm[k]["값_당분기"] - v) <= 1e-9 for k, v in pins.items()), f"({len(pins)} cells)")
follow_bad = [k for k in chg_dangi if k not in planned and (CODE, k[1], prevq(k[2])) not in planned]
chk("every changed 값_당분기 belongs to a changed cumulative (this quarter or the previous one of the same item)", not follow_bad, f"({follow_bad[:3]})")
p3 = VALS["printed_3m"]
bad3 = []
for k in chg_dangi:
    code, item, q = k
    if q in p3 and str(item) in p3[q] and lm[k]["값_당분기"] is not None and abs(lm[k]["값_당분기"] - p3[q][str(item)]) > 1e-4:
        bad3.append((k, lm[k]["값_당분기"], p3[q][str(item)]))
chk("changed 2023.2Q / 2023.3Q single quarters of the re-read items equal the PRINTED 3-month column of the later filing (to 1e-4 백만원; the 8 pinned cells exactly)", not bad3, f"({bad3[:3]})")
chk("2024.x quarters of KR0072 untouched", not [k for k in lm if k[0] == CODE and k[2] >= "2024.1Q" and lm[k] != hm[k]])
out.append(f"   값 changed items {sorted({k[1] for k in chg_val})} (quarters {sorted({k[2] for k in chg_val})}); 값_당분기 changed cells {len(chg_dangi)} (dangi-only {len(set(chg_dangi) - set(chg_val))})")
hb, lb = (BK / "PL_breakdown.json").read_bytes(), (POST / "PL_breakdown.json" if (POST / "PL_breakdown.json").exists() else ROOT / "PL_breakdown.json").read_bytes()
chk("PL file keeps the newline convention and the ending", (b"\r\n" in hb) == (b"\r\n" in lb) and hb[-3:] == lb[-3:])
# ------------------------------------------------------------------------------------------------ PL gold
hg = json.loads(pre("data/_gold/user_pl_cells.json").decode("utf-8"))
lg = json.loads(live("data/_gold/user_pl_cells.json").decode("utf-8"))
gk = lambda e: (e["원보험사코드"], e["항목번호"], e["공시분기"])  # noqa: E731
n0 = len(hg["set"])
rep = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_replace"]}
untouched = all(lg["set"][i] == hg["set"][i] for i in range(n0) if gk(hg["set"][i]) not in rep)
chk("gold: all existing set entries untouched except the 4 replaced ones (same order)", untouched and [gk(e) for e in lg["set"][:n0]] == [gk(e) for e in hg["set"]])
for i in range(n0):
    k = gk(hg["set"][i])
    if k in rep:
        e = rep[k]
        chk(f"gold: replaced entry {k} == plan (값, was, note; same position; old note quoted verbatim)", (lg["set"][i]["값"], lg["set"][i]["was"], lg["set"][i]["note"]) == (e["value"], e["was"], e["note"]) and set(lg["set"][i]) == set(hg["set"][i])
            and hg["set"][i]["note"] in lg["set"][i]["note"] and e["note"].startswith("owner 2026-10-23 승인"))
added = lg["set"][n0:]
chk("gold: appended entries == plan new entries (order, 값, was, note)", [(gk(e), e["값"], e["was"], e["note"]) for e in added] == [((e["code"], e["item"], e["quarter"]), e["값"] if False else e["value"], e["was"], e["note"]) for e in C["gold_new"]], f"({len(added)} appended)")
chk("gold: every appended entry has keys 원보험사코드/항목번호/공시분기/값/was/note only", all(set(e) == {"원보험사코드", "항목번호", "공시분기", "값", "was", "note"} for e in added))
chk("gold: null_dangi untouched", lg["null_dangi"] == hg["null_dangi"])
hs, ls_ = hg["set_dangi"], lg["set_dangi"]
n_s = len(hs["cells"])
chk("gold: set_dangi existing cells untouched (same order)", ls_["cells"][:n_s] == hs["cells"])
chk("gold: set_dangi appended cells == plan set_dangi_add (8, order and source text)", ls_["cells"][n_s:] == [list(x) for x in C["set_dangi_add"]], f"({len(ls_['cells']) - n_s} appended)")
chk("gold: set_dangi only gained cells + the doc key _doc_e23_kr0072_20261023", set(ls_) - set(hs) == {"_doc_e23_kr0072_20261023"} and all(ls_[k] == hs[k] for k in hs if k != "cells"))
chk("gold: other top-level keys untouched", all(lg[k] == hg[k] for k in hg if k not in ("set", "set_dangi")) and set(lg) == set(hg))
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
    if k[0] != CODE or k[2] not in QS:
        couts.append(k)
    for f in set(a) | set(b):
        if a.get(f) != b.get(f):
            (cval if f == "값" else cdangi if f == "값_당분기" else coth).append(k if f in ("값", "값_당분기") else (k, f))
cplanned = {(e["code"], e["item"], e["quarter"]): e for e in C["csm_gold_new"] + C["csm_gold_replace"] + C["csm_gold_remove"]}
chk("CSM: no changed row outside KR0072 2023.1Q-2023.4Q, no other field", not couts and not coth, f"({couts[:3]} {coth[:3]})")
chk(f"CSM: 값 changed cells == the {len(cplanned)} plan cells with the plan values", set(cval) == set(cplanned) and all(clm[k]["값"] == cplanned[k]["value"] for k in cval), f"({len(cval)})")
two_dp = {"2023.1Q": True, "2023.2Q": True, "2023.3Q": False, "2023.4Q": False}
exp_vec = {q: [(round(x, 2) if two_dp[q] else round(x, 1)) for x in VALS["csm_exact"][q]] for q in QS}
chk("CSM: every changed 값 equals the INDEPENDENTLY re-read stored value (2 decimals for 2023.1Q/2Q, 1 decimal for 2023.3Q/4Q)", all(abs(clm[k]["값"] - exp_vec[k[2]][k[1] - 1]) < 1e-9 for k in cval))
chk("CSM: every planned cell had the plan 'old' value before", all(abs(chm[k]["값"] - [c["old"] for cb in PLAN["csm_buckets"] for c in cb["cells"] if (cb["code"], c["item"], cb["quarter"]) == k][0]) <= 1e-9 for k in cplanned))
chk("CSM: all 24 FY2023 cells now equal the independently re-read vector (to the stored precision; 2023.4Q items 2/3/5/6 unchanged at 1 decimal)", all(abs(clm[(CODE, i, q)]["값"] - exp_vec[q][i - 1]) < 1e-9 for q in QS for i in range(1, 7)))
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
chk("CSM: every changed 값_당분기 equals the derivation from the post cumulative cells", not bad, f"({len(cdangi)} cells, {bad[:3]})")
out.append(f"   CSM 값_당분기 changed {len(cdangi)} cells: {sorted((k[1], k[2], chm[k]['값_당분기'], clm[k]['값_당분기']) for k in cdangi)}")
hcg = json.loads(pre("data/_gold/user_csm_cells.json").decode("utf-8"))
lcg = json.loads(live("data/_gold/user_csm_cells.json").decode("utf-8"))
rm = {(e["code"], e["item"], e["quarter"]) for e in C["csm_gold_remove"]}
rpl = {(e["code"], e["item"], e["quarter"]): e for e in C["csm_gold_replace"]}
kept = [e for e in hcg["set"] if gk(e) not in rm]
untouched_c = all(lcg["set"][j] == kept[j] for j in range(len(kept)) if gk(kept[j]) not in rpl) and [gk(e) for e in lcg["set"][:len(kept)]] == [gk(e) for e in kept]
chk("CSM gold: the 2 chain-forced entries are gone, every other existing entry untouched except the 5 replaced ones (same order)", untouched_c and len(kept) == len(hcg["set"]) - 2 and not any(gk(e) in rm for e in lcg["set"]))
for j in range(len(kept)):
    k = gk(kept[j])
    if k in rpl:
        e = rpl[k]
        chk(f"CSM gold: replaced entry {k} == plan (값, was, why; same position; old why quoted verbatim)", (lcg["set"][j]["값"], lcg["set"][j]["was"], lcg["set"][j]["why"]) == (e["value"], e["was"], e["why"]) and set(lcg["set"][j]) == set(kept[j])
            and kept[j]["why"] in lcg["set"][j]["why"] and e["old_entry"] == kept[j])
chk("CSM gold: removed entries were exactly the plan's old entries", [e for e in hcg["set"] if gk(e) in rm] == [e["old_entry"] for e in C["csm_gold_remove"]])
cadded = lcg["set"][len(kept):]
chk("CSM gold: appended entries == plan new entries", [(gk(e), e["값"], e["was"], e["why"]) for e in cadded] == [((e["code"], e["item"], e["quarter"]), e["value"], e["was"], e["why"]) for e in C["csm_gold_new"]], f"({len(cadded)} appended)")
chk("CSM gold: only the documentation key _doc_e23_kr0072_20261023 was added at top level", set(lcg) - set(hcg) == {"_doc_e23_kr0072_20261023"} and all(lcg[k] == hcg[k] for k in hcg if k != "set"))
hcp = json.loads(pre("CSM_waterfall_provenance.json").decode("utf-8"))
lcp = json.loads(live("CSM_waterfall_provenance.json").decode("utf-8"))
ck = lambda c: (c["company_code"], c["quarter"], c["item_block"])  # noqa: E731
chk("CSM provenance: same block keys and order", [ck(c) for c in hcp["cells"]] == [ck(c) for c in lcp["cells"]])
hcm, lcm = {ck(c): c for c in hcp["cells"]}, {ck(c): c for c in lcp["cells"]}
cdif = sorted(k for k in lcm if hcm[k] != lcm[k])
chk("CSM provenance: changed blocks == 2023.3Q gaining owner_override=True and 2023.4Q losing it (2023.1Q/2Q already carried it, no gold left on 2023.4Q)",
    set(cdif) == {(CODE, "2023.3Q", "csm_waterfall"), (CODE, "2023.4Q", "csm_waterfall")} and lcm[(CODE, "2023.3Q", "csm_waterfall")].get("owner_override") and not lcm[(CODE, "2023.4Q", "csm_waterfall")].get("owner_override")
    and hcm[(CODE, "2023.4Q", "csm_waterfall")].get("owner_override") and lcm[(CODE, "2023.1Q", "csm_waterfall")].get("owner_override") and lcm[(CODE, "2023.2Q", "csm_waterfall")].get("owner_override"), f"({cdif})")
cnew = sorted(set(lcp) - set(hcp))
chk("CSM provenance: only the new merge note key added", cnew == ["merge_note_20261023_e23_kr0072_kdb_csm"] and all(lcp[k] == hcp[k] for k in hcp if k != "cells"), f"({cnew})")
# ------------------------------------------------------------------------------------------------ ledger
hl = json.loads(pre("data/_gold/gold_overlay_ledger.json").decode("utf-8"))
ll = json.loads(live("data/_gold/gold_overlay_ledger.json").decode("utf-8"))
chk("ledger: exactly the 3 pins of the replaced masked CSM gold cells were removed (none added, none changed)", sorted(set(hl["entries"]) - set(ll["entries"])) == sorted(PINS3) and not (set(ll["entries"]) - set(hl["entries"]))
    and all(ll["entries"][k] == hl["entries"][k] for k in ll["entries"]) and all(ll[k] == hl[k] for k in hl if k != "entries") and set(ll) == set(hl), f"({len(hl['entries'])} -> {len(ll['entries'])})")
# ------------------------------------------------------------------------------------------------ files that must not change
for rel in ("data/_gold/pl_bridge_baseline.json", "data/_gold/pl_csm_amort_missing_ledger.json", "scripts/validate_master_tables.py", "scripts/validate_data_contract.py",
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
chk("provenance: changed or inserted blocks only of KR0072 2023.1Q-2023.4Q", all(k[0] == CODE and k[1] in QS for k in dif), f"({len(dif)} blocks: {[(k[1], k[2]) for k in dif]}; inserted {[k[1:] for k in inserted]})")
newkeys = sorted(set(lp) - set(hp))
chk("provenance: only the new merge note key added at top level, others untouched", newkeys == ["merge_note_20261023_e23_kr0072_kdb"] and all(lp[k] == hp[k] for k in hp if k != "cells"), f"({newkeys})")
cover = {(k[0], k[1]) for k in dif}
unc = sorted(k for k in set(chg_val) if (k[0], k[2]) not in cover)
chk("provenance: every cell whose 값 changed belongs to a re-emitted (company, quarter) block", not unc, f"({len(unc)} cells in unchanged blocks: {unc[:4]})")
for k in dif:
    out.append(f"   provenance block re-emitted: {k}; source_id {lpm[k].get('source_id')} resolution {lpm[k].get('resolution')} keys {sorted(lpm[k].keys())[:8]}")
# ------------------------------------------------------------------------------------------------ test file
ht = pre("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
lt = live("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
d = [x for x in difflib.unified_diff(ht, lt, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
chk("test file: only the census declaration (+1 comment) changed", 0 < len(d) <= 4, f"({len(d)} differing lines, lines {len(ht)} -> {len(lt)})")
for x in d:
    out.append("   " + x[:300])
out.append("   " + [x for x in lt if x.startswith("GOLD_OVERLAY_CENSUS")][0])
out.append("ALL PASS" if ok else "SOME FAIL")
(OUT / f"kr0072_diff_vs_backup{TAG}.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
sys.exit(0 if ok else 1)
