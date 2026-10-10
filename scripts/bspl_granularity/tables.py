# -*- coding: utf-8 -*-
"""Locate and extract the statement-type tables of a management-disclosure PDF (Stage A).

Table kinds
  sum_bs   요약 재무상태표(총괄)            (2-2 / 4-1 / 4-2 ...; supervisory 업무보고서 basis, IFRS17/9)
  equity   B/S상 자기자본                    (4-1 / 5-1 ...: 자본금 이익잉여금 기타포괄손익누계액 ...)
  bs_full  재무상태표 (8-1)                  (supervisory 8-1 in 억원/천원, or K-IFRS style statement in won; may span pages)
  sum_pl   요약 포괄손익계산서(총괄)
  pl_full  포괄손익계산서 (8-2)

The 건전성감독기준 (K-ICS) balance sheet is deliberately NOT extracted: it is a different valuation basis.
Values are returned raw (unit not applied) together with the printed unit caption; the unit and the
current-period column are verified downstream against the master's own totals.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import fitz

from .pdfrows import rows_from_page

BR = "【】[]〔〕"

_PREFIX_RE = re.compile(
    r"^(?:(?:[0-9]{1,2}(?:-[0-9]{1,2})?|[IVXLCivxlc]{1,4}|[Ⅰ-Ⅻ]{1,2}|[가-하])[.)]\s*)+")
_FOOT_RE = re.compile(r"(?:\(?주석?[\d,]+\)?|<주석?[\d,]+>)+$")


def comp(s: str) -> str:
    return "".join((s or "").split())


def norm_label(s: str) -> str:
    """Canonical label: no whitespace, no bracket marks, no leading numbering, no trailing footnote marks."""
    t = comp(s)
    for ch in BR:
        t = t.replace(ch, "")
    t = re.sub(r"^(자본)(?=자본총계)", "", t)
    t = _PREFIX_RE.sub("", t)
    t = _FOOT_RE.sub("", t)
    if t.startswith("(") and t.endswith(")") and t.count("(") == 1:
        t = t[1:-1]
    return t


def clean_row_label(label_raw: str) -> str:
    return norm_label(label_raw)


_UNIT_RE = re.compile(r"단위\s*[:：]?\s*([가-힣A-Za-z]+)")


def _unit_from_text(lines):
    for t in lines:
        m = _UNIT_RE.search(t)
        if m:
            return m.group(1)
    return None


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _rows_to_dict(rows, page):
    out = []
    for r in rows:
        lab = clean_row_label(r.label_raw)
        if not lab:
            continue
        out.append({"label": lab, "raw": r.label_raw, "vals": r.vals, "dash": r.dash, "xs": [round(x, 1) for x in r.xs],
                    "y": round(r.y, 1), "page": page})
    return out


def _title_lines(free, first_row_y):
    """free-text lines located above the first numeric row (header / title / unit caption)"""
    return [t for (y, x0, t) in sorted(free) if y < first_row_y]


def _basis(c: str):
    """'별도' / '연결' / None from a page's compact text (first marker wins)."""
    pos = {}
    for key, name in (("①별도", "별도"), ("별도재무상태표", "별도"), ("재무상태표별도", "별도"), ("(별도)", "별도"), ("별도손익", "별도"),
                      ("②연결", "연결"), ("연결재무상태표", "연결"), ("재무상태표연결", "연결"), ("(연결)", "연결"), ("연결손익", "연결")):
        k = c.find(key)
        if k >= 0 and (name not in pos or k < pos[name]):
            pos[name] = k
    if not pos:
        return None
    return min(pos, key=lambda n: pos[n])


def classify_pages(doc):
    """page index -> (set of kinds, compact text)  (screening by compact text)."""
    out = {}
    for i in range(len(doc)):
        txt = doc[i].get_text()
        c = comp(txt)
        kinds = set()
        kics = "건전성감독기준" in c
        is_sum = "요약재무상태표" in c
        if kics and is_sum:
            kinds.add("kics_bs")      # excluded on purpose
        elif is_sum and "자산총계" in c:
            kinds.add("sum_bs")
        if "자기자본" in c and "자본금" in c and ("이익잉여금" in c or "결손금" in c) and "기타포괄손익누계액" in c:
            kinds.add("equity")
        if "재무상태표" in c and not is_sum and not kics:
            has_tot = all(x in c for x in ("자산총계", "부채총계", "자본총계"))
            pointer = ("첨부" in c and "참조" in c)          # table-of-contents / "see attached statements" pages
            # an audited statement may put the equity section on the next page: header with the period-end sentence
            # ('제 20 (당)기말 2023년 12월 31일 현재') plus the asset total is enough to start it
            audited_head = ("자산총계" in c and "현재" in c
                            and any(k in c for k in ("(당)기말", "당기말", "(당)분기말", "당분기말", "(당)반기말", "당반기말")))
            if has_tot or audited_head or (("8-1." in c or "8-1)" in c) and not pointer):
                kinds.add("bs_full_start")
        if ("요약포괄손익계산서" in c or "요약손익계산서" in c) and "보험손익" in c:
            kinds.add("sum_pl")
        if ("손익계산서" in c and "요약" not in c and "건전성" not in c
                and (("8-2." in c or "8-2)" in c) or ("보험수익" in c and ("당기순이익" in c or "당기순손실" in c)))):
            kinds.add("pl_full_start")
        if kinds:
            out[i] = (kinds, c)
    return out


def extract_pdf(pdf_path: Path) -> dict:
    doc = fitz.open(pdf_path)
    try:
        cls = classify_pages(doc)
        res = {"pdf": str(pdf_path), "sha256": _sha(pdf_path), "pages": len(doc), "tables": []}
        res["text_chars_first5"] = sum(len(doc[i].get_text()) for i in range(min(5, len(doc))))
        done_full: dict = {"bs_full": set(), "pl_full": set()}      # per kind: a PL window must not swallow the BS start
        for i, (kinds, c) in sorted(cls.items()):
            page = doc[i]
            for kind in sorted(kinds):
                if kind == "kics_bs":
                    continue
                if kind in ("bs_full_start", "pl_full_start"):
                    fk = "bs_full" if kind == "bs_full_start" else "pl_full"
                    if i in done_full[fk]:
                        continue
                    t = _extract_multipage(doc, i, fk, c)
                    if t:
                        res["tables"].append(t)
                        done_full[fk].update(range(i, i + t["npages"]))
                    continue
                # the table may start at the bottom of this page and continue on the next one, and a page may stack
                # several tables: keep the rows of this page and the next one; views slice the block they need.
                rows, free = rows_from_page(page, pageno=i + 1)
                d = _rows_to_dict(rows, i + 1)
                free_all = [t for (_, _, t) in sorted(free)]
                npages = 1
                if i + 1 < len(doc):
                    rows2, free2 = rows_from_page(doc[i + 1], pageno=i + 2)
                    d += _rows_to_dict(rows2, i + 2)
                    free_all += [t for (_, _, t) in sorted(free2)]
                    npages = 2
                if not d:
                    continue
                titles = _title_lines(free, rows[0].y) if rows else free_all[:6]
                res["tables"].append({"kind": kind, "page": i + 1, "npages": npages,
                                      "unit": _unit_from_text(titles) or _unit_from_text(free_all),
                                      "titles": titles[-8:], "rows": d})
        return res
    finally:
        doc.close()


def _extract_multipage(doc, i0: int, kind: str, c0: str, max_pages: int = 14) -> dict | None:
    """8-1 / 8-2 style statements can run over 2-3 pages; accumulate rows until the closing total is seen."""
    rows_all: list = []
    titles_all: list = []
    unit = None
    npages = 0
    for j in range(i0, min(len(doc), i0 + max_pages)):
        page = doc[j]
        rows, free = rows_from_page(page, pageno=j + 1)
        npages += 1
        titles_all += [t for (_, _, t) in sorted(free)]
        if unit is None:
            unit = _unit_from_text(titles_all)
        d = _rows_to_dict(rows, j + 1)
        rows_all += d
        labs = [r["label"] for r in d]
        if kind == "bs_full" and any(("부채와자본총계" in l or "부채및자본총계" in l or "자본및부채총계" in l
                                      or "자본과부채총계" in l) for l in labs):
            break
        if kind == "pl_full" and any(l.startswith(("당기순이익", "당기순손실", "반기순이익", "분기순이익", "당반기순이익")) for l in labs):
            break
    if not rows_all:
        return None
    return {"kind": kind, "page": i0 + 1, "npages": npages, "unit": unit, "basis": _basis(c0),
            "titles": titles_all[:12], "rows": rows_all}
