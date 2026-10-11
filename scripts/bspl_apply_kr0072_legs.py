#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (parser/ifrs17, inbox/parser/20261011T1130Z item A2): KDB생명 (KR0072) reinsurance/direct PL legs, YTD column vs master (read-only).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_kr0072_legs.py [KR0072]

For every quarter: reads the DART '보험영업수익(비용) 및 재보험영업수익(비용)' note tables (3개월 / 누적 pair layout in Q2/Q3, 당기 column otherwise),
computes the YTD legs with the master's own formulas (companies._life_build_items):
  item5 = |수익 위험해제 RA|        item6 = |수익 예상발생보험금| - |비용 실제발생보험금|
  item9 = -|재보험비용 CSM|          item10 = -|재보험비용 RA|        item11 = |재보험수익 실제출재| - |재보험비용 예상출재|
and prints them next to the master (YTD) values together with the printed 3-month column value, so a 3-month pick is visible.
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

CODE = sys.argv[1] if len(sys.argv) > 1 else "KR0072"


def num(c):
    t = re.sub(r"[\s\u3000\xa0]+", "", str(c))
    if t in ("", "-"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(",", "")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def nospace(s):
    return re.sub(r"[\s\u3000\xa0]+", "", s or "")


EXP_REV = ("예상발생보험금및보험서비스비용", "예상보험금및보험서비스비용", "예상발생보험금및비용", "예상발생보험금")
RA = ("위험해제로인한비금융위험에대한위험조정의변", "위험해제로인한위험조정의변동", "비금융위험에대한위험조정의변동")
CSM = ("제공된서비스의보험계약마진", "제공받은서비스의보험계약마진", "서비스의이전으로당기손익에인식한보험계약마진")
ACT_COST = ("실제발생보험금및보험서비스비용", "실제발생보험금")
RE_ACT = ("실제출재보험금및보험서비스비용", "실제출재보험금및재보험비용", "실제출재보험금및재보험서비스비용", "당기발생재보험금")
RE_EXP = ("예상출재보험금및보험서비스비용", "예상출재보험금및재보험비용", "예상출재보험금및재보험서비스비용")


def is_pair(t):
    blob = " ".join(" ".join(str(c) for c in r) for r in t.rows[:5]) + " " + " ".join(" ".join(h) for h in (t.header or []))
    return "누적" in blob and "3개월" in blob


def sections(t):
    """yield (section, label, [numbers]) for the note table; section in rev/cost/re_rev/re_cost."""
    sec = None
    for r in t.rows:
        cells = [str(c) for c in r]
        lab = nospace(cells[0]) if cells else ""
        nums = [n for n in (num(c) for c in cells[1:]) if n is not None]
        m = re.sub(r"^\d+\.", "", lab)
        if m in ("보험영업수익", "보험수익"):
            sec = "rev"
        elif m in ("보험영업비용", "보험서비스비용", "보험비용"):
            sec = "cost"
        elif m in ("재보험영업수익", "재보험수익"):
            sec = "re_rev"
        elif m in ("재보험영업비용", "재보험비용", "재보험서비스비용"):
            sec = "re_cost"
        if not nums:
            continue
        yield sec, lab, nums


def read_note(xml: Path):
    """returns dict kind -> (3m, ytd) for rev.exp/ra/csm, cost.act, re_rev.act, re_cost.exp/ra/csm (first matching table per section)."""
    out = {}
    layout = {}
    for t in _iter_tables_with_context(xml):
        cap = nospace(t.caption)
        txt = " ".join(" ".join(str(c) for c in r) for r in t.rows)
        if "재보험" not in txt or "위험조정" not in txt or "보험계약마진" not in txt:
            continue
        if not any(k in cap for k in ("구성내역", "보험영업수익", "보험서비스비용", "재보험비용", "보험수익")):
            continue
        if any(k in cap for k in ("변동내역", "요소별")):
            continue
        pair = is_pair(t)
        for sec, lab, nums in sections(t):
            def put(kind):
                if kind not in out:
                    three = nums[0]
                    ytd = nums[1] if pair and len(nums) > 1 else nums[0]
                    out[kind] = (three, ytd)
                    layout[kind] = ("pair" if pair else "single", t.line_no)
            if sec == "rev":
                if any(v in lab for v in RA):
                    put("rev.ra")
                elif any(v in lab for v in CSM):
                    put("rev.csm")
                elif any(v in lab for v in EXP_REV):
                    put("rev.exp")
            elif sec == "cost":
                if any(v in lab for v in ACT_COST):
                    put("cost.act")
            elif sec == "re_rev":
                if any(v in lab for v in RE_ACT):
                    put("re_rev.act")
            elif sec == "re_cost":
                if any(v in lab for v in RA):
                    put("re_cost.ra")
                elif any(v in lab for v in CSM):
                    put("re_cost.csm")
                elif any(v in lab for v in RE_EXP):
                    put("re_cost.exp")
    return out, layout


def legs(d, which):
    i = 1 if which == "ytd" else 0
    g = lambda k: abs(d[k][i]) if k in d else None
    res = {}
    if g("rev.ra") is not None:
        res[5] = g("rev.ra")
    if g("rev.exp") is not None and g("cost.act") is not None:
        res[6] = g("rev.exp") - g("cost.act")
    if g("re_cost.csm") is not None:
        res[9] = -g("re_cost.csm")
    if g("re_cost.ra") is not None:
        res[10] = -g("re_cost.ra")
    if g("re_rev.act") is not None and g("re_cost.exp") is not None:
        res[11] = g("re_rev.act") - g("re_cost.exp")
    return res


def main():
    pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    mv = {(str(r["항목번호"]), r["공시분기"]): r["값"] for r in pl if r["원보험사코드"] == CODE}
    print(f"{CODE}: per quarter, items 5/6/9/10/11: recomputed YTD | recomputed 3-month | master   (flag: Y = master==YTD, 3 = master==3-month, ? = neither)")
    for y in (2023, 2024, 2025, 2026):
        for n in (1, 2, 3, 4):
            q = f"{y}.{n}Q"
            base = ROOT / "data" / "dart" / f"FY{y}_Q{n}" / "raw"
            files = sorted(base.glob(f"{CODE}_*/*.xml")) + sorted(base.glob(f"{CODE}_*/xml/*.xml"))
            if not files:
                continue
            best = None
            for f in files:
                d, lay = read_note(f)
                if best is None or len(d) > len(best[0]):
                    best = (d, lay, f)
            d, lay, f = best
            ytd, three = legs(d, "ytd"), legs(d, "3m")
            kinds = sorted({v[0] for v in lay.values()})
            line = f"{q} {f.name[:22]:<22} {'/'.join(kinds) or '-':<6}"
            for it in (5, 6, 9, 10, 11):
                m = mv.get((str(it), q))
                if it not in ytd:
                    line += f" | {it}: n/a (master {m})"
                    continue
                fl = "Y" if m is not None and abs(m - ytd[it]) < 0.51 else ("3" if m is not None and it in three and abs(m - three[it]) < 0.51 else "?")
                line += f" | {it}: {ytd[it]:,.0f} {three.get(it, float('nan')):,.0f} m={m if m is None else format(m, ',.0f')} [{fl}]"
            print(line)


if __name__ == "__main__":
    main()
