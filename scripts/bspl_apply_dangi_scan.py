#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (parser/ifrs17): scan PL_breakdown.json for rows whose stored `값_당분기` differs from the master's own rule
(build_root_masters._flow_dangi: YTD(q) - YTD(previous quarter of the same year), Q1 = YTD, None when a YTD is missing).  Read-only.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_dangi_scan.py [out.json]
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")


def prev_q(q):
    y, n = int(q[:4]), int(q[5])
    return None if n == 1 else f"{y}.{n - 1}Q"


def rule(ytd, q):
    cur = ytd.get(q)
    if cur is None:
        return None
    p = prev_q(q)
    if p is None:
        return cur
    prev = ytd.get(p)
    return None if prev is None else round(cur - prev, 6)


def main():
    rows = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    ytd = defaultdict(dict)
    for r in rows:
        ytd[(r["원보험사코드"], str(r["항목번호"]))][r["공시분기"]] = r.get("값")
    bad = []
    kinds = Counter()
    for r in rows:
        if r.get("값") is None:
            if r.get("값_당분기") is not None:
                kinds["dangi_without_value"] += 1
                bad.append((r["원보험사코드"], r["항목번호"], r["공시분기"], r.get("값"), r.get("값_당분기"), None, "dangi_without_value"))
            continue
        exp = rule(ytd[(r["원보험사코드"], str(r["항목번호"]))], r["공시분기"])
        got = r.get("값_당분기")
        if exp is None and got is None:
            continue
        if exp is not None and got is not None and abs(exp - got) <= 1e-6:
            continue
        kind = "stored_None_rule_number" if got is None else ("stored_number_rule_None" if exp is None else "number_mismatch")
        kinds[kind] += 1
        bad.append((r["원보험사코드"], r["항목번호"], r["공시분기"], r.get("값"), got, exp, kind))
    print(f"rows {len(rows)}; 값_당분기 deviations from the rule: {len(bad)}  {dict(kinds)}")
    by_co = Counter(b[0] for b in bad)
    print("by company (top 15):", by_co.most_common(15))
    by_it = Counter(str(b[1]) for b in bad)
    print("by item (top 12):", by_it.most_common(12))
    if len(sys.argv) > 1:
        Path(sys.argv[1]).write_text(json.dumps([list(b) for b in bad], ensure_ascii=False, indent=0), encoding="utf-8", newline="\n")
        print("wrote", sys.argv[1])


if __name__ == "__main__":
    main()
