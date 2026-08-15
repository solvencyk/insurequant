---
from: owner
to: downloader
created: 20260814T0746Z
status: resolved
route: backlog
company: MULTI
period: ALL
rule: NEW_DOMAIN_ONBOARD
iter: 1
---

## 미결 (sender 작성)

**신규 도메인 백로그 — 배당에 관한 사항(OpenDART alotMatter)을 회기별 정기 수집 대상에 편입.**

KRFS 쪽 리포트 지원 작업으로 오늘(2026-08-14) 생보10·손보9(19개사) × 4시점(2023.4Q·2024.4Q·2025.4Q·2026.2Q, reprt_code=11011/11012)의 배당 데이터를 alotMatter API로 1회성 수집했다. 이 파이프라인에 없던 도메인이라 앞으로는 결산기마다(4Q=사업보고서, 필요시 1Q/2Q/3Q도) insurequant가 정기적으로 수집·게시했으면 한다는 owner 요청.

### 참고 — 오늘 만든 1회성 산출물 (재사용 가능)
- 스크립트(이 저장소 밖, KRFS 세션 스크래치패드): `fetch_dividend_alotmatter.py`(19개사 corp_code 해결 + alotMatter 호출) / `build_dividend_xlsx.py`(요약·원본·corp_code매핑 3시트 엑셀 변환). 기존 `src/ifrs17/opendart_client.py`의 `OpenDARTClient`를 그대로 재사용(신규 엔드포인트 1개만 `client._get("/api/alotMatter.json", ...)`로 추가 — 클래스 자체는 미수정).
- 산출물: `insurequant_master_tables.xlsx`와 별도로 `배당현황_OpenDART_2023Q4-2026Q2.xlsx`(이 저장소 루트)에 저장 — 마스터 파일은 파이프라인 산출물로 보여 손대지 않음. 정식 도메인으로 편입한다면 `build_master_xlsx.py` 쪽에 새 시트로 합류시킬지 결정 필요.
- corp_code 19개사 전부 CORPCODE.xml 이름 대조로 해결 완료(회사명·corp_code 매핑은 위 엑셀 3번째 시트 참조). 삼성생명·미래에셋생명은 "OO생명보험"이 아니라 "OO생명"으로만 검색해야 매칭됨(주의사항으로 남김).

### 알아둘 함정 2건 (오늘 직접 겪음)
1. **alotMatter는 같은 `se`(예: "주당 현금배당금(원)")를 보통주식/종류주식 각각 별도 행으로 중복 반환**하고, 회사에 종류주식이 없으면 두 번째 행이 `stock_knd="-"`·`thstrm="-"`로 채워진다. 마지막 행으로 덮어쓰면 실제 DPS가 사라짐 — 반드시 `stock_knd`(예: "보통주식"/"종류주식")로 구분해서 파싱할 것. (한화손보처럼 실제 종류주식 배당이 있는 회사는 stock_knd가 제대로 채워짐.)
2. status가 000이어도 관련 행 전체가 "-"인 경우(그 결산기 실제 무배당)와 status 013(그 분기 자체 미공시)을 구분해서 처리할 것 — 둘 다 "배당 없음"이지만 의미가 다르다.

### 스코프 제안
- 최소: 위 19개사(생보10·손보9)를 4Q(사업보고서) 기준 매년 자동 갱신.
- 확장 여지: kics_disclosure 커버리지(37/39사)에 맞춰 전사로 확대, 1Q/2Q/3Q 중간배당도 함께 수집.
- 게시(퍼블리싱/디자이너 반영)까지 원하면 이 메시지가 downloader 완료 후 자연스럽게 parser/publishing에도 후속 발주가 필요함 — 우선 downloader 스코프(수집·raw 저장)만 이 메시지에 담음.

---

## 스코프 확정 (owner 후속 지시, 20260814T1250Z — 이 스레드에서 바로 착수)

owner 원문(2026-08-14): *"배당현황도 전부 OpenDart API로 크롤링 & 별도 탭에 게시하면 좋을거같은데."*
→ 위 "스코프 제안"의 **최소안이 아니라 전사안으로 확정**한다.

### C-1. 범위

- **회사**: 19개사가 아니라 `kics_disclosure.json` 커버리지 **전사**(현재 38-39사). 이름→corp_code는
  런타임 검색(`scripts/fetch_dart_fs.py:resolve_corp` 재사용 — 영구 매핑 파일 금지 규칙).
  삼성생명·미래에셋생명은 "OO생명"으로만 매칭되는 케이스(위 22행) 포함해 **resolve 실패 회사는
  census로 남겨 보고**할 것. 비상장사도 배당 공시는 하므로 상장 여부로 거르지 말 것.
- **기간**: FY2023~FY2026 × **reprt_code 4종 전부**(11011 사업 · 11012 반기 · 11013 1Q ·
  11014 3Q). owner 회신(2026-08-14): *"반기별 배당 전부 + 작업량 manageable하면 분기별 배당까지"*
  → 39사 × 4년 × 4reprt ≈ 620콜, 클라이언트 기본 0.4s 간격이면 **약 4~5분**이라 manageable로
  판단하고 전부 확정. 실행해 보고 레이트리밋·에러가 나면 **11011+11012를 먼저 완주**시키고
  1Q/3Q는 그 다음에 돌려라(부분 완주 > 전체 실패).

### C-2. 저장 (raw 캐시)

`data/dart/_alotmatter_cache/{corp_code}_{year}_{reprt}.json` — **응답 JSON 원본 그대로**.
`_fs_api_cache`와 같은 관례(파일 존재 시 재fetch 안 함, `--refresh` 옵션으로 강제 갱신).
가공·집계는 여기서 하지 말 것(파서 몫). `src/ifrs17/opendart_client.py`는 **수정하지 말고**
`client._get("/api/alotMatter.json", ...)` 호출만 추가.

### C-3. 함정 (위 owner 메모 2건은 파서에도 그대로 전달할 것)

원본 캐시를 그대로 저장하면 두 함정(같은 `se`의 보통주/종류주 중복행, status 013 vs 전행 "-")은
**파싱 단계에서 처리**된다 — 다운로더가 미리 뭉개지 말 것. 다만 **status 코드는 파일에 남는지
확인**하고(013도 저장), 회사×기간별 status 분포를 답변에 census로 적어라("무배당"과 "미공시"를
파서가 구분해야 한다).

### C-4. 후속 체인 (드라이버=오케스트레이터가 순서대로 킥한다)

1. (여기) downloader: raw 수집 → **parser에 raw-ready 발주**
2. parser: `dividend.json` 마스터 빌드(회사·연도·주당배당금·배당총액·배당성향·시가배당률 등
   `se` 행 정규화, 보통주/종류주 분리) + xlsx 합류 여부 결정
3. designer: **기존 `공시보고서.html`("준비 중" 빈 껍데기)을 배당 화면으로 채운다** —
   owner 확정(2026-08-14). 새 페이지·새 탭을 만들지 말 것(nav 4개 HTML 동시수정 회피).
   / publishing: keep-list + 문서 표에 신규 마스터 JSON 등록

루트의 `배당현황_OpenDART_2023Q4-2026Q2.xlsx`(오늘 KRFS 세션 산출물)는 **참조용 답지로만** 쓰고
파이프라인 산출물로 승격하지 말 것 — 재수집 결과와 대조해 불일치가 나오면 답변에 적어라.

## 답변 (recipient 작성 — 처리 후, 20260814T2210Z)

**C-1/C-2 완료 — 전사 39개사 × FY2023-2026 × 4개 reprt_code, 624셀 전수 수집.**

- 신규 `scripts/fetch_dart_alotmatter.py`(`OpenDARTClient` 클래스는 무수정, `client._get("/api/alotMatter.json", ...)`
  직접 호출만 추가 — 지시대로). `resolve_corp`는 `fetch_dart_fs.py` 것 그대로 재사용.
- 캐시: `data/dart/_alotmatter_cache/{corp_code}_{year}_{reprt}.json`(원본 그대로, 파일 존재 시 skip).
- 2-pass 실행(11011+11012 먼저, 11013+11014 다음) — **레이트리밋/에러 0건, 전량 완주**(재우선순위
  분기 처리 불필요했음).
- **corp_code 해결 39/39**(38개사는 이름검색, **KR0029 AIG손해보험만 이름검색 실패**(기존 문서화된
  quirk, `find_corp_codes_by_name`이 "AIG"를 "에이아이지손해보험"에서 못 찾음) → 문서화된 corp_code
  `00983606`으로 직접 fetch, 16/16 정상 수신(전부 013=배당공시 없음, resolve 실패지 fetch 실패 아님).

**status 분포 (624셀): 000(정상)=310 · 013(그 기간 무공시)=314.** reprt별·연도별 분해는
`data/_derived/alotmatter_fetch_census.json`에 census로 남김. **013 전량이 다른 도메인(FS API/body
XML)에서 이미 확인된 14개 구조적 미제출사**(NON_LISTED_SKIP·AUDIT_REPORT_ANNUAL — KR0004/49/50/51/
74/75/76/80/95/97/100/1010/1011/1098)와 **2026년 미도래 분기(3Q·사업보고서 아직 없음)**에 거의
전부 수렴 — 새로운 종류의 결측 아님, 이미 아는 패턴의 재확인. 상장사 16/16 완전커버 0개사이지만
이건 구조적(2026 3Q·연간이 아직 존재하지 않아 최대치가 14/16).

**C-3 함정 2건 raw에서 실측 확인** (원본 그대로 저장했으니 파서 단계에서 그대로 재현 가능):
1. 삼성생명 2023.4Q: `주당 현금배당금(원)`이 두 행(`stock_knd='-'`값 3,700 / `stock_knd='-'`값 `-`)
   — 종류주 없는 회사는 두 번째 행이 빈 placeholder. 한화생명 2023.4Q는 `stock_knd`가 실제로
   "보통주"/"우선주"로 구분되어 나옴(150원/`-`) — 정상 케이스 실측.
2. status=000인데 전 항목 `-`(무배당)와 status=013(무공시)이 실제로 섞여 있음을 확인 —
   예시는 아래 교차검증 참조.

**루트 `배당현황_OpenDART_2023Q4-2026Q2.xlsx` 교차검증 — 1건 불일치 발견, 재수집이 정답.**
19개사×4시점 answer-key 대조: 27건 "배당 있음"·26건 "무배당(전 항목 `-`)"은 재수집과 전부
일치. **`무배당(웹조사, API조회 생략)`으로 표기된 7건 중 6건은 재확인 결과도 무배당으로
일치하지만, 1건(한화생명 2023.4Q)은 실제로 배당이 있었다** — 현금배당금총액 112,709백만원,
보통주 주당 150원(우선주는 `-`). 그 xlsx는 이 셀만 API를 안 부르고 웹조사로 "무배당" 단정한
것으로 보임 — **재수집(API 기반) 쪽이 맞다**, xlsx가 참조용 오답. parser가 마스터 만들 때 이
xlsx가 아니라 방금 받은 raw 캐시를 정본으로 쓸 것.

**parser 후속 발주**: `inbox/parser/20260814T0938Z`.

**후속 필요(사용자/오케스트레이터 판단)**: C-4의 designer(`공시보고서.html` 채우기)·publishing
(keep-list 등록)는 parser가 마스터를 만든 뒤 순서. 이 스레드는 downloader 몫 완결로 `resolved`
전환.
