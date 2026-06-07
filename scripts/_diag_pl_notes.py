# -*- coding: utf-8 -*-
"""Diagnostic: dump the LOB / 발행·재보험 analysis note tables for a (code, quarter).
Shows caption, header, and per-row (col0|col1 label + numeric cells) so we can see
exactly what structure a 'not matched' company uses.  Read-only.

Usage: python scripts/_diag_pl_notes.py KR0002 2025.4Q [--all]
"""
import glob
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.stdout.reconfigure(encoding="utf-8")
from src.ifrs17.csm_extractor import _iter_tables_with_context  # noqa: E402
from scripts.build_net_income_breakdown import to_num  # noqa: E402


def _norm(s):
    return (s or "").replace("　", "").replace("\xa0", " ").strip()


# Rollforward (CSM waterfall) tables to EXCLUDE — they also carry 보험계약마진/위험조정.
ROLLFWD = ("기초 순장부금액", "기말 순장부금액", "기초 보험계약", "기말 보험계약",
           "수취한 보험료", "총 현금흐름", "순장부금액")
# The 보험손익 analysis note decomposes 보험수익/보험서비스비용 into expected claims +
# CSM amortization + RA release.  Signature row-label fragments:
ANALYSIS_ROWS = ("당기손익에 인식한 보험계약마진", "보험계약마진의 상각", "제공된 서비스의 보험계약마진",
                 "위험조정의 변동", "위험해제", "예상 측정치", "기초 예상", "예상 발생보험금",
                 "발생한 보험금", "회수")


def looks_like_note(t):
    rowblob = " ".join(_norm(r[0]) + " " + (_norm(r[1]) if len(r) > 1 else "") for r in t.rows)
    if any(k in rowblob for k in ROLLFWD):
        return False  # rollforward, not the P&L analysis note
    hits = sum(1 for k in ANALYSIS_ROWS if k in rowblob)
    return hits >= 2 and ("보험수익" in rowblob or "보험서비스비용" in rowblob
                          or "재보험" in rowblob or "보험계약마진" in rowblob)


def fmt_row(r):
    lab = _norm(r[0])
    lab1 = _norm(r[1]) if len(r) > 1 else ""
    nums = [to_num(c) for c in r]
    nums = [round(n, 1) for n in nums if n is not None]
    label = lab if not lab1 else f"{lab} | {lab1}"
    return f"    {label[:60]:<60}  nums={nums}"


def main():
    code, q = sys.argv[1], sys.argv[2]
    show_all = "--all" in sys.argv
    y, qq = re.match(r"(\d{4})\.(\d)Q", q).groups()
    base_glob = f"data/dart/FY{y}_Q{qq}/raw/{code}_*"
    dirs = glob.glob(base_glob)
    if not dirs:
        print("no raw dir for", code, q, "glob=", base_glob)
        return
    tables = []
    for d in dirs:
        xs = glob.glob(d + "/*.xml") + glob.glob(d + "/xml/*.xml") + glob.glob(d + "/extracted*/*.xml")
        for x in sorted(set(xs), key=os.path.getsize, reverse=True):
            try:
                tables.extend(_iter_tables_with_context(Path(x)))
            except Exception as e:
                print("  parse error", x, e)
    print(f"=== {code} {q} : {len(tables)} tables ===")
    n = 0
    for t in tables:
        if not show_all and not looks_like_note(t):
            continue
        n += 1
        print(f"\n[table {n}] caption={t.caption!r}")
        for h in t.header:
            print("   H:", [_norm(c) for c in h])
        for r in t.rows[:24]:
            print(fmt_row(r))
    print(f"\n-> {n} candidate note tables shown")


if __name__ == "__main__":
    main()
