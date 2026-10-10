# -*- coding: utf-8 -*-
"""
P1 (ticket 20261010T1330Z ilp_ibk_fix_dups_and_kr0004_pl_holes): KR1011 IBK연금보험
insurance_liability_portfolio.json items 1-8, 2025.1Q .. 2026.2Q (6 quarters x 8 items = 48 cells).

Finding (runlog data/disclosure/_meta/lic_load_runlog_stage1.md section 10, re-verified 2026-10-10 against the
six 경영공시 PDFs, every 합계 row rendered at 120 dpi and read off the image, text layer cross-checked):
the master had items 1-6 = 0 and item 7 (보험료배분접근법) = item 8 = the FIRST number of the 합계 row (일반모형
최선추정부채, rounded to a whole 억원) -- i.e. a single column of the 2-4 합계 row had been read as the PAA
total.  The real 합계 row is 일반모형 BEL/RA/CSM + 변동수수료접근법 BEL/RA/CSM, PAA blank ('-').
Independent anchors: the 2026.1Q/2026.2Q filings print the 2025.1Q/2025.2Q rows again as "전년 동기" and they are
identical to the values below; the corrected 2025.4Q item 8 = 78,938.6 vs the DART 잔여보장요소(부채 기준) 78,938.7.

Cell-level fix with an OLD-VALUE GUARD (a cell is changed only if it still holds the value found on 2026-10-10;
any other value aborts without writing).  Backup first, byte-exact round trip required, the file is rewritten in its
own format (CRLF, indent 2), every other row is left untouched.  Before writing, the PLAN is re-read from the PDFs
(`verify_against_pdf`): a mismatch aborts.

Usage:  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/fix_20261010_ilp_kr1011_ibk_total_row.py [--write]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ILP = REPO / "insurance_liability_portfolio.json"
BACKUP = REPO / "data" / "_derived" / "ilp_backup_20261010_pre_ibk.json"

CODE = "KR1011"
# quarter -> (FY dir, 1-based PDF page of the 2-4 table, [item1..item7 new], item8 new)   all 억원, as printed in the PDF
PDF_PAGES = {
    "2025.1Q": ("FY2025_Q1", 7),
    "2025.2Q": ("FY2025_Q2", 8),
    "2025.3Q": ("FY2025_Q3", 7),
    "2025.4Q": ("FY2025_Q4", 21),
    "2026.1Q": ("FY2026_Q1", 7),
    "2026.2Q": ("FY2026_Q2", 8),
}
NEW = {
    #            1 일반BEL  2 일반RA  3 일반CSM  4 VFA BEL  5 VFA RA  6 VFA CSM  7 PAA   8 합계
    "2025.1Q": (74076.5, 376.8, 4631.1, 353.6, 16.2, 159.8, 0.0, 79614.0),
    "2025.2Q": (74441.8, 445.2, 4840.3, 376.7, 21.4, 235.5, 0.0, 80360.9),
    "2025.3Q": (74392.7, 453.0, 5082.1, 410.1, 25.1, 305.3, 0.0, 80668.3),
    "2025.4Q": (72887.3, 480.8, 4694.9, 319.1, 47.7, 508.8, 0.0, 78938.6),
    "2026.1Q": (71016.1, 511.7, 4802.5, 262.4, 76.1, 687.2, 0.0, 77356.0),
    "2026.2Q": (69412.6, 565.7, 5039.0, 439.1, 116.7, 887.5, 0.0, 76460.6),
}
# values found in the master on 2026-10-10: items 1-6 = 0.0; item 7 = item 8 = the first number of the 합계 row, rounded
OLD_ITEM78 = {"2025.1Q": 74076.0, "2025.2Q": 74441.0, "2025.3Q": 74392.0, "2025.4Q": 72887.0, "2026.1Q": 71016.0, "2026.2Q": 69412.0}


def _num(tok: str):
    t = tok.replace("\u3000", "").replace(" ", "").strip()
    if t in ("", "-"):
        return None
    return float(t.replace(",", ""))


def pdf_rows(pdf: Path, page_no: int):
    """First (= 해당 분기) 2-4 table of the page: ([row1 nums], [row2 nums], [row3 nums], [합계 nums], n_dash_after_total)."""
    import fitz  # PyMuPDF

    doc = fitz.open(pdf)
    try:
        lines = [ln for ln in doc[page_no - 1].get_text("text").split("\n")]
    finally:
        doc.close()
    if not any("회계모형별" in ln or "보험부채 현황" in ln for ln in lines):
        raise SystemExit(f"abort: {pdf.name} p{page_no} does not look like the 2-4 page")
    names = ["유배당연금∙저축", "무배당연금∙저축", "변액연금∙저축"]
    out = {}
    i0 = None
    for i, ln in enumerate(lines):
        if ln.strip() == names[0]:
            i0 = i
            break
    if i0 is None:
        raise SystemExit(f"abort: {pdf.name} p{page_no}: first portfolio row not found")
    cur = None
    for ln in lines[i0:]:
        s = ln.strip()
        if s in names and s not in out:
            cur = s
            out[cur] = []
            continue
        if s == "합계":
            cur = "합계"
            out[cur] = []
            continue
        if s.startswith("주)"):
            break
        if cur is not None and s not in ("", "Direct", "-Par", "Indirect", "생명"):
            out[cur].append(s)
    res = []
    for key in names + ["합계"]:
        toks = out.get(key)
        if toks is None:
            raise SystemExit(f"abort: {pdf.name} p{page_no}: row {key} not found")
        nums = [n for n in (_num(t) for t in toks) if n is not None]
        res.append(nums)
    return res


def verify_against_pdf(verbose: bool = True) -> None:
    for q, (fy, page) in PDF_PAGES.items():
        pdf = REPO / "data" / "disclosure" / fy / "raw" / "KR1011_IBK연금보험.pdf"
        r1, r2, r3, tot = pdf_rows(pdf, page)
        if len(r1) != 3 or len(r2) != 3 or len(r3) != 3 or len(tot) != 6:
            raise SystemExit(f"abort: {q} PDF row shape r1={r1} r2={r2} r3={r3} total={tot}")
        # sub rows add up to the 합계 row (일반모형 = 유배당 + 무배당, 변동수수료접근법 = 변액)
        gen = [round(a + b, 1) for a, b in zip(r1, r2)]
        for a, b in zip(gen + r3, tot):
            if abs(a - b) > 0.051:
                raise SystemExit(f"abort: {q} PDF sub rows do not add up to 합계: {gen + r3} vs {tot}")
        plan = NEW[q]
        if any(abs(a - b) > 1e-9 for a, b in zip(tot, plan[:6])):
            raise SystemExit(f"abort: {q} PLAN {plan[:6]} differs from the PDF 합계 row {tot}")
        if verbose:
            print(f"  PDF check {q} {pdf.name} p{page}: 합계 {tot}  (sub rows add up) == PLAN items 1-6")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    print("re-reading the six PDFs:")
    verify_against_pdf()

    raw0 = ILP.read_bytes()
    txt = raw0.decode("utf-8")
    crlf = "\r\n" in txt
    rows = json.loads(txt)
    dump = lambda r: (json.dumps(r, indent=2, ensure_ascii=False).replace("\n", "\r\n") if crlf else json.dumps(r, indent=2, ensure_ascii=False))
    if dump(rows) != txt:
        raise SystemExit("abort: file does not round-trip byte-for-byte")
    idx = {}
    for i, r in enumerate(rows):
        if r["원보험사코드"] == CODE and 1 <= r["항목번호"] <= 8:
            k = (r["공시분기"], r["항목번호"])
            if k in idx:
                raise SystemExit(f"abort: duplicate key {CODE} {k}")
            idx[k] = i

    plan = []  # ((quarter, item), old, new)
    for q, vals in NEW.items():
        s7 = round(sum(vals[:7]), 1)
        if abs(s7 - vals[7]) > 1e-6:
            raise SystemExit(f"abort: PLAN identity {q}: sum(1..7)={s7} != item 8 {vals[7]}")
        for item in range(1, 9):
            key = (q, item)
            if key not in idx:
                raise SystemExit(f"abort: {CODE} {key} not found in the master")
            cur = float(rows[idx[key]]["값"])
            new = vals[item - 1]
            old = OLD_ITEM78[q] if item in (7, 8) else 0.0
            if cur == new and old != new:
                print(f"already fixed: {CODE} {key} = {cur}")
                continue
            if cur != old:
                raise SystemExit(f"abort (old-value guard): {CODE} {key} holds {cur}, expected {old}")
            plan.append((key, old, new))

    print(f"{len(plan)} cell(s) to change:")
    for (q, n), old, new in plan:
        print(f"  {CODE} {q} item {n}: {old} -> {new}")
    if not args.write or not plan:
        print("dry run" if not args.write else "nothing to do")
        return 0
    if BACKUP.exists():
        raise SystemExit(f"abort: backup {BACKUP.name} already exists")
    shutil.copyfile(ILP, BACKUP)
    if hashlib.sha256(BACKUP.read_bytes()).hexdigest() != hashlib.sha256(raw0).hexdigest():
        raise SystemExit("abort: backup mismatch")
    new_rows = json.loads(txt)
    for (q, n), old, new in plan:
        new_rows[idx[(q, n)]]["값"] = new
    if ILP.read_bytes() != raw0:
        raise SystemExit("abort: file changed while preparing the fix")
    tmp = ILP.with_name(ILP.name + ".tmp")
    tmp.write_bytes(dump(new_rows).encode("utf-8"))
    os.replace(tmp, ILP)
    after = json.loads(ILP.read_text(encoding="utf-8"))
    changed = [i for i, (a, b) in enumerate(zip(rows, after)) if a != b]
    assert len(after) == len(rows) and len(changed) == len(plan), (len(changed), len(plan))
    # identity item 8 == sum(items 1..7) on the written file
    for q in NEW:
        v = {n: after[idx[(q, n)]]["값"] for n in range(1, 9)}
        assert abs(sum(v[n] for n in range(1, 8)) - v[8]) < 1e-6, (q, v)
    print(f"wrote {ILP.name}; backup {BACKUP.name}; {len(changed)} rows changed, all others identical; item8 == sum(items1..7) in all 6 quarters")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
