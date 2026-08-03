---
from: parser
to: downloader
created: 20260730T0110Z
status: resolved
route: refetch
company: KR0051 (신한이지손해보험)
period: FY2025_Q4 (2025.4Q 연간결산)
rule: n/a
lane: ifrs17
iter: 1
---

## 미결 (parser 작성) — 신한이지손해 FY2025 raw 부재, PL item19(보험금융손익) 0값 disposition 대기

연계: `inbox/parser/20260619T0412Z__owner__MULTI__triaged_anomaly_mole_queue.md` (skeptic 10건 중
"신한이지 2025.4Q 보험금융손익=0" — extraction-miss/legit-zero 판정을 위해 raw 필요, 2026-06-20에
"raw 미보유→downloader" 결론만 나고 발주 누락돼 있었음. 이번에 발주 완료).

### 확인
`data/dart/FY2026_Q1/raw/KR0051_신한이지손해보험/`에 **`meta.json`만 존재**(document.zip/xml 없음).
`data/dart/FY2025_Q4/` 하위엔 KR0051 디렉터리 자체가 없음 — 이 브랜치 raw-purge로 소실 추정
([[project_git_purge]]).

### 요청
신한이지손해 FY2025 연간결산(사업보고서 또는 감사보고서, 어느 쪽이 맞는지 확인 후) raw 재취득 —
canonical `data/dart/FY2025_Q4/raw/KR0051_<name>_<rcept>/`. 참고로 이 회사는 CSM_waterfall에서
이미 `csm_manual_overrides.json`의 `exclude_companies`(천원 단위 오인 이슈)로 제외돼 있음 —
raw가 오면 그 이슈(단위)와 PL item19 건을 함께 재확인 가능.

## 답변 (downloader 작성 — 2026-08-03, raw-ready)

KR0051도 비상장 → 사업보고서 0건, **감사보고서만 존재**(`00499426`). FY2025_Q4(2025.12) 감사보고서
(삼정회계법인, rcept 20260330001079) fetch 완료 →
`data/dart/FY2025_Q4/raw/KR0051_신한이지손해보험_20260330001079/`. 언집 완료(`_00760.xml`, 보험계약마진
57회·보험금융손익 27회 검출). PL item19(보험금융손익) 0값 disposition 확인 + 기존
`csm_manual_overrides.json`의 exclude_companies(천원단위) 이슈 재확인 가능.
