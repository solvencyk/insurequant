# -*- coding: utf-8 -*-
"""Reinsurer branches (KR1101~KR1107) -- read the CSM-family tables of the management disclosures (PDF text layer).

Ticket: inbox/parser/20261011T0430Z__orchestrator__KR1101-KR1108_2024.4Q-2026.2Q__reinsurer_csm_masters.md
Runlog: data/disclosure/_meta/reinsurer_ifrs17_csm_runlog.md

What it reads (FY2024_Q4 and FY2025_Q4 closing disclosures; every number comes from the PDF text layer):
  amort : 4-6-3 (2) CSM amortization schedule  -> one total row per (company, year[, segment])
  p462  : 4-6-2 portfolio table                 -> 일반모형 CSM total per (company, year[, segment])
  sens  : 4-6-5 (1) assumption sensitivity      -> 8 standard shock rows per (company, year)

It only READS pdfs and WRITES the staging file
  data/_derived/reinsurer_ifrs17_csm_20261011/tables.json
No master is touched. All decisions (which filing wins, unit conversion, segment sums) are made in
build_reinsurer_csm_rows_20261011.py from this file, with the evidence kept side by side.

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_reinsurer_csm_tables_20261011.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "_derived" / "reinsurer_ifrs17_csm_20261011"
sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)

COS = {
    "KR1101": "KR1101_뮌헨재보험", "KR1102": "KR1102_스위스리아시아", "KR1103": "KR1103_제네럴재보험",
    "KR1104": "KR1104_하노버재보험", "KR1105": "KR1105_알지에이리인슈어런스", "KR1106": "KR1106_스코리재보험",
    "KR1107": "KR1107_퍼시픽라이프리",
}
FILINGS = ["FY2024_Q4", "FY2025_Q4"]
DASHES = {"-", "\u2013", "\u2014", "\u2212", "\uff0d"}
PAGE_GAP = 40.0
PCT = re.compile(r"^\d+(\.\d+)?%(p)?")
LABEL_RE = re.compile(r"^(사망률|장해질병|장기재물|해지율|사업비)")


# --------------------------------------------------------------------------------------------
# token helpers
# --------------------------------------------------------------------------------------------
def tok_to_num(s: str):
    """-> (value, flag). flag: '' normal | 'dash' printed '-' | 'neg0' printed '(0)' or '-0' | None not a number"""
    t = s.strip().replace("\u3000", "")
    if t in DASHES:
        return None, "dash"
    t2 = t.replace("\u2212", "-").replace("\u2013", "-")
    neg = False
    if t2.startswith("(") and t2.endswith(")"):
        neg, t2 = True, t2[1:-1]
    elif t2.startswith("-"):
        neg, t2 = True, t2[1:]
    t2 = t2.replace(",", "")
    if not re.fullmatch(r"\d+(\.\d+)?", t2):
        return None, None
    v = float(t2)
    if v == 0.0 and neg:
        return 0.0, "neg0"
    return (-v if neg else v), ""


def is_num(s: str) -> bool:
    return tok_to_num(s)[1] is not None


def yc(w):
    return (w["y0"] + w["y1"]) / 2.0


def virtual_words(doc, pages):
    """Words of consecutive pages in one coordinate system (y offset by cumulative page height)."""
    words, spans, off = [], [], 0.0
    for pn in pages:
        page = doc[pn - 1]
        h = page.rect.height
        for w in page.get_text("words"):
            words.append({"x0": w[0], "y0": w[1] + off, "x1": w[2], "y1": w[3] + off, "t": w[4], "page": pn})
        spans.append((pn, off, off + h))
        off += h + PAGE_GAP
    words.sort(key=lambda d: (round(d["y0"], 0), d["x0"]))
    return words, spans


def table_cells(doc, pages, spans):
    """cell rectangles (virtual y) of the ruled tables on the pages: [(x0, y0, x1, y1)]"""
    off = {pn: o for pn, o, _e in spans}
    cells = []
    for pn in pages:
        try:
            tabs = doc[pn - 1].find_tables()
        except Exception:
            continue
        for t in tabs.tables:
            for c in t.cells:
                cells.append((c[0], c[1] + off[pn], c[2], c[3] + off[pn]))
    return cells


def merge_split_minus(words, cells):
    """Some PDFs print the minus of a negative as its own word at the left edge of the cell ('-  329').

    A lone '-' is merged with the number to its right only when both sit in the SAME table cell
    (a dash standing alone in its own cell stays a printed dash = nil). Without cell rectangles the
    gap must be <= 9pt.
    """
    def same_cell(a, b):
        ax, ay, bx, by = (a["x0"] + a["x1"]) / 2, yc(a), (b["x0"] + b["x1"]) / 2, yc(b)
        return any(c[0] <= ax <= c[2] and c[1] <= ay <= c[3] and c[0] <= bx <= c[2] and c[1] <= by <= c[3] for c in cells)

    out, used = [], set()
    numeric = [w for w in words if is_num(w["t"]) and not w["t"].startswith(("-", "(", "−"))]
    for w in words:
        if id(w) in used:
            continue
        if w["t"] in DASHES:
            cand = [n for n in numeric if abs(yc(n) - yc(w)) <= 3 and 0 <= n["x0"] - w["x1"] <= 60 and id(n) not in used
                    and ((same_cell(w, n)) if cells else n["x0"] - w["x1"] <= 9)]
            if cand:
                n = min(cand, key=lambda n: n["x0"] - w["x1"])
                used.add(id(n))
                out.append({**n, "t": "-" + n["t"], "x0": w["x0"]})
                continue
        out.append(w)
    return [w for w in out if id(w) not in used or w.get("t", "").startswith("-")]


def find_year_headings(words):
    """[(year, y0, x0, page)] for '<2025년>' / '2025 년' / '<2025' + '년>' headings.

    Running page headers such as '2025 년 뮌헨재보험 현황' or '| 2025 년 경영공시' are not table headings.
    """
    heads = []
    for w in words:
        m = re.fullmatch(r"<?(20\d\d)(년>?)?>?", w["t"])
        if not m:
            continue
        if any(abs(o["y0"] - w["y0"]) < 3 and (o["t"] in ("현황", "경영공시", "|") or o["t"].endswith("현황"))
               for o in words if o is not w):
            continue
        year = int(m.group(1))
        if m.group(2):
            heads.append((year, w["y0"], w["x0"], w["page"]))
            continue
        for nx in words:
            if nx is not w and abs(nx["y0"] - w["y0"]) < 3 and -2 <= nx["x0"] - w["x1"] <= 30 and re.fullmatch(r"년>?", nx["t"]):
                heads.append((year, w["y0"], w["x0"], w["page"]))
                break
    return sorted(heads, key=lambda h: h[1])


def unit_near(words, y_lo, y_hi):
    cand = sorted([w for w in words if y_lo <= w["y0"] <= y_hi], key=lambda w: (round(w["y0"], 0), w["x0"]))
    for i, w in enumerate(cand):
        if w["t"].startswith("(단위") or w["t"] == "단위":
            txt = "".join(s["t"] for s in cand[i:i + 6])
            for u in ("백만원", "억원", "천원", "만원"):
                if u in txt:
                    return u
    return None


def cluster_rows(words, y_lo, y_hi, min_tokens, y_tol=3.0):
    cand = sorted([w for w in words if y_lo <= yc(w) <= y_hi and is_num(w["t"])], key=yc)
    clusters = []
    for w in cand:
        c = yc(w)
        if clusters and abs(c - clusters[-1]["yc"]) <= y_tol:
            clusters[-1]["toks"].append(w)
            clusters[-1]["yc"] = sum(yc(t) for t in clusters[-1]["toks"]) / len(clusters[-1]["toks"])
        else:
            clusters.append({"yc": c, "toks": [w]})
    return [{"yc": c["yc"], "toks": sorted(c["toks"], key=lambda w: w["x0"])} for c in clusters if len(c["toks"]) >= min_tokens]


def attach_wraps(row_tokens, words, y_pitch=20.0, x_tol=9.0):
    """Join digit fragments wrapped under a numeric cell token ('36'+'9' -> '369'). Use on the LAST table row only."""
    used, out = set(), []
    for tk in sorted(row_tokens, key=lambda d: d["x0"]):
        text, merged = tk["t"], False
        cont = sorted([w for w in words if w is not tk and id(w) not in used and 0 < w["y0"] - tk["y1"] < y_pitch
                       and abs(w["x1"] - tk["x1"]) <= x_tol and re.fullmatch(r"[\d,]+", w["t"] or "")], key=lambda w: w["y0"])
        if cont and re.fullmatch(r"[\d,]+", text):
            text += cont[0]["t"]
            used.add(id(cont[0]))
            merged = True
        out.append({"t": text, "x0": tk["x0"], "x1": tk["x1"], "merged": merged})
    return out


def row_label(words, row_y, x_max, y_win=12.0):
    cand = sorted([w for w in words if w["x1"] <= x_max and abs(yc(w) - row_y) <= y_win and not is_num(w["t"])],
                  key=lambda w: (round(w["y0"], 0), w["x0"]))
    return "".join(w["t"] for w in cand)


def ns(t: str) -> str:
    return re.sub(r"\s+", "", t)


# --------------------------------------------------------------------------------------------
# find_tables based fallback for the last row (ruled tables with wrapped cells)
# --------------------------------------------------------------------------------------------
def find_tables_total_rows(doc, pages, off):
    rows = []
    for pn in pages:
        page = doc[pn - 1]
        try:
            tabs = page.find_tables()
        except Exception:
            continue
        for t in tabs.tables:
            ext = t.extract()
            for i, r in enumerate(ext):
                cells = [("" if c is None else c.replace("\n", "")) for c in r]
                lab, toks = "", []
                for c in cells:
                    c2 = c.strip()
                    if not c2:
                        continue
                    if is_num(c2):
                        toks.append(c2)
                    elif not toks:
                        lab += c2
                try:
                    rb = t.rows[i].bbox
                    ry = (rb[1] + rb[3]) / 2 + off[pn]
                except Exception:
                    ry = t.bbox[1] + off[pn]
                rows.append({"y": ry, "page": pn, "label": lab, "toks": toks})
    return rows


# --------------------------------------------------------------------------------------------
# AMORT  (4-6-3 (2))
# --------------------------------------------------------------------------------------------
def amort_window(doc):
    start = end = None
    for i, p in enumerate(doc):
        n = ns(p.get_text())
        if start is None and "보험계약마진상각" in n and "1년" in n and "계" in n:
            start = i + 1
        if start is not None and "최적가정" in n:
            end = i + 1
            break
    if start is None:
        return []
    return list(range(start, (end if end else min(start + 3, len(doc))) + 1))


def extract_amort(pdf: Path):
    doc = fitz.open(pdf)
    pages = amort_window(doc)
    rec = {"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "pages": pages, "tables": []}
    if not pages:
        return rec
    words, spans = virtual_words(doc, pages)
    off = {pn: o for pn, o, _e in spans}
    heads = find_year_headings(words)
    title_y = None
    for w in words:
        if w["t"].startswith("②"):
            near = [x for x in words if abs(x["y0"] - w["y0"]) < 3 and x["x0"] > w["x0"]]
            if any("보험계약마진" in x["t"] for x in near):
                title_y = w["y0"]
                break
    end_y = next((w["y0"] for w in words if w["t"] == "최적가정"), 1e9)
    heads = [h for h in heads if (title_y is None or h[1] > title_y - 1) and h[1] < end_y]
    segs = sorted((w["y0"], w["t"]) for w in words if w["t"] in ("[생명보험]", "[손해보험]"))
    ft_rows = find_tables_total_rows(doc, pages, off)
    for k, h in enumerate(heads):
        y_lo = h[1]
        y_hi = heads[k + 1][1] if k + 1 < len(heads) else end_y
        unit = unit_near(words, y_lo - 5, y_lo + 120)
        sgs = [s for s in segs if y_lo <= s[0] < y_hi]
        bounds = [(s[0], s[1]) for s in sgs] if sgs else [(y_lo, None)]
        for bi, (by, bname) in enumerate(bounds):
            bhi = bounds[bi + 1][0] if bi + 1 < len(bounds) else y_hi
            rows = cluster_rows(words, by, bhi, min_tokens=10)
            data_rows, total = [], None
            for ri, r in enumerate(rows):
                toks = [t["t"] for t in r["toks"]]
                if toks[:10] == [str(i) for i in range(1, 11)]:
                    continue                                    # header row (bucket numbers 1..10)
                lab = row_label(words, r["yc"], r["toks"][0]["x0"] - 1)
                is_total = ("합계" in lab or lab.endswith("합") or "합" == lab[-1:])
                if is_total and ri == len(rows) - 1:
                    a = [m["t"] for m in attach_wraps(r["toks"], words)]
                    b = None
                    cand = [x for x in ft_rows if x["page"] == r["toks"][0]["page"] and abs(x["y"] - r["yc"]) < 14
                            and x["label"].startswith("합") and len(x["toks"]) >= 10]
                    if cand:
                        b = cand[0]["toks"]
                    total = {"A": a, "B": b, "page": r["toks"][0]["page"], "label": lab[-8:]}
                else:
                    data_rows.append({"label": lab[-14:], "toks": toks, "page": r["toks"][0]["page"]})
            rec["tables"].append({"year": h[0], "segment": bname, "unit": unit, "total_row": total,
                                  "data_rows": data_rows})
    return rec


# --------------------------------------------------------------------------------------------
# P462  (4-6-2)  -- 합계 row: 일반모형 [BEL, RA, CSM] then 변동수수료 [BEL, RA, CSM] then PAA
# --------------------------------------------------------------------------------------------
def extract_p462(pdf: Path):
    doc = fitz.open(pdf)
    start = end = None
    for i, p in enumerate(doc):
        n = ns(p.get_text())
        if start is None and "포트폴리오별" in n and "보험부채현황" in n:
            start = i + 1
        if start is not None and "변동내역" in n and i + 1 > start:
            end = i + 1
            break
        if start is not None and "변동내역" in n and i + 1 == start and "계리적가정" in n:
            end = i + 1
            break
    pages = list(range(start, (end if end else min(start + 3, len(doc))) + 1)) if start else []
    rec = {"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "pages": pages, "tables": []}
    if not pages:
        return rec
    words, _ = virtual_words(doc, pages)
    heads = find_year_headings(words)
    ty = next((w["y0"] for w in words if w["t"].startswith(("회계모형별", "회계보험별"))), -1)
    ey = next((w["y0"] for w in words if w["t"] == "변동내역"), 1e9)
    heads = [h for h in heads if ty - 1 <= h[1] < ey]
    segs = sorted((w["y0"], w["t"]) for w in words if w["t"] in ("[생명보험]", "[손해보험]"))
    for k, h in enumerate(heads):
        y_lo = h[1]
        y_hi = heads[k + 1][1] if k + 1 < len(heads) else ey
        unit = unit_near(words, y_lo - 5, y_lo + 120)
        sgs = [s for s in segs if y_lo <= s[0] < y_hi]
        bounds = [(s[0], s[1]) for s in sgs] if sgs else [(y_lo, None)]
        for bi, (by, bname) in enumerate(bounds):
            bhi = bounds[bi + 1][0] if bi + 1 < len(bounds) else y_hi
            rows = cluster_rows(words, by, bhi, min_tokens=3)
            tot = None
            for r in rows:
                lab = row_label(words, r["yc"], r["toks"][0]["x0"] - 1)
                if lab.endswith("합계") or lab == "합계" or lab.endswith("합"):
                    toks = [t["t"] for t in r["toks"]]
                    # the sheet may print a second '합계' row of zeros (PAA); keep the one with the biggest |value|
                    if tot is None or sum(abs(tok_to_num(x)[0] or 0) for x in toks) > sum(abs(tok_to_num(x)[0] or 0) for x in tot["toks"]):
                        tot = {"toks": toks, "page": r["toks"][0]["page"]}
            rec["tables"].append({"year": h[0], "segment": bname, "unit": unit, "total_row": tot})
    return rec


# --------------------------------------------------------------------------------------------
# SENS  (4-6-5 (1))
# --------------------------------------------------------------------------------------------
SLOTS = ["사망률", "장해질병(정액보상)", "장해질병(실손보상)", "장기재물기타", "해지율(상승)", "해지율(하락)",
         "사업비(수준)", "사업비(인플레이션)"]
MERGE_PAIRS = [(1, 2), (6, 7)]


def sens_window(doc):
    start = end = None
    for i, p in enumerate(doc):
        n = ns(p.get_text())
        if start is None and "가정민감도" in n and "보험위험" in n:
            start = i + 1
        if start is not None and ("금리위험" in n or "4-6-6)" in n):
            end = i + 1
            break
    if start is None:
        return []
    return list(range(start, (end if end else min(start + 3, len(doc))) + 1))


def columns_by_x(tokens, gap=22.0):
    toks = sorted(tokens, key=lambda w: (w["x0"] + w["x1"]) / 2)
    cols = []
    for w in toks:
        xc = (w["x0"] + w["x1"]) / 2
        if cols and xc - cols[-1]["xc"] <= gap:
            cols[-1]["toks"].append(w)
            cols[-1]["xc"] = xc
        else:
            cols.append({"toks": [w], "xc": xc})
    return cols


def extract_sens(pdf: Path):
    doc = fitz.open(pdf)
    pages = sens_window(doc)
    rec = {"pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"), "pages": pages, "tables": []}
    if not pages:
        return rec
    words, spans = virtual_words(doc, pages)
    words = merge_split_minus(words, table_cells(doc, pages, spans))
    heads = find_year_headings(words)
    start_y = next((w["y0"] for w in words if w["t"].startswith("①")), None)
    end_y = next((w["y0"] for w in words if w["t"].startswith("②") and w["y0"] > (start_y or 0)), 1e9)
    heads = [h for h in heads if (start_y is None or h[1] > start_y) and h[1] < end_y]
    for k, h in enumerate(heads):
        y_lo = h[1]
        y_hi = heads[k + 1][1] if k + 1 < len(heads) else end_y
        foot = [w for w in words if y_lo + 40 < w["y0"] < y_hi and re.match(r"^주1?\)?$|^주1\)", w["t"])]
        y_hi_foot = y_hi
        if foot:
            y_hi = min(y_hi, min(f["y0"] for f in foot))
        unit = unit_near(words, y_lo - 5, y_lo + 100)
        # row labels (first column) by y
        labels = sorted([w for w in words if y_lo < w["y0"] < y_hi and LABEL_RE.match(w["t"]) and w["x0"] < 200],
                        key=lambda w: w["y0"])
        # drop duplicates of the same label that sit on the same line (e.g. '사업비' + '(수준)' are separate words)
        pct = sorted([w for w in words if y_lo < w["y0"] < y_hi and PCT.match(w["t"]) and w["x0"] < 260], key=lambda w: w["y0"])
        x_shock_right = max([w["x1"] for w in pct], default=0) + 1
        body_top = (labels[0]["y0"] - 20) if labels else (min([yc(w) for w in pct], default=y_lo) - 25)
        body = [w for w in words if body_top <= yc(w) <= y_hi and w["x0"] >= x_shock_right
                and (is_num(w["t"]))]
        cols = columns_by_x(body)
        # base columns = the two left-most columns that have <= 2 tokens in total
        base_cols = [c for c in cols if len(c["toks"]) <= 2]
        var_cols = [c for c in cols if len(c["toks"]) > 2]
        # a dash-only column of single-token height could be the OCI column of a table without values: keep if >=3
        # footnote block (주1)~) of this table: shows how 당기손익 영향 is defined (company specific)
        foot_words = sorted([w for w in words if (min(f["y0"] for f in foot) if foot else y_hi) <= w["y0"] <= y_hi_foot],
                            key=lambda w: (round(w["y0"], 0), w["x0"]))
        foot_text = " ".join(w["t"] for w in foot_words)[:700]
        # row centres: every label-column word (all text lines of the row's label cell) between this label and
        # the next one; the label cell is vertically centred like the value cells of that row
        x_label_right = min([w["x0"] for w in pct], default=200.0) - 2
        row_centers = []
        for li, lw in enumerate(labels):
            nxt = labels[li + 1]["y0"] - 2 if li + 1 < len(labels) else y_hi
            lines = [w for w in words if lw["y0"] - 2 <= w["y0"] < nxt and w["x1"] <= x_label_right
                     and not is_num(w["t"]) and not PCT.match(w["t"])]
            row_centers.append(round(sum(yc(w) for w in lines) / len(lines), 1) if lines else round(yc(lw), 1))
        rec_t = {"year": h[0], "unit": unit, "page": h[3], "footnote": foot_text,
                 "pcts": [(round(yc(w), 1), w["t"]) for w in pct],
                 "row_centers": row_centers,
                 "labels": [(w["t"], round(yc(w), 1)) for w in labels],
                 "base": [[t["t"] for t in c["toks"]] for c in base_cols],
                 "n_var_cols": len(var_cols), "cols": []}
        for c in var_cols:
            rec_t["cols"].append({"x": round(sum((t["x0"] + t["x1"]) / 2 for t in c["toks"]) / len(c["toks"]), 1),
                                  "toks": [(round(yc(t), 1), t["t"]) for t in sorted(c["toks"], key=yc)]})
        rec["tables"].append(rec_t)
    return rec


# --------------------------------------------------------------------------------------------
def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    res = {"tool": "scripts/extract_reinsurer_csm_tables_20261011.py", "amort": {}, "p462": {}, "sens": {}}
    for code, d in COS.items():
        for fy in FILINGS:
            pdf = ROOT / "data" / "disclosure" / fy / "raw" / f"{d}.pdf"
            key = f"{code}|{fy}"
            for name, fn in (("amort", extract_amort), ("p462", extract_p462), ("sens", extract_sens)):
                try:
                    res[name][key] = fn(pdf)
                except Exception as e:  # noqa: BLE001
                    res[name][key] = {"error": repr(e), "pages": [], "tables": []}
            print(key, {n: (res[n][key].get("pages"), len(res[n][key].get("tables", []))) for n in ("amort", "p462", "sens")})
    out = OUT_DIR / "tables.json"
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("wrote", out.relative_to(ROOT), out.stat().st_size, "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
