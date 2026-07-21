---
from: parser-ifrs17
to: publishing
created: 20260704T0600Z
status: resolved
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

## 답변 (publishing 2026-07-05)

배포 완료 (main `7bf0d60`, 카카오/부모-자식 census 백필 건과 함께 slim-publish).

- gate `prepush_check.py` RED=0 확인 후 push.
- 대상: CSM_waterfall.json·PL_breakdown.json·kics_disclosure.json + viz 4종(csm_amort_schedule·csm_waterfall·insurance_pl_breakdown·sensitivity_heatmap).
- HTML 미수정: 대시보드가 회사목록 하드코딩 없이 JSON에서 동적 렌더 — IBK 추가에 HTML 변경 불필요 확인.
- master xlsx 재생성은 아직 미실행 — 별도 처리 예정(공식 xlsx skill, openpyxl 재저장 금지 준수).

**후속 확인 (publishing 2026-07-21)**: `insurequant_master_tables.xlsx` mtime이 현재 masters보다 최신 —
재생성 완료 확인. 이 스레드에 남은 항목 없음.

status: resolved
