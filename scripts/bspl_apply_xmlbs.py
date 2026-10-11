#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (parser/ifrs17): list / compare the full balance-sheet tables of a DART body XML against the BS master (read-only).

  ... bspl_apply_xmlbs.py KR0070 2023.1Q                 list the BS-like tables (line, rows, totals) of every XML of that filing
  ... bspl_apply_xmlbs.py KR0070 2023.1Q --compare       also print, per table, the master item values next to the matching table lines
A 'BS-like' table has 자산총계, 부채총계 and 자본총계 rows.  Line -> item mapping follows the master definitions (build_ifrs17_bs.LABELS):
10 현금및현금성자산, 11 당기손익-공정가치측정금융자산, 12 기타포괄손익-공정가치측정금융자산, 13 상각후원가측정금융자산, 14 재보험계약자산, 15 유형자산,
20 보험계약부채, 21 재보험계약부채, 22 투자계약부채, 23 차입부채, 24 기타부채, 30 자본금, 31 이익잉여금(결손금), 4 기타포괄손익누계액, 1/2/3 totals.
Numbers are returned in the table's own unit (detected: 원 if the asset total has >= 13 digits, else the unit that matches the summary tables = 백만원).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402

MAP = {
    1: ("자산총계",), 2: ("부채총계",), 3: ("자본총계",),
    10: ("현금및현금성자산",), 11: ("당기손익-공정가치측정금융자산", "당기손익공정가치측정금융자산"),
    12: ("기타포괄손익-공정가치측정금융자산", "기타포괄손익공정가치측정금융자산"),
    13: ("상각후원가측정금융자산",), 14: ("재보험계약자산",), 15: ("유형자산",),
    20: ("보험계약부채",), 21: ("재보험계약부채",), 22: ("투자계약부채",), 23: ("차입부채",), 24: ("기타부채",),
    30: ("자본금",), 31: ("이익잉여금", "결손금", "이익잉여금(결손금)", "연결이익잉여금", "연결결손금", "연결이익잉여금(결손금)"),
    4: ("기타포괄손익누계액", "연결기타포괄손익누계액"),
}


def ns(s):
    return re.sub(r"[\s　\xa0]+", "", s or "")


def num(c):
    t = ns(str(c))
    if t in ("", "-"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(",", "")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def clean_label(lab):
    t = ns(lab)
    t = re.sub(r"^[ⅠⅡⅢⅣⅤⅥⅦⅧⅨⅩⅪⅫIVXLCivxlc]+\.", "", t)       # roman numeral prefix (ASCII or full-width)
    t = re.sub(r"^\d+\.", "", t)
    t = re.sub(r"^\(\d+\)", "", t)
    t = re.sub(r"\(주[^)]*\)?$", "", t)
    t = re.sub(r"\(주[\d,\s]*\)", "", t)
    t = re.sub(r"\(대손준비금.*$", "", t)
    return t


def bs_like(t):
    labs = [clean_label(r[0]) for r in t.rows if r]
    return all(any(l.startswith(k) for l in labs) for k in ("자산총계", "부채총계", "자본총계")) or \
        (any("자산총계" in l for l in labs) and any("부채총계" in l for l in labs) and any("자본총계" in l for l in labs))


LEGIT = re.compile(r"^\(?-?\d{1,3}(,\d{3})*\)?$")


def table_lines(t):
    """label -> first numeric value of the row (current period column).  Note-reference cells ('4,5', '10,12') are skipped; in a 원 table
    (asset total >= 1e10) values below 1e6 are note numbers, not amounts."""
    rows = []
    for r in t.rows:
        if not r:
            continue
        lab = clean_label(str(r[0]))
        vals = []
        for c in r[1:]:
            tx = ns(str(c))
            if not LEGIT.match(tx):
                continue
            v = num(c)
            if v is not None:
                vals.append(v)
        rows.append((lab, vals))
    tot = [v for lab, vals in rows if lab.startswith("자산총계") for v in vals]
    won = bool(tot) and max(abs(v) for v in tot) >= 1e10
    out = {}
    for lab, vals in rows:
        if won:
            vals = [v for v in vals if abs(v) >= 1e6 or v == 0]
        if not vals:
            continue
        out.setdefault(lab, vals[0])
    return out


def item_values(lines):
    res = {}
    for item, names in MAP.items():
        for n in names:
            nn = ns(n)
            hit = [k for k in lines if k == nn]
            if not hit:
                hit = [k for k in lines if k.startswith(nn) and (item in (1, 2, 3) or k[len(nn):len(nn) + 1] == "(")]
            if hit:
                res[item] = lines[hit[0]]
                break
    return res


def xml_files(code, quarter):
    y, q = quarter.split(".")
    base = ROOT / "data" / "dart" / f"FY{y}_Q{q[0]}" / "raw"
    out = []
    for d in sorted(base.glob(f"{code}_*")):
        out += sorted(d.rglob("*.xml"))
    return out


def main():
    code, quarter = sys.argv[1], sys.argv[2]
    compare = "--compare" in sys.argv
    bs = json.loads((ROOT / "IFRS17_BS.json").read_text(encoding="utf-8"))
    mv = {r["항목번호"]: r["값"] for r in bs if r["원보험사코드"] == code and r["공시분기"] == quarter}
    for f in xml_files(code, quarter):
        print(f"##### {f.relative_to(ROOT)}")
        for t in _iter_tables_with_context(f):
            if not bs_like(t):
                continue
            lines = table_lines(t)
            iv = item_values(lines)
            a = iv.get(1)
            unit = 1e-6 if (a and abs(a) >= 1e12) else 1.0
            labs = [clean_label(r[0]) for r in t.rows[:4] if r]
            print(f"--- line {t.line_no} rows {len(t.rows)} unit {'원' if unit < 1 else '백만원'} caption {(t.caption or '')[:60]!r} first labels {labs[:3]}")
            print("    totals: " + " ".join(f"{k}={iv.get(k) * unit:,.3f}" if iv.get(k) is not None else f"{k}=-" for k in (1, 2, 3)))
            if compare:
                print(f"    {'item':>4} {'xml line value':>20} {'master':>20}  match")
                for item in sorted(MAP):
                    xv = iv.get(item)
                    m = mv.get(item)
                    x6 = None if xv is None else xv * unit
                    flag = ""
                    if x6 is not None and m is not None:
                        flag = "==" if abs(x6 - m) <= max(1.0, 1e-6 * abs(m)) else "!="
                    elif x6 is not None and m is None:
                        flag = "xml only"
                    elif x6 is None and m is not None:
                        flag = "master only"
                    if x6 is None and m is None:
                        continue
                    print(f"    {item:>4} {('-' if x6 is None else format(x6, ',.3f')):>20} {('-' if m is None else format(m, ',.3f')):>20}  {flag}")


if __name__ == "__main__":
    main()
