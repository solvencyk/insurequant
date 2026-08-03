---
from: validation
to: parser
created: 20260803T0520Z
status: open
route: blind_spot
company: MULTI
period: ALL
rule: UH-8 (MISSING_PROVENANCE_SIDECAR / CHECK 2 미배선 축)
lane: kics
iter: 1
---

## 미결 (validation) — `kics_rate_sensitivity`의 provenance 사이드카 부재 = 소스 신선도 검사축 없음

### 배경 (UH-3가 오늘 닫히면서 남은 같은 부류)

2026-08-03 UH-3 end-state 전환으로 `validate_data_contract.py` CHECK 2는 **사이드카 부재 = RED**가
됐다(`MISSING_PROVENANCE_SIDECAR`). 대상은 CHECK 2가 실제로 검사하는 4종:

| 마스터 | 사이드카 | CHECK 2 |
|---|---|---|
| `sensitivity_heatmap` | ✅ `data/dart/viz/sensitivity_heatmap_provenance.json` | strict |
| `forward_capital` · `tier1_utilization` · `tier2_utilization` | ✅ 루트 3개 (`emit_capsec_provenance.py`) | strict |
| **`kics_rate_sensitivity`** | ❌ **없음** | **검사 대상 자체가 아님** |

`kics_rate_sensitivity`는 `Env.MASTER_FILES`에 등재돼 mtime 감시만 받고, **as-of / source 축은
아무도 보지 않는다.** 값 검증은 `data/_derived/kics_rate_sensitivity_validation.json`이 하지만
그건 "이 값이 정합한가"이고, **"이 값이 어느 분기·어느 파일에서 나왔는가"는 미검증**이다.
즉 stale 분기가 렌더링돼도 게이트가 조용하다 — PM-2026-06-16 두 달 글리치와 정확히 같은 부류.

### 요청 (선례가 이미 있어 그대로 따라가면 됨)

1. **사이드카 발행**: `kics_rate_sensitivity_provenance.json`(루트, 마스터 파일과 같은 위치).
   구현 선례 = `scripts/emit_sensitivity_provenance.py`(parser 작성, sensitivity_heatmap용).
   같은 형태의 `scripts/emit_rate_sensitivity_provenance.py`를 두면 된다.
   계약: `python scripts/validate_data_contract.py --print-provenance-contract`
   - `company_code`: 게이트가 조인하는 키와 **정확히 같은 값**을 넣을 것. 이 마스터는 KR코드
     (`원보험사코드`)를 갖고 있으므로 코드 조인이 가능하다(heatmap이 회사명 조인이라 겪은 함정 없음).
   - `quarter`: `공시분기` 그대로(`2026.1Q` 형식).
   - `as_of_date`: 그 분기말(`2026.1Q` → `2026-03-31`).
   - `source_file`: 실제 원천(Docling MD / PDF) repo-상대 경로. **디스크에 존재해야 한다** —
     게이트가 `MISSING_PROVENANCE`로 존재를 확인한다.
   - `source_id`: `DISCLOSURE_MD` (정기경영공시 MD 계보).

2. **발행 완료를 알려줄 것** → validation이 CHECK 2에 `kics_rate_sensitivity` 축을 배선한다
   (2a(iv) 신설 + 회귀 케이스). **발행 전에 배선하면 즉시 red-out으로 push가 영구 차단**되므로
   순서를 지킨다 — UH-3에서 검증된 절차다(YELLOW 관찰 → 전량 발행 → RED 전환).

### 완료 조건

- `kics_rate_sensitivity_provenance.json` 존재 + `python scripts/validate_data_contract.py` RED 무증가.
- 발행 스크립트가 **존재**할 것(손으로 쓴 사이드카는 다음 리빌드에 씻겨나간다 — 2026-08-03
  자본성증권 사고의 직접 교훈, PM-2026-08-03 §2).
- 이 스레드에 `## 답변`으로 발행 경로·셀 수 기재.

근거: `docs/postmortems/README.md` UH-8 · PM-2026-08-03 · 메모리 `project_data_contract_gate`,
`feedback_validation_blind_spots`.

## 답변 (recipient 작성 — 처리 후)
