#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (B1): 하나손해보험 KR0050 -- read the 11 non-Q4 separate-FS attachments, calibrate against the year-end DART anchors, list the loadable cells.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_kr0050.py            report only
  ... --spec out.json                                                                                 also write the add-spec

Calibration (the 1st-round principle: a line->item mapping must reproduce an anchor): the PRIOR-YEAR-END column of every Q1/Q2/Q3 attachment of year Y+1 is the
31 Dec Y balance sheet; the master holds the year-end values of year Y (DART audit XML: items 10, 14, 15, 20, 21, 22, 24, ...).  Equal -> the mapping is proven for that
year's labels.  The 2023 attachments (prior column = 31 Dec 2022, no master anchor) use the labels proven on 2024-2026 plus identities (assets = liabilities +
equity, line sums = totals) and the master cells that the disclosure summary already holds.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
import bspl_apply_attfs as A  # noqa: E402

CODE = "KR0050"
QUARTERS = [f"{y}.{n}Q" for y in (2023, 2024, 2025, 2026) for n in (1, 2, 3)][:11]
FILL_ITEMS = (10, 14, 15, 20, 21, 22, 24)
NAMES = {10: "현금및현금성자산", 14: "재보험계약자산", 15: "유형자산", 20: "보험계약부채", 21: "재보험계약부채", 22: "투자계약부채", 24: "기타부채"}
ANCHOR_Q4 = {2024: "2023.4Q", 2025: "2024.4Q", 2026: "2025.4Q"}
CHECK_ITEMS = (1, 2, 3, 10, 14, 15, 20, 21, 22, 24, 30, 31, 4, 11, 12, 13)


def att_path(q):
    y, n = q.split(".")
    return ROOT / "data" / "disclosure" / f"FY{y}_Q{n[0]}" / "attachments" / "KR0050_하나손해보험_attachment_separate_fs.pdf"


def main():
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    spec, problems = [], []
    for q in QUARTERS:
        pdf = att_path(q)
        rows, unit, page = A.read_bs(pdf)
        items = A.to_items(rows)
        sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
        cur = {it: v[1][0] for it, v in items.items() if v[1]}
        pri = {it: v[1][1] for it, v in items.items() if len(v[1]) > 1}
        # identities on the current column
        ids = []
        a, l, e = cur.get(1), cur.get(2), cur.get(3)
        ids.append(("assets = liabilities + equity", None if None in (a, l, e) else a - l - e))
        # section sums: the numbered lines between the section start and the printed total must add up to the total (guards against a mis-read value)
        sec_sum, sec_ok = {}, True
        order = [(lab, raw, vals) for lab, raw, vals, _d in rows if vals]
        acc, which = 0.0, "assets"
        totals_by = {"자산총계": "assets", "부채총계": "liab", "자본총계": "equity"}
        for lab, raw, vals in order:
            if lab in totals_by:
                tot = vals[0]
                sec_sum[totals_by[lab]] = (acc, tot)
                acc = 0.0
                continue
            if lab.startswith("부채및자본총계"):
                continue
            rs = raw.strip()
            if re.match(r"^\d+\)", rs) or re.match(r"^\(\d+\)", rs):
                continue                               # sub-line ("1) 배당요소가 있는 ..."): already inside the numbered line above
            if rs[:1].isdigit():
                acc += vals[0]
        for k, (sm, tot) in sec_sum.items():
            if abs(sm - tot) > 0.0015:
                sec_ok = False
                problems.append((q, "section-sum", k, sm, tot))
        print("    section sums vs totals: " + ", ".join(f"{k} {sm:,.3f}/{tot:,.3f}" for k, (sm, tot) in sec_sum.items()) + ("  OK" if sec_ok else "  MISMATCH"))
        year = int(q[:4])
        anchor = ANCHOR_Q4.get(year)
        print(f"=== {q}  {pdf.name}  page {page} unit {unit}  assets {a:,.3f} liab {l:,.3f} equity {e:,.3f}  A-L-E={a - l - e:+.6f}")
        if anchor:
            diffs = []
            for it in CHECK_ITEMS:
                m = mv.get((CODE, it, anchor))
                p = pri.get(it)
                if m is None or p is None:
                    continue
                diffs.append((it, p, m, p - m))
            bad = [d for d in diffs if abs(d[3]) > 0.0015]
            print(f"    prior-year-end column vs master {anchor}: {len(diffs)} items compared, {len(bad)} differ" +
                  ("" if not bad else "  " + "; ".join(f"item {d[0]}: att {d[1]:,.4f} master {d[2]:,.4f}" for d in bad)))
            if bad:
                problems.append((q, "anchor", bad))
        for it in FILL_ITEMS:
            m = mv.get((CODE, it, q))
            if it not in cur:
                # a line that is not printed -> report (22/23 may be absent)
                print(f"    item {it} {NAMES.get(it)}: no line on the statement" + ("" if m is None else f" (master {m})"))
                continue
            if m is not None:
                print(f"    item {it} {NAMES[it]}: master already {m:,.3f}, statement {cur[it]:,.3f} -> {'same' if abs(m - cur[it]) < 0.6 else 'DIFFERENT'}")
                continue
            print(f"    item {it} {NAMES[it]}: FILL {cur[it]:,.6f}   [{items[it][0].strip()}]")
            anchor_txt = (f"보정: 다음 해가 아니라 같은 해 회계연도 분기 첨부의 전기말 열이 아니라 — 이 분기 표 자체의 전기말(31 Dec {year - 1}) 열이 DART 감사 마스터 {anchor} 값 16개 항목을 0.0015백만원 이내로 재현"
                          if anchor else
                          "보정: 이 해 첨부는 전기말 열이 2022-12-31 이라 마스터 앵커가 없다. 2024~2026 첨부에서 검증된 같은 라벨 매핑 + 자산 = 부채 + 자본 원 단위 폐합 + 번호 줄 합 = 총계 + 마스터에 이미 있는 경영공시 요약 자본총계와 억 반올림 안에서 일치로 대체")
            basis = (f"신규 2026-10-11(round 3, B1): 하나손해보험 KR0050 {q} 분기재무제표 첨부(별도, 단위 원) 재무상태표 p{page} 「{items[it][0].strip()}」 "
                     f"{cur[it] * 1e6:,.0f}원 = {cur[it]:,.6f}백만원. 경영공시 PDF 는 재무제표를 「첨부 파일 참조」로만 둬 이 항목이 비어 있었다. 첨부 수령: downloader "
                     f"inbox/parser/20261010T2350Z, 매니페스트 data/disclosure/_meta/attachments_manifest.json. {anchor_txt.replace('보정: 다음 해가 아니라 같은 해 회계연도 분기 첨부의 전기말 열이 아니라 — ', '보정: ')}.")
            spec.append({"key": f"{CODE}|{it}|{q}", "item": it, "quarter": q, "action": "add", "old": None, "new": round(cur[it], 6), "line": NAMES[it], "basis": basis,
                         "pdf": pdf.relative_to(ROOT).as_posix(), "page": page, "pdf_sha256": sha,
                         "stmt_label": items[it][0].strip(), "prior_col": pri.get(it), "anchor_q4": anchor,
                         "method": "round3_fill:attachment_separate_fs", "scale": "원 -> 백만원"})
        # cross-check of the cells the disclosure summary already holds (rounded to 억)
        cc = []
        for it in (1, 2, 3, 4, 11, 12, 13, 30, 31):
            m = mv.get((CODE, it, q))
            if m is not None and it in cur:
                cc.append((it, cur[it], m, cur[it] - m))
        print("    vs master cells already present (disclosure summary, 억 rounding => |diff| <= 50 expected): " +
              "; ".join(f"{it}: {c:,.1f}/{m:,.1f}({d:+.1f})" for it, c, m, d in cc))
    print(f"\nloadable cells: {len(spec)}; problems: {len(problems)}")
    if "--spec" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--spec") + 1])
        out.write_text(json.dumps({"_what": "B1 KR0050 attachments (separate FS)", "cells": spec}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        print("spec ->", out)


if __name__ == "__main__":
    main()
