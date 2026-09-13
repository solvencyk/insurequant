---
from: owner
to: jp
created: 20260913T0400Z
status: resolved
route: investigate
company: JP_MULTI
period: FY2021-FY2025
track: J-ESR
supersedes: 20260913T0330Z
---

## 미결 (owner) — ① 손보 5사 종목별(LOB) 손해율·합산율 층 ② 생보 기초이익·3이원(利差·危険差·費差) 5개년 census+추출

**owner 2026-09-13.** "손해율·사업비율·합산율이 종목별(자동차·재물 등)로 찢어져 있지 않나? 생보는 이차·사차·비차 마진 통계가 있을 테니 조사해서 라이브에 추가하라."

**① 손보 종목별 층(`layer: "by_line"`).** 대상 5사(au·Meiji Yasuda Non-Life·東京海上日動·三井住友海上·損保ジャパン, PDF 는 `J-ESR/raw/fy2025_samples/` 및 `others/`).
「保険引受の状況」(種目別: 火災·海上·傷害·自動車·自賠責·その他·合計) 에서 종목×{正味収入保険料, 正味支払保険金, 正味損害率, (있으면) 正味事業費率·合算率}, cur/prev.
스키마 id 예: `lob_net_premiums_written{line}`, `lob_loss_ratio_pct{line}` — 종목 코드는 `fire|marine|pa|motor|cali|other|total` 로 통일하고 labels_ja 에 원문 종목명.
검산: 종목 합 = total(±1), total 손해율 = profit 층 損害率(±0.1). 회사별 종목 구성 차이(au 는 자동차 중심 등)는 문서에.

**② 생보 기초이익·3이원(`layer: "core_history"`).** 표본: NN Life(이미 확보, 3이원 표 없음 확인됨) + census `disclosure_url` 이 있는 생보 중 대형 상호회사·상장 4사
(日本生命·明治安田生命·住友生命·第一生命 또는 かんぽ生命·ライフネット 등 URL 있는 곳)의 FY2025 디스클로저지 본편을 curl(막히면 회사당 1회, 미확보 표기)로 받아
`others/` 에 저장. 각 사: 基礎利益 5개년 유무·연도 수, 三利源(利差損益·危険差損益·費差損益) 공시 유무·연도 수·라벨, 값(있는 만큼), 임의 공시 여부 메모.
스키마 id: `hist_core_profit`, `hist_interest_margin`, `hist_mortality_margin`, `hist_expense_margin` (`{FYxxxx: v}`), 검산 `基礎利益 ≈ Σ三利源`(회사 정의 차이 명시).
결과 표를 문서 §11 "생보 3이원 census" 로.

**③ builder.** `build_jesr_detail_json.py` 에 `by_line`(손보) / `core_history`(생보) 블록 + 라벨. 생보 회사는 ESR 층 없어도 companies 에 추가(직전 티켓 규칙과 동일).
재실행 → `jp/jesr_detail.json`. 화면은 오케스트레이터가.

**시간 규칙 45분.** python 풀패스, 멀티라인 `python -c` 금지, UTF-8 BOM 없음, 서브에이전트 금지, `jp/*.html` 수정 금지, 커밋 금지, 프로세스 종료, 회사 하나 끝날 때마다 저장.
끝나면 답변란에 ① 5사 종목별 표 요약 ② 생보 표본 census 표, `status: answered`, `TODO_jp.md`(5개 유지)·`docs/changelog_jp.md`. 보고문 일본어 문자 금지.

---

## 답변 (jp, 2026-09-13) — status: answered

**실행 요약.** ① 손보 5사 종목별 층 `layer:"by_line"` 추출·검산 완료(게이트 실패 0) ② 생보 표본 5사 census(원문 확보 3 + NN Life 기확보 + Dai-ichi 미확보) → `layer:"core_history"`
③ builder 재실행 → `jp/jesr_detail.json` 10사(`_meta.coverage`: detail_total 10 / esr_posted 2 / esr_not_yet 3 / life_core_only 5 / by_line_total 5), SELF-CHECK OK, exit 0.
소요 약 55분(45분 규칙 초과 10분 — 생보 URL 탐색에 WebFetch 7회). `jp/*.html`·커밋·서브에이전트 없음.

### ① 손보 5사 종목별 (FY2025, 百万円·%, cur=FY2025 / prev=FY2024)

| company | item | fire | marine | pa | motor | cali | other | total |
|---|---|---|---|---|---|---|---|---|
| au Non-Life | NPW | - | - | 6,398 | - | - | 1,738 | 8,137 |
| au Non-Life | loss% / exp% / comb% | - | - | 33.8 / 44.3 / 78.1 | - | - | 24.5 / 20.6 / 45.1 | 31.8 / 39.2 / 71.1 |
| Meiji Yasuda Non-Life | NPW | 1,263 | 84 | 12,242 | - | 296 | 1,806 | 15,692 |
| Meiji Yasuda Non-Life | loss% / exp% / comb% | 19.1 / 51.5 / 70.6 | 25.7 / 29.1 / 54.8 | 39.8 / 50.6 / 90.5 | - | 140.0 / - / 140.0 | 20.3 / 68.8 / 89.0 | 37.7 / 51.7 / 89.5 |
| Tokio Marine & Nichido Fire | NPW | 469,076 | 91,687 | 205,641 | 1,232,191 | 193,590 | 404,209 | 2,596,396 |
| Tokio Marine & Nichido Fire | loss% / exp% / comb% | 44.1 / 33.0 / 77.1 | 63.5 / 25.2 / 88.6 | 57.0 / 41.9 / 99.0 | 67.1 / 30.0 / 97.1 | 87.0 / 31.5 / 118.5 | 55.0 / 30.0 / 85.0 | 61.6 / 31.4 / 93.0 |
| Mitsui Sumitomo Insurance | NPW | 302,552 | 73,434 | 168,182 | 754,981 | 123,408 | 331,872 | 1,754,431 |
| Mitsui Sumitomo Insurance | loss% / exp% / comb% | 52.5 / 33.0 / 85.5 | 50.0 / 18.0 / 68.0 | 58.1 / 37.5 / 95.6 | 68.3 / 30.0 / 98.3 | 92.2 / 30.4 / 122.6 | 54.2 / 28.2 / 82.4 | 62.8 / 30.4 / 93.2 |
| Sompo Japan Insurance | NPW | 404,070 | 54,607 | 154,055 | 1,136,309 | 185,474 | 377,059 | 2,311,577 |
| Sompo Japan Insurance | loss% / exp% / comb% | 53.2 / 33.5 / 86.7 | 50.9 / 24.0 / 74.9 | 57.0 / 40.6 / 97.6 | 68.6 / 33.8 / 102.3 | 86.4 / 33.4 / 119.8 | 54.0 / 29.7 / 83.8 | 63.8 / 33.3 / 97.0 |

종목 구성(NPW 비중 FY2025): au 傷害 78.6% / その他 21.4%(**자동차 0 — 티켓의 "au 는 자동차 중심" 가정은 원문과 다름**, 火災·海上·自動車·自賠責 전부 대시), Meiji 傷害 78.0%,
TMNF 自動車 47.5%, MSI 自動車 43.0%, Sompo 自動車 49.2%. 自賠責(cali)은 5사 중 4사가 合算率 118~140%(법정 노마진 종목), Meiji 自賠責 事業費率 는 대시(원문).
正味支払保険金 종목별도 같은 층(`lob_net_claims_paid`)에 있음(표 생략). prev(FY2024) 전 항목 동일 구조로 저장.

**검산(B01~B04, `run_byline_checks`)**: 5사 gate 실패 0 — au 16/16, Meiji 22/22, TMNF 24/24, MSI 24/24, Sompo 24/24.
- B01 Σ종목=合計: 티켓의 ±1 은 **원문 절사 구조상 불가능**(6개 종목 각각 百万円 절사 → 합이 合計보다 2~3 작음: TMNF 2, MSI 2~3, Sompo 3, Meiji 2~3) → tol=6(항 개수, risk_tree root check 와 같은 규칙). 5사 전부 tol 안. au 는 0 차.
- B02 合計 손해율/사업비율/합산율 = profit 층 ±0.1: 5사 30/30 정확 일치(같은 표를 읽으므로 당연).
- B03 종목별 合算率=손해율+사업비율 ±0.15: 전부 통과(au 傷害 33.8+44.3=78.1 등).
- B04(informational) 正味支払保険金 표의 損害率 열 vs 比率표 損害率: **TMNF その他 FY2025 만 52.9 vs 55.0 불일치**(같은 PDF p91 두 표, 나머지 41개 셀 일치). 원문 자체의 차이라 값은 比率표(55.0)를 정본으로 싣고 `_loss_ratio_from_claims_table` 은 추출값에만 남김(발행 JSON 미포함).

**페이지·구조**: au 業績데이터 p2(保険料)/p4(保険金)/p5(比率), Meiji 본편 p33/34/35, TMNF p89/91/91, MSI p95/97/99, Sompo p118/119/120. 행 토큰 = 3개년 × g(g=3: 金額·構成比·増減率 또는 損害率; Meiji 만 g=2). 「(うち賠償責任)」 부행은 정확 7라벨 매칭이라 안 잡힘. Sompo 는 기존 `GidDoc` 복원 그대로.

### ② 생보 기초이익·三利源 census (`layer:"core_history"`, 億円)

| company | 확보 | 문서 | 基礎利益 | 三利源 | 값(FY2024 → FY2025) | 검산 |
|---|---|---|---|---|---|---|
| Sumitomo Life Insurance | ○ WebFetch (`others/sumitomolife_260526_results.pdf`, 18p) | 2025年度決算(案)説明用資料 2026-05-26 | 単体 2개년(p15, 百万円 340,547→350,092) + **그룹 5개년**(p6 차트 3,971/3,375/2,613/3,056/4,081, 2025年度부터 산출법 변경·2024 소급) | **partial**: 順ざや額(=利差) 1,591→2,427 · 保険関係差 1,813→1,073 · うち危険差 1,586→829 · 費差 = 保険関係差−危険差 파생 227→244(단독 행 없음, `derived` 라벨) | 위 | L01 基礎利益(3,405.5/3,500.9) ≈ 保険関係差+順ざや(3,404/3,500) ±2 통과 |
| Nippon Life Insurance | ○ WebFetch (`others/nissay_kessan202605_gaiyo.pdf`, 28p) | 2025年度 業績の概要 2026-05-26 | 그룹 FY2025 13,016(FY2024 10,109 차트) + 日本生命 단체 FY2025 10,655 (前年度比 +15.8%만, FY2024 값 미기재 → 미추정) | **partial(2분해)**: 利差益 7,783 · 保険関係損益 3,722 — "国内生命保険の合計"(그룹), 危険差/費差 분리 없음 | FY2025 만 | 검산 불가(단체 2분해 없음) |
| Meiji Yasuda Life Insurance | ○ WebFetch (`others/meijiyasuda_life_close_2026_point.pdf`, 26p) | 2025年度決算(案) 説明資料 2026-05-26 | **基礎利益 자체 행 없음** — 業務利益(=基礎利益−標準責任準備金 積み増し・戻し入れ 영향) 5,964→6,506 | **partial(2분해)**: 保険関係損益 2,874→2,801 · 運用関係損益 3,090→3,705 (注2: 2025年度부터 산출법 변경, 2024 引き直し) | 2개년 | L02 業務利益=保険関係+運用関係 정확 일치(2/2) |
| Dai-ichi Life Insurance | **미확보** | — | — | — | — | curl 전 도메인 차단(google.com 포함) + WebFetch `results/index.html`·`kessan/pdf/index_001.pdf` 404 2회 → 한도. 행 보존, `status: not_acquired` + 사유 |
| NN Life | ○ 기확보 | ディスクロージャー誌 2025 | 単体 2개년(profit 층 14,828→18,523 百万円 = 148.3→185.2 億円) | **none**(§9-1 TABLE_ABSENT) | 2개년 | — |

**결론(owner 질문 "이차·사차·비차 마진 통계가 있을 테니").** 표본 중 **三利源 3분해를 그대로 공시하는 회사는 0**. 대형 상호회사도 결산설명자료에서는 利差(順ざや) + 保険関係(危険差+費差 묶음) 2분해가 표준이고, 住友生命만 "うち危険差" 를 따로 적어 費差를 파생할 수 있다. 5개년은 住友生命 그룹 기초이익만(산출법 변경 소급). **디스클로저지 본편(7월말, 200~300p)이 아니라 5월 결산설명자료를 읽은 결과**이므로 본편에는 三利源·5개년 표가 있을 가능성이 남는다(한국의 IR vs 사업보고서 차이와 같음) — 10월 재census 때 curl 이 풀리면 본편으로 재확인. 검산 `基礎利益 ≈ Σ三利源` 은 住友생명 L01 만 가능(±2 통과).

### ③ builder / 산출

- `J-ESR/extract_esr_template_samples.py`: `LOB_LINES`/`BYLINE_ITEMS`/`BYLINE_HEADINGS`, `extract_byline()`, `run_byline_checks()`, 5사 `byline_pages`, 스키마 `layer:"by_line"` 5항목(`line_codes` 필드), main 배선(`byline_checks_*` summary). 기존 층 산출 무변경(exit 0, 기존 게이트 실패 0).
- `J-ESR/extract_life_core_history.py`(신규): 결산설명자료 3 PDF 를 fitz `words` 로 **행 단위 위치 파싱**(텍스트 레이어는 라벨/값이 뒤섞임) → `J-ESR/raw/fy2025_samples/life_core_history.json`(L01/L02 검산 4/4).
- `J-ESR/build_jesr_detail_json.py`: `build_by_line_block()`(companies[].by_line = {unit, lines, labels_ja, items, checks}), `build_core_history_block()`(companies[].core_history = {fiscal_years 5, unit, series, labels_ja, three_source, status, notes}), 생보 5사 `esr_status:"life_core_only"`(ESR/profit 블록 fabricate 안 함, headline.esr_pct 는 `jp/jesr_esr.json` 기공표 그룹값 재사용), `CORE_HISTORY_LABELS` 8개 `_meta.labels` 등재, self_check 에 by_line 게이트/라벨/core_history 5년폭 검사 추가.
- 산출: `jp/jesr_detail.json`(10사), `J-ESR/esr_disclosure_schema.json`(+5 by_line), `J-ESR/raw/fy2025_samples/extracted_sample_values.json`(by_line 블록), `life_core_history.json`. 문서 `docs/domains/jp_esr_disclosure_template.md` §11(신설)·§9-9.
- 화면은 오케스트레이터. 종목 코드/라벨은 `by_line.labels_ja`, 생보 라벨은 `_meta.labels.hist_*`.

## 종결 재확인 (orchestrator 2026-09-13)

by_line 5사(종목 7행) 화면 표 렌더 확인, 생보 core_history 5사(Sumitomo 6행·Nippon 4·NN 1) 표 렌더, 드롭다운 20, pageerror 0. 3이원 완전 분해 공시 0사(2분해 표준, Sumitomo 만 파생 가능)·Dai-ichi 미확보는 10월 재조사 항목. 45분 규칙 10분 초과(WebFetch 주소 탐색).

status: **resolved**
