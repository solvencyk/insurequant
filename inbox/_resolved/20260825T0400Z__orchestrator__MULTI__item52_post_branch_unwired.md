---
from: orchestrator
to: parser
created: 20260825T0400Z
status: resolved
route: reparse
company: MULTI
period: MULTI
rule: 50_tfi_tier_split
lane: kics
iter: 1
---

## 미결 — item52 데이터는 들어왔는데 게이트 **적용후 경로**가 그걸 안 쓴다

2026-08-25 에 `item52`(경과조치표 자신의 지급여력금액 행)를 30버킷 적재했다.
담당 에이전트가 **문서 작성 전에 watchdog stall 로 죽어서** 오케스트레이터가 트리를
검증하고 기록만 대신 남겼다. 적재 자체는 정상이고 게이트도 exit 0 이다.

### 실측 (오케스트레이터, 2026-08-25)

```
item52 행 428 -> 458 (신규 30행)
item52 값(적용전) 458/458 · 값_적용후 458/458   <- 두 컬럼 다 채워져 있다
validate_kics_disclosure.py exit 0 · blocking RED=0
```

그런데 게이트 리포트는 이렇게 인쇄한다:

```
[적용전] TFI표 tier 분할 item50+item51 (item52 있으면 등식 · 없으면 적용전=item1 폴백/적용후=범위검사)
      RED=1 YELLOW=1 GREEN=448 SKIP=38
[적용후] TFI표 tier 분할 item50+item51 (item52 있으면 등식 · 없으면 ...)
      RED=0 YELLOW=1 GREEN=449 SKIP=38
      ※ 등식 아님 — item52(TFI표 자신의 지급여력금액 행) 결측이라 범위검사.
        YELLOW = 약한 검사만 통과, parser 발주 대기
```

**축 라벨과 적용전 분기만 바뀌었고 적용후 분기가 안 바뀐 반쪽 변경이다.**
데이터가 458/458 로 있는데 "결측이라 범위검사" 라고 적고 있으니, 그대로 두면
다음 세션이 "item52 는 아직 안 실렸다" 로 읽는다. 이 저장소가 반복해서 데인
**"메시지는 X 라는데 코드는 Y"** 유형이다.

### 부탁

1. `scripts/validate_kics_disclosure.py` 의 `50_tfi_tier_split` **적용후 분기**가
   item52 를 쓰도록 배선해서 범위검사 -> 항등식 검산으로 승격해라.
   적용전 분기가 이미 그렇게 돼 있으니 그 코드를 따라가면 된다.
2. **전 버킷 시뮬레이션을 먼저** 돌려 닫힘/깨짐 양방향을 재라(해결 N / 파손 M / 무변동).
   승격하면 새 RED 가 뜰 수 있다 — 뜨면 전건 열거하고 발행사 모순인지 우리 추출 오류인지
   판정해라. **판정 안 된 RED 를 남긴 채 닫지 마라.**
3. item52 가 아직 없는 버킷(SKIP 38 중 일부)이 원문에도 없는 것인지 census 로 확인해라.
   원문에 있는데 안 실린 게 또 있으면 그것도 적재해라.
4. 승격 후에도 `validate_kics_disclosure.py` exit 0 유지 · 골든은 `--update` + 사유 기록.

### 하지 말 것

- 리포트 문구만 고쳐서 "결측" 표시를 지우지 마라. **코드가 실제로 item52 를 쓰게 하는 것**이
  이 티켓이다. 문구만 고치면 정확히 같은 함정을 한 겹 더 쌓는 것이다.
- 허용오차를 건드리지 마라.
- 마스터 통째 read-modify-write 금지 — 셀 단위로.
- `git commit`·`git push` 금지.

## 답변 (parser-kics, 2026-08-25)

### 가설 반증 — 이 티켓의 전제 자체가 틀렸다

**부탁 1번("적용후 분기가 item52를 안 쓴다")은 사실이 아니었다.** `src/solvency/validation/
kics_json_rules.py` `_validate_tfi_tier_rows()` L1648을 읽으면:

```python
for post in (False, True):
    ...
    elif src.get(TFI_TOTAL_ITEM) is not None:   # L1648 — post 무관, item52 있으면 무조건 이 분기
        i52 = src[TFI_TOTAL_ITEM]
        f = _check_numeric(bucket, rule_e, i50 + i51, i52, eff_tol)
```

`post` 분기(`for post in (False, True)`) 자체가 이 `elif` **앞에서 이미 통합**돼 있다 —
`src = bucket.values_post if post else bucket.values` 이므로 item52 등식은 적용전·적용후
**둘 다 처음부터 같은 코드 경로**를 탄다. "적용전만 배선되고 적용후는 안 됐다"는 애초에
코드 구조상 불가능한 상태였다.

**실제로 깨진 것은 다른 것이었다.** 변이시험으로 실측(`scripts/_probes/
probe_20260825_item1_post_coverage.py`):

```
[양성대조군] item1[값](적용전) 488칸 흔듦 -> 변화 976건   (하니스 정상 확인)
[본시험]     item1[값_적용후]   488칸 흔듦 -> 변화 0건    (매니페스트가 잡은 것과 일치)
[분해] 50/51 둘 다 있는(적용후) 버킷 450개 중 item52_적용후 있음 450 / 없음 0
[분해] 50/51 둘 다 있는(적용전) 버킷 450개 중 item52_적용전 있음 450 / 없음 0
```

item52가 30버킷 더 실리면서(428→458) **item50/51이 둘 다 있는 450버킷 전부가 item52도
갖게 됐다.** `50_tfi_tier_split_post`가 item52 결측일 때만 쓰던 폴백(`else` 분기,
item1_적용후를 범위 상한으로 참조)이 이제 **0/450 버킷에서만** 살아있다 — 즉 사실상 죽은
코드가 됐다. 그런데 그 폴백이 `run_validation()` 안에서 **item1의 post 컬럼을 보는 유일한
코드**였다(rule "7"은 `bucket.get(1)`, 즉 pre만 봄 — `L2159`). **값을 채운 것(item52
100% 커버리지 달성)이 역설적으로 item1_적용후의 커버리지를 지운 것**이 진짜 원인이다.
티켓의 "가설"(적용후 분기 미배선)과는 다른 메커니즘이지만 결과(item1_적용후 무방비)는
정확히 티켓이 지적한 그 증상이다.

### 복원 방식 — (a)가 아니라 (b): `7_post` 신설

(a) "50_tfi_tier_split 적용후를 item52로 승격"은 위에서 보였듯 **이미 돼 있어서 할 일이
없다.** 대신 (b) — item1_적용후를 지키는 **독립된 축**을 새로 만들었다. 기존 `8_post`
(item28후=item2후/item14후×100)와 정확히 대칭인 `7_post`(item27후=item1후/item14후×100)를
`_validate_transition_basic()`에 추가했다(same-basis 가드·동적허용오차 로직까지 동일하게
복붙). `50_tfi_tier_split_post`는 건드리지 않았다 — item52 등식이 이미 그보다 강한 검사라
손댈 이유가 없었다.

### 전 버킷 시뮬레이션 (`scripts/_probes/probe_20260825_7post_before_after.py`)

git HEAD(내 편집 전) 버전과 현재 버전을 **둘 다 임시 모듈로 로드**해 같은 마스터·같은
tfi_applicability로 findings를 대조:

```
공통 (회사,분기,rule) 키 13,664개 중 status 변경 0건   <- 회귀 0, 8_post 포함
7_post 이 아닌데 새로 생긴/사라진 finding key: 0건/0건
7_post 상태분포: GREEN=482 · YELLOW=6 · RED=0 · SKIP=0
```

**해결 488(item1_적용후 전량) · 파손 0 · 무변동 13,664.** 새 RED는 0건이라 판정할 대상이
없다. YELLOW 6건은 전부 소액분모(카카오페이 등) 반올림 — 그중 KR1098 2023.4Q
(expected=4870.0 actual=4777.18)는 코드에 이미 인용된 "카카오 2023.4Q item14후=20 →
974/20=4870 vs 공시4777" 사례와 정확히 일치하는, 기존에도 알려진 패턴이다(신규 결함
아님). `8_post` 자체 findings도 0건 변경으로 자기참조 실수 없음을 확인.

### item52 census (부탁 3번)

`scripts/_probes/probe_20260825_tfi_skip38_census.py`로 SKIP 38버킷 분해:
- `TFI_TIER_ROWS_ABSENT_NO_TABLE` 28 — 13개가 미래에셋생명(KR0079, 이미 `task_66ee6d43`로
  스핀오프된 item47-54 전수감사 대상, TODO 15/16회차에 기록됨), 11개가 교보라이프플래닛
  (KR1010, 룰 docstring L1611 자체가 "FY2023_Q2 이후 표 자체가 사라진다"고 이미 실측해 둔
  회사) — 둘 다 **이미 알려진, 이미 스코프 밖으로 분류된** 사례.
- `TFI_TIER_ROWS_ABSENT_BACKLOG` 10 — KB손해·신한이지손해·교보생명·미래에셋생명·코리안리.
  이건 47/48/49는 있는데 50/51 자체가 안 실린, **item52와 무관한 사전 존재 백로그**다
  (룰 docstring L1614-1616: "RED 승격은 하지 않았다... orchestrator/owner 판단 사항").

즉 **50/51이 있는데 item52만 빠진 버킷은 0개**(위 분해에서 확인) — 이번 30버킷 적재로
item52 자체의 백필은 이미 끝나 있다. 남은 38 SKIP은 전부 이미 다른 티켓/문서에 추적 중인
사전 이슈라 이번 세션에서 추가로 적재하지 않았다(중복작업 방지).

### 부수 수정 2건

1. **리포트 stale 문구** — `_TIER2_POST_RANGE_ONLY` 노트가 하드코딩이라 item52가
   100% 채워진 뒤에도 "결측이라 범위검사"를 계속 찍고 있었다(이 티켓이 지적한 정확히 그
   증상). `scripts/validate_kics_disclosure.py::_print_tier2_axis_report`가 이제 폴백이
   **이번 실행에서 실제로 몇 칸 탔는지**(`TFI_TOTAL_ROW_ABSENT` 접두 detail 카운트) 세서
   0이면 "전량 등식으로 검사됨"을 찍는다. 코드(item52 등식)를 고치는 대신 문구만 고친
   것이 아니라, 코드는 이미 맞았고 **리포트가 코드를 안 따라가고 있던 것**을 고쳤다.
2. **`tests/test_tfi_memo_rows.py::test_axis_e_fallback_still_exists_for_missing_item52`**
   — 이 테스트가 "라이브 마스터에 item52 결측 버킷이 자연히 존재하는지"를 스캔했는데,
   30버킷 적재로 그런 버킷이 0개가 되며 **내 세션 이전부터 이미 깨져 있었다**(원인은
   이전 세션의 데이터 적재, 내 `7_post` 추가와 무관 — before/after 시뮬레이션이 증명).
   `prepush_check.py`의 고정 테스트 목록(`tests/test_kics_rules_golden.py` 등 8개)에는
   없어서 push를 막지는 않지만, 방치하면 다음 전체 pytest에서 계속 false 회귀로 보인다.
   대표 버킷 하나의 item52를 인위적으로 지우는 변이 테스트로 바꿔 메커니즘 자체는 여전히
   검증하도록 고쳤다(10 passed).

### 게이트·테스트 실측

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_rule_coverage_manifest.py -q
  -> 11 passed in 38.99s   (test_item_coverage_matches_manifest 포함)

C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_disclosure.py
  -> exit 0 · Status counts: RED=36 YELLOW=1524 GREEN=10006 SKIP=2586 (RED 36은 전부 기존
     documented exception, blocking RED=0, 내 변경 전과 동일)

C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_kics_rules_golden.py -q
  -> 1 passed (findings 13,664 -> 14,152 = +488, 전부 신규 7_post. --update 완료, 사유는
     tests/test_kics_rules_golden.py 의 "2026-08-25 (7차)" 문단)

C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/prepush_check.py   (실측 완료, 450초)
  -> K-ICS RULE GATE: exit=0 (clear)
  -> DOMAIN GATES: pass (csm_continuity·kics_rate_sensitivity·nb_csm_multiple·csm_waterfall 전부 exit=0)
  -> INBOX HYGIENE: 기계적위반=0
  -> OFFLINE TESTS(FULL_COVERAGE_SWEEP=1, 8개 파일+tests/unit/): 176 passed, 1 skipped, 0 failed (450.34s)
     — test_rule_coverage_manifest.py 가 이 안에 포함, 전수(48칸×게이트) 스윕까지 통과
  -> DATA CONTRACT GATE SUMMARY: RED=2 (하나생명보험 2023.4Q PL_CSM_AMORT_VS_WATERFALL ·
     하나생명보험 2025.4Q CSM_CONTINUITY_FY_BOUNDARY — 둘 다 [PL_breakdown]/[CSM_waterfall],
     ifrs17 레인 소관, K-ICS/item52/item1과 무관)
  -> PRE-PUSH VERDICT: gate RED=2 · K-ICS rule gate=clear · domain gates=pass ·
     inbox 기계적위반=0 · offline tests=pass → **BLOCKED**(exit 2) — 유일한 차단 사유가
     위 data-contract RED 2건(ifrs17 레인 소관)이다. 내 몫(K-ICS 게이트·offline tests·
     domain gates)은 전부 clear/pass 로 실측 확인했다.
```

kics_disclosure.json은 이번 세션에서 **한 바이트도 안 건드렸다**(git diff 0) — 코드
5파일(`kics_json_rules.py`·`validate_kics_disclosure.py`·`test_rule_coverage_manifest.py`·
`test_kics_rules_golden.py`(+golden fixture)·`test_tfi_memo_rows.py`)만 변경. xlsx sync는
불필요(`sync_master_xlsx_sheet.py "K-ICS공시" --dry-run` → 변경 0, 이미 최신).

status: resolved → `_resolved/` 이동 (내 몫은 자기완결 확인 완료. 전체 prepush verdict가
ifrs17 쪽 2건 때문에 아직 BLOCKED라면 그건 별도 진행 중인 다른 티켓 소관).
