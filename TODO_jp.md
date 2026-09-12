# Insurequant TODO — jp 레인 (일본 ESR)

> Last updated: 2026-09-12 (10) · 도메인 문서: `docs/domains/claude-agent-jp.md` · Changelog: `docs/changelog_jp.md` · inbox: `inbox/jp/`
> Status 는 최신 5개만 유지, 밀린 항목은 [`docs/todo_archive_jp.md`](docs/todo_archive_jp.md) 로(무수정).

## Status

**🟢 2026-09-12 (10) 스키마에 손익 층 `layer:"profit"` 36항목 + 표본 추출·검산 P01~P13 + 회계기준 메타(jp).**
티켓 `inbox/jp/20260912T1150Z__owner__JP_MULTI__profit_layer_schema.md`(answered). owner "당기순이익 breakdown 등도 보면 좋겠다" → 한국 PL 패널의
일본판 입력층. `J-ESR/esr_disclosure_schema.json` 에 profit 36(값 32 + 메타 4: `accounting_basis`/`ifrs17_applied`/근거문/출처), 값은 `{prev,cur}` 쌍,
`sector_scope`·`pl_item_ref`(정확 24/22/23, 근사 20/1/17, 나머지 null — 억지 대응 금지). esr 115·article_axes 22 는 바이트 무변경 확인.
`extract_esr_template_samples.py` 에 `extract_profit`/`run_profit_checks`/`run_profit_axes_xref`/`merge_vertical`(au 5개년표 세로쓰기 라벨)/`pick_pc`
(열 레이아웃 4종) — exit 0. **실측**: au 25/25 추출·19/19 검산(経常利益 1,654·当期純利益 1,171·保険引受利益 1,550·資産運用損益 48·損害率/事業費率/
合算率 31.8/39.2/71.1, 5개년표 교차 16/16, P07 経常=引受+運用+その他 를 P&L 행으로 명시하니 ±1) / NN Life 13/16(三利源 미공시)·12/12(基礎利益 18,523
+キャピタル△1,232+臨時 4,082 = 経常利益 21,373 정확, 当期純利益 15,090) / Meiji Yasuda Non-Life **NOT_ACQUIRED**(별책에 손익 표 없음, 본편
`…/pdf/20260729.pdf` 는 443 차단 curl 000×3·requests ×3 + WebFetch 10MB 초과 — URL·사유를 COMPANIES 에 등재, 443 열리면 `profit_pages` 만 채우면 됨).
**회계기준 판정**: au jgaap/ifrs17=false(B 티어: 법정 P&L 양식+会社法436条/保険業法111条 감사문), NN jgaap/false(A 티어: 会計方針 標準責任準備金
大蔵省告示48号), MY unstated/unstated(회계방침 절 없음 — 추정 금지). 문서 `docs/domains/jp_esr_disclosure_template.md` §9(위치·검산·생손보 차이·
판정 규칙·publishing 블록 형식), `claude-agent-jp.md` §4b-3 흡수 문장. `jp/`·마스터·`build_jesr_detail_json.py` 미접촉(builder 는 esr 층만 읽어 안 깨짐).

**🟢 2026-09-12 (9) `jp/jesr.html` 신규(K-ICS.html 대응 회사별 ESR 상세) + `jp/index.html` 링크·표 개편(designer).**
티켓 `inbox/designer/20260912T1120Z__owner__JP_MULTI__jesr_company_page.md`(answered). 데이터는 publishing 산출
`jp/jesr_detail.json`(위 (8) 항목, 병행완성 — designer 개발 중 도착해 fixture(`jp/_fixture_jesr_detail.json`)는 만들자마자
삭제, 실제로는 안 씀; 코드는 실패 시에만 폴백하도록 남겨둠). owner 중간지시 2건 반영: ① 파일명 `company.html`→`jesr.html`
(K-ICS.html 처럼 제도명, hreflang/canonical 도 갱신) ② `jp/index.html` 一覧表 2개에서 業態·基準日 열 제거(生保/損保 섹션
분리로 業態 중복, 基準日은 상단 asOfLine 한 줄로 대체) → 5열(会社名/範囲/ESR/公表日/備考). ③ 基準日 표기를 날짜
그대로 대신 **일본 회계연도 분기**(基準時点 2025年度 4Q, title 툴팁에 실제 날짜)로 — 한국식 "2026.1Q" 로 읽으면
역월(4~6月)로 오독되는 문제(owner 정정) — `jp/index.html`·`jp/jesr.html` 둘 다 `jaFiscalQuarter(as_of)` 로 유도(하드코딩 안 함).

구성 9개(헤더+뒤로가기·회사선택+기준/범위/출처·헤드라인3카드·Tier1/Tier2 구성 스택바+표·소요자본 워터폴(ECharts
custom renderItem, IFRS17.html 워터폴 관례)+規定再現 배지·시장리스크 세부 6개·감응도 표+미니바·기사3축(숫자값만)).
실측 버그 2건 발견·직접수정: (a) publishing 실 데이터의 `doc_type` 에 파이프라인 내부 한국어 메모가 섞여 있어
(`…업적데이터편, 2026-07-30 발행)`) jp/index.html 의 기존 `jaOnly()` 를 그대로 이식해 제거. (b) 適格資本 구성표
비중(構成比)을 전부 적격자본 총액 대비로 계산하면 `tier1_basic` 류 중간항목이 149.6% 로 찍혀 오독 유발 →
Tier1/Tier2 최상위 2행만 총액 대비, 나머지는 자기 tier 의 `tier1_basic`/`tier2_basic` 대비로 분모 교체(표 하단에
계산기준 각주 추가). 모바일(375px) 렌더에서 워터폴 x축 8라벨 겹침 발견 → 짧은 라벨(生保/損保/巨大災害/市場/信用/
運営/分散効果/税効果/所要資本)+45도 회전으로 수정, 추가로 echarts.init 컨테이너 폭이 좁게 굳어 뒤쪽 2개 막대
(税効果·所要資本)가 통째로 안 그려지는 타이밍버그 실측 → `requestAnimationFrame` 안전망 resize 로 수정.
메타줄(기준시점|범위|공표)이 모바일에서 줄바꿈 없이 뷰포트 밖으로 밀려나가는 오버플로도 `.meta-line{overflow-wrap:anywhere}`
로 수정. `jp/index.html` 一覧表 회사명은 `jesr_detail.json` companies id 매칭 시만 `jesr.html?company=<id>` 링크
(au損害保険만 해당 — 明治安田損害保険 은 `excluded_subsidiaries` 라 一覧表 행 자체가 없어 링크 대상 없음, 정상).

검증: 로컬서버(`python -m http.server 8917`), 2사 전환(select 변경 + URL `?company=` 동기·직접 이동) 확인, 콘솔에러=0
(jsdelivr `ERR_NETWORK_ACCESS_DENIED` 는 이 PC 공통현상, JS 런타임에러 아님 — renderWaterfall 은 `typeof echarts==='undefined'`
가드로 무해하게 스킵됨). 이 PC 크로미움 CDN 차단으로 echarts 는 로컬 임시사본(`jp/_tmp_echarts.min.js`, SRI 해시
`sha384-o5uz97et3bErHvpKfD4Jz4n0JfhJDWABFuF4NP+iEEDxE1VwMWJ19QGR0lqFZnr6` 일치 확인 후 사용)으로 렌더 확인 후 삭제,
CDN 참조·integrity 원복을 `grep echarts jp/jesr.html` 로 재확인(git 미추적 신규파일이라 `git diff` 대신 `grep`). 최종
스크린샷은 msedge headless `--screenshot` 가 RAF resize 안전망 타이밍과 안 맞아 반복적으로 구버전 렌더가 찍혀(파일
크기 동일 반복) Playwright(`C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, `networkidle`+600ms 대기+
`full_page=True`)로 전환해 확보: `artifacts/designer/jesr_jp_jesr_desktop_20260912.png`(1280×2454)·
`artifacts/designer/jesr_jp_jesr_mobile_20260912.png`(375×2545, 워터폴 막대 8개 전부 표시 확인).
배포는 owner 승인 후 별도 라운드(`scripts/android_push_and_deploy.sh` NEW_FILES 는 오케스트레이터가 처리 — 미접촉).

**🟢 2026-09-12 (8) `jp/jesr_detail.json` 신규 조립 — au_nonlife·meijiyasuda_nonlife 2사 상세(publishing).**
티켓 `inbox/publishing/20260912T1120Z__owner__JP_MULTI__jesr_detail_json.md`(answered). `jp/company.html`(designer 병렬
작업, 이 세션 미접촉) 이 fetch 할 회사별 상세 JSON. 신규 `J-ESR/build_jesr_detail_json.py`(stdlib, self-check 내장 exit 1).
입력 4개: `extracted_sample_values.json`(이미 존재 — 없으면 추출기 자동 선실행) · `esr_disclosure_schema.json`(137 items 라벨) ·
`esr_aggregation_rules.json`(포인터만, known_deviations 는 이미 각 check 의 note 에 반영돼 있어 재병합 안 함) · `jp/jesr_esr.json`
(self-check 대조용). **판단 근거**: `jp/jesr_esr.json` 은 부모-자회사 중복 제거로 明治安田損害保険 을 `excluded_subsidiaries`
로만 남기고 `source_url`/`doc_type`/`doc_date`/`preliminary` 를 비운 상태라, 이 4필드는 제외 전 원본인 `J-ESR/jesr_master.json`
에서 조인(실측 확인 완료 — au 는 두 파일 값 동일, meiji 손보만 master 에만 존재). `census.status=="posted"` 인 2사만
(nnlife 는 ESR 미공시 제외). 계약 고정 키 그대로(`risk`=`diversification_effect`/`tax_effect` 리네임 포함,
`market_sub` 6개, `sensitivity[].delta_pp`=기준 대비, `aggregation.deviations`=informational 실패 체크만). **실측**(exit 0):
au_nonlife esr_pct=791.7·eligible=9,278·required=1,171·reproduced=true·checks=43/43·deviations=0·sensitivity=[](공시 생략사) /
meijiyasuda_nonlife esr_pct=743.2·eligible=40,290·required=5,420·reproduced=true·checks=49/51·deviations=2(G06_nonlife
다지역·G07_catastrophe, 둘 다 `esr_aggregation_rules.json known_deviations` 등재분)·sensitivity=7행(엔금리+50bp→-6.5pp 등).
`_meta.coverage`={detail_posted:2, posted_total:13, census_total:79}. self-check 4종 전부 통과(companies==2·headline.esr_pct
=jesr_esr.json 대조 일치·risk.rc_post_tax==headline.required_capital·items 전 id 가 labels 에 존재·단위 무변환 확인).
BOM 없음(`7b0a`)·`ast.parse` 통과. 배포: `scripts/android_push_and_deploy.sh` `NEW_FILES` 에 `jp/company.html jp/jesr_detail.json`
추가(한 줄). `git status --short J-ESR/ jp/` = 신규 `build_jesr_detail_json.py`·`jp/jesr_detail.json` 뿐(루트 마스터·xlsx·
public_exports·keep-list·HTML 무변경 확인; `jp/_fixture_jesr_detail.json` 은 designer 병렬세션 산출물이라 미접촉).
재현: `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_detail_json.py`.
**아직 라이브 미반영**(owner 승인 후 별도 배포 라운드, `jp/company.html` 대기 중).

**🟢 2026-09-12 (7) 소요자본 합산 규정(상관행렬)을 告示 원문에서 기계화 + √(xᵀRx) 재계산 검산 G01~G10 — 표본 2사 최상위·세효과·시장 재현.**
티켓 `inbox/jp/20260912T1005Z__owner__JP_MULTI__esr_aggregation_rule.md`(answered). 규정 원문 3건 확보 `J-ESR/raw/regulation/`(告示74호
통합본 167p·告示75호 별지양식 67p·令和8年告示6호 개정 8p; 개정은 합산 조문 무변경. curl 이 시간대 차단이라 75호는 WebFetch 바이너리
저장본). 기계본 `J-ESR/esr_aggregation_rules.json`: 최상위 第百五十五条(生保–損保 0.00, 그 외 0.25, オペ 선형가산)·생보 第八十一条·손보
第八十九条+別表七·巨大災害 第百条(0.00)·시장 第百二十七条(스프레드 上昇/下降 2행렬)·オペ 상한 20%·세효과 0.8×税率·分散効果 정의(75호 注 6(5)).
`extract_esr_template_samples.py` 에 `run_aggregation_checks`(G01~G10) + `rc_life_*` 6 id(스키마 esr 109→115). **재현:** 分散効果 au 273.6
vs 274·MY 2,529.5 vs 2,530, 세효과 = 0.8×28.0%×J 두 회사 ±1(역산 세율 27.98/27.99%), 시장 MY 4,611.8 vs 4,613, au 損保 1,119.0 정확, au
オペ는 20% 캡에 걸림(251 vs 251.5). **미재현(등재):** MY 損保 2,137 vs 2,096(다지역 — 규정 통합 순서와 공시 하위행 정의가 교환 안 됨,
informational 규칙) · MY 巨大災害 1,974 vs 1,865(注 4(4) 대로면 맞아야 함 — `その他の巨大災害` 단순합 가설, 10월 다수 확인 후 규칙 수정).
내부모형사 판정 규칙 문서 §8-4. exit 0(au 43/43, MY 49/51+info 2, NN 4/4). 문서 `docs/domains/jp_esr_disclosure_template.md` §8.

**🟢 2026-09-12 (6) ESR 규제 공시 양식 지도 + 기계 스키마 + 표본값(10월 62사 대비) — 두 층(esr / article_axes).**
티켓 `inbox/jp/20260912T0905Z__owner__JP_MULTI__esr_disclosure_template_map.md`(answered). 로컬 표본 3건(au Non-Life 31p·Meiji Yasuda
Non-Life 별책 14p·NN Life 95p, 전부 텍스트 PDF)을 fitz 로 해부. 산출 (A) `docs/domains/jp_esr_disclosure_template.md`(양식 구조 T1~T8·항목 표
131행·검산식·추출 규칙·K-ICS 대응·회사별 편차) (B) `J-ESR/esr_disclosure_schema.json`(items 131 = esr 109 + article_axes 22, `kics_item_ref`
27개만 대응·근사 사유 문서 §6) (C) `J-ESR/raw/fy2025_samples/extracted_sample_values.json` + 생성기 `J-ESR/extract_esr_template_samples.py`
(exit 0). 검산 au 34/34·MY 41/41·NN 4/4, census 헤드라인 791.7/743.2 일치, NN `not_yet` 일치. 핵심 발견: ESR 비율은 百万円 절사라
**구간 검산**만 맞음(au 점추정 792.31 vs 공시 791.7); 리스크 부모 ≤ Σ하위(상관 통합, 등식 아님); `Tier1 基礎項目 == EBS 純資産` 등 T2↔T4 교차
6건 일치; 경과조치 표는 양식에 없음; au 는 EBS 빈 행 생략·민감도 값 생략(1%p 미만 주기). 3축: au 異常危険準備金 2,222 = EBS 規制上の準備金,
NN Life 逆ざや 37億円(단위 億円)→negative·三利源 없음·AIR 키워드 0(정황 2건 `air_evidence`), MY 3축은 별책에 없어 본편 필요. **10월 census
확장 열 이름 = 스키마 id.** 생보 `生命保険リスク` 하위행은 표본 없어 미등록(발견 즉시 `rc_life_*` 추가).

## Active follow-ups

- **10월 말 재census** (2026-10-31 기한 직후): 같은 티켓 구조·같은 csv 열로 79사 재조회. notes 에 "패턴 기반 잠정" 이라 적힌 행(Zurich Life·AXA Life 등)부터 연다. 확정치가 나오면 `preliminary` 5사(LifeNet·Asahi·Fukoku·Japan Post·Sumitomo) 갈아끼움.
  **같은 라운드에 3축도 같이 뽑는다(owner 2026-09-12 확정, 아래 스코프 확장 항목과 병합·더는 미결 아님):** 회사별 공시 PDF 를 어차피 다시 여니
  ESR 옆에 열 3개 추가 — `air_used`(자산집약형 재보험 활용 여부·목적에 "ESR 개선" 명시 있는지) · `catastrophe_reserve_adequacy`(이상위험준비금/화재보험
  충족 여부, 생보는 해당없음) · `interest_margin_sign`(이차손익 부호·역마진→이익 전환 서술 유무). 손보 원문에 이상위험준비금 열람이 이미 필요하므로
  추가 비용 작지만, **생보 AIR·이차손익 서술은 다른 섹션**(결산설명자료 리스크관리·계리 파트)이라 놓치기 쉽다 — census 티켓에 이 3열을 명시할 것,
  "ESR 만 보고 넘어가는" 기본 습관으로 되돌아가지 말 것.
  **+ 산정방식 2열**(owner 09-12 질문): `calc_method`(standard/internal_model/unstated) · `confidence_level`. 09-12 census 는 SOMPO 1사만
  "VaR 99.5%" 명시, 14사는 미확인(기본값 `J-ICS`). 도메인 문서 §4b-4. 결과로 `/jp/` 각주("各社で異なる場合があり")를 실측 문구로 교체.
- `/jp/` 라이브 반영(owner 승인 후): publishing 티켓 답변의 "라이브 반영 시 필요한 것" 3건 — 배포 keep-list 가 4페이지 하드코딩(3곳)이라 새 페이지가 게이트에서 안 보임 → 목록화 필요; xlsx 시트 불필요; status_report 4절은 현재 무검사. 루트 `index.html` 에 hreflang 2줄 + 언어 전환 링크(designer 답변 조각).
- `jp_insurers.csv` 완전 중복 2행 정리(행 순서 보존 원칙 때문에 이번엔 보존). not_found 2사(Meiji Yasuda Trust Life·Yamap) 공시 페이지 재탐색.
- **3축 화면 반영은 별도 판단.** census 에 열만 먼저 채우고, `/jp/` 화면에 얹을지(카드 추가·범례 등)는 10월 말 데이터가 실제로 얼마나 뽑히는지
  본 뒤 owner 에게 다시 묻는다(루트 `TODO.md` J-ESR 항목의 기사 원 취지 — insnews #92437, 일본 금융청 2026 보험 모니터링 보고서 참고).
