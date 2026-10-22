# -*- coding: utf-8 -*-
"""Read-only, independent of the applier: cell-level diff of every file the apply writes vs git HEAD.
Asserts: PL master changed rows only of the 7 companies, only fields 값 / 값_당분기, 값 changes == the 171 manifest cells with the manifest values,
no row added/removed/reordered; gold: no existing set entry modified, added == manifest; null/set_dangi existing cells untouched; provenance: only blocks of the 7 companies changed + new merge note key;
test file: exactly the census line (+ comment)."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant"
OUT = Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")
CODES = {"KR0005", "KR0032", "KR0070", "KR0082", "KR0083", "KR0087", "KR0104"}
man = json.loads((OUT / "e19_manifest.json").read_text(encoding="utf-8"))


def head(rel):
    return subprocess.run(["git", "-C", ROOT, "show", f"HEAD:{rel}"], capture_output=True, stdin=subprocess.DEVNULL).stdout


def live(rel):
    return open(f"{ROOT}/{rel}", "rb").read().replace(b"\r\n", b"\n")   # working tree is CRLF (core.autocrlf=true), git blobs are LF


out, ok = [], True


def chk(name, cond, extra=""):
    global ok
    ok = ok and bool(cond)
    out.append(f"[{'PASS' if cond else 'FAIL'}] {name} {extra}")


key = lambda r: (r["원보험사코드"], r["항목번호"], r["공시분기"])
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
chk("no changed row outside the 7 companies", not outside, f"({len(outside)})")
chk("no changed field other than 값 / 값_당분기", not other_field, f"({other_field[:3]})")
want = {(g["원보험사코드"], g["항목번호"], g["공시분기"]): g["값"] for g in man["gold_set"]}
chk("값 changed cells == the 171 manifest cells", set(chg_val) == set(want), f"(changed {len(chg_val)}, manifest {len(want)})")
chk("every changed 값 equals the manifest value", all(lm[k]["값"] == want[k] for k in chg_val if k in want))
chk("every changed 값 had the manifest 'was' value before", all(abs((hm[k]["값"] or 0) - g["was"]) <= 5e-4 for g in man["gold_set"] for k in [(g["원보험사코드"], g["항목번호"], g["공시분기"])] if g["was"] is not None))
nd = {(c, i, q) for c, q, i in man["null_dangi"]}
sd = {(c, i, q): v for c, q, i, v, _s in man["set_dangi"]}
chk("null_dangi cells are blank in the master", all(lm[k]["값_당분기"] is None and lm[k]["값"] is not None for k in nd))
chk("set_dangi cells hold the printed 3-month value", all(abs(lm[k]["값_당분기"] - v) <= 1e-9 for k, v in sd.items()))
by_co = {}
for k in chg_dangi:
    by_co[k[0]] = by_co.get(k[0], 0) + 1
out.append(f"   값_당분기 changed {len(chg_dangi)} cells {dict(sorted(by_co.items()))}; of which dangi-only (값 unchanged) {len(set(chg_dangi) - set(chg_val))}")
# byte-level: rows that did not change are byte-identical objects -> check file prefix/suffix formatting stays (indent/newline)
hb, lb = head("PL_breakdown.json"), live("PL_breakdown.json")
chk("file ends the same way and uses the same newline convention", (b"\r\n" in hb) == (b"\r\n" in lb) and hb[-3:] == lb[-3:])
# gold
hg = json.loads(head("data/_gold/user_pl_cells.json").decode("utf-8"))
lg = json.loads(live("data/_gold/user_pl_cells.json").decode("utf-8"))
gk = lambda e: (e["원보험사코드"], e["항목번호"], e["공시분기"])
chk("gold: existing set entries untouched (prefix equal)", lg["set"][:len(hg["set"])] == hg["set"], f"({len(hg['set'])} -> {len(lg['set'])})")
added = lg["set"][len(hg["set"]):]
chk("gold: added entries == manifest (value, was, note)", [(gk(e), e["값"], e["was"], e["note"]) for e in added] == [(gk(e), e["값"], e["was"], e["note"]) for e in man["gold_set"]])
chk("gold: every added entry has keys 원보험사코드/항목번호/공시분기/값/was/note only", all(set(e) == {"원보험사코드", "항목번호", "공시분기", "값", "was", "note"} for e in added))
chk("gold: null_dangi existing cells untouched, +17", lg["null_dangi"]["cells"][:len(hg["null_dangi"]["cells"])] == hg["null_dangi"]["cells"] and len(lg["null_dangi"]["cells"]) == len(hg["null_dangi"]["cells"]) + 17)
chk("gold: set_dangi existing cells untouched, +20", lg["set_dangi"]["cells"][:len(hg["set_dangi"]["cells"])] == hg["set_dangi"]["cells"] and len(lg["set_dangi"]["cells"]) == len(hg["set_dangi"]["cells"]) + 20)
chk("gold: existing doc keys untouched", all(lg[k] == hg[k] for k in hg if k not in ("set", "null_dangi", "set_dangi")) and all(lg["null_dangi"].get(k) == v for k, v in hg["null_dangi"].items() if k != "cells") and all(lg["set_dangi"].get(k) == v for k, v in hg["set_dangi"].items() if k != "cells"))
# provenance
hp = json.loads(head("PL_breakdown_provenance.json").decode("utf-8"))
lp = json.loads(live("PL_breakdown_provenance.json").decode("utf-8"))
pk = lambda c: (c["company_code"], c["quarter"], c["item_block"])
hpm, lpm = {pk(c): c for c in hp["cells"]}, {pk(c): c for c in lp["cells"]}
dif = sorted(k for k in lpm if hpm.get(k) != lpm[k])
chk("provenance: same block keys and order", [pk(c) for c in hp["cells"]] == [pk(c) for c in lp["cells"]])
chk("provenance: changed blocks only of the 7 companies", all(k[0] in CODES for k in dif), f"({len(dif)} blocks: {dif})")
newkeys = sorted(set(lp) - set(hp))
chk("provenance: only the new merge note key added at top level, others untouched", newkeys == ["merge_note_20261022_e19_latest_comparative"] and all(lp[k] == hp[k] for k in hp if k != "cells"), f"({newkeys})")
# every cell that changed value or single-quarter lies in a changed provenance block (income_statement / contract_notes of that company+quarter)
cover = {(k[0], k[1]) for k in dif}
chk("provenance: every cell whose 값 changed belongs to a replaced (company, quarter) block", all((k[0], k[2]) in cover for k in set(chg_val)))
nocover = sorted(k for k in set(chg_dangi) - set(chg_val) if (k[0], k[2]) not in cover)
out.append(f"   dangi-only cells in quarters without a changed provenance block (the sidecar records sources, not 값_당분기): {len(nocover)}")
# test file
ht = head("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
lt = live("tests/test_rule_coverage_manifest.py").decode("utf-8").split("\n")
import difflib
d = [x for x in difflib.unified_diff(ht, lt, lineterm="", n=0) if x[:1] in "+-" and x[:3] not in ("+++", "---")]
chk("test file: only the census declaration changed (+1 comment line)", len(lt) == len(ht) + 1 and len(d) == 3, f"({len(d)} differing lines, lines {len(ht)} -> {len(lt)})")
out.append("   " + [x for x in lt if x.startswith("GOLD_OVERLAY_CENSUS")][0])
out.append("ALL PASS" if ok else "SOME FAIL")
(OUT / "e19_diff_vs_head.txt").write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
print("\n".join(out))
