#!/usr/bin/env python3
"""item23(기타 요구자본) = item24 + item25 + item26 의 적용전/적용후 전수 측정 probe.

`inbox/validation/20260821T1100Z` 티켓의 ①을 배선하기 전에 **오케스트레이터가 준 숫자를
내가 직접 재현**하기 위한 일회성 감사 도구(상주). 게이트 배선본은
`scripts/validate_kics_disclosure.py::_other_capital_children_sum` 이고 여기는 측정만 한다.
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from solvency.validation.kics_json_rules import (  # noqa: E402
    IMAGE_OCR_COMPANIES,
    IMAGE_OCR_TOLERANCE,
    KEY_CODE,
    KEY_ITEM,
    KEY_NAME,
    KEY_QUARTER,
    KEY_VALUE,
    KEY_VALUE_POST,
)


def _num(v):
    try:
        return float(str(v).replace(",", ""))
    except (TypeError, ValueError):
        return None


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    recs = json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8"))
    labels = defaultdict(Counter)
    byq: dict[tuple, dict] = {}
    name: dict[str, str] = {}
    for r in recs:
        c, q = r.get(KEY_CODE), r.get(KEY_QUARTER)
        name[c] = r.get(KEY_NAME, c)
        try:
            it = int(r.get(KEY_ITEM))
        except (TypeError, ValueError):
            continue
        if it in (23, 24, 25, 26):
            labels[it][str(r.get("항목명", ""))] += 1
        if c and q:
            byq.setdefault((c, q), {})[it] = (_num(r.get(KEY_VALUE)), _num(r.get(KEY_VALUE_POST)))

    print("== 항목 라벨 (23~26) ==")
    for it in (23, 24, 25, 26):
        for lbl, n in labels[it].most_common(4):
            print(f"  item{it}: {n:>4}x  {lbl}")

    for col, idx in (("적용전", 0), ("적용후", 1)):
        checked = miss = 0
        fails = []
        skipped: Counter = Counter()
        for (c, q), m in sorted(byq.items()):
            tgt = m.get(23, (None, None))[idx]
            kids = [m.get(i, (None, None))[idx] for i in (24, 25, 26)]
            if tgt is None:
                skipped["부모(item23)결측"] += 1
                continue
            if any(k is None for k in kids):
                skipped["자식(24/25/26)일부결측"] += 1
                miss += 1
                continue
            checked += 1
            exp = sum(kids)
            tol = IMAGE_OCR_TOLERANCE if c in IMAGE_OCR_COMPANIES else 2.0
            if abs(exp - tgt) > tol:
                fails.append((c, q, name.get(c, c), tgt, exp, kids))
        print(f"\n== {col}: 검사 {checked} / 통과 {checked - len(fails)} / 불일치 {len(fails)} ==")
        print(f"   미판정 {dict(skipped)}")
        for c, q, n, tgt, exp, kids in fails:
            print(f"   {q} {c} {n}: item23={tgt} vs 24+25+26={exp} {kids}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
