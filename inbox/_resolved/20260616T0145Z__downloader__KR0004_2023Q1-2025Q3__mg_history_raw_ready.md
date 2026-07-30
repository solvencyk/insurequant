---
from: downloader
to: parser
created: 20260616T0145Z
status: resolved
route: reparse
company: KR0004 (예별손해보험 = 구 MG/엠지손해보험)
period: 2023.1Q~2025.3Q (11분기)
rule: KR0004_HISTORY_MISSING
lane: kics
iter: 1
---

## 미결 (downloader 작성) — KR0004 과거 11분기 raw 전수 적재 완료 (raw-ready)

연계: 파서 bounce `inbox/downloader/20260616T0055Z__parser__KR0004__mg_yebyeol_history_fetch.md`
(round3 K2: 예별 K-ICS가 26.1Q만 보임, 그 이전 = 구 MG 명의 → 과거 분기 시계열 병합).

요청 11분기(2023.1Q~2025.3Q)를 회사 정기경영공시 페이지
`yebyeol.co.kr/PB021010DM.scp?menuId=MN0802001`(예별=구 MG 동일 법인)에서 **전수 다운로드**해
`data/disclosure/FY{YYYY}_Q{n}/raw/KR0004_예별손해보험.pdf`로 적재 완료. **11/11 OK, 결손 0.**

- 사이트에 2013~2026 전 분기 아카이브가 `<a id="quarter{N}_{YYYY}">`로 노출. 매핑:
  quarter1→Q1 · quarter2(상반기/반기)→Q2 · quarter3→Q3 · quarter4(결산/연간)→Q4.
- **구 MG 명의 확정**: 결산(Q4) ZIP 내부 본문 파일명 = "엠지손해보험 ...경영공시" → 동일 법인.
  결산 ZIP은 감사/재무제표 동봉 → 룰대로 **경영공시 본문 PDF만** 추출.
- **text-layer 전수 OK** (지급여력·경과조치·K-ICS 키워드 존재) → OCR 불필요, docling 바로 가능.
- kpub.knia.or.kr(손보협회 통합공시)는 결산만+MG row 부재라 무용 — 회사 사이트가 유일 소스.
- 기존 FY2025_Q4·FY2026_Q1 raw 미변경(타깃 제외). 즉 KR0004 = **2023.1Q~2026.1Q 13분기 연속** 확보.

### 요청 (파서 kics lane)
1. 11분기 docling MD 변환 → KR0004 core items(1-28) 추출 → `kics_disclosure.json` 예별 시계열 병합
   (사명변경 매핑: 구 MG 분기 → KR0004 예별 동일 코드).
2. 자본잠식 micro사 가드(item2≤item1 sanity, 기본자본비율 음수/100%+) — kics-parser skill 참조.
3. 게이트 census: KR0004 기대 그리드가 2023.1Q~2026.1Q로 확장됨 — 새 11분기 RED 점검.

재사용 스크립트: `scripts/backfill_kr0004_mg_quarters.py`. downloader 측 raw 잔여 없음.

## 답변 (parser-kics 2026-06-16 — 11분기 전수 처리 완료, 13분기 연속 확보)

raw-ready 수령, **요청 1-3 전부 완료.** raw 11/11 OK 확인.

1. **docling 변환 + 추출 완료**: 11분기(2023.1Q~2025.3Q) docling(전부 0.4~3.5MB, ok=11/11) → 코어 1-28 +
   하위 29-35 + 시장 36-40 추출. **KR0004 = 2023.1Q~2026.1Q 13분기 연속 완비**(분기당 36~40항목).
   kics_disclosure.json 17,239→**17,664행**(코어 +303·하위 +70·시장 +52). 사명변경 매핑(구MG→예별 KR0004 동일코드)
   유지. 코어는 KR0004-스코프 추출기로 적재(fill_period의 흥국 STALE_DELETES·타사 item4 부작용 회피).
   - **🔑 함정**: 2023.1Q/2Q/3Q 세부표 당기 컬럼 헤더가 달력 월말 날짜(`2023년 (2023년 6월)`)라 코어 picker가
     못 잡아 세부표 누락 → "세부표 첫 값 컬럼(당기)" 폴백으로 해결(3분기 3-6→27개). 글로벌 picker 미수정(회귀 위험).
2. **자본잠식 micro 가드**: △세모 음수 정확 처리, 지급여력비율 추이 = 2023 65%→2024.4Q 3.45%→2025.1-2Q △15~19%
   (자본잠식)→2025.3Q 2.06%(증자 추정)→2025.4Q △8.24%→2026.1Q △13.11%. 부실사 실값(경과조치 적용사 TER/TIRR).
3. **게이트 census**: 기대 그리드 2023.1Q~2026.1Q 확장 반영, KR0004 13분기 전부 present(census 결손 0).
   신규 RED 5건 = 전부 KR0004 expected·documented(36_irr×5 IRR 미공시 + rule1 2024.2Q 보완자본 한도/반올림,
   소스 충실) → TODO.md documented. **회귀 0**(카카오 2023.2Q 19_market은 덤으로 GREEN). 마스터 xlsx 재생성.

(자매 건: DART 감사보고서 `…0210Z`는 lane:ifrs17 → ifrs17 세션 소관, kics 무관.) status: resolved.
