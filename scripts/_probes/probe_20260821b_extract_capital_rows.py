# -*- coding: utf-8 -*-
"""Extract '기본자본'/'보완자본'/'지급여력금액' pre/post rows from the SAME
'[지급여력비율의 경과조치 적용에 관한 사항] 1) 공통적용 경과조치' table that
extract_tier2() reads 47/48/49 from -- so we can cross-check item2/item3 in the
core master against an independent source printed on the very same page.
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from fix_20260821_tier2_limit_lines import _pdf, q2p, _collect_values  # noqa: E402

import fitz  # noqa: E402


def norm(s):
    return s.replace(" ", "")


def extract_capital_rows(pdf):
    doc = fitz.open(pdf)
    try:
        page_texts = [doc[i].get_text() for i in range(doc.page_count)]
    finally:
        doc.close()
    matched = {i for i, t in enumerate(page_texts)
               if "공통적용" in t and "보완자본" in t and "한도" in t}
    if not matched:
        return {}
    include = set(matched)
    for i in matched:
        if i + 1 < len(page_texts):
            include.add(i + 1)
    lines = []
    for i in sorted(include):
        lines.extend(x.strip() for x in page_texts[i].splitlines())

    targets = {
        "지급여력비율": norm("지급여력비율(%)"),
        "지급여력금액": norm("지급여력금액"),
        "기본자본": norm("기본자본"),
        "보완자본": norm("보완자본"),
        "지급여력기준금액": norm("지급여력기준금액"),
    }
    found = {}
    k = 0
    while k < len(lines):
        s = norm(lines[k])
        hit = False
        for name, tgt in targets.items():
            if s == tgt and name not in found:
                vals, j = _collect_values(lines, k + 1, need=2)
                if len(vals) == 2:
                    found[name] = (vals[0], vals[1])
                elif len(vals) == 1:
                    found[name] = (vals[0], vals[0])
                k = j
                hit = True
                break
        if not hit:
            k += 1
    return found


def main():
    code = sys.argv[1]
    quarters = sys.argv[2].split(",")
    for q in quarters:
        pdf = _pdf(q2p(q), code)
        if pdf is None:
            print(f"{q}: NO PDF")
            continue
        found = extract_capital_rows(pdf)
        print(f"{q}: {found}")


if __name__ == "__main__":
    raise SystemExit(main())
