# PM-2026-06-16 — 두 달 글리치: "맞는 산수·틀린 소스"가 RED=0으로 통과

> 상태: `closed` (잔여 UH-3·UH-4는 후속 티켓으로 이관)
> 발견 경로: owner 라이브 QA 누적(두 달) → 근본원인 소급 분석
> 관련: owner spec `20260616T1155Z` §4 · `scripts/validate_data_contract.py`

## 0. 사실관계 (blameless)

약 두 달간 라이브 화면에 반복적으로 수치 글리치가 노출됐다. 매번 개별 증상을 고쳤으나 다른 형태로
재발했다. 소급 분석 결과 개별 파싱 실수가 아니라 **게이트의 검사 축 자체가 하나 비어 있던 것**이
원인이었다: 게이트는 **산술 정합성(등식이 닫히는가)** 만 봤고, **그 숫자가 올바른 소스·시점에서
왔는가**는 아무도 검사하지 않았다.

영향: 다수 마스터·분기(라이브 노출). 개별 셀 단위가 아니라 구조적.

---

## 1. 무엇이 통과했나

- 통과 당시 게이트 상태: 산술 룰(K-ICS R1~R8, IFRS17 closing identity 등) **RED=0**.
- **못 잡은 이유 (2중)**:
  1. **권고룰 미강제** — "이렇게 해야 한다"가 문서·honor 수준에만 있고 코드 게이트로 강제되지 않음.
  2. **게이트가 산술만 검사** — 등식은 *존재하는 숫자들끼리* 닫히면 통과한다. 소스가 stale하거나
     (2025.4Q 데이터를 2026.1Q로 렌더), 아예 빠진 칸이 있어도 등식은 그대로 닫힌다.

> false-green 메커니즘: **틀린 소스에서 온 숫자들끼리도 산술은 완벽히 닫힌다.** 정합성(consistency)을
> 완비성(completeness)·정확성(provenance)으로 잘못 등치한 것. (동형 교훈: `docs/LESSONS_2026-06-07.md` §0)

## 2. 어떤 룰이었으면 잡았나

| 항목 | 내용 |
|---|---|
| 룰 id | `DATA_CONTRACT`(census + as-of/provenance + same-concept guard) |
| 입력 | 전 마스터의 (회사 × 분기 × item-block) 기대그리드, 각 산출물의 `as_of`/`period`, 소스 enum |
| 판정식 | ① 기대그리드 대비 **결측 셀 = RED**(SKIP-as-pass 금지) ② 산출물 as_of 분기 ≠ 공시분기 → STALE_AS_OF RED ③ 자본증권 effective 필터 적용증거 없음 → RED ④ 구조적으로 **다른 개념**(tier2 Face vs BS)은 비교·감점 금지 |
| 임계값 | census 결측 0 허용 / as-of 분기 완전일치 / cross-source `max(5%, 100억)` |
| severity | 전부 RED (**exception 메커니즘 없음** — owner 2026-06-16) |
| 오탐 억제 | display 7분기 scope(`_DISPLAY_QUARTERS`) — git-purge된 과거분기 갭은 push 차단 안 함 |

핵심 설계원칙(owner): **싼 모델 + 하드게이트 > 비싼 모델 + honor.**

## 3. 그 룰이 지금 배선됐나

| | 함수/규칙 | 파일 | scope | exit-code |
|---|---|---|---|---|
| K-ICS 게이트 | `_coverage_census` 등 | `scripts/validate_kics_disclosure.py` | 전분기 | ✅ |
| **push 게이트** | `check_census` / `check_as_of` / `check_cross_source` / `check_domain_identity` / `check_generic_anomalies` | `scripts/validate_data_contract.py` (← `prepush_check.py`) | display 7분기 | ✅ RED>0 → exit 2 |

✅ **push 차단 경로에 배선됨.** 이 사고의 대응은 처음부터 push 게이트로 만들어져서 굳었다.

> **후속 정정 (2026-08-25).** 위 표의 `check_generic_anomalies` 는 **더 이상 push 게이트에 있지 않다**
> (commit `22697c2`). 애초에 YELLOW 전용이라 `blocked` 계산에 들어간 적이 없어 실제로 push 를 막은
> 적은 없었고, 게이트 YELLOW 297건 중 224건을 혼자 만들어 `scripts/scan_generic_anomalies.py` 로
> 분리했다. **폐지가 아니라 주기 변경** — 분기 라운드 1회 실행이 정본이다
> (`docs/agents/claude-agent-publishing.md` §3.0b). 나머지 4개 함수는 그대로 배선돼 있다.

## 4. documented exception

**없음.** owner 2026-06-16 명시: "RED=0 to pass, no exception mechanism — fix or owner-escalate."
(과거분기 갭은 exception이 아니라 `_DISPLAY_QUARTERS` **scope**로 처리 — 개념 구분 유지.)

## 5. 미배선 잔여 + 후속 티켓

| 잔여 | 왜 위험 | 후속 / 우선순위 |
|---|---|---|
| **UH-3** provenance Phase-2 end-state 미강제 | 소스 신선도 미검증 마스터가 조용히 통과 = 이 사고의 원형이 부분적으로 생존 | ⚠️ **2026-07-21 부분강화**: notes(비집계) → **YELLOW `MISSING_PROVENANCE_SIDECAR`**(집계, 현 4건)로 승격해 가시화. RED 전환은 **발행 후**(지금 RED면 미발행 마스터 전부 red-out → push 영구차단). 발행 발주: publishing `20260721T0530Z` · parser `20260721T0530Z` |
| ~~**UH-4** `--selftest` 모듈 부재~~ | — | ✅ **2026-07-21 해소**: `scripts/_data_contract_selftest.py` 신설, mutation suite **14/14 PASS**(이빨 검증 포함 — 룰 죽이면 FAIL 확인) |

---

## close 체크

- [x] 1 무엇이 통과했나 — 산술만 검사 + 권고룰 미강제
- [x] 2 구체 룰 정의 — census/as-of/concept-guard
- [x] 3 배선: **push 게이트 ✅**
- [x] 4 exception 없음(설계상 부재)
- [x] 5 잔여 UH-3·UH-4 명시
