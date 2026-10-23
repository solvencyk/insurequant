# -*- coding: utf-8 -*-
"""build e23_apply.py (케이디비생명보험 KR0072 D3 applier, scenario N5_KDB_FY2023) from the audited ABL variant (kr0070_abl/e23_apply.py <- Lotte variant <- e21_apply.py, audited in the READY-25 load) by asserted
string substitutions.  Every substitution must hit exactly once; the audited logic (guards, real build_pl()/build_csm() sandbox deltas, sandbox emitter, ledger/census/test updates, verify, revert) is unchanged.
Differences to the ABL variant:
  * this load carries 8 set_dangi single-quarter pins (printed 3-month columns of the FY2024 Q2/Q3 reports) -> a set_dangi doc key;
  * it REPLACES 4 PL + 5 CSM owner-gold entries in place (the ABL load replaced 1 PL) and removes 2 chain-forced CSM entries (as ABL);
  * the 4 replaced PL gold entries 2023.2Q/3Q items 7 are STALE: the live master cell holds the formula value 3-(4+5+6) of the corrected legs (hand-fixed 2026-10-11, A2 leg fix) while the gold entry holds the value
    from before the leg fix, i.e. master != gold for exactly those two cells; the guard accepts that only for the two documented cells (GOLD_MASTER_DRIFT_OK) and requires master == plan `old`;
  * 3 ledger pins of replaced masked CSM gold cells vanish (REMOVED, never added)."""
from pathlib import Path

SRC = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e23_d1_d3/kr0070_abl/e23_apply.py")
DST = Path(__file__).resolve().parent / "e23_apply.py"
s = SRC.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:110])
    s = s.replace(a, b)


# ---- header / paths
sub('"""Cell-level applier (parser/ifrs17, ticket 20261023T0900Z, D3: 에이비엘생명보험 KR0070 FY2023 2023.1Q-2023.4Q at the latest comparative).  Derived from the Lotte variant (kr0003_lotte/e23_apply.py) <- e21_apply.py (audited in the READY-25 load).\nInput = e23_plan_abl_final.json (apply_contract) produced by e23_plan.py (abl) and re-read independently by kr0070_verify.py.',
    '"""Cell-level applier (parser/ifrs17, ticket 20261023T0900Z, D3: 케이디비생명보험 KR0072 FY2023 2023.1Q-2023.4Q at the latest comparative).  Derived from the ABL variant (kr0070_abl/e23_apply.py) <- Lotte variant <- e21_apply.py (audited in the READY-25 load).\nInput = e23_plan_kdb_final.json (apply_contract) produced by e23_plan.py (kdb) and re-read independently by kr0072_verify.py.')
sub('"e23_d1_d3" / "kr0070_abl"\nBACKUP', '"e23_d1_d3" / "kr0072_kdb"\nBACKUP')
sub('"backup_before_apply" / "kr0070_abl"', '"backup_before_apply" / "kr0072_kdb"')
sub('scratchpad/e23_kr0070_tmp"', 'scratchpad/e23_kr0072_tmp"')
sub('PLAN = json.loads((EV / "e23_plan_abl_final.json").read_text(encoding="utf-8"))', 'PLAN = json.loads((EV / "e23_plan_kdb_final.json").read_text(encoding="utf-8"))')
sub('manifest_path = EV / "apply_manifest_e23_abl.json"', 'manifest_path = EV / "apply_manifest_e23_kdb.json"')

# ---- merge notes + documented allowances
a = s.index('STALE_NONE_OK = {("KR0070", 16, "2023.4Q")}')
b = s.index("SUBS = [")
new_notes = '''STALE_NONE_OK = set()
# live master cells that a FRESH build_pl() with the live gold does not reproduce: (live master value, baseline-build value).  Evidence: c05_drift_evidence.txt (live = formula value of the leg-corrected master,
# hand fix of the 2026-10-11 A2 round that was never put into the gold overlay; TODO_parser_ifrs17 open item "BS·PL 세부 백필 후속 ③").
#   items 7 (2023.2Q/3Q): live = 3-(4+5+6) of the corrected legs; baseline = the STALE owner-gold plug (the gold entry is replaced by this load)
#   items 12 (2023.2Q/3Q): live = 8-(9+10+11) of the corrected legs; baseline = the builder value from the uncorrected legs (override 3984 / uncorrected leg sum)
#   item 16 (2023.2Q): live = 5,400 (경영공시 PDF, 억원 rounding); baseline = None (the builder nulls item 16 where the old 보험손익 closes without it)
LIVE_VS_BASE_OK = {("KR0072", 7, "2023.2Q"): (-17294.0, -18990.0), ("KR0072", 7, "2023.3Q"): (-52310.275872, -44935.275872),
                   ("KR0072", 12, "2023.2Q"): (1790.0, 3984.0), ("KR0072", 12, "2023.3Q"): (12952.808227, 20566.808227), ("KR0072", 16, "2023.2Q"): (5400.0, None)}
MERGE_NOTE_KEY = "merge_note_20261023_e23_kr0072_kdb"
MERGE_NOTE = ("ticket 20261023T0900Z (parser/ifrs17, owner decision D3 of 2026-10-23): PL cells of 케이디비생명보험 KR0072 FY2023 2023.1Q-2023.4Q refreshed to the latest comparative (separate basis, prior-year "
              "cumulative column of the FY2024 Q1/H1/Q3/annual reports rcept 20240516000597 / 20240814000801 / 20241114000809 / 20250331002302) via data/_gold/user_pl_cells.json (61 new set cells + 4 owner-gold "
              "cells replaced in place: 2023.2Q and 2023.3Q items 4 and 7; 8 set_dangi single-quarter cells = printed 3-month columns). Blocks that changed or appeared are the output of scripts/emit_pl_provenance.py "
              "(sandbox copy) for the post-apply masters. Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/")
DOC_SET = ("2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3): 값_당분기 set to the 3-month column printed in the FY2024 Q2 / Q3 reports for KR0072 케이디비생명보험: 2023.2Q items 16 / 21 (the derivation differs from the "
           "printed 3-month column only by the 2-decimal rounding of the kept 2023.1Q cumulatives 2346.17 / -5425.7, whose exact print is a masked gold cell) and 2023.3Q items 17 / 18 / 20 / 22 / 24 / 31 (the FY2024 Q3 "
           "report implies a 6-month cumulative that is 726.922994 lower than the one printed in the FY2024 Q2 report: a second revision of the 2023 half-year comparative inside FY2024, so the difference of the two "
           "cumulatives is not the third quarter).")
CSM_NOTE_KEY = "merge_note_20261023_e23_kr0072_kdb_csm"
CSM_NOTE = ("ticket 20261023T0900Z (D3): CSM cells of 케이디비생명보험 KR0072 FY2023 2023.1Q-2023.4Q set to the latest-filing (FY2024 quarterly/annual prior-period roll-forward, separate basis, issued-contract CSM, "
            "opening 5,695.9 in all four quarters) vector via data/_gold/user_csm_cells.json (13 new + 5 class-A owner-gold entries replaced in place: 2023.1Q items 4/5/6 and 2023.2Q items 4/5 + 2 chain-forced entries "
            "removed: 2023.4Q items 1 and 4; owner_override flagged on the 2023.1Q-2023.3Q blocks and cleared on the 2023.4Q block). Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0072_kdb/")
'''
s = s[:a] + new_notes + s[b:]

# ---- guard: a replaced PL gold entry is compared with the plan's `old` (the live master value); master != gold only for the two documented stale plug cells
sub('''        r = cur.get(k)
        if r is None or not same(r.get("값"), e["was"]):
            bad.append(("PL master cell != old gold value", k, e["was"], None if r is None else r.get("값")))''',
    '''        r = cur.get(k)
        old_plan = PLAN_OLD[k]
        if r is None or not same(r.get("값"), old_plan):
            bad.append(("PL master cell != plan old value", k, old_plan, None if r is None else r.get("값")))
        elif not same(r.get("값"), e["was"]):
            gm = LIVE_VS_BASE_OK.get(k)
            if gm is None or not same(gm[1], e["was"]) or not same(gm[0], r.get("값")):
                bad.append(("PL master cell != old gold value and not a documented stale-gold cell", k, e["was"], r.get("값")))''')
sub('''PLANNED = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_new"] + C["gold_replace"]}''',
    '''PLANNED = {(e["code"], e["item"], e["quarter"]): e for e in C["gold_new"] + C["gold_replace"]}
PLAN_OLD = {(b["code"], c["item"], b["quarter"]): c["old"] for b in PLAN["buckets"] for c in b["cells"]}''')

# ---- set_dangi doc key
sub('''    sd["cells"] = [x for x in sd["cells"] if (x[0], x[1], int(x[2])) not in rm_s]
    return g''', '''    sd["cells"] = [x for x in sd["cells"] if (x[0], x[1], int(x[2])) not in rm_s]
    sd["_doc_e23_kr0072_20261023"] = DOC_SET
    return g''')

# ---- CSM gold doc key
sub('g["_doc_e23_kr0070_20261023"]', 'g["_doc_e23_kr0072_20261023"]')

# ---- documented stale-gold cells on the delta: live != fresh baseline build (= the gold value) and the apply writes the new derivation
sub('''        elif k in STALE_NONE_OK and x[2] is None and x[1] == x[3] and x[4] is not None and x[6] is not None and _stale_none_ok(k, new_by):
            allowed_pre.append((k, x[2], x[6], "stale None filled by the derivation new cumulative - new previous-quarter cumulative"))''',
    '''        elif k in STALE_NONE_OK and x[2] is None and x[1] == x[3] and x[4] is not None and x[6] is not None and _stale_none_ok(k, new_by):
            allowed_pre.append((k, x[2], x[6], "stale None filled by the derivation new cumulative - new previous-quarter cumulative"))
        elif k in LIVE_VS_BASE_OK and k in PLANNED and same(x[1], LIVE_VS_BASE_OK[k][0]) and same(x[3], LIVE_VS_BASE_OK[k][1]) and abs(x[5] - PLANNED[k]["value"]) <= 1e-9:
            allowed_pre.append((k, x[1], x[5], "documented live-vs-baseline drift (hand-fixed live cell): live %s, baseline %s, new = plan value" % tuple(LIVE_VS_BASE_OK[k])))
        elif k not in PLANNED and same(x[1], x[3]) and same(x[1], x[5]) and _follows_cumulatives(k, x, {rkey(r): r for r in live["PL"].obj}, new_by):
            allowed_pre.append((k, x[2], x[6], "single quarter only: live single = live cumulative - live previous cumulative, new single = same cumulative - new previous cumulative"))''')

# ---- baseline-build value check of the planned cells (documented live-vs-baseline pairs)
sub('''    for k, e in PLANNED.items():
        if not same(base_by[k]["값"], e["was"]):
            errs.append(f"PL baseline build value {k}: {base_by[k]['값']} != was {e['was']}")''',
    '''    for k, e in PLANNED.items():
        if k in LIVE_VS_BASE_OK:
            lv_, bs_ = LIVE_VS_BASE_OK[k]
            if not (same(base_by[k]["값"], bs_) and same(PLAN_OLD[k], lv_)):
                errs.append(f"PL baseline build value {k}: {base_by[k]['값']} / live {PLAN_OLD[k]} do not match the documented live-vs-baseline pair {LIVE_VS_BASE_OK[k]}")
        elif not same(base_by[k]["값"], e["was"]):
            errs.append(f"PL baseline build value {k}: {base_by[k]['값']} != was {e['was']}")''')
sub('''def _stale_none_ok(k, new_by):''', '''def _follows_cumulatives(k, x, live_by, new_by):
    """x = (key, live 값, live 값_당분기, base 값, base 값_당분기, new 값, new 값_당분기): the cumulative is unchanged and both single quarters are plain differences of cumulatives (live of live, new of new)"""
    c, i, q = k
    pq = None if q[5] == "1" else f"{q[:4]}.{int(q[5]) - 1}Q"
    if pq is None or x[2] is None or x[6] is None:
        return False
    lp, np_ = live_by.get((c, i, pq)), new_by.get((c, i, pq))
    if lp is None or np_ is None or lp["값"] is None or np_["값"] is None:
        return False
    return abs(x[2] - (x[1] - lp["값"])) <= 1e-6 and abs(x[6] - (x[5] - np_["값"])) <= 1e-6


def _stale_none_ok(k, new_by):''')

# ---- test file update: census comment, tax22 comment anchor
sub('"# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3: 에이비엘생명보험 KR0070 FY2023 2023.1Q-2023.4Q refreshed to the latest comparative; 1 PL owner-gold cell replaced in place, 2 CSM chain-forced owner-gold cells removed because the approved value equals the builder source): "',
    '"# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D3: 케이디비생명보험 KR0072 FY2023 2023.1Q-2023.4Q refreshed to the latest comparative; 4 PL + 5 CSM owner-gold cells replaced in place, 2 CSM chain-forced owner-gold cells removed because the approved value equals the builder source, ledger pins of the 3 replaced masked CSM gold cells removed): "')
sub('old_c = re.search(r"^# 2026-10-23 ticket 20261023T0900Z: 롯데손해보험 2023.4Q .*\\n", s, re.M)', 'old_c = re.search(r"^# 2026-10-23 ticket 20261023T0900Z: 에이비엘생명보험 FY2023 2023.1Q-2023.4Q .*\\n", s, re.M)')
sub('raise SystemExit("ABORT: the TAX22 comment of the Lotte load (ticket 20261023T0900Z) was not found")', 'raise SystemExit("ABORT: the TAX22 comment of the ABL load (ticket 20261023T0900Z) was not found")')
sub('"# 2026-10-23 ticket 20261023T0900Z: 에이비엘생명보험 FY2023 2023.1Q-2023.4Q 최신 비교열 적재(D3)로 최신 비교열 판 버킷이 늘었다 -> 총 %d칸(실측).\\n" % n_new',
    '"# 2026-10-23 ticket 20261023T0900Z: 케이디비생명보험 FY2023 2023.1Q-2023.4Q 최신 비교열 적재(D3)로 최신 비교열 판 버킷이 늘었다 -> 총 %d칸(실측).\\n" % n_new')
DST.write_text(s, encoding="utf-8", newline="\n")
compile(s, str(DST), "exec")
print("wrote", DST, len(s))
left = [l for l in s.splitlines() if "kr0070" in l or "KR0070" in l or "ABL" in l and "ABL variant" not in l and "ABL load" not in l]
print("remaining ABL mentions:", len(left))
for l in left[:20]:
    print("   ", l[:200])
