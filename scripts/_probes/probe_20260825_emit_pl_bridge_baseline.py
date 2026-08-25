# -*- coding: utf-8 -*-
"""PL_BRIDGE 기지 실패 등재부를 생성한다 (건별 + 분류 + 라우팅).

분류는 `probe_20260825_classify_new_pl_fails.py` / `probe_20260825_csm_amort_cell_provenance.py`
의 실측에 근거한다:
  · basis_mix_csm_amort — 원수CSM상각 셀이 배포본과 viz 에서 갈렸고, 한쪽은 YTD 누계·다른 쪽은
    당분기다. 기타OO손익이 **잔차 plug** 라 잘못된 기준으로 계산되면 항등식이 그만큼 벌어진다.
    (동양생명: 배포본이 깨끗한 YTD 계열 / 에이비엘: 배포본 2024 Q1~Q3 가 2025 Q1~Q3 값과 **완전 동일** = 복사)
  · lob_sum_gap — 보험손익 ≠ ΣLOB. `build_root_masters._zero_other_expense` docstring 이
    "DB손해 2023.2Q resid 6869" 를 partial mis-extract 로 이미 명시하고 있다(기지 결함).
  · sub_leg_gap — 생명장기손익 ≠ 원수+재보험. 하위 leg 미추출.
  · pre_existing — 재조준 전에도 실패하던 것(소스와 무관).

사용: python scripts/_probes/probe_20260825_emit_pl_bridge_baseline.py
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "_gold" / "pl_bridge_baseline.json"

CLASS = {
    # (회사, 분기) -> (분류, 사유, 라우팅)
    ("동양생명", "2024.2Q"): ("basis_mix_csm_amort",
        "배포본 원수CSM상각=129,439(YTD 계열로 깨끗)인데 기타생명장기원수손익 plug 는 "
        "당분기 65,243 기준으로 계산돼 있어 항등식이 64,196 벌어진다. 마스터 쪽 YTD 가 "
        "맞고 plug 를 다시 계산해야 한다.", "parser/ifrs17"),
    ("동양생명", "2024.3Q"): ("basis_mix_csm_amort",
        "위와 같음. Δ=129,438.", "parser/ifrs17"),
    ("에이비엘생명보험", "2023.1Q"): ("basis_mix_csm_amort",
        "배포본 원수CSM상각=22,664 vs viz 3,364. Δ=19,300.", "parser/ifrs17"),
    ("에이비엘생명보험", "2024.1Q"): ("copied_cell",
        "배포본 2024.1Q 원수CSM상각=22,447 인데 이 값은 **2025.1Q 값과 완전 동일**하다. "
        "2024.2Q(44,994)=2025.2Q, 2024.3Q(66,762)=2025.3Q 도 같다 — 연도 통째 복사 지문.",
        "parser/ifrs17"),
    ("에이비엘생명보험", "2024.2Q"): ("copied_cell", "위와 같음(=2025.2Q 값).", "parser/ifrs17"),
    ("에이비엘생명보험", "2024.3Q"): ("copied_cell", "위와 같음(=2025.3Q 값).", "parser/ifrs17"),
    ("케이디비생명보험", "2023.2Q"): ("basis_mix_csm_amort",
        "배포본 23,415 vs viz 12,290. Δ=11,125.", "parser/ifrs17"),
    ("케이디비생명보험", "2023.3Q"): ("basis_mix_csm_amort",
        "배포본 35,250 vs viz 11,835. Δ=23,415 (직전분기 배포본 값과 같다).", "parser/ifrs17"),
    ("DB생명보험", "2023.1Q"): ("lob_sum_gap",
        "보험손익 22,946 vs ΣLOB 27,125 (Δ 4,179). 기타사업비용 미추출로 adj-form 평가 불가.",
        "parser/ifrs17"),
    ("DB손해보험", "2023.2Q"): ("lob_sum_gap",
        "보험손익 971,298 vs ΣLOB 978,167 (Δ 6,869). build_root_masters._zero_other_expense "
        "docstring 이 이 잔차를 partial mis-extract 로 이미 명시 — 기지 결함.", "parser/ifrs17"),
    ("메리츠화재해상보험", "2023.1Q"): ("lob_sum_gap",
        "보험손익 419,537 vs ΣLOB 407,167 (Δ 12,370). 기타영업수익/기타사업비용 미추출.",
        "parser/ifrs17"),
    ("메리츠화재해상보험", "2023.2Q"): ("lob_sum_gap",
        "보험손익 822,607 vs ΣLOB 894,154 (Δ 71,547).", "parser/ifrs17"),
    ("흥국화재", "2025.1Q"): ("lob_sum_gap",
        "보험손익 59,132 vs ΣLOB 64,684 (Δ 5,552 / adj-form Δ 714).", "parser/ifrs17"),
    ("교보라이프플래닛생명보험", "2024.4Q"): ("sub_leg_gap",
        "생명장기손익 -26,016 vs 원수(-17,846)+재보험(-1,908) = -19,754 (Δ -6,261).",
        "parser/ifrs17"),
    ("비엔피파리바카디프생명보험", "2024.4Q"): ("sub_leg_gap",
        "생명장기손익 -13,639 vs 원수+재보험 -3,470 (Δ -10,169).", "parser/ifrs17"),
    ("비엔피파리바카디프생명보험", "2025.4Q"): ("sub_leg_gap",
        "생명장기손익 -24,223 vs 원수+재보험 -14,075 (Δ -10,148).", "parser/ifrs17"),
}

PROMOTE = (
    "승격 조건 — 아래 중 하나라도 충족되면 그 줄을 지우고 RED 로 되돌린다.\n"
    "  (1) parser/ifrs17 가 해당 셀을 정정해 항등식이 닫히면 즉시 그 줄 삭제 (게이트가 "
    "      FIXED? 로 인쇄해 알려준다).\n"
    "  (2) 등재 없이 새로 뜬 실패는 이미 RED 다 — SUMMARY 의 `pl_bridge:...NEW` 가 0 을 "
    "      벗어나면 골든(tests/test_master_tables_golden.py)이 push 를 막는다.\n"
    "  (3) 기한: 2026-10-31. 그때까지 남은 줄은 등재를 갱신하거나 documented exception 으로 "
    "      승격 사유를 다시 쓴다 — 무기한 방치 금지.\n"
    "라우팅: 전건 parser/ifrs17 레인. 발주 티켓 "
    "inbox/parser/20260825T*__validation__MULTI__pl_bridge_deployed_master_defects.md"
)


def main() -> int:
    spec = importlib.util.spec_from_file_location(
        "vmt", ROOT / "scripts" / "validate_master_tables.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    pl = m.load_long(m.PL_PATH)
    buf = io.StringIO()
    with redirect_stdout(buf):
        _, pb_fail, _, _, _ = m._check_pl_bridge(pl)

    entries = {}
    for co, q, label, lhs, diff in pb_fail:
        cls, reason, route = CLASS.get(
            (co, q), ("pre_existing",
                      "재조준 전에도 실패하던 항목(소스 변경과 무관). 기존 잔여 결함.",
                      "parser/ifrs17"))
        entries[f"{co}|{q}|{label}"] = {
            "class": cls, "reason": reason, "route": route,
            "lhs": round(lhs, 1), "diff": round(diff, 1),
            "first_seen": "2026-08-25",
        }

    out = {
        "_what": "validate_master_tables.py PL_BRIDGE 기지 실패 등재부. 2026-08-25 에 PL 축 "
                 "소스를 중간산출물(data/dart/viz/pl_breakdown_master.json)에서 배포본"
                 "(PL_breakdown.json)으로 재조준하면서, 처음 검사 대상이 된 1,307셀에서 드러난 "
                 "실패를 건별로 등재한다. **통째 skip 이 아니다** — 여기 없는 실패는 SUMMARY 의 "
                 "pl_bridge NEW 카운트로 올라가 골든이 push 를 막는다.",
        "_promote": PROMOTE,
        "_counts": {c: sum(1 for v in entries.values() if v["class"] == c)
                    for c in sorted({v["class"] for v in entries.values()})},
        "entries": entries,
    }
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"등재 {len(entries)}건 -> {OUT}")
    for c, n in out["_counts"].items():
        print(f"   {c:26s} {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
