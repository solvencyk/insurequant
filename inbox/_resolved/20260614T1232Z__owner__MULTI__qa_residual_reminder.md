---
from: owner
to: downloader
created: 20260614T1232Z
status: resolved
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

## 추가 확인 (downloader — 2026-08-03 드레인)

(1)은 이미 위에서 resolved. (2)는 여전히 owner 결정 대기 — `TODO_downloader.md`의 `OCR-MARKETRISK` 행이
정본 추적 위치이니 이 스레드는 그 행이 닫힐 때까지 open 유지(중복 판단 없음, 새 정보 없음).

## 추가 확인 (2026-08-15, owner "패스")

(2) OCR-MARKETRISK 두 옵션 다 owner 보류 결정("됐어 패스") — 급한 건 아님, 재요청 전까지 미착수 유지.

## 상태 확정 (2026-08-20, status-sweep `20260820T0033Z` 요청에 따라)

`status:`가 `open`으로 남아있던 게 (1)이 resolved된 뒤에도 안 바뀐 것뿐이었다 — 파일 자체
갱신 누락, 새 정보 아님. (1)은 위에서 이미 `_resolved/`로 옮긴 후속 티켓으로 완전히
종결됐고, 남은 (2) OCR-MARKETRISK는 **owner가 명시적으로 보류를 택한 상태**(처리 옵션이
아니라 "재요청 전 미착수"가 확정 결정)라 `open`보다 `answered`가 맞다. `status: answered`로
정정, 추적은 `TODO_downloader.md`의 `OCR-MARKETRISK` 행이 계속 정본.

---

### 종결 (owner status-sweep, 2026-08-20)

(1) NB CSM배수 25.4Q는 raw 복원 후 parser 라우팅으로 종결(원 스레드 _resolved 이동 완료). (2) OCR-MARKETRISK는 owner가 2026-08-15 '됐어 패스'로 명시 보류 — 정본 추적은 TODO_downloader의 OCR-MARKETRISK 행.
