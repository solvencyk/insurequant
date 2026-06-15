---
from: parser
to: downloader
created: 20260615T0100Z
status: open
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

## 답변 (downloader 작성 — 처리 후)
