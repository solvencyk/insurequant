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
| [PM-2026-06-16](PM-2026-06-16_two_month_glitch.md) | 두 달 글리치 — 맞는 산수·틀린 소스 false-green | ✅ push 게이트(data-contract 5 CHECK) | `closed` (잔여 UH-3·UH-4) |
| [PM-2026-07-07](PM-2026-07-07_after_capture_blindspot.md) | 경과조치 **적용후** 전면 미검증 | ✅ 양쪽 (2026-07-21 lift) | `closed` |
| [PM-2026-07-08](PM-2026-07-08_v17_mirror_fill.md) | V17 가짜복사(적용후=round(적용전)) | ✅ 양쪽 (2026-07-21 lift) | `closed` |
| [PM-2026-07-15](PM-2026-07-15_post_parent_census.md) | 적용후 요구자본 **부모** 결측 → 라이브 공란 | ✅ 양쪽(K-ICS + push) | `closed` |

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
| **UH-3** | provenance end-state(no-sidecar=RED) 미전환 | 진행 중 — sidecar YELLOW **4→1**. publishing(`faa34cd`)이 forward_capital·tier1·tier2 sidecar 발행 → 3종 Phase-2 strict 전환. **sensitivity_heatmap만 잔여**(parser(ifrs17) `20260721T0530Z` 발주 대기). 4종 전부 발행 후 no-sidecar=RED 보편룰 활성화 |

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
