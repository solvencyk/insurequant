# -*- coding: utf-8 -*-
"""
Interim-quarter backfill of insurance_liability_portfolio.json: 2024.1Q-2024.3Q and 2023.1Q-2023.3Q
(ticket 20261011T0320Z; owner 2026-10-11 「이 round 끝나면 나머지 시점도 백필 전부」).  Same rules as the year-end backfill
(scripts/load_ilp_backfill_pre2025.py): ADDITIVE rows only, 억원, every cell reconciled before anything is written (nothing is written
without --write), provenance per cell, restated basis marked.

Rows added
  items 10-15  발생사고요소(LIC) / 잔여보장요소(LRC) / 합계 of the quarter itself, from the DART 분기·반기보고서 note
               「보험계약부채(자산)의 변동」 with the unchanged stage-1 engine (scripts/extract_insurance_liability_lic.py), 23 DART filers.
  items 1-8    (2024.1Q-3Q only) LRC by measurement model = the 2-4 table of the 경영공시 -- the 2024 quarterly 경영공시 had no such table, but the
               2025.1Q/2Q/3Q 경영공시 print a prior-year-same-quarter table behind the current one (scripts/extract_insurance_liability_model_pdf_interim.py;
               image PDFs 미래에셋 and AIA were read by eye at 230 dpi: MANUAL below, each with its evidence).  2023.1Q-3Q has no such source: items 1-8 stay empty.

Rules per cell (all recorded in the provenance)
  * the FIRST table of the same PDF page must equal the master's 2025.NQ items 1-7 (proves section + reading) -- else withheld
  * the prior-year vector must not be identical to the 2024.4Q vector or to the current-quarter vector (a filer copy error) -- else withheld
  * R-LIC2: item 8 vs the DART NET remaining-coverage liability of the same quarter (+-0.5 % or 0.5억; the three 2-4-includes-LIC filers vs item 15)
  * CSM(items 3+6) vs CSM_waterfall closing CSM, max(2억, 0.5 %): YELLOW only
  * RESTATED comparative (R-LIC2 DIFF, or CSM off by > 2 %): the 2025.NQ filing restated the 2024 interim period.  The items 10-15 of that cell are then
    read from the PRIOR-period tables of the same 2025.NQ DART filing (cur/prior swapped, as scripts/unify_ilp_restated_3cells_2023_4q.py does) so that
    the whole cell is on the latest basis; original-basis values stay in the provenance and the sidecar data/_derived/ilp_restated_comparative.json
    (basis latest_filing_comparative_restatable).  If the restated read does not confirm the PDF the items 1-8 are withheld instead (never mixed).

Usage:
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/load_ilp_interim_2023_2024.py --quarters 2024.1Q [--write] [--report out.json]
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import extract_insurance_liability_lic as lic  # noqa: E402
import extract_insurance_liability_model_pdf_interim as I  # noqa: E402
import load_ilp_backfill_pre2025 as L  # noqa: E402

HERE = REPO / "data" / "disclosure" / "_meta" / "ilp_round3_20261011"
SIDECAR_RESTATED = REPO / "data" / "_derived" / "ilp_restated_comparative.json"
TICKET = "inbox/parser/20261011T0320Z__orchestrator__MULTI_2023.1Q-2026.2Q__ilp_remaining_backfill_lic23_reinsurers.md"
BASIS_RESTATED = "latest_filing_comparative_restatable"
REINS = L.REINS

CFG = {
    "2024.1Q": dict(lic_fy="FY2024_Q1", pdf_fy="FY2025_Q1", pdf_q="2025.1Q", n=1, lrc=True),
    "2024.2Q": dict(lic_fy="FY2024_Q2", pdf_fy="FY2025_Q2", pdf_q="2025.2Q", n=2, lrc=True),
    "2024.3Q": dict(lic_fy="FY2024_Q3", pdf_fy="FY2025_Q3", pdf_q="2025.3Q", n=3, lrc=True),
    "2023.1Q": dict(lic_fy="FY2023_Q1", lrc=False),
    "2023.2Q": dict(lic_fy="FY2023_Q2", lrc=False),
    "2023.3Q": dict(lic_fy="FY2023_Q3", lrc=False),
}

# --------------------------------------------------------------------------------------------------------------------
# evidence-backed per-cell decisions
# --------------------------------------------------------------------------------------------------------------------
# 2-4 tables of image-only PDFs, read by eye on a 230 dpi render of the 합계 row of the prior-year ('전년 동기') table.  run = 7 value slots
# [일반모형 BEL, RA, CSM, 변동수수료 BEL, RA, CSM, 보험료배분]  in 억원.  The 합계 row of the CURRENT table of the same page equals the master's 2025.NQ cell
# (checked by eye for every one of these); 미래에셋's three readings are additionally confirmed by the DART restated prior-period tables
# (net LRC 253,768.08 / 256,357.37 / 257,687.79 vs 253,769 / 256,357 / 257,689).
MANUAL = {
    ("KR0079", "2024.1Q"): dict(run=[125532, 2687, 15986, 103502, 1122, 4940, 0], file="data/disclosure/FY2025_Q1/raw/KR0079_미래에셋생명보험.pdf", page=9,
                                label="전년 동기 (24.1Q)", evidence="image PDF; rendered p9 at 230 dpi, 합계 row of the 전년 동기 (24.1Q) table: 125,532 2,687 15,986 103,502 1,122 4,940 (PAA blank)"),
    ("KR0079", "2024.2Q"): dict(run=[129522, 2687, 16268, 102159, 1086, 4635, 0], file="data/disclosure/FY2025_Q2/raw/KR0079_미래에셋생명보험.pdf", page=10,
                                label="전년 동기 (24.2Q)", evidence="image PDF; rendered p10 at 230 dpi, 합계 row of the 전년 동기 (24.2Q) table: 129,522 2,687 16,268 102,159 1,086 4,635 (PAA blank)"),
    ("KR0079", "2024.3Q"): dict(run=[133701, 2727, 16751, 99574, 1033, 3903, 0], file="data/disclosure/FY2025_Q3/raw/KR0079_미래에셋생명보험.pdf", page=9,
                                label="전년 동기 (24.3Q)", evidence="image PDF; rendered p9 at 230 dpi, 합계 row of the 전년 동기 (24.3Q) table: 133,701 2,727 16,751 99,574 1,033 3,903 (PAA blank)"),
    ("KR0080", "2024.1Q"): dict(run=[99832, 3646, 14841, 7424, 22, 45, 12], file="data/disclosure/FY2025_Q1/raw/KR0080_에이아이에이생명보험.pdf", page=9,
                                label="전년 동기 (24.1Q)", evidence="image PDF; rendered p9 at 230 dpi, 합계 row of the 전년 동기 (24.1Q) table: 99,832 3,646 14,841 7,424 22 45 12"),
    ("KR0080", "2024.2Q"): dict(run=[104045, 3653, 16948, 7487, 21, 41, 8], file="data/disclosure/FY2025_Q2/raw/KR0080_에이아이에이생명보험.pdf", page=11,
                                label="전년 동기 (24.2Q)", evidence="image PDF; rendered p11 at 230 dpi, 합계 row of the 전년 동기 (24.2Q) table: 104,045 3,653 16,948 7,487 21 41 8"),
    ("KR0080", "2024.3Q"): dict(run=[111150, 3743, 16790, 7104, 22, 36, 6], file="data/disclosure/FY2025_Q3/raw/KR0080_에이아이에이생명보험.pdf", page=10,
                                label="전년 동기 (24.3Q)", evidence="image PDF; rendered p10 at 230 dpi, 합계 row of the 전년 동기 (24.3Q) table: 111,150 3,743 16,790 7,104 22 36 6"),
}
# image PDF whose rendering shows ONLY the current-quarter table
DOC_ABSENT = {
    ("KR0010", "2024.1Q"): "KB손해보험 2025.1Q 경영공시는 스캔 PDF: p8 렌더링에서 2-4 는 <2025년 1분기> 표 하나뿐(전년 동기 표 없음)",
    ("KR0010", "2024.3Q"): "KB손해보험 2025.3Q 경영공시는 스캔 PDF: p6 렌더링에서 2-4 는 <2025년 3분기> 표 하나뿐(전년 동기 표 없음)",
}
# value scale printed wrongly by the filer: (code, pdf_fy) -> extra divisor.  ABL 2025.2Q prints '(단위 : 억원)' over 백만원-scale numbers (the master cell was
# corrected the same way on 2026-10-10: values/100; the 2026.2Q 공시 prior-year table, in true 억원, agrees)
UNIT_FIX = {("KR0070", "FY2025_Q2"): 100.0}
# first table of the PDF != master 2025.NQ although the reading is right (documented per cell)
FIRST_TABLE_EXCEPTION = {
    ("KR0076", "FY2025_Q1"): "아이엠라이프 2025.1Q 자체 합계 행은 변액사망 340/18/65 를 빠뜨려 마스터는 2026.1Q 공시 전기 칸으로 보정돼 있다(런로그 stage1 §10 의 정찰). "
                           "전년 동기 표의 합계는 상세행 합과 반올림 안에서 같다(BEL 37,672 vs 37,670 · RA 680 vs 679 · CSM 5,261 vs 5,259)",
}
# label of the prior-year table is wrong in the filing (typo), values are the 2024.NQ ones (trend + BS item 20)
LABEL_EXCEPTION = {
    ("KR1011", "FY2025_Q3"): "아이비케이연금 2025.3Q 경영공시의 전년 동기 표 머리글이 '(24.2Q)' 로 인쇄돼 있다(오기). 2025.2Q 공시의 (24.2Q) 표와 값이 다르고(76,701 vs 74,345) "
                           "추이(71,791 → 74,345 → 76,701)와 BS 항목 20(77,106)에 맞아 2024.3Q 로 읽는다",
}
RESTATEMENT_REASON = {
    "KR0073": ("FY2025 분기보고서 주석 「재무제표 소급재작성 효과」({file}): 「당사는 보험계약마진 상각을 위한 시간가치 계산의 오류로 분기순이익 과소계상을 발견하여, "
               "비교표시된 과거 재무제표를 소급재작성하였습니다」(비교대상 전분기=제68기 {qtxt})"),
    "KR0079": ("FY2025 분기보고서 주석 39 「재무제표 소급재작성 효과」({file}): 「전기 중 유배당 확정연금 일부 상품의 현금흐름추정 로직 오류로 인한 보험계약부채 과대계상을 발견했고 "
               "보험금융손익의 체계적배분과 관련된 회계정책을 변경하였으며, 비교표시된 과거 재무제표를 소급재작성하였습니다. 전기 중간 보고기간의 요약 분ㆍ반기 재무제표 또한 재작성되었습니다」"),
}
# 2023.NQ DART cells the engine cannot close on its own -- each with its evidence (see the runlog)
LIC_OVERRIDES = {
    ("KR0001", "2023.3Q"): dict(kind="filing_anchor", why="IFRS17_BS item 20 (19,016,341.5 백만원) differs by +1.99 % from the filing's own 별도 재무상태표 (4-1) 보험계약부채 19,395,628.466; "
                                                         "the three separate roll-forward tables sum to 19,395,629 = the filing's own balance sheet"),
    ("KR0011", "2023.3Q"): dict(kind="filing_anchor", why="IFRS17_BS item 20 (27,493,912.8 백만원) differs by +0.16 % from the filing's own 별도 재무상태표 (4-1) 보험계약부채 27,538,062.951; "
                                                         "the three separate roll-forward tables sum to 27,538,063 = the filing's own balance sheet"),
    ("KR1000", "2023.1Q"): dict(kind="filing_anchor", why="IFRS17_BS item 20 (7,661,996 백만원) is the CONSOLIDATED 제61기말 figure printed in the same filing (연결 재무상태표 T76), not the "
                                                         "separate 2023.1Q balance sheet (4. 재무제표) 7,282,935.111 that the roll-forward table (7,282,935) closes with"),
    ("KR1000", "2023.2Q"): dict(kind="filing_anchor", why="IFRS17_BS item 20 (7,661,996 백만원) equals the CONSOLIDATED 제61기말 figure again (same value as 2023.1Q); the separate 2023.2Q "
                                                         "balance sheet (4. 재무제표) says 6,722,224.779 and the roll-forward table (6,722,225) closes with it"),
    ("KR0009", "2023.1Q"): dict(kind="filing_anchor", why="IFRS17_BS has no item 20 for 현대해상 2023.1Q; the separate 재무상태표 (4. 재무제표) 보험계약부채 is 27,896,092.964 and the three "
                                                         "separate roll-forward tables sum to 27,896,092.963"),
    ("KR0009", "2023.2Q"): dict(kind="filing_anchor", why="IFRS17_BS has no item 20 for 현대해상 2023.2Q; the separate 재무상태표 (4. 재무제표) 보험계약부채 is 27,450,838.515"),
    ("KR0002", "2023.1Q"): dict(kind="lrc_total_minus_lic", why="한화손해보험 일반보험 표(T670) 기말 행: 잔여보장 소계 304,975,191 천원 != 손실요소외 205,911,825 + 손실요소 7,918,018 = 213,829,843 "
                                                              "(발행사 표 내부 불일치, 차 91,145,348 천원). 합계열 513,610,168 = 소계 304,975,191 + 발생사고 소계 208,634,977 이고 세 표의 합계 합이 별도 재무상태표 "
                                                              "보험계약부채(12,559,733 백만원)와 0.01 % 안에서 닫힌다 → 합계·발생사고 열을 믿고 LRC = 합계 − LIC"),
    ("KR0003", "2023.1Q"): dict(kind="absent", why="롯데손해보험 2023.1Q 분기보고서(20230515002687.xml)의 「4. 재무제표」「5. 재무제표 주석」 절이 비어 있다(연결 절은 「해당 사항 없음」, 별도 절은 제목만 있고 "
                                                  "표가 0개 — 주석 표 자체가 DART 본문에 없다). 첨부 파일은 받지 않는 정책(루트 TODO #8)")
}

# --------------------------------------------------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------------------------------------------------
_orig_annotate = lic.annotate_tables


def swapped_annotate(tabs, repair=frozenset()):
    """lic.annotate_tables with current <-> prior swapped: the PRIOR-period tables of a 분기보고서 (the same quarter one year earlier) become 'cur'"""
    out = _orig_annotate(tabs, repair)
    for t in out:
        if t.get("rows_p"):
            rp = t["rows_p"]
            t["rows_p"] = {"cur": rp.get("prior", {}), "prior": rp.get("cur", {})}
            t["rows"] = rp.get("prior", {})
        else:
            hdr = t.get("hdr", "")
            if hdr.startswith("구분당기"):
                true = "cur"
            elif hdr.startswith("구분전기"):
                true = "prior"
                nl = t.get("nl", 1)
                t["roles"] = [lic.role_of(p.replace("전기", "")) if k >= nl else None for k, p in enumerate(t["paths"])]
                t["kind"] = "ME" if "CSM" in t["roles"] else "RF"
            else:
                true = t["period"]
            t["period"] = {"cur": "prior", "prior": "cur"}.get(true, true)
    return out


def harvest_files(fy, code):
    """[(rel path, harvested tables)], dir meta by rel path"""
    files, metas = [], {}
    for e in lic.inventory([fy], [code]):
        for f in e["files"]:
            if os.path.isfile(f):
                rel = f.split("/raw/", 1)[-1]
                files.append((rel, lic.harvest_file(f)))
                metas[rel] = e["meta"]
    return files, metas


def robust_bs_anchor(path):
    """별도 재무상태표 보험계약부채 (current period) of one DART xml; [{idx,title,unit,value_mm}].  Second anchor next to lic.filing_bs_anchor, which misses
    balance sheets whose header repeats the period text over two columns (the number sits in the second one)."""
    t = lic.read_xml(path)
    tops = [(m.start(), m.group(1).strip()) for m in lic.TITLE_RE.finditer(t)]
    out = []
    prev_small, prev_unit, last_end = "", None, 0
    for i, m in enumerate(lic.TAB_RE.finditer(t)):
        body = m.group(0)
        ntr = body.upper().count("<TR")
        pre = lic.clean(t[max(last_end, m.start() - 600): m.start()])[-200:]
        last_end = m.end()
        if ntr <= 6:
            small = lic.clean(body)
            prev_small, prev_unit = small[:200], lic.unit_of(small)
            continue
        flat = lic.comp(lic.clean(body))
        if not ("자산총계" in flat and "부채총계" in flat and "보험계약부채" in flat):
            prev_small, prev_unit = "", None
            continue
        title = lic.scope_at(tops, m.start())
        ct = lic.comp(title)
        if "연결" in ct or "요약" in ct or "주석" in ct or ("재무상태표" not in ct and "재무제표" not in ct):
            prev_small, prev_unit = "", None
            continue
        g, _ = lic.parse_table(body)
        skip = {k for k, c in enumerate(g[0]) if "주석" in c}
        unit = prev_unit or lic.unit_of(prev_small + " " + pre + " " + " ".join(" ".join(r) for r in g[:3]))
        for r in g:
            if lic._bs_label(lic.comp(r[0])) != "보험계약부채":
                continue
            val = None
            for k in range(1, len(r)):
                if k in skip or not r[k].strip():
                    continue
                v = lic.parse_num(r[k])
                if v is not None:
                    val = v
                    break
            if val is not None and unit in lic.UNIT_SCALE:
                out.append({"idx": i, "title": title[:30], "unit": unit, "value_mm": val * lic.UNIT_SCALE[unit]})
            break
        prev_small, prev_unit = "", None
    return out


def meta_for(rec, metas):
    m = metas.get(rec.get("file", ""), {})
    return {k: m.get(k) for k in ("rcept_no", "report_kind", "corp_code") if m.get(k)}


def assemble_one(code, fy, quarter, bs20_mm, filing_mm, swap=False):
    """one cell with the stage-1 engine (repair ladder included); swap=True reads the PRIOR-period tables"""
    files, metas = harvest_files(fy, code)
    if swap:
        lic.annotate_tables = swapped_annotate
    try:
        rec = lic.assemble_cell(code, fy, files, bs20_mm, filing_mm)
    finally:
        lic.annotate_tables = _orig_annotate
    rec["quarter"] = quarter
    rec["meta"] = meta_for(rec, metas)
    return rec, files, metas


def within(a, b, tol_abs, tol_rel):
    return abs(a - b) <= max(tol_abs, tol_rel * abs(b))


# --------------------------------------------------------------------------------------------------------------------
# items 1-8 (2024.NQ) from the 2025.NQ 경영공시
# --------------------------------------------------------------------------------------------------------------------
def read_cache(pdf_fy):
    p = HERE / f"t21_interim_{pdf_fy}.json"
    if not p.exists():
        raise SystemExit(f"missing cache {p.name}: run data/disclosure/_meta/ilp_round3_20261011/t21_read_interim_all.py {pdf_fy}")
    return json.loads(p.read_text(encoding="utf-8"))


def lrc_cell(code, q, cfg, M, cache):
    """{'status': loaded|absent|withheld, ...} for items 1-7 of (code, q).  M = master {(code, quarter): {item: value}}"""
    n, pdf_fy, pdf_q = cfg["n"], cfg["pdf_fy"], cfg["pdf_q"]
    if (code, q) in DOC_ABSENT:
        return {"status": "absent", "reason": DOC_ABSENT[(code, q)]}
    man = MANUAL.get((code, q))
    if man:
        items = {i + 1: float(v) for i, v in enumerate(man["run"])}
        return {"status": "loaded", "items": items, "src": "PDF_image", "file": man["file"], "page": man["page"], "label": man["label"], "run": man["run"],
                "run_kind": "full", "unit_in_source": "억원", "text_source": "image (rendered, read by eye)", "flags": ["manual_reading_image_pdf"],
                "evidence": man["evidence"], "table_year_src": "label"}
    rd = cache.get(code)
    if rd is None:
        return {"status": "absent", "reason": f"{pdf_q} 경영공시 PDF 가 수집돼 있지 않다(그 분기 공시 없음)"}
    if rd["status"] != "ok":
        return {"status": "absent", "reason": f"{pdf_q} 경영공시 PDF 텍스트 층에서 2-4 표를 찾지 못했다({rd['status']}); 렌더링 확인 대상 아님으로 분류되지 않은 셀"}
    tabs = [t for t in rd["tables"] if t["slots"]]
    if len(tabs) < 2:
        return {"status": "absent", "reason": f"{pdf_q} 경영공시 2-4 는 당분기 표 하나만 인쇄한다(전년 동기 표 없음; {len(rd['tables'])}개 합계 행 판독)"}
    div = rd["unit_div"] * UNIT_FIX.get((code, pdf_fy), 1.0)
    t1 = {int(k): round(v / div, 4) for k, v in tabs[0]["slots"].items()}
    t2 = {int(k): round(v / div, 4) for k, v in tabs[1]["slots"].items()}
    flags = []
    if (code, pdf_fy) in UNIT_FIX:
        flags.append(f"unit_fix_x{UNIT_FIX[(code, pdf_fy)]:g}")
    m25 = M.get((code, pdf_q), {})
    eq1 = bool(m25) and all(abs(t1[i] - m25.get(i, 1e9)) < 0.51 for i in range(1, 8))
    if not eq1:
        if (code, pdf_fy) in FIRST_TABLE_EXCEPTION:
            flags.append("first_table_exception")
        else:
            return {"status": "withheld", "reason": f"첫 표(당분기)가 마스터 {pdf_q} 와 다르다: 절 위치·읽기를 믿을 수 없어 전년 동기 표도 싣지 않는다",
                    "detail": {"t1": t1, "master": {i: m25.get(i) for i in range(1, 8)}, "t2": t2}}
    if tabs[0]["kind"] != tabs[1]["kind"]:
        return {"status": "withheld", "reason": f"두 표의 열 구성이 다르다({tabs[0]['kind']} vs {tabs[1]['kind']}): 열 배정을 믿을 수 없다", "detail": {"t1": t1, "t2": t2}}
    lab = tabs[1]
    if lab["label_year"] is not None and (lab["label_year"], lab["label_quarter"]) != (2024, n):
        if (code, pdf_fy) in LABEL_EXCEPTION:
            flags.append("label_typo_exception")
        else:
            return {"status": "withheld", "reason": f"전년 동기 표 머리글 {lab['label']} 이 2024.{n}Q 가 아니다", "detail": {"t2": t2}}
    v44 = M.get((code, "2024.4Q"), {})
    if v44 and all(abs(t2[i] - v44.get(i, 1e9)) < 0.51 for i in range(1, 8)):
        return {"status": "withheld", "reason": "전년 동기 표가 마스터 2024.4Q(2024.12.31) 와 7개 항목 모두 같다: 발행사가 연말 표를 그대로 옮긴 오기로 보고 싣지 않는다", "detail": {"t2": t2}}
    if all(abs(t2[i] - t1[i]) < 0.51 for i in range(1, 8)):
        return {"status": "withheld", "reason": "전년 동기 표가 당분기 표와 같다(사본)", "detail": {"t2": t2}}
    if lab["label"] is None:
        flags.append("table_order_only")
    return {"status": "loaded", "items": t2, "src": "PDF", "file": rd["pdf"], "page": lab["page"], "label": lab["label"], "run": lab["run"],
            "run_kind": lab["kind"], "unit_in_source": rd["unit"], "text_source": rd["source"], "flags": flags, "table_year_src": "label" if lab["label"] else "order",
            "t1_equals_master": eq1, "evidence": FIRST_TABLE_EXCEPTION.get((code, pdf_fy)) or LABEL_EXCEPTION.get((code, pdf_fy))}


# --------------------------------------------------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------------------------------------------------
def build_quarter(q, cfg, M, reg, bs20, csmw, report):
    code_list = sorted(c for c in reg if c not in REINS)
    fy = cfg["lic_fy"]
    recs = {r["code"]: r for r in lic.build_all(None, [fy], verbose=False)}
    red, yellow, info = [], [], []
    new_rows, prov_cells, prov_notloaded, lrc_prov, lrc_absent, restated_cells = [], [], [], [], [], []
    cache = read_cache(cfg["pdf_fy"]) if cfg["lrc"] else None
    table = []
    rmap_local = {}
    for code in code_list:
        rec = recs.get(code)
        ov = LIC_OVERRIDES.get((code, q))
        loaded_note = None
        # ---------------- LIC part: overrides ----------------
        if ov and ov["kind"] == "absent":
            prov_notloaded.append({"company_code": code, "quarter": q, "reason": ov["why"]})
            rec = None
        elif ov and ov["kind"] in ("filing_anchor", "lrc_total_minus_lic"):
            files, metas = harvest_files(fy, code)
            main_file = sorted(files, key=lambda x: lic.file_priority(x[0]))[0][0]
            anc = robust_bs_anchor(str(REPO / "data" / "dart" / fy / "raw" / main_file))
            anc_mm = anc[0]["value_mm"] if anc else None
            if ov["kind"] == "filing_anchor":
                rec2, _, _ = assemble_one(code, fy, q, None, anc_mm)
                if rec2["status"] != "loaded":
                    red.append(f"LIC {code} {q}: override filing_anchor did not close: {rec2['reason']}")
                    rec = None
                else:
                    rec2["flags"] = list(rec2["flags"]) + ["bs20_master_disagrees_with_filing_bs" if rec.get("bs20_mm") else "bs20_master_absent_filing_anchor_used"]
                    rec2["override"] = ov
                    rec2["bs20_master_mm"] = rec.get("bs20_mm")
                    rec2["robust_anchor"] = anc[0] if anc else None
                    rec = rec2
            else:       # lrc_total_minus_lic
                rec2, _, _ = assemble_one(code, fy, q, rec.get("bs20_mm"), None)
                it = rec2["items_mm"]
                lic_cols = it["bel"] + it["ra"] + it["single"]
                rec2["items_mm"] = dict(it, lic_total=lic_cols, lrc_total=it["total"] - lic_cols)
                tot_ok = lic._close(it["total"], rec2["bs20_mm"])
                if not tot_ok:
                    red.append(f"LIC {code} {q}: override lrc_total_minus_lic: total {it['total']:,.0f} does not close with BS20 {rec2['bs20_mm']:,.0f}")
                    rec = None
                else:
                    rec2.update(status="loaded", basis="liability", r_lic1="pass", reason=None, r_lic3_gap_mm=0.0)
                    rec2["flags"] = [f for f in rec2["flags"] if not f.startswith("table_total_vs_columns_gap")] + ["lrc_derived_total_minus_lic"]
                    rec2["override"] = ov
                    rec = rec2
        # ---------------- LRC part ----------------
        lrc = None
        if cfg["lrc"]:
            lrc = lrc_cell(code, q, cfg, M, cache)
        d = {}
        line = {"code": code, "lic": rec["status"] if rec else "-", "lrc": lrc["status"] if lrc else "-"}
        # reconciliation of items 1-8 against the DART of the same quarter
        restated = None
        if lrc and lrc["status"] == "loaded":
            items = {i: round(lrc["items"][i], 4) for i in range(1, 8)}
            items[8] = round(sum(items[i] for i in range(1, 8)), 4)
            lrc["items_final"] = items
            line["item8"] = items[8]
            csm = items[3] + items[6]
            cs = csmw.get((code, q))
            net = alt = i15 = None
            if rec and rec["status"] == "loaded":
                net = rec["net_lrc_mm"] / 100.0
                alt = rec["net_lrc_alt_mm"] / 100.0 if rec.get("net_lrc_alt_mm") is not None else None
                i15 = lic.eok(rec["items_mm"]["total"])
            if code in L.SIDECAR_COS and i15 is not None:
                ref, refname, tol = i15, "item15 (2-4 contains LIC)", max(5.0, 1e-4 * abs(i15))
            elif net is not None:
                ref, refname = net, "DART net LRC"
                if alt is not None and abs(items[8] - alt) < abs(items[8] - net):
                    ref, refname = alt, "DART net LRC (alt asset sign)"
                tol = max(L.TOL_ITEM8_ABS, L.TOL_ITEM8_REL * abs(ref))
            else:
                ref = None
            r2 = None
            if ref is not None:
                diff = items[8] - ref
                r2 = "pass" if abs(diff) <= tol else "DIFF"
                line.update(ref=round(ref, 1), diff=round(diff, 1), r2=r2)
            csm_flag = None
            if cs is not None:
                cdiff = csm - cs
                csm_flag = "ok" if abs(cdiff) <= max(2.0, 0.005 * abs(cs)) else "DIFF"
                line.update(csm=round(csm, 1), csm_wf=round(cs, 1), csm_diff=round(cdiff, 1), csm_flag=csm_flag)
                if cs and abs(cdiff) > 0.02 * abs(cs) and code not in L.SIDECAR_COS:
                    csm_flag = "RESTATED?"
            b = bs20.get((code, q))
            if b is not None and items[8] > b / 100.0 + max(5.0, 0.005 * items[8]):
                yellow.append(f"R3 {code} {q}: item 8 {items[8]:,.1f} > BS item 20 {b / 100.0:,.1f} (item 20 = LRC+LIC should be the larger)")
            trigger = (r2 == "DIFF" and code not in L.SIDECAR_COS) or csm_flag == "RESTATED?"
            if trigger and rec and rec["status"] == "loaded":
                restated = {"r2": r2, "csm": csm_flag}
            elif (r2 == "DIFF"):
                yellow.append(f"R-LIC2 {code} {q}: item 8 {items[8]:,.1f} vs {refname} {ref:,.2f} (diff {items[8] - ref:+,.1f}, tol {tol:,.1f})")
            if csm_flag == "DIFF" and not restated:
                yellow.append(f"CSM {code} {q}: items 3+6 {csm:,.1f} vs CSM_waterfall closing {cs:,.1f} (diff {csm - cs:+,.1f})")
        elif lrc:
            lrc_absent.append({"company_code": code, "quarter": q, "items": "1-8", "reason": lrc["reason"], **({"detail": lrc["detail"]} if lrc.get("detail") else {})})
            if lrc["status"] == "withheld":
                yellow.append(f"WITHHELD {code} {q}: {lrc['reason']}")
        # ---------------- restated: unify items 10-15 on the PDF's (latest) basis ----------------
        if restated:
            exp_total = rec["items_mm"]["total"] + (lrc["items_final"][8] - net) * 100.0
            rrec, _, _ = assemble_one(code, cfg["pdf_fy"], q, None, exp_total, swap=True)
            ok = rrec["status"] == "loaded"
            rn = rrec["net_lrc_mm"] / 100.0 if ok else None
            if ok and within(lrc["items_final"][8], rn, L.TOL_ITEM8_ABS, L.TOL_ITEM8_REL):
                orig = rec
                rrec["flags"] = list(rrec["flags"]) + ["restated_comparative_prior_period_tables"]
                rec = rrec
                reason = RESTATEMENT_REASON.get(code, "").format(file=rrec["file"].split("/")[-1], qtxt={1: "1분기", 2: "반기", 3: "3분기"}[cfg["n"]])
                rcell = {"code": code, "quarter": q, "orig": orig, "rec": rrec, "item8": lrc["items_final"][8], "item8_orig_net": net, "reason": reason,
                         "trigger": restated, "restated_net_lrc": rn, "exp_total_mm": exp_total}
                restated_cells.append(rcell)
                rmap_local[code] = rcell
                lrc["flags"] = list(lrc.get("flags", [])) + ["restated_comparative"]
                info.append(f"RESTATED {code} {q}: item 8 {lrc['items_final'][8]:,.1f} vs original DART net LRC {net:,.1f} ({restated}); restated DART net LRC {rn:,.2f}; "
                            f"items 10-15 taken from the {cfg['pdf_fy']} prior-period tables: original {lic.cell_item_values(orig)} -> restated {lic.cell_item_values(rrec)}")
                line["restated"] = True
                if not reason:
                    red.append(f"RESTATED {code} {q}: no restatement reason on file for this company")
            else:
                why = (f"restated read {rrec['status']}: {rrec.get('reason')}" if not ok else
                       f"restated DART net LRC {rn:,.2f} vs PDF item 8 {lrc['items_final'][8]:,.1f} outside tolerance")
                lrc_absent.append({"company_code": code, "quarter": q, "items": "1-8", "reason": f"재작성 의심(원 공시 대비 차) + 재작성 기준 DART 표로 확인 실패 → 보류: {why}",
                                   "detail": {"items_eok": {str(k): v for k, v in lrc["items_final"].items()}, "orig_net_lrc": round(net, 2), "trigger": restated}})
                yellow.append(f"WITHHELD {code} {q}: restated comparative could not be confirmed ({why})")
                lrc["status"] = "withheld"
                line["lrc"] = "withheld"
        # ---------------- rows ----------------
        if lrc and lrc["status"] == "loaded":
            for nn in range(1, 9):
                name, level = L.MODEL_ITEMS[nn]
                new_rows.append(L.row(reg, code, q, nn, name, L.SEC_MODEL, level, lrc["items_final"][nn]))
            lrc_prov.append(lrc_record(code, q, cfg, lrc, rmap_local.get(code), rec))
        if rec and rec["status"] == "loaded":
            lv = lic.cell_item_values(rec)
            for nn, v in lv.items():
                name, section, level = lic.ITEM_CATALOG[nn]
                new_rows.append({"원보험사코드": code, "원수사명": reg[code]["원수사명"], "티커": reg[code]["티커"], "생손보여부": reg[code]["생손보여부"],
                                 "항목번호": nn, "항목명": name, "섹션": section, "레벨": level, "공시분기": q, "값": v})
            gap_a = lv.get(11, 0.0) + lv.get(12, 0.0) + lv.get(13, 0.0) - lv[10]
            gap_b = lv[10] + lv[14] - lv[15]
            # engine tolerance is 3 백만원 = 0.03억: compare with a hair of slack so that 0.030 is not read as 0.0300000001
            if abs(gap_a) > 0.0301 or abs(gap_b) > 0.0301:
                red.append(f"R-LIC3 {code} {q}: gaps {gap_a:+.3f} / {gap_b:+.3f}")
            b = rec.get("bs20_mm")
            if b:
                line["r_lic1_ppm"] = round((lv[15] * 100.0 / b - 1) * 1e6, 1)
            line["item15"] = lv[15]
            line["class"] = rec["class"]
            line["basis"] = rec["basis"]
            prov_cells.append(rec)
        elif rec and rec["status"] != "loaded":
            prov_notloaded.append({"company_code": code, "quarter": q, "reason": rec["reason"]})
            red.append(f"LIC {code} {q}: not loaded ({rec['reason']})")
        table.append(line)
    new_rows.sort(key=lambda r: (r["원보험사코드"], r["공시분기"], r["항목번호"]))
    return dict(rows=new_rows, red=red, yellow=yellow, info=info, prov_cells=prov_cells, prov_notloaded=prov_notloaded, lrc_prov=lrc_prov,
                lrc_absent=lrc_absent, restated=restated_cells, table=table, recs=recs)


def lrc_record(code, q, cfg, lrc, rcell, rec):
    items = {str(k): v for k, v in lrc["items_final"].items()}
    r = {"company_code": code, "quarter": q, "item_block": "lrc_model_table_2-4_prior_year_quarter", "source_id": lrc["src"], "as_of_date": lic.as_of_date(q),
         "source_file": lrc["file"], "page": lrc["page"], "table": None, "table_label": lrc["label"], "table_year": 2024, "table_year_src": lrc.get("table_year_src"),
         "unit_in_source": lrc["unit_in_source"], "printed_run": lrc["run"], "run_kind": lrc["run_kind"], "text_source": lrc["text_source"], "items_eok": items,
         "item9": None, "item9_evidence": "no 2-5 section existed in the 2024 quarterly 경영공시; the 2025 2-5 text concerns 2025", "flags": lrc.get("flags", []),
         "evidence": lrc.get("evidence"), "published_in": f"{cfg['pdf_q']} 경영공시 2-4 (전년 동기 표)",
         "basis": BASIS_RESTATED if rcell else "latest_filing_comparative", "t1_equals_master_2025": lrc.get("t1_equals_master")}
    return r


def provenance_cell(rec, cfg_q, restated_info=None):
    """one 'cells' record via the engine's own emitter; restated cells get the basis markers of the 2023.4Q unify step"""
    p = lic.build_provenance([rec], datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"))["cells"][0]
    if rec.get("override"):
        p["override"] = {"kind": rec["override"]["kind"], "why": rec["override"]["why"]}
        if rec["override"]["kind"] == "filing_anchor":
            p["checks"]["bs20_master_eok"] = lic.eok(rec["bs20_master_mm"]) if rec.get("bs20_master_mm") else None
            p["checks"]["bs20_master_disagrees"] = bool(rec.get("bs20_master_mm"))
            p["checks"]["filing_bs_robust"] = rec.get("robust_anchor")
    return p


def apply_restated_to_prov(pcell, rcell):
    orig = rcell["orig"]
    pcell["original_basis"] = {"source_file": f"data/{orig['fy']}/raw/{orig['file']}", "basis": orig["basis"], "unit": orig["unit"], "items_eok": {str(n): v for n, v in lic.cell_item_values(orig).items()},
                               "net_lrc_eok": lic.eok(orig["net_lrc_mm"]), "bs20_eok": lic.eok(orig["bs20_mm"]) if orig.get("bs20_mm") else None}
    pcell["original_basis_value"] = pcell["original_basis"]["items_eok"]
    pcell["period_basis"] = BASIS_RESTATED
    pcell["basis_note"] = ("items 10-15 read from the PRIOR-period tables of the 2025 quarterly DART filing (the same quarter one year earlier, restated); original 2024 "
                           "values kept in original_basis_value; r_lic1 below is against the derived anchor (original total + PDF item-8 delta), not IFRS17_BS item 20")
    pcell["checks"]["r_lic1"] = "derived_anchor_restated"
    # the anchor of the restated read is derived (original total + PDF item-8 delta): say so, never present it as a balance-sheet figure
    pcell["checks"]["derived_anchor_eok"] = pcell["checks"].pop("filing_bs_eok", None)
    pcell["checks"]["ratio_derived_anchor"] = pcell["checks"].pop("ratio_filing_bs", None)
    pcell["checks"]["filing_bs_eok"] = None
    pcell["checks"]["ratio_filing_bs"] = None
    pcell["checks"]["restated_net_lrc_eok"] = round(rcell["restated_net_lrc"], 2)
    pcell["checks"]["item8_pdf_minus_restated_net_lrc"] = round(rcell["item8"] - rcell["restated_net_lrc"], 2)
    pcell["restatement_trigger"] = rcell["trigger"]


def print_summary(q, res):
    rows = res["table"]
    n_lic = sum(1 for x in rows if x["lic"] == "loaded")
    n_lrc = sum(1 for x in rows if x["lrc"] == "loaded")
    print(f"\n=== {q}: LIC cells loaded {n_lic}; LRC (1-8) cells loaded {n_lrc}; rows to add {len(res['rows'])}; restated {len(res['restated'])} ===")
    for x in rows:
        if x["lic"] == "-" and x["lrc"] in ("-", "absent"):
            continue
        extra = "  ".join(f"{k}={v}" for k, v in x.items() if k not in ("code", "lic", "lrc"))
        print(f"  {x['code']} lic={x['lic']:10s} lrc={x['lrc']:9s} {extra}")
    print(f"RED {len(res['red'])}  YELLOW {len(res['yellow'])}  INFO {len(res['info'])}")
    for s in res["red"]:
        print("  RED   ", s)
    for s in res["yellow"]:
        print("  YELLOW", s)
    for s in res["info"]:
        print("  INFO  ", s)
    print("not loaded (LIC, documented):", [(c["company_code"], c["reason"][:60]) for c in res["prov_notloaded"]])
    print("LRC absent/withheld:", len(res["lrc_absent"]), "->", sorted(c["company_code"] for c in res["lrc_absent"]))


def append_provenance_and_sidecar(res, q, cfg, tag, backup_dir):
    raw0 = L.PROV.read_bytes()
    txt = raw0.decode("utf-8")
    prov = json.loads(txt)
    if json.dumps(prov, ensure_ascii=False, indent=1) + "\n" != txt:
        raise SystemExit("abort: provenance file does not round-trip byte for byte")
    have = {(c["company_code"], c["quarter"]) for c in prov["cells"]}
    cells = []
    rmap = {(r["code"], r["quarter"]): r for r in res["restated"]}
    for rec in res["prov_cells"]:
        pc = provenance_cell(rec, q)
        if (rec["code"], q) in rmap:
            apply_restated_to_prov(pc, rmap[(rec["code"], q)])
        cells.append(pc)
    clash = [(c["company_code"], c["quarter"]) for c in cells if (c["company_code"], c["quarter"]) in have]
    if clash:
        raise SystemExit(f"abort: provenance cells already exist: {clash[:3]}")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    backup = backup_dir / f"ilp_provenance_backup_{stamp}_{tag}.json"
    k = 2
    while backup.exists():
        backup = backup_dir / f"ilp_provenance_backup_{stamp}_{tag}_{k}.json"
        k += 1
    shutil.copyfile(L.PROV, backup)
    prov["cells"] = prov["cells"] + cells
    prov["not_loaded"] = prov.get("not_loaded", []) + res["prov_notloaded"]
    prov["lrc_model_cells"] = prov.get("lrc_model_cells", []) + res["lrc_prov"]
    prov["lrc_model_not_loaded"] = prov.get("lrc_model_not_loaded", []) + res["lrc_absent"]
    prov["backfills"] = prov.get("backfills", []) + [{
        "stage": q, "at": datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ"), "emitted_by": "scripts/load_ilp_interim_2023_2024.py", "ticket": TICKET,
        "note": ("items 10-15 from the DART quarterly roll-forward of the quarter itself (stage-1 engine; restated cells from the PRIOR-period tables of the 2025 filing); "
                 + ("items 1-8 from the prior-year table of the 2025 quarterly 경영공시 2-4 (image PDFs read by eye)" if cfg["lrc"] else "items 1-8: no source exists for 2023 interim quarters"))}]
    out = json.dumps(prov, ensure_ascii=False, indent=1) + "\n"
    tmp = L.PROV.with_name(L.PROV.name + ".tmp")
    tmp.write_bytes(out.encode("utf-8"))
    os.replace(tmp, L.PROV)
    # restated sidecar (additive cells; the three 2023.4Q cells stay byte-identical)
    sb = None
    if res["restated"]:
        stxt = SIDECAR_RESTATED.read_text(encoding="utf-8")
        side = json.loads(stxt)
        if json.dumps(side, ensure_ascii=False, indent=1) + "\n" != stxt:
            raise SystemExit("abort: restated sidecar does not round-trip")
        sb = backup_dir / f"ilp_restated_comparative_backup_{stamp}_{tag}.json"
        shutil.copyfile(SIDECAR_RESTATED, sb)
        for r in res["restated"]:
            rec, orig = r["rec"], r["orig"]
            new = lic.cell_item_values(rec)
            old = lic.cell_item_values(orig)
            side["cells"].append({
                "company_code": r["code"], "quarter": r["quarter"], "basis": BASIS_RESTATED, "restatement_reason": r["reason"],
                "item8_restated": r["item8"], "item8_minus_original_net_lrc": round(r["item8"] - r["item8_orig_net"], 2),
                "restated_bs_insurance_contract_liability_eok": new[15],
                "restated_bs_source": "derived: closing total (item 15) of the restated PRIOR-period roll-forward tables of the 2025 quarterly DART filing; the 2025 interim filing carries no prior-year-quarter balance sheet",
                "bs_item20_fy2023_original_eok": round((orig["bs20_mm"] or orig["items_mm"]["total"]) / 100.0, 2),
                "bs_item20_original_eok": round((orig["bs20_mm"] or orig["items_mm"]["total"]) / 100.0, 2),
                "bs_source_file": f"data/{rec['fy']}/raw/{rec['file']}",
                "items_10_15_restated": {str(n): v for n, v in new.items()},
                "items_10_15_original": {str(n): v for n, v in old.items()},
            })
        side["extended_at"] = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
        side["extended_by"] = side.get("extended_by", []) + ["scripts/load_ilp_interim_2023_2024.py"]
        SIDECAR_RESTATED.write_text(json.dumps(side, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return backup, sb


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--quarters", nargs="+", required=True, choices=sorted(CFG))
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--report", help="json report of the (single) quarter")
    args = ap.parse_args(argv)
    ilp = L.load(L.ILP)
    reg = lic.ilp_registry(ilp)
    M = {}
    for r in ilp:
        M.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]
    bs20 = lic.load_bs20()
    csmw = {(r["원보험사코드"], r["공시분기"]): r["값"] for r in L.load(L.CSMW) if r["항목번호"] == 6}
    for q in args.quarters:
        cfg = CFG[q]
        res = build_quarter(q, cfg, M, reg, bs20, csmw, None)
        print_summary(q, res)
        if args.report:
            with open(args.report, "w", encoding="utf-8") as f:
                json.dump({"quarter": q, "table": res["table"], "red": res["red"], "yellow": res["yellow"], "info": res["info"], "lrc_absent": res["lrc_absent"],
                           "lrc_prov": res["lrc_prov"], "n_rows": len(res["rows"]), "not_loaded": res["prov_notloaded"],
                           "restated": [{k: v for k, v in r.items() if k not in ("orig", "rec")} for r in res["restated"]]}, f, ensure_ascii=False, indent=1, default=str)
        if res["red"]:
            print("RED present: nothing written")
            return 1
        if not args.write:
            print("dry run: nothing written (use --write)")
            continue
        tag = "pre_interim_" + q.replace(".", "")
        backup = lic.merge_into_ilp(res["rows"], tag=tag)
        pb, sb = append_provenance_and_sidecar(res, q, cfg, tag, lic.BACKUP_DIR)
        print(f"appended {len(res['rows'])} rows; backup {backup.name}; provenance backup {pb.name}" + (f"; sidecar backup {sb.name}" if sb else ""))
        # keep the in-memory master current for the next quarter of this run
        for r in res["rows"]:
            M.setdefault((r["원보험사코드"], r["공시분기"]), {})[r["항목번호"]] = r["값"]
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
