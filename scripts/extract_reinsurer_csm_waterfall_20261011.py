# -*- coding: utf-8 -*-
"""Reinsurer branches -- CSM roll-forward (기초 -> 기말) from the audit-report notes (PDF text layer).

Ticket: inbox/parser/20261011T0430Z__orchestrator__KR1101-KR1108_2024.4Q-2026.2Q__reinsurer_csm_masters.md
Runlog: data/disclosure/_meta/reinsurer_ifrs17_csm_runlog.md

The management disclosures have no CSM roll-forward; the audit reports do (note: 보험계약부채 구성요소별 변동내역,
수재 일반모형 = the issued/assumed business, ceded tables are not read). Recipes below list, per audit report, the
pages of the current-year and prior-year table. Every table is read from the text layer by row geometry; the CSM
value of a row is the sum of the CSM columns (all columns between 위험조정 and the total; for 7-column tables the
three CSM method columns, the 4th CSM sub-total column is only a check).

Output (staging only, no master is touched):
  data/_derived/reinsurer_ifrs17_csm_20261011/audit_tables.json

Run:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/extract_reinsurer_csm_waterfall_20261011.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "_derived" / "reinsurer_ifrs17_csm_20261011" / "audit_tables.json"
sys.stdout.reconfigure(encoding="utf-8")
fitz.TOOLS.mupdf_display_errors(False)

DASHES = {"-", "\u2013", "\u2014", "\u2212"}
UNIT_TO_EOK = {"원": 1e-8, "천원": 1e-5, "백만원": 1e-2}

# (code, filing, pdf relative to data/disclosure/<filing>/, tables: [(year, pages)])  -- first table of a page list = 당기
RECIPES = [
    ("KR1101", "FY2025_Q4", "raw_aux/KR1101_뮌헨재보험__audit.pdf", [([58, 59], [2025, 2024])]),
    ("KR1101", "FY2024_Q4", "raw_aux/KR1101_뮌헨재보험__audit.pdf", [([57, 58], [2024, 2023])]),
    ("KR1101", "FY2023_Q4", "raw_aux/KR1101_뮌헨재보험__audit.pdf", [([64, 65], [2023, 2022])]),
    ("KR1102", "FY2025_Q4", "raw_aux/KR1102_스위스리아시아__audit.pdf", [([69, 70], [2025, 2024])]),
    ("KR1102", "FY2024_Q4", "raw_aux/KR1102_스위스리아시아__audit.pdf", [([66, 67], [2024, 2023])]),
    ("KR1102", "FY2023_Q4", "raw_aux/KR1102_스위스리아시아__audit.pdf", [([65, 66], [2023, 2022])]),
    ("KR1103", "FY2024_Q4", "raw_aux/KR1103_제네럴재보험__audit.pdf", [([51, 52], [2024, 2023])]),
    ("KR1103", "FY2023_Q4", "raw_aux/KR1103_제네럴재보험__audit.pdf", [([54, 55], [2023, 2022])]),
    ("KR1104", "FY2024_Q4", "raw/KR1104_하노버재보험.pdf", [([119, 120], [2024, 2023])]),
    ("KR1104", "FY2023_Q4", "raw/KR1104_하노버재보험.pdf", [([86, 87], [2023, 2022])]),
    ("KR1105", "FY2024_Q4", "raw/KR1105_알지에이리인슈어런스.pdf", [([185, 186], [2024, 2023])]),
    ("KR1105", "FY2023_Q4", "raw/KR1105_알지에이리인슈어런스.pdf", [([285, 286], [2023, 2022])]),
    ("KR1106", "FY2023_Q4", "raw/KR1106_스코리재보험.pdf", [([102, 103], [2023, 2022])]),
    ("KR1106", "FY2025_Q4", "raw_aux/KR1106_스코리재보험__audit.pdf", [([51, 52], [2025, 2024])]),
    ("KR1106", "FY2024_Q4", "raw_aux/KR1106_스코리재보험__audit.pdf", [([50, 51], [2024, 2023])]),
    ("KR1107", "FY2025_Q4", "raw_aux/KR1107_퍼시픽라이프리__audit.pdf", [([51, 52], [2025, 2024])]),
    ("KR1107", "FY2024_Q4", "raw_aux/KR1107_퍼시픽라이프리__audit.pdf", [([50, 51], [2024, 2023])]),
]

# Tables whose text layer is unusable (embedded font maps every glyph, digits included, to wrong code points): read from
# the rendered page (170-190 dpi crops) and typed in here with the CSM columns kept separate. The closing identity
# open + 조정 + 신계약 + 상각 + 금융 = close is re-checked in code (|diff| <= 2 천원) and the opening must equal the
# closing printed by the previous year's audit report.
VISION_TABLES = [
    {
        "code": "KR1103", "filing": "FY2025_Q4", "year": 2025, "pdf": "data/disclosure/FY2025_Q4/raw_aux/KR1103_제네럴재보험__audit.pdf",
        "pages": [54], "unit": "천원", "unit_source": "printed",
        "note": "page 54 (printed -52-) table '(4) 보험계약부채의 측정요소별 변동내역 (당기)'; CSM columns = 공정가치법 적용계약 + 그 밖의 모든 보험 계약; "
                "text layer garbled (glyph/digit mapping), values read from a 190 dpi render; 전기 table on page 55 re-read: equals the FY2024 audit's 2024 values",
        "open": [33736619, 3427108],            # 기초 보험계약부채(자산)
        "adj": [-8885167, -628576],             # 보험계약마진을 조정하는 변동
        "new": [0, 1919293],                    # 처음 인식한 계약의 효과
        "amort": [-3543088, -598568],           # 서비스를 제공한 보험계약마진
        "interest": [1001026, 135007],          # 당기손익인식 보험금융손익
        "close": [22309390, 4254265],           # 기말 보험계약부채(자산)
    },
]

OPEN = ["기초순장부금액", "기초순보험계약부채", "기초보험계약부채(자산)", "보험계약순부채(순자산)(A)"]
CLOSE = ["기말순장부금액", "기말순보험계약부채", "기말보험계약부채(자산)", "(A+B+C+D+E+F+G)", "당기말보험계약순부채(자산)"]
NEW = ["신계약인식효과", "처음인식한계약의효과", "기중최초인식한계약의효과"]
AMORT = ["서비스를제공한보험계약마진", "보험계약마진상각", "보험계약마진의상각", "당기손익으로인식한", "손익으로인식한보험계약", "이전을반영하기위해"]
# audit pages without a printed '(단위: ...)' line next to the table: the amounts are in 원 (11-digit CSM figures; the
# closing CSM then equals the 4-6-2 CSM of the management disclosure within rounding -- checked in the builder)
UNIT_OVERRIDE = {("KR1104", "FY2024_Q4"): "원", ("KR1104", "FY2023_Q4"): "원"}
ADJ = ["보험계약마진을조정하는", "보험계약마진을변경하는"]


def tok_num(t):
    t = t.strip()
    if t in DASHES:
        return "dash", 0.0
    s = t.replace("\u2212", "-")
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    elif s.startswith("-"):
        neg, s = True, s[1:]
    s = s.replace(",", "")
    if not re.fullmatch(r"\d+(\.\d+)?", s):
        return None, None
    v = float(s)
    return "num", (-v if neg else v)


def is_value(t):
    return tok_num(t)[0] is not None


def ns(t):
    return re.sub(r"\s+", "", t)


def yc(w):
    return (w["y0"] + w["y1"]) / 2


def page_rows(page, y_tol=3.0):
    words = [{"x0": w[0], "y0": w[1], "x1": w[2], "y1": w[3], "t": w[4]} for w in page.get_text("words")]
    nums = sorted([w for w in words if is_value(w["t"])], key=yc)
    clusters = []
    for w in nums:
        c = yc(w)
        if clusters and abs(c - clusters[-1]["y"]) <= y_tol:
            clusters[-1]["toks"].append(w)
            clusters[-1]["y"] = sum(yc(t) for t in clusters[-1]["toks"]) / len(clusters[-1]["toks"])
        else:
            clusters.append({"y": c, "toks": [w]})
    rows = []
    for ci, c in enumerate(clusters):
        toks = sorted(c["toks"], key=lambda w: w["x0"])
        x_first = toks[0]["x0"]
        lo = (clusters[ci - 1]["y"] + c["y"]) / 2 if ci > 0 else c["y"] - 14
        hi = (c["y"] + clusters[ci + 1]["y"]) / 2 if ci + 1 < len(clusters) else c["y"] + 14
        lab = sorted([w for w in words if w["x1"] <= x_first + 1 and lo <= yc(w) < hi and not is_value(w["t"])],
                     key=lambda w: (round(w["y0"], 0), w["x0"]))
        rows.append({"y": round(c["y"], 1), "label": "".join(w["t"] for w in lab), "toks": [t["t"] for t in toks]})
    return rows


def page_unit(page):
    m = re.search(r"\(\s*단위\s*:\s*(천원|백만원|원)\s*\)", re.sub(r"[ \t]+", " ", page.get_text()))
    return m.group(1) if m else None


def csm_of(toks):
    """CSM value of a row = sum of the CSM method columns; None if the row layout is not recognised"""
    vals = [tok_num(t)[1] for t in toks]
    n = len(vals)
    if n == 4:
        return vals[2]
    if n == 5:
        return vals[2] + vals[3]
    if n == 6:
        return vals[2] + vals[3] + vals[4]
    if n == 7:
        sub = vals[5]
        s3 = vals[2] + vals[3] + vals[4]
        return s3 if abs(s3 - sub) <= 2 else None        # the sub-total column must equal the three method columns
    return None


def has(label, pats):
    return any(p in label for p in pats)


def read_pages(doc, pages, years):
    """Walk the rows of the pages; each opening row starts a table, each closing row ends one."""
    tables, cur, unit = [], None, None
    for pn in pages:
        page = doc[pn - 1]
        unit = page_unit(page) or unit
        for r in page_rows(page):
            lab, n = ns(r["label"]), len(r["toks"])
            if n < 4:
                continue
            if cur is None:
                if has(lab, OPEN) and not has(lab, CLOSE):
                    cur = {"unit": unit, "pages": [pn], "rows": {}, "open_row": r}
                    cur["open"] = csm_of(r["toks"])
                continue
            if pn not in cur["pages"]:
                cur["pages"].append(pn)
            if has(lab, CLOSE) and not has(lab, OPEN):
                cur["close"] = csm_of(r["toks"])
                cur["close_row"] = r
                tables.append(cur)
                cur = None
                continue
            rows = cur["rows"]
            if has(lab, NEW) and "최초손상" not in lab:
                rows.setdefault("new", []).append((r["label"], csm_of(r["toks"])))
            elif has(lab, AMORT):
                rows.setdefault("amort", []).append((r["label"], csm_of(r["toks"])))
            elif has(lab, ADJ):
                rows.setdefault("adj", []).append((r["label"], csm_of(r["toks"])))
            if "보험금융손익계" in lab:
                rows.setdefault("int_total", []).append((r["label"], csm_of(r["toks"])))
            elif "소계(E)" in lab:
                rows.setdefault("int_E", []).append((r["label"], csm_of(r["toks"])))
            elif ("순보험금융비용" in lab or "순보험금융수익" in lab) and n == 4:
                rows.setdefault("int_net", []).append((r["label"], csm_of(r["toks"])))
            elif "당기손익인식보험금융손익" in lab or "기타포괄손익인식보험금융손익" in lab:
                rows.setdefault("int_split", []).append((r["label"], csm_of(r["toks"])))
            elif lab == "보험금융손익":
                rows.setdefault("int_plain", []).append((r["label"], csm_of(r["toks"])))
            elif has(lab, ["환율"]) and "환율차이로인한변동효과" in lab:
                rows.setdefault("fx", []).append((r["label"], csm_of(r["toks"])))
    out = []
    for i, t in enumerate(tables):
        out.append({"year": years[i] if i < len(years) else None, **t})
    return out


def interest_of(rows):
    for key in ("int_total", "int_E", "int_net", "int_plain"):
        if rows.get(key):
            return key, rows[key][0][1]
    if rows.get("int_split"):
        vals = [v for _, v in rows["int_split"]]
        return "int_split", sum(vals) if None not in vals else None
    return None, None


def main() -> int:
    res = {"tool": "scripts/extract_reinsurer_csm_waterfall_20261011.py", "tables": []}
    for code, filing, rel, specs in RECIPES:
        pdf = ROOT / "data" / "disclosure" / filing / rel
        doc = fitz.open(pdf)
        for pages, years in specs:
            tabs = read_pages(doc, pages, years)
            for t in tabs:
                t["unit_source"] = "printed" if t["unit"] else None
                if t["unit"] is None and (code, filing) in UNIT_OVERRIDE:
                    t["unit"], t["unit_source"] = UNIT_OVERRIDE[(code, filing)], "override_anchor_4-6-2"
            for t in tabs:
                rows = t["rows"]
                ikey, ival = interest_of(rows)
                f = UNIT_TO_EOK.get(t["unit"], None)
                rec = {
                    "code": code, "filing": filing, "year": t["year"], "pdf": str(pdf.relative_to(ROOT)).replace("\\", "/"),
                    "pages": t["pages"], "unit": t["unit"], "unit_source": t["unit_source"], "factor_to_eok": f,
                    "open": t.get("open"), "close": t.get("close"),
                    "new": [v for _, v in rows.get("new", [])], "amort": [v for _, v in rows.get("amort", [])],
                    "adj": [v for _, v in rows.get("adj", [])], "interest_key": ikey, "interest": ival,
                    "labels": {k: [l for l, _ in v] for k, v in rows.items()},
                    "open_label": t["open_row"]["label"], "close_label": t["close_row"]["label"],
                }
                res["tables"].append(rec)
                print(f"{code} {filing} {t['year']} p{t['pages']} unit={t['unit']} open={rec['open']} new={rec['new']} "
                      f"interest({ikey})={ival} amort={rec['amort']} adj={rec['adj']} close={rec['close']}")
            if len(tabs) != len(years):
                print(f"  !! {code} {filing}: expected {len(years)} tables on pages {pages}, found {len(tabs)}")
    for v in VISION_TABLES:
        o, a, n, am, it, c = (sum(v[k]) for k in ("open", "adj", "new", "amort", "interest", "close"))
        resid = o + a + n + am + it - c
        ok = abs(resid) <= 2
        prev = [t for t in res["tables"] if t["code"] == v["code"] and t["year"] == v["year"] - 1 and t["filing"] == "FY2024_Q4"]
        cont = (abs(prev[0]["close"] - o) <= 1) if prev else None
        res["tables"].append({
            "code": v["code"], "filing": v["filing"], "year": v["year"], "pdf": v["pdf"], "pages": v["pages"], "unit": v["unit"],
            "unit_source": v["unit_source"], "factor_to_eok": UNIT_TO_EOK[v["unit"]], "open": o, "close": c, "new": [n], "amort": [am],
            "adj": [a], "interest_key": "vision", "interest": it, "labels": {}, "open_label": "vision", "close_label": "vision",
            "method": "vision_read", "note": v["note"], "identity_residual_unit": resid, "identity_ok": ok, "continuity_ok": cont,
        })
        print(f"{v['code']} {v['filing']} {v['year']} VISION p{v['pages']} open={o} new={n} interest={it} amort={am} adj={a} close={c} "
              f"identity_residual={resid} ok={ok} continuity_with_prev_close={cont}")
        if not ok or cont is False:
            raise SystemExit("vision table failed its own checks")
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("wrote", OUT.relative_to(ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
