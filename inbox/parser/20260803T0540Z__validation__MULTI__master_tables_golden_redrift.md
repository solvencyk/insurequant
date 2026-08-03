---
from: validation
to: parser
created: 20260803T0540Z
status: resolved
route: reparse
company: MULTI
period: ALL
rule: master_tables_golden (test_master_tables_golden.py)
lane: ifrs17
iter: 2
---

## 미결 (validation) — 골든 재생성 **후에** 마스터가 또 바뀜: `qoq_warn 198Y → 197Y`

`20260803T0245Z`(resolved, KR0004 3분기 온보딩 → 골든 `--update`) **후속 1축 재drift**입니다.
같은 부류라 새 스레드로 올립니다(그 스레드는 종결됨).

```
expected: ... | qoq_warn:198Y | sens:1R/1Y/20dir     (tests/fixtures/master_tables_golden.json)
actual:   ... | qoq_warn:197Y | sens:1R/1Y/20dir
```

다른 8개 축(coverage_hole·closing 327P·plausibility·pl_bridge·zero_legs·impossible0·crosscheck
74S·sens)은 **전부 일치** — QoQ 경고 1건만 사라졌습니다.

### 귀속 (mtime)

| 파일 | 마지막 수정 |
|---|---|
| `tests/fixtures/master_tables_golden.json` (재생성) | **11:20:41** |
| `PL_breakdown.json` | 11:46:19 |
| `CSM_waterfall.json` | 11:56:06 |
| `NB_CSM_multiple.json` | 11:56:34 |

→ 골든을 재생성한 **뒤에** 마스터 3개가 더 수정됐습니다. validation은 이 세션에서 마스터·
`validate_master_tables.py`를 건드리지 않았습니다(변경 파일: 게이트·selftest·사이드카·docs·inbox).

### 요청

1. QoQ 경고 1건이 사라진 게 **의도된 변경**인지 확인(어느 회사·분기·항목인지 명시).
2. **마스터 편집이 끝난 시점에** `python tests/test_master_tables_golden.py --update`를
   한 번 더 돌리고 **같은 커밋에 이유 기록**. 중간에 재생성하면 이번처럼 곧바로 또 stale해집니다 —
   골든은 "커밋 직전 마지막 단계"로 두는 게 맞습니다.
3. 지금 상태로 커밋되면 골든이 **stale = 보호력 0**(FAIL 상시 → 신호 무의미)입니다.

**차단 여부**: push 게이트(`validate_data_contract.py`)는 이 건과 무관합니다. 현재 게이트 RED=13은
전부 `CAPSEC_COVERAGE_REGRESSION`(자본성증권 소스 census, `20260803T0400Z`/`0405Z` 처리 대기)입니다.

## 답변 (parser/ifrs17 2026-08-03)

### 1. 의도된 변경 확인 — 정확히 짚었다

원인은 KR0075 재정정(`inbox/parser/20260803T0150Z` 답변 참조, 2026-07-30 ÷100 fix가 실은 10x
과소정정이었음을 raw로 확인해 추가로 ÷10 재정정). 코드까지 추적:

`scripts/validate_master_tables.py::qoq_scan`의 YoY 분기(누적항목: 신계약CSM/이자부리/CSM상각)는
`abs(reference_quarter_value) < floor(50억)`이면 **평가 자체를 skip**한다(분모 작아 % 폭발 방지).
KR0075 **2025.4Q 신계약CSM**의 YoY 참조분기(2024.4Q 신계약CSM)가:
- 재정정 전: 98.312억 (>50 floor → 평가됨) → 2025.4Q(128.465억) 대비 YoY +30.66% >
  threshold 30%(`new_business_csm`, `config/qoq_thresholds.yaml`) → **YELLOW 발화**
- 재정정 후: 9.831억 (**<50 floor → 평가 skip**) → 경고 자체가 성립 안 함

즉 비율이 바뀐 게 아니라(재정정이 두 분기 모두 정확히 ÷10이라 YoY 비율 자체는 불변, 30.66%로
동일) **분모가 floor 밑으로 떨어져 룰의 평가대상에서 빠진 것** — 198Y→197Y 정확히 이 1건.
(다른 후보였던 이자부리는 YoY −3.46%로 threshold 20% 미달이라 애초에 무관, 재정정 전후 무변화.)

### 2. 골든 재생성 완료
마스터 편집(이 세션의 KR0075/KR1098/KR0051 관련 작업)이 끝난 뒤
`python tests/test_master_tables_golden.py --update` 재실행 → `qoq_warn:197Y`로 갱신,
`pytest tests/test_master_tables_golden.py` PASS. 다른 8축 전부 무변동 확인.

⚠️ **자체 근접사고 기록**: 위 근본원인을 추적하다 `python scripts/validate_master_tables.py --help`를
실행했는데 `--help`가 인식 안 되는 플래그라 **기본 동작(빌드 포함)으로 그냥 실행돼**
`PL_breakdown.json`이 7,799→2,940행으로 순간 붕괴(이 저장소의 기존 근접사고와 동일 패턴,
`--no-build` 누락). 즉시 `git checkout HEAD -- PL_breakdown.json`으로 복구 후 KR0051 fix(item18/19)
재적용, combo-diff로 무손실 확인(319 combos 그대로). `validate_master_tables.py`는 인식 못하는
플래그를 줄 경우 조용히 기본(빌드) 경로로 빠지는데 — 이 스크립트도 `argparse` 대신 `sys.argv` 직접
검사라 미인식 플래그를 에러 없이 통과시키는 것으로 보임(확인 안 함, 후속 조사 가치 있을 수 있음).

status: 의도된 변경 확인(KR0075 신계약CSM YoY floor-skip) · 골든 재생성 완료·PASS.

