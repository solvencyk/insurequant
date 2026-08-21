---
from: owner
to: downloader
created: 20260703T1138Z
status: resolved
route: pipeline
company: KR1011 (IBK연금보험)
period: 2023.1Q~2026.1Q
lane: ifrs17
---

## 미결 (owner) — #6 IBK연금보험 주요사 격상 + IFRS17 지표 전체 크롤링 개시

**요청**: IBK연금보험을 주요사로 격상하고, IFRS17(17) 지표 전체 크롤링을 시도.

**현황 확인 (owner probe):**
- IBK연금(KR1011)은 **K-ICS(kics_disclosure.json)엔 이미 존재**(지급여력 전 항목 있음).
- **IFRS17 마스터엔 0행** — PL_breakdown.json·CSM_waterfall.json 둘 다 IBK/연금 rows=0. = DART IFRS17 공시 미크롤 상태.

**할 것 (downloader):**
1. IBK연금보험 **DART 사업보고서·반기/분기보고서 수집** (회사명으로 검색 — 영구 매핑 파일 만들지 말 것, 메모리 [IFRS17 company mapping]). 대상 분기 = 기존 IFRS17 마스터 커버리지에 맞춰 **2023~2026.1Q**.
2. source-catalog에 IBK연금 IFRS17 소스 등재(주요사 격상).
3. 수집분 → **parser(ifrs17) inbox로 핸드오프** (CSM 워터폴 / PL breakdown / 가정민감도 추출 발주).

**주의**: IBK연금은 연금보험 전업사 — 계약 대부분 연금/저축성. CSM 구조는 생보와 유사하나 PAA vs GMM(일반모형) 적용 비중·유배당 특성 확인해서 파서에 명기. 자동차/일반손보 항목은 0(생명장기 전업 아님, 연금 중심)일 것.

**후속**: parser-ifrs17 추출 완료 후 designer가 IFRS17 viz 패널·회사 드롭다운에 IBK연금 노출(데이터 들어온 뒤). 이번 발주는 **수집 인프라 + 마스터 적재**가 목표.

## 답변 (downloader, 2026-07-03)

**완료.** A형 공시 없음 확인 → F형(감사보고서) 경로로 전환.

- `src/ifrs17/universe.py`: IBK연금보험 NON_LISTED_SKIP에서 제거 → AUDIT_REPORT_ANNUAL에 추가
- `scripts/ifrs17_ingest_audit_annual.py`: NAME_ALIASES 연결 (DART alias=아이비케이연금보험)
- `docs/agents/source-catalog.yaml`: audit_only_5 → audit_only_6으로 격상
- FY2023~FY2025 감사보고서 3개년 수집·추출 완료 (FY2022는 IFRS17 전환 전, CSM=0)
- 7종 artifact × 3년 = 21개 파일 in `data/dart/extracted/아이비케이연금보험_*`
- Parser handoff: `inbox/parser/20260703T1200Z__downloader__KR1011__ibk_pension_ifrs17_raw_ready.md`
