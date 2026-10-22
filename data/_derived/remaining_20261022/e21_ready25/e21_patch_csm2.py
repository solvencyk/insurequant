"""one-off patcher: apply two text edits to e21_csm2.py (layout (c) for 롯데 FY2025_Q3; contains-matching for the 미래에셋 wide rows)"""
import sys
p = "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25/e21_csm2.py"
s = open(p, encoding="utf-8").read()
old1 = '''    if a_tabs:
        if len(a_tabs) != 2:'''
new1 = '''    c_tabs = []
    for t in M.iter_tables(lines):
        if t["start"] < s0:
            continue
        rows = W.rows_full(lines, t["start"], t["end"])
        labs = [nl(W.label_of(r)) for r in rows]
        blob = nl(" ".join(c["text"] for r in rows[:14] for c in r["cells"]))
        nn = [len(W.numeric_cells(r)) for r in rows if nl(W.label_of(r)) == "기초순보험계약부채"]
        if nn and nn[0] == 1 and "보험계약마진상각액" in labs and "최초인식계약" in labs and "발행한보험계약" in blob and "장기보험" in blob \
                and "보험료배분접근법을적용한보험계약외의보험계약" in blob:
            c_tabs.append((t, rows))
    if c_tabs:
        if len(c_tabs) != 2:
            raise RuntimeError(f"{path.name}: {len(c_tabs)} layout-(c) tables (need the current/prior pair)")
        t, rows = c_tabs[1]
        unit = T.find_unit(lines, t, span=2500)
        return _lotte_c(path, t, rows, unit)
    if a_tabs:
        if len(a_tabs) != 2:'''
assert s.count(old1) == 1
s = s.replace(old1, new1)
old2 = '''def _lotte_b(path, t, rows, unit):'''
new2 = '''def _lotte_c(path, t, rows, unit):
    def last_num(r, label):
        n = W.numeric_cells(r, 0)
        if not n:
            raise RuntimeError(f"{label}: no numeric cell")
        return n[-1]

    def row(pred):
        h = [r for r in rows if pred(lab_lead(r))]
        if len(h) != 1:
            raise RuntimeError(f"{path.name}: predicate matched {len(h)} rows (need 1)")
        return h[0]

    cells = {
        1: [eok_cell("기초순보험계약부채", last_num(row(lambda x: x == "기초순보험계약부채"), "open"), 1, unit)],
        2: [eok_cell("최초 인식 계약", last_num(row(lambda x: x == "최초인식계약"), "new"), 1, unit)],
        3: [eok_cell("당기손익으로 인식하는 보험금융수익(비용)", last_num(row(lambda x: "당기손익으로인식하는보험금융수익(비용)" in x), "int"), 1, unit)],
        4: [eok_cell("보험계약마진을 조정하는 추정치의 변동", last_num(row(lambda x: x == "보험계약마진을조정하는추정치의변동"), "adj"), 1, unit)],
        5: [eok_cell("보험계약마진 상각액", last_num(row(lambda x: x == "보험계약마진상각액"), "amort"), 1, unit)],
        6: [eok_cell("분기말순보험계약부채", last_num(row(lambda x: re.match(r"^(기말|분기말|반기말)순보험계약부채$", x) is not None), "close"), 1, unit)],
    }
    grp = last_num(row(lambda x: x == "현행서비스관련변동현행서비스관련변동"), "group")
    out = finish(cells, False, f"{M.rel(path)} table@L{t['start']} layout (c) unit {unit}")
    out["check_group_row_5"] = eok_cell("현행서비스 관련 변동", grp, 1, unit)
    return out


def _lotte_b(path, t, rows, unit):'''
assert s.count(old2) == 1
s = s.replace(old2, new2)
# 미래에셋 wide rows: contains instead of startswith
for a, b in (('x.startswith("자산인보험계약의기초장부금액")', '"자산인보험계약의기초장부금액" in x'), ('x.startswith("부채인보험계약의기초장부금액")', '"부채인보험계약의기초장부금액" in x'),
             ('x.startswith("처음인식한계약의효과")', '"처음인식한계약의효과" in x'), ('x.startswith("당기손익인식보험금융손익")', '"당기손익인식보험금융손익" in x'),
             ('x.startswith("보험수익,서비스의이전으로당기손익에인식한보험계약마진")', '"보험수익,서비스의이전으로당기손익에인식한보험계약마진" in x'),
             ('x.startswith("자산인보험계약의기말장부금액")', '"자산인보험계약의기말장부금액" in x'), ('x.startswith("부채인보험계약의기말장부금액")', '"부채인보험계약의기말장부금액" in x')):
    assert b not in s
    s = s.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("patched")
