---
from: downloader
to: parser
created: 20260703T1215Z
status: resolved
route: parse
company: KR1011 IBK연금보험
period: 2023.1Q~2025.3Q (11분기)
lane: kics
---

## 발주 (downloader → parser-kics) — IBK연금보험 K-ICS 11분기 파싱 미완료

### 현황

- **raw PDF**: FY2023_Q1 ~ FY2026_Q1 전 분기 존재 ✅
- **parsed MD**: FY2025_Q4, FY2026_Q1 만 존재 ✅
- **kics_disclosure.json**: 2025.4Q, 2026.1Q 만 적재 ✅
- **미파싱 11분기**: 2023.1Q~2025.3Q

### 대상 PDF 경로

```
data/disclosure/FY2023_Q1/raw/KR1011_IBK연금보험.pdf
data/disclosure/FY2023_Q2/raw/KR1011_IBK연금보험.pdf
data/disclosure/FY2023_Q3/raw/KR1011_IBK연금보험.pdf
data/disclosure/FY2023_Q4/raw/KR1011_IBK연금보험.pdf
data/disclosure/FY2024_Q1/raw/KR1011_IBK연금보험.pdf
data/disclosure/FY2024_Q2/raw/KR1011_IBK연금보험.pdf
data/disclosure/FY2024_Q3/raw/KR1011_IBK연금보험.pdf
data/disclosure/FY2024_Q4/raw/KR1011_IBK연금보험.pdf
data/disclosure/FY2025_Q1/raw/KR1011_IBK연금보험.pdf
data/disclosure/FY2025_Q2/raw/KR1011_IBK연금보험.pdf
data/disclosure/FY2025_Q3/raw/KR1011_IBK연금보험.pdf
```

### 요청

1. 위 11개 PDF → docling MD 변환 (`data/disclosure/FY<y>_Q<q>/parsed/KR1011_IBK연금보험.md`)
2. 각 MD → kics_disclosure.json 파싱 적재 (KR1011, 원수사명=IBK연금보험)
3. 연금전업사 특성: 자동차/일반 항목은 0 또는 부재 정상. 생보 계열 표 구조 적용.
4. 파싱 완료 후 validation gate 돌릴 것 (RED=0 확인).

### 배경

IBK연금보험 주요사 격상 (owner inbox 20260703T1138Z). IFRS17 raw는 별도 handoff 완료(`20260703T1200Z`). K-ICS는 이 발주.

## 답변 (recipient 작성 — 처리 후) — 2026-07-04 parser-kics DONE

11분기(2023.1Q~2025.3Q) 파싱 완료, kics_disclosure.json 적재. 게이트 RED=0 (KR1011 순증 RED 0).

**처리:**
1. docling MD 11개 생성 (`run_harness --stage parse`, rc=0 전부, FY2024_Q4 7.87MB bad_alloc 없이 통과).
2. fill_period/subitems/market_subitems 적재. 13분기 census 정합 — item27 궤적 매끄러움(68.85→…→143.56→119.23, 연금사 자본증강 추세).
3. **item28 기본자본비율** 11분기 산출·삽입 (MD 미공시 → item2/item14×100 직접산출). rule 8 ×11 RED 해소.
4. **2023.2Q 시장 subs(36-40)+IRR(41-46) 복구**: docling이 ③주식위험액 섹션을 통째 누락 → fitz로 raw p22에서 주식위험액=1,655.98억 복구. 5개 sub로 MARKET_M reconcile 검증 item19=4,610.15 vs 공시 4,610 ✓. rule 19_market RED 해소.

**연금전업사 특성 확인:** 일반손해(item18)=0 ✓ · #35 대재해위험액 = 생명장기 sub표에 원천부재(경과조치표에만 "대재해위험 0") → #35 absent 정상, 8_life SKIP.

**잔여(별건, 비-RED):** IBK는 경과조치 적용사(적용전 68.85 / 적용후 165.93)인데 신규 11분기 item1-28 **값_적용후 미포착**. → owner 전수건 `20260703T1138Z__owner__MULTI__transition_after_capture_systematic`(22 적용사)에서 함께 처리 예정. 지금은 적용전 값 기준 게이트 통과.

**TODO(파서):** 마스터 xlsx 재빌드(잔여 인박스 데이터수정과 함께 배치).
