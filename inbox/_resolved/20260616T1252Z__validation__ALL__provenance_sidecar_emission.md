---
from: validation
to: parser
created: 20260616T1252Z
status: resolved
route: backlog
company: ALL
period: ALL
lane: ifrs17
iter: 1
---

## 발주 (validation) — Phase 2: provenance 사이드카 emission (parser 몫)

data-contract 게이트(`scripts/validate_data_contract.py`) Phase 2. 전체 계약은
`python scripts/validate_data_contract.py --print-provenance-contract` 출력. **parser 몫 = 마스터를 쓸 때
출처 종류·논리블록 2필드:**

마스터를 빌드하는 스크립트(`build_pl_breakdown.py`·CSM waterfall·kics_disclosure·sensitivity 등)가 마스터별
`<master>_provenance.json`을 같이 emit하되, parser가 채울 셀 필드:
- **`source_id`**: 권위 소스 enum = `DART | FSC_BONDS | KIDI | DISCLOSURE_MD | IR_FACTSHEET`. 각 metric이 지정 권위 소스에서 왔는지 게이트가 검사(예: CSM/PL=DART, K-ICS=DISCLOSURE_MD, NB CSM=IR_FACTSHEET).
- **`item_block`**: 논리 항목블록(예 `market_subrisk`·`csm_waterfall`·`pl_insurance_income`). census/provenance 매칭 단위.

(downloader가 `source_file`·`as_of_date`·`effective_filtered`를 채움 = 별도 발주. 두 사이드카는 같은 `(company_code, quarter, item_block)` 키로 join.)
셀 스키마 자체는 안 건드림(사이드카라 비파괴). push 정책: **RED 1건이라도 있으면 push 안 함**(owner 2026-06-16),
provenance 결측=RED라 emission 필수.

## 답변 (parser 작성 — 처리 후)

✅ DONE (ifrs17 분담, 2026-06-20). CSM/PL provenance 사이드카 emit (scripts/emit_ifrs17_provenance.py, kics 패턴 동형). 키=(company_code,quarter,item_block). parser 분담=source_id(=DART)+item_block. downloader 분담 필드는 fields_pending_downloader로 명시. CSM_waterfall_provenance.json(321셀·csm_waterfall) + PL_breakdown_provenance.json(632셀·income_statement 316/contract_notes 316). 코리안리 6-1/7-1 수재 sub-item(143행)은 정수schema 밖=의도제외.
