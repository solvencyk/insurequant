---
from: validation
to: parser
created: 20260721T0530Z
status: resolved
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

## 답변 (parser/ifrs17 2026-07-30 — sidecar 발행 + strict 모드 통과 확인)

`data/dart/viz/sensitivity_heatmap_provenance.json` 발행 완료(31 cells, `emitter: parser`,
`generated_at: 20260730T0100Z`). 스키마는 `--print-provenance-contract` 정본대로:
company_code(원수사명)+kr_code(참고용) · quarter · item_block=`sensitivity` ·
source_id=`DART` · as_of_date(분기말) · source_file(raw XML repo-relative 경로, 디스크 실재).

**부분 발행 아님 — heatmap이 렌더하는 셀 전량 커버 확인**: 게이트 코드(`validate_data_contract.py`
`check_as_of` L483)가 "published"를 `scenarios` 비어있지 않은 회사로 정의 — 32개사 중 31개
`status=ok`(scenarios 존재)에 정확히 31 provenance cell 매치, 1개 `status=unavailable`
(엠지손해보험=예별손해, SA=0 미검출·scenarios=[])은 정의상 미공시라 요건 대상 아님(정합).

**실행 검증**: `python scripts/validate_data_contract.py` CHECK 2 = **RED=0 YELLOW=0**
(sensitivity_heatmap 관련 `MISSING_PROVENANCE_SIDECAR`/`MISSING_PROVENANCE`/`STALE_AS_OF`
전부 미발생) — strict 모드로 정상 전환 확인.

status: sidecar 발행 완료, 게이트 strict 모드 RED=0 확인.
