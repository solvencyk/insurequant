"""s7c_completeness_tables.py -- step 7c (READ-ONLY).  "Does the prior column of the later disclosure carry ALL verification units?" -- measured.

Verification units (owner definition 2026-10-12):
    odd quarters (1Q/3Q)  : up to the mid-level risk amounts = core table items 1..23  (17 생명장기 / 18 일반손해 / 19 시장 / 20 신용 / 21 운영 ...)
    even quarters (2Q/4Q) : down to the detailed risk amounts = core items 1..23 + 29..35 (life sub-risks) + 36..40 (market sub-risks) + 41..46 (IRR scenarios)
Two readings of "the prior column of the later disclosure":
    NEXT   = the next filing's 직전 column            F(Q+1)            (literal reading)
    LATEST = the latest filing carrying the quarter    F(Q+2) 전전/직전 반기 열, else F(Q+1)   (ticket item 4)
A block is COMPLETE when (core items present) AND (every sub-risk family the master needs has a prior-half page in that filing).
Core presence comes from s2c (PDF coordinates); sub-risk family presence from s7b (PDF text, prior marker + family keyword on the same page).
Output: completeness_blocks.csv, completeness_summary.txt
"""
import csv
import importlib.util
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_precedence_dryrun_20261012")
from lib_dry import *  # noqa: F401,F403,E402

utf8_stdout()
spec = importlib.util.spec_from_file_location("s7b", OUT / "s7b_pdf_subitem_match.py")
s7b = importlib.util.module_from_spec(spec)
sys.modules["s7b"] = s7b
spec.loader.exec_module(s7b)

rows = read_rows()
midx, names = master_index(rows)
codes = sorted(names)
ccomp = {(r["code"], r["quarter"]): r for r in read_json(OUT / "core_completeness.json")}
FAM_OF = s7b.FAM_OF


def needed_families(code, q):
    m = midx[(code, q)]
    fams = set()
    for it, fam in FAM_OF.items():
        if it in m:
            v = num(m[it][0])
            if v is not None and abs(v) >= 0.005:
                fams.add(fam)
    return fams


out = []
for code in codes:
    for q in QUARTERS[:-1]:
        if (code, q) not in midx:
            continue
        even = is_even(q)
        rec = {"code": code, "name": names[code], "quarter": q, "parity": "even" if even else "odd"}
        cc = ccomp[(code, q)]
        for label, key, qq in (("next", "next", qadd(q, 1)), ("latest", "latest", qadd(q, 2) or qadd(q, 1))):
            core = cc.get(key)
            if label == "latest":
                filing_q = (qadd(q, 2) if (cc["next2"] and cc["next2"]["readable"]) else qadd(q, 1))
            else:
                filing_q = qadd(q, 1)
            rec[f"{label}_filing"] = filing_q
            rec[f"{label}_core_readable"] = bool(core and core.get("readable"))
            rec[f"{label}_core_complete"] = bool(core and core.get("complete"))
            if even:
                need = needed_families(code, q)
                rec["needed_families"] = ",".join(sorted(need))
                if filing_q and core and core.get("readable"):
                    s = s7b.scan_pdf(period_of(filing_q), code, q)
                    if s["status"] == "OK":
                        present = set(s["fam"])
                        rec[f"{label}_families_present"] = ",".join(sorted(present & need))
                        rec[f"{label}_families_missing"] = ",".join(sorted(need - present))
                        rec[f"{label}_sub_complete"] = need <= present
                    else:
                        rec[f"{label}_families_present"] = rec[f"{label}_families_missing"] = None
                        rec[f"{label}_sub_complete"] = None
                        rec[f"{label}_sub_status"] = s["status"]
                else:
                    rec[f"{label}_sub_complete"] = None
            rec[f"{label}_complete"] = (rec[f"{label}_core_complete"] and (rec.get(f"{label}_sub_complete") is True)) if even else rec[f"{label}_core_complete"]
        out.append(rec)

keys = sorted({k for r in out for k in r})
with open(OUT / "completeness_blocks.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=keys)
    w.writeheader()
    for r in out:
        w.writerow(r)
write_json_lf(OUT / "completeness_blocks.json", out)

lines = []
lines.append("Completeness of the prior column of the later disclosure (core = PDF coordinates; sub-risk families = PDF text with prior marker)")
lines.append("denominator A = all blocks of that quarter type that have a later filing; denominator B = only blocks whose later filing is readable (text layer)")
for parity, qs in (("odd", ["1Q", "3Q"]), ("even", ["2Q", "4Q"])):
    for label in ("next", "latest"):
        for qtype in qs + ["all"]:
            sel = [r for r in out if r["parity"] == parity and (qtype == "all" or r["quarter"].endswith(qtype))]
            if label == "next":
                sel = [r for r in sel if r["next_filing"]]
            tot = len(sel)
            read = [r for r in sel if r[f"{label}_core_readable"]]
            core_ok = [r for r in read if r[f"{label}_core_complete"]]
            if parity == "even":
                scanned = [r for r in read if r.get(f"{label}_sub_complete") is not None]
                comp = [r for r in scanned if r[f"{label}_complete"]]
                sub_ok = [r for r in scanned if r[f"{label}_sub_complete"]]
                lines.append(f"{parity:4s} {qtype:3s} {label:6s}: blocks={tot:3d} readable={len(read):3d} core-complete={len(core_ok):3d} "
                             f"sub-families-present={len(sub_ok):3d}/{len(scanned):3d} COMPLETE={len(comp):3d}  "
                             f"=> {100*len(comp)/max(1,tot):.1f}% of A, {100*len(comp)/max(1,len(scanned)):.1f}% of B")
            else:
                lines.append(f"{parity:4s} {qtype:3s} {label:6s}: blocks={tot:3d} readable={len(read):3d} core-complete={len(core_ok):3d} COMPLETE={len(core_ok):3d}  "
                             f"=> {100*len(core_ok)/max(1,tot):.1f}% of A, {100*len(core_ok)/max(1,len(read)):.1f}% of B")
(OUT / "completeness_summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print("\n".join(lines))
