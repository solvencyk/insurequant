"""k1_write_outputs.py -- applied_blocks.csv (one row per changed cell, 65) and held_blocks.csv (one row per dry-run block that was NOT applied, 72).

Sources: plans/*.json (final plans with evidence), the dry-run block_verdicts.csv (88 blocks) and core_extract_all.json (own / F+1 / F+2 prints).
CSV = UTF-8 with BOM (Excel).  READ-ONLY on everything except the two output files.
"""
import csv
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/kics_latest_prior_apply_20261012")
from lib_apply import *  # noqa: F401,F403,E402

utf8_stdout()
core = read_json(DRY / "core_extract_all.json")
verd = list(csv.DictReader(open(DRY / "block_verdicts.csv", encoding="utf-8-sig")))
QS = [f"{y}.{q}Q" for y in (2023, 2024, 2025, 2026) for q in (1, 2, 3, 4)][:14]
ledger = read_json(REPO / "data" / "_gold" / "kics_restatement_ledger.json")["entries"]


def qadd(q, n):
    i = QS.index(q) + n
    return QS[i] if 0 <= i < len(QS) else None


def per(q):
    return f"FY{q[:4]}_Q{q[5]}"


def printed(code, fq, col, item):
    rec = core.get(f"{per(fq)}|{code}") if fq else None
    if not rec or rec["status"] not in ("OK", "VISION_ONLY"):
        return None
    v = rec["cols"].get(col, {}).get(str(item))
    return None if v is None else v[0]


# ---------------------------------------------------------------- applied_blocks.csv
HEAD = ["block_id", "code", "company", "quarter", "item", "item_name", "field", "kind", "class", "old", "new", "new_value_source(latest prior column)",
        "own_filing_print", "own_filing_source", "f1_print(next filing prev col)", "f1_source", "f2_print(2 filings later prev2 col)", "f2_source",
        "direct_check", "rendered_pages_viewed", "dryrun_flags", "ledger_entry", "plan_file"]
CLASS_TXT = {"R": "R restatement (own print = old master value; later filings print the new value)",
             "C": "C master correction (own filing already prints the new value; master held a derived/mis-read number)",
             "T": "T own-filing typo (own filing prints 2,481; master held the component sum 24,808; later filings print 24,807)"}
rows_out = []
for bid in APPLIED:
    plan = load_plan(bid)
    code, q = plan["code"], plan["quarter"]
    ev = {e["item"]: e for e in plan["evidence"]}
    viewed = "; ".join(plan.get("viewed_pages") or [])
    for e in plan["edits"]:
        it = e["item"]
        w = ev.get(it)
        isprim = e["kind"] == "primary"
        led = f"{code}|{q}|{it}" in ledger and isprim
        direct = ""
        if isprim:
            direct = "PDF text-layer rows of the own / F+1 / F+2 pages read directly (b1_pdf_rows.txt)"
            if viewed:
                direct += "; rendered pages viewed (img/, see rendered_pages_viewed)"
            if any(t in (w["own_src"] or "") for t in ("image-only", "scanned", "vector/image")):
                direct += "; own-filing print read from the render (image-only / scanned page)"
        rows_out.append([
            bid, code, plan["company"], q, it, (w or {}).get("item_name") or "", e["field"], e["kind"],
            CLASS_TXT[w["class"]] if isprim else ("mirror of the 값 cell (전=후)" if e["kind"] == "post_mirror" else "derived ratio (existing formula)"),
            e["old"], e["new"],
            e["src"] if isprim or e["kind"] == "post_mirror" else e["col"],
            (w or {}).get("own_print", ""), (w or {}).get("own_src", ""), (w or {}).get("f1_print", ""), (w or {}).get("f1_src", ""),
            (w or {}).get("f2_print", ""), (w or {}).get("f2_src", ""),
            direct, viewed if isprim else "", "; ".join(plan.get("dryrun_flags") or []), "Y" if led else "N", f"plans/{bid}.json"])
with open(OUT / "applied_blocks.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(HEAD)
    w.writerows(rows_out)
print("applied_blocks.csv rows:", len(rows_out), "| primary", sum(1 for r in rows_out if r[7] == "primary"), "| ledger entries Y:", sum(1 for r in rows_out if r[21] == "Y"))

# ---------------------------------------------------------------- held_blocks.csv
# the 9 candidates held by ticket criterion 4 (the changed cell differs between the two later disclosures) + 1 held for rebuild durability
CRIT4 = ["KR0050_2023.1Q", "KR0051_2023.3Q", "KR0069_2023.2Q", "KR0069_2024.3Q", "KR0083_2025.2Q", "KR0095_2024.3Q", "KR0099_2024.2Q", "KR0099_2024.4Q", "KR0100_2025.2Q"]
DURABILITY = ["KR0070_2024.3Q"]
HHEAD = ["block_id", "code", "company", "quarter", "dryrun_category", "hold_group", "hold_reason", "diffs(item:master->latest)", "n_items_differ", "max_abs_delta",
         "dryrun_flags", "dryrun_decision_outcome", "dryrun_outcome_note", "applier", "f1_vs_f2_on_changed_cells", "latest_source"]
held = []
applied = set(APPLIED)
for r in verd:
    bid = r["id"]
    if bid in applied:
        continue
    cat = r["ticket_category"]
    f1f2 = ""
    if bid in CRIT4 or bid in DURABILITY:
        plan = read_json(DRY / "plans" / f"{bid}.json")
        code, q = plan["code"], plan["quarter"]
        parts = []
        for it in sorted({e["item"] for e in plan["edits"]}):
            e = [x for x in plan["edits"] if x["item"] == it and x["field"] == "값"][0]
            parts.append(f"item{it}: master {e['old']} | own {printed(code, q, 'cur', it)} | F+1 {printed(code, qadd(q, 1), 'prev', it) if qadd(q, 1) else 'NA'} | F+2 {printed(code, qadd(q, 2), 'prev2', it) if qadd(q, 2) else 'NA'} -> latest {e['new']}")
        f1f2 = " ; ".join(parts)
    if bid in CRIT4:
        grp = "ticket criterion 4"
        why = ("The two later disclosures print DIFFERENT values for the changed cell (the issuer re-printed it again, so the latest column also wobbles): "
               "F+1 (next filing's prior column) still shows the master/own value and only F+2 shows the new one. Held and listed, not applied (owner: only the blocks certainly closed by every check).")
    elif bid in DURABILITY:
        grp = "durability (ticket step 4)"
        why = ("Value is certain (own filing, F+1 and F+2 all print 1 for item 22; master held 0) but the standard derived step scripts/recalc_kics_derived.py zeroes item 22 again "
               "whenever item14 == item15 and item23 == 0 (verified in memory: starting from 1 it returns 0), so the corrected cell would silently revert on the next recalc. "
               "Fixing needs a recalc rule change (outside this ticket); the master keeps 0 (+/-1 eok on a minor line).")
    else:
        grp = "not a candidate"
        why = (r["category_reasons"] or r["outcome_note"] or cat)
    held.append([bid, r["code"], r["company"], r["quarter"], cat, grp, why, r["diffs"], r["n_items_differ"], r["max_abs_delta"], r["flags"],
                 r["decision_table_outcome"], r["outcome_note"], r["applier"], f1f2, r["latest_source"]])
held.sort(key=lambda x: (x[5], x[1], x[3]))
with open(OUT / "held_blocks.csv", "w", encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(HHEAD)
    w.writerows(held)
from collections import Counter
print("held_blocks.csv rows:", len(held), dict(Counter(h[5] for h in held)), "| by dry-run category:", dict(Counter(h[4] for h in held)))
assert len(held) + len(APPLIED) == len(verd) == 88, (len(held), len(APPLIED), len(verd))
