# -*- coding: utf-8 -*-
"""build e23_apply.py (에이비엘생명보험 KR0070 D3 applier, scenario N4_ABL_FY2023) from the audited Lotte variant (kr0003_lotte/e23_apply.py, itself derived from e21_apply.py) by asserted string substitutions.
Every substitution must hit exactly once; the audited logic (guards, real build_pl()/build_csm() sandbox deltas, sandbox emitter, ledger/census/test updates, verify, revert) is unchanged.
Differences to the Lotte variant: this load adds NO null_dangi/set_dangi pins (the single quarters follow the cumulatives: both sides restated), so the null_dangi doc key is dropped; it replaces
1 PL + 2 CSM owner-gold entries in place (the apply contract carries them as gold_replace / csm_gold_replace)."""
from pathlib import Path

SRC = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0003_lotte/e23_apply.py")
DST = Path(__file__).resolve().parent / "e23_apply.py"
s = SRC.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:100])
    s = s.replace(a, b)


# ---- header / paths
sub('"""Cell-level applier (parser/ifrs17, ticket 20261023T0900Z, D2: 롯데손해보험 KR0003 2023.4Q at the latest comparative).  Derived from e21_apply.py (audited in the READY-25 load).\nInput = e23_plan_lotte.json (apply_contract) produced by e23_plan.py (lotte) and re-read independently by kr0003_verify.py.',
    '"""Cell-level applier (parser/ifrs17, ticket 20261023T0900Z, D3: 에이비엘생명보험 KR0070 FY2023 2023.1Q-2023.4Q at the latest comparative).  Derived from the Lotte variant (kr0003_lotte/e23_apply.py) <- e21_apply.py (audited in the READY-25 load).\nInput = e23_plan_abl_final.json (apply_contract) produced by e23_plan.py (abl) and re-read independently by kr0070_verify.py.')
sub('"e23_d1_d3" / "kr0003_lotte"\nBACKUP', '"e23_d1_d3" / "kr0070_abl"\nBACKUP')
sub('"backup_before_apply" / "kr0003_lotte"', '"backup_before_apply" / "kr0070_abl"')
sub('scratchpad/e23_kr0003_tmp"', 'scratchpad/e23_kr0070_tmp"')
sub('PLAN = json.loads((EV / "e23_plan_lotte.json").read_text(encoding="utf-8"))', 'PLAN = json.loads((EV / "e23_plan_abl_final.json").read_text(encoding="utf-8"))')
sub('manifest_path = EV / "apply_manifest_e23_lotte.json"', 'manifest_path = EV / "apply_manifest_e23_abl.json"')

# ---- merge notes
a = s.index('MERGE_NOTE_KEY = "merge_note_20261023_e23_kr0003_lotte"')
b = s.index("SUBS = [")
new_notes = '''MERGE_NOTE_KEY = "merge_note_20261023_e23_kr0070_abl"
MERGE_NOTE = ("ticket 20261023T0900Z (parser/ifrs17, owner decision D3 of 2026-10-23): PL cells of 에이비엘생명보험 KR0070 FY2023 2023.1Q-2023.4Q refreshed to the latest comparative (separate basis, prior-year "
              "cumulative column of the FY2024 Q1/H1/Q3/annual reports rcept 20240516002045 / 20240814004092 / 20241114002738 / 20250331001358) via data/_gold/user_pl_cells.json (73 new set cells + 1 owner-gold "
              "cell replaced in place: 2023.1Q item 4; no single-quarter pins). Blocks that changed or appeared are the output of scripts/emit_pl_provenance.py (sandbox copy) for the post-apply masters. "
              "Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0070_abl/")
CSM_NOTE_KEY = "merge_note_20261023_e23_kr0070_abl_csm"
CSM_NOTE = ("ticket 20261023T0900Z (D3): CSM cells of 에이비엘생명보험 KR0070 FY2023 2023.1Q-2023.4Q set to the latest-filing (FY2024 quarterly/annual prior-period roll-forward, separate basis, issued-contract CSM, "
            "opening 7,585.3 in all four quarters) vector via data/_gold/user_csm_cells.json (18 new + 2 chain-forced owner-gold entries replaced in place: 2023.4Q items 1 and 4; owner_override flagged on these "
            "blocks). Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0070_abl/")
'''
s = s[:a] + new_notes + s[b:]

# ---- no null_dangi pins in this load
a = s.index("DOC_NULL = (")
b = s.index("\n\ndef rkey(r):")
s = s[:a].rstrip("\n") + "\n" + s[b:]
sub('    nd["_doc_e23_kr0003_20261023"] = DOC_NULL\n', '')

# ---- test file update: census comment, tax22 comment anchor
sub('"# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D2: 롯데손해보험 KR0003 2023.4Q refreshed to the latest comparative; no owner-gold cell replaced): "',
    '"# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3: 에이비엘생명보험 KR0070 FY2023 2023.1Q-2023.4Q refreshed to the latest comparative; 1 PL + 2 CSM owner-gold cells replaced in place): "')
sub('old_c = re.search(r"^# 2026-10-23 ticket 20261023T0900Z: KB라이프생명 FY2023 .*\\n", s, re.M)', 'old_c = re.search(r"^# 2026-10-23 ticket 20261023T0900Z: 롯데손해보험 2023.4Q .*\\n", s, re.M)')
sub('raise SystemExit("ABORT: the TAX22 comment of the KB라이프 load (ticket 20261023T0900Z) was not found")', 'raise SystemExit("ABORT: the TAX22 comment of the Lotte load (ticket 20261023T0900Z) was not found")')
sub('"# 2026-10-23 ticket 20261023T0900Z: 롯데손해보험 2023.4Q 최신 비교열 적재(D2)로 최신 비교열 판 버킷이 늘었다 -> 총 %d칸(실측).\\n" % n_new',
    '"# 2026-10-23 ticket 20261023T0900Z: 에이비엘생명보험 FY2023 2023.1Q-2023.4Q 최신 비교열 적재(D3)로 최신 비교열 판 버킷이 늘었다 -> 총 %d칸(실측).\\n" % n_new')
sub('"# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3: 에이비엘생명보험 KR0070 FY2023 2023.1Q-2023.4Q refreshed to the latest comparative; 1 PL + 2 CSM owner-gold cells replaced in place): "',
    '"# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3: 에이비엘생명보험 KR0070 FY2023 2023.1Q-2023.4Q refreshed to the latest comparative; 1 PL owner-gold cell replaced in place, 2 CSM chain-forced owner-gold cells removed because the approved value equals the builder source): "')

# ---- (ABL) the two chain-forced CSM gold entries are REMOVED (value == builder source -> a replaced entry would be a masked gold cell needing a ledger pin)
sub('PLANNED_C = {(e["code"], e["item"], e["quarter"]): e for e in C["csm_gold_new"] + C["csm_gold_replace"]}',
    'PLANNED_C = {(e["code"], e["item"], e["quarter"]): e for e in C["csm_gold_new"] + C["csm_gold_replace"] + C["csm_gold_remove"]}')
sub('''    for e in C["csm_gold_replace"]:
        k = (e["code"], e["item"], e["quarter"])
        ge = cgold_by.get(k)
        if ge is None or ge != e["old_entry"]:
            bad.append(("CSM gold entry missing/moved", k))''',
    '''    for e in C["csm_gold_replace"] + C["csm_gold_remove"]:
        k = (e["code"], e["item"], e["quarter"])
        ge = cgold_by.get(k)
        if ge is None or ge != e["old_entry"]:
            bad.append(("CSM gold entry missing/moved", k))''')
sub('''    for e in C["csm_gold_new"]:
        g["set"].append({"원보험사코드": e["code"], "항목번호": e["item"], "공시분기": e["quarter"], "값": e["value"], "was": e["was"], "why": e["why"]})
    return g''',
    '''    rm_c = {(e["code"], e["item"], e["quarter"]) for e in C["csm_gold_remove"]}
    n0 = len(g["set"])
    g["set"] = [x for x in g["set"] if (x["원보험사코드"], x["항목번호"], x["공시분기"]) not in rm_c]
    if n0 - len(g["set"]) != len(rm_c):
        raise SystemExit("ABORT: CSM gold removal did not hit every planned entry")
    for e in C["csm_gold_new"]:
        g["set"].append({"원보험사코드": e["code"], "항목번호": e["item"], "공시분기": e["quarter"], "값": e["value"], "was": e["was"], "why": e["why"]})
    if C["csm_gold_remove"]:
        g["_doc_e23_kr0070_20261023"] = ("2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3, owner 2026-10-23 approval): chain-forced owner-gold entries REMOVED (not replaced) because the approved value equals the CSM builder source "
                                         "value (a replaced entry would be a masked gold cell that needs a ledger pin). Removed entries (code, item, quarter, gold value, was, why verbatim): "
                                         + " || ".join("%s %s %s: gold %s, was %s, why 「%s」 -> builder value %s" % (e["code"], e["item"], e["quarter"], e["old_entry"]["값"], e["old_entry"]["was"], e["old_entry"]["why"], e["value"])
                                                       for e in C["csm_gold_remove"]))
    return g''')
sub('''    flagged = []
    have = {(e["code"], e["quarter"]) for e in C["csm_gold_new"] + C["csm_gold_replace"]}
    for c in new["cells"]:
        if c["item_block"] == "csm_waterfall" and (c["company_code"], c["quarter"]) in have and not c.get("owner_override"):
            c["owner_override"] = True
            flagged.append((c["company_code"], c["quarter"]))''',
    '''    flagged = []
    have = {(e["code"], e["quarter"]) for e in C["csm_gold_new"] + C["csm_gold_replace"]}
    for c in new["cells"]:
        if c["item_block"] == "csm_waterfall" and (c["company_code"], c["quarter"]) in have and not c.get("owner_override"):
            c["owner_override"] = True
            flagged.append((c["company_code"], c["quarter"]))
    # blocks whose last gold entry was removed no longer carry an owner override
    remaining = {(x["원보험사코드"], x["공시분기"]) for x in new_cgold["set"]}
    for e in C["csm_gold_remove"]:
        pair = (e["code"], e["quarter"])
        if pair in remaining:
            continue
        for c in new["cells"]:
            if c["item_block"] == "csm_waterfall" and (c["company_code"], c["quarter"]) == pair and c.get("owner_override"):
                del c["owner_override"]
                CPROV_CLEARED.append(pair)''')
sub('MERGE_NOTE_KEY = "merge_note_20261023_e23_kr0070_abl"', 'CPROV_CLEARED = []\nSTALE_NONE_OK = {("KR0070", 16, "2023.4Q")}\nMERGE_NOTE_KEY = "merge_note_20261023_e23_kr0070_abl"')
sub('''    if cen_c_new[0] != cen_c_old[0] + len(C["csm_gold_new"]):
        errs.append(f"CSM census gold cells {cen_c_new[0]} != expected {cen_c_old[0] + len(C['csm_gold_new'])}")''',
    '''    if cen_c_new[0] != cen_c_old[0] + len(C["csm_gold_new"]) - len(C["csm_gold_remove"]):
        errs.append(f"CSM census gold cells {cen_c_new[0]} != expected {cen_c_old[0] + len(C['csm_gold_new']) - len(C['csm_gold_remove'])}")''')
sub('''| {f"CSM|{e['code']}|{e['quarter']}|{e['item']}" for e in C["csm_gold_replace"]}''',
    '''| {f"CSM|{e['code']}|{e['quarter']}|{e['item']}" for e in C["csm_gold_replace"] + C["csm_gold_remove"]}''')
sub('''(+{len(c1['set']) - len(c0['set'])}, {len(C['csm_gold_replace'])} replaced in place)")''',
    '''({len(C['csm_gold_new'])} new, {len(C['csm_gold_replace'])} replaced in place, {len(C['csm_gold_remove'])} removed)")''')
sub('''    pr(f"CSM provenance: owner_override flagged on {len(P['cprov_flagged'])} blocks: {P['cprov_flagged']}")''',
    '''    pr(f"CSM provenance: owner_override flagged on {len(P['cprov_flagged'])} blocks: {P['cprov_flagged']}; owner_override cleared (last gold entry removed) on {CPROV_CLEARED}")''')
# ---- (ABL) stale-None single quarter: a live 값_당분기 that is None only because an older hand load never derived it (TODO_parser_ifrs17 item 7: 369 rows) is filled by the new derivation when both cumulatives are adopted here
sub('''        if k in p3m and x[6] is not None and abs(x[6] - p3m[k]) <= 1e-6 and x[5] == x[3]:
            allowed_pre.append((k, x[2], x[6], p3m[k]))
        else:''',
    '''        if k in p3m and x[6] is not None and abs(x[6] - p3m[k]) <= 1e-6 and x[5] == x[3]:
            allowed_pre.append((k, x[2], x[6], p3m[k]))
        elif k in STALE_NONE_OK and x[2] is None and x[1] == x[3] and x[4] is not None and x[6] is not None and _stale_none_ok(k, new_by):
            allowed_pre.append((k, x[2], x[6], "stale None filled by the derivation new cumulative - new previous-quarter cumulative"))
        else:''')
sub('''def expected_dangi():''',
    '''def _stale_none_ok(k, new_by):
    """the new 값_당분기 of k equals (new 값 of k) - (new 값 of the previous quarter of the same item): the cell is derived from two cumulatives that are both adopted/consistent in this load"""
    c, i, q = k
    pq = None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"
    if pq is None or (c, i, pq) not in new_by or new_by[(c, i, pq)]["값"] is None:
        return False
    return abs(new_by[k]["값_당분기"] - (new_by[k]["값"] - new_by[(c, i, pq)]["값"])) <= 1e-6


def expected_dangi():''')
DST.write_text(s, encoding="utf-8", newline="\n")
compile(s, str(DST), "exec")
print("wrote", DST, len(s))
assert "kr0003" not in s.replace("kr0003_lotte/e23_apply.py", ""), [l for l in s.splitlines() if "kr0003" in l]
