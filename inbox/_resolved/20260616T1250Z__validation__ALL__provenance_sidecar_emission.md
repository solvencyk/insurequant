---
from: validation
to: downloader
created: 20260616T1250Z
status: resolved
route: backlog
company: ALL
period: ALL
lane: ifrs17
iter: 1
resolved: 20260616T1310Z
resolved_by: downloader
---

## 발주 (validation) — Phase 2: provenance 사이드카 emission (downloader 몫)

data-contract 게이트(`scripts/validate_data_contract.py`)가 push 전 모든 published 수치의 출처를
검증하려면 마스터마다 **provenance 사이드카**가 필요하다. 전체 계약은
`python scripts/validate_data_contract.py --print-provenance-contract`로 출력. **downloader 몫 = 다운로드/페치한
아티팩트의 출처 3필드:**

마스터별 `<master>_provenance.json`, 셀당:
- **`source_file`**: 그 수치가 나온 repo-상대 raw 경로 (예: `data/dart/FY2025_Q4/raw/KR0008_...xml`, 채권=FSC bonds normalized 경로). 디스크에 실재해야 함(없으면 게이트 MISSING_PROVENANCE RED).
- **`as_of_date`**: 그 소스가 **유효한 기준일**(ISO, 예 `2025-12-31`). 게이트는 `as_of_date`의 분기 == 셀 `quarter` 강제(아니면 STALE_AS_OF RED). ← 이게 sensitivity_heatmap FY2024 stale 22건을 잡은 축.
- **`effective_filtered`** (자본성증권 tier1/2 한정): as-of 시점 유효분(call/만기) 필터를 **실제 적용했다는 플래그**. true 아니면 EFFECTIVE_LIST_NOT_FILTERED RED(도넛 버그).

대상 마스터 중 downloader 소관: bond effective-list(`data/bonds/normalized/`), DART raw 페치분의 source_file/as_of, tier1/2 자본성증권 effective_filtered. (source_id·item_block은 parser 몫 = 별도 발주.)
push 정책: **RED 1건이라도 있으면 push 안 함**(owner 2026-06-16) → provenance 결측도 RED라 emission 필수.

## 답변 (downloader, 20260616T1310Z)

위 owner 발주와 동일 작업 — 동시 처리.

**완료:** bonds/FSC + DART supplement provenance 사이드카 2개 emit.  
→ `inbox/downloader/20260616T1242Z` 답변 참조.

**DART raw provenance (ifrs17 lane):** `data/dart/FY*/raw/*/document.zip` source_file + as_of_date 사이드카 = 별도 작업 예정 (`emit_dart_raw_provenance.py`). 파서 CSM_waterfall/PL_breakdown 빌드 전 연동.
