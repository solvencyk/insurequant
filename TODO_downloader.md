# Insurequant TODO — Downloader Stage

> Last updated: 2026-09-03 · Stage 1/5 — downloader
> Prompt: docs/agents/claude-agent-downloader.md (+ docs/agents/source-catalog.yaml) · Changelog: docs/changelog_downloader.md

**Cross-stage TODO:** `TODO.md` (root). **This file:** active + done items scoped to data collection only.

## Status

**🟢 2026-09-03 owner 직접 지시 — FY2026_Q2 정기경영공시 raw/ 정본화(1→39) + 항목5(해약환급금
준비금) 3분기 이월버그 4사 발견, parser(ifrs17) 발주.** 상세: `docs/changelog_downloader.md`
2026-09-03.

- **owner가 "PDF가 거의 통째로 빠졌다"고 지적한 근거**(`raw/*.pdf` count=1)**는 관찰은 맞았지만
  원인 진단은 틀렸다 — 39사 전부 이미 원문이 있었다, 단 다른 폴더(`pdf/`)에.** 2026-09-01
  04:56 커밋 `8f5e3b8`("39사 전원 적재+검증 RED 0")가 그 라운드를 이미 완주했는데, 그 시점
  `download_disclosure_2026q2_{nonlife,life_sites}.py`의 `OUT_DIR`이 `raw/`가 아니라 `pdf/`로
  바뀌어 있었다(원인 미상 — 이 사실이 `TODO_downloader.md`에 기록되지 않아 이번 세션까지
  아무도 몰랐다). validation이 같은 날 `disclosure_pdfs()` 공유 해석기를 배선해 `raw/` 우선·
  `pdf/` 폴백으로 두 위치를 다 읽게 만들어 놔서 K-ICS 파싱·검증(RED 0)은 이미 정상 동작 중
  이었다 — 그래서 **파이프라인은 안 깨졌는데 owner가 보는 위치(raw/)는 비어 보이는** 상태.
- **세션 도중 `pdf/`→`raw/` 39개 파일이 동시 세션에 의해 이동됐다**(mtime 8/31 보존 확인,
  내가 만든 것 아님 — 셔플 순간을 실측: 확인 시점 A=pdf 39/raw 1, 직후 B=pdf 0/raw 39).
  결과적으로 raw/ 가 정본 위치로 정리됨(레거시 13분기·FY2026_Q1과 동일 관례로 통일).
  `source-catalog.yaml`(`output: raw/`)과도 다시 일치.
- **39사 전원 내용검증**(신규 `scripts/_probes/probe_20260903_verify_2026q2_disclosure_pdfs.py`):
  회사코드 39/39 = source-catalog 기대 집합과 정확히 일치(과부족 0). 기간마커("2026년2/4분기"·
  "2026.1.1~6.30") 36/39 전자검출 + 스캔본 3사(KR0010·KR0079·KR0087)는 240dpi 렌더로 육안
  확인(전부 진짜 그 회사·그 분기, 텍스트레이어만 없음 — OCR 필요, parser 소관).
  `validate_disclosure_freshness.py --period FY2026_Q2`: RED=0 YELLOW=0 GREEN=39(직전분기와
  전부 다른 파일 — 재탕 없음).
- **"7-2/7-3.해약환급금준비금등의적립" 절 39/39 보유 확인** — owner 원 지시의 "손보는 5-3"은
  실측과 다르다(정정): 생손보 공통으로 "7-3"(일부사 7-2 표기)을 쓴다, KR0049·KR0051(손보 2사)
  raw에서 직접 확인. 37사는 전자 텍스트로, 2사(KR0010·KR0087, 완전 스캔본)는 절 유무 자체가
  OCR 전엔 미확정 — 그 2사만 대조 불가 사유로 명시.
- **owner 지적이 맞았다 — KR0069(삼성생명) 항목5가 3분기(2025.4Q~2026.2Q) 완전 동일값(832,412
  백만) 고정.** raw p48 실측: 2026.1Q=1,651,800백만·2026.2Q=3,126,000백만(마스터의 3.76배).
  같은 3분기-플랫 패턴을 IFRS17_BS.json 전수 스캔(항목5)으로 찾으니 6개사 — **KR0049·KR0097·
  KR0080 3사 추가로 버그 확정**(raw 대조 완료), **KR0004·KR0075는 원문도 0이라 정상**(대조
  없이 넘기면 오탐이었을 케이스). 값 산출은 parser 소관이라 고치지 않고 근거와 함께
  `inbox/parser/20260903T0048Z__downloader__MULTI_2026.2Q__item5_surrender_reserve_frozen_3q.md`
  로 발주. **더 이전 분기까지 얼어있을 가능성·같은 표의 다른 항목(대손준비금 등) 전이 여부는
  미확인 — parser 후속 필요.**
- **census: FY2026_Q2 raw/ 1 → 39.** 미게시/실패 구분 불필요 — 39/39 전원 이미 posted+fetched
  상태였음(원래 우려였던 "일부 미게시"는 해당 없음).

**🟢 2026-09-02 DART 본문 XML 전수 census — 발주된 "결측" 은 오탐, 진짜 결손 3칸 회수해 0으로.**
상세: `docs/changelog_downloader.md` 2026-09-02.

- **발주 근거였던 삼성생명/미래에셋생명 2026.2Q "디렉터리 자체가 없음" 은 사실이 아니다.**
  둘 다 5.3MB·3.7MB 본문 XML 이 디스크에 있다. raw 리프는 `KR####_<DART canonical>` 인데
  DART canonical 이 K-ICS 원수사명과 달라서(`삼성생명` vs `삼성생명보험`) **회사명으로
  디렉터리를 찾으면 거짓 결측이 나온다. 반드시 KR 코드로 키를 잡을 것.**
- **함정 하나 더**: `leaf/*.xml` 만 glob 하면 **64칸**이 "zip 만 있음" 으로 나오는데 전부
  `leaf/xml/*.xml` 로 이미 풀려 있다. 세 레이아웃(`*.xml`·`xml/*.xml`·`extracted*/*.xml`)
  을 다 봐야 한다 — `extract_dart_zips.py` 가 인정하는 그 세 개.
- **census before -> after (39사 x 14분기 = 546칸)**: xml 372 -> **375** · zip_only 0 ·
  no_filing 43 -> **45** · MISSING 131 -> **126**. 그중 **분기 공시사의 진짜 결손 3 -> 0.**
  나머지 126칸은 연1회 공시사(감사보고서만 내는 회사)의 비-4분기라 원천에 필링이 없다
  (판정 근거 = `data/_derived/bs_carry_forward_cells.json` `hold_forward_annual_only_filer`).
- **회수 3칸 (전부 2023.4Q, 전부 감사보고서)**: KR1098 카카오페이손해 `20240329002933` ·
  KR0075 BNP파리바카디프 `20240403001384` · KR0150 서울보증 `20240403001186`.
  셋 다 **사업보고서를 안 내는 회사**라 `A001` 로 훑던 과거 스윕이 `no_filing` 으로
  기록했던 것 — AIG·악사손해 5사에 이은 **같은 함정 세 번째 재발**. `pblntf_ty=None` 으로
  전체를 훑을 것. **특히 KR0150 은 2026-08-19 발주 C 의 "7분기 no_filing 확정" 을
  부분적으로 뒤집는다**(2023.4Q 는 감사보고서가 있었다; 1~3분기 부재는 여전히 맞음).
  내용검증 통과(제3/22/57(당)기 · 2023-12-31 마커 · 회사명 13~22회).
- **2026.2Q 본문 24/24 내용검증 통과** — 전원 제NN기·2026-06-30 마커(50~203회)·BS 키워드
  보유, 1.2M~22.3M자, 스캔본/빈 껍데기 0. 유일 플래그 NH농협손해는 본문이 자기를
  '농협손해보험' 으로 쓰는 것(리프는 'NH농협손해보험') — 발주를 만든 것과 같은 탐지기 함정.
- **신규 경로자산 `scripts/_probes/census_dart_body_xml.py`** (재사용, 진짜 결손 시 exit 1).
  `check_dart_raw_coverage.py` 와 **축이 반대라 둘 다 필요** — 그쪽은 유실(high-water mark),
  이쪽은 기대 그리드 미충족. 유실 축도 clear(baseline 395 -> 398 `--update`, missing=0).
- AIG 2026.1Q/2Q 는 라이브 확인(2026년 필링 = 감사보고서 2건뿐) 후 `no_filing` 마커 기록.
  AIG 2022.4Q 2건은 owner 가 2022.4Q 백필을 보류 확정했으므로 미착수, `known_absent` 유지.

**🟢 2026-09-01 인박스 처리 — KR0011/KR0029/KR0150 정기경영공시 셀렉터 하드닝
(`inbox/_resolved/20260901T0140Z`).** 2026.2Q 라운드에서 세 회사가 위치고정 xpath(`li[1]`)/
duplicate id(`id="test1"` ×5)/하드코딩 파라미터(`pancId=15467`)로 직전 분기(1분기) PDF를 조용히
재수집한 것의 재발 방지. 세 사이트를 실제로 열어 현재 마크업으로 확인 후(추정 없음)
`docs/agents/source-catalog.yaml` + `scripts/download_disclosure_2026q2_nonlife.py`를 분기 라벨
텍스트 매칭(`contains(., "상반기"/"2분기")`)으로 교체 — KR0011은 `url2` 하드코딩 제거하고
`two_step`으로 매 실행 목록에서 상세 URL 해석, KR0029는 사이트가 2단계 자체를 없애 `pancId` 코드
전체 삭제(`direct_href`로 단순화), KR0150은 id 대신 링크 자신의 텍스트로 매칭. `_run_one`에
`_verify_period()` 신설 — 집은 요소의 텍스트를 다운로드 직전 정규식으로 재검사해 기대 분기가
아니면 즉시 실패(조용한 오탐 재발 차단). 스크래치에서 실제 엔진으로 재수집해 대상분기(2026.2Q)·
회귀(2026.1Q) 양방향 검증 — 셋 다 기존 repo 파일과 sha256 완전 일치. `validate_disclosure_
freshness.py` RED=0 유지 확인. 신규 `tests/test_disclosure_selector_hardcoding.py`(12 tests,
mutation-tested against 원본) — **단, `scripts/prepush_check.py`의 fast 리스트에는 미배선**(동시
편집 중인 공용 파일이라 충돌 회피, validation/orchestrator 후속 필요). 상세: 티켓 `## 답변`.

**🟢 2026-08-30 인박스 처리 — 생보 22사 **자사 사이트** 직접 스윕: 0/22 게시,
경로자산 22개 신규 확보 (`inbox/downloader/20260830T0400Z`).** 상세: `docs/changelog_downloader.md` 2026-08-30.

- **owner 지적 수용**: 08-27/08-29 스윕은 생보를 **생보협회 일괄페이지만 보고** 판정했다.
  그건 "협회에 올라왔나" 이지 "회사가 냈나" 가 아니다. **22사 자사 경영공시 페이지를 직접 훑음.**
- **결과 = posted 0 / not_posted 22 / not_observed 0 / unreachable 0.** 22사 전원에서
  **그 회사의 2026 1분기 행을 실제로 읽어낸** 뒤 2분기 부재를 확인했다(양성대조 성립 —
  "탐지기가 아무것도 못 봄" 이 아니라 "볼 수 있는데 없음"). 같은 날 협회 그리드도 재확인
  (2026년, 1분기=22, 2분기=0) — 두 독립 경로 일치.
- **코리안리(KR1000) owner 확인 반영 → 손보 17사 전원 판정 완료.** 08-29 UNKNOWN 이던 건을
  owner 가 직접 확인해 미게시 확정(2026-08-30). `listing_census.json` 에 `verdict=not_posted`
  + `verdict_source=owner_manual_check` + `probe_verdict=unreachable` 병기(관측 vs owner 확인
  구분). **39사 전체 = 1 게시(하나손보) + 38 미게시, 미관측 0.**
- **신규 `scripts/_probes/census_q2_life_own_sites.py`** — 08-29 프로브를 **import** 해서 쓰고
  (함정 4종 그대로 상속) 그 위에 **함정 5종을 추가로 막았다. 4종은 조용히 틀린 판정을 낸다**:
  ⑤ 상시 네비 메뉴가 "관측됨" 을 만족시켜 **6개사가 자기 홈페이지에 선 채로 not_posted** 를
  받음 → 판정에 **연도 붙은 기간 행** 요구 ⑥ 수시공시 등록일 `2026.06.30` 이 기간 라벨로
  읽혀 **KB라이프 거짓 posted** → Q2 히트는 기간을 이름으로 불러야 함 ⑦ `2026년
  회계연도(1분기)`(삼성생명)처럼 연도-분기 사이 글자 삽입 → 간격 14자 허용하되 **사이에
  숫자 금지** ⑧ `FY2026 1Q`(라이나)·`FY2026 Q1`(BNP) 라틴 분기 + 연도 선행 → 세 어순 커버
  ⑨ **연도×분기 표**인 회사(iM라이프)는 라벨에 2026·2분기가 같이 안 나옴 → **칸을 직접 읽음**.
- **`--selftest`(오프라인 1초) 를 상설로 넣었다.** 오늘 실측한 라벨 방언을 Q2 로 바꾼
  **양성대조 21건** + **음성대조 7건**. **정규식을 고치면 반드시 돌릴 것 — 아무것도 매칭
  안 하는 탐지기도 "2분기 없음" 이라고 보고한다.** 현재 21/21·오탐 0/7. `--rescan` 은
  저장된 라벨 덤프로 네트워크 없이 22사 판정을 재계산한다.
- **접근 함정과 우회**: 흥국생명식 `home_first`(홈 먼저 방문해 session/referer 확보)를 22사
  전원 기본 적용. 더 큰 장벽은 **딥링크가 없는 사이트** — JS 메뉴(동양·라이나·신한라이프·
  KDB·삼성·iM라이프)는 접힌 드롭다운이라 Playwright 클릭이 타임아웃 → **페이지 안에서
  `element.click()` 디스패치**. 그래도 안 되면 원본에서 라우트를 캐냈다: 삼성생명
  `/gw/api/display/menu/all` 메뉴 API(기존에 쓰던 `PDO-MAMAA010100M` 은 **안내 페이지**,
  정본은 `PDO-MAMAP010100M`), 라이나는 Nuxt 청크 grep. **교보는 URL 이 반직관적** —
  `.../fixed-term/**last-year**` 가 현행이고 `.../fixed-term` 은 404, 기간은 `<title>` 에 있음.
  **동양생명 공시는 별도 서브도메인** `pbano.myangel.co.kr`.
- **경로자산 위치**: `docs/agents/source-catalog.yaml` 신규 `disclosure_life_own_sites`
  (22 entries: home·url·click_path·함정 notes) + 프로브의 `LIFE_SITES`(운영 정본).
- **받은 파일 0개** → `data/disclosure/FY2026_Q2/` 변화 없음, parser 통지 없음, docling 없음.
- **다음 확인 = 2026-08-31(월)** 유지. 순서: 생보 자사 census → 손보/협회 census →
  posted 인 회사만 다운로드 → `verify_q2_disclosure_content.py` 내용검증.

**🟡 2026-08-29 인박스 처리 — 2026.2Q 정기경영공시 재스윕: 1/39 확보, 침묵실패 함정 구조적 해소
(`inbox/downloader/20260829T1900Z`).** 상세: `docs/changelog_downloader.md` 2026-08-29.

- **하나손해보험(KR0050) 2026년 상반기 경영공시 확보** — 39사 중 유일. 60p·1,620,955B,
  1페이지 `[기간 : 2026. 1. 1 ~ 2026. 6. 30]`·보험업감독규정 제7-44조·2026-1Q 마커 0건으로
  **내용 검증** 통과. `data/disclosure/FY2026_Q2/pdf/`. docling 변환 안 함(parser 소관).
  parser raw-ready: `inbox/parser/20260829T2130Z`.
- **미게시 확정 37사**(생보 22 + 손보 15) · **미확인 1사 = 코리안리(KR1000)**, 전 transport
  `Empty reply from server`(서버측 다운, 2026-08-17 과 동일). **미확인을 미게시로 세지 말 것.**
- **함정 대응이 사후대조 → 사전판정으로 바뀌었다.** 신규 `scripts/_probes/
  census_q2_disclosure_listings.py` 가 다운로드 전에 listing 라벨을 전량 덤프해
  `posted/not_posted/not_observed/unreachable` 4-값 판정을 낸다(행 인덱스 미사용).
  신규 `scripts/_probes/verify_q2_disclosure_content.py` 가 받은 파일을 freshness+period+
  doctype 3중 검사(기존 `check_q2_disclosure_freshness.py` 의 해시대조만으론 불충분 —
  해시가 달라도 틀린 분기일 수 있다). **다음 세션은 이 두 개를 앞뒤로 끼고 돌릴 것.**
- **KR0050 XPath 를 행 인덱스 → 텍스트 앵커로 교체**(`download_disclosure_2026q2_nonlife.py`).
  이 사이트는 1/4분기를 2/4분기 **위에** 나열해서 `tr[1]` 이 Q1 을 집었다(실제 발동, Q1 파일과
  SHA256 동일한 파일을 받아옴). 다른 회사도 게시되면 같은 방식으로 앵커링할 것.
- **다음 확인 = 2026-08-31(월).** 근거: 마감 = 분기말+2개월 = 8/31, KB손해 24년치 등록일에
  요일을 붙이면 **마감일 또는 직전 마지막 영업일**에 내고 주말 게시는 0회. 올해 8/29=토·
  8/30=일이라 "8/29~31 창"의 영업일은 **8/31 월 하루뿐**이다. 9/1(화) 낙오사 1회 추가.

> 📦 **Status 이력은 `docs/todo_archive_downloader.md` 로 이동했다** (2026-09-11, 내용 무수정 — 2026-08-29 및 그 이전 항목). 세션 시작 시 읽지 않는다; changelog 처럼 특정 과거 결정의 배경이 필요할 때만 연다. **이 Status 는 최신 5개 항목만 유지**하고, 밀려난 항목은 그 파일 헤더 바로 아래에 그대로 잘라 붙인다.

## Active follow-ups (next sessions)

| # | Task | Priority | Notes |
|---|------|----------|-------|
| Q2-2026-SWEEP | **2026.2Q 정기경영공시 8/31 탐색 루프 (2시간 간격) + 수집** | 🔴 **P0 (내일)** | owner 지시(2026-08-30): 호출받으면 2시간 간격으로 게시 여부 census -> `posted` 로 뒤집힌 회사만 수집 -> 파싱부터 끝까지. **실행 순서 정본은 루트 `TODO.md` 「상시 점검」의 2026.2Q 항목**(1~5단계 명령어 포함). 여기에 복사하지 말 것. 요점만: 프로브 2종을 매 회차 다 돌리고(`census_q2_disclosure_listings.py` 손보 + `census_q2_life_own_sites.py` 생보), `unreachable` 은 미게시가 아니며, 생보 2Q 다운로더는 아직 없어 `download_disclosure_2026q1_life.py` 복제로 만들어야 하고, 수집분은 반드시 `verify_q2_disclosure_content.py` 3종 검사(freshness/period/doctype)를 통과해야 한다. |
| ~~HKF-WAF-BLOCK~~ | ~~흥국화재(KR0005) FY2024_Q4 정기경영공시 재취득~~ | ✅ **2026-07-07 완료(재취득 불필요로 정정)** | WAF 때문에 재다운로드는 결국 못했지만 **필요 없었음** — 원인 재조사 결과 **기존 raw가 이미 맞는 파일**이었음(폰트인코딩 깨짐으로 fitz 텍스트추출만 실패, 렌더링+비전으로 읽으면 정상 정기경영공시). 흥국생명(KR0071)도 동일 패턴(스캔이미지+뒤에 감사보고서 합본). 양사 item1-28(전/후)·item36 등을 raw에서 직접 판독해 `kics_disclosure.json` 반영, 게이트 RED 0. 상세: `docs/changelog_downloader.md` 2026-07-07, `TODO_parser_kics.md` 8차 |
| F7 | **KOSIS 손보사별 손해율 시계열 ingest** | 🔴 P1 | 출처: 국가통계포털 KOSIS `orgId=382, tblId=TX_38202_A1561`. JSON API 공개 → 자동화 쉬움. 손해보험사별 원수보험료/보유보험료/경과손해율 (개별사 × 분기/연간). 현재 손해율은 PDF/HTML 파싱 기반 → KOSIS 교차검증으로 품질 보완. **액션**: `scripts/ingest_kosis_loss_ratio.py` 신규 + `data/kosis/<stamp>/` |
| F8 | **손보협회 비교공시 (consumer.knia.or.kr) — GA 인사이트** | 🔴 P1 | 핵심 항목: (a) **채널별 불완전판매비율** (GA/직판/방카 구분) (b) **설계사정착률** (c) **민원발생현황** (d) **보험금 부지급률** (e) **보험금 지급지연율**. **액션**: 사이트 구조 probe (JS-rendered 가능성 점검) → API 또는 scrape 결정 → `data/knia_consumer/` |
| F9 | **data.go.kr 금융통계 API 추가 연동** | 🟠 P2 | 이미 자본성증권 (15059611) 연동 패턴 있음. 추가: (a) `15061307` 금융통계손해보험정보 (b) `15061306` 금융통계생명보험정보 (c) `15094797` 실손보험정보. **액션**: `src/bonds/fsc_client.py` 패턴 재활용해서 `src/finstat/` 신규 모듈 작성 |
| F10 | **GA 통합공시 (gapub.insure.or.kr)** | 🟠 P3 | GA별 불완전판매비율/계약건수/모집실적. **액션**: 사이트 구조 probe |
| F14 | **규제 뉴스 피드** (roadmap §1E) | 🟠 P3 | 최근 1주 규제뉴스 스크래핑 + 키워드 피드백 학습 랭킹. 큐레이션 피드(자동발행 X) |
| DART-RAW-PROVENANCE | DART raw 23사×13분기 source_file+as_of 사이드카 (`emit_dart_raw_provenance.py`) | 🟠 P2 | Phase 2 gate: CSM_waterfall/PL_breakdown 마스터 provenance 필요. bonds 완료, DART raw 잔여 |
| CAPSEC-SAMO-GAP | 삼성생명·악사·하나손해·AIA·삼성화재 사모채 per-bond 데이터 없음 | 🟠 P2 | FSC 0건, DART 0건 확인. 공개소스 없음. forward-sim에서 BS 총계 기반 단순가정 처리 불가피 — publishing 결정 필요 |
| OCR-MARKETRISK | 시장위험 스캔-only PDF OCR 경로 | 🟢 low (2026-08-15 owner pass) | KB손해·한화손해 2023.4Q 금리위험 = full-page 이미지(텍스트레이어 없음); 카카오페이 2025.4Q 시장위험 = 스캔. 파서가 fitz/pdfplumber로 텍스트 못 뜸 → OCR 필요. **owner "됐어 패스" — 두 옵션(downloader OCR 스택 도입 / owner 수동 OCR) 다 보류, 재요청 전 미착수.** 출처 `inbox/downloader/20260614T1232Z` item(2) |
| MISC-SEIBRO | Seibro HTML fallback | 🟢 low | m.seibro.or.kr smoke ok; lower priority since FSC works |
| ~~REORG2-DART~~ | ~~DART batch script 3개 canonical-layout refactor~~ | ✅ **2026-05-30N 완료** | `scripts/_dart_path_helpers.py` 신규 + 3 script 갱신 + smoke 9/9. 다음 분기 fetch는 `data/dart/FY<year>_Q<q>/raw/` canonical 위치에 쌓임 |
| BATCH-HISTORICAL-FIX | ~~`ifrs17_batch_historical.py` 정정 rcept picking 버그~~ | 🟠 P2 (코드 fix 완료, 소급감사 잔여) | **2026-08-13 코드 fix 완료**: KR0104 2023.4Q fetch 중 실발화(status=014, `[첨부정정]`이 원본보다 먼저 골라짐) → `fetch_rcept_no`를 "대괄호로 시작하는 report_nm 전부 제외"로 수정, 재시도 확인. **잔여**: 2026-05-30 이래 누적 DART 이력 중 이 버그로 조용히(에러 없이) 정정본이 골라진 셀이 있을 수 있음(첨부정정도 document.xml이 성공 응답하는 경우 있음) — 소급 전수 재검사 미실시, 필요시 validation이 우선순위 판단 |
| F15-DL | 동양생명 2025.2Q~2026.1Q 재다운로드 검토 | 🟠 P2 | (F15 본체는 parser 버그 — `TODO.md`) 추출단계에서 wide `<TE>` 표의 잔액(기초/기말)행이 전부 0으로 들어옴 → 원본 다시 받아야 할 수도 있음. 재다운로드 후 재파싱이 효과적인지 먼저 확인 |
| FUTURE-DL | DART 별첨 fetch endpoint 조사 (KB/메리츠/NH FY2025 LOB) | 🟠 P2 | KB/메리츠/NH FY2025 사업보고서는 LOB 표를 별첨 감사보고서로 분리. 결정 2026-05-30: **fetch 안 함** (본문에 다 있음, 회사별 라벨 변형 처리로 해결). 단 별첨 endpoint 위치는 future reference로 기록 — 새 이슈에 필요 시 조사 |
| IR-SAMSUNGLIFE-23 | 삼성생명 IR FY2023 Q1/Q2/Q3 standalone factsheet 부재 | 🟢 low | samsunglife.com IR은 ~2년치만 보존 → FY23 Q1-Q3 standalone factsheet 롤오프됨 (2026-05-30P 확인). **단 데이터는 살아있음**: 보유 중인 `★ 4QFY23FactsheetKOR.xlsx`에 1Q~4Q 분기 컬럼 물리적 존재 → parser stage에서 구판 시트 레이아웃(`parse_factsheet`가 "월초대비 신계약CSM 배수" 라벨 못 찾음) 핸들링하면 복구 가능. **다운로더 액션 없음** — parser stage 이슈로 이관 |
| ~~NONLIFE-Q123~~ | ~~손보 6사 분기(Q1-Q3) 경영공시 — 회사 자체사이트 스크래퍼~~ | ✅ **2026-06-01 완료** | 34셀 중 **26셀 backfill 수집**(AIG 9 / 악사 4 / 신한EZ 4 / 코리안리 6 / 카카오 3), **8셀(서울보증)은 구조적 미발행** 판정. 사별 스크립트 `scripts/backfill_q123_<token>.py` (aig/axa/shinhanez/sgi/koreanre/kakaopay). 검증: 무결성 2,041/2,041 OK + audit disclosure REAL GAPS 0. ⚠️ AIG/신한EZ/카카오 Q2 = 반기 누적(위 핸드오프 주의 참조). 서울보증 = 자체사이트 연간+최신분기만 보존(audit `SGI_QUARTERLY_STRUCTURAL` 예외 등록) |
| ~~HEUNGKUK-CALL-FIX~~ | ~~흥국화재 신종자본증권1 콜 미행사 override~~ | ✅ **2026-06-17 완료** | normalize.py `_CALL_NOT_EXERCISED={"KR60005416C3"}` 추가 → 재실행 → KR0005 신종 3,200→**4,120억** (FS appendix 일치). normalize `20260616T153258Z`. provenance 재발행 |
| ~~CAPSEC-DART-FETCH~~ | ~~자본성증권 in-force per-bond DART fetch (KDB생명·농협생명)~~ | ✅ **2026-06-16 완료** | FSC 0→DART B-type 조사→KDB 2건(2,410억)+농협 2건(5,000억). 교보=미발행. 현대해상=FSC 정확(parser오류). `data/bonds/disclosure/2026q1_capital_securities.json`. `inbox/publishing/20260616T1300Z` |
| ~~PROVENANCE-BONDS~~ | ~~bonds provenance 사이드카 emission (Phase 2)~~ | ✅ **2026-06-16 완료** | `bonds_provenance.json`(24사) + `disclosure_bonds_provenance.json`(2사). as_of=2026-03-31, effective_filtered=true. `scripts/emit_bonds_provenance.py` |
| ~~CSM-CONTINUITY~~ | ~~CSM 워터폴 연속성(기말≠기시) 복구 raw~~ | ✅ **2026-06-16 완료** | owner: 2026.1Q 기시 전사 misparse(`FY2026_Q1` git-purge로 0 dirs). **우선 5사 2026.1Q**(교보·메리츠·신한라이프·에이비엘·푸본) + `validate_csm_continuity` break(코리안리 23.4Q→24.1Q 경계 + FY2023 드리프트 현대·에이비엘·KDB·교보 + FY2024 KB라이프·코리안리)→ **FY2023/FY2024 Q1-Q4 동반 = 33/33 fetched**, CSM블록 결손 0. break는 24.4Q/25.1Q 아니었음. parser raw-ready `inbox/parser/20260616T0640Z`. ⚠️rebuild은 복원분+기존 raw 범위 |
| ~~CAPSEC-VERIFY~~ | ~~자본성증권 발행현황 검증·수정 (owner 0506Z #2)~~ | ✅ **2026-06-16 완료** | registry **bare-stem alias 오수집** 발견·수정(메리츠/아이엠/미래에셋/카카오 → 계열사 채권 오태깅, 메리츠 1.77→19.6조 폭증). 4 alias 제거(`{nonlife,life}_insurer_registry.yaml`). 재크롤 clean(normalized `20260616T060817Z`): 22/24 live 동일, 🔴KR1098 카카오페이 3,202억→0(가짜), 🟢KR0099 KB라이프 0→1,200억(누락분), KR0011 −890(정상). big-3 Face 정확→owner T2 BS −11.6%는 parser BS시가측 추정. parser-kics `inbox/parser/20260616T0615Z`. ⚠️tier 재빌드는 publishing/parser gate |
| ~~NBCSM-INTERIM~~ | ~~NB CSM 시계열 오염 복구용 interim DART raw~~ | ✅ **2026-06-16 완료** | parser/ifrs17 발주(validation partial-extract 오염). git-purge로 부재한 반기/분기보고서 raw를 `ifrs17_batch_historical.py --skip-extract`로 **10사×{2025.2Q,2025.3Q,2023.1Q}=30셀 fetch-only 재취득**(30/30). CSM 블록 29/30 존재(우선 7셀 OK, 롯데 2025.2Q NB=0 최악건 포함). 🔴 honest gap: 롯데 2023.1Q CSM표 부재(도입초 축약, census whitelist). parser raw-ready `inbox/parser/20260616T0420Z`. ⚠️마스터 rebuild은 raw 전체복원 세션에서 |
| ~~KR0004-MG-DART~~ | ~~예별손해(구 MG=엠지) DART 감사보고서~~ | ✅ **2026-06-16 완료** | KR0004는 비상장 → DART 정기보고서 0 = universe 부재(통째로 0이었음). 외부감사 감사보고서(F)는 존재 = DART entity '엠지손해보험'(corp `00962861`). **별도·FY2023~ 3건 적재**(owner 스코프; FY2022 IFRS4·연결 제외). `data/dart/FY{Y}_Q4/raw/KR0004_엠지손해보험_<rcept>/`(00760 별도). IFRS17 주석 확인(보험계약마진 36~59). `scripts/fetch_kr0004_mg_dart_audit.py`. parser/ifrs17 raw-ready `inbox/parser/20260616T0210Z` |
| ~~KR0004-MG-HISTORY~~ | ~~예별손해(구 MG) 과거 11분기 K-ICS 공시~~ | ✅ **2026-06-16 완료** | parser bounce(round3 K2): KR0004가 26.1Q만 적재, 그 이전=구 MG 명의. 2023.1Q~2025.3Q **11분기 전수 fetch(11/11 OK)** from `yebyeol.co.kr`(예별=구 MG 동일 법인, 2013~ 전 분기 아카이브). 결산 ZIP 본문="엠지손해보험" 확인. text-layer OK(OCR 불필요). `scripts/backfill_kr0004_mg_quarters.py`. KR0004=2023.1Q~2026.1Q 13분기 연속 확보. parser raw-ready `inbox/parser/20260616T0145Z` |
| ~~SEOULBO-DART~~ | ~~서울보증 DART 8셀~~ | ✅ **2026-06-01 drop (won't-fix)** | 사용자 결정("서울보증 걍 버려"). 미상장(IPO 철회) → DART 분기/반기/사업보고서 미공시 = 구조적. audit `DART_DROP`에 등록 → 전 source REAL GAPS 0 |
| ~~IR-DONGYANG-401~~ | 동양생명 IR factbook (myangel) 401 — disclosure로 부분 해결 | 🟢 low | **2026-05-30R: 사용자 지적으로 생보협회 경영공시(pub.insure.or.kr)로 대체 → disclosure 13/13 완성** (`download_dongyang_disclosure_q4.py`로 FY2023_Q4·FY2024_Q4 결산 2개 받아 채움). 동양생명 검증 데이터는 disclosure(IFRS17 주석 포함)로 확보됨. IR factbook(myangel) 자체는 여전히 401 차단 — **IR factbook 전용 지표(CSM배수 등)가 disclosure에 없어 별도로 필요할 때만** 재시도: (a) non-headless+다른IP로 raon ozvid auth header 캡처 (b) DART 본문 fallback. 현재는 low priority |

**전략적 시너지 (코리안리 리포트 인과 체인 재현):**
- F8 (설계사정착률) + F8 (채널별 불완전판매비율) + 37회차 해지율 (별도 source)
- = "GA 채널 → 해지율 → 손해율" 인과 체인을 공시 데이터만으로 재현
- → insurequant 프리미엄 기능 후보

---

## User decisions (downloader-scoped)

| # | Decision | Date |
|---|----------|------|
| D5 | API keys: repo root `.env` only (gitignored). `OPENDART_API_KEY` / `DATA_GO_KR_BOND_ISSUANCE_KEY` / `DATA_GO_KR_BOND_REDE_KEY`. Never commit/log key values. **2026-08-03: `bonds` source retired (`inbox/downloader/20260803T0057Z`) — the two `DATA_GO_KR_BOND_*` keys are kept as-is (not deleted) since F9 (`source-catalog.yaml` future_sources_planned, same data.go.kr portal) may reuse them.** | 2026-05-24 |
| D6 | Bond Call rule: issue + 5y for ALL bonds (Korean market convention; ignore "콜" keyword gate). Past 5y = assume `called` (de facto mandatory per thebell/흥국 cases) | 2026-05-24 |
| DL-FYR | **Next quarter onwards (2026.2Q+)**: find URLs / XPaths yourself. 2026.1Q only was user-provided. Reuse existing configs, swap only period-specific labels. Escalate to user only if site structure fully changed | 2026-05-30 |
| DL-NOATTACH | **Don't fetch DART attachments (별첨/감사보고서 zip).** Body XML has all IFRS17 disclosures. Verified 2026-05-30 (한화 647 / KB 259 / 농협생명 176 / 라이나 audit 55 / AIG audit 55 occurrences of `보험계약마진` in body) | 2026-05-30 |
| DL-NOTSKIP | KR0029 AIG + KR0150 SGI **K-ICS skip** (no PDF on their own sites), BUT **DART**에서는 받을 수 있는 만큼 받음 (AIG = "에이아이지손해보험" corp_code 00983606 / SGI = 2024.4Q 이후 분기보고서 시작) | 2026-05-30 |
| DL-DART-C-FY23 | bucket C 빈 dir 121건 분류: 110 = 비상장 11사 Q1-3 (DART 분기보고서 구조적 미제출, gap 아님) + 11 = 비상장 11사 **FY2023_Q4 감사보고서 = 받지 않음** (사용자 결정 2026-06-03, "비상장사 감사보고서 불필요" 유지). → 비상장사 DART PL/CSM 시계열 = **FY2024_Q4 + FY2025_Q4 2포인트로 확정** (extract_dart_zips로 추출 완료). 다음 세션 재제기 금지 | 2026-06-03 |
| DL-2022Q4-HOLD | 법정준비금 항목5-8용 2022.4Q 본문 XML 24사 = **보류, 지금 안 받음**. 항목5(해약환급금준비금)는 소급가정치뿐이라 항목6·7(비상위험·대손준비금) 실측만 목적이면 받을 값어치 있었으나, 재요청 전까지 미착수(`inbox/downloader/20260819T0820Z` 발주 E) | 2026-08-19 |

---

## Done — recent (one-liners; detail in changelog / data manifests)

| ID | Task | Done |
|----|------|------|
| SENS-FY25 | IFRS17 CSM 민감도 FY2025 사업/감사보고서 raw 28사 전수 적재 (FY2024 고정 해소) — DART 회사명검색, `data/dart/FY2025_Q4/raw/`, 28/28 공시·실패0, KR prefix 통일. 추출(sensitivity)은 parser/ifrs17로 라우팅(`inbox/parser/20260615T0520Z`) | 2026-06-15 |
| G8 | NB CSM배수 25.4Q 누락 3사 FY2025 감사보고서 raw 복원 (AIG/카카오페이손해/하나생명) — 라이브 DART 재취득 + `KR0029_` prefix 정정 + IFRS17 키워드 검증. 추출 교정(magnitude misparse + 하나생명 audit-annual)은 parser/ifrs17로 라우팅(`inbox/parser/20260614T1330Z`). 단순 refetch 아님 = 파서 추출 이슈로 확정 | 2026-06-14 |
| F2 | KIDI ML01/MN07 NB CSM crawler (38사×13Q=494, premium_summary.json) | 2026-05-30 |
| DL-FY26Q1 | FY2026.1Q full ingest (손보17+생보22+IR13+DART) | 2026-05-30 |
| DL-DART-AUDIT | DART raw 100% audit + gap fill (`_inventory_manifest.json`) | 2026-05-30 |
| MISC-BOND | FSC bond issuance+Call ingest → per-ISIN calendar (tier1 63 + tier2 261) | 2026-05-25 |
| IFRS-HIST | Historical 13Q ingest 2023.1Q~2026.1Q (`ifrs17_batch_historical.py`) | done |
| DL-COMPLETE | 5-source 완결: 전수 audit + disclosure 28셀 backfill (gap 73→34) | 2026-05-31 |
| DL-ARCHIVE-PROBES | Archived 45 early IR auto-discovery probes (`scripts/_probes/`) → `data/_archive/20260602T150745Z_downloader_ir_probes/` (git rename, kept for foreign-insurer ref). Canonical `crawl_ir_*.py` untouched | 2026-06-02 |
| DL-DART-EXTRACT | Fixed parser `raw_not_extracted`: 42 insurer DART dirs had `document.zip` but no body XML (fetch-only + foreign filings have only `_00760`/`_00761` members, no main xml). New idempotent `scripts/extract_dart_zips.py` extracted them in-place; bucket A 40→0. Parser auto-picks via `*.xml` glob | 2026-06-03 |

---

## Reading order for downloader subagent

When invoked, read in this order:

1. This file (`TODO_downloader.md`) — current state and documented exceptions
2. `docs/agents/claude-agent-downloader.md` — master prompt (mission + 5 sources catalog + canonical layout)
3. `docs/agents/source-catalog.yaml` — machine-readable URL/XPath catalog
4. `data/dart/_inventory_manifest.json` — DART coverage; avoid re-fetching
5. `data/disclosure/_meta/FY*/_manifest.json` — per-period manifests
6. `data/ir/_*.json` — IR manifests (`_db_manifest.json`, `_db_decks_manifest.json`, `_hyundai_manifest.json`, `_kr_map.json`)

Deferred (2026-07-27): `docs/changelog_downloader.md` is history — open it only when you need the background of a past decision; most sessions don't. For cross-stage context, see root `TODO.md`.

---

NOTE: English only where Korean encoding is fragile. Korean content preserved here is read-only history; new entries prefer English. See `CLAUDE.md` "Document/TODO Encoding Rule".
