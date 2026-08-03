# 사고 포스트모템 (blameless) — 게이트 룰로 종결

> owner 발주 `inbox/validation/20260721T0233Z__owner__MULTI__adopt_incident_postmortem_practice.md`
> 운영 스킬: `.claude/skills/incident-postmortem/SKILL.md` · 스테이지 프롬프트 링크: `docs/agents/claude-agent-validation.md` §5.1

## 왜 이 관행인가

이 저장소의 사고는 대부분 이 경로를 탔다:

> 사고 발생 → 메모·changelog 기록 → **게이트 룰로는 안 굳음** → 다른 형태로 재발

기록만으로는 재발을 못 막는다. **포스트모템은 "어떤 룰이 어디에 배선됐다"로 종결돼야 한다.**
비난 없음(blameless) — 사람이 아니라 **게이트의 사각**을 원인으로 본다.

## 종결 조건 (5칸 — 하나라도 비면 close 불가)

| # | 칸 | 반드시 담을 것 |
|---|---|---|
| 1 | **무엇이 통과했나** | 어떤 게이트가 **왜** 못 잡았나 (통과 당시 RED 수, false-green이면 그 이유) |
| 2 | **어떤 룰이었으면 잡았나** | 추상적 교훈 금지. **구체 룰 정의**(입력 항목·판정식·임계값·severity) |
| 3 | **그 룰이 지금 배선됐나** | 함수명 + 파일(`validate_kics_disclosure.py` / `validate_data_contract.py`) + **scope(display-only / 전분기)** + exit-code 반영 여부 |
| 4 | **documented exception** | 있으면 근거 + **등재 위치(registry 변수명·파일)**. 없으면 "없음" 명시 |
| 5 | **미배선 잔여 + 후속 티켓** | 2번 룰 중 아직 안 굳은 부분 + inbox 티켓 파일명. 없으면 "없음" |

**3번이 "아니오"인데 5번이 비어 있으면 그 포스트모템은 미완이다.** 그 상태가 바로 재발 경로다.

## 두 게이트의 차이 (3번 칸을 채울 때 반드시 구분)

| 게이트 | 파일 | 언제 도나 | 무엇을 막나 |
|---|---|---|---|
| K-ICS 게이트 | `scripts/validate_kics_disclosure.py` | CLAUDE.md 규정상 수동 실행 | 자기 exit code(2)만. **push를 자동으로 막지 않는다** |
| **push 게이트** | `scripts/validate_data_contract.py` (← `prepush_check.py`) | publishing이 push 직전 | **실제 push 차단.** display 7분기 scope |

⚠️ **`prepush_check.py`는 `validate_kics_disclosure.py`를 호출하지 않는다.**
→ K-ICS 게이트에만 배선한 룰은 **push를 못 막는다.** 3번 칸에 "K-ICS 게이트에 배선"이라고만 적으면
그건 절반만 굳은 것이다. 반드시 push 게이트 배선 여부를 따로 적을 것. (이 사실 자체가 PM-2/PM-3의
미배선 잔여 = UH-1.)

## 파일 규칙

`docs/postmortems/PM-<YYYY-MM-DD>_<slug>.md` — 템플릿은 [`_TEMPLATE.md`](_TEMPLATE.md).

## 색인

| ID | 사고 | 룰 배선 | 상태 |
|---|---|---|---|
| [PM-2026-06-16](PM-2026-06-16_two_month_glitch.md) | 두 달 글리치 — 맞는 산수·틀린 소스 false-green | ✅ push 게이트(data-contract 5 CHECK) | `closed` (UH-3·UH-4 **모두 해소** 2026-08-03) |
| [PM-2026-07-07](PM-2026-07-07_after_capture_blindspot.md) | 경과조치 **적용후** 전면 미검증 | ✅ 양쪽 (2026-07-21 lift) | `closed` |
| [PM-2026-07-08](PM-2026-07-08_v17_mirror_fill.md) | V17 가짜복사(적용후=round(적용전)) | ✅ 양쪽 (2026-07-21 lift) | `closed` |
| [PM-2026-07-15](PM-2026-07-15_post_parent_census.md) | 적용후 요구자본 **부모** 결측 → 라이브 공란 | ✅ 양쪽(K-ICS + push) | `closed` |
| [PM-2026-07-30](PM-2026-07-30_kr0075_csm_100x_unit.md) | KR0075 CSM_waterfall 100x 단위과대 — 절대값 cap은 있었으나 상대규모 검사축 없음 | ✅ push 게이트 `CSM_WATERFALL_PLAUSIBILITY` (2026-08-03 배선, 초기 YELLOW) | `closed` (UH-6 해소) |
| [PM-2026-08-03](PM-2026-08-03_capsec_provenance_label_mismatch.md) | 자본성증권 provenance **라벨 거짓**(DART 파일에 `FSC_BONDS`)이 통과 — 게이트가 틀린 주장을 "검증" | ✅ push 게이트 `SOURCE_ID_LINEAGE_MISMATCH` + 계보별 effective 증거 + 사이드카 도출 emitter | `closed` (잔여 UH-7) |
| [PM-2026-08-03 §6](PM-2026-08-03_capsec_provenance_label_mismatch.md#6-후속--같은-사건의-두-번째-얼굴-커버리지-census-2026-08-03-b) | **같은 사건의 두 번째 얼굴** — 소스가 통째로 비어도 통과(커버리지 후퇴). DART 전환으로 raw 없는 회사의 채권이 사라져 비율이 낙관 방향으로 틀림(KR0076 94→152%) | ✅ push 게이트 `CAPSEC_COVERAGE_REGRESSION` + `CAPSEC_SOURCE_UNRESOLVED` (+YELLOW 그물 2종) | `closed` (데이터 잔여 RED 15 = 의도된 push 차단, parser·downloader 발주) |

## ✅ 2026-07-21 해소 (owner 승인)

| ID | 조치 |
|---|---|
| **UH-1** | 적용후 검증 7종을 `validate_data_contract.py` `check_census` **1b(iv)** 로 lift (display 7분기 scope). 6종 RED + `_ratio_series_spikes`만 YELLOW(휴리스틱이라 단독 차단 금지). **주입 테스트로 방출 경로 검증**: display-scope를 2023.1~3Q로 임시 확장 시 baseline RED 0 → lifted RED 4건 |
| **UH-2** | push 게이트 체인 3종(`validate_data_contract.py`·`prepush_check.py`·`triage_anomaly_candidates.py`) **git 등재**. gitignore가 아니라 단순 미추가였음(scripts/ 163개는 이미 tracked) |

## 2026-07-21 (2차) — UH-4 해소 · UH-3 부분강화 · UH-5 선행조건 확정

| ID | 조치 |
|---|---|
| **UH-4 ✅ 해소** | `scripts/_data_contract_selftest.py` 신설 — `Env(inject=…)` 합성데이터 mutation suite **14/14 PASS**. 기존 spec §5 회귀(census·impossible-0·stale as-of·donut·concept-guard·tier2 identity) + **1b(iv) lift 5종(F1~F5) 회귀 보호**. **이빨 검증**: 룰을 죽이면(`_item12_equals_item1`·`_post_transition_parent_census` monkeypatch) 해당 케이스가 미검출→FAIL 처리됨을 확인 |
| **UH-3 ⚠️ 부분강화** | 종전 `notes`에만 적혀 **집계도 안 되고 조용히 통과**하던 sidecar 부재를 집계되는 **YELLOW `MISSING_PROVENANCE_SIDECAR`** 로 승격(현 4건: sensitivity_heatmap·forward_capital·tier1/tier2_utilization). **RED 전환은 발행 후** — 지금 RED로 두면 미발행 마스터가 전부 red-out돼 push가 영구 차단. 발행 발주: publishing `20260721T0530Z…provenance_sidecar_emission` · parser(ifrs17) `20260721T0530Z…sensitivity_heatmap_provenance` |

## 🔴 아직 룰로 안 굳은 것

| ID | 내용 | 상태 |
|---|---|---|
| **UH-3 ✅ 해소 (2026-08-03 c)** | **end-state 도달 = no-sidecar RED 전환.** 4종 사이드카 전부 발행 완료(publishing `faa34cd` → forward_capital·tier1·tier2 / parser `scripts/emit_sensitivity_provenance.py` → `data/dart/viz/sensitivity_heatmap_provenance.json`) → 라이브 `MISSING_PROVENANCE_SIDECAR` YELLOW **1→0** 확인 후 `_fallback_note`를 **YELLOW→RED** 승격(`validate_data_contract.check_as_of`). 이제 사이드카 부재 = "미발행 정상"이 아니라 **발행 경로가 씻겨나간 신호**이므로 push 차단. Phase-1 추론 블록은 진단용으로 존치(그 분기가 이미 RED라 통과 경로가 아니다). 회귀 케이스 **C3** + 이빨 검증(YELLOW로 강등하면 미검출 FAIL). **전환 후 라이브 CHECK2 RED=0 유지** = 오탐 0 |
| **UH-8** | `kics_rate_sensitivity`는 `MASTER_FILES`에 있으나 **CHECK 2 provenance 검사 대상이 아니다**(사이드카 없음·as-of 축 미검사). 다른 검증기(`data/_derived/kics_rate_sensitivity_validation.json`)가 값은 보지만 **소스 신선도는 아무도 안 본다** — UH-3가 닫은 것과 같은 부류의 잔여 축 | 신규 — 발주 `inbox/parser/20260803T0520Z__validation__MULTI__rate_sensitivity_provenance_sidecar.md` (lane: kics). 사이드카 발행 후 CHECK 2에 배선 |
| **UH-6 ✅ 해소 (2026-08-03)** | `CSM_WATERFALL_PLAUSIBILITY` 배선 완료 — `_csm_magnitude_implausible()` → `validate_data_contract.check_census` **1d**. 판정식 `기말CSM ÷ item1지급여력금액`(회사별 최신 분기, KR코드 조인) > `median × 10`. **임계값은 parser 초안 ×20에서 ×10으로 조정** — 초안 근거(KR0075 r=153)는 정정 전 값이고 정정 후 라이브 36사 분포는 median 0.563 / 최대 1.530(=median의 2.7배)이라 ×20(r>11.3)은 중간규모사의 ×10 단위오류를 놓친다. severity **초기 YELLOW**(관찰 1~2 릴리스 후 RED, UH-3 선례). 오탐 억제 4종(K-ICS 미공시사 skip·표본<10 skip·상한만·지급여력금액≤0 skip). 회귀 케이스 `_data_contract_selftest.py` **G2** + 이빨 검증(룰 죽이면 FAIL) |
| **UH-7** | `kics_forward_capital.json`의 셀 키가 `baseline_2025_4Q`인데 실제 데이터는 `BASELINE_QUARTER="2026.1Q"` 산출물 — **값은 맞고 키 이름만 거짓**, as-of 정본 판단을 흐린다(`forward_capital_simulation.py:442`). HTML이 이 키를 읽으므로 rename은 publishing+designer 동시 변경 → validation 단독 수정 금지 | 신규 — 발주 `inbox/publishing/20260803T0210Z__validation__MULTI_2026.1Q__forward_baseline_key_misnomer.md` (PM-2026-08-03 §5) |

## ✅ 2026-07-21 (3차) — UH-5 종결 (owner 승인, premise-refined)

**UH-5 = 요구자본(15~21) 부모 COPY 검사** → **신설 불요로 종결.** 선행조건이던 FSS 2023-03-20
붙임-1(`trend20230320_3.pdf` p6, 회사별 경과조치 종류)을 좌표추출로 전수 복원(총계 검증 4/19/12/8
일치) → `_TRANSITION_KIND` registry(`validate_kics_disclosure.py`)로 등재.

- **전제 falsify**: "TAC형(가용자본만·요구자본 무영향) 회사"는 **0사.** 가용자본(AC) 경과조치 신청은
  4사(케이디비·IBK연금·하나생명·푸본현대)뿐이고 이 4사 전부 요구자본 보험리스크(IR)도 신청. elective
  18사 **전원**이 요구자본(보험리스크) 경과조치 신청사.
- **실측 78 "부모후=전" 셀 분류**: **A(subrisk후≠전인데 부모후=전 = 모순) = 0** [owner 지적 그대로,
  기존 `_transition_mmult_after`가 부모후=sqrt(subrisks후·상관행렬)를 이미 강제 → 모순이 살아남지 못함]
  · **C(item14후는 다른데 부모후=전) = 52, 전부 item19(시장위험)** [한화손·롯데손·악사·처브는 주식/금리
  미신청사 → 정당 / 농협손·DB생명·에이비엘은 신청사이나 금리·주식 경과조치가 *조건부*(K-ICS리스크
  60%>RBC일 때만 발동)라 실효과 0 가능 + identity·mmult 전부 통과=내부정합] · **D(subrisk후 부재) =
  26** [census 소관, 기존 `_parent_present_child_incomplete_after` 담당]. **진짜 미검출 = 0.**
- **결론**: 부모 COPY 룰은 item17=mmult 중복·item19=오탐 52건·진짜미검출 0 → **신설이 오히려 게이트를
  더럽힘.** headline(지급여력비율 item27/28)은 이미 `_transition_ratio_after_capture`가 18사 전원 검증.
  registry는 소비 룰 없는 **문서 registry**(향후 근거)로만 존치.

> owner Socratic 지적("subrisk 다르면 상위 risk도 당연히 달라야")이 결론의 핵심이었다 — 그 논리는 참이며
> **이미 mmult가 강제**하고 있어서 A=0. 즉 UH-5가 없어도 사각이 아니다.

## ⚠️ 도메인 경계 — 경과조치는 K-ICS 전용 (owner 2026-07-21)

경과조치(적용전/적용후 이중공시)는 **K-ICS 고유**다. **IFRS17에는 대응 개념이 없다** — 전환방법
(수정소급/공정가치/그 외)은 도입시점 측정방법이지 이중컬럼이 아니므로 **복사할 짝 자체가 없다.**
따라서 `TRANSITION_AFTER_*` 룰군의 IFRS17 유사룰을 만들지 말 것.
(상위 패턴 *"presence만 검사하면 세탁된다"* 는 도메인 무관이며, IFRS17에서는 분기 복붙·impossible-0
형태로 나타나 `CSM_WATERFALL_PLAUSIBILITY` / `IMPOSSIBLE_ZERO_*` 가 이미 담당.)
