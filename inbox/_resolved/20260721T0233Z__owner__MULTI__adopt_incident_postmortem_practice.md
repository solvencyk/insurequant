---
from: owner
to: validation
created: 20260721T0233Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 미결 (sender 작성)

**배경:** 외부 스킬 목록(42종) 검토 중 `incident-postmortem`(blameless 사고 포스트모템)이 이 프로젝트 실패 유형에 정확히 맞는다고 판단 → 도입 발주.

**왜 필요한가 — 실제 재발 이력:**
이 저장소의 사고는 대부분 "사고 발생 → 메모/changelog 기록 → **게이트 룰로는 안 굳음** → 다른 형태로 재발" 경로를 탔음.
- 두 달 글리치: 근본원인 = 권고룰 미강제 + 게이트가 산술만 검사 → "맞는 산수·틀린 소스"가 RED=0으로 통과(false-green).
- 경과조치 **적용후** 검증 사각(2026-07-07): 적용전 등식만 닫혀 있어 통과.
- V17 가짜복사(미러fill) 건.
- **2026-07-15 post-transition parent census** 건: 부모 요구자본 적용후 결측이 산술 등식 다 닫힌 채 push 게이트 통과 → 라이브 공란 노출. (이번엔 게이트 신설로 해소됐고, RED 47→4까지 내려왔음.)

공통점: **포스트모템이 게이트 룰로 종결되지 않으면 같은 부류가 다시 통과한다.**

**요청 (deliverable):**
1. 포스트모템 템플릿을 만들되, **반드시 아래 항목으로 종결**되게 강제:
   - 무엇이 통과했나(어떤 게이트가 왜 못 잡았나)
   - **"어떤 룰이었으면 잡았나"** — 구체 룰 정의
   - **그 룰이 지금 배선됐나** (`validate_kics_disclosure.py` / `validate_data_contract.py` 중 어디에, display-scope인지 전분기인지)
   - documented exception이면 근거·등재 위치(registry 파일명)
   - 미배선이면 후속 티켓 번호
   → 이 5칸이 안 차면 postmortem은 close 불가.
2. **기존 사고 4건을 이 템플릿으로 소급 기록**(위 목록). 소급하면서 "룰로 안 굳은 채 남아있는 것"이 있으면 그게 곧 다음 게이트 후보 = 이번 작업의 실질 산출물.
3. **구현 형태 판단은 위임**: 외부 서드파티 스킬을 그대로 설치할지, `skill-creator`로 **로컬 스킬**을 만들지 직접 판단해서 진행. 이 저장소는 이미 로컬 스킬(`kics-parser`, `ifrs17-parser`) 패턴이 있고 금융데이터를 다루므로 **로컬 작성을 기본 권장**. 외부 스킬을 쓸 거면 그 이유를 답변에 명시.
4. 산출물 위치: `docs/` 하위 + `docs/agents/claude-agent-validation.md`에서 링크. 이력은 `TODO_validation.md` / `docs/changelog_validation.md`.

**스코프 밖:** 이번 건은 프로세스 정비이지 신규 데이터 검증이 아님. 진행 중인 census RED 잔여 4건(흥국생명 2024.4Q·하나생명 2024.4Q exemption 판단 등)과 섞지 말 것 — 그건 별건으로 계속.

## 답변 (validation 처리 — 2026-07-21)

4개 요청 전부 반영. **소급의 실질 산출물(미배선 4건)이 예상보다 큽니다 — 사고 4건 중 3건의 대응 룰이
push 차단 경로 밖에 있습니다.**

### 3) 구현형태 판단 = **로컬 스킬** (외부 서드파티 미채택)

`.claude/skills/incident-postmortem/SKILL.md` 신규 작성. 외부 스킬을 안 쓴 이유:
- 종결 5칸의 강제력이 **이 저장소 고유 지식**에서 나옵니다 — 게이트 파일명(`validate_kics_disclosure.py`
  vs `validate_data_contract.py`), scope(display 7분기 vs 전분기), registry 변수명
  (`_AFTER_SUBRISK_NOT_DISCLOSED` 등), **두 게이트가 분리돼 있다는 함정**. 범용 postmortem 스킬은
  "회고를 잘 쓰게" 할 뿐 "룰이 push 게이트에 배선됐는지"를 물어볼 수 없습니다.
- 기존 로컬스킬(`kics-parser`·`ifrs17-parser`) 패턴 존재 + 금융데이터 → 권고대로 로컬.

### 1) 템플릿 — 5칸 미충족 시 close 불가

`docs/postmortems/README.md`(관행·종결조건·색인·UH표) + `docs/postmortems/_TEMPLATE.md`.
요청하신 5칸 그대로 강제하되, **3번 칸을 두 게이트로 분리 기재**하도록 했습니다(아래 이유).

### 4) 위치·링크

`docs/postmortems/` 하위 + `docs/agents/claude-agent-validation.md` **§5.1 신설**에서 링크.
이력: `TODO_validation.md` V19 · `docs/changelog_validation.md` 2026-07-21.

### 2) 소급 4건 + 🔴 실질 산출물

| PM | 사고 | 배선 상태 | 미배선 |
|---|---|---|---|
| PM-2026-06-16 | 두 달 글리치(산술만 검사) | ✅ push 게이트 | UH-3·UH-4 |
| PM-2026-07-07 | 적용후 전면 미검증 | ⚠️ **K-ICS 게이트만** | **UH-1** |
| PM-2026-07-08 | V17 가짜복사 | ⚠️ **K-ICS 게이트만** | **UH-1** + 요구자본 COPY 검사 부재 |
| PM-2026-07-15 | 부모 census(라이브 공란) | ✅ 양쪽 | UH-2 |

**UH-1 (P1) — 이번 소급의 최대 발견:** 적용후 검증 7종
(`_transition_ratio_after_capture`·`_transition_mmult_after`·`_transition_identities_after`·
`_parent_present_child_incomplete_after`·`_diversification_negative`·`_item12_equals_item1`·
`_ratio_series_spikes`)이 **push 게이트에 미배선**입니다. 근거(코드 확인):
`validate_data_contract.py`의 `check_census`는 `kics_json_rules.run_validation`의 **rule-based 결과만**
lift하고, **`prepush_check.py`는 `validate_kics_disclosure.py`를 import조차 하지 않습니다.**
→ 07-07·V17 사고의 대응 룰 전부가 **push를 막지 못합니다.** 정확히 발주서의 "룰로 안 굳어 재발" 상태.

**UH-2 (P1):** `scripts/validate_data_contract.py`가 **git untracked**(머신-로컬) → push 게이트 배선이
git에 없습니다. V18 부모 census 배선도 이 머신에만 존재.
**UH-3 (P2):** provenance Phase-2 end-state 미강제(sidecar 없는 마스터는 추론 fallback 통과).
**UH-4 (P2):** data-contract `--selftest` 모듈 부재로 게이트 자체 회귀 검증 불가.

### 스코프 준수

발주서대로 **프로세스 정비만** 수행. census RED 잔여(흥국생명·하나생명 2024.4Q)는 안 건드렸고
별건으로 유지 중(현 push 게이트 RED=0, 두 건은 owner 승인 exemption 등재 상태).

**UH-1/UH-2 배선 발주 여부는 owner 판단 대기** — 지시하시면 게이트 배선 작업으로 착수하겠습니다.
