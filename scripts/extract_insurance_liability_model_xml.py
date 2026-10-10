# -*- coding: utf-8 -*-
"""
Read the "회계모형별, 포트폴리오별 보험부채 현황" note table (BEL / RA / CSM by 일반모형 · 변동수수료접근법 and the
보험료배분접근법 liability, 합계 row) out of the DART 사업/반기/분기보고서 (and 감사보고서) XML.

Why: the 정기경영공시 PDF carries this table as 4-6-2 (year-end template, from FY2024) and 2-4 (quarterly template, from
2025.1Q) -- insurance_liability_portfolio.json items 1-8.  The same table is a financial-statement note in many DART
filings, and a FY2024 year-end note shows BOTH the current and the prior year end ("당기말 / 전기말"): the prior-year
table is the only disclosure of the 2023-12-31 balances in this form (the FY2023 filings do not contain the table at all).
It is also a second, independent reading of the 2024-12-31 balances for the cross-check against the PDF and the source
for filers whose PDF is an image scan.

Definition (identical to the PDF table): 원수보험 및 수재보험계약의 잔여보장요소 (net of 잔여보장자산; negative = asset),
separate-statement scope.  The 재보험(출재) tables and the consolidated tables are dropped.

Output per table (dict): scope, period (cur|prior), unit, reins, vals {model: {BEL, RA, CSM, TOT}} in the table's unit,
the column map and the 합계 row, so that every cell value can be traced to table index + row label.
Pure function of the file bytes; no master is read or written.
"""
from __future__ import annotations

import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_lic as lic  # noqa: E402  (table grid parser, section markers, unit helpers)

CAP_RE = re.compile(r"회계\s*모형\s*별|회계\s*모형\s*및\s*포트폴리오|포트폴리오\s*및\s*회계\s*모형|회계\s*모형\s*,?\s*부채\s*포트폴리오")
MODEL_WORDS = ("일반모형", "변동수수료", "보험료배분")


def _model_of(p: str):
    if "변동수수료" in p:
        return "VFA"
    if "보험료배분" in p:
        return "PAA"
    if "일반모형" in p:
        return "GMM"
    return None


def _comp_of(p: str):
    if "마진" in p:
        return "CSM"
    if "위험조정" in p or "위험요소" in p:       # 하나생명 heads the RA column '위험요소'
        return "RA"
    if "최선추정" in p or ("현금흐름" in p and "취득" not in p):
        return "BEL"
    return None


def column_map(g, h, nl):
    """[(col, model, comp)] for the numeric columns.  model in GMM/VFA/PAA/ALL; comp in BEL/RA/CSM/TOT.
    A column under 보험료배분접근법 without BEL/RA/CSM wording is the PAA liability (comp TOT); a column headed only
    '합계' (no model word) is the grand total ('ALL','TOT')."""
    paths = lic.col_paths(g, h)
    out = []
    for c in range(nl, len(paths)):
        p = paths[c]
        if lic.PRIOR_COL.search(p):
            continue
        m, k = _model_of(p), _comp_of(p)
        if m == "PAA" and k is None:
            out.append((c, "PAA", "TOT"))
        elif m and k:
            out.append((c, m, k))
        elif m is None and k is None and re.search(r"합계|^계$|총계", p.split("|")[-1] if p else ""):
            out.append((c, "ALL", "TOT"))
        elif m == "GMM" and k is None:
            out.append((c, "GMM", "TOT"))
        elif m == "VFA" and k is None:
            out.append((c, "VFA", "TOT"))
    # no model wording over the BEL/RA/CSM columns (e.g. 한화손해보험: '최선추정부채 | 위험조정 | 보험계약마진 |
    # 보험료배분접근법'): exactly one BEL/RA/CSM triple is the 일반모형 (the PDF 합계 run agrees); anything else stays unmapped
    bare = [(c, k) for c, m, k in [(c, _model_of(paths[c]), _comp_of(paths[c])) for c in range(nl, len(paths))]
            if m is None and k in ("BEL", "RA", "CSM") and not lic.PRIOR_COL.search(paths[c])]
    if bare and not any(m == "GMM" for _, m, _ in out) and sorted(k for _, k in bare) == ["BEL", "CSM", "RA"]:
        out += [(c, "GMM", k) for c, k in bare]
    return out, paths


def _norm_label(cells, nl):
    parts = []
    for c in range(min(nl, len(cells))):
        x = lic.comp(cells[c])
        if x and (not parts or parts[-1] != x):
            parts.append(x)
    return "".join(parts)


def harvest_file(path) -> list:
    """candidate model/portfolio tables of one xml, in document order.  `pre` = all text since the previous
    big (>=4 rows) table, small caption/unit boxes included, last 500 characters."""
    t = lic.read_xml(path)
    ms = lic.markers(t)
    tops = [(m.start(), m.group(1).strip()) for m in lic.TITLE_RE.finditer(t)
            if re.search(r"재무제표|재무상태표|주석|감사보고서", m.group(1))]
    out = []
    last_end = 0
    buf = ""
    for i, m in enumerate(lic.TAB_RE.finditer(t)):
        body = m.group(0)
        ntr = body.upper().count("<TR")
        between = lic.clean(t[max(last_end, m.start() - 1500):m.start()])
        buf = (buf + " " + between)[-1500:]
        last_end = m.end()
        if ntr < 4:
            buf = (buf + " " + lic.clean(body))[-1500:]
            continue
        pre = buf[-500:]
        buf = ""
        flat = lic.comp(lic.clean(body))
        has_model = any(w in flat for w in MODEL_WORDS)
        has_bel = "최선추정" in flat or "현금흐름" in flat
        by_header = has_model and has_bel and ("위험조정" in flat or "위험요소" in flat) and "마진" in flat
        by_caption = bool(CAP_RE.search(pre)) and "보험료배분" in flat
        if not ("합계" in flat and (by_header or by_caption)):
            continue
        if "발생사고" in flat or "기초" in flat[:400]:
            continue                      # a roll-forward table, not the portfolio/model table
        g, _ = lic.parse_table(body)
        h = lic.split_header_rows(g)
        nl = lic.label_cols(g, h)
        cmap, paths = column_map(g, h, nl)
        if not cmap:
            continue
        tot_rows = [ri for ri in range(h, len(g))
                    if _norm_label(g[ri], nl) in ("합계", "계", "총계") or re.fullmatch(r"(합계)+", _norm_label(g[ri], nl))]
        if not tot_rows:
            continue
        # one table holding BOTH year-end blocks (first label column '당기' ... '전기' ..., a 합계 row closing each block,
        # e.g. 미래에셋생명): one entry per block, the period taken from the block label
        blk = {}
        for ri in range(h, len(g)):
            first = lic.comp(g[ri][0]) if g[ri] else ""
            if first in ("당기", "당분기", "당반기", "당기말"):
                blk.setdefault("cur", []).append(ri)
            elif first in ("전기", "전분기", "전반기", "전기말"):
                blk.setdefault("prior", []).append(ri)
        entries = []
        if len(blk) == 2 and len(tot_rows) >= 2:
            cur_end = max(blk["cur"])
            prior_start = min(blk["prior"])
            first_period = "cur" if min(blk["cur"]) < prior_start else "prior"
            t_first = [r for r in tot_rows if r > (cur_end if first_period == "cur" else max(blk["prior"]))]
            ordered = sorted(tot_rows)
            # the 합계 row closing the first block is the first one after that block's last labelled row
            first_blk_last = max(blk[first_period])
            second = "prior" if first_period == "cur" else "cur"
            r1 = next((r for r in ordered if r > first_blk_last), None)
            r2 = ordered[-1]
            if r1 is not None and r1 != r2:
                entries = [(first_period, r1), (second, r2)]
        if not entries:
            entries = [(None, tot_rows[-1])]
        for bper, tot_row in entries:
            vals = {}
            for c, model, comp in cmap:
                v = lic.parse_num(g[tot_row][c])
                if v is None:
                    continue
                vals.setdefault(model, {}).setdefault(comp, 0.0)
                vals[model][comp] += v
            out.append({
                "i": i, "note": lic.scope_at(ms, m.start()), "top": lic.scope_at(tops, m.start()),
                "pre": pre, "unit_pre": unit_of(pre) or unit_of(lic.clean(body)[:200]),
                "nrows": len(g), "ncols": len(g[0]), "h": h, "nl": nl, "block_period": bper,
                "cmap": cmap, "paths": [p[:70] for p in paths], "tot_row": tot_row,
                "total_row_cells": g[tot_row], "vals": vals,
            })
    return out


COMPAR = re.compile(r"(당분기|당반기|당기)말?\s*(와|과|및|,|/)\s*(전분기|전반기|전기)말?")
M_CUR = re.compile(r"\(당\)|당분기|당반기|당기")
M_PRIOR = re.compile(r"\(전\)|전분기|전반기|전기")
REINS_PAT = re.compile(r"(?<![수원])재보험계약|출재|보유한\s*재보험|재보험자|재보험\s*(?:자산|부채)|재보험\s*[\)\.]")
# a sentence that names the issued book AND the ceded book together ('보험계약부채 및 출재보험계약자산(부채)') captions a
# table of the issued book (the ceded part is a column / a row group of the same table): not a reinsurance table
GENERIC_BOTH2 = re.compile(r"(보험계약부채|보험계약자산|원수보험|원수|수재|발행한\s*보험계약|보험계약)\s*(?:\([^)]*\))?\s*(및|와|과|,)\s*(출재|재보험)")


def unit_of(ctx: str):
    """last '(단위: 백만원)' / '(단위 백만원)' / '단위:천원' cue in the text"""
    m = re.findall(r"단위\s*[:：]?\s*(백\s*만\s*원|천\s*원|억\s*원|원)", ctx or "")
    return m[-1].replace(" ", "") if m else None


def classify(tabs: list) -> list:
    """scope (con|sep), period (cur|prior), reins, in document order.
    period: the LAST explicit marker in the 200 characters in front of the table (comparison phrases such as
    '당기와 전기' are removed first); with no marker: the second of an adjacent same-shape pair is the prior-year table
    (current first -- the filers' order), anything else is current.  unit: explicit cue, else the pair partner's."""
    res = []
    prev = None
    for t in tabs:
        t = dict(t)
        pre = t["pre"]
        sent = list(re.finditer(r"다음과\s*같", pre))
        # 1) markers AFTER the introducing sentence ('... 다음과 같습니다. 1) 당기'); 2) else inside that sentence (comparison
        # phrases such as '당기와 전기' removed); older text (a previous note's '당기말 전기말' column heads) is never read
        after = pre[sent[-1].end():] if sent else pre[-120:]
        inside = pre[max(0, sent[-1].start() - 160):sent[-1].start()] if sent else ""
        marks = sorted([(m.start(), "cur") for m in M_CUR.finditer(COMPAR.sub(" ", after))]
                       + [(m.start(), "prior") for m in M_PRIOR.finditer(COMPAR.sub(" ", after))])
        if not marks:
            # inside the sentence only the phrase '당기말 현재' / '전기말 현재' counts (column heads such as '구분 당기말 전기말'
            # of a neighbouring table must not be read as a marker)
            ins = COMPAR.sub(" ", inside)
            marks = sorted([(m.start(), "cur") for m in re.finditer(r"(?:당분기|당반기|당기)말?\s*현재", ins)]
                           + [(m.start(), "prior") for m in re.finditer(r"(?:전분기|전반기|전기)말?\s*현재", ins)])
        tail = pre[max(0, sent[-1].start() - 200):] if sent else pre[-200:]
        if t.get("block_period"):
            t["period"], t["period_src"] = t["block_period"], "block"
        elif marks:
            t["period"], t["period_src"] = marks[-1][1], "marker"
        elif (prev is not None and prev["period"] == "cur" and t["i"] - prev["i"] <= 3
              and (prev["nrows"], prev["ncols"]) == (t["nrows"], t["ncols"]) and prev["con"] == (("연결" in t["note"]) or ("연결" in t["top"]))):
            t["period"], t["period_src"] = "prior", "pair"
        else:
            t["period"], t["period_src"] = "cur", "default"
        t["con"] = ("연결" in t["note"]) or ("연결" in t["top"])
        t["unit"] = t["unit_pre"]
        if t["unit"] is None and prev is not None and t["i"] - prev["i"] <= 3:
            t["unit"] = prev["unit"]
        t["reins"] = bool(REINS_PAT.search(GENERIC_BOTH2.sub(" ", tail)))
        res.append(t)
        prev = t
    return res


def model_totals(t: dict, scale: float) -> dict:
    """items 1-7 in 억원 from one table: scale converts the table unit to 억원."""
    v = t["vals"]
    g = lambda m, c: v.get(m, {}).get(c)
    items = {
        1: g("GMM", "BEL"), 2: g("GMM", "RA"), 3: g("GMM", "CSM"),
        4: g("VFA", "BEL"), 5: g("VFA", "RA"), 6: g("VFA", "CSM"),
        7: g("PAA", "TOT"),
    }
    return {k: (None if x is None else x * scale) for k, x in items.items()}


UNIT_TO_EOK = {"원": 1e-8, "천원": 1e-5, "백만원": 1e-2, "억원": 1.0}


if __name__ == "__main__":
    import glob
    sys.stdout.reconfigure(encoding="utf-8")
    fy = sys.argv[1]
    codes = sys.argv[2:]
    for d in sorted(os.listdir(REPO / "data" / "dart" / fy / "raw")):
        code = d[:6]
        if codes and code not in codes:
            continue
        files = sorted(glob.glob(str(REPO / "data" / "dart" / fy / "raw" / d / "*.xml"))) + \
            sorted(glob.glob(str(REPO / "data" / "dart" / fy / "raw" / d / "xml" / "*.xml")))
        for f in files:
            tabs = classify(harvest_file(f))
            for t in tabs:
                u = t["unit"]
                sc = UNIT_TO_EOK.get(u)
                it = model_totals(t, sc) if sc else {}
                tail = (" ".join(f"{k}:{x:,.1f}" if x is not None else f"{k}:-" for k, x in it.items())) if sc else ("RAW " + str(t["vals"]))
                print(f"{code} {Path(f).name[-18:]} T{t['i']:<4} {'CON' if t['con'] else 'sep'} {t['period']:5s}({t['period_src'][:4]}) "
                      f"{'REINS' if t['reins'] else '     '} unit={u} " + tail)
