# -*- coding: utf-8 -*-
"""data/_gold/pl_bridge_baseline.json 갱신 -- 이번 라운드에 고친 10건 삭제, 조사했지만
못 고친 6건에 조사노트 추가.

사용: C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/update_20260825_pl_bridge_baseline.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")

PATH = ROOT / "data" / "_gold" / "pl_bridge_baseline.json"
TICKET = ("inbox/parser/20260825T1120Z__validation__MULTI__"
          "pl_bridge_deployed_master_defects.md")

# 이번 라운드에 완전히 고쳐 등식이 닫힌 10건 -- 등재부에서 삭제.
FIXED_KEYS = [
    "에이비엘생명보험|2023.1Q|생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수",
    "에이비엘생명보험|2024.1Q|생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수",
    "에이비엘생명보험|2024.2Q|생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수",
    "에이비엘생명보험|2024.3Q|생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수",
    "동양생명|2024.2Q|생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수",
    "동양생명|2024.3Q|생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수",
    "케이디비생명보험|2023.2Q|생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수",
    "케이디비생명보험|2023.3Q|생명장기원수손익 = 원수CSM상각+원수RA+원수예실차+기타원수",
    "메리츠화재해상보험|2023.1Q|보험손익(dual)",
    "메리츠화재해상보험|2023.2Q|보험손익(dual)",
]

# 조사했지만 이번 라운드에 못 닫은 6건 -- reason/lhs/diff 갱신 + 조사노트 추가.
UPDATED = {
    "DB생명보험|2023.1Q|보험손익(dual)": {
        "class": "issuer_structural_residual",
        "reason": (
            "item16(기타사업비용) raw 보강(2,577.05백만, '(3) 기타사업비' 라벨변형) 후에도 "
            "잔차 1,601.9 = **정확히 item8(생명장기재보험손익)**. DB생명 원표 '(2) 요약포괄손익"
            "계산서'에서 '1. 보험손익'(=item1)이 '2. 재보험손익'(=item8)과 별도 최상위 항목으로 "
            "병기돼 있어(56행 표, 0/1/5행 참조) 이 회사 '보험손익' 캡션 자체가 재보험을 구조적으로 "
            "제외한다 — 원수만의 결과다. 우리 dual-form 룰(bare=item2+13+14, item2=item3+item8)은 "
            "재보험 포함을 가정해 이 회사엔 구조적으로 안 맞는다. 회사별 예외 룰(예: 메리츠/DB손해 "
            "등 3개사서 시뮬레이션한 결과 'item3 단독' 후보를 추가하면 2개사는 더 나빠져 범용 룰 "
            "변경은 보류했다 — probe_20260825_lobsumgap_items.py)."
        ),
        "route": "parser/ifrs17",
        "lhs": 22946.4,
        "diff": 1601.9,
        "first_seen": "2026-08-25",
        "investigated_20260825": (
            f"{TICKET}: item16 raw 확정(2577.053702, fix_20260825_lobsumgap_item16.py 로 "
            "override 반영, master 값 갱신됨). item1 은 raw 라벨과 정확 일치라 변경 안 함. "
            "잔차가 item8 과 정확히 일치함을 확인해 구조적 배제로 결론 — 통째 skip 아니고 "
            "숫자로 확증."
        ),
    },
    "DB손해보험|2023.2Q|보험손익(dual)": {
        "class": "lob_sum_gap",
        "reason": (
            "보험손익 971,298 vs ΣLOB 978,167 (Δ 6,869). build_root_masters._zero_other_expense "
            "docstring 이 이 잔차를 partial mis-extract 로 이미 명시 — 기지 결함."
        ),
        "route": "parser/ifrs17",
        "lhs": 971297.9,
        "diff": 6869.1,
        "first_seen": "2026-08-25",
        "investigated_20260825": (
            f"{TICKET}: raw '(2) 요약(연결)포괄손익계산서' 재확인(probe_20260825_"
            "lobsumgap_raw_search.py) — item16(기타사업비용, 70,375.73백만)은 '3.기타사업비용' "
            "라벨과 정확 일치해 **이미 올바르게 추출돼 있다.** 그런데 그 값을 bare 에서 빼면 "
            "잔차가 6,869→63,507 로 오히려 악화된다(adj=907,791 vs bo=971,298). 즉 item16 을 "
            "이 등식에 적용하면 안 되는데(생명장기 LOB 원가에 이미 포함돼 이중차감 가능성) "
            "'(10)기타보험영업수익/비용' '(7)기타재보험수익/비용' 등 후보 sub-item 어느 조합도 "
            "6,869.09 를 정확히 재현하지 못했다. 코드 주석의 'partial mis-extract' 진단을 "
            "재확인만 하고 새 raw 근거를 못 찾아 원인 미확정으로 남긴다 — 다음 세션 재조사 필요."
        ),
    },
    "흥국화재|2025.1Q|보험손익(dual)": {
        "class": "lob_sum_gap",
        "reason": "보험손익 59,132 vs ΣLOB 64,684 (Δ 5,552 / adj-form Δ 714).",
        "route": "parser/ifrs17",
        "lhs": 59132.0,
        "diff": -714.0,
        "first_seen": "2026-08-25",
        "investigated_20260825": (
            f"{TICKET}: raw '(단위 : 백만원)' 표(probe_20260825_lobsumgap_raw_search.py) 확인 "
            "— item16(기타사업비용=6,266)은 '(3)기타사업비용' 라벨과 정확 일치, 이미 올바르게 "
            "추출됨(adj 후보가 bare 보다 더 가까움: 714 vs 5,552, 게이트도 adj 를 채택). 잔차 714 "
            "를 설명할 추가 '기타' 항목을 이 표에서 못 찾았다 — 보험손익 섹션엔 (3)기타사업비용 "
            "외에 다른 기타 라인이 없다. 허용오차(200)를 살짝 넘는 작은 잔차로 cross-note 반올림 "
            "가능성이 높지만 확증하지 못해 그대로 둔다."
        ),
    },
    "교보라이프플래닛생명보험|2024.4Q|생명장기손익 = 원수손익+재보험손익": {
        "class": "sub_leg_gap",
        "reason": "생명장기손익 -26,016 vs 원수(-17,846)+재보험(-1,908) = -19,754 (Δ -6,261.4).",
        "route": "parser/ifrs17",
        "lhs": -26015.5,
        "diff": 6261.4,
        "first_seen": "2026-08-25",
        "investigated_20260825": (
            f"{TICKET}: PAA(보험료배분접근법) 노트 캡션 4건 발견(16-4/16-5, 15-4/15-5, "
            "probe_20260825_subleg_raw_check.py)했으나 해당 표가 파서에서 rows=1/빈 nums 로 "
            "쪼개져 있어(멀티페이지 표 분리 아티팩트 추정) 실제 수치를 못 읽었다. 같은 회사 "
            "2025.4Q 는 이 등식이 정확히 닫힌다(diff=0.000, probe_20260825_dy_kdb_full_items.py "
            "류 점검) — 스키마 자체는 이 회사에 유효하므로 구조적 배제가 아니라 **2024.4Q "
            "한정 추출 결함**일 가능성이 높다. 이번 라운드엔 PAA 표 파싱 복구가 필요해 못 고쳤다 "
            "— 후속 필요(멀티페이지 표 분리 로직 점검)."
        ),
    },
    "비엔피파리바카디프생명보험|2024.4Q|생명장기손익 = 원수손익+재보험손익": {
        "class": "sub_leg_gap",
        "reason": "생명장기손익 -13,639 vs 원수+재보험 -3,470 (Δ -10,169.1).",
        "route": "parser/ifrs17",
        "lhs": -13639.3,
        "diff": 10169.1,
        "first_seen": "2026-08-25",
        "investigated_20260825": (
            f"{TICKET}: item3(-1,833.58)·item8(-1,636.55) 둘 다 raw 보험계약부채 변동표의 "
            "'보험서비스결과 합계'(각각 1,833.581/−1,636.545, 단위환산 후 부호주의 — 직접은 "
            "부채감소=이익이라 부호반전, 재보험은 그대로)와 0.01 이내로 교차검증됐다 "
            "(probe_20260825_subleg_raw_check.py). 즉 item3+item8 은 신뢰할 수 있다. PAA 캡션은 "
            "0건 — 2024.4Q·2025.4Q 공통으로 Δ≈10,150~10,169(연도 간 크기 유사)라 우연한 추출 "
            "오류가 아니라 **item2(Tier1 헤드라인)와 item3+8(Tier2 CSM/RA 노트) 사이 포착범위가 "
            "다른 구조적 성분**이 있는 것으로 보이나 그 성분을 raw 에서 특정하지 못했다. "
            "item1/2 자체가 틀렸을 가능성도 배제 못 함 — 후속 필요."
        ),
    },
    "비엔피파리바카디프생명보험|2025.4Q|생명장기손익 = 원수손익+재보험손익": {
        "class": "sub_leg_gap",
        "reason": "생명장기손익 -24,223 vs 원수+재보험 -14,075 (Δ -10,147.6).",
        "route": "parser/ifrs17",
        "lhs": -24222.9,
        "diff": 10147.6,
        "first_seen": "2026-08-25",
        "investigated_20260825": (
            f"{TICKET}: 2024.4Q 와 동일 조사·동일 결론(위 항목 참조) — item3/item8 교차검증 "
            "완료, Δ 크기가 전년(10,169.1)과 유사(10,147.6)해 같은 구조적 원인으로 추정되나 "
            "미특정. 후속 필요."
        ),
    },
}


def main() -> int:
    data = json.loads(PATH.read_text(encoding="utf-8"))
    entries = data["entries"]

    removed = 0
    for k in FIXED_KEYS:
        if k in entries:
            del entries[k]
            removed += 1
        else:
            print(f"  WARN: expected fixed key not found: {k}")

    updated = 0
    for k, new_entry in UPDATED.items():
        if k not in entries:
            print(f"  WARN: expected existing key not found for update: {k}")
            continue
        entries[k] = new_entry
        updated += 1

    # recompute _counts
    counts = {}
    for v in entries.values():
        counts[v["class"]] = counts.get(v["class"], 0) + 1
    data["_counts"] = dict(sorted(counts.items()))

    data["_round_20260825b"] = (
        f"{TICKET} 처리: 16건 중 10건 완전히 고쳐 등재 삭제(copied_cell 3 전부 + "
        "basis_mix_csm_amort 5 전부 + lob_sum_gap 중 메리츠화재 2건). 나머지 6건은 raw 로 "
        "재조사해 조사노트를 남기되 등식을 못 닫아 등재 유지(class 는 실태에 맞게 조정: "
        "DB생명 2023.1Q 는 item16 부분보강 후 잔차가 item8 과 정확일치해 issuer_structural_"
        "residual 로 재분류). pre_existing 10건은 이번 티켓 범위 밖(재조준과 무관, 발주문 "
        "'나머지 13건' 계산에서 제외됨)이라 손대지 않음."
    )

    print(f"removed {removed} entries, updated {updated} entries")
    print(f"new _counts: {data['_counts']}")
    total = len(entries)
    print(f"total entries now: {total}")

    PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {PATH}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
