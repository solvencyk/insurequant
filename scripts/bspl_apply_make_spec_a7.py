#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (A7): BS fills from the DART separate balance sheet of the quarterly report (the 9 blanks of the follow-up probe, minus what does not verify).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_make_spec_a7.py [out.json]

Each fill reads its table by (company, quarter, xml table line, label prefix), converts to 백만원 with full precision when the table is in 원
(summary tables are in 백만원), checks the table's asset total against the master item 1 of the same cell (the master of that quarter is the separate
basis there) and that the same table reproduces >= 5 other master cells of the quarter.  KR0005 item 24 (2023.1Q·2Q) is NOT filled: the filing line
「기타부채」 106,989 / 97,571 is 기타금융부채 + 비금융 기타부채, while the master series (FS-API ifrs-full_OtherNonfinancialLiabilities) is the
non-financial part only (2023.3Q 10,934) -- a definition break of about 10x.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
import bspl_apply_xmlbs as X  # noqa: E402
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "_derived" / "bspl_apply_20261011" / "spec_A7_dart_fills.json"
NAMES = {10: "현금및현금성자산", 20: "보험계약부채", 21: "재보험계약부채", 31: "이익잉여금", 24: "기타부채"}
# (code, quarter, item, xml table line, label prefix (spaces removed), unit)
FILLS = [
    ("KR0003", "2023.2Q", 31, 5399, "Ⅵ.이익잉여금", "원"),
    ("KR0009", "2023.1Q", 10, 21857, "Ⅰ.현금및현금성자산", "원"),
    ("KR0009", "2023.1Q", 20, 21857, "Ⅰ.보험계약부채", "원"),
    ("KR0009", "2023.1Q", 21, 21857, "Ⅱ.재보험계약부채", "원"),
    ("KR0009", "2023.2Q", 20, 25960, "Ⅰ.보험계약부채", "원"),
    ("KR0009", "2023.2Q", 21, 25960, "Ⅱ.재보험계약부채", "원"),
    ("KR0069", "2023.1Q", 10, 11140, "I.현금및현금성자산", "백만원"),
]


def main():
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {(r["원보험사코드"], r["항목번호"], r["공시분기"]): r["값"] for r in bs}
    cells, tables = [], {}
    for code, q, item, line, prefix, unit in FILLS:
        if (code, item, q) in mv:
            print(f"SKIP {code}|{item}|{q}: master already holds {mv[(code, item, q)]}")
            continue
        xml = X.xml_files(code, q)
        assert len(xml) == 1, xml
        xml = xml[0]
        key = (str(xml), line)
        if key not in tables:
            for t in _iter_tables_with_context(xml):
                if t.line_no == line:
                    tables[key] = t
                    break
            assert key in tables, key
        t = tables[key]
        # table identity: totals and >= 5 other master cells reproduced
        lines = X.table_lines(t)
        iv = X.item_values(lines)
        scale = 1e-6 if unit == "원" else 1.0
        assert abs(iv[1] * scale - mv[(code, 1, q)]) < 0.6, (code, q, iv.get(1), mv[(code, 1, q)])
        tie = [i for i in iv if i not in (item,) and (code, i, q) in mv and abs(iv[i] * scale - mv[(code, i, q)]) < 0.6]
        assert len(tie) >= 5, (code, q, tie)
        # the label row
        val = None
        for r in t.rows:
            if r and X.ns(str(r[0])).startswith(prefix):
                nums = []
                for c in r[1:]:
                    if X.LEGIT.match(X.ns(str(c))):
                        v = X.num(c)
                        if v is not None and (unit == "백만원" or abs(v) >= 1e6):
                            nums.append(v)
                if nums:
                    val = nums[0]
                    lab = str(r[0])
                    break
        assert val is not None, (code, q, item, prefix)
        new = round(val * scale, 6)
        sha = hashlib.sha256(xml.read_bytes()).hexdigest()
        rel = xml.relative_to(ROOT).as_posix()
        basis = (f"신규 2026-10-11(round 3, A7): 마스터 빈 칸. {rel}(sha256 {sha[:12]}...) 의 별도 {'재무상태표' if unit == '원' else '요약별도재무상태표'}"
                 f"(XML 표 line {line}, 단위 {unit}) 「{lab.strip()}」 {new:,.6f}백만원. 같은 표가 이 분기 마스터의 자산총계({iv[1] * scale:,.3f})와 다른 {len(tie)}개 칸"
                 f"({sorted(tie)})을 정확히 재현하므로 마스터와 같은 별도 기준·같은 정의다. 후속 보고(bspl_granularity 런로그 부수 발견 ⑤)가 찾은 빈 칸이고 이 라운드에서 "
                 f"원천 표를 다시 열어 값을 재현했다. 계보: DART 분기보고서 본문 XML.")
        cells.append({"key": f"{code}|{item}|{q}", "item": item, "quarter": q, "action": "add", "old": None, "new": new, "line": NAMES[item],
                      "pdf": rel, "page": line, "pdf_sha256": sha, "basis": basis, "method": "round3_fill:dart_separate_bs_xml",
                      "scale": "원 -> 백만원" if unit == "원" else "백만원 -> 백만원"})
    OUT.write_text(json.dumps({"_what": "A7 BS fills from the DART separate BS", "cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for c in cells:
        print(f"{c['key']:<18} (blank) -> {c['new']:>20,.6f}  (table line {c['page']})")
    print(f"{len(cells)} cells -> {OUT}")


if __name__ == "__main__":
    main()
