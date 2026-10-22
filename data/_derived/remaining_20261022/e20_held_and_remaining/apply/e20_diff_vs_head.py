# -*- coding: utf-8 -*-
"""Read-only, independent of the applier: cell-level diff of every file the apply writes vs git HEAD.
Asserts: PL master changed rows only of the 11 companies, only fields 값 / 값_당분기; 값 changes == the 84 plan cells with the plan values and plan 'was' values;
pins hold (null_dangi blank, set_dangi printed value, removed pins value-neutral); gold: exactly the 9 replaced entries differ (only 값/was/note), the rest identical, appended entries == plan;
ledger: exactly the 4 pins of replaced masked cells removed; provenance: only blocks of the 11 companies changed + the new merge note key; test file: only the census declaration / tax22 lines."""
import difflib
import json
import subprocess
import sys
from pathlib import Path

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
PLAN = json.loads((OUT / "e20_plan.json").read_text(encoding="utf-8"))
C = PLAN["apply_contract"]
CODES = {b["code"] for b in PLAN["buckets"] if "error" not in b}


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
chk("no changed row outside the 11 companies", not outside, f"({len(outside)})")
chk("no changed field other than 값 / 값_당분기", not other_field, f"({other_field[:3]})")
planned = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_new"] + C["gold_replace"]}
chk(f"값 changed cells == the {len(planned)} plan cells", set(chg_val) == set(planned), f"(changed {len(chg_val)}, plan {len(planned)})")
chk("every changed 값 equals the plan value", all(lm[k]["값"] == planned[k]["value"] for k in chg_val if k in planned))
chk("every planned cell had the plan 'was' value in HEAD", all(abs((hm[k]["값"] or 0) - e["was"]) <= 5e-4 for k, e in planned.items()))
nd = {(c, i, q) for c, q, i in C["null_dangi_add"]}
sd = {(c, i, q): v for c, q, i, v, _s in C["set_dangi_add"]}
chk("null_dangi_add cells: 값_당분기 blank, 값 kept", all(lm[k]["값_당분기"] is None and lm[k]["값"] is not None for k in nd), f"({len(nd)})")
chk("set_dangi_add cells hold the printed 3-month value", all(abs(lm[k]["값_당분기"] - v) <= 1e-9 for k, v in sd.items()), f"({len(sd)})")
rm = {(c, i, q) for c, q, i in C["set_dangi_remove"]}
chk("set_dangi_remove cells: 값_당분기 identical to HEAD (value-neutral removal)", all(abs(lm[k]["값_당분기"] - hm[k]["값_당분기"]) <= 1e-9 for k in rm), f"({len(rm)})")
by_co = {}
for k in chg_dangi:
    by_co[k[0]] = by_co.get(k[0], 0) + 1
out.append(f"   값_당분기 changed {len(chg_dangi)} cells {dict(sorted(by_co.items()))}; of which dangi-only (값 unchanged) {len(set(chg_dangi) - set(chg_val))}")
seam_keys = {(s["code"], s["item"], s["quarter"]) for s in PLAN["seams"]}
chk("every changed 값_당분기 cell is a planned seam / Q1 / own cell", all(k in seam_keys or k in planned for k in chg_dangi), f"({[k for k in chg_dangi if k not in seam_keys and k not in planned][:3]})")
blank_now = [k for k in chg_dangi if lm[k]["값_당분기"] is None]
chk("every cell that turned blank is a planned null_dangi cell", set(blank_now) <= nd, f"({len(blank_now)} blanked, {len(nd)} planned pins)")
hb, lb = head("PL_breakdown.json"), live("PL_breakdown.json")
chk("file ends the same way and uses the same newline convention", (b"\r\n" in hb) == (b"\r\n" in lb) and hb[-3:] == lb[-3:])
# gold
hg = json.loads(head("data/_gold/user_pl_cells.json").decode("utf-8"))
lg = json.loads(live("data/_gold/user_pl_cells.json").decode("utf-8"))
gk = lambda e: (e["원보험사코드"], e["항목번호"], e["공시분기"])  # noqa: E731
n0 = len(hg["set"])
repl = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_replace"]}
diff_idx = [i for i in range(n0) if lg["set"][i] != hg["set"][i]]
chk("gold: exactly the replaced entries differ among the existing ones", {gk(lg["set"][i]) for i in diff_idx} == set(repl), f"({len(diff_idx)} differ, plan {len(repl)})")
chk("gold: replaced entries keep the same key set and order", all(list(lg["set"][i].keys()) == list(hg["set"][i].keys()) for i in diff_idx))
chk("gold: replaced entries changed only 값 / was / note",
    all({f for f in lg["set"][i] if lg["set"][i][f] != hg["set"][i][f]} <= {"값", "was", "note"} for i in diff_idx))
chk("gold: replaced entries == plan (값, was, note)", all((lg["set"][i]["값"], lg["set"][i]["was"], lg["set"][i]["note"]) == (repl[gk(lg["set"][i])]["value"], repl[gk(lg["set"][i])]["was"], repl[gk(lg["set"][i])]["note"]) for i in diff_idx))
chk("gold: replaced entries' old 값 == the original-vintage print (plan gold_class)", all(hg["set"][i]["값"] == repl[gk(hg["set"][i])]["old_entry"]["값"] for i in diff_idx))
added = lg["set"][n0:]
chk("gold: appended entries == plan new entries (order, 값, was, note)", [(gk(e), e["값"], e["was"], e["note"]) for e in added] == [((e["code"], e["item"], e["quarter"]), e["value"], e["was"], e["note"]) for e in C["gold_new"]])
chk("gold: every appended entry has keys 원보험사코드/항목번호/공시분기/값/was/note only", all(set(e) == {"원보험사코드", "항목번호", "공시분기", "값", "was", "note"} for e in added))
hn, ln = hg["null_dangi"]["cells"], lg["null_dangi"]["cells"]
chk("gold: null_dangi existing cells untouched, + plan cells", ln[:len(hn)] == hn and ln[len(hn):] == [list(x) for x in C["null_dangi_add"]], f"(+{len(ln) - len(hn)})")
hs, ls = hg["set_dangi"]["cells"], lg["set_dangi"]["cells"]
rmk = {(c, q, int(i)) for c, q, i in C["set_dangi_remove"]}
kept = [x for x in hs if (x[0], x[1], int(x[2])) not in rmk]
chk("gold: set_dangi = existing minus the removed pins, + plan cells", ls == kept + [list(x) for x in C["set_dangi_add"]], f"({len(hs)} -> {len(ls)}, removed {len(hs) - len(kept)})")
docs_ok = all(lg[k] == hg[k] for k in hg if k not in ("set", "null_dangi", "set_dangi")) and all(lg["null_dangi"].get(k) == v for k, v in hg["null_dangi"].items() if k != "cells") \
    and all(lg["set_dangi"].get(k) == v for k, v in hg["set_dangi"].items() if k != "cells")
chk("gold: existing doc keys untouched", docs_ok)
chk("gold: only the new _doc_e20 keys added to the dangi dicts", set(lg["null_dangi"]) - set(hg["null_dangi"]) == {"_doc_e20_20261022"} and set(lg["set_dangi"]) - set(hg["set_dangi"]) == {"_doc_e20_20261022"})
# ledger
hl = json.loads(head("data/_gold/gold_overlay_ledger.json").decode("utf-8"))
ll = json.loads(live("data/_gold/gold_overlay_ledger.json").decode("utf-8"))
removed = sorted(set(hl["entries"]) - set(ll["entries"]))
chk("ledger: only removals, nothing added or changed", set(ll["entries"]) <= set(hl["entries"]) and all(ll["entries"][k] == hl["entries"][k] for k in ll["entries"]) and all(ll[k] == hl[k] for k in hl if k != "entries"))
chk("ledger: removed pins == the replaced owner-gold cells that were masked", set(removed) <= {f"PL|{c}|{q}|{i}" for (c, i, q) in repl}, f"({removed})")
# provenance
hp = json.loads(head("PL_breakdown_provenance.json").decode("utf-8"))
lp = json.loads(live("PL_breakdown_provenance.json").decode("utf-8"))
pk = lambda c: (c["company_code"], c["quarter"], c["item_block"])  # noqa: E731
hpm, lpm = {pk(c): c for c in hp["cells"]}, {pk(c): c for c in lp["cells"]}
dif = sorted(k for k in lpm if hpm.get(k) != lpm[k])
chk("provenance: same block keys and order", [pk(c) for c in hp["cells"]] == [pk(c) for c in lp["cells"]])
chk("provenance: changed blocks only of the 11 companies", all(k[0] in CODES for k in dif), f"({len(dif)} blocks)")
newkeys = sorted(set(lp) - set(hp))
chk("provenance: only the new merge note key added at top level, others untouched", newkeys == ["merge_note_20261022_e20_latest_comparative_held_remaining"] and all(lp[k] == hp[k] for k in hp if k != "cells"), f"({newkeys})")
cover = {(k[0], k[1]) for k in dif}
unc = sorted(k for k in set(chg_val) if (k[0], k[2]) not in cover)
chk("provenance: every cell whose 값 changed belongs to a replaced (company, quarter) block, or is a REPLACED owner-gold cell (its lineage 'owner_gold_overlay' was already recorded)", all(k in repl for k in unc), f"({len(unc)} cells in unchanged blocks: {unc})")
chk("provenance: the unchanged blocks of those replaced cells already list the cells under owner_gold_overlay",
    all(any(sf["how"] == "owner_gold_overlay" and k[1] in sf["items"] for sf in hpm[(k[0], k[2], "income_statement")]["source_files"]) for k in unc))
# test file
ht = head("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
lt = live("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
d = [x for x in difflib.unified_diff(ht, lt, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
chk("test file: only the census declaration (+1 comment) and the TAX22 lines (+1 comment, 2 edited lines) changed", len(d) <= 9, f"({len(d)} differing lines, lines {len(ht)} -> {len(lt)})")
for x in d:
    out.append("   " + x[:230])
out.append("   " + [x for x in lt if x.startswith("GOLD_OVERLAY_CENSUS")][0])
out.append("ALL PASS" if ok else "SOME FAIL")
(OUT / "e20_diff_vs_head.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
