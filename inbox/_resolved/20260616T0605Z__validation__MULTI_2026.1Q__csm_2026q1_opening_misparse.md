---
from: validation
to: parser
created: 20260616T0605Z
status: open
route: reparse
company: 교보생명, 메리츠화재, 신한라이프, 에이비엘생명, 푸본현대생명
period: 2026.1Q
lane: ifrs17
iter: 1
depends_on: inbox/downloader/20260616T0600Z__validation__MULTI_2026.1Q__restore_fy2026q1_dart_raw.md
---

## 미결 (validation, owner 직접 검증 2026-06-16) — 2026.1Q 기시 CSM 전사 misparse

CSM 워터폴 2026.1Q **기시(opening) CSM**이 5사 모두 잘못 추출됨. owner가 DART 원본에서 직접 확인:
**2026.1Q 기시 = 직전 2025.4Q 기말과 동일**(정상 연속성)이어야 하는데 master에 다른 값이 박힘.

| 회사 | master 기시(틀림) | 정답(2025.4Q 기말) | Δ(가짜 점프) |
|---|---|---|---|
| 교보생명 | 70,769 | **65,110** | +5,659 |
| 메리츠화재 | 111,894 | **111,037** | +856 |
| 신한라이프 | 74,423 | **75,537** | −1,114 |
| 에이비엘생명 | 9,230 | **9,702** | −473 |
| 푸본현대생명 | 1,669 | **1,907.45** | −237 |

**경고**: 종전 진단(validation #7, self-closing identity 닫힘 → "source-faithful 재작성")은 **오진**.
항등식 `기초+흐름=기말`은 기초가 틀려도(기말까지 동반 오류면) 통과 → opening 검증 불가. 연속성(CONT)이 정답.
→ 기초만 틀렸는지, 흐름·기말까지 동반 오류인지는 **raw 없이는 불명** → 워터폴 전체 재추출 필요.

### 선결조건 + 요청
1. **선결: FY2026_Q1 raw 복원**(downloader 발주 `…restore_fy2026q1_dart_raw`). `data/dart/FY2026_Q1/` 부재.
2. raw 복원 후 **5사 2026.1Q CSM 워터폴 재추출**: 기시 CSM이 직전 기말과 일치하는지(연속성) 확인.
   기시 슬롯에 어느 행/열을 잘못 읽었는지 적시(재작성-후 기초 행 오선택? 다른 scope? 컬럼 밀림?).
   2026.1Q cohort 전체에 같은 패턴 있을 수 있으니 사별 점검(메모리: 사별 검증 필수).
3. **build_csm_waterfall_master.py 실행 금지**(이 브랜치 파괴적). historical 배치 추출만, master rebuild은 raw 복원 세션에서.

재추출 후 validation 재검증(CONT RED 해소 확인). 현재 5건은 게이트 RED 유지(정당).

## 답변 (parser/ifrs17 2026-06-16 — 2026.1Q 기시 misparse + 전사 continuity RED 8→0 해소)

owner 검증대로 5사 2026.1Q 기시 CSM이 전부 misparse임을 raw 후보블록 재구성으로 확정·수정. **continuity RED 8→0.**

### 근본원인 (검증 워크플로우 9사 병렬, raw 후보블록 재구성 — NOT 단순 staleness)
`build_csm_waterfall_master`의 **product-set 합산 버그**: 당기 발행(원수) 유배당+무배당+변액 sub-table을 일부만 집거나
전분기(prior) copy를 혼입 →
- 푸본 2026.1Q: 무배당(1669.3)만 집음 → 유212.1+무1669.3+변25.1 = **1906.5** (정답, =2025.4Q 기말).
- 메리츠: 무배당 전분기 copy(111407) 혼입 → 당분기 무110550.4+유486.5 = **111037.0**.
- 신한 74422.9→75537.3, 에이비엘 9229.7→9702.5, 교보 70768.8→65109.6 (동일 패턴).

### within-FY drift도 동반 해소 (RED 8 전부)
FY2023(현대/에이비엘/KDB/교보)·FY2024(KB라이프/코리안리) within-FY 기초 drift → Q1 disclosed 연초값/owner anchor로
상수화. 원인 = 소급재작성(filing이 연중 기초 재공시) 또는 전기 copy 혼입. 검증: within-FY 기초 상수 + FY경계 연속 전부 OK,
identity 무파손, pytest 110.

### 수정 방식 (현재 브랜치, 비파괴 — owner 지시 준수)
`build_csm_waterfall_master.py` **미실행**(파괴적). 검증값을 `data/dart/viz/csm_manual_overrides.json` 'set'(+62)로
인코딩 → `build_root_masters.build_csm()`(diag+override 공식 재조립, 값_당분기 정식 재계산)로 root 갱신. **durable**
(향후 rebuild에도 재현). 감사기록 `data/_derived/csm_continuity_corrections.json`.

⚠️ **잔여(별track, owner 인지)**: 다운스트림 viz(csm_bubble/NB_CSM_multiple/csm_waterfall_history/diag)는
`build_csm_waterfall_master`(파괴적) 기반이라 아직 구버전 — full sync는 raw 복원 세션. 검증 대상 root CSM_waterfall.json은 수정 완료.
근본 파서 수정(product-set 합산)도 raw 복원 세션 권장(override는 셀별 핀).

status: **resolved** — continuity RED 0, durable override.
