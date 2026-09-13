# jp 레인 — 일본 보험사 ESR 도메인 문서 (정본, 2026-09-12 신설)

jp 레인은 **한국 stage 프롬프트를 읽지 않는다.** 이 문서 + `TODO_jp.md` + `inbox/jp/` + 루트 `CLAUDE.md` 만 읽는다.
에이전트 정의는 `.claude/agents/jp-collector.md`(머신 로컬, push 안 됨 — 새 머신이면 이 문서로 다시 만든다).

## 1. 무엇을 모으나

- 대상: `J-ESR/jp_insurers.csv` 81행(완전 중복 2행 포함, 실질 79사 = 생보 45·손보 33·재보험 2·미분류 1). 열: `company_jp, company_en, ticker, sector, category, edinet_code, edinet_eligible, parent_group, ir_url, ir_health_url, notes`.
- 지표: **ESR(경제가치 기준 지급여력비율, %)** 1종 + 구성요소(적격자본·소요자본, 억엔) + 기준일 + 연결/단체 구분. 지금은 헤드라인 1종만 화면에 쓴다.
- 산출: `J-ESR/fy2025_esr_census_<YYYYMMDD>.csv`(census, 14열) → `J-ESR/build_jesr_page_json.py` → `J-ESR/jesr_master.json` + 배포용 `jp/jesr_esr.json`(바이트 동일). 화면은 `jp/index.html`(designer 소관).

## 2. 제도·주기 (한국과 다른 점 — 이걸 몰라서 생기는 오판이 대부분)

- 회계연도 4월~3월. FY2025 = 2026-03-31 기준. 첫 의무 ESR 사이클이 FY2025 말이다.
- **정본은 회사별 공시 사이트의 PDF**(결산설명자료·디스클로저지·별책). EDINET(전자공시) XBRL 은 보조 — FY2024 XBRL 6사 probe 에서 ESR 구성요소 0건(`inbox/_resolved/20260624T0337Z__owner__JP_MULTI__jesr_datalayer_asof.md`). 상장사 교차확인용으로만. **2026-09-13 키 확보 후 실측: 태그는 여전히 없지만 有報 본문에는 ESR 이 서술로 있고, 대상은 최대 17사다 — §4d.**
- 본문 디스클로저는 대부분 7월 말에 나오지만 **신기준 비율은 "2026년 10월 말 공표 예정" 으로 미루는 회사가 다수**(09-12 census: 손보 원문 13건 중 11건 명시). 최종 기한 2026-10-31. → 9월엔 분모(페이지 존재)와 일부 값, 10월 말에 전수 값.
- 단위 억엔(億円). 비율은 % 한 자리.
- 지주 상장 6사(Tokio Marine·MS&AD·Sompo·T&D·Sony FG·Dai-ichi)는 **그룹 연결값**을 결산설명자료에 먼저 낸다(5월). 자회사 단체값은 별도 — 둘을 `scope=group|solo` 로 반드시 구분해 적는다. 상호회사 5사(Nippon·Sumitomo·Meiji Yasuda·Fukoku·Asahi)는 비상장·EDINET 비대상, IR PDF 만.
- 속보/잠정(速報·暫定) 표기가 붙은 값은 `preliminary=true`. 확정치가 나오면 갈아끼운다(같은 as_of).

## 3. 라벨 변형 (원문 검색 키)

`ESR` · `経済価値ベースのソルベンシー比率` · `ソルベンシー・マージン比率（新基準）`(신기준 표에서는 옛 이름을 그대로 쓰는 회사가 많다 — 표 안에 `所要資本`·`適格資本`·`UFR`·민감도(株式 10%下落 등)가 같이 있으면 신기준) · `適格自己資本` · `所要資本の額` · 미공표 문구 `後日公表予定` / `2026年10月末に公表予定`.
구기준 `ソルベンシー・マージン比率` 단독(분모가 リスクの合計額 ×1/2)은 **ESR 이 아니다** — 옛 지표. 두 표가 같은 PDF 에 나란히 있는 경우가 흔하다.

**규제 양식(告示 74호·75호) 표 골격·항목 id·검산식·회사별 편차는 `docs/domains/jp_esr_disclosure_template.md` 가 정본**(2026-09-12, 표본 3건으로 해부). 10월 census 확장 열 이름은 그 문서/`J-ESR/esr_disclosure_schema.json` 의 id 를 그대로 쓴다.
**소요자본 합산(상관행렬·오퍼리스크 선형가산·세효과 80%)은 `J-ESR/esr_aggregation_rules.json` 이 기계본**(告示74 원문 `J-ESR/raw/regulation/`, 같은 문서 §8). 하위 리스크가 공시된 회사는 `extract_esr_template_samples.py` 의 G01~G10 으로 √(xᵀRx) 재현을 돌려 부모≤Σ하위 부등식이 아니라 **등식**으로 검산한다. 내부모형사·다지역 손보사는 하위 재현이 안 되는 것이 정상(§8-4).

## 4. 처리 규칙

- 판정값은 `posted / not_yet / not_found` 셋뿐. `posted` 는 값이 들어 있는 문서 URL 을 **실제로 열어** 확인한 경우만. 패턴 추정으로 판정했으면 notes 에 그렇게 적는다(다음 라운드 재확인 대상).
- 브라우저 도구 금지. `curl`/`requests`/WebFetch/WebSearch 만. 요청당 timeout 20초, 회사당 실패 3회면 `not_found` + 사유. 이 PC 는 시간대별로 curl 이 막혔다 풀린다(WebFetch 는 대체로 됨).
- 회사 단위 통째 제외 금지. 못 찾은 회사는 행을 남기고 사유를 적는다.
- 10개 회사마다 census csv 를 디스크에 저장(중단 대비). `jp_insurers.csv` 는 병렬 에이전트가 직접 고치지 않는다(오케스트레이터가 census 에서 병합).
- 보고문(사용자에게 가는 글)에는 **일본어 문자를 넣지 않는다**(회사명은 `company_en`). 원문 인용이 필요하면 티켓 답변란에만.
- `J-ESR/build_jesr_page_json.py` 의 self-check(15사·100~1000%·https·as_of 일치·census 합계)가 이 레인의 게이트다. 라이브 연결 후 확장.

## 4b. 10월 말 재census 부터는 3축도 같이 뽑는다 (owner 2026-09-12 확정)

owner 가 2026-09-01 에 공유한 기사(insnews #92437, 일본 금융청 '2026년 보험 모니터링 보고서')의 취지는 ESR 비율 자체가 아니라
그 뒤의 위험 구조다. **ESR 만 보고 넘어가는 게 기본 습관이 되지 않도록 이 절을 먼저 읽는다.**

1. **자산집약형 재보험(AIR, Asset-Intensive Reinsurance) 활용** — 생보 절반가량(주로 외국계·상장사)이 활용, 목적에 "ESR 개선" 이 명시되는
   경우가 많다. 금융청은 재보험사 신용위험 + 자산/지역/재보험사 집중위험을 경고한다. → census 열 `air_used`: 결산설명자료·유가증권보고서의
   **리스크관리(リスク管理) 파트**에서 "再保険"·"アセット・インテンシブ" 언급과 목적 서술을 찾는다. ESR 계산 표 안이 아니라 다른 섹션이다.
2. **손보 이상위험준비금(異常危険準備金, 화재보험) 적립 부족** — 2025-03말 기준 28사 중 12사 부족 확인된 바 있다. → census 열
   `catastrophe_reserve_adequacy`: 손보만 해당(생보는 해당없음으로 남긴다), 적립률/부족 여부 서술을 찾는다.
3. **생보 이익구조 전환** — 이차손익(利差損益)이 금리상승으로 역마진→이익 전환 중, 예정이율 인상 확산. → census 열
   `interest_margin_sign`: 생보 위주, "역마진"·"逆ざや" 해소 서술이나 이차손익 부호를 적는다.
   **2026-09-12 이후 三利源(利差·危険差·費差)·基礎利益·当期純利益 등 손익 항목은 스키마 `layer:"profit"`(`jp_esr_disclosure_template.md` §9) 로 뽑는다** —
   三利源 공시사는 `pl_interest_margin` 부호가 `interest_margin_sign` 의 정본이고, 없는 회사만 逆ざや 서술로 판정한다. 같은 층에 `accounting_basis`/`ifrs17_applied`(회계기준, 추정 금지) 메타가 있다.

3열 다 ESR 표와 **같은 PDF, 다른 섹션**에 있다 — 회사당 문서를 다시 열 필요는 없지만 훑는 페이지 수는 늘어난다. 화면(`/jp/`) 반영 여부는
이 데이터가 얼마나 뽑히는지 본 뒤 owner 에게 다시 묻는다(즉시 화면에 얹지 않는다).

5. **esr_target_range — 각사 ESR 목표레인지(자본정책), 랭킹 색 차등용 (owner 2026-09-13 확정, 티켓
   `inbox/jp/20260913T1610Z__owner__JP_MULTI__esr_target_ranges.md`).** 감독하한 100%만으로는 랭킹 막대색이 전부 초록이 된다 — 회사가 자본정책에서 공표한
   목표레인지(상단 초과=주주환원, 하단 미달=자본조치)로 색을 차등한다. 산출 `J-ESR/esr_target_ranges.json`(`_meta` + `ranges[]`: company_jp/company_en/low_pct/high_pct/
   basis(`internal_99.95`|`regulatory`|`unknown`)/confidence_level/policy_note/source_url/source_doc/as_of/inherited_from). 単体사는 자기 레인지가 없으면 모회사(HD) 레인지를
   `inherited_from` 표기로 상속, 상호회사(日本生命·住友生命·明治安田生命·朝日生命·富国生命)는 목표레인지 미공표가 정상이라 `null`(추정 금지). 2026-09-13 census 20사(jesr_esr.json 15
   + jesr_detail.json 미중복 5사) 결과: 확보 6건(Tokio Marine HD 190%+·MS&AD HD 180~250%·Sompo HD 200~270%·T&D HD 133~225%·Dai-ichi Life 170~200%, 전부 basis=regulatory·
   confidence=99.5%) + 자회사 3사 상속, null 14건(상호회사 5사 전원 + Sony FG/ソニー生命/かんぽ生命/ライフネット生命/NN生命/au損保/明治安田損保). **10월 말 재census 때 같이 갱신**
   (Sony FG·かんぽ生命·ライフネット生命·NN生명·상호회사 5사 우선 재탐색). 페이지 색 규칙 자체는 designer/오케스트레이터 소관, 이 항목은 census + JSON 까지만.

4. **산정 방식·신뢰수준도 같이 적는다 (owner 2026-09-12 질문에서 드러난 공백).** 09-12 census 는 15사 중 SOMPO 1사만 원문에
   "VaR 99.5%" 가 명시돼 `basis=J-ICS_VaR99.5` 로 적혔고, 나머지 14사는 방식을 안 뽑아 기본값 `J-ICS` 로만 남았다("다르다" 가 아니라
   "미확인"). 새 규제의 표준식은 1년 VaR 99.5%, 내부모형은 금융청 승인제 — 규제 전엔 회사별 자체 ESR 신뢰수준이 달랐다(도쿄해상 99.95%
   전례, 09-12 census 메모의 "新 J-ICS 기준 전환·목표 190%+ 재설정" 이 그 흔적). → census 열 `calc_method`(standard | internal_model |
   unstated) · `confidence_level`(예: 99.5) 추가. ESR 표 각주·리스크관리 파트에서 `標準的手法`/`内部モデル`/`信頼水準`/`VaR` 를 찾는다.
   결과가 오면 `/jp/` 각주를 "各社で異なる場合があり" 에서 실측("標準式 n社・内部モデル n社") 으로 바꾼다.

## 4c. 출처 URL 규칙 (2026-09-13 리허설로 생긴 규칙 — 10월 재census 전에 반드시 읽는다)

기게시 15사의 1차 출처를 전수 두드렸더니 5건이 실패했는데 **원인이 전부 달랐다.** 실패를 한 덩어리로 보면
멀쩡한 출처를 `not_found` 로 적재한다. 판정은 `J-ESR/check_source_urls.py`(엔진 `J-ESR/jesr_http.py`)가 하고,
**census 를 돌리기 전에 먼저 돌린다.**

| 분류 | 뜻 | census 에 어떻게 적나 |
|---|---|---|
| `ok` | 정적으로 열린다 | 그대로 |
| `ok_requires_headers` | 브라우저 헤더(UA·Accept-Language·Referer) 붙이면 200 | **살아있다.** `not_found` 금지 |
| `blocked` | 404 아닌 4xx(WAF·봇룰) | 죽음 아님. 사람 브라우저로 재확인 |
| `tls_client_issue` | 파이썬은 악수 실패인데 curl 은 200 | 우리 쪽 문제. 죽음 아님 |
| `spa_shell` | 200 인데 `<a>` 0개 + `<script>` 있음 | 정적 수집 불가 — 헤드리스 필요 |
| `dead` | 404/410 | 대체 URL 확보 대상 |

규칙 4개.

1. **수집기는 `requests.get` 을 직접 부르지 않는다.** `jesr_http.get()` / `probe()` 를 쓴다 — 헤더 기본값이
   한 군데 있어야 다음 라운드에 또 403 을 "죽음" 으로 적지 않는다(MS&AD·ソニーFG 가 그 사례, URL 은 멀쩡했다).
2. **만료 호스트는 1차 출처로 쓰지 않는다.** `release.tdnet.info`(TDnet 적시개시)는 게시 후 일정 기간이 지나면
   문서를 내린다 — T&D 2026-05-15 결산단신이 그래서 404 가 됐다. 회사 IR 상설 경로로 인용한다.
   목록은 `jesr_http.EXPIRING_HOSTS`, 점검기가 `expiring_host` 로 따로 표시한다(지금 200 이어도 경고).
3. **meta refresh 를 먼저 확인한다.** 東京海上HD `/ir/event/presentation/` 은 HTML 364바이트라 "SPA 셸" 로
   오진했지만 실체는 `<meta http-equiv="refresh">` 한 줄이었다 — 따라가면 링크 25개·PDF 6개가 정적으로 다 있다.
   requests 도 `curl -L` 도 meta refresh 는 안 따라간다. `jesr_http.probe()` 가 2홉까지 따라간다.
4. **URL 이 200 이라고 출처가 맞는 게 아니다.** MS&AD 출처 URL 은 200 이었지만 내용은 2026-02-13
   三井住友海上·あいおいニッセイ同和 **합병 보도자료**였고 ESR 은 한 줄도 없었다(기본 fetcher 에 403 이라
   그동안 아무도 못 열어봤다). 수치를 census 에 적을 때는 **그 문서에서 그 수치를 눈으로 본다.**

## 4d. EDINET 루트 — 2026-09-13 키 확보 후 실측으로 확정

- **키·호스트.** 환경변수 `EDINET_KEY`(저장소에 커밋 금지). 정본 호스트는 `https://api.edinet-fsa.go.jp/api/v2`
  — 종전 코드가 쓰던 `disclosure.edinet-fsa.go.jp/api/v2` 는 301→302 로 튕겨 간다. 인증은 헤더
  `Ocp-Apim-Subscription-Key` 와 쿼리 `Subscription-Key` 둘 다 된다. **키가 없으면 HTTP 200 에 본문이
  `{"StatusCode": 401}` 로 온다** — 상태코드만 보고 "결과 0건" 으로 읽지 말 것.
  확인: `python J-ESR/jesr_edinet_fetch.py --smoke`.
- **회사코드 정본은 `J-ESR/jp_insurers.csv` 한 곳뿐.** 갱신은 `python J-ESR/edinet_codelist.py --apply`
  (공식 EDINETコードリスト 11,389건 대조, 증거는 `J-ESR/edinet_code_match.json`). 스크립트에 코드를 하드코딩하지 말 것 —
  종전 하드코딩 13개 중 **7개가 다른 회사 코드**였다(E04979=パーク24, E04506=九州電力 …).
- **누가 EDINET 에 있나(81행 실측).** 有報 제출의무 17 · 등록만 있고 의무 없음 9(상호회사 5 + 第一生命保険·大同生命·
  太陽生命·FWD生命) · **미등록 51**. 즉 EDINET 으로 ESR 을 받을 수 있는 회사는 **최대 17사**이고 나머지는 영원히 안 온다
  — 각사 디스클로저 PDF 가 1차 출처라는 판단(owner 2026-09-12)의 기계 근거다.
- **FY2025 有報는 이미 다 나왔다.** 2026-06-11~06-30 에 14사 제출(전부 XBRL 있음). 인덱스는
  `python J-ESR/jesr_edinet_fetch.py --scan --from 2026-06-01 --to 2026-07-31` → `J-ESR/raw/edinet/scan_*.json`.
- **XBRL 태그에는 ESR 이 없다(FY2024 probe 결론 유지). 본문 iXBRL htm 에는 서술로 있다.**
  `python J-ESR/edinet_esr_probe.py` 가 有報 15건 전부에서 ESR 문장을 찾았고 5사는 수치까지 확정된다
  (東京海上HD 268% · T&D 222% · SOMPO 270% · ライフネット 333% · かんぽ 181%). 산출 `J-ESR/edinet_esr_probe.json`.
- **용도 두 가지.** ① 화면 수치 교차검증(감사받은 문서라 2차보도보다 강하다) ② 회사 IR PDF 가 사라졌을 때의 증거.
  단 **EDINET 뷰어 딥링크는 사용자용 링크로 쓸 수 없다** — 세션 기반이라 `WEEK0040.html?docId=…` 는 "Document Moved" 로
  튕긴다(2026-09-13 확인). 화면 `source_url` 은 회사 경로로 두고, 교차검증한 docID 는 census `notes` 에 적는다.

## 5. 이력 포인터

- 2026-06-24 트랙 신설·1차 수집(HD 그룹값)·EDINET probe: `docs/changelog_downloader.md` 06-24 항목 2건, `inbox/_resolved/*jesr*` 8건.
- 2026-07-21 MVP 페이지 revert(그룹값뿐이라 화면 보류, owner 결정). 2026-09-01 9월 말 킥오프 확정. 2026-09-12 소스 루트 정정(EDINET→회사별 사이트) + census 79사 + `/jp/` 초안. 상세는 `docs/changelog_jp.md`.
