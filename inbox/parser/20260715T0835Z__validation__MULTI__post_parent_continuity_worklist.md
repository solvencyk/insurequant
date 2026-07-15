---
from: validation
to: parser
created: 20260715T0835Z
status: answered
route: reparse
company: MULTI
period: 2024.4Q~2025.4Q
lane: kics
iter: 1
---

## 미결 — 적용후 요구자본 부모(15~21) continuity break (신설 게이트 표면화)

owner `20260715T0801Z`(post_transition_parent_census blind spot) 대응으로 **신설한 게이트
`_post_transition_parent_census`**(scripts/validate_kics_disclosure.py)가 표면화한 갭 목록.
당신이 병행 처리한 owner 티켓 `20260715T0801Z__…__post_transition_scr_subtable_gap.md`(2026.1Q 5사)는
**이미 fill 완료 확인**(2026.1Q census RED=0). 아래는 **그 외 display 분기 갭 = push 게이트 차단 중**.

**판정 로직**: (회사,항목) 값_적용후가 직전 공시분기엔 있는데 당 분기 결측 + (이후 재출현 or 최신분기)
= 추출갭 시그니처(continuity-break-is-RED). 인접분기에 적용후가 있으니 구조적 미공시 아님.

### 🆕 신규 발견 (owner 2차 목록에 없던 것 — 최우선)
| 회사 | 분기 | 결측 부모후 | 근거 |
|---|---|---|---|
| **삼성생명 KR0069** | 2025.1Q | 16,17,18,19,20,21 (+22,23) | 2023.1Q~2026.1Q **매분기 적용후 공시**, **2025.1Q만** 16~21 유실(item15후는 있음) = 명백 파싱유실 |
| **흥국생명 KR0071** | 2024.4Q | 15,16,17,18,19,20,21 (+22) | 전분기(2024.3Q)·다음분기(2025.1Q) 다 present, 2024.4Q만 표 전체 유실 |

### owner 2차 목록(이미 인지) — 재확인 요청
| 회사 | 분기 | 결측 부모후 |
|---|---|---|
| 한화생명 KR0068 | 2025.2Q | 16~21,22,23 |
| 한화생명 KR0068 | 2025.3Q | 15 |
| (참고: 한화 2024.3Q = 전항목, non-display 비차단) | | |

### raw 확인 필요 (구조적 미공시면 exemption 회신)
| 회사 | 분기 | 결측 부모후 | 비고 |
|---|---|---|---|
| 동양생명 KR0087 | 2024.4Q | 16~21,22,23 | scan/image PDF 이력. item15후는 있음 → 부모후 breakdown만 유실 여부 확인 |
| 동양생명 KR0087 | 2025.1Q | 15 | |
| 동양생명 KR0087 | 2025.4Q | 16~21,22,23 | |
| 하나생명 KR0097 | 2024.4Q | 16,18,19,20,21 | 기존 `_AFTER_SUBRISK_NOT_DISCLOSED`(감사보고서 스타일, phase-in 10%만). **부모 요구자본후도 진짜 미공시**면 그 취지 회신 → owner가 `_POST_PARENT_NOT_DISCLOSED` 등재 |

### 처리
1. 각 (회사,분기) 원본 MD/PDF 지급여력 요구자본 표의 **'적용후' 컬럼** 확인.
2. 있으면 15~21(+가능시 22/23) 값_적용후 추출·UPSERT (fill 스크립트 영구반영, idempotent).
3. raw에 부모후 컬럼 진짜 부재면 → 회사·분기별 취지 `## 답변` 명기(구조적 미공시). owner가 exemption 등재.

### 완료기준
`python scripts/validate_kics_disclosure.py` → **"적용후 요구자본 부모 continuity break: 0"**
(또는 잔존분은 전부 raw부재 확인분 → owner exemption 대기). 라이브 목록은 게이트 실행 시
`artifacts/kics_validation/report_latest.json` `post_transition_parent_census.red`가 정본.

**non-display/비차단(우선순위 낮음)**: 코리안리 KR1000(2023.2Q·2024.1Q·2024.3Q 16~21 간헐)·처브 KR0100
2024.3Q·농협생명 2023.2Q 등은 push 차단 안 함(과거분기 비노출). 22/23 단독(IBK연금 2026.1Q 등)은
종속회사/법인세 legit-absent 가능 → review, 이 티켓 대상 아님.

## 답변 (parser 작성 2026-07-15)

**신규 발견 최우선 2건 + raw확인필요 2건 처리, continuity break 96셀/14쌍 → 62셀/10쌍.**

### ✅ 완전 해소 (raw 재대조, 전부 "선택경과조치 완전 미적용" 패턴)
- **삼성생명(KR0069) 2025.1Q**: raw 명시("당사는 [자본감소분/장수위험 등/주식위험] 경과조치를
  적용하지 않아 전후 동일") — 16-23후=전 미러링.
- **동양생명(KR0087) 2024.2Q·2024.4Q·2025.1Q·2025.2Q(연쇄로 신규 노출)**: 전 분기 공통 "당사는
  공통적용 경과조치만 적용하였습니다"(선택 ①②③ 전부 X) — 15/16-23후=전 미러링. (2025.1Q 채우자
  2025.2Q가 새로 sandwiched로 노출 → 같은 raw로 즉시 해소, 이 회사 체인은 이제 완전)

### ⚠️ 부분 해소 (raw 확인, 진짜 파싱갭이었으나 일부 항목은 다중경과조치 결합불가로 잔존)
- **하나생명(KR0097) 2024.4Q**: raw는 표준 정기경영공시 아니라 **"지급여력 및 건전성감독기준
  재무상태표"(감사보고서 첨부) 스타일**(`FY2024_Q4/raw/…pdf` p.281, 단위 천원). item18/19/20/21/22/23
  이 페이지에서 확정 채움(19만 실변화, 나머지 전후 동일 확인). **item17후=1757.32(기존 저장값)가 이
  페이지 값(2001.90)과 불일치·재현 안 됨** — item29-35 부분채움(해지/사업비만 있고 장수/대재해는
  아직 None)에서 유래한 것으로 추정되나 원출처 특정 못함. item17을 건드리지 않아 **item16(분산효과)도
  같이 보류**. 잔존 [16] — item17 출처 재확인 필요(validation 쪽에 원 fill 이력 있으면 공유 요청).
- **흥국생명(KR0071) 2024.4Q**: **image-only PDF**(0-111p 스캔, 8차 changelog 선례) — fitz 텍스트
  실패, **비전으로 렌더링 페이지 직접 판독**(p.44 총괄·p.47 적용여부·p.50 ②표·p.51 ③표).
  TIR+TER 동시적용, item17(②표, ③에서 시장 불변 확인)·item19(③표, ②에서 생명 불변 확인)·18/20/21
  (양표 일치)은 안전 채움. **item22/23는 ②③ 두 표가 서로 다른 값**(348,792/599,206 vs
  429,635/703,625백만) — 어느 쪽도 신뢰 headline(item14=16,987, p.44 총괄 기존확인값)과 R4로
  재현 안 됨(disjoint 17/19로 역산한 item15=14,747 vs 헤드라인 14=16,987, 차이 ~2,240으로 큼,
  단순 반올림 아님) — **진짜 다중결합 불명 케이스**로 판단, item15/16/22/23은 그대로 둠.
  잔존 [15,16,22] — `_POST_PARENT_NOT_DISCLOSED` 류 owner exemption 검토 요청.
  (`scripts/_probes/verify_r4_hkl_2024q4.py`, `render_hkl_pages.py`)

### 손 안 댐 (ticket의 "non-display/비차단" 지정 그대로 존중)
코리안리(KR1000) 3분기·처브(KR0100) 2024.3Q — ticket 지정대로 미착수.

### 미확인 (ticket 표에 명시 안 됐던 잔여, 다음 라운드 후보)
하나손해(KR0050) 2023.2Q·하나생명(KR0097) 2023.2Q(2024.4Q와 별개 분기)·악사손해(KR0049) 2024.3Q —
raw 미확인, 구조적 미공시인지 파싱갭인지 미판정.
IBK연금(KR1011) 2023.2Q는 **이미 알려진 documented exception**(5차 라운드,
`_AFTER_SUBRISK_NOT_DISCLOSED` — 다중경과조치 결합 raw로 불가 확정, None이 정답) — 이 게이트가 재적발한
것뿐, 파싱갭 아님. 게이트에 이 예외 등록 반영 권장.

**검증**: `validate_kics_disclosure.py` continuity break 96→**62**셀(14→10쌍). core RED 12(무관
기존건, 회귀 0). `pytest` 110 passed. xlsx 재생성 완료.

스크립트: `scripts/fix_20260715_round3_continuity_gaps.py` + `…round3b_dongyang_2025q2.py`.
