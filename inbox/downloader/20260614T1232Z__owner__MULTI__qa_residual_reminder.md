---
from: owner
to: downloader
created: 20260614T1232Z
status: open
route: backlog
company: MULTI
period: 2025.4Q / 2023.4Q
iter: 1
---

## 미결 (sender 작성 — owner QA 잔여 리마인더)

다운로더 큐에 미처리/신규 2건:

**(1) [bump] NB CSM배수 25.4Q 미적재 — G8 (기존 thread 재촉)**
- `inbox/downloader/20260614T0712Z__owner__MULTI_2025.4Q__nb_csm_multiple_latest_quarter.md` 아직 status:open.
- AIG손해(KR0029)·카카오페이손해(KR1098) 2025.4Q "신계약CSM배수_연누계" null, 하나생명(KR0097) 2025.4Q/2026.1Q 레코드 부재 → index.html이 24.4Q로 fallback.
- DART/정기경영공시 refetch 건(raw purge 무관). 다음 드레인 시 우선 처리.

**(2) [신규] 시장위험 스캔-only 소스 — OCR 필요 (blind_spot/owner-OCR)**
- KB손해 & 한화손해 **2023.4Q 금리위험액** = full-page 이미지(텍스트레이어 없음).
- 카카오페이손해 **2025.4Q 시장위험** = 스캔 이미지.
- 파서가 fitz/pdfplumber로 못 뜸 → OCR된 텍스트가 있어야 추출 가능. downloader OCR 경로 or owner 수동 OCR. 확보되면 parser/kics가 시장위험 36-40 추출.

## 답변 (downloader 처리 — 2026-06-14)

**(1) G8 NB CSM배수 25.4Q — resolved (raw 복원).** 진단상 단순 refetch가 아니라 추출 이슈였음.
3사 FY2025 감사보고서 raw를 라이브 DART에서 복원(canonical `data/dart/FY2025_Q4/raw/`, AIG는
`KR0029_` prefix 정정) → 추출 교정은 parser/ifrs17로 라우팅
(`inbox/parser/20260614T1330Z__downloader__MULTI_2025.4Q__nb_csm_fy2025_raw_ready.md`).
원 스레드는 `_resolved/`로 이동. AIG/카카오=magnitude misparse(파서), 하나생명=audit-annual ingest 필요.

**(2) 시장위험 스캔-only OCR — open (미착수).** KB손해·한화손해 2023.4Q 금리위험, 카카오페이 2025.4Q
시장위험이 텍스트레이어 없는 이미지. downloader OCR 경로가 현재 파이프라인에 없음(신규 도구 필요) —
owner 수동 OCR vs downloader OCR 스택 도입은 결정 필요. 다음 드레인까지 이 메시지 open 유지.
