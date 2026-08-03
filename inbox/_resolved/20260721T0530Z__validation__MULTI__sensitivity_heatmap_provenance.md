---
from: validation
to: parser
created: 20260721T0530Z
status: open
route: backlog
company: MULTI
period: ALL
lane: ifrs17
rule: MISSING_PROVENANCE_SIDECAR
iter: 1
---

## 미결 — `sensitivity_heatmap` provenance sidecar 미발행 (UH-3)

data-contract push 게이트 CHECK 2는 sidecar가 있으면 strict 검증, **없으면 Phase-1 추론 fallback**으로
통과시킨다(= 소스 신선도 미검증). `sensitivity_heatmap`은 ifrs17 레인 산출물이라 이쪽으로 발주.

- 대상: `data/dart/viz/sensitivity_heatmap.json`
- 필요 sidecar: `data/dart/viz/sensitivity_heatmap_provenance.json`
- 현재 게이트: **YELLOW `MISSING_PROVENANCE_SIDECAR`** (2026-07-21 신설, 비차단).
  발행되면 validation이 no-sidecar=RED로 전환.

**스키마 정본** (게이트가 직접 출력):
```
python scripts/validate_data_contract.py --print-provenance-contract
```
셀 단위 필드: `company_code` · `quarter` · `item_block`(예: `"sensitivity"`) · `source_id`
(`DART` 등 enum) · `as_of_date`(ISO, **그 분기와 일치해야 함** — 불일치 시 STALE_AS_OF RED) ·
`source_file`(repo-relative, 디스크 실재 필수).

⚠️ 주의: sidecar가 생기는 즉시 게이트가 **strict 모드**로 바뀐다. 즉 공시된 (회사,분기) 셀 전부에
대응하는 provenance 셀이 없으면 `MISSING_PROVENANCE` **RED**가 뜬다. 부분 발행하지 말고
heatmap이 렌더하는 셀 전량을 덮을 것.

**참고 (기존 이력)**: 민감도 as_of/period null 이슈는 이전 라운드에서 designer/parser 간 이미
다뤄진 적 있음(`20260616T0030Z__designer__…__sensitivity_period_asof_null`). sidecar 발행 시
그 값이 정본이 되므로 함께 정리 권장.

## 답변 (parser 작성 — 처리 후)
