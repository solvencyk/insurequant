# -*- coding: utf-8 -*-
"""마스터 3종의 값 컬럼 **타입 분포**를 센다 (read-only).

변이시험 하니스가 `isinstance(v,(int,float))` 로 거르면 무엇을 놓치는지 실측하기 위한 것.
2026-08-24 에 그 필터로 4만 칸 중 80칸만 흔들고 "전부 눈멀었다" 는 거짓 결과가 나온 전례.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

NUMLIKE = re.compile(r"^-?[\d,]+(\.\d+)?$")


def classify(v):
    if v is None or v == "":
        return "empty"
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, (int, float)):
        return "number"
    s = str(v)
    if NUMLIKE.match(s.strip()):
        return "str-numeric"
    if "△" in s or "▲" in s:
        return "str-samo(△)"
    if s.strip().startswith("(") and s.strip().endswith(")"):
        return "str-paren"
    return "str-other"


def main() -> int:
    for fname, cols in (("kics_disclosure.json", ("값", "값_적용후")),
                        ("CSM_waterfall.json", ("값",)),
                        ("PL_breakdown.json", ("값",))):
        p = ROOT / fname
        rows = json.loads(p.read_text(encoding="utf-8"))
        print(f"=== {fname}  rows={len(rows)}")
        for col in cols:
            c = Counter(classify(r.get(col)) for r in rows)
            tot = sum(c.values())
            shakeable = c["number"] + c["str-numeric"] + c["str-samo(△)"] + c["str-paren"]
            print(f"   [{col}] {dict(c)}")
            print(f"        총 {tot} · 숫자로만 걸면 {c['number']} · 실제 흔들 수 있는 칸 {shakeable}")
            odd = [str(r.get(col)) for r in rows if classify(r.get(col)) == "str-other"][:6]
            if odd:
                print(f"        str-other 표본: {odd}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
