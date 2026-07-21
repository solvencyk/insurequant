# PM-2026-07-15 — 적용후 요구자본 **부모** 결측이 등식 다 닫힌 채 push 통과 → 라이브 공란

> 상태: `closed` (양쪽 게이트 배선 완료 · 잔여 UH-2는 후속 이관)
> 발견 경로: owner 라이브 QA — K-ICS.html 적용후 모드에서 요구자본 세부 공란
> 관련: `inbox/validation/20260715T0801Z…post_transition_parent_census_blindspot.md` · 커밋 `20bb4ff` · 배포 `25d8e98`

## 0. 사실관계 (blameless)

2026.1Q push 게이트가 통과한 상태로 배포됐는데, 라이브 K-ICS.html **적용후 모드**에서 요구자본 세부
(17 생명장기·18 일반손해·19 시장위험액)가 **공란**으로 노출됐다. 5개 경과조치 적용사
(KR0068 한화생명·KR0073 교보·KR0097 하나·KR0003 롯데손해·KR0104 농협)의 `값_적용후`가 결측.

`값`(적용전)은 39사 전부 완비 → 적용후 모드가 폴백 없이(base-mixing 방지 설계) 공란 렌더.

영향: 2026.1Q 5개사 요구자본 부모 항목, **라이브 노출**. 소급 census 결과 과거분기 포함 117셀/18(회사,분기).

---

## 1. 무엇이 통과했나

- 통과 당시 게이트 상태: push 게이트 **RED=0**, K-ICS 산술룰 전부 정합.
- **못 잡은 이유 (구조적)**: PM-2026-07-07로 켠 적용후 검사들이 전부 **"부모후가 present일 때만"**
  동작하도록 짜여 있었다.
  - `_parent_present_child_incomplete_after`: `post_p is None → continue`
  - `_transition_mmult_after`: `post_p is None → continue`
  - `_transition_identities_after`: 입력 결측 셀은 skip("genuine 적용후 입력 완비 셀만")
  → **부모(15~21)후가 통째로 없으면 세 검사가 전부 skip.** 산술 등식은 적용전 기준으로 다 닫혀 RED=0.

> false-green 메커니즘: **"있는 것의 정합성"만 검사하는 룰들은, 그 입력 자체가 없어지면 일제히 침묵한다.**
> 결측이 검사를 *트리거*하는 게 아니라 *무력화*했다. (SKIP-on-missing의 상위 버전 —
> `feedback_coverage_census_mandatory` 원칙이 부모 레벨에는 미적용이었음.)

부수 원인: 기존 적용후 검사는 `_TRANSITION_APPLIERS`(elective 18사) 하드코딩이라 **공통경과조치사인
한화생명(KR0068)·삼성생명(KR0069)은 대상에서 빠져** 있었다.

## 2. 어떤 룰이었으면 잡았나

| 항목 | 내용 |
|---|---|
| 룰 id | `POST_TRANSITION_PARENT_MISSING` (부모후 continuity census) |
| 입력 | 요구자본 부모 `값_적용후` — 코어 15·16·17·18·19·20·21 / 조정 22·23. **적용사 판정 = continuity 자체**(별도 seed 없음 → 공통경과조치사도 포착) |
| 판정식 | (회사,항목) 시계열에서 **직전 공시분기에 `값_적용후` present인데 당 분기 결측**이고, 이후 재출현(SANDWICHED) 또는 당 분기가 최신(TRAILING) → RED |
| 임계값 | 임계값 없음(presence 기반). 적용전 `값` present(=행 실재) 분기만 대상 |
| severity | RED (코어 15~21). 22/23은 코어 break 동반 시만 RED, 단독은 review(비차단) |
| 오탐 억제 | ① **도입초 onset 제외**(직전에 적용후가 없으면 break 아님) ② **항구적 중단 제외**(직전만 있고 이후 계속 없으면 구조변화 가능) ③ **22 법인세조정·23 기타요구자본은 단독 flag 안 함** — 종속회사·법인세 유무로 legit-absent가 흔함 |

**근거 원칙**: `feedback_continuity_break_is_red` — 인접 분기에 적용후가 있었다는 건 그 회사가 그 항목의
적용후를 공시한다는 증거다. 따라서 당 분기 결측은 구조적 미공시가 아니라 **추출갭**이다.

## 3. 그 룰이 지금 배선됐나

| | 함수/규칙 | 파일 | scope | exit-code |
|---|---|---|---|---|
| K-ICS 게이트 | `_post_transition_parent_census` | `scripts/validate_kics_disclosure.py` | **전분기**(parser 워크리스트) | ✅ |
| **push 게이트** | `check_census` 1b(iii) `POST_TRANSITION_PARENT_MISSING` | `scripts/validate_data_contract.py` | **display 7분기**(push 차단) | ✅ |

✅ **양쪽 배선 완료.** 사고 4건 중 유일하게 push 차단 경로까지 굳은 건.

**실효 검증**: 갭 있을 때 push 게이트 census RED=47 → parser fill 후 → exemption 2건 등재 후 **RED=0**.
"갭→RED, 채움→통과"가 실측으로 확인됨.

## 4. documented exception

- 있음: `_POST_PARENT_NOT_DISCLOSED` (`scripts/validate_kics_disclosure.py`) — 2셀, **owner 승인 2026-07-16**
  - `(KR0071, 2024.4Q)` 흥국생명 — image-only PDF + TIR/TER 다중경과조치, R4 재현불가
    (역산 item15 14,747 vs 헤드라인 16,987, Δ2,240 비반올림)
  - `(KR0097, 2024.4Q)` 하나생명 — 비표준(감사보고서 재무상태표) 공시. item16후 산술파생은 가능하나
    입력 item17후=1757.32가 raw page(2001.90)와 불일치(partial-mmult 아티팩트 의심) → 파생값 불신
- 등재 기본값은 **빈 집합**이었고(owner "구조적 미공시로 오면제 금지"), 2건 모두 parser가 raw를
  소진한 뒤 owner 승인으로 등재.

## 5. 미배선 잔여 + 후속 티켓

| 잔여 | 왜 위험 | 후속 / 우선순위 |
|---|---|---|
| ~~UH-2 `validate_data_contract.py` git untracked~~ | — | ✅ **2026-07-21 해소** — push 게이트 체인 3종(`validate_data_contract.py`·`prepush_check.py`·`triage_anomaly_candidates.py`) git 등재. gitignore 아니라 단순 미추가였고, 나머지 의존성(`validate_kics_disclosure.py`·`validate_master_tables.py`·`kics_json_rules.py`)은 이미 tracked였음 |
| non-display 잔여 58셀(코리안리·악사·처브·IBK 2023.2Q·하나손/하나생 2023.2Q 등) | push 비차단(과거분기 비노출). 워크리스트로만 관리 | 저우선 |

---

## close 체크

- [x] 1 무엇이 통과했나 — 부모후 결측이 하위검사를 일제히 무력화
- [x] 2 구체 룰 정의 (오탐억제 3종 포함)
- [x] 3 배선 — **K-ICS ✅ + push ✅ 양쪽**
- [x] 4 exception 2셀 근거·등재 위치 명시
- [x] 5 잔여 UH-2 명시

**→ closed.** (UH-2는 이 룰의 *배선 영속성* 문제로 별도 추적)
