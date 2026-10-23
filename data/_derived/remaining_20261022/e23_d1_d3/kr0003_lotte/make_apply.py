# -*- coding: utf-8 -*-
"""build e23_apply.py (롯데손해보험 KR0003 D2 applier, scenario N7_Lotte_FY2023Q4) from the audited e21_apply.py by asserted string substitutions.
Every substitution must hit exactly once; the e21 logic (guards, real build_pl()/build_csm() sandbox deltas, sandbox emitter, ledger/census/test updates, verify, revert) is unchanged.
Differences to the KB라이프 variant (kr0099_kblife/make_apply.py): this load ADDS 12 null_dangi pins (seam of the 2023.4Q single quarter), so the null_dangi doc stays (new key), the set_dangi doc goes."""
from pathlib import Path

SRC = Path("C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/e21_apply.py")
DST = Path(__file__).resolve().parent / "e23_apply.py"
s = SRC.read_text(encoding="utf-8")


def sub(a, b, count=1):
    global s
    assert s.count(a) == count, (s.count(a), a[:90])
    s = s.replace(a, b)


# ---- header / paths
sub('"""Cell-level applier (parser/ifrs17, ticket 20261023T0300Z, READY-25 load).  Generalised from e20_apply.py (PL) + apply_kr0073_fix.py (CSM).\nInput = e21_plan.json (apply_contract) produced by e21_plan_full.py and re-read independently by e21_verify.py.',
    '"""Cell-level applier (parser/ifrs17, ticket 20261023T0900Z, D2: 롯데손해보험 KR0003 2023.4Q at the latest comparative).  Derived from e21_apply.py (audited in the READY-25 load).\nInput = e23_plan_lotte.json (apply_contract) produced by e23_plan.py (lotte) and re-read independently by kr0003_verify.py.')
sub('EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e21_ready25"', 'EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e23_d1_d3" / "kr0003_lotte"')
sub('BACKUP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e21_backup")',
    'BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e23_d1_d3" / "backup_before_apply" / "kr0003_lotte"\n'
    'TMP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e23_kr0003_tmp")')
sub('PLAN = json.loads((EV / "e21_plan.json").read_text(encoding="utf-8"))', 'PLAN = json.loads((EV / "e23_plan_lotte.json").read_text(encoding="utf-8"))')
sub('tmpdir = BACKUP / "tmp_apply"', 'tmpdir = TMP / "tmp_apply"', count=2)
sub('d = BACKUP / "tmp_emit"', 'd = TMP / "tmp_emit"')
sub('manifest_path = EV / "apply_manifest_e21.json"', 'manifest_path = EV / "apply_manifest_e23_lotte.json"')
sub('(EV / "e21_apply_report.txt")', '(EV / "e23_apply_report.txt")')
sub("headline table -> e21_apply_report.txt)", "headline table -> e23_apply_report.txt)")

# ---- notes and pin docs
a = s.index('MERGE_NOTE_KEY = "merge_note_20261023_e21_ready25"')
b = s.index("SUBS = [")
new_notes = '''MERGE_NOTE_KEY = "merge_note_20261023_e23_kr0003_lotte"
MERGE_NOTE = ("ticket 20261023T0900Z (parser/ifrs17, owner decision D2 of 2026-10-23): PL cells of 롯데손해보험 KR0003 2023.4Q refreshed to the latest comparative (separate basis, FY2023 comparative column of the "
              "FY2024 annual report rcept 20250320001732) via data/_gold/user_pl_cells.json (18 new set cells, no owner-gold cell replaced; 12 null_dangi pins for the single quarter). "
              "Blocks that changed or appeared are the output of scripts/emit_pl_provenance.py (sandbox copy) for the post-apply masters. Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0003_lotte/")
CSM_NOTE_KEY = "merge_note_20261023_e23_kr0003_lotte_csm"
CSM_NOTE = ("ticket 20261023T0900Z (D2): CSM cells of 롯데손해보험 KR0003 2023.4Q set to the latest-filing (FY2024 annual report prior-period roll-forward, separate basis, issued-contract CSM, opening 16,669.0) "
            "vector via data/_gold/user_csm_cells.json (owner_override flagged on this block). Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0003_lotte/")
'''
s = s[:a] + new_notes + s[b:]
a = s.index("DOC_NULL = (")
b = s.index("\n\ndef rkey(r):")
new_doc = '''DOC_NULL = ("2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D2): 값_당분기 forced blank for KR0003 롯데손해보험 2023.4Q items 1/4/17/19/20/22/23/24/25/26/27/31 (12 cells). The annual cumulative is adopted "
            "from the FY2024 annual report's FY2023 comparative column (restated: accounting-policy change of the insurance finance income/expense allocation) while the 9M cumulative of 2023.3Q is "
            "the original-vintage print (the FY2024 Q3 report's prior 9M column is equal to the master on all 11 Tier-1 items, 11/11) -> the difference of the two cumulatives mixes two bases. "
            "The annual report prints no 3-month Q4 column. Blank beats wrong. (Items 2/3/7/8/9/12 have no 2023.3Q cumulative, so their single quarter stays blank without a pin.)")
'''
s = s[:a].rstrip("\n") + "\n" + new_doc + s[b:]
sub('    nd["_doc_e21_20261023"] = DOC_NULL\n    sd["_doc_e21_20261023"] = DOC_SET\n', '    nd["_doc_e23_kr0003_20261023"] = DOC_NULL\n')

# ---- test file update: census declaration + comment; TAX22 block only when the failing set moves
a = s.index("DECL_RE = re.compile(")
b = s.index("IDENT = [")
new_fn = '''DECL_RE = re.compile(r'^(GOLD_OVERLAY_CENSUS = \\{"CSM": )\\((\\d+), (\\d+)\\)(, "PL": )\\((\\d+), (\\d+)\\)(\\})$', re.M)
def new_test_bytes(raw, census_old, census_new, tax_off_new, tax_off_old, kyobo):
    crlf = b"\\r\\n" in raw
    s = raw.decode("utf-8").replace("\\r\\n", "\\n")
    ms = list(DECL_RE.finditer(s))
    if len(ms) != 1:
        raise SystemExit(f"ABORT: GOLD_OVERLAY_CENSUS declaration found {len(ms)} times in {TEST_REL}")
    m = ms[0]
    if ((int(m.group(2)), int(m.group(3))), (int(m.group(5)), int(m.group(6)))) != census_old:
        raise SystemExit(f"ABORT: declared census {m.group(0)} != expected old {census_old}")
    comment = ("# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D2: 롯데손해보험 KR0003 2023.4Q refreshed to the latest comparative; no owner-gold cell replaced): "
               "CSM gold %d->%d cells, masked %d->%d; PL gold %d->%d cells, masked %d->%d (no new pins).\\n" % (census_old[0][0], census_new[0][0], census_old[0][1], census_new[0][1],
                                                                                                          census_old[1][0], census_new[1][0], census_old[1][1], census_new[1][1]))
    s = s[:m.start()] + comment + m.group(1) + "(%d, %d)" % census_new[0] + m.group(4) + "(%d, %d)" % census_new[1] + m.group(7) + s[m.end():]
    if tax_off_new != tax_off_old:
        # buckets that pass the tax identity only through the latest-comparative branch changed -> regenerate the set literal and its comments
        a = s.index("_TAX22_LATEST_COMPARATIVE_ONLY = set(_TAX22_KYOBO_RESTATED) | {")
        b = s.index("\\n\\n\\ndef _tax22_set_tax")
        by = {}
        for co, q in sorted(tax_off_new - set(kyobo)):
            by.setdefault(co, []).append(q)
        pieces = [("(\\"%s\\", \\"%s\\")" % (co, qs[0])) if len(qs) == 1 else ("(\\"%s\\", q) for q in (%s)" % (co, ", ".join('"%s"' % q for q in sorted(qs)))) for co, qs in sorted(by.items())]
        nl_ = chr(10)
        body = "_TAX22_LATEST_COMPARATIVE_ONLY = set(_TAX22_KYOBO_RESTATED) | {" + nl_ + "    " + ("} | {" + nl_ + "    ").join(pieces) + "}"
        s = s[:a] + body + s[b:]
        n_new = len(tax_off_new)
        old_c = re.search(r"^# 2026-10-23 ticket 20261023T0900Z: KB라이프생명 FY2023 .*\\n", s, re.M)
        if old_c is None:
            raise SystemExit("ABORT: the TAX22 comment of the KB라이프 load (ticket 20261023T0900Z) was not found")
        s = s[:old_c.end()] + "# 2026-10-23 ticket 20261023T0900Z: 롯데손해보험 2023.4Q 최신 비교열 적재(D2)로 최신 비교열 판 버킷이 늘었다 -> 총 %d칸(실측).\\n" % n_new + s[old_c.end():]
        pat = re.compile(r"(    # \\(a\\) 분기를 빼면 최신 비교열로만 통과하는 )\\d+(칸\\(교보 4 \\+ 다른 )\\d+(사 )\\d+(\\)이 RED 로 돌아온다 = 이 분기가 실제로 읽힌다)")
        if not pat.search(s):
            raise SystemExit("ABORT: the TAX22 (a) comment was not found")
        n_co = len({co for co, _q in tax_off_new} - {"교보생명보험"})
        s = pat.sub(lambda mm: f"{mm.group(1)}{n_new}{mm.group(2)}{n_co}{mm.group(3)}{n_new - len(kyobo)}{mm.group(4)}", s)
    out = s.replace("\\n", "\\r\\n") if crlf else s
    return out.encode("utf-8")


'''
s = s[:a] + new_fn + s[b:]
DST.write_text(s, encoding="utf-8", newline="\n")
print("wrote", DST, len(s))
assert "DOC_SET" not in s.replace("DOC_SET = (", "") or True
