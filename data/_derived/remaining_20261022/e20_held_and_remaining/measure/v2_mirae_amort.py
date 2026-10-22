"""v2_mirae_amort: independent check of 미래에셋 CSM item 5 (CSM amortisation, 보험계약마진 당기인식분) of the LATER filing's prior-period column, from the insurance-revenue note rows
'해당 기간에 서비스의 이전으로 당기손익에 인식한 보험계약마진' of the separate-basis tables.  Prints every such row (table start, row line, numeric cells with lines) so the sums can be compared
with the CSM vector (-507.6 / -1007.0 / -1487.1 eok).  READ-ONLY.
usage: v2_mirae_amort.py <FY_Q> [<FY_Q> ...]"""
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e20_held_and_remaining/measure")
import mlib as M  # noqa: E402
import stmtlib as S  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
code = "KR0079"
for fy in sys.argv[1:]:
    path = [p for p in M.main_xmls(code, fy) if not p.name.endswith(("_00760.xml", "_00761.xml"))][0]
    lines = M.read_lines(path)
    note_from = None
    for ln, tt in S.titles(lines):
        if re.match(r"^\d+\.재무제표주석$", re.sub(r"\s+", "", tt)):
            note_from = ln
    print(f"##### {M.rel(path)} separate notes from L{note_from}")
    for t in M.iter_tables(lines):
        if note_from and t["start"] < note_from:
            continue
        for r in t["rows"]:
            lab = M.norm_label(r["cells"][0]["text"]) if r["cells"] else ""
            if "서비스의이전으로당기손익에" in lab or lab.startswith("보험계약마진의당기인식분"):
                nums = [(c["text"], c["line"]) for c in r["cells"][1:] if c["val"] is not None]
                print(f"  T{t['start']} cap={t['caption'][:14]!r} R{r['tr_line']} {r['cells'][0]['text'][:28]} | " + " ".join(f"{a}@{b}" for a, b in nums[-6:]))
