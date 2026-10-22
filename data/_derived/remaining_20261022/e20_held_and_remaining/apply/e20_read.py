# -*- coding: utf-8 -*-
"""e20 statement reader + PL Tier-1 item mapper (own code; no scripts/ or src/ imports).
Reads the SEPARATE-basis comprehensive income statement ('4-2. 포괄손익계산서') of a DART filing, either the ATOC xml layout (<TE ... ACONTEXT>) or the plain HTML layout
(<TD>), and maps the printed rows to the master's Tier-1 items 1, 16..32 with the production definitions:
  18 = 17 - 19 ; 19 = (보험금융수익 + 재보험금융수익) - (보험금융비용 + 재보험금융비용) ; 21 = 영업외손익 (or 영업외수익 - 영업외비용) ; 32 = 25 - (26+27+28+29+30)
Every value carries its citation parts (label, physical xml line, printed text, sign) so a second script can re-read the line independently."""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e20_xml as X  # noqa: E402

CUM_SUFFIX = ("FQA", "HYA", "TQA", "FY")
Q3M_SUFFIX = ("FQQ", "HYQ", "TQQ")
RE_CTX = re.compile(r"^(C|P|BP)FY(\d{4})d(FQQ|FQA|HYQ|HYA|TQQ|TQA|FY)(?:_|$)")


def norm(label):
    s = (label or "").replace("　", "").replace(" ", "").replace("\xa0", "")
    s = re.sub(r"^([Ⅰ-Ⅹ]|[IVX]+|\d+)\.", "", s)           # leading numbering  I.  1.  Ⅰ.
    s = re.sub(r"^\(\d+\)", "", s)                                    # (1)
    s = re.sub(r"^\d+\)", "", s)                                       # 1)
    s = re.sub(r"\(주[^)]*\)", "", s)                                  # note refs
    s = s.replace("(손실)", "").replace("(수익)", "").replace("(이익)", "")
    return s


def cellnum(c):
    """numeric value of a printed cell; '-' counts as 0 (printed dash); empty -> None"""
    if c["val"] is not None:
        return c["val"]
    if c["text"].strip() in ("-", "−"):
        return 0.0
    return None


class Row:
    def __init__(self, raw, lab, line, tr, cells):
        self.raw, self.lab, self.line, self.tr, self.cells = raw, lab, line, tr, cells
        self.sect, self.oci, self.subtotal = None, False, False


class Stmt:
    def __init__(self, code, fy, path=None):
        self.code, self.fy = code, fy
        self.path = Path(path) if path else X.main_xml(code, fy)
        self.rel = X.rel(self.path)
        lines = X.load_lines(self.path)
        ts = X.find_titles(lines, r"4-2\. 포괄손익계산서")
        raw_rows = []
        if ts:
            self.fmt = "atoc"
            self.title, self.end, rows = X.read_statement_at(lines, ts[0])
            for r in rows:
                lab_text = r["label"][0] if r["label"] else ""
                lab_line = r["label"][1] if r["label"] else None
                raw_rows.append((lab_text, lab_line, r["tr_line"], [dict(text=c["text"], val=c["val"], line=c["line"], ctx=c["ctx"]) for c in r["cells"]]))
        else:
            s, e = X.html_marker_range(lines, r"4-2\. 포괄손익계산서")
            if s is None:
                raise KeyError(f"{self.rel}: no '4-2. 포괄손익계산서' title/marker")
            self.fmt = "html"
            self.title, self.end = s, e
            for r in X.read_html_rows(lines, s, e):
                if not r["cells"]:
                    continue
                lab = r["cells"][0]
                raw_rows.append((lab["text"], lab["line"], r["tr_line"], [dict(text=c["text"], val=c["val"], line=c["line"], ctx="") for c in r["cells"][1:]]))
        self.unit = "?"
        self.rows = []
        in_oci, sect = False, None
        for lab_text, lab_line, tr, cells in raw_rows:
            if self.unit == "?" and "단위" in lab_text:
                self.unit = "백만원" if "백만원" in lab_text else ("원" if "원" in lab_text else "?")
            lab = norm(lab_text)
            cells = [c for c in cells if c["text"] != ""]
            row = Row(lab_text, lab, lab_line, tr, cells)
            if lab in ("기타포괄손익", "법인세비용차감후기타포괄손익", "당기기타포괄손익") and not in_oci:
                in_oci, sect = True, None
                row.oci = True
            elif in_oci:
                row.oci = True
                if "재분류" in lab and ("구성요소" in lab or lab.startswith("후속적으로") or lab.startswith("당기손익으로")):
                    sect = "N" if "재분류되지" in lab else "R"
                    row.subtotal = True
                row.sect = sect
                if lab.endswith("총포괄손익"):
                    in_oci = False
            self.rows.append(row)
        self.scale = 1e6 if self.unit == "원" else 1.0

    # ---------------------------------------------------------------- column selection
    def pick_cell(self, row, role, kind):
        """role 'cur'|'prior', kind 'cum'|'3m'.  ctx mode (ACONTEXT present) or positional mode ([cur3m, curcum, prior3m, priorcum] / [cur, prior(, before-prior)])."""
        nums = [c for c in row.cells]
        if any(RE_CTX.match(c["ctx"] or "") for c in nums):
            want = []
            for c in nums:
                m = RE_CTX.match(c["ctx"] or "")
                if not m or "SeparateMember" not in c["ctx"]:
                    continue
                who, suf = m.group(1), m.group(3)
                if (who == "C") != (role == "cur") or who == "BP":
                    continue
                if kind == "cum" and suf in CUM_SUFFIX:
                    want.append(c)
                elif kind == "3m" and suf in Q3M_SUFFIX:
                    want.append(c)
            if len(want) != 1:
                return None
            return want[0]
        vals = [c for c in nums if (c["val"] is not None or c["text"].strip() == "-")]
        if len(vals) == 4:
            idx = {("cur", "3m"): 0, ("cur", "cum"): 1, ("prior", "3m"): 2, ("prior", "cum"): 3}[(role, kind)]
            return vals[idx]
        if len(vals) in (2, 3):
            if kind == "3m":
                return None
            return vals[0 if role == "cur" else 1]
        return None

    def find(self, names, sect=None, exclude=(), optional=False, oci_only=None):
        cand = []
        for r in self.rows:
            if r.subtotal or r.lab not in names:
                continue
            if sect is not None and r.sect != sect:
                continue
            if oci_only is True and not r.oci:
                continue
            if oci_only is False and r.oci:
                continue
            if any(x in r.lab for x in exclude):
                continue
            cand.append(r)
        if not cand:
            if optional:
                return None
            raise KeyError(f"{self.rel}: none of {names} (sect={sect})")
        if len(cand) > 1:
            raise RuntimeError(f"{self.rel}: ambiguous {names} sect={sect}: {[(c.raw, c.line) for c in cand]}")
        return cand[0]

    def leafs(self):
        return [r for r in self.rows if r.oci and not r.subtotal and r.lab not in ("기타포괄손익", "법인세비용차감후기타포괄손익", "당기기타포괄손익") and not r.lab.endswith("총포괄손익")
                and r.cells and any(cellnum(c) is not None for c in r.cells)]


# --------------------------------------------------------------------------------------------- item mapper
NAMES = {
    1: ["보험손익", "보험서비스결과", "보험서비스손익"],
    16: ["기타사업비용", "기타사업비"],
    17: ["투자손익", "투자서비스결과"],
    20: ["영업이익", "영업손익"],
    22: ["법인세차감전순이익", "법인세비용차감전순이익", "법인세비용차감전계속영업이익", "법인세차감전계속영업이익"],
    23: ["법인세비용", "법인세수익", "법인세비용수익"],
    24: ["당기순이익", "분기순이익", "반기순이익"],
    25: ["기타포괄손익", "법인세비용차감후기타포괄손익", "당기기타포괄손익"],
    31: ["총포괄손익", "분기총포괄손익", "반기총포괄손익", "당기총포괄손익"],
}


def classify_leaf(r):
    """OCI leaf row -> master item 26/27/28/29/30 or 32 (residual bucket)"""
    n = r.lab
    if "신용손실" in n or "손상충당금" in n:
        return 32
    if "위험회피" in n:
        return 28
    if "재보험" in n and "금융" in n:
        return 30
    if ("보험계약" in n or "보험금융" in n) and "금융" in n:
        return 27
    if "공정가치측정" in n:
        if "채무증권" in n or "채무상품" in n:
            return 26
        if "지분증권" in n or "지분상품" in n:
            return 29
        return 26 if r.sect == "R" else (29 if r.sect == "N" else 26)
    return 32


class Part:
    def __init__(self, label, line, printed, sign, val_mn):
        self.label, self.line, self.printed, self.sign, self.val_mn = label, line, printed, sign, val_mn

    def d(self):
        return dict(label=self.label, line=self.line, printed=self.printed, sign=self.sign, contribution_mn=round(self.sign * self.val_mn, 6))


def read_vector(st, role, kind, want=None):
    """-> dict item -> dict(val (백만원), parts[Part...]) ; helper entries under '_h'.  want = optional set of items to produce (default all)."""
    sc = st.scale
    out = {}

    def one(row):
        c = st.pick_cell(row, role, kind)
        if c is None:
            raise RuntimeError(f"{st.rel}: row {row.raw!r} L{row.line}: no {role}/{kind} cell (cells={[(x['text'], x['ctx'][:14]) for x in row.cells]})")
        v = cellnum(c)
        if v is None:
            raise RuntimeError(f"{st.rel}: row {row.raw!r}: cell not numeric {c['text']!r}")
        return Part(row.raw.replace("　", " ").strip(), c["line"], c["text"], 1, v / sc)

    def direct(it, names, sect=None, optional=False, oci_only=None):
        r = st.find(names, sect=sect, optional=optional, oci_only=oci_only)
        if r is None:
            return None
        p = one(r)
        out[it] = dict(val=p.val_mn, parts=[p])
        return out[it]

    for it in (1, 16, 17, 20, 22, 23, 24):
        direct(it, NAMES[it], oci_only=False)
    direct(25, NAMES[25])
    direct(31, NAMES[31])
    # 19
    parts, v19 = [], 0.0
    for nm, sg, opt in (("보험금융수익", 1, True), ("재보험금융수익", 1, True), ("보험금융비용", -1, False), ("재보험금융비용", -1, True)):
        r = st.find([nm], optional=opt, oci_only=False)
        if r is None:
            continue
        p = one(r)
        p.sign = sg
        v19 += sg * p.val_mn
        parts.append(p)
    out[19] = dict(val=v19, parts=parts)
    # 18 = 17 - 19
    out[18] = dict(val=out[17]["val"] - v19, parts=[out[17]["parts"][0]] + [Part(p.label, p.line, p.printed, -p.sign, p.val_mn) for p in parts])
    # 21
    r21 = st.find(["영업외손익"], optional=True, oci_only=False)
    if r21 is not None:
        p = one(r21)
        out[21] = dict(val=p.val_mn, parts=[p])
    else:
        a = one(st.find(["영업외수익"], oci_only=False))
        b = one(st.find(["영업외비용"], oci_only=False))
        b.sign = -1
        out[21] = dict(val=a.val_mn - b.val_mn, parts=[a, b])
    # OCI leaf classification
    cls = {26: [], 27: [], 28: [], 29: [], 30: [], 32: []}
    for r in st.leafs():
        if st.pick_cell(r, role, kind) is None:
            out.setdefault("_skipped_leafs", []).append((r.raw, r.line))
            continue
        it = classify_leaf(r)
        cls[it].append(one(r))
    for it in (26, 27, 28, 29, 30):
        if len(cls[it]) > 1:
            raise RuntimeError(f"{st.rel}: item {it}: several leaf rows {[p.label for p in cls[it]]}")
        out[it] = dict(val=(cls[it][0].val_mn if cls[it] else 0.0), parts=cls[it], absent=not cls[it])
    leaf32 = cls[32]
    # residual definition (production): 32 = 25 - (26+27+28+29+30)
    out[32] = dict(val=out[25]["val"] - sum(out[i]["val"] for i in (26, 27, 28, 29, 30)),
                   parts=[out[25]["parts"][0]] + [Part(p.label, p.line, p.printed, -1, p.val_mn) for i in (26, 27, 28, 29, 30) for p in out[i]["parts"]])
    out["_leaf32"] = leaf32
    out["_leaf32_sum"] = sum(p.val_mn for p in leaf32)
    leaf_all = sum(p.val_mn for i in (26, 27, 28, 29, 30, 32) for p in (cls[i] if i != 32 else leaf32))
    out["_leaf_all_sum"] = leaf_all
    if want is not None:
        out = {k: v for k, v in out.items() if (not isinstance(k, int)) or k in want}
    return out
