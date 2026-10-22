#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""e20 step 12b: KR0071 FY2026_Q1 / Q2 -- look for the explanation of the changed comparative OCI (재평가잉여금 / 지분상품평가손익) -> stdout"""
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import e20_xml as X  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
for fy in ("FY2026_Q1", "FY2026_Q2"):
    p = X.main_xml("KR0071", fy)
    lines = X.load_lines(p)
    print("#####", fy, X.rel(p))
    n = 0
    for i, l in enumerate(lines, 1):
        t = re.sub(r"\s+", " ", X.RE_TAG.sub("", l)).strip()
        if len(t) > 30 and re.search(r"오류|정정|수정|재분류|재작성", t) and re.search(r"전기|비교|재평가|지분상품|기타포괄", t) and "제1118호" not in t and "연차개선" not in t:
            print(f"  L{i}: {t[:500]}")
            n += 1
            if n >= 25:
                break
