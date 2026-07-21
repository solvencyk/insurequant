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

| ID | 사고 | 룰 배선 | 미배선 잔여 |
|---|---|---|---|
| [PM-2026-06-16](PM-2026-06-16_two_month_glitch.md) | 두 달 글리치 — 맞는 산수·틀린 소스 false-green | ✅ push 게이트(data-contract 5 CHECK) | UH-3 provenance end-state · UH-4 selftest 부재 |
| [PM-2026-07-07](PM-2026-07-07_after_capture_blindspot.md) | 경과조치 **적용후** 전면 미검증 | ⚠️ K-ICS 게이트만 | **UH-1** push 게이트 미배선 |
| [PM-2026-07-08](PM-2026-07-08_v17_mirror_fill.md) | V17 가짜복사(적용후=round(적용전)) | ⚠️ K-ICS 게이트만 | **UH-1** + 요구자본 항목 COPY 검사 부재 |
| [PM-2026-07-15](PM-2026-07-15_post_parent_census.md) | 적용후 요구자본 **부모** 결측 → 라이브 공란 | ✅ 양쪽(K-ICS + push) | UH-2 게이트 파일 untracked |

## 🔴 소급 기록의 실질 산출물 — 아직 룰로 안 굳은 것 (다음 게이트 후보)

| ID | 내용 | 왜 위험한가 | 우선순위 |
|---|---|---|---|
| **UH-1** | 적용후 검증 7종(`_transition_ratio_after_capture` / `_transition_mmult_after` / `_transition_identities_after` / `_parent_present_child_incomplete_after` / `_diversification_negative` / `_item12_equals_item1` / `_ratio_series_spikes`)이 **push 게이트에 미배선**. `prepush_check.py`가 `validate_kics_disclosure.py`를 호출조차 안 함 | 07-07·V17 사고 대응 룰 전부가 **push를 못 막는다.** 같은 부류 재발 시 또 통과 | **P1** |
| **UH-2** | `scripts/validate_data_contract.py`가 **git untracked**(머신-로컬) | push 게이트 배선(PM-2026-07-15 포함)이 git에 없음 → 다른 환경/재생성 시 소실 | **P1** |
| **UH-3** | provenance Phase-2 end-state 미강제. sidecar 있는 3종(kics_disclosure·CSM_waterfall·PL_breakdown)만 strict, 없는 마스터는 Phase-1 추론 fallback + note | 소스 신선도 미검증 마스터가 조용히 통과(= 두 달 글리치 원형) | P2 |
| **UH-4** | `validate_data_contract.py --selftest`가 `_data_contract_selftest` 모듈 부재로 실행 불가 | 게이트 자체의 회귀를 못 잡음 | P2 |

**UH-1이 이번 소급의 최대 발견이다.** 사고 4건 중 3건의 대응 룰이 push 차단 경로 밖에 있다.
