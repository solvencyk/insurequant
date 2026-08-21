---
from: downloader
to: parser
created: 20260814T0938Z
status: resolved
route: reparse
company: MULTI
period: 2023.1Q-2026.2Q
lane: ifrs17
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

신규 도메인 온보딩(`inbox/downloader/20260814T0746Z`, 지금 `_resolved/`) — **배당에 관한 사항
(DART alotMatter) raw 전수 확보 완료.** owner 확정 스코프: 새 마스터 `dividend.json` 빌드해서
`공시보고서.html`("준비 중" 껍데기)을 채우는 것이 다음 단계.

**Raw 위치**: `data/dart/_alotmatter_cache/{corp_code}_{year}_{reprt}.json`(원본 그대로,
가공 없음). 39/39개사 × FY2023-2026 × 4개 reprt_code(11011 사업·11012 반기·11013 1Q·11014
3Q) = 624셀. Census: `data/_derived/alotmatter_fetch_census.json`.

**KR0029 AIG는 corp_code `00983606`로 직접 fetch**(이름검색 실패는 기존 quirk, universe
제외 아님) — kics_disclosure 기준 이름→corp_code 매핑에 AIG 넣을 때 이 corp_code 쓸 것.

**status 분포: 000(정상)=310 · 013(그 기간 무공시)=314.** 013 거의 전량은 이미 아는 14개
구조적 미제출사(NON_LISTED_SKIP/AUDIT_REPORT_ANNUAL) + 2026년 미도래 분기(3Q·사업보고서).
새 결측 패턴 아님.

**파싱 함정 2건 (owner 원 티켓 그대로 인용, raw에서 실측도 확인함) — 마스터 빌드 시 반드시 처리:**
1. **같은 `se`가 보통주/종류주로 중복 행.** 종류주 없는 회사는 두 번째 행이 `stock_knd`
   구분 없이 `thstrm='-'`인 placeholder(삼성생명 2023.4Q 실측: `주당 현금배당금(원)` 두 행,
   하나는 `3,700` 하나는 `-`). **마지막 행으로 덮어쓰면 실제 DPS가 사라진다** — `stock_knd`로
   구분해서 파싱할 것(한화생명 2023.4Q는 진짜로 "보통주"/"우선주"로 구분되어 나옴).
2. **status=000인데 전 항목 `-`(그 기간 진짜 무배당) vs status=013(그 기간 자체 미공시)을
   구분할 것.** 둘 다 "배당 없음"으로 보이지만 의미가 다르다 — census의 status 필드로 판별 가능.

**루트 `배당현황_OpenDART_2023Q4-2026Q2.xlsx`(owner 오늘 1회성 산출물) — 답지 아니라 대조용,
1건 불일치 발견:** 19개사×4시점 대조 결과 27건 일치("배당 있음")·26건 일치("무배당, 전항목
`-`") · `무배당(웹조사, API조회 생략)` 7건 중 6건은 일치하지만 **한화생명 2023.4Q는 그
xlsx가 틀렸다** — xlsx는 그 셀만 API 호출을 생략하고 웹조사로 "무배당" 단정했는데, 방금 받은
raw는 실제 배당 있음(현금배당금총액 112,709백만원, 보통주 주당 150원)을 보여준다.
**마스터는 raw 캐시를 정본으로 쓰고 그 xlsx는 참조만 할 것** — 그 셀은 xlsx 쪽이 오답.

## 답변 (recipient 작성)

**완료** — 신규 `scripts/build_dividend.py` → 루트 `dividend.json`(1924행, 24개사=Tier-1
전원, 항목1-7 회사단위 + 8-11 종류주별). 함정 2건 전부 반영: (1) se 중복행은 stock_knd로
구분 — 검증 중 삼성생명(무종류주, 두 행 다 stock_knd='-')에서 실버그 하나 발견+수정(순진한
"보통 아니면 우선" 폴백이 삼성생명 실값을 우선주로 오분류하던 문제, `-`→보통주 기본값으로
고침). (2) status=000+전항목 '-'(진짜 무배당)은 배당금총액 항목만 값=0 명시, 나머지 항목은
행 생략 — status=013(미공시)은 어떤 항목도 행 없음. 한화생명 2023.4Q 검산: 112,709백만원/
보통주 150원, 요청하신 그 xlsx 오답 셀 정확히 그대로(재수집 raw가 맞음) 재현.

24사 = Tier-1 상장사 전원(비상장 Tier-2 15사는 전 기간 status=013 — 이 DART 엔드포인트가
비상장사는 아예 안 다루는 것으로 확인, 결측 아님). 골든(`test_dividend_golden.py`) 신설,
`insurequant_master_tables.xlsx`에 "배당" 시트 추가. designer(`공시보고서.html` 채우기)·
publishing(keep-list 등록)에 각각 통지함. 상세: `TODO_parser_ifrs17.md` 2026-08-14 (6th
pass).
