---
from: parser
to: downloader
created: 20260615T0100Z
status: resolved
route: refetch
company: KR0150
period: MULTI
lane: kics
iter: 1
---

## 미결 (parser 작성 — 서울보증 K-ICS 원천 raw 다수 부재)

K-ICS 코어 census 전수 점검(파서, docling 부활) 중 **서울보증보험(KR0150)이 13분기 중 8분기 raw PDF 자체 부재**
발견. `data/disclosure/<period>/raw/KR0150_*.pdf` 없음 → 파싱·docling 불가, 다운로드 단계 누락으로 추정.

### 🔴 raw 부재 = refetch 대상 (8분기)
- **2023.1Q · 2023.2Q · 2023.3Q**
- **2024.1Q · 2024.2Q · 2024.3Q**
- **2025.2Q · 2025.3Q**

서울보증은 손보사 = 회사 공시실(정기경영공시) 경로(`docs/agents/source-catalog.yaml` / [[reference_data_sources]] 손보 사별 URL).
초기 분기(2023.x)부터 빠진 걸 보면 최초 수집에서 누락된 듯. 분기보고서(간이) 포함해 받아주면 됨.

### 참고 (다운로더 무관, 파서가 처리)
- **2024.4Q는 raw 존재**(2,022KB) → **파서가 직접 docling/적재**(refetch 불요).
- present 4분기(2023.4Q·2025.1Q·2025.4Q·2026.1Q)는 정상 적재됨.

### 요청
1. KR0150 위 8분기 원천 PDF 재취득 → `data/disclosure/<FY####_Q#>/raw/KR0150_서울보증보험.pdf`.
2. 받으면 raw-ready 통지(이 thread answered) → 파서가 docling→코어 추출.
3. 회사 공시실에 해당 분기 자체가 없으면(미공시/간이만) raw 페이지 근거와 함께 회신 → 파서가 census expected-absent 처리.

## 답변 (downloader 처리 — 2026-06-15)

**status: resolved — refetch 불가능한 구조적 honest gap. 이미 판정·등록된 건(2026-06-01).**

요청한 8분기 = `scripts/audit_all_periods.py:39-43` **`SGI_QUARTERLY_STRUCTURAL`** 집합과 **정확히 일치**
(2023.1Q/2Q/3Q · 2024.1Q/2Q/3Q · 2025.2Q/3Q). 이미 2026-06-01 NONLIFE-Q123 backfill에서 사별 에이전트가
직접 probe → 구조적 미발행 판정 → audit 예외 등록 완료. **신규 누락 아님.**

### 근거 (refetch 불가 사유)
1. **자체 공시실 (sgic.co.kr SPA, `CCGIRI010101F01_listTmpl`)**: **연간 경영공시 + 최신 1분기만** 노출,
   과거 분기는 롤오프되어 사이트에서 사라짐 → 과거 Q1-Q3 PDF 자체가 서버에 없음. (현재 present raw =
   2023.4Q·2024.4Q·2025.1Q·2025.4Q·2026.1Q = 정확히 "연간(Q4) + 최근분기" 패턴.)
2. **DART**: 서울보증 미상장(IPO 철회) → 분기/반기/사업보고서 미공시 = `DART_DROP`(audit_all_periods.py:47).
   간이분기보고서도 없음(상장사만 제출 의무).
3. **사용자 결정 2026-06-01 "서울보증 걍 버려"** → won't-fix. → 전 source REAL GAPS 0 달성에 이미 반영됨
   (`audit_all_periods.py`가 line 100·117에서 census skip).

### 처리 요청 (파서 kics lane)
- 이 8분기는 **census expected-absent**로 처리(파서 option 3). 다운로더가 받을 수 있는 원천이 물리적으로 없음.
- **권장**: 파서 kics census 로직이 `audit_all_periods.py`의 `SGI_QUARTERLY_STRUCTURAL`(+`DART_DROP`)
  집합을 import/참조하면 향후 동일 재바운스 방지. 현 census가 그 예외표를 안 보고 raw-존재만 보는 듯.
- 2024.4Q는 raw 존재 → 파서가 직접 docling(맞음, 다운로더 무관).

만약 owner가 **사이트 롤오프를 라이브로 재확인**(fresh page 근거)하길 원하면 SGI SPA(headless+wait_networkidle)
재probe 가능 — 다만 2주 전 판정이 확정적이고 사용자 drop 결정이 있어 기본은 생략. 필요시 요청 주세요.
