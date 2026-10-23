# -*- coding: utf-8 -*-
"""build e23_apply.py (현대해상 KR0009 D3 applier, scenario N6c_HD_FY2023_IRlegs) from the audited KDB variant (kr0072_kdb/e23_apply.py <- ABL variant <- Lotte variant <- e21_apply.py, audited in the READY-25 load)
by asserted string substitutions.  Every substitution must hit exactly once; the audited logic (guards, real build_pl()/build_csm() sandbox deltas, sandbox emitter, ledger/census/test updates, revert) is unchanged.
Differences to the KDB variant:
  * this load has NO set_dangi pins but 11 null_dangi additions (2023.4Q: restated annual vs unrestated 9M) -> a null_dangi doc key instead of the set_dangi doc key;
  * 6 PL cells are LOB legs read from the IR factsheet: the sandbox provenance emitter output is extended by `add_ir_lineage` (one extra source_files entry per IR file with sheet, cells, label / block / header
    cells, printed values) both in the apply and in --verify;
  * the live PL master holds hand-loaded 경영공시 values for 2023.1Q / 2023.2Q (items 1, 16, 22, 23, 24 and the Tier-2 legs) that a fresh build_pl() does not reproduce: LIVE_VS_BASE_OK is generated from the
    drift snapshot (drift_before.json) and written into live_vs_base_ok.json by snapshot_live_vs_base.py;
  * --verify compares the provenance sidecar with the emitter for the target company and requires that no block that matched BEFORE the load differs now (blocks that already differed in the backup are reported);
  * no PL owner gold is replaced; 3 chain-forced CSM gold entries are removed and 1 replaced (the plan's csm_gold_remove / csm_gold_replace)."""
from pathlib import Path

SRC = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/e23_apply.py")
DST = Path(__file__).resolve().parent / "e23_apply.py"
s = SRC.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:110])
    s = s.replace(a, b)


# ---- header / paths
sub('"""Cell-level applier (parser/ifrs17, ticket 20261023T0900Z, D3: 케이디비생명보험 KR0072 FY2023 2023.1Q-2023.4Q at the latest comparative).  Derived from the ABL variant (kr0070_abl/e23_apply.py) <- Lotte variant <- e21_apply.py (audited in the READY-25 load).\nInput = e23_plan_kdb_final.json (apply_contract) produced by e23_plan.py (kdb) and re-read independently by kr0072_verify.py.',
    '"""Cell-level applier (parser/ifrs17, ticket 20261023T0900Z, D3: 현대해상 KR0009 FY2023 2023.1Q-2023.4Q at the latest comparative, LOB legs from the IR factsheet).  Derived from the KDB variant (kr0072_kdb/e23_apply.py) <- ABL variant <- Lotte variant <- e21_apply.py (audited in the READY-25 load).\nInput = e23_plan_hd_final.json (apply_contract) produced by e23_plan.py (hd) and re-read independently by kr0009_verify.py.')
sub('"e23_d1_d3" / "kr0072_kdb"\nBACKUP', '"e23_d1_d3" / "kr0009_hyundai"\nBACKUP')
sub('"backup_before_apply" / "kr0072_kdb"', '"backup_before_apply" / "kr0009_hyundai"')
sub('scratchpad/e23_kr0072_tmp"', 'scratchpad/e23_kr0009_tmp"')
sub('PLAN = json.loads((EV / "e23_plan_kdb_final.json").read_text(encoding="utf-8"))', 'PLAN = json.loads((EV / "e23_plan_hd_final.json").read_text(encoding="utf-8"))')
sub('manifest_path = EV / "apply_manifest_e23_kdb.json"', 'manifest_path = EV / "apply_manifest_e23_hd.json"')

# ---- merge notes + documented allowances
a = s.index("STALE_NONE_OK = set()")
b = s.index("SUBS = [")
new_notes = '''STALE_NONE_OK = set()
# live master cells that a FRESH build_pl() with the live gold does not reproduce: (live master value, baseline-build value).  The live PL master holds the 경영공시 PDF values (억원 rounding) that the
# 2026 backfill rounds wrote directly into PL_breakdown.json for the 2023.1Q / 2023.2Q Tier-1 items (not in the gold overlay), and a few builder literals; the apply replaces the planned ones by gold.
# Generated from drift_before.json (snapshot_live_vs_base.py -> live_vs_base_ok.json): planned cells whose live value differs from the fresh build.
_LVB = EV / "live_vs_base_ok.json"
LIVE_VS_BASE_OK = {(r[0], int(r[1]), r[2]): (r[3], r[4]) for r in json.loads(_LVB.read_text(encoding="utf-8"))} if _LVB.exists() else {}
MERGE_NOTE_KEY = "merge_note_20261023_e23_kr0009_hd"
MERGE_NOTE = ("ticket 20261023T0900Z (parser/ifrs17, owner decision D3 of 2026-10-23): PL cells of 현대해상 KR0009 FY2023 2023.1Q / 2023.2Q / 2023.4Q refreshed to the latest comparative (separate basis, prior-year "
              "cumulative column of the FY2024 Q1 / H1 / annual reports rcept 20240516002153 / 20240814004187 / 20250313001346) via data/_gold/user_pl_cells.json (57 new set cells, no owner PL gold replaced; "
              "2023.1Q / 2023.2Q items 2 / 13 / 14 = LOB insurance results of the IR factsheet '(3) UW Income' (owner D3 2026-10-23 allowed the IR factsheet as the leg source because the later DART filings print no "
              "quarterly LOB breakdown): the IR lineage (file, sheet, cells) is listed in the source_files entries with how=ir_factsheet_uw_income_prior_year_cumulative; 11 null_dangi single-quarter cells = 2023.4Q "
              "items whose annual comparative is restated while the 9M comparative is not). Blocks that changed or appeared are the output of scripts/emit_pl_provenance.py (sandbox copy) for the post-apply masters "
              "plus the IR lineage entries. Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0009_hyundai/")
DOC_NULL = ("2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3): 값_당분기 left blank (null_dangi) for KR0009 현대해상 2023.4Q items 1 / 4 / 17 / 19 / 20 / 22 / 23 / 24 / 25 / 27 / 31: the 4Q cumulative is taken from the "
            "FY2024 annual report (restated comparative) while the 9M cumulative of the FY2024 Q3 report equals the originally filed 2023.3Q value (the annual restatement is not in the 9M comparative), so the difference "
            "of the two cumulatives is not the fourth quarter (owner rule 2026-10-22). Evidence kr0009_verify.txt section D4.")
CSM_NOTE_KEY = "merge_note_20261023_e23_kr0009_hd_csm"
CSM_NOTE = ("ticket 20261023T0900Z (D3): CSM cells of 현대해상 KR0009 FY2023 2023.1Q-2023.4Q set to the latest-filing (FY2024 quarterly/annual prior-period roll-forward, separate basis, issued long-term contracts, "
            "opening 83,515.4 in all four quarters) vector via data/_gold/user_csm_cells.json (14 new + 1 chain-forced owner-gold entry replaced in place: 2023.4Q item 4 + 3 chain-forced entries removed: 2023.3Q items 1 / 4 "
            "and 2023.4Q item 1, because the approved value equals the CSM builder source value; owner_override flagged on the 2023.1Q / 2023.2Q blocks, kept on 2023.4Q, cleared on 2023.3Q). "
            "Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0009_hyundai/")


def add_ir_lineage(doc):
    """extend the sandbox-emitter output with the IR factsheet lineage of the LOB-leg gold cells: one extra source_files entry per (block, IR file) after the owner_gold_overlay entry"""
    out = copy.deepcopy(doc)
    contract_items = {4, 5, 6, 9, 10, 11, 13, 14}          # scripts/emit_pl_provenance.py::PL_CONTRACT_NOTES
    by_block = {}
    for lin in PLAN.get("ir_lineage", []):
        blk = "contract_notes" if lin["item"] in contract_items else "income_statement"
        by_block.setdefault((lin["code"], lin["quarter"], blk), []).append(lin)
    seen = set()
    for c in out["cells"]:
        key = (c["company_code"], c["quarter"], c["item_block"])
        if key not in by_block:
            continue
        gold_items = next((sf["items"] for sf in c["source_files"] if sf.get("how") == "owner_gold_overlay"), [])
        for lin in by_block[key]:
            if lin["item"] not in gold_items:
                raise SystemExit(f"ABORT: IR lineage item {lin['item']} of {key} is not an owner_gold_overlay item of the emitted block")
        for f in sorted({lin["file"] for lin in by_block[key]}):
            ls = sorted((lin for lin in by_block[key] if lin["file"] == f), key=lambda x: x["item"])
            c["source_files"].append({"file": f, "how": "ir_factsheet_uw_income_prior_year_cumulative", "items": [lin["item"] for lin in ls], "sheet": ls[0]["sheet"],
                                      "cells": {str(lin["item"]): lin["cell"] for lin in ls}, "label_cells": {str(lin["item"]): lin["label_cell"] for lin in ls},
                                      "block_cells": {str(lin["item"]): lin["block_cell"] for lin in ls}, "header_cell": ls[0]["header_cell"], "header": ls[0]["header"], "unit": ls[0]["unit"],
                                      "printed": {str(lin["item"]): lin["printed"] for lin in ls}, "total_cell": ls[0]["total_cell"],
                                      "role": "LOB leg of 보험손익 read from the IR factsheet (owner 2026-10-23 D3: allowed because the later DART filings print no quarterly LOB breakdown); the three legs add up to the DART separate-basis 보험손익"})
        seen.add(key)
    if seen != set(by_block):
        raise SystemExit(f"ABORT: IR lineage blocks not found in the emitter output: {sorted(set(by_block) - seen)}")
    return out


'''
s = s[:a] + new_notes + s[b:]

# ---- null_dangi doc key (instead of the set_dangi doc key)
sub('''    sd["cells"] = [x for x in sd["cells"] if (x[0], x[1], int(x[2])) not in rm_s]
    sd["_doc_e23_kr0072_20261023"] = DOC_SET
    return g''', '''    sd["cells"] = [x for x in sd["cells"] if (x[0], x[1], int(x[2])) not in rm_s]
    if C["null_dangi_add"]:
        nd["_doc_e23_kr0009_20261023"] = DOC_NULL
    return g''')

# ---- CSM gold doc key
sub('g["_doc_e23_kr0072_20261023"]', 'g["_doc_e23_kr0009_20261023"]')

# ---- provenance: IR lineage on the emitter output (apply) and in --verify
sub('''    emit_new = run_emitter(sub_new, new_gold, "apply_new")''', '''    emit_new = add_ir_lineage(run_emitter(sub_new, new_gold, "apply_new"))''')
sub('''    emit_doc = run_emitter(sub, gold, "verify")
    live_prov = load_json(F["PROV"])
    lk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in live_prov["cells"] if c["company_code"] in CODES}
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_doc["cells"] if c["company_code"] in CODES}
    bad = [k for k in set(lk) | set(ek) if lk.get(k) != ek.get(k)]
    print(f"verify PL provenance: emitter reproduces {len(ek) - len(bad)}/{len(ek)} target-company blocks (sidecar has {len(lk)})")
    for k in sorted(bad)[:10]:
        print("   provenance block differs from emitter:", k)
    return ok1 and ok1b and ok1c and ok2 and ok3 and ok4 and ok5 and not bad''',
    '''    emit_doc = add_ir_lineage(run_emitter(sub, gold, "verify"))
    live_prov = load_json(F["PROV"])
    lk = {(c["company_code"], c["quarter"], c["item_block"]): c for c in live_prov["cells"] if c["company_code"] in CODES}
    ek = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_doc["cells"] if c["company_code"] in CODES}
    bad = [k for k in set(lk) | set(ek) if lk.get(k) != ek.get(k)]
    print(f"verify PL provenance: emitter (+ IR lineage) reproduces {len(ek) - len(bad)}/{len(ek)} target-company blocks (sidecar has {len(lk)})")
    # blocks that already differed from the emitter BEFORE the load (backup copies) are pre-existing; only NEW differences fail
    pre_rows = json.loads((BACKUP / F["PL"]).read_text(encoding="utf-8"))
    pre_gold = json.loads((BACKUP / F["GOLD"]).read_text(encoding="utf-8"))
    pre_prov = json.loads((BACKUP / F["PROV"]).read_text(encoding="utf-8"))
    emit_pre = run_emitter([r for r in pre_rows if r["원보험사코드"] in CODES], pre_gold, "verify_pre")
    lkp = {(c["company_code"], c["quarter"], c["item_block"]): c for c in pre_prov["cells"] if c["company_code"] in CODES}
    ekp = {(c["company_code"], c["quarter"], c["item_block"]): c for c in emit_pre["cells"] if c["company_code"] in CODES}
    bad_pre = {k for k in set(lkp) | set(ekp) if lkp.get(k) != ekp.get(k)}
    new_bad = [k for k in bad if k not in bad_pre]
    fixed = sorted(k for k in bad_pre if k not in set(bad))
    print(f"verify PL provenance: blocks differing from the emitter before the load {len(bad_pre)}, now {len(bad)}; NEW differences {len(new_bad)}; differences the load resolved {len(fixed)}")
    for k in sorted(bad)[:12]:
        print("   provenance block differs from emitter:", k, "(pre-existing)" if k in bad_pre else "(NEW)")
    return ok1 and ok1b and ok1c and ok2 and ok3 and ok4 and ok5 and not new_bad''')

# ---- test file update: census comment, tax22 comment anchor
sub('"# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3: 케이디비생명보험 KR0072 FY2023 2023.1Q-2023.4Q refreshed to the latest comparative; 4 PL + 5 CSM owner-gold cells replaced in place, 2 CSM chain-forced owner-gold cells removed because the approved value equals the builder source, ledger pins of the 3 replaced masked CSM gold cells removed): "',
    '"# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3: 현대해상 KR0009 FY2023 2023.1Q / 2023.2Q / 2023.4Q refreshed to the latest comparative (LOB legs from the IR factsheet); 57 PL cells added, 1 CSM chain-forced owner-gold cell replaced in place, 3 CSM chain-forced owner-gold cells removed because the approved value equals the builder source, no ledger pin touched): "')
sub('"# 2026-10-23 ticket 20261023T0900Z: 케이디비생명보험 FY2023 2023.1Q-2023.4Q 최신 비교열 적재(D3)로 최신 비교열 판 버킷이 늘었다 -> 총 %d칸(실측).\\n" % n_new',
    '"# 2026-10-23 ticket 20261023T0900Z: 현대해상 FY2023 2023.1Q-2023.4Q 최신 비교열 적재(D3)로 최신 비교열 판 버킷이 늘었다 -> 총 %d칸(실측).\\n" % n_new')
sub('import copy\nimport importlib.util', 'import copy\nimport importlib.util')            # sanity: copy is imported already
DST.write_text(s, encoding="utf-8", newline="\n")
compile(s, str(DST), "exec")
print("wrote", DST, len(s))
left = [l for l in s.splitlines() if "kr0072" in l or "KR0072" in l or "KDB" in l and "KDB variant" not in l]
print("remaining KDB mentions:", len(left))
for l in left[:20]:
    print("   ", l[:200])
