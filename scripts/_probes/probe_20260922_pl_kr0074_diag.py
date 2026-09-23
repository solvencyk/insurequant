# -*- coding: utf-8 -*-
"""KR0074(라이나생명) PL 결손 진단 — 왜 2023.4Q 만 breakdown 이 비었나.

읽기 전용. 분기별로 tier1(FS API / HTML) · tier2 가 무엇을 돌려주는지, assemble 결과
항목1~24 중 몇 개가 채워지는지 인쇄한다. 마스터는 건드리지 않는다.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))

from scripts.build_pl_breakdown import (  # noqa: E402
    ITEM_NAMES,
    ZERO_FILL_ITEMS,
    _fs_tier1,
    _quarter_sort_key,
    _xmls_in,
    assemble,
    discover_filings,
    load_universe,
    parse_filing,
)

CODE = "KR0074"


def main():
    uni = load_universe()
    name, life_flag = uni.get(CODE, (CODE, None))
    is_life = life_flag == "생명보험"
    filings = discover_filings()
    qs = sorted(filings.get(CODE, {}), key=_quarter_sort_key)
    print(f"{CODE} {name} 생손보={life_flag} · 발견된 filing 분기 {len(qs)}개")
    for q in qs:
        print("   ", q, [str(Path(d).name) for d in filings[CODE][q]])
    print()

    parsed = {}
    for q in qs:
        dirs = filings[CODE][q]
        has_xml = any(_xmls_in(d) for d in dirs)
        t1_html, t2 = parse_filing(dirs, is_life, code=CODE, name=name, quarter=q)
        t1_api = _fs_tier1(name, q, CODE)
        t1 = t1_api if t1_api else t1_html
        parsed[q] = (t1, t2, has_xml, t1_api is not None, t1_html is not None)

    print(f"{'분기':<10}{'xml':>5}{'t1_api':>8}{'t1_html':>9}{'t2':>6}{'채운항목수':>9}  결손항목")
    for q in qs:
        t1, t2, has_xml, api_ok, html_ok = parsed[q]
        if t1 is None and t2 is None:
            print(f"{q:<10}{str(has_xml):>5}{str(api_ok):>8}{str(html_ok):>9}"
                  f"{'None':>6}{0:>9}  전부(파싱 실패)")
            continue
        v = assemble(t1, t2, is_life, zero_fill_ok=frozenset())
        filled = [n for n in range(1, 25) if v.get(n) is not None]
        miss = [n for n in range(1, 25) if v.get(n) is None]
        print(f"{q:<10}{str(has_xml):>5}{str(api_ok):>8}{str(html_ok):>9}"
              f"{('dict' if t2 else 'None'):>6}{len(filled):>9}  {miss}")

    print("\n[상세] 2023.4Q vs 2024.4Q tier1 키")
    for q in ("2023.4Q", "2024.4Q"):
        t1 = parsed.get(q, (None,))[0]
        print(f"  {q}: ", end="")
        if t1 is None:
            print("t1 None")
        else:
            print(json.dumps({k: t1[k] for k in sorted(t1)}, ensure_ascii=False)[:900])


main()
