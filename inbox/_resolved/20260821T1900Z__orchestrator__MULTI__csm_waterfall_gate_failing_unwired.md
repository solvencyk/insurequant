---
from: orchestrator
to: parser
created: 20260821T1900Z
status: open
route: reparse
company: MULTI
period: ALL
rule: CSM_WATERFALL_BALANCE_INCOMPLETE
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

**`scripts/validate_csm_waterfall.py` 가 exit 1 로 실패하고 있는데, 이 게이트를 부르는 곳이
아무 데도 없어서 아무도 몰랐다.**

2026-08-21 에 push 훅에 게이트를 전수 배선하다 발견했다. `scripts/validate_*.py` 8개 중
훅이 부르던 것은 `validate_data_contract` 하나뿐이었고, 나머지를 전수 실행해 보니
**3개는 통과 중인데 미배선**(바로 배선함), **1개는 실패 중인데 미배선**(이 티켓)이었다.

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_csm_waterfall.py
  → exit 1, 3초
  FAIL <회사명>: balance_incomplete:assumption
  → needs_reparse_for_new_business: run run_ifrs17_csm_reconcile_loop.py
```

게이트 자신이 다음 단계까지 알려주고 있다(`run_ifrs17_csm_reconcile_loop.py`). 그 루프가
언젠가부터 안 돌고 있었던 것으로 보인다.

## 부탁 (수신자가 할 일)

1. `balance_incomplete:assumption` 이 걸린 (회사, 분기)를 **전수 열거**해라. 몇 건인지,
   어느 분기에 몰려 있는지부터.
2. 게이트가 지시하는 `run_ifrs17_csm_reconcile_loop.py` 를 돌릴 수 있는 상태인지 확인하고,
   돌려서 닫히는 것과 안 닫히는 것을 나눠라.
3. **안 닫히는 것은 원인을 원문까지 내려가서 적어라.** "재파싱 필요" 로 끝내지 말 것.
4. 게이트가 exit 0 이 되면 알려라 — `tests/test_push_gate_wiring.py` 의 매니페스트에서
   `NOT_A_PUSH_GATE` → `WIRED` 로 옮기고 훅 1c 단계에 넣는다.

## 참고 — 지금은 이 게이트가 push 를 막지 않는다 (일부러)

지금 배선하면 **모든 push 가 막힌다.** 그래서 `tests/test_push_gate_wiring.py` 의
`NOT_A_PUSH_GATE` 에 **사유를 적어서** 등재해 뒀다. 다만 같은 파일의
`test_unwired_gates_still_fail` 이 매 push 마다 이 스크립트를 실제로 돌려서
**"아직도 실패하는지"를 재확인**한다 — 네가 고쳐서 통과시키는 순간 그 테스트가 실패하면서
배선하라고 막는다. 즉 이 티켓을 조용히 묻어둘 수는 없다.

## 하지 말 것

- 게이트 임계를 낮추거나 실패 케이스를 skip 처리해서 exit 0 을 만들지 말 것.
- `build_root_masters.py` 의 `main()` 통짜 실행 금지(PL 절반 파괴 전례). `build_csm` 개별호출
  + combo-diff. `validate_master_tables.py` 는 반드시 `--no-build`.
- `insurequant_master_tables.xlsx` 는 전체 재생성 금지 — `scripts/sync_master_xlsx_sheet.py`
  로 해당 시트만 cherry-pick (2026-08-21 현재 8개 시트 전부 마스터와 0 drift 상태다,
  네가 마스터를 바꾸면 그 시트만 다시 맞춰라).

## 답변 (parser-ifrs17)

### 결론

exit code **1 (아직 0 아님)**. 18건 → **13건**으로 줄었다. `STAGE_PATTERNS["assumption"]`
라벨 갭 2건을 고쳐 6건 중 5건을 완전히 닫았다(1건은 닫히면서 그 아래 깔려있던 **별개의
선재(先在) 결함**이 드러났다). 나머지 13건은 전부 함수·라인 단위로 원인을 규명했지만 이번
세션 범위를 넘는 리팩터가 필요해 미수정으로 남긴다. **`NOT_A_PUSH_GATE` 유지 요청.**

### 1. 전수열거 (수정 전 18건, 8개 회사)

| 유형 | 회사 | 분기(접수연도) | 원인 | 처리 |
|---|---|---|---|---|
| A. 시행일 이전 | 라이나·메트라이프·아이비케이연금·에이아이에이·처브라이프·하나생명(6사) | FY2022(2023년 필링) | IFRS17 시행일(2023-01-01) 이전 — 원문이 가정형("...적용할 경우") 문구거나 아예 무관한 표. **결측 아니라 원천 부재** | 정상, 손대지 않음 |
| B. assumption 라벨 갭 | 라이나생명보험 | FY2023·FY2024·FY2025(2024/2025/2026 필링) | `STAGE_PATTERNS["assumption"]`에 "을" 없이 "...변동분"으로 끝나는 변형 미등재 | **수정 → 2/3 완전 닫힘, 1/3 잔존(원인 별도)** |
| B. assumption 라벨 갭 | 처브라이프생명보험 | FY2023·FY2024·FY2025(2024/2025/2026 필링) | 같은 리스트에 "조정" 대신 "변경" 동사 변형 미등재 | **수정 → 3/3 완전 닫힘** |
| C. 전기열 오선택 | 메트라이프생명보험 | FY2023·FY2024·FY2025(2024/2025/2026 필링) | `_disambiguate_basis_period()` 부분 가드 미비(§4 상세) | 미수정 — 원인규명 |
| D. no_stage_match | 하나생명보험 | FY2023·FY2025(2024/2026 필링) | 표 선택기가 "13-4"형과 다른 블록을 고르는 것으로 추정 | 미수정 — 원인규명 |
| E. 재보험표 오선택 | 에이아이에이생명보험 | FY2025(2026 필링) | 같은 함수, 다른 가드 구멍 | 미수정 — 원인규명 |

### 2. 라이나·처브라이프 assumption 라벨 갭 — 고쳤다

`scripts/viz_build_csm_waterfall.py`의 `STAGE_PATTERNS["assumption"]`에 원문 실측 라벨
2개를 추가했다:

```python
"보험계약마진 조정하는 추정치의 변동"   # 라이나: "을" 조사 없이 "...변동분"으로 끝맺음
"보험계약마진을 변경하는 추정치"        # 처브라이프: "조정" 대신 "변경" 동사
```

각 3개년 raw(`data/dart/extracted/{라이나,처브라이프}생명보험_<rcept>_measurement.json`)에서
동일 라벨이 반복됨을 확인했다(회사별 표 템플릿은 연도가 바뀌어도 안 바뀐다). 순수 추가
(삭제 0)라 combo-diff로 `csm_waterfall.json` 47개 (회사,rcept) 엔트리 중 **정확히 이 6개만**
바뀌었고 나머지 41개는 바이트 단위 무변화임을 확인했다.

결과: 처브라이프 3/3 완전 통과. 라이나는 2/3(FY2024·FY2025 필링) 완전 통과, FY2023 필링
(rcept 20240409003674)은 **`balance_incomplete:assumption` → `balance_fail:residual=
-3439401.61`**로 실패 사유가 바뀌었다 — 회귀가 아니라 **가려져 있던 다른 결함의 노출**이다.
assumption 이 결측이던 동안은 항등식 자체를 못 돌려 안 보이던 문제가, assumption 이
채워지자 잔차로 드러났다. 이 회사 FY2023(첫 IFRS17 연차) 필링만 `공정가치법/수정소급법/
전환이후계약` 3방식 분해 + "계약의 경계 변경 효과"라는 일회성 재작성 행이 섞인 유별나게
복잡한 표 구조를 쓰는데(FY2024·FY2025 필링엔 이 구조가 없다), `find_csm_leaf_cols()`의
열 오프셋 추정이 이 구조에서 깨지는 것으로 보인다(opening 2,208,247 → closing 5,515,548로
1년 만에 2.5배 뛰는 값 자체가 이미 신호). **assumption 라벨 수정과 무관한 별개 결함**이라
이번엔 손대지 않았다.

### 3. `run_ifrs17_csm_reconcile_loop.py` — 이것도 고쳤다 (별건, 인코딩 버그)

`--skip-measurement --waterfall-only`로 공식 진입점을 실행하니 **`UnicodeEncodeError`로
즉시 죽었다**(`sys.stdout.reconfigure` 미적용, Windows cp949 콘솔이 서브프로세스 출력 속
`�` 문자를 못 씀). `.claude/skills/ifrs17-parser/SKILL.md`가 명시하는 바로 그 함정
("cp949 default")인데 이 스크립트만 빠져 있었다. **"루프가 언젠가부터 안 돌고 있었다"는
티켓의 추측이 맞다** — 원인은 재파싱 로직이 아니라 스크립트 자체가 실행 즉시 죽는 것이었다.

`sys.stdout.reconfigure(encoding="utf-8", errors="replace")` / `sys.stderr...` 2줄만
추가(순수 추가, 로직 무변경)한 뒤 재실행하니 정상 완주했다:
```
wf_fail=13 nb_csm_fail=8 nb_mult_fail=0
NB CSM gate open -> continue reparse loop
=== LOOP ENDED WITH FAILURES ===
```
직접 실행한 `validate_csm_waterfall.py` 결과(13건 실패)와 정확히 일치 — 루프가 이제
작동한다.

**부수 발견(지시 범위 밖, 투명하게 보고)**: 이 루프는 `--waterfall-only`로도
`viz_build_ifrs17_kpis.py`·`viz_build_csm_bubble.py` 두 단계를 무조건 돈다. 돌려보니
`data/dart/viz/downstream_kpis.json`(마지막 커밋 **2026-07-04**)·`csm_bubble.json`이
`csm_amort_schedule.json`의 2026-08-20 단위 정규화(25th pass `_amort_unit_xref`) 이전
상태로 **1.5개월 정체**돼 있었다 — 예: 삼성생명 상각 y1버킷이 1,030,710(100배 부풀어
있었음) → 10,561.21(현재 `closing_csm_mn_krw`/100과 정확히 일치)로 정정됐다. 되돌리지
않았다(되돌리면 stale 상태로 역행하는 게 더 나쁘다) — `validate_data_contract.py` RED=0·
`test_deploy_assets.py` 10/10 통과로 안전 확인했다. 정식 발주 대상이 아니니 인지만
부탁한다(별도 staleness 감사가 필요해 보인다).

### 4. 안 닫히는 나머지 — 전부 함수·라인까지 추적("재파싱 필요"로 안 끝냄)

**C. 메트라이프생명보험(3개년) — `_disambiguate_basis_period()`
(`scripts/viz_build_csm_waterfall.py:614-691`)의 부분 가드.**
FY2024 필링(rcept 20250402000865) 실측: 후보 4블록 중 direct 3개(당기/전기/소규모 별도표)
+ 원문 각주("(주1)...")를 캡션으로 잘못 문 전기(FY2023) 블록. `is_direct`/`period`/
`completeness`/`score`가 4블록 모두 동률이라 최종 타이브레이커(new_business 절댓값)가
이기는데, **전기(comparative) 블록의 new_business(504,448,140)가 당기 블록(374,208,778)
보다 커서 전기 블록이 1순위로 정렬**된다. 그다음 `_is_prior()`가 "이 블록 기말=다른 블록
기초"를 검사해 이 전기 블록을 정확히 prior로 잡아내지만(계산 자체는 맞음), **그 결과를
실제로 쓰는 경로는 생존 후보가 정확히 1개(`len(current)==1`)일 때뿐**(라인 663-667).
이번 케이스는 생존 후보가 2개(당기 direct + 소규모 별개표)라 그 분기를 안 타고, 다음
매그니튜드 밴드 체크(`len(full)>=2`, 라인 686)도 조건 미달(작은 표가 20% 문턱 미달)로
"그대로 둔다"(라인 687) — **이미 prior로 확정된 1순위 블록을 다시 안 끌어내린다.** IBK연금
사례(라인 656-661 주석)에서 `len(current)==1` 케이스는 고쳐졌지만 `len(current)==2+`
케이스는 그대로 남아있던 구멍이다.

**E. 에이아이에이생명보험(FY2025) — 같은 함수, 다른 구멍.** 후보 4블록(direct 당기/전기 +
재보험 당기/전기) 중 `_is_prior()`가 전기 2개를 정확히 걸러 `current=[direct당기,
재보험당기]`까지는 맞게 좁힌다. 그다음 매그니튜드 밴드 체크에서 재보험 블록 기초(521,402)가
direct 블록 기초(1,509,649)의 **34.5%**로 20% 문턱을 넘어버려 `full=[direct,재보험]` 둘 다
살아남고, "작은 쪽이 별도(別途) 기준"이라는 원래 취지(연결 vs 별도 중복표 판별용) 휴리스틱이
**direct vs 재보험(전혀 다른 개념)** 짝에도 그대로 적용돼 재보험 쪽을 승격시킨다. 이 함수는
"연결/별도 중복"을 가정하고 설계됐는데 direct/ceded는 애초에 그 전제에 안 맞는 쌍이다.
(부수: `find_csm_leaf_cols`가 이 회사의 FCA 2분할 서브헤더에서 컬럼 오프셋을 한 칸 놓쳐
RA+CSM을 합산하는 2차 결함도 확인 — opening 값이 원문으로 재계산한 857,061과 안 맞고
1,509,649(RA+CSM 합)로 나온다.)

**D. 하나생명보험(FY2023·FY2025) — 표 구조 자체가 다르다.** 통과하는 FY2024 필링
("13-4" 캡션)과 실패하는 FY2023("13-3")·FY2025 필링은 **원문 라벨 문구가 동일**(둘 다
"기초잔액에서 보고기간말잔액까지의 차이조정")한데 결과가 다르다 — 라벨 매칭 문제가 아니라
**어느 블록이 선택되는지**가 해마다 갈리는 것으로 보인다. 이 회사 표는 "기초"(부모,
col[0])/"자산"·"부채"(자식, col[1])로 라벨이 컬럼에 걸쳐 쪼개지는 rowspan 병합 구조인데,
코드에 이미 그 정확한 케이스를 이름으로 명시한 보정 로직이 있다(`extract_stages` 873-896행
주석 "e.g. 하나생명 13-4") — 단 opening/closing 두 스테이지에만 적용되고 assumption 등
나머지 4개엔 적용 안 된다. FY2024는 통과하는데 라벨이 같은 FY2023/FY2025가 실패하는
정황상, 이 두 해엔 아예 다른(더 넓은/다른 모양의) 후보 블록이 이기고 있을 가능성이 높다 —
정확한 승자 블록 추적까지는 이번 세션에서 못 끝냈다.

**공통 관찰**: C·E(그리고 D도 개연성 있게)가 전부 `_disambiguate_basis_period()` 한 함수
(80줄)에 몰려 있다. 이 함수는 이미 한화생명·IBK연금 실사례로 여러 번 패치된 민감한 공유
로직이라, 이번에 찾은 2개 구멍을 한 번에 고치려면 그 두 회사를 포함한 전사 combo-diff
재검증이 따로 필요하다고 판단해 **이번 세션에서는 고치지 않고 정확한 위치만 못 박아
넘긴다.**

### 5. 게이트 재확인

- `validate_csm_waterfall.py`: **exit 1**(13건 잔존, `nb_csm_fail=8` — Type A 6사 +
  Type D 하나생명(no_stage_match라 6스테이지 전부 결측 취급)).
- `run_ifrs17_csm_reconcile_loop.py --skip-measurement --waterfall-only`: 이제 정상
  완주(전에는 UnicodeEncodeError로 즉사).
- `test_viz_csm_waterfall_golden.py`: 값이 의도적으로 바뀌어 `--update`로 재생성 후 통과.
- `scripts/prepush_check.py`: **RED=0 · K-ICS rule gate=clear · domain gates=pass ·
  inbox 기계적위반=0 · offline tests 157 passed · exit 0**(내 변경 반영 후 실행. 동시에
  돌고 있던 K-ICS 레인 세션의 워킹트리 변경분은 실행 전후 git status 대조로 훼손 없음
  확인 — 신규 파일 3개만 추가됐고 삭제·되돌려진 항목 없음).
- `validate_data_contract.py`: RED=0(kpis/bubble 갱신 이후 재확인, 동일).

### 하지 말 것 준수

게이트 임계 완화·실패 케이스 skip 처리 없음. `build_root_masters.py` 안 건드림. xlsx 안
건드림(`data/dart/viz/csm_waterfall.json`은 root 마스터가 아니라 viz 패널이라 xlsx sync
대상이 아니다 — CSM_waterfall.json·IFRS17_BS.json 등 root 마스터는 이번 세션에서 전혀
안 건드렸음을 재확인).

### 결론

`NOT_A_PUSH_GATE` 유지 요청 — exit code 1. 5건 완전 종결(라이나 2 + 처브라이프 3), 1건은
별개 결함으로 이관(라이나 FY2023), 13건 잔존은 전부 `_disambiguate_basis_period()`/
`find_csm_leaf_cols()` 레벨까지 원인 규명 완료. 다음 세션(또는 별도 티켓)에서 그 함수를
한화생명·IBK연금 케이스와 함께 전사 재검증하며 고치는 걸 권한다.

## 답변 (parser-ifrs17, iter-2)

### 결론

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_csm_waterfall.py
  → exit 0.  pass=41 fail=0 nb_fail=0 in_scope=41 excluded_pre_ifrs17=6 total=47
```

**exit 0 달성. `NOT_A_PUSH_GATE` → `WIRED` 전환 + 훅 1c 목록 등재를 요청한다.** iter-1이 규명한
잔여 13건을 함수·라인까지 추적해 전부 닫았고(라이나 열-오프셋 결함 포함), 그 과정에서 같은
공유 함수의 버그가 **원 티켓 범위 밖 5개사에도 숨어 있던 것**을 추가로 찾아 같이 고쳤다(아래
§4). 자체 회귀도 2건 발생시켰다가 그 자리에서 원인 추적해 잡았다(§5) — "고쳤다"만 보고하지
않고 고치는 과정 자체를 투명하게 남긴다.

### 1. 13건 전수 처리 결과

| 유형 | 회사(건수) | 근본원인 | 처리 |
|---|---|---|---|
| A. 시행일 이전 | 라이나·메트라이프·IBK연금·에이아이에이·처브라이프·하나생명(6사, 전부 FY2022 필링) | IFRS17 시행일(2023-01-01) 이전 회계연도 — 원문에 "보험계약마진" 단어가 0회(46개 필링 전수조회, 6개 파일 전부 확인) | **게이트에 구조적 제외 신설**(§3) — "실패지만 봐준다"가 아니라 평가대상에서 뺌 |
| B. 라이나생명 FY2023 열-오프셋(사실은 결측 라인) | 라이나생명보험 1건 | `extract_stages()`가 "계약의 경계 변경 효과"(계약경계 재판정 catch-up) 라인을 6-스테이지 패턴 어디에도 안 걸려 누락 — 잔차 -3,439,401.61 | **수정**(§4-1) |
| C. 전기열 오선택(부분가드) | 메트라이프생명보험 3개년 | `_disambiguate_basis_period()`의 `len(full)==1` 케이스가 처리 안 돼 있어 이미 prior로 확정된 블록이 승격 못 됨(FY2024) + whole-vs-parts 오판(FY2025) + FX효과 라인 누락(FY2023) | **수정**(§4-3, §4-4, §4-1) |
| D. no_stage_match(헤더 오프셋) | 하나생명보험 2개년 | `find_csm_leaf_cols()` Case 2가 spurious 상위헤더 행을 못 걸러 컬럼 오프셋 3배 과대추정 + `_is_ceded_block()`이 재보험 블록 오분류 | **수정**(§4-2) |
| E. 재보험표 오선택 | 에이아이에이생명보험 1건 | `_disambiguate_basis_period()`가 원수/재보험을 연결/별도로 오인 | **수정**(§4-3) |

전부 `scripts/viz_build_csm_waterfall.py` 안에서 닫혔다. 재파싱(`data/dart/extracted/*` 자체
수정)은 0건 — 전부 이미 추출된 원문 셀을 워터폴로 조립하는 로직 버그였다.

### 2. iter-1의 "부수 발견" 재검증 — RA+CSM 합산설은 오판이었다

iter-1이 §4에서 남긴 "에이아이에이생명 `find_csm_leaf_cols`가 FCA 2분할 서브헤더에서 컬럼
오프셋을 한 칸 놓쳐 RA+CSM을 합산한다"는 가설을 실측으로 반증했다. 직접 블록을 열어
`PV(idx0)+RA(idx1)+CSM방법1(idx2)+CSM방법2(idx3) = 합계(idx4)` 행 자체 항등식을 검산하니
`csm_cols=[2,3]` 그대로 정확히 닫힌다(기초 보험계약부채: 12,984,182+415,991+652,588+857,061
=14,909,822, 원문 합계열과 일치). 서브헤더 `['공정가치법 적용 계약', '완전소급법 및 그 외
계약']`는 RA가 아니라 CSM 전환방법 2종이 맞다. 실패 원인은 순수하게 §4-3(재보험 오선택)
하나였다 — 에이아이에이는 컬럼 로직을 안 건드렸다.

### 3. 시행일 이전 6건 — 구조적 제외 (조용한 skip 아님)

`scripts/validate_csm_waterfall.py`에 `IFRS17_EFFECTIVE_FISCAL_YEAR = 2023` 상수 +
`_annual_fiscal_year(rcept_no)`(rcept 필링연도-1, `_dart_path_helpers.annual_period_dir_for_rcept`/
`viz_build_ifrs17_panels._period_asof_from_rcept`의 1-4월=연차보고서 컨벤션과 동일 로직 재사용)
+ `build_report()`가 대상 47건을 `in_scope`/`excluded` 로 먼저 분리 신설(파일 53-83행,
161-224행). **평가 대상에서 뺀 6건을 조용히 버리지 않고 `_meta.companies_excluded_pre_ifrs17`
카운트 + `excluded_pre_ifrs17` 목록으로 산출 JSON에 남기고, `main()`이 실행마다
`EXCLUDED (pre-IFRS17, FY2022): <회사> <rcept>` 6줄을 콘솔에 인쇄한다**(아래 재현 출력의
실제 라인). 근거: 이 6개 필링의 추출 원문(`data/dart/extracted/<회사>_<rcept>_measurement.json`)
전수조회 결과 "보험계약마진" 문자열이 파일당 0회 — 캡션도 전부 "…2022년 12월 31일 기준
보험부채에 대해 기업회계기준 제1117호를 적용할 경우…"류의 가정형 pro-forma 문구뿐이라
구조적으로 워터폴 자체가 존재할 수 없다(재파싱해도 영원히 못 채운다).

```
$ C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_csm_waterfall.py
  pass=41 fail=0 nb_fail=0 in_scope=41 excluded_pre_ifrs17=6 total=47
  EXCLUDED (pre-IFRS17, FY2022): 라이나생명보험 20230414000060
  EXCLUDED (pre-IFRS17, FY2022): 메트라이프생명보험 20230407003159
  EXCLUDED (pre-IFRS17, FY2022): 아이비케이연금보험 20230407000580
  EXCLUDED (pre-IFRS17, FY2022): 에이아이에이생명보험 20230410002773
  EXCLUDED (pre-IFRS17, FY2022): 처브라이프생명보험 20230412002541
  EXCLUDED (pre-IFRS17, FY2022): 하나생명보험 20230331001232
```
(콘솔은 cp949라 한글이 깨져 보일 수 있는데 `data/dart/viz/csm_waterfall_validation.json`은
UTF-8로 정상 — 위는 그 JSON에서 직접 읽은 값이다.)

### 4. 코드 수정 4건 (`scripts/viz_build_csm_waterfall.py`)

**4-1. `extract_stages()`(893행 근방) — 보조 가산 라인 메커니즘 신설.** 일부 필링은 6-스테이지
패턴 어디에도 안 걸리는 자체 최상위 라인을 별도로 공시한다. 기존 단일후보pick 루프에 넣으면
그 라인이 더 크면 기존 정답을 "대체"해버려 오답이 나므로, 이미 뽑힌 스테이지 값에 **가산**하는
전용 루프를 신설(`_SUPPLEMENTARY_ADDITIVE`):
- `("assumption", ("계약의 경계 변경 효과",))` — 라이나생명 FY2023 1회성 계약경계 재판정. 46개
  필링 전수조회로 이 라벨이 이 회사 이 연도에만 등장함을 확인, 다른 회사 오염 위험 없음.
- `("interest", ("환율변동효과 등",))` — 메트라이프 3개년 공통. `row5(보험서비스결과)+
  row6(순금융손익)+row7(이 행)=row8(총변동)` 항등식으로 검증. **트레일링 "등"까지 정확히
  일치시켜야 한다** — 처음에 "환율변동효과"만 부분일치시켰다가 케이비라이프(같은 접두어로
  시작하는 "환율변동효과 외"가 실은 "보험금융손익(PL)"의 **자식행**이라 부모+자식 이중계상,
  §5-1)를 깨뜨려서 라벨을 정확히 좁혔다.

**4-2. `find_csm_leaf_cols()` Case 2(329행 근방) — 데이터폭 검증 fallback.** 하나생명 13-3/14-4
표는 헤더 첫 행이 `['구분', '보험료배분접근법외 보험계약']`(2칸짜리 spanning 라벨)이라 진짜
[PV,RA,CSM,합계] 행이 한 단 밀려 `sub`로 들어간다. 기존 로직은 PV/RA도 CSM과 똑같이 `grp`번
반복된다고 가정해(`flat_start=i*grp`) 실제 6~7칸 데이터에 `[6,7,8]`같은 범위밖 인덱스를
요구했다 — 매번 결측이라 `no_stage_match`. 실제 행 폭(`_richest_value_slice`)과 대조해 안
맞으면 PV/RA를 1칸으로 보고 `flat_start=i`로 재추정하도록 fallback 추가. **부수 버그**: 일부
연도는 sub2에 "소계" 열이 섞여 있어(`[수정소급법,공정가치법,이외모든계약,소계]`) fallback이
그것까지 합쳐 CSM을 2배로 만들었다 — 기존 method_cols 빌더와 동일하게 `_is_subtotal_label`
필터를 추가해 제거(§5-2 재현 사고).

**4-3. `_disambiguate_basis_period()`(659행 근방) — 세 가지 가드 신설:**
1. **ceded 배제** — `is_direct`가 원래 1차 정렬키인데, 이 함수 자신의 크기밴드 픽은 direct 여부를
   전혀 안 본다. 원수 기초가 재보험 기초의 34.5%(20%문턱 초과)라 `full`에 재보험이 같이 살아남고
   "작은쪽=별도" 휴리스틱이 원수/재보험(전혀 다른 축) 쌍에 적용돼 재보험이 이겼다(에이아이에이
   FY2025). `current`를 `_is_ceded_block` 기준으로 먼저 direct만 남기게 필터링.
2. **`len(full)==1` 승격** — 기존 코드는 `len(current)==1`일 때만 prior 확정 블록을 재승격했다.
   크기밴드 필터를 거친 뒤에야 1개로 좁혀지는 경우(작은 재보험곁표가 `current`엔 남았다가
   `full`에서 걸러지는 경우)는 처리가 없어 `len(full)<2: return ranked` 가 **이미 prior로 확정된
   블록을 그대로 승자로 방치**했다(메트라이프 FY2024: 각주를 캡션으로 잘못 문 전기 블록이
   nb_abs로 1위 정렬돼 있었는데 안 끌어내려짐). `len(current)==1`과 대칭으로 `len(full)==1`도
   승격하게 추가.
3. **whole-vs-parts 판별** — 크기밴드가 아그리게이트 표 + 자기 자신의 상품별 부분표(무배당/변액
   등)를 동시에 통과시키면 "작은쪽=별도" 로직이 부분표를 승격시킨다(메트라이프 FY2025: 변액
   단독표가 승격, 실제로는 아그리게이트 closing 2,608,160,261 ≈ 무배당 1,847,845,220+변액
   755,779,349=2,603,624,569, 0.17%차). `collect_current_product_blocks`가 이미 쓰는 "한
   블록이 나머지 합과 같으면 total"(5%허용) 판별을 `full`에도 적용, 발견되면 그 전체가 승자.
   **단 `len(full)>=3`에서만** — 2개짜리에서는 "나머지 1개의 합"이 그냥 "나머지 1개와 같다"로
   퇴화해 진짜 연결/별도 쌍(별도가 연결에 가까운 회사)도 오탐한다(§5-3).

**4-4. `extract_stages()`의 "Rowspan-split" 패치(967행 근방) — 자산 하위행 라벨 기반 재검.**
기존 가드는 "현재 픽이 값 0에 가까울 때만" 순부채/순자산 행으로 대체했다. 하나생명 FY2025는
`당기말` 태그가 `자산` 하위행에만 붙고(`부채`/`보험계약순부채` 형제행엔 안 붙음) 그 `자산`
행 자체가 **0이 아닌 진짜 값**(-19,577,929)이라 가드를 안 타 기말이 통째로 틀렸다(잔차 62%).
현재 픽의 라벨이 `" / "`로 조인된 마지막 세그먼트가 정확히 "자산"일 때도(값 무관) 재검하도록
조건 추가 — 라벨 기준이라 다른 회사가 "기말잔액" 등 정상 라벨로 이미 맞게 픽한 경우는 안 건드림.

### 5. 내가 낸 회귀 2건 — 그 자리에서 잡았다

**5-1. 케이비라이프생명보험(FY2024 필링, 통과 중이던 회사)** — §4-1의 "환율변동효과" 패턴을
처음엔 부분일치로 넣었더니 그 회사의 "보험금융손익(PL)"(CSM=123,071) 부모행 + 그 자식
"환율변동효과 외"(102,487, 부분일치로 걸림)를 동시에 더해 interest가 225,558로 뻥튀기됐다
(실측: 이전 residual=0 → 이 실수로 residual=102,487 발생, `validate_csm_waterfall.py` 재실행
으로 즉시 검출). 라벨을 "환율변동효과 등"(트레일링 등까지) 정확일치로 좁혀 해결 — 메트라이프의
실제 라벨과 정확히 일치하고 케이비라이프의 자식행(외/등 없는 bare형)과는 안 겹친다.

**5-2. 하나생명보험(FY2025, 원래 목표 대상)** — §4-2 fallback을 처음 넣었을 때 "소계" 열
필터를 안 넣어 CSM이 2배가 됐다(잔차 1,492,947 tol=500). §4-2에 적은 대로
`_is_subtotal_label` 필터를 추가해 잔차 746,474로 반감 → §4-4(자산 하위행 재검)까지 넣고서야
0으로 닫혔다. 두 결함이 같은 필링에 겹쳐 있었다.

두 건 다 "고쳤다"로 끝내지 않고 `validate_csm_waterfall.py` + 셀 단위 원문 대조로 재확인했다.

### 6. 원 티켓 범위 밖 — 같은 공유 함수 버그가 5개사에 더 숨어 있었다

수정 4건은 전부 `rank_main_blocks`/`extract_stages`가 **모든 회사가 공유하는** 함수라, 고치고
나니 원래 "ok"였던 회사 중 **라벨은 그대로인데 숫자만 통째로 바뀐** 사례가 5건 더 나왔다(전후
diff로 발견, 표로 남긴다):

| 회사 | rcept | 증상 | 검증 |
|---|---|---|---|
| 코리안리 | 20250320001161 | opening 1,064,090→803,146, closing 803,146→904,674 | 새 opening=구 closing(803,146) 완전일치 — 구 픽이 전기였다는 수학적 증거. `_is_prior` 추적으로 확인 |
| NH농협손해보험 | 20250331003247 | opening 2,106,008→2,055,155, closing 2,055,155→1,513,226 | 새 opening=구 closing(2,055,155) 완전일치, 동일 증거 |
| 동양생명 | 20250319000486 | opening 2,374,228→2,541,801, closing 2,541,801→2,671,088 | 새 opening=구 closing(2,541,801) 완전일치, 동일 증거 |
| 삼성생명 | 20250312001063 | interest만 465,809→495,114(+29,305, ~0.06%) | §4-1 FX가산(라벨과 정확히 "환율변동효과 등" 일치) — 블록선택 무관, 의도된 변화 |
| 교보생명보험 | 20250331004015 | (일시적 회귀, §5-3에서 자체 정정) | whole-vs-parts len>=3 제한 후 원래값(별도, 5,824,924)으로 복귀 확인 |

즉 원래 코리안리·NH농협손해보험·동양생명 3사는 **전기 데이터를 당기로 잘못 표시한 채
`balance_fail` 없이 통과하던 false-green**이었다 — assumption/opening/closing이 전부 같은
(틀린) 연도에서 나와 내부적으로는 항등식이 닫혔기 때문에 게이트가 못 잡았다. `_is_prior`
연속성 로직으로 셋 다 "새 opening == 구 closing 정확일치"를 확인해 새 픽이 옳다는 걸
수학적으로 증명했다(추측 아님). 정식 발주 대상은 아니지만 인지해 달라는 취지로 남긴다 —
전사 combo-diff는 §8에서 재확인.

### 7. 연속성 자기검산 (직전분기 기말 == 당분기 기초)

멀티이어 데이터가 있는 6개사 전부 스캔:

| 회사 | 전이 | 괴리율 | 판정 |
|---|---|---|---|
| 메트라이프생명보험 | FY2023→FY2024, FY2024→FY2025 | 0.0000% / 0.0000% | 완벽 |
| 에이아이에이생명보험 | FY2023→FY2024, FY2024→FY2025 | 0.0000% / 0.0000% | 완벽(후자가 이번 수정분) |
| 아이비케이연금보험 | FY2023→FY2024 | 0.0000% | 완벽(비교용, 미수정 구간) |
| 처브라이프생명보험 | FY2023→FY2024, FY2024→FY2025 | (전전 세션 수정분) / 0.1428% | 정상 |
| 하나생명보험 | FY2023→FY2024, FY2024→FY2025 | 0.0012% / 1.3046% | 정상(후자가 이번 수정분, 소폭) |
| **라이나생명보험** | FY2023→FY2024 | **41.4353%** | **미해결 — 아래 §8** |

### 8. 미해결 오픈 이슈 — 라이나생명 FY2023→FY2024 대규모 불연속 (게이트 범위 밖)

라이나생명 FY2023 필링(20240409003674) 자체 보고 기말=5,515,548.316(백만원, PV+RA+CSM+
취득CF=합계 행 항등식으로 검증 완료)인데, FY2024 필링(20250409002702)이 **자신의 전기
비교값**으로 제시하는 기말은 3,230,161.575다 — 같은 2023-12-31 시점인데 41% 차이난다.
이 차이는:
- **내 수정으로 생긴 게 아니다.** FY2023 필링 자체의 기말값은 이번 세션에서 한 번도 안
  바뀌었다(assumption 스테이지만 손댔고, closing은 항상 "기말 잔액" 행 직독출).
- **이미 있었다.** 백업 JSON(수정 전) 대조 결과 이전에도 FY2024 필링의 opening(3,526,401.798,
  이것도 §6과 같은 이유로 실은 전기 오선택값이었다)과 FY2023 필링의 기말(5,515,548.316)
  사이에 36% 괴리가 이미 있었다 — 내 수정이 41%로 키운 게 아니라 못 보던 걸 드러낸 것에 더
  가깝다.
- **게이트가 안 잡는 종류다.** `validate_csm_waterfall.py`는 **필링 내부** 항등식만 검사한다
  (opening+NB+interest+assumption+amortization≈closing, 같은 rcept 안에서). 필링 A의 기말과
  필링 B의 "전기" 컬럼이 같은 회사 같은 연도인데 다르다는 건 **필링간(cross-filing)** 검사라
  이 게이트의 3대 룰 어디에도 안 걸린다 — exit 0에 영향 없음.
- **원인을 추측하지 않는다.** FY2023이 최초 IFRS17 연차라 "계약의 경계 변경 효과"라는 1회성
  항목(§4-1)이 껴 있었는데(+3,439,401.606), 5,515,548.316에서 그만큼 빼도(2,076,146.710)
  3,230,161.575와 안 맞는다 — 단순 차감으로 설명 안 된다. 소급수정(retrospective
  restatement)일 개연성이 높지만 `measurement.json` 추출본만으로는 확정할 근거가 없다.
  "재파싱 필요"로 뭉개지 않고 여기 명시적으로 남긴다 — 원문 XML의 주석/정정 섹션까지
  내려가는 별도 조사가 필요하면 새 inbox 티켓으로 발주해달라.

### 9. 골든 · 게이트 재확인

```
$ python scripts/viz_build_csm_waterfall.py && python tests/test_viz_csm_waterfall_golden.py --update
  updated tests/fixtures/viz_csm_waterfall_golden.json: 47 companies {'ok': 41, 'no_csm_columns': 6}
$ python -m pytest tests/test_viz_csm_waterfall_golden.py tests/test_viz_ifrs17_panels_golden.py tests/unit/test_csm_extractor.py -q
  9 passed
$ python scripts/validate_csm_waterfall.py
  pass=41 fail=0 nb_fail=0 in_scope=41 excluded_pre_ifrs17=6 total=47   EXIT=0
$ python -m pytest tests/test_push_gate_wiring.py -k unwired_gates_still_fail -q
  FAILED (assert 0 != 0) — 예상된 동작. "아직도 깨져 있나" 자기확인 테스트가 이제 깨졌다는
  뜻은 곧 이 게이트가 통과한다는 뜻이니, NOT_A_PUSH_GATE→WIRED 전환이 필요하다는 신호다.
$ python scripts/validate_data_contract.py
  SUMMARY RED=36 YELLOW=296 provisional=False, EXIT=0 (root master CSM_waterfall.json 기준 —
  이번 세션이 안 건드린 파일이라 내 변경과 무관한 기존 베이스라인)
```
값이 의도적으로 바뀌어(라이나·메트라이프·하나생명·에이아이에이·삼성생명·코리안리·NH농협손해·
동양생명 = 8사, 위 표 사유대로) 골든을 손으로 안 고치고 `--update`로 재생성했다.

### 10. 하지 말 것 준수

- 게이트 임계 완화·실패 케이스 skip 없음(§3 제외는 "구조적으로 불가능"이 근거이자 카운트
  인쇄됨, 실패를 숨긴 게 아님).
- `build_root_masters.py`/`main()` 안 건드림, `CSM_waterfall.json`(root)·`IFRS17_BS.json`
  등 root 마스터 전혀 미접촉(확인: `git status`에 이 세션이 건드린 파일은 정확히
  `scripts/viz_build_csm_waterfall.py` · `scripts/validate_csm_waterfall.py` ·
  `data/dart/viz/csm_waterfall.json` · `data/dart/viz/csm_waterfall_validation.json` ·
  `tests/fixtures/viz_csm_waterfall_golden.json` 5개뿐).
- `insurequant_master_tables.xlsx` 안 건드림(`csm_waterfall.json`은 xlsx sync 대상 아님).
- `kics_disclosure.json`·`validate_kics_disclosure.py`·`src/solvency/**` 전혀 미접촉 —
  `git status`로 그 3개 파일이 **다른 세션에 의해** 이미 M 상태임을 확인했고 이번 세션이
  손대지 않았음을 재확인.
- 커밋·push 없음.
- 값이 판독 불가한 곳은 없었다(6건 제외는 "판독불가"가 아니라 "원문에 그 개념 자체가 없음"
  — 근거는 §3).

### 결론 (iter-2)

`validate_csm_waterfall.py` **exit 0**. 잔여 13건 전부 종결(구조적 제외 6 + 코드수정 7),
부수로 원 범위 밖 false-green 3건 추가 발견·수정, 자체 회귀 2건 즉시 검출·수정. 유일한
미해결 항목은 라이나생명 FY2023↔FY2024 필링간 41% 불연속인데 게이트 범위 밖이라 exit
code에 영향 없다 — §8에 명시적으로 남기고 종결하지 않는다. `tests/test_push_gate_wiring.py`의
`NOT_A_PUSH_GATE`→`WIRED` 전환 + `prepush_check.py` 1c 목록 등재를 요청한다.
