---
from: orchestrator
to: downloader
created: 20260830T0400Z
status: resolved
route: refetch
company: MULTI
period: 2026.2Q
iter: 3
---

## 미결 (orchestrator 작성 — owner 지적)

**생보 22사를 협회 일괄페이지만 보고 "0/22 미게시" 로 판정한 것이 방법론 구멍이다.
사별 사이트를 직접 훑어라.**

owner 지적: *"생보사는 생보협회 말고 사별 사이트에 올린 데가 한 회사쯤은 있을 것 같은데."*
타당하다 — **회사가 자기 사이트에 먼저 올리면 협회 페이지가 갱신되기 전에는 안 보인다.**
`docs/changelog_downloader.md` 2026-08-29 스윕은 `pub.insure.or.kr` 그리드의 2분기 셀만
읽었다(22/22 `-`). 그건 "협회에 안 올라왔다" 이지 "회사가 안 냈다" 가 아니다.

### 같이 확정할 것 — 코리안리

08-29 스윕이 코리안리(KR1000)를 "서버 다운으로 미확인" 으로 남겼다. **owner 가 직접 확인해
미게시로 확정했다(2026-08-30).** 기록에 반영해라. 이제 손보 17사는 전원 판정 완료다.

### 선례가 있다 — 그대로 쓰면 된다

`docs/changelog_downloader.md` 2026-08-21 항목(흥국생명 KR0071)에 자사 사이트 경로와
접근 함정이 이미 기록돼 있다.

```
경로 예:  heungkuklife.co.kr/front/public/manageList.do   (경영공시 목록)
함정:    직접 URL 진입(특히 www. 없이, 또는 첫 headless goto)에 "현재 잘못된 접근경로" 반환.
         메뉴 클릭 흐름(session/referer)을 요구한다. www. prefix + 홈 방문 후 진입으로 우회.
```

**이 함정은 흥국생명만의 것이 아닐 개연성이 높다.** 국내 금융사 사이트가 흔히 쓰는 패턴이라
다른 회사에서도 같은 증상이 나오면 같은 우회를 먼저 시도해라.

### 요청

1. **생보 22사의 자사 경영공시 페이지를 찾아 2026년 상반기/2분기 게시 여부를 확인해라.**
   대상: DB생명 · IBK연금 · KB라이프 · 교보라이프플래닛 · 교보생명 · 농협생명 · 동양생명 ·
   라이나생명 · 메트라이프 · 미래에셋생명 · BNP파리바카디프 · 삼성생명 · 신한라이프 ·
   아이엠라이프 · ABL생명 · AIA생명 · 처브라이프 · KDB생명 · 푸본현대 · 하나생명 · 한화생명 ·
   흥국생명.
2. **08-29 스윕에서 쓴 "다운로드 전 listing 라벨 전량 덤프 → 4-값 판정"(`scripts/_probes/
   census_q2_disclosure_listings.py`)을 그대로 써라.** 그때 잡은 함정 4종(연도가 다른 `<td>`,
   두 자리 연도 `FY 26`, 접근성 배너 날짜의 거짓 posted, 미관측 vs 미게시 분리)이 자사
   사이트에서도 나온다.
3. **미관측을 미게시로 세지 마라.** 접근 실패·서버 다운은 `not_observed` 로 따로 센다.
   08-29 에 코리안리를 그렇게 처리한 것이 옳았다.
4. **받은 게 있으면 내용으로 검증해라.** 파일명·응답코드 금지. 하나손보 때 XPath `tr[1]` 이
   Q1 과 SHA256 동일한 파일을 반환한 전례가 있다(그 사이트는 1분기를 2분기 위에 나열).
   기간 마커(`2026. 1. 1 ~ 2026. 6. 30`)와 Q1 마커 0건을 확인해라.
5. 받은 게 있으면 `data/disclosure/FY2026_Q2/pdf/` 와 게이트가 걷는 `raw/` 양쪽에 설치하고
   `inbox/parser/` 에 `lane: kics` raw-ready 통지. **docling 변환은 하지 마라 — parser 소관.**
6. **경로를 재사용 가능하게 남겨라.** 회사별 URL·셀렉터·접근 함정을 `docs/agents/source-catalog.yaml`
   또는 전용 스크립트에 적어라. 8/31 재확인과 다음 분기에 그대로 쓴다.

### 참고 — 현재 상태

```
2026.2Q 게시 확정:  하나손해보험 1사 (파싱·검증 완료, 마스터 삽입은 39사 중 1사라 보류)
손보 미게시 확정:   16사 (+ 코리안리 owner 확인으로 17사 전원 판정 완료)
생보:              협회 기준 22/22 미게시 — 자사 사이트 미확인  <- 이 티켓
다음 정기 확인:     8/31(월). 주말 게시 0회 규칙상 그 창의 유일한 영업일
```

### 하지 말 것

- URL 을 owner 에게 묻지 마라. 2026.1Q 만 owner 제공이고 그 다음부터는 직접 찾는 것이 계약이다.
- PDF→MD 변환(docling) 금지 — parser 소관.
- 마스터 JSON·xlsx 금지. `index.html` 등 HTML 금지.
- 브랜치 변경 금지(현재 `fix/csm-product-segmented-columns`). `git push` 금지. `git add -A` 금지.

## 답변 (recipient 작성 — 처리 후)

**처리 완료 (downloader, 2026-08-30). 지적이 옳았다 — 방법론 구멍을 메웠다. 다만 결과는
0건이다: 생보 22사 자사 사이트도 전원 미게시.** 경로자산은 22사 전부 확보했다.

### 1. 22사 판정 — posted 0 / not_posted 22 / not_observed 0 / unreachable 0

**근거의 질이 달라졌다.** 08-29 의 "협회 그리드가 `-`" 가 아니라, **각 사 자사 목록에서 그
회사의 2026 1분기 행을 실제로 읽어낸 뒤** 2분기 행 부재를 확인했다. 즉 양성대조가 성립한다 —
"탐지기가 아무것도 못 보는 상태" 가 아니라 "볼 수 있는데 2분기가 없다". 같은 날 협회 그리드도
재확인(기준년 2026, 22사, 1분기=22 다운로드, 2분기=0) — 두 독립 경로 일치.

| KR | 회사 | 판정 | 자사 목록 URL | 그 사이트가 보여준 최신 행 |
|---|---|---|---|---|
| KR0068 | 한화생명 | not_posted | `hanwhalife.com/main/disclosure/management/occasionalmanagement/DF_MDRM000_P10000.do` | 2026년 1분기 정기경영공시 |
| KR0069 | 삼성생명 | not_posted | `samsunglife.com/individual/products/disclosure/management/PDO-MAMAP010100M` | 2026년 회계연도(1분기) |
| KR0070 | ABL생명 | not_posted | `abllife.co.kr/st/pban/admPban/fprdPban/2026` | [2026년 1분기 정기경영공시] |
| KR0071 | 흥국생명 | not_posted | `heungkuklife.co.kr/front/public/manageList.do` | FY2026 1분기 경영공시 (2026.05.29) |
| KR0072 | KDB생명 | not_posted | `kdblife.co.kr/ajax.do?scrId=HDLMA001M03P` | FY 2026년 1/4분기 경영공시 (#30) |
| KR0073 | 교보생명 | not_posted | `kyobo.com/dgt/web/notice-management/fixed-term/last-year` | 2026년 1분기 (select 옵션 1개뿐) |
| KR0074 | 라이나생명 | not_posted | `lina.co.kr/disclosure/management-public-announcement/regular-announcement` | FY2026 1Q 경영공시 |
| KR0075 | BNP파리바카디프 | not_posted | `cardif.co.kr/disclosure/papam001.do` | FY2026 Q1 정기 경영공시 |
| KR0076 | 아이엠라이프 | not_posted | `imlifeins.co.kr/BA/BA_F010.do` | 연도x분기 표: 2026 행 1/4분기만 채움 |
| KR0079 | 미래에셋생명 | not_posted | `life.miraeasset.com/micro/disclosure/management/PC-HO-082000-000000.do` | FY 2026년 1/4 분기 |
| KR0082 | DB생명 | not_posted | `idblife.com/notice/business/fxpd_mgm_pban` | 2026년 1분기 DB생명보험회사의 현황 |
| KR0083 | 푸본현대생명 | not_posted | `fubonhyundai.com` + `goMenu('CUSI150413010000')` | FY2026 1/4분기 현황 |
| KR0087 | 동양생명 | not_posted | `pbano.myangel.co.kr/notice/product/WE_PA_AP_01_00_00.jsp` → 경영공시 → 정기경영공시 | FY2026 1분기 정기공시 (2026.05) |
| KR0094 | 신한라이프 | not_posted | `shinhanlife.co.kr/hp/cdhi0310.do` → 정기경영공시 | 2026.01~2026.03 2026년 1분기 |
| KR0095 | 메트라이프 | not_posted | `brand.metlife.co.kr/pn/fxtrmMnnt/retrieveFxtrmMnntMain.do` | 2026년 1분기 주요경영현황 |
| KR0097 | 하나생명 | not_posted | `hanalife.co.kr/home/publicAnn/listPublicAnn.do?gubun=F` | (하나생명) 2026년 1분기 경영공시자료 |
| KR0099 | KB라이프 | not_posted | `kblife.co.kr/customer-common/managementPublicNoticeOffice.do` | 2026년 1분기 경영통일공시 (2026.05.29) |
| KR0100 | 처브라이프 | not_posted | `chubblife.co.kr/front/official/management/list.do` | FY2026 1/4분기 경영공시 |
| KR0104 | 농협생명 | not_posted | `nhlife.co.kr/ho/on/HOON0001M00.nhl` | 2026년 1/4분기 경영공시 |
| KR1010 | 교보라이프플래닛 | not_posted | `lifeplanet.co.kr/disclosure/admi/HPDC21S0.dev` | 2026년 1/4분기 …의 현황 |
| KR1011 | IBK연금 | not_posted | `ibki.co.kr/process/HP_PBANO_MGMT_FIXTERM_LIST` | 2026년 1/4분기 경영공시 |
| KR0080 | AIA생명 | not_posted | `aia.co.kr/ko/disclosure/management-information/regular.html` | 2026년 1분기 결산 경영공시 |

**코리안리(KR1000) 반영 완료.** `data/disclosure/_meta/FY2026_Q2/listing_census.json` 의 KR1000 에
`verdict=not_posted` + `verdict_source=owner_manual_check` + `verdict_source_date=2026-08-30` 를
넣고, 우리 프로브가 관측한 값은 `probe_verdict=unreachable` 로 **따로** 남겼다(우리가 본 것과
owner 가 확인한 것을 섞지 않기 위해). census 병합 규칙상 나중에 unreachable 로 재프로브해도
이 값은 안 덮인다. **→ 손보 17사 전원 판정 완료. 39사 전체 = 1 게시(하나손보) + 38 미게시,
미관측 0.**

### 2. 접근 함정과 우회

**흥국생명 패턴(`www.` + 홈 먼저)은 실제로 일반적이라 22사 전원에 기본 적용했다**
(`home_first`). 다만 이번에 드러난 더 큰 장벽은 그게 아니라 **딥링크 자체가 없는 사이트**였다.

- **JS 메뉴만 있는 곳** (동양·라이나·신한라이프·KDB·삼성·iM라이프): `href="javascript:void(0)"`
  이거나 아예 없다. **Playwright 의 actionability 대기가 접힌 드롭다운 항목에서 매번
  타임아웃** → 페이지 안에서 `element.click()` 을 직접 디스패치하는 경로를 넣었다(숨어 있어도
  onclick 은 돈다).
- **그래도 안 되면 라우트를 원본에서 캐냈다.**
  - 삼성생명: `/gw/api/display/menu/all`(메뉴 API)에서 `정기 경영공시` 의 `linkTo` 를 읽어
    `PDO-MAMA**P**010100M` 확정. 기존에 검색으로 잡았던 `PDO-MAMAA010100M` 은 **안내
    페이지**였다(수시는 `...N...`, 한 글자 차이). Vue SPA라 **어떤 경로든 200 + 동일한 3.6KB
    껍데기**를 주므로 응답코드로는 아무것도 판단 못 한다.
  - 라이나: LNB 에 href 가 없어 Nuxt 청크를 grep →
    `/disclosure/management-public-announcement/regular-announcement`.
    잘못된 slug 는 HTTP 500, 맞는 slug 는 200 이라 이게 탐침이 된다.
  - KDB: 홈 메뉴가 `javascript:_KDB_.fn_link('/ajax.do?scrId=...')` → `/ajax.do?scrId=HDLMA001M03P`
    로 직접 진입(`/scrId/<id>.do` 형태는 빈 페이지).
- **교보생명은 URL 이 반직관적**: 현행 정기경영공시가 `.../notice-management/fixed-term/**last-year**`
  이고 `.../fixed-term` 은 404. 기간이 `<select>` 옵션이고 **페이지 `<title>` 이 선택 기간을
  그대로 담는다**(`2026년 1분기-정기경영공시-교보생명`).
- **동양생명 공시는 별도 서브도메인** `pbano.myangel.co.kr`. `www.myangel.co.kr/paging/WE_AC_*`
  는 `/comm/notFound` 로 떨어진다.
- **푸본현대**는 전 화면이 `goMenu('<CODE>')`, 경영공시실 = `CUSI150413010000`.
- **IBK연금**은 헤드리스보다 평범한 `requests` 가 잘 통한다(정적 폴백이 받아냄).
- **농협생명**은 정기 점검창이 있다 — 점검 페이지는 `not_observed` 로 떨어뜨리게 해 뒀다.

### 3. 내용 검증 — 해당 없음

**받은 파일이 0개다.** 22사 전원 미게시라 `data/disclosure/FY2026_Q2/` 에 추가된 파일이 없고,
따라서 기간 마커(`2026. 1. 1 ~ 2026. 6. 30`)/Q1 마커 검사 대상 자체가 없다.
`inbox/parser/` 통지 없음, docling 변환 없음.

**대신 탐지기 자체를 검증했다.** 22사 라벨 방언을 전부 Q2 로 바꾼 **양성대조 21건**(+ 손보
2종)과 **음성대조 7건**을 `--selftest` 로 상설화했다: 현재 **21/21 탐지, 오탐 0/7, 표 판독 OK**.
"0건" 이라는 보고는 탐지기가 볼 수 있다는 증명이 붙어야 의미가 있다.

### 4. 남긴 경로자산 (이 티켓의 절반)

| 위치 | 내용 |
|---|---|
| `scripts/_probes/census_q2_life_own_sites.py` | **운영 정본.** `LIFE_SITES` 22사 = home·url·click_path·js_eval_first·회사별 함정 note. 모드 4개: 기본 census / `--discover`(홈+착지 페이지의 공시 링크 덤프) / `--rescan`(저장된 덤프로 네트워크 없이 재판정) / `--selftest`(양성·음성 대조). 08-29 프로브를 **import** 해 쓴다(정규식 복제 없음) |
| `docs/agents/source-catalog.yaml` → `disclosure_life_own_sites` | 사람이 읽는 색인. 22 entries + `access_trap` + `label_dialects` + 회사별 `verified_2026_08_30` |
| `data/disclosure/_meta/FY2026_Q2/life_own_site_census.json` | 22사 4-값 판정 + 근거 라벨 + 표 판독값 |
| `data/disclosure/_meta/FY2026_Q2/life_KR####_listing_labels.txt` | 22사 라벨 전량 덤프(재실행 없이 판정 감사 가능) |
| `data/disclosure/_meta/FY2026_Q2/listing_census.json` | 손보 17사 + 협회 일괄. KR1000 owner 확정 반영 |

**추가로 막은 함정 5종**(4종은 조용히 틀린 판정을 낸다 — 상세는 changelog 2026-08-30):
⑤ 상시 네비 메뉴가 "관측됨" 을 만족시켜 **6개사가 자기 홈페이지에 선 채로 `not_posted`** 를
받았다 → 판정에 **연도 붙은 기간 행** 요구 ⑥ 수시공시 등록일 `2026.06.30` 이 기간 라벨로 읽혀
**KB라이프 거짓 `posted`** → Q2 히트는 기간을 이름으로 불러야 함 ⑦ `2026년 회계연도(1분기)`
(삼성생명) 연도-분기 사이 글자 삽입 → 간격 14자 허용하되 **사이에 숫자 금지** ⑧ `FY2026 1Q`
(라이나)·`FY2026 Q1`(BNP) → 세 어순 커버 ⑨ **연도x분기 표**(iM라이프) → **칸을 직접 읽음**.

### 5. 다음 확인

**2026-08-31(월)** 유지. 이번 실측이 근거를 하나 더 보탠다 — 흥국생명은 2025년 2분기를
**2025-08-29(금)**, 즉 마감 직전 영업일에 올렸다. 실행 순서:

```
1) python scripts/_probes/census_q2_life_own_sites.py           # 생보 22사 자사
2) python scripts/_probes/census_q2_disclosure_listings.py      # 손보 17사 + 협회 일괄
3) posted 인 회사만 다운로드 -> verify_q2_disclosure_content.py  # 내용검증(파일명/응답코드 금지)
```

(python 은 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe` 풀패스)
