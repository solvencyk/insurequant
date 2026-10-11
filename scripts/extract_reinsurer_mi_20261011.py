# -*- coding: utf-8 -*-
"""Read 경영공시 1-1 (주요 경영지표) / 1-2 (주요 경영효율 지표) / 5-1 (수익성) of the reinsurer branches KR1101~KR1108.

READ ONLY: writes only data/_derived/reinsurer_ifrs17_csm_20261011/mi_tables.json.
The master's own extractor (extract_management_indicators.py) mis-reads this template for the reinsurers (it picks the
"증감" column or the wrong row for 1-1 pages whose labels carry `<AI801>` code lines), so the three tables are read
from the PDF text layer with PyMuPDF `find_tables()` (cell grid), keeping the raw cell text next to the parsed number.

Per (code, period) the output holds, for each table kind, the page, the unit, the column headers and the parsed rows:
  {"label": <cleaned label>, "cells": [<raw cell text>...], "vals": [cur, prior, delta] (floats or None), "flags": [...]}

Ticket: inbox/parser/20261011T0430Z__orchestrator__KR1101-KR1108_2024.4Q-2026.2Q__reinsurer_csm_masters.md (item 4)

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_reinsurer_mi_20261011.py [--only KR1101,KR1102]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
DISC = ROOT / "data" / "disclosure"
sys.path.insert(0, str(ROOT / "scripts"))
from _disclosure_pdf_paths import disclosure_pdfs  # noqa: E402
OUT = ROOT / "data" / "_derived" / "reinsurer_ifrs17_csm_20261011" / "mi_tables.json"
sys.stdout.reconfigure(encoding="utf-8")
CODES = [f"KR11{n:02d}" for n in range(1, 9)]
MAX_PAGES = 70

DASHES = {"-", "–", "—", "−", "－", "ㅡ"}
UNIT_FACTOR = {"억원": 1.0, "백만원": 0.01, "천원": 1e-5, "원": 1e-8}


def nz(s: str) -> str:
    return re.sub(r"\s+", "", s or "")


def clean_cell(c) -> str:
    return re.sub(r"\s+", " ", (c or "").replace("\n", " ")).strip()


def parse_num(raw: str):
    """-> (value or None, flag). flag: '' number | 'dash' | 'blank' | 'na' | 'text'"""
    t = nz(raw)
    if t == "":
        return None, "blank"
    if t in DASHES:
        return None, "dash"
    if t.upper() in ("N/A", "NA", "해당없음"):
        return None, "na"
    t2 = t.replace("−", "-").replace("–", "-").replace("％", "%").rstrip("%")
    neg = False
    if t2.startswith("(") and t2.endswith(")"):
        neg, t2 = True, t2[1:-1]
    elif t2.startswith("△") or t2.startswith("▲"):
        neg, t2 = True, t2[1:]
    elif t2.startswith("-"):
        neg, t2 = True, t2[1:]
    t2 = t2.replace(",", "")
    if not re.fullmatch(r"\d+(\.\d+)?", t2):
        return None, "text"
    v = float(t2)
    return (-v if neg else v), ""


# ---------------------------------------------------------------------------------------------
# label recognition (whitespace removed; angle-bracket codes and trailing notes dropped)
# ---------------------------------------------------------------------------------------------
def canon_label(raw: str):
    t = nz(raw)
    t = re.sub(r"<[^>]*>", "", t)            # <AI801>
    t = re.sub(r"\(\d+\)", "", t) if re.match(r"^\(\d\)", t) else t
    t = re.sub(r"^\(\d\)", "", t)            # (1) 운용자산이익률
    if t.startswith("자산") and len(t) == 2:
        return "assets"
    if t == "부채":
        return "liabilities"
    if t == "자본":
        return "equity"
    if t.startswith("당기순이익") or t.startswith("당기순손실") or t.startswith("당기순손익"):
        return "net_income"
    if t.startswith("지급여력비율") and "전" in t and "후" not in t:
        return "solv_pre"
    if t.startswith("지급여력비율") and "후" in t:
        return "solv_post"
    if t.startswith("운용자산이익") and ("A/B" in t or t in ("운용자산이익률", "운용자산이익율")):
        return "inv_yield"
    if t.startswith("영업이익률") or t.startswith("영업이익율"):
        return "op_margin"
    if t.startswith("총자산수익률") or t.startswith("총자산수익율"):
        return "roa"
    if t.startswith("자기자본수익률") or t.startswith("자기자본수익율"):
        return "roe"
    if t.startswith("투자이익"):
        return "inv_profit_A"
    if t.startswith("경과운용자산"):
        return "avg_inv_assets_B"
    if t.startswith("신계약률") or t.startswith("신계약율"):
        return "new_contract_rate"
    if t.startswith("효력상실및해약") or t.startswith("효력상실"):
        return "lapse_rate"
    if t.startswith("보험금지급률") or t.startswith("보험금지급율"):
        return "claims_paid_rate"
    if t.startswith("자산운용률") or t.startswith("자산운용율"):
        return "asset_mgmt_rate"
    m = re.match(r"^(13|25|37|49|61|73|85)회차", t)
    if m:
        return f"persist_{m.group(1)}"
    return None


KIND_REQ = {
    "t11": {"assets", "liabilities", "equity", "roe"},
    "t12": {"asset_mgmt_rate"},
    "t51": {"inv_profit_A", "avg_inv_assets_B"},
}


def find_unit_above(page, bbox):
    """nearest '(단위 ...)' text above the table top; falls back to the first one on the page"""
    words = page.get_text("words")
    lines = {}
    for w in words:
        key = round(w[1] / 3)
        lines.setdefault(key, []).append(w)
    cands = []
    for key, ws in lines.items():
        txt = "".join(x[4] for x in sorted(ws, key=lambda x: x[0]))
        if "단위" in txt:
            cands.append((min(x[1] for x in ws), txt))
    above = [c for c in cands if c[0] <= bbox[1] + 2]
    pick = max(above, key=lambda c: c[0]) if above else (cands[0] if cands else None)
    if pick is None:
        return None, None
    txt = pick[1]
    for u in ("백만원", "억원", "천원"):
        if u in txt:
            return u, txt
    return "원" if "원" in txt else None, txt


def read_table(tab):
    """rows of (clean text, cell bbox or None); the bbox lets a value be assigned to its header column by x position"""
    ex = tab.extract()
    rows = []
    for ri, r in enumerate(ex):
        try:
            boxes = tab.rows[ri].cells
        except Exception:  # noqa: BLE001
            boxes = []
        rows.append([(clean_cell(t), (boxes[j] if j < len(boxes) else None)) for j, t in enumerate(r)])
    return rows


def classify(rows):
    labs = set()
    for r in rows:
        for c in r[:3]:
            lab = canon_label(c[0])
            if lab:
                labs.add(lab)
    if KIND_REQ["t51"] <= labs:
        return "t51"
    if KIND_REQ["t11"] <= labs:
        return "t11"
    if "asset_mgmt_rate" in labs or "new_contract_rate" in labs:
        return "t12"
    return None


def _xc(box):
    return None if box is None else (box[0] + box[2]) / 2.0


def _value_cells(cells):
    """cells = [(text, bbox)]. Blank cells are layout padding; a '-' is a value; a text cell (e.g. the label printed again
    in a merged category column) is not a value and is kept aside. -> keep, vals, flags, dropped, xcs"""
    keep, vals, flags, dropped, xcs = [], [], [], [], []
    for c, box in cells:
        if nz(c) == "":
            continue
        v, fl = parse_num(c)
        if fl == "text":
            dropped.append(c)
            continue
        keep.append(c)
        vals.append(v)
        flags.append(fl)
        xcs.append(_xc(box))
    return keep, vals, flags, dropped, xcs


def parse_rows(rows):
    """a data row = label cell + numeric cells; the label may sit in col 0 or 1 (category column in front).
    Some tables split one logical row over three physical rows (label row / values row / blank row): a label row without
    numbers takes the numbers of the next row that has no label."""
    out, hdr = [], []
    pending = None
    for r in rows:
        lab, li = None, None
        for i, c in enumerate(r[:3]):
            lab = canon_label(c[0])
            if lab:
                li = i
                break
        if lab:
            cells, vals, flags, dropped, xcs = _value_cells(r[li + 1:])
            ent = {"label": lab, "label_raw": r[li][0], "cells": cells, "vals": vals, "flags": flags, "dropped": dropped, "xcs": xcs}
            out.append(ent)
            pending = ent if not cells else None
            continue
        if pending is not None:
            cells, vals, flags, dropped, xcs = _value_cells(r)
            if cells and not dropped and not any(nz(c) for c, _ in r[:2]):      # a values-only row (label cells blank)
                pending.update({"cells": cells, "vals": vals, "flags": flags, "split_row": True, "xcs": xcs})
                pending = None
                continue
            if dropped or any(nz(c) for c, _ in r[:2]):
                pending = None                                                    # another text row: no values for the label
        if not out:
            hdr.append(r)
    return out, hdr


def header_cols(hdr_rows):
    """x-centres of the three value columns (당기 / 전년동기 / 증감) from the header cells; None when not determinable"""
    cs = []
    for r in hdr_rows:
        for t, box in r:
            if box is None:
                continue
            tt = nz(t)
            if re.search(r"(해당|당기|전년|전기|증감|20\d\d년)", tt):
                cs.append(_xc(box))
    cs = sorted(set(round(x, 1) for x in cs))
    # merge centres closer than 8pt (same column)
    merged = []
    for x in cs:
        if merged and x - merged[-1] < 8:
            continue
        merged.append(x)
    return merged[-3:] if len(merged) >= 3 else None


def assign_columns(data, cols):
    """positional assignment of the numeric cells of every row to [cur, prior, delta] by x position; missing = blank"""
    for ent in data:
        xcs = ent.get("xcs") or []
        if cols is None or not ent["cells"] or any(x is None for x in xcs):
            ent["col_mode"] = "order"
            continue
        cells3, vals3, flags3 = [""] * 3, [None] * 3, ["blank"] * 3
        clash = False
        for t, v, fl, x in zip(ent["cells"], ent["vals"], ent["flags"], xcs):
            j = min(range(3), key=lambda k: abs(cols[k] - x))
            if cells3[j] != "":
                clash = True
            cells3[j], vals3[j], flags3[j] = t, v, fl
        ent["cells"], ent["vals"], ent["flags"] = cells3, vals3, flags3
        ent["col_mode"] = "x_clash" if clash else "x"


def header_labels(hdr_rows):
    txt = " ".join(" ".join(t for t, _ in r) for r in hdr_rows)
    qs = re.findall(r"(\d{2}\.\dQ)", txt.replace(" ", ""))
    ys = re.findall(r"(20\d{2})년", txt.replace(" ", ""))
    return {"quarters": qs[:4], "years": ys[:4], "text": clean_cell(txt)[:160]}


def geom_rows(page):
    """words clustered into visual rows by y-centre: [[y, [(x0, x1, text)...]]...] top to bottom"""
    ws = [w for w in page.get_text("words") if w[4].strip()]
    ws.sort(key=lambda w: ((w[1] + w[3]) / 2, w[0]))
    rows = []
    for w in ws:
        yc = (w[1] + w[3]) / 2
        if rows and abs(rows[-1][0] - yc) <= 3.5:
            rows[-1][1].append((w[0], w[2], w[4]))
            rows[-1][0] = (rows[-1][0] * (len(rows[-1][1]) - 1) + yc) / len(rows[-1][1])
        else:
            rows.append([yc, [(w[0], w[2], w[4])]])
    for r in rows:
        r[1].sort(key=lambda t: t[0])
    return rows


def parse_geom(page):
    """rows whose label (the non-numeric tokens left of the numbers) is recognised; numbers = numeric/dash tokens"""
    out = []
    for y, toks in geom_rows(page):
        lab_parts, num_cells = [], []
        for x0, x1, t in toks:
            if not lab_parts and not num_cells and re.fullmatch(r"\(\d\)", t):
                lab_parts.append(t)                      # the "(1)" index in front of a label
                continue
            v, fl = parse_num(t)
            if fl in ("", "dash"):
                num_cells.append(t)
            elif not num_cells:
                lab_parts.append(t)
        lab = canon_label("".join(lab_parts))
        if lab is None:
            continue
        vals, flags = [], []
        for c in num_cells:
            v, fl = parse_num(c)
            vals.append(v)
            flags.append(fl)
        out.append({"label": lab, "label_raw": "".join(lab_parts), "cells": num_cells, "vals": vals, "flags": flags, "y": round(y, 1),
                    "xcs": [(x0 + x1) / 2.0 for (x0, x1, t) in toks if parse_num(t)[1] in ("", "dash") and
                            not re.fullmatch(r"\(\d\)", t)][-len(num_cells):] if num_cells else []})
    # column centres from the rows that print exactly three numbers; the other rows are assigned by x position
    full = [r for r in out if len(r["cells"]) == 3 and len(r["xcs"]) == 3]
    if len(full) >= 2:
        cols = [sorted(r["xcs"][k] for r in full)[len(full) // 2] for k in range(3)]
        assign_columns(out, cols)
    return out


def process(code, period):
    pdfs = [str(p) for p in disclosure_pdfs(period, code)]      # raw/ first, pdf/ as the fallback (same sorted list for every period that has raw/ files)
    if not pdfs:
        return None
    pdf = pdfs[0]
    doc = fitz.open(pdf)
    res = {"pdf": str(Path(pdf).relative_to(ROOT)).replace("\\", "/"), "npages": len(doc), "tables": {}, "notes": []}
    ntext = sum(1 for i in range(min(len(doc), 6)) if len(doc[i].get_text()) > 40)
    if ntext == 0:
        res["notes"].append("no_text_layer_first_pages")
        return res
    for pn in range(1, min(len(doc), MAX_PAGES) + 1):
        page = doc[pn - 1]
        flat = nz(page.get_text())
        if not (("자기자본수익" in flat) or ("자산운용률" in flat) or ("경과운용자산" in flat) or ("신계약률" in flat)):
            continue
        try:
            tabs = page.find_tables().tables
        except Exception as e:  # noqa: BLE001
            res["notes"].append(f"find_tables error p{pn}: {e}")
            continue
        for ti, tab in enumerate(tabs):
            rows = read_table(tab)
            kind = classify(rows)
            if kind is None:
                continue
            data, hdr = parse_rows(rows)
            assign_columns(data, header_cols(hdr))
            unit, unit_txt = find_unit_above(page, tab.bbox)
            ent = {"page": pn, "bbox": [round(v) for v in tab.bbox], "unit": unit, "unit_text": (unit_txt or "")[:60],
                   "header": header_labels(hdr), "rows": data}
            res["tables"].setdefault(kind, []).append(ent)
    # geometry fallback for the 5-1 block and the 1-2 block when find_tables() did not return them
    keep_all = {"inv_yield", "op_margin", "roa", "roe", "new_contract_rate", "lapse_rate", "claims_paid_rate", "asset_mgmt_rate",
                "inv_profit_A", "avg_inv_assets_B"}
    for kind, need, trig in (("t51", {"inv_profit_A", "avg_inv_assets_B"}, "경과운용자산"), ("t12", {"asset_mgmt_rate"}, "자산운용률")):
        if kind in res["tables"]:
            continue
        for pn in range(1, min(len(doc), MAX_PAGES) + 1):
            page = doc[pn - 1]
            flat = nz(page.get_text())
            if trig not in flat:
                continue
            rows = parse_geom(page)
            labs = {r["label"] for r in rows}
            if need <= labs:
                ytop = min(r["y"] for r in rows if r["label"] in need)
                unit, unit_txt = find_unit_above(page, [0, ytop, 0, 0])
                res["tables"].setdefault(kind, []).append({
                    "page": pn, "bbox": None, "unit": unit, "unit_text": (unit_txt or "")[:60], "via": "geometry",
                    "header": {"quarters": [], "years": [], "text": "(geometry rows: no cell header)"},
                    "rows": [r for r in rows if r["label"] in keep_all or r["label"].startswith("persist_")]})
                break
    for k in ("t11", "t12", "t51"):
        if k not in res["tables"]:
            res["notes"].append(f"{k}: not found")
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=",".join(CODES))
    a = ap.parse_args()
    only = [c.strip() for c in a.only.split(",")]
    periods = sorted(p.name for p in DISC.iterdir() if p.is_dir() and re.fullmatch(r"FY\d{4}_Q[1-4]", p.name))
    out = {"tool": "scripts/extract_reinsurer_mi_20261011.py", "docs": {}}
    for period in periods:
        for code in only:
            r = process(code, period)
            if r is None:
                continue
            out["docs"][f"{code}|{period}"] = r
            kinds = {k: len(v) for k, v in r["tables"].items()}
            print(f"{code} {period}: tables {kinds} notes {r['notes']}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(out['docs'])} docs")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
