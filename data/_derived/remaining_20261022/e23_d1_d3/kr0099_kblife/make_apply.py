# -*- coding: utf-8 -*-
"""build e23_apply.py (KB라이프 D1 option B applier) from the audited e21_apply.py by asserted string substitutions.
Every substitution must hit exactly once; the e21 logic (guards, real build_pl()/build_csm() sandbox deltas, sandbox emitter, ledger/census/test updates, verify, revert) is unchanged."""
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
    '"""Cell-level applier (parser/ifrs17, ticket 20261023T0900Z, D1 = option B: KB라이프 KR0099 FY2023 2023.1Q-2023.3Q at the latest comparative).  Derived from e21_apply.py (audited in the READY-25 load).\nInput = e23_plan_kblife.json (apply_contract) produced by e23_plan.py (kblife) and re-read independently by kr0099_verify.py.')
sub('EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e21_ready25"', 'EV = ROOT / "data" / "_derived" / "remaining_20261022" / "e23_d1_d3" / "kr0099_kblife"')
sub('BACKUP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e21_backup")',
    'BACKUP = ROOT / "data" / "_derived" / "remaining_20261022" / "e23_d1_d3" / "backup_before_apply" / "kr0099_kblife"\n'
    'TMP = Path("C:/Users/sangwook.cho/AppData/Local/Temp/claude/C--Users-sangwook-cho-Desktop-insurequant/429689e1-5ae3-4467-ae2a-745748238c8b/scratchpad/e23_kr0099_tmp")')
sub('PLAN = json.loads((EV / "e21_plan.json").read_text(encoding="utf-8"))', 'PLAN = json.loads((EV / "e23_plan_kblife.json").read_text(encoding="utf-8"))')
sub('tmpdir = BACKUP / "tmp_apply"', 'tmpdir = TMP / "tmp_apply"', count=2)
sub('d = BACKUP / "tmp_emit"', 'd = TMP / "tmp_emit"')
sub('manifest_path = EV / "apply_manifest_e21.json"', 'manifest_path = EV / "apply_manifest_e23_kblife.json"')
sub('(EV / "e21_apply_report.txt")', '(EV / "e23_apply_report.txt")')
sub("-> drift_before.json (run BEFORE --apply)", "-> drift_before.json (run BEFORE --apply)")
sub("headline table -> e21_apply_report.txt)", "headline table -> e23_apply_report.txt)")

# ---- notes
a = s.index('MERGE_NOTE_KEY = "merge_note_20261023_e21_ready25"')
b = s.index("SUBS = [")
new_notes = '''MERGE_NOTE_KEY = "merge_note_20261023_e23_kr0099_kblife"
MERGE_NOTE = ("ticket 20261023T0900Z (parser/ifrs17, owner decision D1 = option B of 2026-10-23): PL cells of KB라이프생명 KR0099 2023.1Q-2023.3Q refreshed to the latest comparative (separate basis, prior-year "
              "cumulative column of the FY2024 Q1/Q2/Q3 reports; 2023.4Q and 2024 untouched) via data/_gold/user_pl_cells.json (new set cells only, no owner-gold cell replaced, no pin changed). "
              "Blocks that changed or appeared are the output of scripts/emit_pl_provenance.py (sandbox copy) for the post-apply masters. Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife/")
CSM_NOTE_KEY = "merge_note_20261023_e23_kr0099_kblife_csm"
CSM_NOTE = ("ticket 20261023T0900Z (D1 = option B): CSM cells of KB라이프생명 KR0099 2023.1Q-2023.3Q set to the latest-filing (FY2024 Q1/Q2/Q3 prior-period roll-forward, separate basis, issued-contract CSM, "
            "V1 opening 31,327.6) vector via data/_gold/user_csm_cells.json (owner_override flagged on these blocks). Evidence data/_derived/remaining_20261022/e23_d1_d3/kr0099_kblife/")
'''
s = s[:a] + new_notes + s[b:]
# the e21 pin docs are not used (no dangi change in this load)
sub('    nd["_doc_e21_20261023"] = DOC_NULL\n    sd["_doc_e21_20261023"] = DOC_SET\n', '')

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
    comment = ("# 2026-10-23 ticket 20261023T0900Z (parser/ifrs17, D1 = option B: KB라이프생명 KR0099 FY2023 2023.1Q-2023.3Q refreshed to the latest comparative; no owner-gold cell replaced): "
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
        old_c = re.search(r"^# 2026-10-23 ticket 20261023T0300Z: READY-25 .*\\n", s, re.M)
        if old_c is None:
            raise SystemExit("ABORT: the TAX22 comment of ticket 20261023T0300Z was not found")
        s = s[:old_c.end()] + "# 2026-10-23 ticket 20261023T0900Z: KB라이프생명 FY2023 2023.1Q-3Q 최신 비교열 적재(D1-B)로 최신 비교열 판 버킷이 늘었다 -> 총 %d칸(실측).\\n" % n_new + s[old_c.end():]
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

# ---- second pass: drop the unused e21 pin docs (no null_dangi / set_dangi change in this load)
s = DST.read_text(encoding="utf-8")
a = s.index("DOC_NULL = (")
b = s.index("\n\ndef rkey(r):")
s = s[:a].rstrip("\n") + "\n" + s[b:]
assert "DOC_NULL" not in s and "DOC_SET" not in s
DST.write_text(s, encoding="utf-8", newline="\n")
print("second pass ok", len(s))
