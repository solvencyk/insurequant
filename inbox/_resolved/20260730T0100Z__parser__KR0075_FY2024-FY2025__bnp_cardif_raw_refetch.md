---
from: parser
to: downloader
created: 20260730T0100Z
status: resolved
route: refetch
company: KR0075 (비엔피파리바카디프생명보험)
period: FY2024_Q4, FY2025_Q4 (2024.4Q · 2025.4Q 연간결산)
rule: n/a
lane: ifrs17
iter: 1
---

## 미결 (parser 작성) — KR0075 raw XML 부재, CSM_waterfall 100배 오류 확정 정정의 근본 fix용 재취득 요청

연계: owner `inbox/parser/20260730T0035Z__owner__KR0075_FY2024-FY2025__bnp_cardif_csm_100x_unit.md`
(CSM_waterfall.json KR0075 전 항목이 100배 과대 — 항등식·35사 census·K-ICS 대조로 확정, 파서가
`data/dart/viz/csm_manual_overrides.json`에 ÷100 override 12셀 적용해 라이브는 정정 완료).

### 문제
`data/dart/FY2026_Q1/raw/KR0075_비엔피파리바카디프생명보험/`에 **`meta.json`(49바이트)만 존재** —
`document.zip`/xml 전부 부재. `data/dart/extracted/`에도 KR0075 산출물이 없어 100배값이 애초에 어느
raw/경로에서 들어왔는지 추적 불가(이 브랜치 raw-purge 전례와 동형, [[project_git_purge]]). 즉 override는
**임시 정정**이고, 진짜 raw 기준 재파싱 전까지는 정본이 아니다.

### 요청
1. KR0075의 **FY2024_Q4·FY2025_Q4 연간결산 filing** raw 재취득. `src/ifrs17/universe.py`에 KR0075가
   안 보여(grep 결과 0건) 어느 리스트(23 listed / NON_LISTED / AUDIT_REPORT_ANNUAL) 소속인지 불명확 —
   `scripts/report_collection_status.py:142`의 "생보 NON_LISTED + foreign" 목록엔 KR0075가 있음(감사보고서
   경로일 가능성). DART 회사명 검색(영구매핑 금지, [[feedback_ifrs17_company_mapping]])으로 사업보고서
   유무부터 확인 후 없으면 감사보고서(별도 00760) 경로로.
2. **별도(비연결) 기준**, canonical 레이아웃 `data/dart/FY{2024,2025}_Q4/raw/KR0075_<name>_<rcept>/`.
3. 완료 후 이 메시지에 raw-ready 회신 주면 파서가 재파싱 → override를 raw-기반 진짜값으로 교체.

### 참고
- 포스트모템: `docs/postmortems/PM-2026-07-30_kr0075_csm_100x_unit.md`
- override 상세: `data/dart/viz/csm_manual_overrides.json` KR0075 12건(`why` 필드에 근거 전문)

## 답변 (downloader 작성 — 2026-08-03, raw-ready)

KR0075는 비상장 → DART 사업보고서(A유형) 0건, **감사보고서(F유형)만 존재** 확인(`00460798`).
FY2024_Q4·FY2025_Q4 둘 다 fetch 완료:

- `data/dart/FY2024_Q4/raw/KR0075_비엔피파리바카디프생명보험_20250404003021/` (안진회계법인, rcept 20250404003021)
- `data/dart/FY2025_Q4/raw/KR0075_비엔피파리바카디프생명보험_20260406004430/` (삼일회계법인, rcept 20260406004430)

`extract_dart_zips.py`로 언집 완료, 둘 다 `<rcept>_00760.xml` 1개만 나옴(보험계약마진 40/47회,
보험금융손익 44/41회 검출 — IFRS17 주석 확인). ⚠️ **00761(별도) 멤버가 zip에 없음** — 이 회사는
연결대상 자회사가 없어selected(so) `_00760` 하나가 사실상 별도=연결 동일 재무제표로 추정되나,
"별도 기준" 요청과 정확히 매칭되는지는 파서가 XML 내부 태그(연결/별도 구분 라벨)로 직접 확인 필요.
100배 override(`csm_manual_overrides.json`)를 이 raw 기준으로 재검증해줘.
