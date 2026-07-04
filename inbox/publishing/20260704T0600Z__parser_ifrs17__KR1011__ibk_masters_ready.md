---
from: parser-ifrs17
to: publishing
created: 20260704T0600Z
status: open
company: KR1011 IBK연금보험
period: FY2023~FY2025
lane: ifrs17
---

## IBK연금보험 IFRS17 마스터 적재 완료 — 사이트 전파 요청

### 완료 내역

**CSM_waterfall.json** (2026-07-03): IBK 18레코드 (6항목×3개년) append — closure/continuity 3중검증 통과.

**pl_breakdown_master.json** (2026-07-04): IBK 72레코드 (24항목×3개년) — tier1 포괄손익계산서 + tier2 gold override (notes [166][167] 직접계산). closure 5종 Δ=0 매년.

**viz 파일 재빌드 완료** (2026-07-04):
- sensitivity_heatmap.json (27/32 ok, IBK 포함)
- csm_amort_schedule.json (28/30 ok, IBK 포함)
- insurance_pl_breakdown.json (29/29 ok, IBK 포함)
- csm_waterfall.json (IBK FY23-25 partial — newbiz 누락은 parser 추가 파싱 필요, 나머지 OK)
- csm_bubble.json, downstream_kpis.json, earnings_quadrant.json 재빌드 완료

### 요청

1. **master xlsx 재생성** — 공식 xlsx skill 사용 (openpyxl 재저장 금지).
2. 사이트 HTML 갱신 및 배포 (owner 승인 후).

### 참고

IBK 티커=null (비상장), 값_당분기=null (연간사 = 라이나/메트라이프 관례). dashboard에서 분기 시계열 없이 연간 포인트 3개만 표시됨.
