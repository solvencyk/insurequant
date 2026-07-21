# PM-2026-07-07 — 경과조치 "적용후"가 전면 미검증(모든 룰이 적용전만 봄)

> 상태: `closed` (2026-07-21 UH-1 배선 완료 — push 게이트 lift)
> 발견 경로: owner 지적 (2026-07-07) — "모든 룰은 적용전·적용후 동일 적용"
> 관련: `TODO_validation.md` V17 · 게이트 배선 커밋 `70df46f`

## 0. 사실관계 (blameless)

K-ICS 공시는 각 항목에 **적용전(`값`)** 과 **경과조치 적용후(`값_적용후`)** 두 계열이 있다.
검증 룰(R1~R8·8_life·19_market·36_irr)은 **전부 `값`(적용전)만** 입력으로 썼다. 결과적으로
`값_적용후` 계열은 **어떤 산술 검증도 받지 않은 채** 라이브 화면(적용후 모드)에 표시돼 왔다.

영향: 경과조치 적용사 전체 × 전 분기의 적용후 계열. 라이브 노출.

---

## 1. 무엇이 통과했나

- 통과 당시 게이트 상태: **RED=0** (적용전 기준 등식 전부 닫힘).
- **못 잡은 이유**: 룰의 입력이 `bucket.get(item)` = `값` 고정. `값_적용후`는 **입력으로 읽히지도
  않았다.** 검사 대상이 아니었으므로 틀려도 통과할 수밖에 없다.

> false-green 메커니즘: **검증 축이 두 개인데 한 축만 검사했다.** 적용전이 완벽하면 RED=0이 나오고,
> 그 RED=0이 적용후의 정당성까지 보증하는 것처럼 읽혔다.

## 2. 어떤 룰이었으면 잡았나

| 항목 | 내용 |
|---|---|
| 룰 id | `TRANSITION_AFTER_ALL_RULES` (적용후 항등식 + mmult + 비율 무결성) |
| 입력 | `값_적용후` 계열, 선택경과조치 적용사 18사(FSS 2023-03-20 붙임-1 정본) |
| 판정식 | ① 항등식후: R1 `1=2+3` · R2 `4=Σ5..11` · R5 `14=15-22+23` · R6 `16=Σ17..21-15` · R7 `27=1/14×100` · R8 `28=2/14×100` ② mmult후: `item17후=√(29~35후·R7)`, `item19후=√(36~40후·M)` ③ 비율후: 적용사면 후>전(분자≥0일 때), 후≈전=COPY, 비율만 패치·금액후 미수정=AMT_MISMATCH |
| 임계값 | 합-항등식 `max(2.0, 0.5%·|exp|)` / mmult `max(2.0, 5%·|exp|)` / 비율 2.0%p |
| severity | RED |
| 오탐 억제 | **분자 음수(자본잠식) 회사는 방향성 검사 제외** — 분모만 줄면 비율이 더 음수가 되는 게 수학적 정상(롯데손해·케이디비·푸본·IBK 확인). 입력 결측 셀은 검사 skip(별도 census 소관) |

## 3. 그 룰이 지금 배선됐나

| | 함수/규칙 | 파일 | scope | exit-code |
|---|---|---|---|---|
| K-ICS 게이트 | `_transition_identities_after` · `_transition_mmult_after` · `_transition_ratio_after_capture` | `scripts/validate_kics_disclosure.py` | 전분기 | ✅ |
| **push 게이트** | `check_census` 1b(iv) → `TRANSITION_AFTER_IDENTITY` · `TRANSITION_AFTER_MMULT_MISMATCH` · `TRANSITION_AFTER_{COPY\|MISSING\|LOWER\|AMT_MISMATCH}` | `scripts/validate_data_contract.py` | display 7분기 | ✅ (2026-07-21) |

✅ **2026-07-21 UH-1 해소.** 최초 대응(2026-07-07)은 K-ICS 게이트에만 배선돼 **push를 못 막는 절반 상태**로
석 달 가까이 남아 있었다 — `validate_data_contract.py`의 `check_census`가 `kics_json_rules.run_validation`의
rule-based 결과만 lift했고, **`prepush_check.py`는 `validate_kics_disclosure.py`를 실행조차 하지 않기 때문.**
이 포스트모템 소급 작업이 그 사실을 적발했고, `check_census` 1b(iv)에 lift해 push 차단 경로로 굳혔다.

**배선 실효 검증(주입 테스트)**: display-scope를 2023.1~3Q까지 임시 확장하면 baseline RED 0 → lifted-rule
RED 4건(예별손해 3분기·IBK연금) 방출 확인 = 함수→`_emit`→`res.add`→RED 경로 end-to-end 작동.

⚠️ **K-ICS 전용 (owner 2026-07-21)**: 경과조치는 K-ICS 고유의 적용전/적용후 이중공시다. IFRS17에는
대응 개념이 없으므로(전환방법=수정소급/공정가치는 도입시점 측정방법이지 이중컬럼이 아님) 이 룰군의
IFRS17 유사룰을 만들지 말 것.

## 4. documented exception

- 있음: `_AFTER_SUBRISK_NOT_DISCLOSED` (`scripts/validate_kics_disclosure.py`) — 7셀
  (하나생명 2024.4Q·2026.1Q, 농협생명 2023.1Q, 처브 2024.3Q, 흥국화재 2024.4Q, 롯데손해 2026.1Q,
  교보생명 2026.1Q). 근거: raw에 적용후 세부표 부재/결합공식 불명/image-only PDF.
- 등재 권한: **owner**. 서브에이전트 자체판단 waiver 금지.

## 5. 미배선 잔여 + 후속 티켓

| 잔여 | 왜 위험 | 후속 / 우선순위 |
|---|---|---|
| ~~UH-1 적용후 검증 3종 push 게이트 미배선~~ | — | ✅ **2026-07-21 해소** (owner 승인, `check_census` 1b(iv)) |
| **없음** (이 사고 한정) | — | — |

---

## close 체크

- [x] 1 무엇이 통과했나
- [x] 2 구체 룰 정의
- [x] 3 배선 — **K-ICS ✅ + push ✅ 양쪽** (2026-07-21)
- [x] 4 exception 등재 위치 명시
- [x] 5 잔여 없음(UH-1 해소)

**→ closed (2026-07-21).**
