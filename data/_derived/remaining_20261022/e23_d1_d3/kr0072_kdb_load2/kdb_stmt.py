# -*- coding: utf-8 -*-
"""KR0072 separate comprehensive-income statement ('4-2. 포괄손익계산서', IFRS17 layout) reader used ONLY by kr0072_verify.py.  Standard library + kdb_raw only (independent of the planner).
Columns are chosen by the DATED period header ('제 36 기 반기 2023.01.01 부터 2023.06.30 까지') AND by the THEAD path ('누적' / '3개월'); rows by normalised label; the OCI leaves by position
inside the reclassifiable / non-reclassifiable blocks.  Every value cell carries its physical line."""
import re

from kdb_raw import (body_rows, clean, header_paths, lines_of, mn, nspace, parse_num, all_tables, section, table_rows, unit_above, ROOT)

MARK_RE = re.compile(r"^(?:[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩ]+\.|\(\d+\)|\d+\.|[가-힣]\.)+")


def rl(text):
    """normalised row label without leading numbering markers"""
    return MARK_RE.sub("", nspace(text))


PERIOD_RE = re.compile(r"제\s*(\d+)\s*기\s*(?:(1분기|반기|3분기)\s*)?(\d{4})\.(\d{2})\.(\d{2})\s*부터\s*(\d{4})\.(\d{2})\.(\d{2})\s*까지")

# item key -> acceptable normalised labels (exactly one row must carry one of them unless noted)
LABELS = {
    "ins_result": ["보험손익"], "rev": ["보험수익"], "rerev": ["재보험수익"], "cost": ["보험비용"], "recost": ["재보험비용"], "other_cost": ["기타사업비용"], "inv": ["투자손익"],
    "ins_fin_rev": ["보험금융수익"], "reins_fin_rev": ["재보험금융수익"], "ins_fin_cost": ["보험금융비용"], "reins_fin_cost": ["재보험금융비용"],
    "op": ["영업이익", "영업이익(손실)"], "nonop": ["영업외손익"], "pretax": ["법인세차감전순이익(손실)", "법인세차감전순이익"], "tax": ["법인세비용(수익)", "법인세수익", "법인세비용"],
    "ni": ["당기순이익(손실)", "당기순이익", "분기순이익(손실)", "분기순이익", "반기순이익(손실)", "반기순이익"],
    "oci": ["당기기타포괄손익", "분기기타포괄손익", "반기기타포괄손익"], "tci": ["당기총포괄손익", "분기총포괄손익", "반기총포괄손익"],
}
SUB_A = nspace("당기손익으로 재분류되는 세후기타포괄손익의 구성요소")
SUB_B = nspace("당기손익으로 재분류되지 않는 세후기타포괄손익의 구성요소")
FVOCI = nspace("기타포괄손익-공정가치측정금융자산평가손익")
HEDGE = nspace("현금흐름위험회피파생상품평가손익")
INSFIN = nspace("보험계약자산(부채)순금융손익")
REINSFIN = nspace("재보험계약자산(부채)순금융손익")


class Stmt:
    def __init__(self, rel, sec_re=r"^4-2\.\s*포괄손익계산서"):
        self.rel = rel
        L = self.L = lines_of(rel)
        a, b = self.sec = section(L, sec_re)
        self.tab = None
        for (ta, tb) in all_tables(L):
            if not (a <= ta <= b):
                continue
            labs = {rl(r["cells"][0]["text"]) for r in table_rows(L, ta, tb) if r["cells"]}
            if "보험손익" in labs and ("법인세차감전순이익" in labs or "법인세차감전순이익(손실)" in labs):
                self.tab = (ta, tb)
                break
        if self.tab is None:
            raise RuntimeError(f"{rel}: statement table not found in section {a + 1}..{b + 1}")
        ta, tb = self.tab
        self.periods = {}
        for k in range(a, ta):
            m = PERIOD_RE.search(clean(L[k]))
            if m and "<T" in "".join(L[max(k - 3, 0):k + 1]):
                self.periods[int(m.group(1))] = dict(line=k + 1, text=clean(L[k]), start=f"{m.group(3)}.{m.group(4)}.{m.group(5)}", end=f"{m.group(6)}.{m.group(7)}.{m.group(8)}")
        un, unl = unit_above(L, ta + 1, span=200)
        if un is None:
            un, unl = unit_above(L, ta + 40, span=300)
        self.unit, self.unit_line = un, unl
        self.paths = header_paths(L, ta, tb)
        self.rows = [r for r in body_rows(L, ta, tb) if r["cells"]]

    # ---- columns
    def col(self, year, kind="cum"):
        """logical column whose dated period ENDS in `year`; kind 'cum' = the 누적 column of a quarterly table or the only column of an annual table, '3m' = the 3개월 column"""
        cands = []
        for j, p in enumerate(self.paths):
            if j == 0 or not p:
                continue
            m = re.search(r"제\s*(\d+)\s*기", p[0])
            if not m:
                continue
            per = self.periods.get(int(m.group(1)))
            if per is None or not per["end"].startswith(f"{year}."):
                continue
            tail = p[1] if len(p) > 1 else None
            if kind == "cum" and tail in (None, "누적"):
                cands.append(j)
            elif kind == "3m" and tail == "3개월":
                cands.append(j)
        if len(cands) != 1:
            raise RuntimeError(f"{self.rel}: {len(cands)} columns for year {year} kind {kind}: {cands}; paths {self.paths}")
        return cands[0]

    def period_of_col(self, j):
        m = re.search(r"제\s*(\d+)\s*기", self.paths[j][0])
        return self.periods[int(m.group(1))]

    # ---- rows
    def _hits(self, alts):
        want = {nspace(x) for x in alts}
        return [(k, r) for k, r in enumerate(self.rows) if rl(r["cells"][0]["text"]) in want]

    def row_index(self, key):
        hits = self._hits(LABELS[key])
        if len(hits) != 1:
            raise RuntimeError(f"{self.rel}: {len(hits)} rows for {key} {LABELS[key]}")
        return hits[0][0]

    def cell_at(self, k, j, blank_ok=False):
        r = self.rows[k]
        cs = r["cells"]
        if len(cs) != len(self.paths):
            raise RuntimeError(f"{self.rel}: row {cs[0]['text']!r} has {len(cs)} cells, header {len(self.paths)}")
        c = cs[j]
        if blank_ok and c["text"] == "":
            return dict(label=cs[0]["text"], label_line=cs[0]["line"], printed="", line=c["line"], unit=self.unit, mn=0.0, col=j, header=self.paths[j], row=k, blank=True)
        v = mn(c["text"], self.unit)
        if v is None:
            raise RuntimeError(f"{self.rel}: {cs[0]['text']!r} col {j} not numeric {c['text']!r}")
        return dict(label=cs[0]["text"], label_line=cs[0]["line"], printed=c["text"], line=c["line"], unit=self.unit, mn=v, col=j, header=self.paths[j], row=k)

    def read(self, year, kind="cum"):
        """-> {key: cell} for the named rows + OCI leaf blocks"""
        j = self.col(year, kind)
        out = {key: self.cell_at(self.row_index(key), j) for key in LABELS}
        i_oci, i_tci = self.row_index("oci"), self.row_index("tci")
        if not i_oci < i_tci:
            raise RuntimeError(f"{self.rel}: OCI rows out of order")
        block = None
        leaves = {"A": [], "B": []}
        subs = {}
        for k in range(i_oci + 1, i_tci):
            lab = rl(self.rows[k]["cells"][0]["text"])
            if lab == SUB_A:
                block = "A"
                subs["A"] = self.cell_at(k, j)
                continue
            if lab == SUB_B:
                block = "B"
                subs["B"] = self.cell_at(k, j)
                continue
            if block is None:
                raise RuntimeError(f"{self.rel}: OCI leaf before any block header: {lab}")
            leaves[block].append(self.cell_at(k, j, blank_ok=True))
        out["_sub_A"], out["_sub_B"] = subs["A"], subs["B"]
        out["_leaves_A"], out["_leaves_B"] = leaves["A"], leaves["B"]
        # classification of the leaves into the production items 26..30 / remainder (32)
        item_leaf = {}
        rest = []
        for c in leaves["A"]:
            n = rl(c["label"])
            if n == FVOCI:
                item_leaf[26] = c
            elif n == HEDGE:
                item_leaf[28] = c
            elif n == INSFIN:
                item_leaf[27] = c
            elif n == REINSFIN:
                item_leaf[30] = c
            else:
                rest.append(c)
        for c in leaves["B"]:
            n = rl(c["label"])
            if n == FVOCI:
                item_leaf[29] = c
            else:
                rest.append(c)
        out["_item_leaf"], out["_rest_leaves"] = item_leaf, rest
        return out


def items_from(V):
    """PL items (백만원) with the production definitions, from freshly read printed cells:
    3 = 보험수익 - 보험비용, 8 = 재보험수익 - 재보험비용, 2 = 3 + 8, 19 = (보험금융수익 + 재보험금융수익) - (보험금융비용 + 재보험금융비용), 18 = 17 - 19,
    26..30 = the named OCI leaves (0 when the leaf row is absent), 32 = sum of every other OCI leaf row (신용손실, 확정급여재측정, 매도가능 ...), 15 = 0.0 (no 기타영업수익 row)."""
    g = {k: V[k]["mn"] for k in LABELS}
    it = {1: g["ins_result"], 16: g["other_cost"], 17: g["inv"], 20: g["op"], 21: g["nonop"], 22: g["pretax"], 23: g["tax"], 24: g["ni"], 25: g["oci"], 31: g["tci"]}
    it[3] = g["rev"] - g["cost"]
    it[8] = g["rerev"] - g["recost"]
    it[2] = it[3] + it[8]
    it[19] = (g["ins_fin_rev"] + g["reins_fin_rev"]) - (g["ins_fin_cost"] + g["reins_fin_cost"])
    it[18] = it[17] - it[19]
    for n in (26, 27, 28, 29, 30):
        it[n] = V["_item_leaf"][n]["mn"] if n in V["_item_leaf"] else 0.0
    it[32] = sum(c["mn"] for c in V["_rest_leaves"])
    it[15] = 0.0
    return it


def identities(V, tol=2e-6):
    """statement-internal identities from PRINTED cells (백만원): [(name, residual, ok)]"""
    g = {k: V[k]["mn"] for k in LABELS}
    out = []

    def chk(name, lhs, rhs, t=tol):
        out.append((name, lhs - rhs, abs(lhs - rhs) <= t))

    chk("보험손익 = 보험수익+재보험수익-보험비용-재보험비용-기타사업비용", g["ins_result"], g["rev"] + g["rerev"] - g["cost"] - g["recost"] - g["other_cost"])
    chk("영업이익 = 보험손익+투자손익", g["op"], g["ins_result"] + g["inv"])
    chk("세전이익 = 영업이익+영업외손익", g["pretax"], g["op"] + g["nonop"])
    chk("당기순이익 = 세전-법인세", g["ni"], g["pretax"] - g["tax"])
    chk("총포괄손익 = 당기순이익+기타포괄손익", g["tci"], g["ni"] + g["oci"])
    chk("기타포괄손익 = 재분류 소계 + 비재분류 소계", g["oci"], V["_sub_A"]["mn"] + V["_sub_B"]["mn"])
    chk("재분류 소계 = 재분류 leaf 합", V["_sub_A"]["mn"], sum(c["mn"] for c in V["_leaves_A"]))
    chk("비재분류 소계 = 비재분류 leaf 합", V["_sub_B"]["mn"], sum(c["mn"] for c in V["_leaves_B"]))
    return out
