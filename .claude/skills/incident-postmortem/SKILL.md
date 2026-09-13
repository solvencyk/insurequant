---
name: incident-postmortem
description: >-
  insurequant blameless 사고 포스트모템 — 게이트가 놓친 사고(false-green, 라이브 오표시, 검증 사각)를
  반드시 "구체 게이트 룰 + 배선 위치"로 종결시키는 로컬 관행. 5칸(무엇이 통과했나 / 어떤 룰이었으면
  잡았나 / 그 룰이 지금 어디에 배선됐나 / documented exception 근거·등재위치 / 미배선 잔여+후속티켓)이
  전부 차야 close 가능. Use this whenever: 게이트를 통과했는데 틀린 데이터가 발견됐을 때, owner가 라이브
  QA로 오류를 지적했을 때, RED=0인데 실제로는 결측·복사·stale이 있었을 때(false-green), 새 검증 룰을
  신설·배선한 뒤 이력을 남길 때, 기존 사고를 소급 기록할 때, 또는 "이거 왜 게이트가 못 잡았지"를 따질 때.
  이 저장소 특유의 함정을 강제로 확인시킨다: "배선했다"와 "실제로 push를 막는다"는 다른 말이라,
  룰을 어느 게이트에 넣었는지와 그 게이트가 훅에 걸려 있는지를 따로 확인해야 한다. 산출물은
  docs/postmortems/PM-<날짜>_<slug>.md, 색인과 미배선(UH) 목록은 docs/postmortems/README.md.
  NOT for: 일반 코드 버그 회고, 신규 데이터 파싱 작업, 성능 이슈 — 게이트가 놓친 데이터 정합성 사고 전용.
---

# 사고 포스트모템 — 게이트 룰로 종결

정본: [`docs/postmortems/README.md`](../../../docs/postmortems/README.md) ·
템플릿: [`docs/postmortems/_TEMPLATE.md`](../../../docs/postmortems/_TEMPLATE.md)

## 이 관행이 존재하는 이유

이 저장소 사고의 재발 경로는 항상 같다:

> 사고 → 메모·changelog 기록 → **게이트 룰로는 안 굳음** → 다른 형태로 재발

그래서 포스트모템의 성공 기준은 "잘 썼다"가 아니라 **"룰이 어디에 배선됐다"** 이다.
blameless: 원인을 사람이 아니라 **게이트의 사각**으로 서술한다.

## 작성 절차

1. `docs/postmortems/_TEMPLATE.md` 복사 → `docs/postmortems/PM-<YYYY-MM-DD>_<slug>.md`
2. 5칸을 채운다. **3번 칸은 반드시 두 게이트를 따로** 적는다(아래 함정 참조).
3. 3번이 "미배선"이면 5번에 **후속 티켓 파일명**을 적고 실제로 inbox에 발주한다.
4. `docs/postmortems/README.md` 색인 + 🔴 미배선(UH) 표 갱신.
5. `TODO_validation.md` / `docs/changelog_validation.md` 반영.

## ⚠️ 이 저장소의 핵심 함정 (3번 칸을 채울 때)

| 게이트 | 파일 | push를 막나 |
|---|---|---|
| K-ICS 게이트 | `scripts/validate_kics_disclosure.py` | ✅ **2026-08-21부터** `prepush_check.py` 단계 1b로 차단 |
| push 게이트 | `scripts/validate_data_contract.py` (← `scripts/prepush_check.py`) | ✅ display 7분기 scope로 차단 |
| 도메인 게이트 4종 | `validate_{csm_continuity,kics_rate_sensitivity,nb_csm_multiple,csm_waterfall}.py` | ✅ 2026-08-21부터 단계 1c |
| 일반 이상치 발견 | `scripts/scan_generic_anomalies.py` | ❌ **2026-08-25에 게이트 밖으로 분리** — YELLOW 전용이라 원래 막은 적 없다. 분기 라운드 1회 수동 실행(`claude-agent-publishing.md` §3.0b) |

**"배선했다"와 "실제로 push를 막는다"는 다른 말이다.** 3번 칸을 채울 때 룰을 어느 스크립트에 넣었는지
만으로 ✅ 하지 말고, **그 스크립트가 `prepush_check.py`에 걸려 있는지**를 확인하라
(`tests/test_push_gate_wiring.py`가 매니페스트로 강제한다). 2026-08-21 이전에는
`prepush_check.py`가 `validate_kics_disclosure.py`를 부르지 않아, K-ICS 게이트에만 배선한 룰이
push를 못 막았다 — 그때 쓰인 우회는 `validate_data_contract.py`의 `check_census`로 함수를 lift하는
것이었다(선례: `_post_transition_parent_census` → `check_census` 1b(iii), display-scope).
그 우회는 이제 불필요하지만, 옛 포스트모템에 그 서술이 남아 있으면 stale로 읽어라.

## 5칸이 요구하는 구체성

- **2번(어떤 룰)**: "검증을 강화한다" 같은 추상은 불합격. **입력 항목번호·필드(`값`/`값_적용후`)·판정식·
  임계값·severity·오탐억제**까지. 오탐억제가 없는 룰은 배선해도 곧 꺼진다.
- **3번(배선)**: 함수명 + 파일 + scope(전분기/display) + exit-code 반영 여부.
- **4번(exception)**: registry **변수명과 파일**까지. 이 저장소의 등재처:
  `_AFTER_SUBRISK_NOT_DISCLOSED` · `_POST_PARENT_NOT_DISCLOSED` · `_MARKET_BREAKDOWN_EXEMPT` ·
  `_IRR_SCENARIO_EXEMPT` · `_INTERNAL_MODEL_36IRR_EXEMPT` (전부 `validate_kics_disclosure.py`),
  `data/_gold/user_pl_confirmed_cells.json`.
  **exemption 추가는 owner 권한** — 서브에이전트 자체판단 waiver 금지.

## 반복 출현하는 false-green 유형 (원인 진단 시 먼저 대조)

| 유형 | 설명 | 선례 |
|---|---|---|
| **산술만 검사** | 틀린 소스에서 온 숫자끼리도 등식은 닫힌다 | PM-2026-06-16 |
| **검사 축 누락** | 적용전만 보고 적용후는 입력으로 읽지도 않음 | PM-2026-07-07 |
| **presence만 검사** | 결측만 RED → 복사로 세탁 가능 | PM-2026-07-08 |
| **입력 결측이 검사를 무력화** | 부모가 없으면 하위 검사가 일제히 skip (SKIP-on-missing 상위판) | PM-2026-07-15 |
| **적용사 집합 하드코딩** | elective 18사만 검사 → 공통경과조치사 사각 | PM-2026-07-15 |

## ⚠️ 도메인 경계 — 경과조치는 K-ICS 전용 (owner 2026-07-21)

경과조치(적용전 `값` / 적용후 `값_적용후` 이중공시)는 **K-ICS 고유**다. **IFRS17에는 대응 개념이 없다**
— 전환방법(수정소급/공정가치/그 외)은 도입시점 측정방법이지 이중컬럼이 아니므로 **복사할 짝 자체가
존재하지 않는다.** `TRANSITION_AFTER_*` 룰군의 IFRS17 유사룰을 만들지 말 것.

단 **상위 패턴은 도메인 무관**이다: "presence만 검사하면 세탁된다"는 IFRS17에서 분기 복붙·impossible-0
형태로 나타나며 `CSM_WATERFALL_PLAUSIBILITY` / `IMPOSSIBLE_ZERO_AMORT` / `IMPOSSIBLE_ZERO_LEG`가 담당.
→ **유형은 옮겨 쓰되, 룰은 그 도메인의 실제 공시구조에서 다시 유도할 것.**

## 현재 미배선(UH) — 새 포스트모템 쓰기 전 확인

`docs/postmortems/README.md` 하단 표가 정본. **2026-07-21 기준: UH-1·UH-2·UH-4 해소**
(적용후 7종 → `check_census` 1b(iv) lift · push 게이트 체인 3종 git 등재 · selftest 신설 14/14).
잔여: **UH-3**(sidecar 발행 대기, 현재 YELLOW로 가시화) · **UH-5**(선행 레지스트리 미충족).

**새 룰을 만들기 전 반드시**: `python scripts/validate_data_contract.py --selftest` 로 기존 14 케이스가
깨지지 않는지 확인하고, 새 룰에는 **케이스를 추가**한다(`scripts/_data_contract_selftest.py`).
케이스 없는 룰은 다음 리팩터에서 조용히 죽는다.

## 룰을 "안 만드는" 것도 결론이다

UH-5(요구자본 COPY 검사)는 구현하지 않았다 — elective 18사 중 요구자본 후=전인 셀이 78개이고
6개사는 전 분기가 그러한데, 그건 오류가 아니라 **TAC형 경과조치(가용자본만 영향)의 정상 결과**다.
선행 레지스트리(회사별 TIR/TAC 구분) 없이 배선하면 78셀 오탐 → 룰이 곧 꺼진다.
**오탐억제를 설계할 수 없으면 배선하지 말고, 선행조건을 5번 칸에 적어라.**

새 사고가 기존 UH와 같은 뿌리면 **새 UH를 만들지 말고 기존 UH에 합류**시킨다.
