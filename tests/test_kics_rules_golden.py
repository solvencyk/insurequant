#!/usr/bin/env python3
"""Golden gate for the K-ICS rule engine (run_validation).

run_validation is 393 lines — a 361-line per-bucket loop applying 14 rules
(1-10, 8_post, 8_life, 19_market, 36_irr) — and it had no unit test at all,
despite being the engine behind the RED count the push gate blocks on.

This pins its output on the live master: it runs the engine over
kics_disclosure.json exactly as scripts/validate_kics_disclosure.py does
(same source_has_breakdown input) and asserts a per-(rule,status) count
matrix plus a hash of the full finding list. No file is written; the engine
is pure. Fast (<1s), so it runs unconditionally.

If the counts legitimately change (a rule fix, new data), regenerate and say
why in the commit:

    python tests/test_kics_rules_golden.py --update
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

GOLDEN = REPO / "tests" / "fixtures" / "kics_rules_golden.json"
MASTER = REPO / "kics_disclosure.json"


def _run() -> dict:
    from solvency.validation.kics_json_rules import run_validation
    from validate_kics_disclosure import _load_tfi_applicability, _scan_breakdown_presence

    records = json.loads(MASTER.read_text(encoding="utf-8"))
    # 게이트와 **같은 부수입력**을 실어야 골든이 게이트를 박제한다. `tfi_applicability` 를
    # 빼면 `47_tier2_census` 의 부재 판정이 전부 UNKNOWN review 로 떨어져, 골든은 게이트가
    # 실제로 내는 RED 를 한 건도 고정하지 못한다(2026-08-22 iter-5 신설).
    report = run_validation(records,
                            source_has_breakdown=_scan_breakdown_presence(records),
                            tfi_applicability=_load_tfi_applicability())
    return report


def _manifest(report: dict) -> dict:
    findings = report["findings"]
    # stable key per finding — (code, quarter, rule, status, diff bucketed)
    rows = []
    for f in findings:
        rows.append([
            f.get("company_code"), f.get("quarter"), str(f.get("rule")),
            f.get("status"),
        ])
    rows.sort(key=lambda r: (str(r[0]), str(r[1]), str(r[2])))
    blob = json.dumps(rows, ensure_ascii=False, sort_keys=True)
    return {
        "sha256": hashlib.sha256(blob.encode("utf-8")).hexdigest(),
        "buckets": report["summary"]["buckets"],
        "findings": report["summary"]["findings"],
        "by_status": report["summary"]["by_status"],
        "by_rule": report["summary"]["by_rule"],
    }


def test_rule_engine_output_matches_golden():
    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    actual = _manifest(_run())
    for k in ("sha256", "buckets", "findings", "by_status", "by_rule"):
        assert expected.get(k) == actual[k], (
            f"run_validation output moved at '{k}':\n"
            f"  expected: {expected.get(k)}\n  actual:   {actual[k]}\n"
            f"If intended, regenerate: python {GOLDEN.name} --update"
        )


def _update() -> int:
    man = _manifest(_run())
    man["_what"] = ("Refactor safety net for run_validation (K-ICS rule engine). "
                    "Captured before the 361-line per-bucket loop was extracted. "
                    "Covers every (code, quarter, rule, status) finding over the live "
                    "kics_disclosure.json. "
                    "2026-08-22 재생성 사유(의도된 산출 변경, 손으로 해시 고치지 않았다): "
                    "① 신규 축 50_tfi_tier_split / 51_tfi_tier2_composition (각 적용전·적용후) "
                    "배선 → findings 10,736 -> 12,688 (+1,952 = 488버킷 x 2룰 x 2컬럼). "
                    "② TIER2_TABLE_ABSENT_INTERMITTENT 를 SKIP -> RED 승격(orchestrator 결정) "
                    "→ RED 32 -> 108 (+76 = 38버킷 x 2컬럼). 데이터는 안 건드렸다. "
                    "2026-08-22 (2차) 재생성 사유 — parser 가 50/51 을 431버킷 백필하자 위 두 "
                    "신규 축이 127칸 RED 로 터졌고, 전수 분해 결과 **데이터 오염 0건 · 전부 룰 "
                    "커버리지 결손**이었다. 룰만 고쳤고 데이터는 이번에도 안 건드렸다: "
                    "③ 51_tfi_tier2_composition 이 형제 룰 3_tier2_composition 의 갈래 "
                    "(CAPPED/UNCAPPED/BOTH/TFI_NA)를 안 쓰고 min(47,48)+49 만 무조건 검사하고 "
                    "있었다 → _tier2_branch 에 target_item 인자를 추가해 **같은 함수를 공유**. "
                    "적용전 RED 67 -> 5 (해소 62 = UNCAPPED 50 + TFI_NA 12). "
                    "④ 50_tfi_tier_split_post 가 TFI 단독 스코프를 전체결합 item1_적용후와 "
                    "비교하고 있었다. 올바른 비교 대상은 TFI 표 자신의 지급여력금액 행(item52)인데 "
                    "마스터에 없고, item1_적용전으로 대신하는 것도 원문에 반증된다(IBK연금 "
                    "FY2026_Q1 p17: 그 합계 행이 857,997 -> 938,740 으로 움직인다). 없는 값을 "
                    "대신 채우지 않고 min/max(item1_전, item1_후) 범위검사로 바꿨다 — item1 이 "
                    "전=후 인 362칸(84%)에서는 범위가 한 점으로 붕괴해 등식과 같은 강도다. "
                    "적용후 RED 60 -> 5, 신규 YELLOW 69(범위만 통과 = item52 발주 대기). "
                    "남은 10칸은 전부 발행사 원본 불일치(5) 또는 확증된 추출결함(교보생명 4 · "
                    "롯데손해 1)이고 raw 로 개별 확인했다. "
                    "※ by_status 가 크게 움직인 것(SKIP 3,953 -> 2,257 · GREEN 7,352 -> 8,758)은 "
                    "내 룰 수정이 아니라 **parser 의 431버킷 백필** 때문이다 — 직전 골든이 백필 "
                    "전에 박제된 상태였다(parser 가 RED=236 을 정상으로 박제하는 것이 옳은지 "
                    "판단이 안 서서 --update 를 미뤄 둔 것이고, 그 판단이 옳았다). findings 총계 "
                    "12,688 은 그대로다 — 룰 개수도 버킷 수도 안 변했고 셀이 채워진 것뿐이다. "
                    "2026-08-22 (3차, iter-5) 재생성 사유 — 데이터는 이번에도 안 건드렸다: "
                    "⑤ 47_tier2_census 의 **전부 부재** 판정을 추론에서 실측으로 교체. 종전 "
                    "기준 TIER2_TABLE_ABSENT_INTERMITTENT(= 같은 회사가 다른 분기엔 공시했나) "
                    "가 틀렸다 — 47/48/49 는 (1)공통적용 경과조치 표의 행이고 TFI 는 해당 "
                    "자본증권이 상환·만기되면 적용이 끝나므로 분기마다 켜졌다 꺼지는 것이 "
                    "정상이다(교보라이프플래닛 FY2023_Q1 MD 는 `보완자본 한도` 3회 + 표 존재, "
                    "FY2023_Q2 이후는 0회). 이제 그 버킷 자신의 TFI 실측값"
                    "(data/_derived/kics_transition_applicability.json)으로 가른다: "
                    "O=RED(추출갭) · X=SKIP(정상 부재) · NA/UNKNOWN/키없음=YELLOW(통과 아님). "
                    "부재 28버킷 x 2컬럼: 30 RED + 26 SKIP -> **2 RED + 26 YELLOW + 28 SKIP**. "
                    "X 를 무조건 면죄부로 쓰지는 않는다 — P(부재|TFI=X)=15/108=13.9% 이고 "
                    "하나손해는 13분기 전부 X 인데 12분기가 표를 인쇄하므로, 같은 회사의 다른 "
                    "TFI=X 분기에 행이 있으면 SKIP 대신 review 로 내린다. "
                    "⑥ 골든·매니페스트 테스트가 게이트와 **같은 부수입력**(tfi_applicability)을 "
                    "싣도록 호출부를 고쳤다. 안 그러면 부재 판정이 전부 UNKNOWN review 로 "
                    "떨어져 골든이 게이트의 RED 를 한 건도 고정하지 못한다. "
                    "blocking RED 81 -> 53. "
                    "2026-08-24 (4차, iter-7) 재생성 사유 — 데이터는 이번에도 안 건드렸다"
                    "(kics_disclosure.json 읽기만 했다). parser iter-10 이 item52/53/54 를 "
                    "1,291셀 적재했고 그 항목을 보는 룰이 하나도 없었다: "
                    "⑦ **축 E 등식 승격.** 50_tfi_tier_split{,_post} 의 비교 대상을 "
                    "item1(헤드라인)/범위검사에서 item52(TFI 표 자신의 지급여력금액 행, "
                    "**같은 표·같은 컬럼**)로 바꿨다. 적용후 YELLOW 70 -> 69칸이 등식으로 "
                    "닫히고, **GREEN 이던 6칸이 RED 로 뒤집혔다** — 카카오페이 5버킷의 "
                    "item52 100배(로더의 ALL_ZERO_TRIVIAL 스케일 단축이 만든 구멍: "
                    "47/48/49/51 이 전부 '-' 라 '스케일 무관'으로 판정했는데 같은 표의 "
                    "item52 는 0 이 아니었다. raw FY2023_Q3 p10 `지급여력금액 119,870` "
                    "백만원인데 마스터 119870) + 삼성화재 2025.3Q 적용후 발행사 자릿수 전치 "
                    "(raw FY2025_Q3 p16 `28,650,195 / 28,605,195`, 같은 표 비율은 "
                    "275.92/275.92 불변이고 각주가 전후 동일이라 씀). item52 결측 버킷에서는 "
                    "종전 폴백이 살고 TFI_TOTAL_ROW_ABSENT 사유로 세어진다. "
                    "⑧ **신규 축 53_tfi_memo_rows{,_post}** (+976 findings). 53/54 는 메모행이라 "
                    "항등식의 항이 아니다(`item51 == min(47,48)+49+item54` 전수 시뮬: 새로 "
                    "닫힘 1 · 새로 깨짐 218) → census(적용전만, 원문에 적용후 칸이 대부분 "
                    "없다) + 부호 + `53+54 <= item51` 포함관계. RED 7(롯데 2026.1Q · 하나생명 "
                    "2025.2Q · 동양생명 2024.1Q·2024.3Q · 푸본현대 2024.3Q 는 행 유실/컬럼 "
                    "오배정, 처브라이프 2023.1Q · 농협생명 2024.3Q 적용후는 원문에 없는 값). "
                    "blocking RED 13 -> 29(신규 18 - NH농협 면제 2). "
                    "2026-08-24 (5차, iter-3) 재생성 사유 — 데이터는 이번에도 안 건드렸다"
                    "(kics_disclosure.json 읽기만 했다). **룰 하나만 바뀌었고 산출은 한 칸만 "
                    "움직였다**: RED 38 -> 37 · GREEN 9,521 -> 9,522, findings 총계 13,664 불변. "
                    "⑨ **item47 스코프 인식.** `item47`(보완자본 한도 적용 전)이 `item49`"
                    "(해약환급금 초과분)를 포함해 인쇄되는 발행사가 있다(원문 대조: 한화생명 "
                    "FY2025_Q2 p18 = 포함 / IBK연금 FY2025_Q3 p16 = 제외). 룰은 제외만 알아서 "
                    "포함 관행 회사에서 한도초과액을 item49 만큼 과대계산했고, 그 값이 "
                    "`2_tier1_bridge` 에 들어가 한화생명 2025.2Q 다리를 −30,095 로 만들었다 — "
                    "그것이 '발행사 모순' 으로 오진돼 owner 판단 면제(VERIFIED_BY_OWNER)까지 "
                    "갔다. 스코프는 회사 하드코딩이 아니라 **그 회사 자신의 결정적 버킷 투표**로 "
                    "정한다(`_tier2_i47_scope_map`). 갈래 이름이 4 -> 6 으로 늘었다"
                    "(I49_IN_I47_CAPPED / I49_IN_I47_UNCAPPED). 전 버킷 시뮬: 새로 닫힘 1 · "
                    "새로 깨짐 0(`scripts/_probes/probe_20260824_findings_snapshot.py` diff). "
                    "부수효과로 BNP카디프 3버킷의 COMPOSITION_NEITHER 잔차가 새 식 기준으로 "
                    "이동했다(−221 -> +14.86 등, status 는 RED 그대로) — 게이트 박제값과 원장을 "
                    "같이 갱신했고 종전 값은 expected_residual_alt_reading 에 남겼다. "
                    "한화생명 면제는 **해제**했다(게이트가 TIER2_EXEMPTION_INERT 로 먼저 "
                    "알려 줬다). blocking RED 0 · 게이트 exit 0. "
                    "2026-08-24 (6차, 면제 재감사 반영) 재생성 사유 — 데이터는 이번에도 안 "
                    "건드렸다(kics_disclosure.json 읽기만 했다). **룰 하나만 바뀌었고 산출은 "
                    "한 칸만 움직였다**: RED 37 -> 36 · GREEN 9,522 -> 9,523, findings 총계 불변. "
                    "⑩ **`한도 적용 전` 행에 한도값이 인쇄된 분기의 한도초과액 복원** "
                    "(`kics_json_rules._tier2_excess_recovered_from_post`). 동양생명 KR0087 "
                    "2025.2Q 는 발행사가 그 행에 한도값(item47 == item48 == 1,210,705백만)을 "
                    "그대로 인쇄해 `max(0, 47−48)` 이 구조적으로 0 이 됐고, 다리가 정확히 "
                    "item12(1,188억)만큼 어긋났다. 종전엔 그것을 '발행사가 자기 각주 주1) 을 "
                    "어겼다' 로 읽어 면제로 등재했는데 **주1) 은 지켜졌고 틀린 것은 우리 룰의 "
                    "item47 해석이었다**(2026-08-24 재감사 판정 OUR_RULE_DEFECT). 참 한도초과는 "
                    "같은 표 적용후 컬럼에서 되짚어진다: promo = item2후 − item2전 = 3,445.63 · "
                    "debt_post = item51후 − item49후 = 9,849.42 → debt_true 13,295.05 → "
                    "한도초과 1,188.00, 다리 잔차 0.00. 가드 5개(중복행·승격액>0·적용후 미구속·"
                    "한도 구속·인쇄 보완자본 재현) 전부 통과할 때만 발동한다. "
                    "전 버킷 시뮬(488): 발동 1 · **해결 1 · 파손 0 · 무변동 0** "
                    "(`scripts/_probes/probe_20260824_v_kr0087_sim.py`). 같은 발행사 2025.4Q·"
                    "2026.1Q 는 47 > 48 을 정상 인쇄해 가드에서 걸러지고 현행대로 닫힌다"
                    "(잔차 0.24 · 0.38). 되짚기 식 자체의 독립 검증: 중복행 가드를 빼면 item47 이 "
                    "정상 인쇄된 5버킷(KR0076 2023.1Q · KR0104 2024.4Q~2025.3Q)에서도 발동하는데 "
                    "되짚은 초과액이 인쇄값 기반 초과액과 **0.41 이내로 일치**한다. "
                    "KR0087 2025.2Q `2_tier1_bridge` 면제는 해제했고 원장 `contradicted_pins` "
                    "tripwire 로 재등재를 막는다. blocking RED 0 · 게이트 exit 0.")
    GOLDEN.write_text(json.dumps(man, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"updated {GOLDEN}: {man['findings']} findings / {man['buckets']} buckets")
    print(f"  by_status: {man['by_status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_update() if "--update" in sys.argv else 0)
