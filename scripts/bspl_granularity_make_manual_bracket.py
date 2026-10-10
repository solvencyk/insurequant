#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Round 11 helper (2026-10-11): load the CAND_BRACKET cells of `bspl_granularity_candidates.py --bracket`.

Bracket acceptance (opt-in): a mapping rule that fails somewhere in the company's whole history (a definition the master itself
changed, a restated comparative, a parse failure of ONE other filing) is trusted for an INTERIM cell of fiscal year Y when the
evidence of that year reproduces the master at BOTH bracketing year-ends (Y-1.4Q and Y.4Q).  The candidates live in
data/_derived/bspl_granularity_20261011/candidates_bracket/ (the normal candidates/ are untouched).  This script turns them into
manual-schema cells with an explicit `basis` and writes manual_round11.json for scripts/bspl_granularity_load_bs.py --manual.

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_candidates.py --company all --bracket
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_make_manual_bracket.py
  ... scripts/bspl_granularity_load_bs.py --status NONE --manual data/_derived/bspl_granularity_20261011/manual_round11.json --round 11 [--apply]
"""
from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

ROOT = "C:/Users/sangwook.cho/Desktop/insurequant/"
sys.stdout.reconfigure(encoding="utf-8")
BASE = Path(__file__).resolve().parents[1] / "data" / "_derived" / "bspl_granularity_20261011"
TAIL = " (inbox/parser/20261011T0310Z bspl granularity)"


def main():
    cells = []
    for f in sorted(glob.glob(str(BASE / "candidates_bracket" / "KR*.json"))):
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        for c in d["candidates"]:
            if c["status"] != "CAND_BRACKET":
                continue
            key = f"{c['rule']}|{c['form']}"
            ev = d["calibration"][key]["evidence"]
            y = int(c["quarter"][:4])
            a1, a2 = f"{y - 1}.4Q", f"{y}.4Q"
            ok1 = [e for e in ev if e[1] == a1 and int(e[0][:4]) == y and e[4]]
            ok2 = [e for e in ev if e[1] == a2 and int(e[0][:4]) in (y, y + 1) and e[4]]
            bad = [e for e in ev if not e[4]]
            bad_txt = "; ".join(f"{e[0]} 공시의 {e[1]} 열 {e[5]/100:,.1f} 대 마스터 {e[6]/100:,.1f}억" for e in bad[:4])
            c = dict(c)
            c["status"] = "MANUAL"
            c["basis"] = (
                f"정기경영공시 {c['quarter']} {'재무상태표(8-1, 단위 ' + c['unit'] + ')' if c['kind'] == 'bs_full' else c['kind']} p{c['page']} "
                f"라벨 규칙「{c['rule']}」 = {c['value_mn'] / 100:,.2f}억. 연말 앵커 브래킷 승인: 이 규칙이 전 기간 단일 규칙으로는 불합격이지만"
                f"({bad_txt}), {y}회계연도 앞뒤 연말 앵커 {a1}·{a2} 를 같은 규칙이 모두 재현한다(전년말 앵커 {len(ok1)}개 열 · 당해 연말 앵커 {len(ok2)}개 열 "
                f"전부 일치) -- 마스터의 이 항목 정의가 그 회계연도 내내 이 규칙이라는 뜻이다. 앵커 사이 분기 흐름 연속 확인."
                + TAIL)
            cells.append(c)
            print(c["code"], c["item"], c["quarter"], f"{c['value_mn'] / 100:,.2f}억", c["rule"], f"a1 {len(ok1)} a2 {len(ok2)}")
    if not cells:
        raise SystemExit("ABORT: no CAND_BRACKET candidates")
    out = BASE / "manual_round11.json"
    out.write_text(json.dumps({"_note": "round 11: bracket-accepted interim cells", "cells": cells}, ensure_ascii=False, indent=1),
                   encoding="utf-8", newline="\n")
    print("wrote", out, len(cells))


if __name__ == "__main__":
    main()
