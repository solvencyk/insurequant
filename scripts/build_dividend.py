#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dividend.json -- 배당에 관한 사항 (DART alotMatter API), long-format master for
공시보고서.html. Owner order 2026-08-14, inbox/parser/20260814T0938Z.

Source = data/dart/_alotmatter_cache/{corp_code}_{year}_{reprt}.json (already fetched,
39 companies x FY2023-2026 x 4 reprt_code, committed offline). KR-code <-> corp_code from
data/_derived/alotmatter_fetch_census.json's cells (built by the same fetch pass).

Schema (9 columns -- adds 종류주 to the usual 8; "-" for company-level items):
  원보험사코드 / 원수사명 / 티커 / 생손보여부 / 항목번호 / 항목명 / 종류주 / 공시분기 / 값

Items 1-7 are company-level (종류주="-"); items 8-11 are per-share/per-class and repeat once
per 종류주 (보통주/우선주 -- 우선주식/종류주식 등 표기 변형은 우선주로 정규화, 이 저장소
보험사 종류주는 사실상 전부 우선주 성격이라 안전한 축약).

Zero-vs-missing (owner trap #2): status="013" (that period's report doesn't exist) -> no
rows at all. status="000" but an item's thstrm=="-" -> for items 5/6 (배당금총액, the
headline totals) this means a genuine, disclosed zero dividend -- emit 값=0.0. For every
other item, thstrm=="-" means that specific sub-metric wasn't disclosed for this filing
(undefined ratio when there's no dividend, e.g.) -- omit the row, not a fabricated 0.

Values need no unit scaling -- DART returns each 'se' already in its labelled final unit
((백만원)/(원)/(%)/(주)), unlike fnlttSinglAcntAll's raw-원 amounts.

Run: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_dividend.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")

CACHE = ROOT / "data" / "dart" / "_alotmatter_cache"
CENSUS = ROOT / "data" / "_derived" / "alotmatter_fetch_census.json"
OUT = ROOT / "dividend.json"
REPRT_Q = {"11013": "1Q", "11012": "2Q", "11014": "3Q", "11011": "4Q"}

# company-level items: se -> item number, no stock-class split
COMPANY_ITEMS = {
    "주당액면가액(원)": 1,
    "(연결)당기순이익(백만원)": 2,
    "(별도)당기순이익(백만원)": 3,
    "(연결)주당순이익(원)": 4,
    "현금배당금총액(백만원)": 5,
    "주식배당금총액(백만원)": 6,
    "(연결)현금배당성향(%)": 7,
}
ZERO_ON_NO_DIVIDEND = {5, 6}  # headline totals: status=000 + thstrm='-' is a real zero
# per-stock-class items: se -> item number, repeats once per 종류주
CLASS_ITEMS = {
    "주당 현금배당금(원)": 8,
    "주당 주식배당(주)": 9,
    "현금배당수익률(%)": 10,
    "주식배당수익률(%)": 11,
}
LABELS = {v: k for k, v in COMPANY_ITEMS.items()} | {v: k for k, v in CLASS_ITEMS.items()}


def _num(s):
    if s in (None, "", "-"):
        return None
    try:
        return float(str(s).replace(",", ""))
    except ValueError:
        return None


def _norm_stock_knd(s: str) -> str:
    """'-' (no class breakdown -- company has only one stock class, e.g. 삼성생명: both
    rows come back stock_knd='-', first carries the real value) and '보통(주|주식)' both
    normalize to 보통주; '우선주'/trailing-space variant/'종류주식' normalize to 우선주
    (한화생명-style: stock_knd genuinely differentiates 보통/우선)."""
    s = (s or "").strip()
    return "우선주" if s.startswith(("우선", "종류")) else "보통주"


def main():
    census = json.loads(CENSUS.read_text(encoding="utf-8"))
    meta = {}  # kr -> (name, ticker, sb), from kics_disclosure.json
    for r in json.loads((ROOT / "kics_disclosure.json").read_text(encoding="utf-8")):
        c = r.get("원보험사코드")
        if c and c not in meta:
            meta[c] = (r.get("원수사명"), r.get("티커"), r.get("생손보여부"))

    rows = []
    n_ok = n_no_filing = 0
    per_company_diag: dict[str, list[str]] = {}
    for cell in census["cells"]:
        kr, cc, year, reprt = cell["kr"], cell["corp_code"], cell["year"], cell["reprt"]
        qlabel = REPRT_Q.get(reprt)
        if not qlabel or kr not in meta:
            continue
        quarter = f"{year}.{qlabel}"
        if cell["status"] != "000":
            n_no_filing += 1
            continue
        n_ok += 1
        f = CACHE / f"{cc}_{year}_{reprt}.json"
        if not f.exists():
            per_company_diag.setdefault(kr, []).append(f"{quarter}: cache file missing")
            continue
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
        except Exception as e:
            per_company_diag.setdefault(kr, []).append(f"{quarter}: EXC {e}")
            continue
        name, ticker, sb = meta[kr]
        base = {"원보험사코드": kr, "원수사명": name, "티커": ticker, "생손보여부": sb,
                "공시분기": quarter}
        seen_company_items = set()
        seen_class_items = set()
        for r in d.get("list", []):
            se = r.get("se")
            v = _num(r.get("thstrm"))
            if se in COMPANY_ITEMS:
                item = COMPANY_ITEMS[se]
                if item in seen_company_items:
                    continue  # duplicate company-level row (rare) -- first wins
                seen_company_items.add(item)
                if v is None and item not in ZERO_ON_NO_DIVIDEND:
                    continue
                rows.append({**base, "항목번호": item, "항목명": LABELS[item],
                             "종류주": "-", "값": v if v is not None else 0.0})
            elif se in CLASS_ITEMS:
                item = CLASS_ITEMS[se]
                cls = _norm_stock_knd(r.get("stock_knd"))
                key = (item, cls)
                if key in seen_class_items or v is None:
                    continue  # v is None: either genuine placeholder row or no data -- skip
                seen_class_items.add(key)
                rows.append({**base, "항목번호": item, "항목명": LABELS[item],
                             "종류주": cls, "값": v})

    rows.sort(key=lambda r: (r["원보험사코드"], r["항목번호"], r["종류주"], r["공시분기"]))
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}: {len(rows)} rows, {n_ok} filings ok, {n_no_filing} no-filing periods, "
          f"{len({r['원보험사코드'] for r in rows})} companies")
    if per_company_diag:
        print(f"  diag ({sum(len(v) for v in per_company_diag.values())} entries):")
        for kr, ds in sorted(per_company_diag.items()):
            print(f"    {kr}: {ds}")


if __name__ == "__main__":
    main()
