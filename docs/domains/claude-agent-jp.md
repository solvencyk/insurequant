# jp 레인 — 일본 보험사 ESR 도메인 문서 (정본, 2026-09-12 신설)

jp 레인은 **한국 stage 프롬프트를 읽지 않는다.** 이 문서 + `TODO_jp.md` + `inbox/jp/` + 루트 `CLAUDE.md` 만 읽는다.
에이전트 정의는 `.claude/agents/jp-collector.md`(머신 로컬, push 안 됨 — 새 머신이면 이 문서로 다시 만든다).

## 1. 무엇을 모으나

- 대상: `J-ESR/jp_insurers.csv` 81행(완전 중복 2행 포함, 실질 79사 = 생보 45·손보 33·재보험 2·미분류 1). 열: `company_jp, company_en, ticker, sector, category, edinet_code, edinet_eligible, parent_group, ir_url, ir_health_url, notes`.
- 지표: **ESR(경제가치 기준 지급여력비율, %)** 1종 + 구성요소(적격자본·소요자본, 억엔) + 기준일 + 연결/단체 구분. 지금은 헤드라인 1종만 화면에 쓴다.
- 산출: `J-ESR/fy2025_esr_census_<YYYYMMDD>.csv`(census, 14열) → `J-ESR/build_jesr_page_json.py` → `J-ESR/jesr_master.json` + 배포용 `jp/jesr_esr.json`(바이트 동일). 화면은 `jp/index.html`(designer 소관).

## 2. 제도·주기 (한국과 다른 점 — 이걸 몰라서 생기는 오판이 대부분)

- 회계연도 4월~3월. FY2025 = 2026-03-31 기준. 첫 의무 ESR 사이클이 FY2025 말이다.
- **정본은 회사별 공시 사이트의 PDF**(결산설명자료·디스클로저지·별책). EDINET(전자공시) XBRL 은 보조 — FY2024 XBRL 6사 probe 에서 ESR 구성요소 0건(`inbox/_resolved/20260624T0337Z__owner__JP_MULTI__jesr_datalayer_asof.md`). 상장사 교차확인용으로만.
- 본문 디스클로저는 대부분 7월 말에 나오지만 **신기준 비율은 "2026년 10월 말 공표 예정" 으로 미루는 회사가 다수**(09-12 census: 손보 원문 13건 중 11건 명시). 최종 기한 2026-10-31. → 9월엔 분모(페이지 존재)와 일부 값, 10월 말에 전수 값.
- 단위 억엔(億円). 비율은 % 한 자리.
- 지주 상장 6사(Tokio Marine·MS&AD·Sompo·T&D·Sony FG·Dai-ichi)는 **그룹 연결값**을 결산설명자료에 먼저 낸다(5월). 자회사 단체값은 별도 — 둘을 `scope=group|solo` 로 반드시 구분해 적는다. 상호회사 5사(Nippon·Sumitomo·Meiji Yasuda·Fukoku·Asahi)는 비상장·EDINET 비대상, IR PDF 만.
- 속보/잠정(速報·暫定) 표기가 붙은 값은 `preliminary=true`. 확정치가 나오면 갈아끼운다(같은 as_of).

## 3. 라벨 변형 (원문 검색 키)

`ESR` · `経済価値ベースのソルベンシー比率` · `ソルベンシー・マージン比率（新基準）`(신기준 표에서는 옛 이름을 그대로 쓰는 회사가 많다 — 표 안에 `所要資本`·`適格資本`·`UFR`·민감도(株式 10%下落 등)가 같이 있으면 신기준) · `適格自己資本` · `所要資本の額` · 미공표 문구 `後日公表予定` / `2026年10月末に公表予定`.
구기준 `ソルベンシー・マージン比率` 단독(분모가 リスクの合計額 ×1/2)은 **ESR 이 아니다** — 옛 지표. 두 표가 같은 PDF 에 나란히 있는 경우가 흔하다.

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

3열 다 ESR 표와 **같은 PDF, 다른 섹션**에 있다 — 회사당 문서를 다시 열 필요는 없지만 훑는 페이지 수는 늘어난다. 화면(`/jp/`) 반영 여부는
이 데이터가 얼마나 뽑히는지 본 뒤 owner 에게 다시 묻는다(즉시 화면에 얹지 않는다).

## 5. 이력 포인터

- 2026-06-24 트랙 신설·1차 수집(HD 그룹값)·EDINET probe: `docs/changelog_downloader.md` 06-24 항목 2건, `inbox/_resolved/*jesr*` 8건.
- 2026-07-21 MVP 페이지 revert(그룹값뿐이라 화면 보류, owner 결정). 2026-09-01 9월 말 킥오프 확정. 2026-09-12 소스 루트 정정(EDINET→회사별 사이트) + census 79사 + `/jp/` 초안. 상세는 `docs/changelog_jp.md`.
