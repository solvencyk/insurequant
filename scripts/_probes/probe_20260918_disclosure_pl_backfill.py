# -*- coding: utf-8 -*-
"""정기경영공시 §2-1 요약 포괄손익계산서 -> PL_breakdown 백필 타당성 프로브 (2026-09-18, orchestrator).

목적: DART 분기보고서를 내지 않는 16개 비상장사의 비-4Q 분기 PL 결손(172칸)을
      경영공시 PDF 로 채울 수 있는지 **실측**한다. 생산용 추출기가 아니라 프로브다.

주의(중요): data/disclosure/*/parsed/*.md 는 `parse_scope: keyword_window` 라
      K-ICS 키워드 페이지만 docling 변환돼 있어 §2-1 이 통째로 빠져 있다.
      가용성은 **raw PDF** 로 재야 한다(MD 로 재면 전부 '없음'으로 오판).

산출: data/_derived/_probe_20260918_disclosure_pl.json
실행: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260918_disclosure_pl_backfill.py
"""
import fitz, re, os, io, sys, glob, json, collections

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
fitz.TOOLS.mupdf_display_errors(False)

LABELS = [
    ("보험손익", "보험손익"),
    ("(보험수익)", "보험수익"),
    ("(보험서비스비용)", "보험서비스비용"),
    ("(재보험수익)", "재보험수익"),
    ("(재보험서비스비용)", "재보험서비스비용"),
    ("(기타사업비용)", "기타사업비용"),
    ("투자손익", "투자손익"),
    ("(투자수익)", "투자수익"),
    ("(투자비용)", "투자비용"),
    ("영업이익", "영업이익"),
    ("영업외손익", "영업외손익"),
    ("(영업외수익)", "영업외수익"),
    ("(영업외비용)", "영업외비용"),
    ("법인세비용차감전순이익", "세전이익"),
    ("법인세비용", "법인세비용"),
    ("당기순이익", "당기순이익"),
]
NUM = re.compile(r"^\(?-?[\d,]+\)?$|^[△▲-]\s?[\d,]+$")


def norm_num(s):
    s = s.strip().replace(" ", "")
    neg = False
    if s[:1] in ("△", "▲"):
        neg, s = True, s[1:]
    if s.startswith("(") and s.endswith(")"):
        neg, s = True, s[1:-1]
    if s.startswith("-") and len(s) > 1:
        neg, s = True, s[1:]
    s = s.replace(",", "")
    if not s.isdigit():
        return None
    return -int(s) if neg else int(s)


def extract(txt):
    """페이지 텍스트에서 §2-1 표를 읽는다. 값은 [해당분기, 전년동기, 증감] 순."""
    lines = [l.strip() for l in txt.split("\n") if l.strip()]
    out, i = {}, 0
    while i < len(lines):
        ln = lines[i]
        key = None
        for lab, name in LABELS:
            if ln == lab or ln.replace(" ", "") == lab or ln.startswith(lab + "("):
                key = name
                break
        if key is None and ln.startswith("법인세비용차감전순이익"):
            key = "세전이익"
        if key and key not in out:
            nums, j = [], i + 1
            while j < len(lines) and len(nums) < 3:
                cand = lines[j].replace(" ", "")
                if NUM.match(cand):
                    v = norm_num(cand)
                    if v is not None:
                        nums.append(v)
                    j += 1
                elif cand.startswith("(또는") or cand in ("-", "―"):
                    j += 1
                else:
                    break
            if nums:
                out[key] = nums
        i += 1
    return out


def probe(pdf, max_pages=25):
    """PDF 앞부분에서 §2-1 표를 찾는다. {page_no: {항목: [3값]}}"""
    doc = fitz.open(pdf)
    res = {}
    for i in range(min(max_pages, doc.page_count)):
        t = doc[i].get_text()
        if "포괄손익계산서" in t and "보험손익" in t:
            d = extract(t)
            if "보험손익" in d:
                res[i + 1] = d
    doc.close()
    return res


MISSING = ["KR0004", "KR0029", "KR0049", "KR0050", "KR0051", "KR0074", "KR0075", "KR0076",
           "KR0080", "KR0095", "KR0097", "KR0100", "KR0150", "KR1010", "KR1011", "KR1098"]


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    periods = [(f"FY{fy}_Q{q}", f"{fy}.{q}Q")
               for fy in range(2023, 2027) for q in range(1, 5)
               if not (fy == 2026 and q > 2)]
    result = []
    for folder, q in periods:
        rawdir = os.path.join(ROOT, "data", "disclosure", folder, "raw")
        for code in MISSING:
            pdfs = sorted(glob.glob(os.path.join(rawdir, code + "_*.pdf")))
            if not pdfs:
                result.append({"code": code, "quarter": q, "status": "NO_PDF"})
                continue
            try:
                res = probe(pdfs[0])
            except Exception as e:
                result.append({"code": code, "quarter": q, "status": "ERROR",
                               "detail": str(e)[:120]})
                continue
            if not res:
                result.append({"code": code, "quarter": q, "status": "TABLE_NOT_FOUND",
                               "source_file": os.path.relpath(pdfs[0], ROOT).replace("\\", "/")})
                continue
            page, d = sorted(res.items())[0]
            result.append({"code": code, "quarter": q, "status": "OK",
                           "source_file": os.path.relpath(pdfs[0], ROOT).replace("\\", "/"),
                           "page": page, "n_fields": len(d),
                           "values_eok": {k: v[0] for k, v in d.items()}})
    outp = os.path.join(ROOT, "data", "_derived", "_probe_20260918_disclosure_pl.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump({"note": "경영공시 §2-1 요약 포괄손익계산서. 단위 억원, 해당분기 열=누계(YTD).",
                   "cells": result}, f, ensure_ascii=False, indent=1)
    c = collections.Counter(r["status"] for r in result)
    print("status:", dict(c))
    print("wrote:", outp)


if __name__ == "__main__":
    main()
