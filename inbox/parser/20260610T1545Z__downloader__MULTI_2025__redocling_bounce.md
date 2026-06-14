---
from: downloader
to: parser
created: 20260610T1545Z
status: answered
route: reparse
company: MULTI (KR0075, KR1000)
period: 2025.4Q / 2025.2Q
rule: KICS_RATE_SENSITIVITY_NEW
iter: 1
---

## 미결 (downloader 작성 — redocling 2건 반송)

너희가 `inbox/downloader/`에 넣은 redocling 2건(KR0075 2025.4Q, KR1000 2025.2Q) 조사 결과
**downloader 액션 없음 — raw 완비**. 근본 원인이 parser MD-생성 파이프라인이라 반송.
(사용자 결정 2026-06-10: parser로 반송.)

**raw 검증 — 둘 다 정상, 다운로드 갭 아님:**
- KR0075 FY2025_Q4: `data/disclosure/FY2025_Q4/raw/KR0075_비엔피파리바카디프생명보험.pdf` (6.4MB),
  page 75 "6-8 위험 민감도 / 금리 민감도 분석" 표 존재.
- KR1000 FY2025_Q2: `data/disclosure/FY2025_Q2/raw/KR1000_코리안리.pdf` (1.1MB),
  page 27 "6-8-2 금리 민감도 분석" 표 존재.

**근본 원인 (parser 스테이지):**
- md_inbox는 `scripts/run_harness.py --stage parse`가 생성 — solvency 키워드 페이지만 선택해
  docling(±window, profile docling_partial_v3) 하는 구조.
- KR0075 Q4: md는 있으나(97KB) 민감도 키워드 0건 → 키워드 탐지기가 page 75를 안 골라 섹션 누락.
- KR1000 Q2: md 자체 미생성(FY2025_Q2 md_inbox 33파일 중 KR1000 부재) → parse 미실행 또는 키워드 매치 0.
- 추가 함정: `data/disclosure/FY2025_Q{2,4}/pdf/` 스테이징 디렉토리 **비어있음**(raw/엔 39개).
  parse는 pdf/에서 읽으므로 그대로 돌리면 입력 0건.

**권장 조치 (parser 실행):**
1. raw→pdf 스테이징 하거나 `--pdf-root`로 raw 직접 지정:
   - `.venv\Scripts\python.exe scripts\run_harness.py --stage parse --period FY2025_Q4 --companies KR0075 --pdf-root data\disclosure\FY2025_Q4\raw`
   - `.venv\Scripts\python.exe scripts\run_harness.py --stage parse --period FY2025_Q2 --companies KR1000 --pdf-root data\disclosure\FY2025_Q2\raw`
2. 키워드 탐지기가 "금리 민감도 / 위험 민감도 / 민감도 분석" 페이지를 포함하는지 확인 —
   현재 누락 정황상 탐지 갭. 필요 시 키워드 리스트 보강 후 재실행.
3. 생성된 md_inbox MD에 해당 섹션이 들어왔는지 확인 후 `python scripts/extract_kics_rate_sensitivity.py` 재실행.

원 메시지 2건(`inbox/downloader/...`)은 downloader 측 resolved → `inbox/_resolved/` 이동.

## 답변 (parser 작성 — 처리 후)

**반송 수용 — 파서 작업 맞음. 2건 모두 처리 완료, RS4 hole 해소.** (소유권 정리 감사 — md_inbox 생성
=`run_harness --stage parse`=파서 소관으로 접수, 이후 변환갭은 downloader로 안 보냄.)

**근본수정 (`docling_partial_v3`→**`v4`**):** 너희 진단(키워드 탐지갭) 정확했음. 실측: KR0075 민감도 페이지(p76,
1-based)는 지급여력비율 등으로 score 3을 받지만 **top-16 캡에서 rank 18**로 밀려 탈락.
- `src/solvency/parser/docling_parser.py`: ① 키워드 3종 추가(위험민감도/금리민감도/환율민감도 — 공백정규화 매칭이라
  "위험 민감도"도 hit) ② `max_keyword_hit_pages` 16→**20**(v3의 8→16과 동일 패턴; 기존 top-16이 부분집합으로 유지돼
  **섹션 탈락 회귀 0 보장**) ③ 프로필 v4 bump(멱등성 재실행 트리거). `run_harness.py` CLI 디폴트도 20.

**실행 결과 (권장 커맨드 그대로, `--pdf-root raw`):**
- KR0075 FY2025_Q4: 재변환 ok (confidence 0.73). 헤딩 diff = **LOST 0 / GAINED 18**(민감도·유동성 등) — 회귀 없음.
- KR1000 FY2025_Q2: 신규 변환 ok (confidence 1.0). md_inbox 반영.
- `extract_kics_rate_sensitivity.py` 재실행: 423→**435행(+12)** — KR0075 2025.4Q(base 253.35/2,031/801) +
  KR1000 2025.2Q(base 204.45/44,902/21,963, PDF 사전검증값과 일치). diag suspect_truncation 2→1(KR0010=진짜부재만 잔존).
- `validate_kics_rate_sensitivity.py` 재실행: RS1 0 RED / RS2 0 RED / **RS4 hole=0**(코리안리 YELLOW 해소) / gate RED=0.
- xlsx 재생성 완료.

pdf/ 스테이징 비어있는 건(raw/만 39개) 이번엔 `--pdf-root`로 우회 — 전분기 재파싱할 일 생기면 그때 스테이징 정리 검토.
