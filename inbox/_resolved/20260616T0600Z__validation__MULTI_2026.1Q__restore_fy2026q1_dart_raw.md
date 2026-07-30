---
from: validation
to: downloader
created: 20260616T0600Z
status: resolved
route: refetch
company: 교보생명, 메리츠화재, 신한라이프, 에이비엘생명, 푸본현대생명 (+ 2026.1Q IFRS17 cohort)
period: 2026.1Q
lane: ifrs17
iter: 1
escalation: owner
---

## 미결 (validation, owner 직접 지시 2026-06-16) — FY2026_Q1 DART raw 복원(재취득)

**owner 확정: CSM 워터폴 2026.1Q 기시(opening) CSM이 전사 misparse.** owner가 원본에서 직접 검증한
2026.1Q 기시 CSM은 전부 **직전 2025.4Q 기말과 동일**(정상 연속성)인데, master는 엉뚱한 값이 박혀 있음:

| 회사 | master 2026.1Q 기시(틀림) | 정답(=2025.4Q 기말, owner 검증) | 단위 |
|---|---|---|---|
| 교보생명 | 70,769 | **65,110** | 억원 |
| 메리츠화재 | 111,894 | **111,037** | 억원 |
| 신한라이프 | 74,423 | **75,537** | 억원 |
| 에이비엘생명 | 9,230 | **9,702** | 억원 |
| 푸본현대생명 | 1,669 | **1,907.45** | 억원 |

재파싱이 필요하나 **`data/dart/FY2026_Q1/` 디렉토리 자체가 부재**(git-purge 2026-06-14로 raw 삭제,
2026.1Q 셀은 purge 전 추출값이 frozen 상태). → **재추출 불가**.

### 요청
**DART에서 2026.1Q 분기보고서 raw를 재취득해 `data/dart/FY2026_Q1/raw/`로 복원.** DART는 공개 원천이고
2026.1Q 분기보고서(2026-05경 공시)는 영구 게시되어 있으므로 재다운로드 가능(origin/data 재팽창 아님 —
원천 DART에서 새로 받는 것). 우선순위 = 위 5사(교보/메리츠/신한라이프/에이비엘/푸본현대), 이어서
2026.1Q IFRS17 cohort 전체(CSM 워터폴 보유사). 회사명으로 DART 검색(영구 매핑 파일 금지, 메모리 규칙).

복원되면 parser/ifrs17가 2026.1Q CSM 워터폴 재추출(`inbox/parser/20260616T0605Z__validation__...
csm_2026q1_opening_misparse`). 복원 전까지 해당 셀은 게이트 RED(CONT) 유지.

## 답변 (downloader 2026-06-16 — 우선 5사 2026.1Q 복원 + 연속성 깨진 FY2023/FY2024 동반 재취득)

owner 지시(2026.1Q 기시 misparse) + 사용자 추가 지시("26.1Q 전부 말고 5사 먼저, 24.4Q/25.1Q는
continuity break된 것만") 반영. `ifrs17_batch_historical.py --skip-extract`(fetch-only).

### 1) 우선 5사 2026.1Q 분기보고서 복원 (`data/dart/FY2026_Q1/raw/`)
교보(KR0073)·메리츠화재(KR0001)·신한라이프(KR0094)·에이비엘(KR0070)·푸본현대(KR0083) = **5/5 fetched**,
CSM 블록 전수 존재(보험계약마진 76/108/96/138/86). 회사명 검색(영구매핑 없음).

### 2) continuity 전수 점검(`validate_csm_continuity.py`) → 깨진 건만 동반 재취득
점검 결과 break는 **24.4Q/25.1Q 경계가 아님** — 실제 위치:
- **FY 경계**: 코리안리 **2023.4Q기말 8032 ≠ 2024.1Q기초 10641**(Δ32.5%) / 푸본 2025.4Q→2026.1Q(위 5사로 커버)
- **FY내 기초 드리프트**: 현대·에이비엘·KDB·교보 = **FY2023** / KB라이프·코리안리 = **FY2024**

→ 해당 raw 동반 fetch:
- **FY2023 Q1-Q4** (현대 KR0009·에이비엘 KR0070·KDB KR0072·교보 KR0073·코리안리 KR1000) = **20/20**
- **FY2024 Q1-Q4** (KB라이프 KR0099·코리안리 KR1000) = **8/8**
- 전 cell CSM 블록 존재(보험계약마진 48~382). Q4=사업보고서(연간, A001), Q1-3=분기/반기.

**합계 33/33 fetched, 실패 0, CSM 블록 결손 0.** raw gitignore(git 재팽창 무관, origin/data 아님).

복원 완료 → parser/ifrs17 raw-ready `inbox/parser/20260616T0640Z`. 파서가 재추출하면 2026.1Q 기시 정상화
(=2025.4Q 기말 연속) + FY2023/FY2024 드리프트·코리안리 23.4Q→24.1Q 경계 수렴 예상. status: resolved, `_resolved/` 이동.
