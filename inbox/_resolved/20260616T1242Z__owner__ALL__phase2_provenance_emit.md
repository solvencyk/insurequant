---
from: owner
to: downloader
created: 20260616T1242Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
resolved: 20260616T1310Z
resolved_by: downloader
---

## 발주 (owner) — Phase 2 provenance emission (downloader측 = 소스 꼬리표)

data-contract 게이트(②)가 "이 숫자가 어느 소스·어느 시점에서 왔나"를 **추론 대신 꼬리표 직접 읽기**로 검사하도록, downloader가 수집물에 **provenance 메타를 emit**한다. **downloader 분담 = `source_file` + `as_of_date` + `effective_filtered`**:
- `source_file` — 이 값의 원천 파일 경로(어느 PDF/XML/API 응답).
- `as_of_date` — 기준 시점(공시분기 말일). **stale/baseline 어긋남을 게이트가 잡는 핵심 필드.**
- `effective_filtered` — **as-of 시점 유효분 필터링을 실제 수행했다는 플래그/근거.** ⚠️ tier 도넛 버그의 정체 = 자본성증권 **유효-as-of 목록(call/만기 제외)**을 안 거름. 이 필드 없거나 false면 게이트 RED. 즉 **"26년 3월 기준 유효 발행분만"을 실제로 거른 뒤 그 증거를 박을 것.**
- 저장: validation이 정의한 마스터별 `<master>_provenance.json` 사이드카 스키마. 키 = (company_code, quarter, item_block). (parser가 `source_id`·`item_block` 채움.)
- 계약 전문: validation `scripts/validate_data_contract.py --print-provenance-contract`.

### 주의
- 5개 소스(disclosure/dart/증권발행/KIDI/IR) **전수 cell**에 대해 수집·꼬리표(메모리 `reference_data_sources` 원칙). python 풀패스. 인라인 멀티라인 `python -c` 금지. UTF-8 no BOM.

## 답변 (downloader, 20260616T1310Z)

**완료 (bonds) / 후속작업 필요 (DART raw)**

### 완료: bonds effective-list provenance

스크립트: `scripts/emit_bonds_provenance.py`

산출물:
- `data/bonds/normalized/20260616T060817Z/bonds_provenance.json` — 24개사 cells
  - source_id=FSC_BONDS, as_of_date=2026-03-31, effective_filtered=true
- `data/bonds/disclosure/disclosure_bonds_provenance.json` — 2개사 cells (DART supplement)
  - source_id=DART, as_of_date=2026-03-31, effective_filtered=true
  - KDB생명(KR0072) 2건, 농협생명(KR0104) 2건

### 후속: DART raw provenance (23사 × 13분기)

`data/dart/FY*/raw/KR####_*/document.zip` per-cell source_file + as_of_date 사이드카 = 별도 스크립트 필요.
IFRS17 마스터(CSM_waterfall/PL_breakdown) 빌드 전 파서가 source_id + item_block 채울 때 연동.
downloader 작업: `emit_dart_raw_provenance.py` — 다음 세션 작업 예정.
