---
from: owner
to: downloader
created: 20260612T0900Z
status: open
route: backlog
company: ALL
period: ALL
rule: BACKLOG_DIGEST
iter: 1
---

## 미결 (sender 작성)

**owner 백로그 다이제스트 (2026-06-12 전수 점검).** 상세는 `TODO_downloader.md` 해당 ID.
수집 상태 자체는 깨끗함(전 source 실질 gap 0) — 아래는 신규 소스 확장 + 버그 + 차기분기 준비.

### 🔴 P1 (착수 가능)
1. **F7 — KOSIS 손보 손해율 시계열 ingest**: `orgId=382, tblId=TX_38202_A1561` JSON API.
   `scripts/ingest_kosis_loss_ratio.py` 신규 + `data/kosis/`. 기존 손해율 PDF 파싱 교차검증용.
2. **F8 — 손보협회 비교공시(consumer.knia.or.kr) probe**: 채널별 불완전판매율·설계사정착률·민원·
   부지급률·지급지연율. JS-render 여부 probe → API/scrape 결정 → `data/knia_consumer/`.
   (F13 재보험 지표 + GA 인과체인의 선행 — publishing이 대기 중.)

### 🟠 P2
3. **BATCH-HISTORICAL-FIX**: `ifrs17_batch_historical.py` 정정공시([기재정정]) rcept 오선택 버그
   (status=014). 정정 prefix 제외 + 최신 rcept picking.
4. **F9 — data.go.kr 금융통계 API**: 15061307(손보)/15061306(생보)/15094797(실손).
   `src/bonds/fsc_client.py` 패턴 재활용 → `src/finstat/`.
5. **F15-DL — 동양생명 2025.2Q~2026.1Q 재다운로드 검토**: wide `<TE>` 잔액행 0 문제.
   재다운로드가 효과 있는지 parser와 먼저 확인 (본체는 parser 버그).

### 🟢 P3 / 대기
6. F10 GA통합공시(gapub) probe / F14 규제뉴스 피드(roadmap §1E) / MISC-SEIBRO fallback.
7. **2026.2Q 시즌 준비 (8월~)**: DL-FYR 룰 — URL/XPath 직접 발굴 (사용자 제공은 2026.1Q가 마지막).
   `source-catalog.yaml` 기존 config 재사용, 기간 라벨만 교체. 사이트 구조 전면 변경 시에만 escalate.

참고: FY2026_Q1 K-ICS PDF→MD 변환은 **parser 소관**(docling = parse stage) — downloader 액션 없음.

## 답변 (recipient 작성 — 처리 후)
