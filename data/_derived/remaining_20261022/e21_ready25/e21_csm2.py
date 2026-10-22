# -*- coding: utf-8 -*-
"""e21 independent CSM readers, part 2: 롯데손해보험 (layouts a/b) and 미래에셋생명 (Q1 row-block product tables; Q2/Q3 wide roll-forward) + the 미래에셋 PL4 (보험수익 note CSM amortisation).
Same return contract as e21_csm.py (vec_exact / vec (2dp) / vec1 (python round 1dp) / cells / derived / src)."""
import re
import sys

sys.path.insert(0, "C:/Users/sangwook.cho/Desktop/insurequant/data/_derived/remaining_20261022/e21_ready25")
import e21_csm as C  # noqa: E402
import e21_raw as W  # noqa: E402
import e21_t2 as T  # noqa: E402

M = T.M
nl = T.nl
eok_cell, finish, sep_tables = C.eok_cell, C.finish, C.sep_tables


def lab_lead(r, k=3):
    """normalised text of the leading non-numeric cells of a row (up to k cells)"""
    out = []
    for c in r["cells"][:k]:
        if c["val"] is None and c["text"].strip() not in ("-", "−"):
            out.append(nl(c["text"]))
        else:
            break
    return "".join(out)


# ====================================================================================================== 롯데손해보험 (KR0003)
def lotte_csm(q):
    fy = M.later_fy(q)
    path = T.main_path("KR0003", fy)
    lines, s0 = sep_tables(path)
    a_tabs, b_tabs = [], []
    for t in M.iter_tables(lines):
        if t["start"] < s0:
            continue
        rows = W.rows_full(lines, t["start"], t["end"])
        labs = [nl(W.label_of(r)) for r in rows]
        if any(x.startswith("기초순보험계약부채") for x in labs) and "보험계약마진상각액" in labs and "최초인식계약" in labs:
            nn = [len(W.numeric_cells(r)) for r in rows if nl(W.label_of(r)).startswith("기초순보험계약부채")]
            if nn and nn[0] == 7:
                a_tabs.append((t, rows))
        blob = nl(" ".join(c["text"] for r in rows[:14] for c in r["cells"]))
        if "구성요소별보험계약" in blob and "보험계약마진" in blob and "장기보험" in blob and "보험료배분접근법을적용한보험계약외의보험계약" in blob \
                and "발행한보험계약" in blob and "기초보험계약부채(자산)" in labs and "미래현금흐름의현재가치추정치" not in blob:
            b_tabs.append((t, rows))
    c_tabs = []
    for t in M.iter_tables(lines):
        if t["start"] < s0:
            continue
        rows = W.rows_full(lines, t["start"], t["end"])
        labs = [nl(W.label_of(r)) for r in rows]
        blob = nl(" ".join(c["text"] for r in rows[:14] for c in r["cells"]))
        nn = [len(W.numeric_cells(r)) for r in rows if nl(W.label_of(r)) == "기초순보험계약부채"]
        if nn and nn[0] == 1 and "보험계약마진상각액" in labs and "최초인식계약" in labs and "발행한보험계약" in blob and "장기보험" in blob                 and "보험료배분접근법을적용한보험계약외의보험계약" in blob:
            c_tabs.append((t, rows))
    if c_tabs:
        if len(c_tabs) != 2:
            raise RuntimeError(f"{path.name}: {len(c_tabs)} layout-(c) tables (need the current/prior pair)")
        t, rows = c_tabs[1]
        unit = T.find_unit(lines, t, span=2500)
        return _lotte_c(path, t, rows, unit)
    if a_tabs:
        if len(a_tabs) != 2:
            raise RuntimeError(f"{path.name}: {len(a_tabs)} layout-(a) tables (need the current/prior pair)")
        t, rows = a_tabs[1]
        unit = T.find_unit(lines, t, span=2500)
        return _lotte_a(path, t, rows, unit)
    if len(b_tabs) != 2:
        raise RuntimeError(f"{path.name}: layout (b) tables {len(b_tabs)} (need the current/prior pair)")
    t, rows = b_tabs[1]
    unit = T.find_unit(lines, t, span=2500)
    return _lotte_b(path, t, rows, unit)


def _lotte_a(path, t, rows, unit):
    def row(pred):
        h = [r for r in rows if pred(nl(W.label_of(r)))]
        if len(h) != 1:
            raise RuntimeError(f"{path.name}: {len(h)} rows for predicate")
        return h[0]

    def sub(r, label):
        n = W.numeric_cells(r)
        if len(n) != 7:
            raise RuntimeError(f"{label}: {len(n)} numeric cells (need 7)")
        return [eok_cell(label, n[5], 1, unit)]

    cells = {
        1: sub(row(lambda x: x.startswith("기초순보험계약부채")), "기초순보험계약부채 [CSM 소계]"),
        2: sub(row(lambda x: x == "최초인식계약"), "최초 인식 계약 [CSM 소계]"),
        3: sub(row(lambda x: x == "보험금융손익"), "보험금융손익 [CSM 소계]"),
        4: sub(row(lambda x: x.startswith("보험계약마진을조정하는추정치의변동")), "보험계약마진을 조정하는 추정치의 변동 [CSM 소계]"),
        5: sub(row(lambda x: x == "보험계약마진상각액"), "보험계약마진 상각액 [CSM 소계]"),
        6: sub(row(lambda x: re.match(r"^(기말|분기말|반기말)순보험계약부채$", x) is not None), "기말순보험계약부채 [CSM 소계]"),
    }
    grp = sub(row(lambda x: x == "현행서비스관련변동"), "현행서비스 관련 변동 [CSM 소계]")[0]
    out = finish(cells, False, f"{M.rel(path)} table@L{t['start']} layout (a) unit {unit}")
    out["check_group_row_5"] = grp
    return out


def _lotte_c(path, t, rows, unit):
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


def _lotte_b(path, t, rows, unit):
    def last_num(r, label):
        n = W.numeric_cells(r, 0)
        if not n:
            raise RuntimeError(f"{label}: no numeric cell")
        return n[-1]

    def row(pred, nth=1):
        h = [r for r in rows if pred(lab_lead(r))]
        if len(h) < nth:
            raise RuntimeError(f"{path.name}: predicate matched {len(h)} rows")
        if len(h) > 1 and nth == 1:
            raise RuntimeError(f"{path.name}: predicate matched {len(h)} rows (need 1)")
        return h[nth - 1]

    cells = {
        1: [eok_cell("기초 보험계약부채(자산)", last_num(row(lambda x: x == "기초보험계약부채(자산)"), "open"), 1, unit)],
        2: [eok_cell("해당 기간에 처음 인식한 계약의 영향에 따른 증가분(감소분)", last_num(row(lambda x: x.startswith("해당기간에처음인식한계약의영향에따른증가분")), "new"), 1, unit)],
        3: [eok_cell("당기손익으로 인식한 발행한 보험계약의 보험금융수익(비용)", last_num(row(lambda x: "당기손익으로인식한발행한보험계약의보험금융수익(비용)" in x), "int"), 1, unit)],
        4: [eok_cell("보험계약마진을 조정하는 추정치의 변동분에 따른 증가분(감소분)", last_num(row(lambda x: x.startswith("보험계약마진을조정하는추정치의변동분에따른증가분")), "adj"), 1, unit)],
        5: [eok_cell("서비스 이전을 반영하기 위해 당기손익으로 인식한 보험계약마진", last_num(row(lambda x: x.startswith("서비스이전을반영하기위해당기손익으로인식한보험계약마진")), "amort"), 1, unit)],
        6: [eok_cell("기말 보험계약부채(자산)", last_num(row(lambda x: x == "기말보험계약부채(자산)"), "close"), 1, unit)],
    }
    return finish(cells, False, f"{M.rel(path)} table@L{t['start']} layout (b) unit {unit}")


# ====================================================================================================== 미래에셋생명 (KR0079)
KEYS_Q1 = {"open": "기초잔액", "new": "처음인식한계약의효과", "int": "당기손익인식보험금융손익", "amort": "보험계약마진의당기인식분", "close": "기말잔액"}


def mirae_q1(fy="FY2025_Q1", block="전분기"):
    """5 issued-contract product tables (i 사망, ii 건강, iii 연금, iv 저축, v 기타) of the later Q1 filing: row blocks '당분기' / '전분기'; CSM 소계 = 6th of the last 7 numeric cells, 합계 = 7th"""
    path = T.main_path("KR0079", fy)
    lines, s0 = sep_tables(path)
    prod = []
    for t in M.iter_tables(lines):
        if t["start"] < s0:
            continue
        rows = W.rows_full(lines, t["start"], t["end"])
        labs = [nl(W.label_of(r)) for r in rows]
        hdr = nl(" ".join(c["text"] for r in rows[:6] for c in r["cells"]))
        if "재보험" in hdr:
            continue
        op = [len(W.numeric_cells(r)) for r in rows if nl(W.label_of(r)) == "기초잔액"]
        if op and all(n == 7 for n in op) and any(x == "기말잔액" for x in labs):
            prod.append((t, rows))
    if len(prod) != 5:
        raise RuntimeError(f"{path.name}: {len(prod)} issued product tables (need 5)")
    unit = None
    cells = {i: [] for i in range(1, 7)}
    pl4 = []
    for t, rows in prod:
        u = T.find_unit(lines, t, span=300)
        unit = unit or u
        if u != unit:
            raise RuntimeError("unit differs between product tables")
        cur = None
        got = {}
        for r in rows:
            first = nl(r["cells"][0]["text"]) if r["cells"] else ""
            if first in ("당기", "당분기", "당반기"):
                cur = "cur"
            elif first in ("전기", "전분기", "전반기"):
                cur = "prior"
            if cur != ("prior" if block in ("전기", "전분기", "전반기") else "cur"):
                continue
            lab = lab_lead(r)
            key = None
            for k, needle in KEYS_Q1.items():
                if lab.endswith(needle) or lab == needle:
                    key = k
            if key is None or key in got:
                continue
            n = W.numeric_cells(r, 0)[-7:]
            if len(n) != 7:
                continue
            got[key] = (n[5], n[6])
        if set(got) != set(KEYS_Q1):
            raise RuntimeError(f"{path.name} table@L{t['start']}: block rows found {sorted(got)}")
        item_of = {"open": 1, "new": 2, "int": 3, "amort": 5, "close": 6}
        cap = nl(t["caption"])
        for k, (csm, tot) in got.items():
            cells[item_of[k]].append(eok_cell(f"{k} [{cap} CSM 소계]", csm, 1, unit))
        pl4.append(dict(label=f"보험계약마진의 당기인식분 [{cap} 합계]", line=got["amort"][1][1], printed=got["amort"][1][2], sign=1, abs=True, unit=unit,
                        csm_line=got["amort"][0][1], csm_printed=got["amort"][0][2], equal=(got["amort"][0][0] == got["amort"][1][0])))
    out = finish(cells, True, f"{M.rel(path)} 5 product tables {[t['start'] for t, _ in prod]} block {block} unit {unit}")
    div = {"백만원": 1.0, "원": 1e-6}[unit]
    out["pl4_parts"] = pl4
    out["pl4_mn"] = sum(abs(M.num(p["printed"])) for p in pl4) * div
    return out


def mirae_wide(q):
    """FY2025 Q2/Q3: wide roll-forward (5 products x [PV, RA, CSM수정소급, CSM공정가치, CSM그밖] = 25 value columns, unit 원); CSM = sum of the 15 CSM cells of a row.
    The pair (current, prior) is the pair of tables containing '부채인 보험계약의 기초 장부금액'; PRIOR = second in document order."""
    fy = M.later_fy(q)
    path = T.main_path("KR0079", fy)
    lines, s0 = sep_tables(path)
    CSM_IDX = [p * 5 + k for p in range(5) for k in (2, 3, 4)]
    tabs = []
    for t in M.iter_tables(lines):
        if t["start"] < s0:
            continue
        rows = W.rows_full(lines, t["start"], t["end"])
        labs = [nl(W.label_of(r)) for r in rows]
        if not any("부채인보험계약의기초장부금액" in x for x in labs):
            continue
        if not any(len(W.numeric_cells(r, 0)) >= 25 for r in rows):
            continue
        hdr = nl(" ".join(c["text"] for r in rows[:6] for c in r["cells"]))
        if "보유재보험계약" in hdr:
            continue
        tabs.append((t, rows))
    if len(tabs) != 2:
        raise RuntimeError(f"{path.name}: {len(tabs)} wide issued roll-forward tables (need current/prior)")
    t, rows = tabs[1]
    unit = T.find_unit(lines, t, span=2500)
    if unit != "원":
        raise RuntimeError(f"unit {unit} (expected 원)")

    def last25(r, label):
        """the last 25 cells of the row as (value, line, text); blank and '-' cells are 0"""
        cs = r["cells"][-25:]
        if len(cs) != 25:
            raise RuntimeError(f"{label}: {len(r['cells'])} cells (need >= 25)")
        out = []
        for c in cs:
            if c["val"] is not None:
                out.append((c["val"], c["line"], c["text"]))
            elif c["text"].strip() in ("", "-", "−"):
                out.append((0.0, c["line"], c["text"]))
            else:
                raise RuntimeError(f"{label}: non-numeric value cell {c['text']!r}")
        return out

    def csm_cells(r, label, sign=1):
        nums = last25(r, label)
        non_csm = [nums[i] for i in range(25) if i not in CSM_IDX]
        return [eok_cell(f"{label} [col {i}]", nums[i], sign, unit) for i in CSM_IDX], non_csm

    def rows_with(pred):
        return [r for r in rows if pred(lab_lead(r))]

    def one(pred, label):
        h = rows_with(pred)
        if len(h) != 1:
            raise RuntimeError(f"{path.name}: {label}: {len(h)} rows")
        return h[0]

    cells = {}
    non_csm_all = {}
    for item, label, rs in (
        (1, "기초 장부금액 (자산인+부채인)", [one(lambda x: "자산인보험계약의기초장부금액" in x, "open-asset"), one(lambda x: "부채인보험계약의기초장부금액" in x, "open-liab")]),
        (2, "처음 인식한 계약의 효과", [one(lambda x: "처음인식한계약의효과" in x, "new")]),
        (3, "당기손익인식 보험금융손익", [one(lambda x: "당기손익인식보험금융손익" in x, "int")]),
        (5, "보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진", [one(lambda x: "보험수익,서비스의이전으로당기손익에인식한보험계약마진" in x, "amort")]),
        (6, "기말 장부금액 (자산인+부채인)", [one(lambda x: "자산인보험계약의기말장부금액" in x, "close-asset"), one(lambda x: "부채인보험계약의기말장부금액" in x, "close-liab")]),
    ):
        cs = []
        for r in rs:
            c, nc = csm_cells(r, label)
            cs += c
            non_csm_all.setdefault(item, []).extend(nc)
        cells[item] = cs
    out = finish(cells, True, f"{M.rel(path)} wide roll-forward table@L{t['start']} (prior of the pair) unit {unit}")
    out["non_csm_cells_abs_max"] = {i: max(abs(c[0]) for c in v) for i, v in non_csm_all.items()}
    # PL4 = |whole-row sum of the amortisation row| / 1e6 (production Era-2 definition); PV/RA columns must be 0 on that row
    am = one(lambda x: "보험수익,서비스의이전으로당기손익에인식한보험계약마진" in x, "amort")
    allc = last25(am, "amort")
    out["pl4_mn"] = abs(sum(c[0] for c in allc)) / 1e6
    out["pl4_parts"] = [dict(label="보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진 [25 value cells]", line=c[1], printed=c[2], sign=1, abs=False, unit=unit) for c in allc]
    return out
