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
| [PM-2026-07-08](PM-2026-07-08_v17_mirror_fill.md) | V17 가짜복사(적용후=round(적용전)) | ✅ 양쪽 (2026-07-21 lift) | `closed` (잔여 UH-5) |
| [PM-2026-07-15](PM-2026-07-15_post_parent_census.md) | 적용후 요구자본 **부모** 결측 → 라이브 공란 | ✅ 양쪽(K-ICS + push) | `closed` |

## ✅ 2026-07-21 해소 (owner 승인)

| ID | 조치 |
|---|---|
| **UH-1** | 적용후 검증 7종을 `validate_data_contract.py` `check_census` **1b(iv)** 로 lift (display 7분기 scope). 6종 RED + `_ratio_series_spikes`만 YELLOW(휴리스틱이라 단독 차단 금지). **주입 테스트로 방출 경로 검증**: display-scope를 2023.1~3Q로 임시 확장 시 baseline RED 0 → lifted RED 4건 |
| **UH-2** | push 게이트 체인 3종(`validate_data_contract.py`·`prepush_check.py`·`triage_anomaly_candidates.py`) **git 등재**. gitignore가 아니라 단순 미추가였음(scripts/ 163개는 이미 tracked) |

## 🔴 아직 룰로 안 굳은 것 (다음 게이트 후보)

| ID | 내용 | 왜 위험한가 | 우선순위 |
|---|---|---|---|
| **UH-3** | provenance Phase-2 end-state 미강제. sidecar 있는 3종(kics_disclosure·CSM_waterfall·PL_breakdown)만 strict, 없는 마스터는 Phase-1 추론 fallback + note | 소스 신선도 미검증 마스터가 조용히 통과(= 두 달 글리치 원형) | P2 |
| **UH-4** | `validate_data_contract.py --selftest`가 `_data_contract_selftest` 모듈 부재로 실행 불가 | 게이트 자체의 회귀를 못 잡음. **1b(iv) lift 신설로 게이트 로직이 커진 만큼 중요도 상승** | P2 |
| **UH-5** | 요구자본 항목(15~21) **COPY 검사 부재** — COPY 판정이 비율 item27/28에만 존재 | elective 적용사의 요구자본 후를 적용전 복사로 채워도 미탐지 | P2 (설계상 `_TRANSITION_APPLIERS` 18사 한정 필수) |

## ⚠️ 도메인 경계 — 경과조치는 K-ICS 전용 (owner 2026-07-21)

경과조치(적용전/적용후 이중공시)는 **K-ICS 고유**다. **IFRS17에는 대응 개념이 없다** — 전환방법
(수정소급/공정가치/그 외)은 도입시점 측정방법이지 이중컬럼이 아니므로 **복사할 짝 자체가 없다.**
따라서 `TRANSITION_AFTER_*` 룰군의 IFRS17 유사룰을 만들지 말 것.
(상위 패턴 *"presence만 검사하면 세탁된다"* 는 도메인 무관이며, IFRS17에서는 분기 복붙·impossible-0
형태로 나타나 `CSM_WATERFALL_PLAUSIBILITY` / `IMPOSSIBLE_ZERO_*` 가 이미 담당.)
