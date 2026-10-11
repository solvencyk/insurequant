#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3: proposal / evidence files for the owner and validation (nothing is written to any master).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_make_proposals.py

Writes into data/_derived/bspl_apply_20261011/:
  proposed_pl_kr0008_2023.2Q_dart_basis.json      삼성화재 2023.2Q 항목 1·15·16 을 DART 별도 포괄손익계산서 기준으로 맞추자는 제안(기존 칸 변경이라 적용 안 함)
  proposed_gold_overlay_pl_20261011.json          이번 라운드에서 PL 마스터에 직접 고친 칸(A1 1 + A2 36) -- PL 은 gold overlay(data/_gold/user_pl_cells.json)에 안 올라 있어
                                                  build_pl 재실행 시 되돌아간다는 점과 등재 후보 목록
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.stdout.reconfigure(encoding="utf-8")
D = ROOT / "data" / "_derived" / "bspl_apply_20261011"


def main():
    # ---------------- KR0008 DART-basis proposal ----------------
    pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    cur = {(r["원보험사코드"], str(r["항목번호"]), r["공시분기"]): r.get("값") for r in pl}
    assert cur[("KR0008", "16", "2023.2Q")] == 172900.0 and cur.get(("KR0008", "1", "2023.2Q")) is None
    prop = {
        "_what": "PROPOSAL ONLY (not applied; item 16 is an existing cell and the change moves item 1/15/16 together): 삼성화재 KR0008 PL 2023.2Q 를 DART 별도 포괄손익계산서 기준(2023.1Q·3Q 마스터와 같은 기준)으로.",
        "_why_not_applied": ("티켓 A1 은 항목 14 만 정정 대상이었다. 항목 16(기타사업비용) 2023.2Q 마스터 172,900 은 경영공시 업무보고서 기준 값이고 DART 별도 포괄손익계산서의 기타사업비용은 208,279.85 — "
                             "같은 마스터의 2023.1Q(92,608)·2023.3Q(308,198)는 DART 기준이다. 기준이 섞여 항목 1(보험손익 = 다리 합 − 항목 16 − 항목 15)이 pl_bridge 허용(0.1%)을 넘는 +2,565(0.21%) 어긋나 "
                             "2023.2Q 항목 1 이 빈 칸으로 남아 있다. DART 기준으로 맞추면 닫힌다."),
        "evidence": {
            "dart_xml": "data/dart/FY2023_Q2/raw/KR0008_삼성화재해상보험/20230814002808.xml",
            "separate_income_statement_line": 38756,
            "legs_sum_master": {"item2_장기": 953944.0, "item13_자동차": 262747.0, "item14_일반_정정후": 161674.0, "sum": 1378365.0},
            "dart_table_total_row_line_3118": 1378370.0,
            "dart_보험손익_from_statement": "8,009,629.18 - 6,312,628.45 + 217,040.18 - 535,671.77 = 1,378,369.14",
            "dart_기타사업비용": 208279.85,
            "closing": "영업이익 1,569,401.7 - 투자손익 399,312.4 = 1,170,089.3 = 1,378,369.14 - 208,279.85",
        },
        "cells": [
            {"key": "KR0008|1|2023.2Q", "action": "add", "old": None, "new": 1170089.29, "line": "보험손익", "basis": "= 다리 합(DART 별도 보험수익-서비스비용+재보험) 1,378,369.14 - 기타사업비용 208,279.85"},
            {"key": "KR0008|15|2023.2Q", "action": "add", "old": None, "new": 0.0, "line": "기타영업수익", "basis": "2023.1Q·3Q 마스터 0.0 과 같은 관례(DART 별도 포괄손익계산서에 기타영업수익 줄 없음)"},
            {"key": "KR0008|16|2023.2Q", "action": "replace", "old": 172900.0, "new": 208279.85, "line": "기타사업비용", "basis": "DART 별도 포괄손익계산서 2023 반기 누적 기타사업비용"},
        ],
        "after_apply": "항목 1 의 값_당분기·항목 16 의 값_당분기(2Q = 2Q-1Q 92,608 차)와 2023.3Q 항목 16 값_당분기(308,198-208,280)가 다시 계산돼야 한다(build_root_masters._flow_dangi).",
    }
    (D / "proposed_pl_kr0008_2023.2Q_dart_basis.json").write_text(json.dumps(prop, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    # ---------------- gold overlay candidates for the PL cells corrected by hand ----------------
    cells = []
    for sp in ("spec_A1_kr0008.json", "spec_A2_kr0072.json"):
        d = json.loads((D / sp).read_text(encoding="utf-8"))
        for c in d["cells"]:
            kr, it, q = c["key"].split("|")
            cells.append({"key": c["key"], "item": it, "quarter": q, "old": c.get("old"), "new": c["new"], "spec": sp, "created": bool(c.get("create"))})
    out = {
        "_what": "PL 마스터를 이번 라운드에 직접 고친 칸(셀 단위 + guard + 백업). 옛 값이 빌더 산출과 같은 칸이라 `build_pl_breakdown.py`/`build_root_masters.build_pl` 재실행 시 되돌아간다.",
        "_owner_overlay": "owner 수정의 정본은 data/_gold/user_pl_cells.json(빌드 마지막 UPSERT) — 이 파일은 내 쓰기 범위 밖이라 등재하지 않았다. 등재하려면 아래 칸을 그 파일 형식으로 옮기거나(owner), "
                          "근본 수정(KR0072 handler: 3개월/누적 쌍 표에서 누적 열 선택 · KR0008 일반손익 다리: DART 보험종목별 표 합산)을 `scripts/pl_breakdown/companies.py` 에 하는 것이 낫다(PL 골든 `--update` 동반).",
        "n_cells": len(cells), "cells": cells,
    }
    (D / "proposed_gold_overlay_pl_20261011.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("wrote proposed_pl_kr0008_2023.2Q_dart_basis.json; proposed_gold_overlay_pl_20261011.json", len(cells), "cells")


if __name__ == "__main__":
    main()
