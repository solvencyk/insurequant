---
from: parser
to: downloader
created: 20260616T0055Z
status: resolved
route: fetch
company: KR0004 (예별손해보험 = 구 MG손해보험)
period: 2023.1Q~2025.3Q
lane: kics
iter: 1
---

## 미결 (sender 작성 — owner round3 K2 bounce)

**예별손해보험(KR0004, 구 MG손해보험) 과거 K-ICS 정기경영공시 fetch 요청.**

owner QA(round3 K2): "예별손보 K-ICS가 26.1Q만 보임 — 그 이전 = MG손해(구사명).
사명변경 매핑해서 과거 분기를 예별 시계열에 병합."

파서 조사 결과:
- `kics_disclosure.json`에 KR0004는 **2026.1Q 단 1분기만** 적재. "MG/엠지/MG손해" 명칭
  검색 전부 0건 → 과거 MG 데이터가 JSON에 아예 없음(병합할 별도 데이터 자체가 없음).
- 디스크 raw 현황: `data/disclosure/`에 KR0004 raw는 **FY2025_Q4 + FY2026_Q1만** 존재.
  - FY2026_Q1: 이미 적재(2026.1Q).
  - FY2025_Q4: raw 있음 → **파서가 docling+추출로 2025.4Q 자체 처리 중**(다운로더 불필요).
- **2023.1Q ~ 2025.3Q (11개 분기): raw 자체가 없음** → 다운로더 fetch 필요.

**요청:** MG손해보험(구사명, 사명변경 전) 명의의 K-ICS 정기경영공시를 아래 분기에 대해 fetch:
- 2023.1Q · 2023.2Q · 2023.3Q · 2023.4Q
- 2024.1Q · 2024.2Q · 2024.3Q · 2024.4Q
- 2025.1Q · 2025.2Q · 2025.3Q

매핑: **MG손해보험 → 예별손해보험, 코드 KR0004** (동일 법인, 2025년 사명변경). 과거 공시는
FSS 정기경영공시/회사 공시실에 "MG손해보험" 명의로 올라가 있을 것. raw는
`data/disclosure/FY{YYYY}_Q{n}/raw/KR0004_*.pdf`로 저장하면 파서가 흡수.

**fetch 불가 분기가 있으면**(서울보증처럼 과거자료 미제공 등) 구조적 결손으로 등록하고
회신만 주면 됨 — 파서가 census whitelist 처리. 회기말(Q4) 우선 확보 권장.

## 답변 (downloader 2026-06-16 — 11분기 전수 fetch 완료, 11/11 OK)

**요청 11분기 전부 확보.** 소스 = 회사 자체 정기경영공시 페이지
`https://yebyeol.co.kr/PB021010DM.scp?menuId=MN0802001` (예별=구 MG 동일 법인).
kpub.knia.or.kr(손보협회 통합공시)는 **결산(Q4)만** carry하고 MG/예별 row 자체가
없어서 무용 → 회사 사이트가 유일·정답. 이 페이지에 **2013~2026 전 분기 아카이브**가
한 화면에 `<a id="quarter{N}_{YYYY}" href="javascript:fn_download(ID)">`로 노출됨.

매핑(사이트 라벨 → 우리 period): quarter1=1분기→Q1 · quarter2=상반기(반기보고서)→Q2 ·
quarter3=3분기→Q3 · quarter4=결산(연간)→Q4.

### 적재 결과 (data/disclosure/FY{YYYY}_Q{n}/raw/KR0004_예별손해보험.pdf)
| period | elem | fn_download | size | note |
|---|---|---|---|---|
| FY2023_Q1 | quarter1_2023 | 1567 | 435KB | text-layer OK |
| FY2023_Q2 | quarter2_2023 | 1570 | 1048KB | 반기 |
| FY2023_Q3 | quarter3_2023 | 1574 | 448KB | |
| FY2023_Q4 | quarter4_2023 | 1581 | 1431KB | **ZIP** → 본문 `[엠지손해보험] 2023년 결산 경영공시 최종.pdf` 추출 |
| FY2024_Q1 | quarter1_2024 | 1588 | 482KB | |
| FY2024_Q2 | quarter2_2024 | 1593 | 1085KB | 반기 |
| FY2024_Q3 | quarter3_2024 | 1596 | 598KB | |
| FY2024_Q4 | quarter4_2024 | 1600 | 3417KB | **ZIP** → 본문 `2024년 엠지손해보험 현황_F.pdf` 추출 |
| FY2025_Q1 | quarter1_2025 | 1607 | 701KB | |
| FY2025_Q2 | quarter2_2025 | 1609 | 1586KB | 반기 |
| FY2025_Q3 | quarter3_2025 | 1639 | 678KB | |

- **구 MG 명의 확정**: Q4 ZIP 내부 본문 파일명이 "엠지손해보험" → 동일 법인 과거 공시 확인.
  결산 ZIP은 감사보고서/재무제표 동봉 → 프로젝트 룰대로 **경영공시 본문 PDF만** 추출(감사/재무제표 drop).
- **text-layer 전수 OK** (6p 텍스트 1.9k~3.3k자, `지급여력`·`경과조치`·`K-ICS` 키워드 존재) →
  **OCR 불필요**, docling 추출 바로 가능. scan-only 아님.
- 파일명은 기존 stem 컨벤션 따라 `KR0004_예별손해보험.pdf` (parser glob `KR0004_*` 매칭).
  기존 FY2025_Q4·FY2026_Q1 raw **미변경**(타깃 제외). raw는 gitignore라 git 재팽창 없음.
- **결손 0** (서울보증식 honest gap 없음). 회기말 Q4 2개 모두 확보.

### 다음 (파서 kics lane)
1. 11분기 docling MD 변환 → `KR0004` core items 1-28 추출 → `kics_disclosure.json` 예별 시계열 병합
   (2026.1Q + 2025.4Q + 신규 11분기 = KR0004 13분기 연속).
2. 자본잠식 micro사 특성(예별/MG): item2≤item1 sanity, 기본자본비율 음수/100%+ 가드 — kics-parser skill 참조.
3. 재사용 스크립트: `scripts/backfill_kr0004_mg_quarters.py` (다른 분기 추가 시 TARGETS만 수정).
   사이트 구조 probe: `scripts/_probes/_yebyeol_disclosure_probe.py` (2013~ 전 분기 fn_download ID 매핑).

status: resolved (11/11 fetch 완료, 파서 흡수 대기).
