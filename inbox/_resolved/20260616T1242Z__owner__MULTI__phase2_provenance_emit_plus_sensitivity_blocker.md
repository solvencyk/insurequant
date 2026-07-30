---
from: owner
to: parser
created: 20260616T1242Z
status: open
route: backlog
company: MULTI
period: ALL
lane: kics+ifrs17
iter: 1
---

## 발주 (owner) — Phase 2 provenance emission(parser측) + STALE_AS_OF 차단건 fix

### A. STALE_AS_OF 차단건 (🔴 push-blocker, 면제 없음)
data-contract 게이트가 `sensitivity_heatmap.json`을 **period=FY2024/as_of=2024-12-31 stale**로 잡아 RED 22 → **push 차단 중**. owner zero-RED 정책이라 **면제 아니라 고쳐야 함.**
- IFRS17 DART 민감도를 **2025.4Q(FY2025) 기준으로 re-extract + heatmap 재빌드**, as_of 스탬프를 올바로 박을 것. 기존 발주 `inbox/parser/20260616T0435Z…ifrs17_sensitivity_fy2025_reextract`(phase 2 product-row 일반화)와 동일 트랙 — **이게 이제 push 막는 차단건**임을 인지하고 우선순위 상향.

### B. Phase 2 provenance emission — parser측 (꼬리표 부착)
validation이 정의한 provenance 계약대로, parser 출력 시 각 셀에 **소스 꼬리표 메타**를 같이 emit. **parser 분담 = `source_id` + `item_block`**:
- `source_id` ∈ {DART, DISCLOSURE_MD, KIDI, IR_FACTSHEET, FSC_BONDS} — 이 셀이 어느 소스 종류에서 왔나.
- `item_block` — 항목 분류(예: CSM_waterfall 6항목, kics 1-28/29-35/36-46, PL 항목블록).
- 저장: 마스터별 `<master>_provenance.json` 사이드카(validation 추천, 셀 스키마 비파괴). 키 = (company_code, quarter, item_block).
- (downloader가 `source_file`·`as_of_date`·`effective_filtered`를 채움 — 별 발주. parser는 위 2필드.)

### 주의
- python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. 인라인 멀티라인 `python -c` 금지. UTF-8 no BOM. `build_csm_waterfall_master.py` 금지(raw purge 붕괴).

## 답변 (parser-kics 2026-06-16 — B(kics) 완료, A·B(ifrs17)는 ifrs17 세션)

**B. Phase 2 provenance emission — kics 몫 ✅ DONE.**
- `scripts/emit_kics_provenance.py` → **`kics_disclosure_provenance.json`** 생성(1,123셀, 39사×13분기).
- 계약(`validate_data_contract.py --print-provenance-contract`)대로 **parser 분담 = `source_id` + `item_block`**:
  - `source_id` = **DISCLOSURE_MD** (kics_disclosure는 전 셀이 정기경영공시 PDF→docling MD 출처, 단일소스).
  - `item_block` = owner 3블록: **capital_summary(1-28, 471) · life_subrisk(29-35, 318) · market_irr(36-46, 334)**.
  - 키 = (company_code, quarter, item_block). 사이드카 헤더에 `fields_pending_downloader`=[as_of_date·source_file·
    effective_filtered] 명시 → **downloader 별 발주가 in-place로 채움**(셀 스키마 비파괴).
- data-contract 게이트 실행: 내 사이드카 **깨끗이 수용(에러 0)**, CHECK1 census는 기존 documented 예외만 그대로.
  (게이트의 사이드카-읽기 로직은 validation이 와이어링 중 — `…zerored_wiring_phase2_go` — emission은 준비 완료.)

**A. STALE_AS_OF push-blocker (sensitivity_heatmap FY2024 stale) = ifrs17 레인 → 이 세션 안 함.**
owner도 "기존 발주 `0435Z…ifrs17_sensitivity_fy2025_reextract`와 동일 트랙"이라 명시. DART 민감도 2025.4Q
re-extract + heatmap 재빌드 + as_of 스탬프 = **ifrs17 세션 몫**(2-lane hard split, user 결정 "별도 ifrs17 세션으로").
→ ifrs17 세션이 0435Z와 묶어 처리(이게 실제 push 차단건이므로 우선순위 상향 필요).

**B(ifrs17) CSM_waterfall/PL_breakdown provenance** 사이드카(source_id=DART, item_block=csm_waterfall/pl_block)도
같은 이유로 ifrs17 세션. (kics 사이드카 패턴 그대로 적용하면 됨.)

status: **kics 분담(B) 완료.** ifrs17 분담(A + B-ifrs17)은 ifrs17 세션 — 이 건 kics측 종결, ifrs17측 open.

✅ DONE (ifrs17 분담, 2026-06-20). A(STALE_AS_OF sensitivity blocker): heatmap FY2025로 정정완료, data-contract CHECK2 AS-OF RED=0 유지. 3 partial 진단=자동복구불가(미래에셋=OCR/이미지·신한라이프=prose 서술·한화손해=시장위험형 환율/금리/주가→손익,자본)→owner 손fix. B(provenance ifrs17): **CSM_waterfall_provenance.json + PL_breakdown_provenance.json** emit(scripts/emit_ifrs17_provenance.py): source_id=DART, item_block=csm_waterfall / income_statement·contract_notes, owner_override·estimate 플래그, fields_pending_downloader=[as_of_date·source_file·effective_filtered]. CSM 321셀·PL 632셀.
