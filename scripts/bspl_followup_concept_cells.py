#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Turn the approved results of bspl_followup_concept_search.py into manual-schema cells (read-only; writes concept_cells.json).

Approval is explicit (APPROVED below), per (company, item, fiscal year), after reading the search report: the label set must be UNIQUE, match every
check of the year exactly (opening column of each interim filing AND, when the year is complete, the closing year-end column), the cell's own prior-year-end
column must match (L1), and the same definition must be the one the master's neighbouring anchors/cells already carry.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")

from bspl_granularity import stage_b as B  # noqa: E402
from bspl_granularity.views import view_all  # noqa: E402

W = ROOT / "data" / "_derived" / "bspl_followup_20261011"
TAIL = " (inbox/parser/20261011T0900Z bspl follow-up, step 5c concept search)"
APPROVED = {("KR1011", 13, 2025): "closing", ("KR1011", 13, 2026): "opening-only (year not complete)"}
NOTE = {("KR1011", 13): ("상각후원가유가증권 + 상각후원가대출채권및기타금융자산 두 줄의 합. 상각후원가예치금 줄(2024.4Q 314백만원·2025.4Q 1,251백만원)은 DART 가 현금및예치금 쪽에 두는 예치금이라 제외한다. "
                          "마스터의 2024.4Q·2025.4Q 연말 칸과 2026.2Q 칸(4,677,761.95백만원)이 모두 이 두 줄의 합과 원 단위까지 같다.")}


def main():
    rep = json.loads((W / "concept_search_report.json").read_text(encoding="utf-8"))
    cells = []
    all_v, anchor, disc, meta = B.load_master()
    for r in rep:
        key = (r["code"], r["item"], r["fiscal_year"])
        if key not in APPROVED or not r.get("cells") or len(r["valid_label_sets"]) != 1:
            continue
        kinds = {(c[1], c[0][5:] if False else None) for c in r["checks"]}
        has_closing = any(c[0].endswith("4Q") and c[1] == 0 for c in r["checks"])
        if APPROVED[key] == "closing":
            assert has_closing, key
        labels = r["valid_label_sets"][0]
        for c in r["cells"]:
            assert c["own_prior_column_ok"] is True, c
            code, item, q = c["key"].split("|")
            item = int(item)
            doc = B.load_tables(code, q)
            t = [x for x in B.pick_tables(doc, "bs_full") if B.table_form(x) == "K"][0]
            unit = t["unit"]
            checks_txt = "; ".join(f"{cq} col{col}→{D} {a:,.2f}" for cq, col, D, a, n in r["checks"])
            cells.append({"code": code, "item": item, "quarter": q, "status": "MANUAL", "calib": "concept_search", "value_mn": c["value_mn"], "rule": f"{item}:{'+'.join(labels)}",
                          "kind": "bs_full", "form": "K", "page": t["page"], "unit": unit, "unit_how": "master", "prec_mn": B.UNIT_PREC[unit], "tol_mn": B.UNIT_TOL[unit],
                          "pdf": doc["pdf"], "sha256": doc["sha256"],
                          "basis": (f"정기경영공시 {q} 재무상태표(8-1 K 구간) p{t['page']} 라인「{'」+「'.join(labels)}」 합 {c['value_mn'] / 100:,.3f}억(단위 {unit}). 정확한 줄 합 탐색 5c: "
                                    f"이 두 줄의 합이 {r['fiscal_year']} 회계연도 모든 연말 대조({checks_txt})에서 마스터 DART 앵커를 원 단위까지 정확히 재현하고(유일한 라벨 조합) 이 공시본 자체의 전기말 열도 같다. "
                                    f"{NOTE[(code, item)]} 표 항등식(자산 = 부채 + 자본) 폐합 확인." + TAIL)})
    (W / "concept_cells.json").write_text(json.dumps({"_note": "step 5c concept-search cells (manual schema)", "cells": cells}, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for c in cells:
        print(c["code"], c["item"], c["quarter"], f"{c['value_mn']:,.3f}", c["rule"], "p", c["page"])
    print(len(cells), "cells")


if __name__ == "__main__":
    main()
