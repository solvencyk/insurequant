#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""2026-10-11 round 3 (A2): build the PL correction spec for KDB생명 (KR0072) reinsurance/direct legs (items 5, 6, 9, 10, 11 + plugs 7, 12).

  C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/bspl_apply_make_spec_kr0072.py [out.json]

For every quarter where the master leg differs from the YTD (누적/당기) column of the DART note (bspl_apply_kr0072_legs.read_note + the master's own
formulas, companies._life_build_items), the spec holds the corrected leg; the plugs 7 = 3-(4+5+6) and 12 = 8-(9+10+11) are recomputed from the master's
own items 3, 4, 8 (they are residuals by construction in build_pl_breakdown.assemble).  The pre-change identities are checked first.
Cells whose master value is blank and whose leg is readable (2026.2Q items 9, 10, 12) become fills (old = null).  Read-only except the output spec.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.stdout.reconfigure(encoding="utf-8")
sys.argv = [sys.argv[0]] + sys.argv[1:]
import bspl_apply_kr0072_legs as K  # noqa: E402

CODE = "KR0072"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "data" / "_derived" / "bspl_apply_20261011" / "spec_A2_kr0072.json"
LISTED = {("10", "2023.2Q"), ("10", "2023.3Q"), ("10", "2024.2Q"), ("10", "2024.3Q")}      # the 4 cells of proposed_pl_corrections_kr0072_item10.json
NAME = {5: "원수 위험조정 변동", 6: "원수 예실차", 7: "기타 생명장기 원수손익", 9: "재보험 CSM상각", 10: "재보험 위험조정 변동", 11: "재보험 예실차",
        12: "기타 생명장기 재보험손익"}
ROWLAB = {5: "(2) 위험해제로 인한 비금융위험에 대한 위험조정의 변동 [보험(영업)수익]",
          6: "예상 발생보험금 및 보험서비스비용 [수익 (1)] - 실제 발생보험금 및 보험서비스비용 [비용 (1)]",
          9: "(3) 제공받은 서비스의 보험계약마진 [재보험(영업)비용]",
          10: "(2) 위험해제로 인한 비금융위험에 대한 위험조정의 변동 [재보험(영업)비용]",
          11: "실제 출재보험금 및 보험서비스(재보험)비용 [재보험(영업)수익 (1)] - 예상 출재보험금 및 보험서비스(재보험)비용 [재보험(영업)비용 (1)]"}


def main():
    pl = json.loads((ROOT / "PL_breakdown.json").read_text(encoding="utf-8"))
    mv = {(str(r["항목번호"]), r["공시분기"]): r["값"] for r in pl if r["원보험사코드"] == CODE}
    cells, report = [], []
    for y in (2023, 2024, 2025, 2026):
        for n in (1, 2, 3, 4):
            q = f"{y}.{n}Q"
            base = ROOT / "data" / "dart" / f"FY{y}_Q{n}" / "raw"
            files = sorted(base.glob(f"{CODE}_*/*.xml")) + sorted(base.glob(f"{CODE}_*/xml/*.xml"))
            if not files:
                continue
            best = None
            for f in files:
                d, lay = K.read_note(f)
                if best is None or len(d) > len(best[0]):
                    best = (d, lay, f)
            d, lay, f = best
            ytd = K.legs(d, "ytd")
            if not ytd:
                continue
            pairmode = any(v[0] == "pair" for v in lay.values())
            rcept = f.stem
            lines = {k: v[1] for k, v in lay.items()}
            new = {}
            for it in (5, 6, 9, 10, 11):
                if it not in ytd:
                    continue
                m = mv.get((str(it), q))
                if m is not None and abs(m - ytd[it]) < 0.51:
                    continue                         # already the YTD value
                if m is None and q != "2026.2Q":
                    continue                         # do not fill other blanks here
                new[it] = (m, round(ytd[it], 6))
            if not new:
                continue
            # pre-change identities on the master (plugs must be pure plugs)
            g = lambda k: mv.get((str(k), q))
            id7 = None if None in (g(3), g(4), g(5), g(6), g(7)) else g(7) - (g(3) - (g(4) + g(5) + g(6)))
            id12 = None if None in (g(8), g(9), g(10), g(11), g(12)) else g(12) - (g(8) - (g(9) + g(10) + g(11)))
            legs_new = {k: (new[k][1] if k in new else g(k)) for k in (5, 6, 9, 10, 11)}
            plug7 = None if None in (g(3), g(4), legs_new[5], legs_new[6]) else round(g(3) - (g(4) + legs_new[5] + legs_new[6]), 6)
            plug12 = None if None in (g(8), legs_new[9], legs_new[10], legs_new[11]) else round(g(8) - (legs_new[9] + legs_new[10] + legs_new[11]), 6)
            report.append(f"{q}: legs {{{', '.join(f'{k}: {v[0]} -> {v[1]}' for k, v in sorted(new.items()))}}}; pre-identity 7:{id7} 12:{id12}; plug7 {g(7)} -> {plug7}; plug12 {g(12)} -> {plug12}")
            src = (f"DART {q} 보고서 XML data/dart/FY{y}_Q{n}/raw/{CODE}_*/{rcept}.xml (note table line {sorted(set(lines.values()))}, "
                   f"{'3개월/누적 열 쌍 표' if pairmode else '단일 기간 열 표'}, 백만원)")
            for it, (old, nv) in sorted(new.items()):
                tag = "ticket-listed item-10 cell" if (str(it), q) in LISTED else ("fill (blank in master)" if old is None else "sibling leg of the same defect")
                basis = (f"정정 2026-10-11(round 3, A2, {tag}): 마스터 값 {old} 은 3개월 열(또는 3개월·누적 혼합) 값이다. {src} 의 {ROWLAB[it]} 누적(YTD) 열로 "
                         f"마스터 자신의 산식(companies._life_build_items)을 적용한 값 {nv:,.1f}. 같은 산식이 단일 기간 표(Q1·Q4)의 마스터 값과 전건 일치하고(스크립트 scripts/bspl_apply_kr0072_legs.py), "
                         f"누계 계열이 분기 간 매끄럽다. 항목 {NAME[it]}.")
                cells.append({"key": f"{CODE}|{it}|{q}", "old": old, "new": nv, "basis": basis, "create": False, "item_name": NAME[it]})
            for it, pv, label in ((7, plug7, "3-(4+5+6)"), (12, plug12, "8-(9+10+11)")):
                old = g(it)
                if pv is None or (old is not None and abs(old - pv) < 1e-6):
                    continue
                if it == 7 and not any(k in new for k in (5, 6)):
                    continue
                if it == 12 and not any(k in new for k in (9, 10, 11)):
                    continue
                cells.append({"key": f"{CODE}|{it}|{q}", "old": old, "new": pv,
                              "basis": f"정정 2026-10-11(round 3, A2, 잔차 항목): 항목 {it} 은 build_pl_breakdown.assemble() 의 잔차 {label} 라서 다리(위 5/6/9/10/11)를 누적 열로 바로잡은 뒤 "
                                       f"항목 3·4·8(변경 없음)로 재계산했다. 정정 전 항등식 잔차 {id7 if it == 7 else id12}.",
                              "create": False, "item_name": NAME[it]})
    OUT.write_text(json.dumps({"_what": "A2 KR0072 legs (YTD column) + plugs; ticket-listed cells = item 10 of 2023.2Q/2023.3Q/2024.2Q/2024.3Q", "cells": cells},
                              ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print("\n".join(report))
    print(f"spec cells {len(cells)} -> {OUT}")


if __name__ == "__main__":
    main()
