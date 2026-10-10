#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stage the PL items the data-contract gate does NOT let the DISCLOSURE lineage carry (2026-10-11, parser/ifrs17).

validate_data_contract §3d allows only items 1/16/22/23/24 from the disclosure lineage; 17 (투자손익), 20 (영업이익) and
21 (영업외손익) are reference-only.  This script runs the SAME selection as bspl_granularity_pl_candidates.py (own summary PL
column, audit statement exact value, R1 for reinsurers, later comparative where no own filing exists, the in-table identities
영업이익 = 보험손익 + 투자손익 and 세전 = 영업이익 + 영업외손익) for those three items and writes the blank-master cells to a
staging file.  NOTHING is loaded into PL_breakdown.json: validation/owner can load them if the lineage rule is ever relaxed
(the existing staging file data/_derived/pl_disclosure_reference_only_staged_20261008.json is left untouched).

Output: data/_derived/bspl_granularity_20261011/pl_reference_only_staged_20261011.json
  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_granularity_pl_stage_ref.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import pl_stage as P  # noqa: E402
import bspl_granularity_pl_candidates as PC  # noqa: E402

REF = {"투자손익": 17, "영업이익": 20, "영업외손익": 21}
OUT = ROOT / "data" / "_derived" / "bspl_granularity_20261011" / "pl_reference_only_staged_20261011.json"
CODES = PC.TIER2 + PC.REINS + PC.LISTED


def main():
    P.PL_ITEM = {**P.PL_ITEM, **REF}            # the identity checks still need the five loadable rows
    PC.ITEMS = tuple(REF.values())
    PC.KPI_ITEM = {"투자손익": 17, "영업이익": 20}
    plm = PC.load_pl_master()
    cells, held, cnt = {}, [], Counter()
    for code in CODES:
        res = PC.process(code, plm, no_anchor=code in PC.REINS)
        for c in res["candidates"]:
            if c["item"] not in REF.values():
                continue
            cnt[c["status"]] += 1
            if c["status"] == "CAND":
                cells[f"{code}|{c['item']}|{c['quarter']}"] = {
                    "값": round(c["value_mn"], 6), "pdf": c.get("pdf"), "page": c.get("page"), "sha256": c.get("sha256"),
                    "scale": f"원문 {c.get('unit')} -> 백만원", "kind": c.get("kind"), "how": c.get("how"),
                    "pdf_quarter": c.get("pdf_quarter")}
            elif c["status"].startswith("HOLD"):
                held.append(f"{code}|{c['item']}|{c['quarter']}|{c['status']}")
    out = {"_note": ("경영공시 요약 포괄손익계산서(및 연말 감사 재무제표)에서 읽은 PL 항목 17 투자손익 · 20 영업이익 · 21 영업외손익 -- "
                     "validate_data_contract §3d(경영공시 계보는 항목 1/16/22/23/24 만) 때문에 마스터에 싣지 않고 대기. 마스터가 빈 칸인 셀만 담았다. "
                     "validation/owner 가 계보 규칙을 풀면 그대로 싣는다. 선택 규칙 = bspl_granularity_pl_candidates.py 와 동일(자체 요약표 당기 열, "
                     "연말 감사값, 재보사 R1, 자체 공시가 없을 때 후속 공시 전년동기 열, 영업이익=보험손익+투자손익·세전=영업이익+영업외손익 항등식)."),
           "status_counts": dict(cnt), "cells": cells, "held": held}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("status counts:", dict(cnt))
    print("staged cells:", len(cells), "| by item:", dict(Counter(k.split("|")[1] for k in cells)),
          "| by group:", {"unlisted15": sum(1 for k in cells if k.split("|")[0] in PC.TIER2),
                          "reinsurers8": sum(1 for k in cells if k.split("|")[0] in PC.REINS),
                          "listed24": sum(1 for k in cells if k.split("|")[0] in PC.LISTED)})
    print("held:", len(held))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
