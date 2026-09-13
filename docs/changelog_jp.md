# Changelog — jp 레인 (일본 ESR)

> 이력 저장소. 세션 시작 시 읽지 않는다. 현황은 `TODO_jp.md`.

## 2026-09-13 (22) -- 회사별 상세 3페이지 분리 + 所要資本 워터폴 폐지 + 貸借対照表 T자형 패널

- owner: 한국 K-ICS/IFRS17/기타공시 대응으로 `jp/jesr.html`(자본) / `jp/jgaap.html`(회계) / `jp/disclosure.html`(기타공시). 인라인 CSS/JS → `jp/jp.css` + `jp/jesr_app.js`
  (공용; `<body data-page>` 분기, 컨테이너 없는 render 는 byId 가드로 스킵, `syncTabLinks` 로 `?company=` 동기화, 제목·그룹 사업회사 링크 페이지별).
- 所要資本 워터폴 제거(owner: 분산효과 △만 보여주는 그래프). 告示 재현 배지는 適格資本・所要資本 표 제목으로. jesr.html 은 더는 ECharts 를 읽지 않는다.
- jgaap.html: 主要指標 카드(当期純利益·経常利益·保険引受利益/基礎利益·合算率), 貸借対照表 T자(IFRS17.html Panel 1 미러: 존 3개·[+]·負債:純資産 flex 비율·2기 비교표·
  資産=負債+純資産 배지, 입력 = (21) `bs.tree`), 損益·収益性·準備金(axes reserve*). disclosure.html: 再保険 의존도(reins_*)·その他·미수록 안내.
- jp/index.html·terms.html 헤더 3탭. 배포 스크립트 NEW_FILES +jgaap.html/disclosure.html/jesr_app.js/jp.css. designer 프롬프트 jp 절·publishing §12 keep-list 갱신.
- 검증: Playwright 12케이스(3페이지×손보/생보/지주/없는 id + index/terms)×1200/375px pageerrors 0, T자 패널 TMNF/日本生命 표시·住友生命 숨김 확인.
- 후속(같은 날): bs 7사→**10사**. 住友生命 = 7월 資料編(`others/sumitomolife_2026_repodata.pdf`, WebFetch 바이너리) 単体 p58 prev_cur / 第一生命 = owner 업로드 アニュアルレポート2026
  분책 index_004(`others/daiichi_2026_index_004.pdf`) 単体 p23~24 prev_cur / 明治安田損保 = 본편 p39~40 **열 우선 3개년 표**(라벨 글리프 병합 불가 → 고정 라벨 목록 index 매핑,
  `col_major_3yr`·`extract_colmajor()`). 準備金Σ 허용오차를 항 개수로(3항 百万円 절사 1~2 실측). 社債 라벨 「社　債」 alias, 相互会社 社員配当準備金 라벨, 페이지는 row.label_ja 우선.

## 2026-09-13 (20) -- 損益表 元受収支 / 再保険収支 두 블록 + 出再保険手数料(注記) 추출

- owner 결정: 상대방 기준 두 블록(수재는 출재 재원이라 재보험 블록에), 명칭은 損益 이 아니라 収支(수입·지급 기준). 出再保険手数料 는 재보험 수지에 더하고
  사업비 행은 총액(支払諸手数料及び集金費)으로 — 순액+수수료 이중계상 방지. 자배책·지진 풀 경유 각주.
- extractor: `pl_commissions_gross`/`pl_ceded_commission` `src:"note"`(문서 전체 스캔) + P16. 5사 확보(TMNF 50,494 / MSI 66,157 / Sompo 45,553 / Meiji 239 / au 209 百万円).
  au 라벨-금액 사이  제어문자 → 제거 후 매칭. 注記 단년이라 prev None.
- builder: `NONLIFE_PROFIT_FLOW` 상단 4행 → `pf_direct_balance`(元受, 収入積立保険料 차감)·`pf_reins_balance`·`pf_commissions_row`·`pf_uw_other_residual`(잔차),
  `row.parts` 계약 신설, `_meta.labels` 5개 추가, checks `premium_bridge_ok`/`claims_bridge_ok`/`commission_note_ok`. 종전 `underwriting_ok` 는 5사 전부 False 였다(積立·準備金 누락).
- page: BRIDGE 상수 제거, `row.parts` 렌더, `#profitFlowNote` 각주. Playwright: TMNF/au 행·[+] 전개·pageerrors 0, 생보(住友) 무영향.

## 2026-09-13 (19) -- 손보 종목별 층 `by_line` + 생보 기초이익·三利源 `core_history`, `jp/jesr_detail.json` 5사→10사

- 티켓 `inbox/jp/20260913T0400Z__owner__JP_MULTI__lob_ratios_and_life_margins.md`. `extract_esr_template_samples.py` 에 `LOB_LINES`/`BYLINE_ITEMS`/`BYLINE_HEADINGS`,
  `extract_byline()`(헤딩 앵커 + 7라벨 순차 커서 grab, 행 토큰 3개년×g, g=3 또는 Meiji g=2), `run_byline_checks()`(B01~B04), 5사 `byline_pages`, 스키마 `layer:"by_line"` 5항목.
  결과 5사 gate 실패 0, 기존 층 산출 무변경. B01 tol 은 항 개수 6(종목별 百万円 절사 — 실측 차 TMNF 2·MSI 2~3·Sompo 3·Meiji 2~3·au 0).
- 발견: au 는 자동차 종목 0(傷害 78.6%) — 티켓의 "au 는 자동차 중심" 은 원문과 다름. TMNF p91 두 표(正味支払保険金 표 vs 比率표)의 その他 FY2025 損害率이 52.9 vs 55.0(원문 차이,
  나머지 41셀 일치) → B04 정보성 체크로 남기고 比率표를 정본으로.
- 생보: 이 세션 curl 은 전 도메인 차단(google.com 포함) → WebFetch 가 PDF 바이너리를 저장해 주는 것을 이용해 住友生命(決算説明用資料 18p)·日本生命(業績の概要 28p)·
  明治安田生命(決算説明資料 26p) 확보(`J-ESR/raw/fy2025_samples/others/`). 第一生命은 index.html/kessan pdf 404 2회로 미확보(행 보존, 사유 기록).
  신규 `J-ESR/extract_life_core_history.py`: 슬라이드형 PDF 라 텍스트 레이어에서 라벨/값이 뒤섞여 fitz `words` 를 y 로 묶는 위치 파싱 → `life_core_history.json`
  (L01 住友 基礎利益≈保険関係差+順ざや ±2, L02 明治安田 業務利益=保険関係+運用関係 정확, 4/4). **표본 三利源 3분해 공시 0사**(2분해 표준, 住友만 危険差 별도→費差 파생).
- `build_jesr_detail_json.py`: `build_by_line_block`/`build_core_history_block`, 생보 5사 `esr_status:"life_core_only"`(ESR/profit 블록 fabricate 없음, headline.esr_pct 는
  `jp/jesr_esr.json` 기공표값), `CORE_HISTORY_LABELS` 8개, self_check 확장(by_line 게이트/라벨, core_history 5년폭·not_acquired 사유). SELF-CHECK OK exit 0.
- 문서 `docs/domains/jp_esr_disclosure_template.md` §11 "생보 3이원 census" + §9-9 종목별 층. 45분 규칙 10분 초과(생보 URL 탐색 WebFetch 7회).

## 2026-09-13 (18) -- 대형 손보 3사 본편에서 ESR 외 전 층 추출, `jp/jesr_detail.json` 2사→5사

- 티켓 `inbox/jp/20260913T0330Z__owner__JP_MULTI__big3_partial_detail.md`. (17)에서 확보한 `J-ESR/raw/fy2025_samples/others/` 3 PDF(TMNF 292p·MSI 272p·
  Sompo Japan 292p)에서 profit(損益計算書·保険引受利益 明細·比率·재보험 다리)·history 5개년·article_axes(責任準備金の内訳·出再先/格付)·회계기준 추출.
  `extract_esr_template_samples.py` 에 `BRIDGE_SPEC`(회사별 표 헤딩·TMNF 2열 쌍표)·`RESERVE_SPEC`(붙은 셀 정규식 12/6 토큰)·`reins_style` 3종·
  `GidDoc`(Sompo 글리프 id 복원)·history 옵션(`hist_skip`/`hist_drop_paren_all`/`hist_label_overrides`/`hist_smr_layout`) 추가. 3사 배선 결과 exit 0,
  게이트 실패 0(profit 31/31·history 10/10·census_match 3/3), au/Meiji/NN 값 무변경(체크 formula 문자열·tol 만 변경).
- 검산식 수정 2건: P07 経常利益 브리지에 `−その他収支`(보험인수이익 안의 自賠責 法人税相当額은 経常利益에 없음 — TMNF −3,152 에서 드러남, 넣으면 0 차이),
  P11 tol 1→3(4항 절사, Sompo 48,253 vs 48,251). P14 는 元受 표가 含む収入積立保険料 뿐인 회사(TMNF·Sompo)에서 P&L 収入積立保険料 를
  `profit.adjustments` 로 뽑아 차감(MSI 는 除く 표 사용). 회계기준 IFRS 검색을 basis 페이지로 한정(본편 뒷부분 그룹 연결 IFRS17 오판 방지).
- `build_jesr_detail_json.py`: census not_yet + profit/history 있는 회사 포함, `esr_status`/`esr_placeholder` 키(5사 전부), not_yet self-check 분기,
  `_meta.coverage` detail_total/esr_posted/esr_not_yet, `LABEL_JA_DISPLAY_OVERRIDES`(커밋 e67bc36 수기 라벨 4개 고정), profit_flow 資産運用損益 라벨 고정.
  SELF-CHECK OK. 기존 2사 블록·labels 스크립트 diff 로 무변경 확인.
- 스키마: bridge 3항목 labels_ja 에 `元受正味保険料(除く/含む収入積立保険料)`·`出再正味保険料`·`出再正味保険金` 변형 추가. 문서 §9-8·§10-8(페이지 매핑·추출값·편차·폰트 복원 규칙).
- 미해결: Sompo 복원은 `C:/Windows/Fonts/msgothic.ttc` 의존(다른 머신은 경고 후 NOT_FOUND). 3사 ESR 은 2026-10-31 이후 재census 때 `layers` 에 `esr` 추가.

## 2026-09-13 (17) -- 손보 6사 표본 실측(3사 확보) — 손해율/사업비율/합산율 시계열 공시 여부 확인, ESR 은 전원 미공표

- 티켓 `inbox/jp/20260913T0230Z__owner__JP_MULTI__nonlife_ratio_availability.md`. owner "손해율 5개년이 다른 손보사에도 다 있는지" 질의에
  대형4(東京海上日動·損保ジャパン·三井住友海上·あいおいニッセイ同和)+중형2(共栄火災·日新火災) 표본으로 답. 세션 중반 curl 이 전 도메인
  차단(`www.google.com` 포함)으로 전환돼 **3사만 원문 PDF 확보**: Tokio Marine & Nichido Fire(TMNF_2026_d.pdf, 292p), Mitsui Sumitomo
  Insurance(a01.pdf, 272p), Sompo Japan Insurance(sj_disc2026.pdf, 292p) — `J-ESR/raw/fy2025_samples/others/`(gitignore).
- 실측 결과: 3사 전부 정미손해율·정미사업비율 시계열이 이미 공시돼 있다(owner 가정 확인). 단 표 구조가 회사마다 다르다 — TMNF/au/Meiji 는
  「主要な経営指標等の推移」5개년 단일표(合算率 행 없음), Sompo Japan 은 표제목 변형 「最近5事業年度に係る主要な財務指標」(5개년, 合算率
  없음), MSI 는 5개년 단일표 자체를 못 찾고 대신 3개년 종목별표에서 합산율을 직접 확인. **MSI·Sompo Japan 둘 다 별도 3개년 종목별표
  (正味損害率、正味事業費率及びその合算率)에 合算率이 라벨로 직접 공시**되어 있어(파생 불필요) `hist_combined_ratio_pct` labels_ja 에
  `"合算率"` 단독 추가. FY2025: TMNF 損害率61.6%/事業費率31.4%, MSI 合計행 損害率62.8%/事業費率30.4%/合算率93.2%, Sompo Japan
  損害率63.8%/事業費率33.3%/合算率(3개년표 合計행)97.0%.
- ESR 은 3사 전부 not_yet(2026年10月末), 문구가 회사마다 새로 발견돼 `esr_disclosure_schema.json` `esr_status` labels_ja 에 3종 추가:
  TMNF 표셀 "別時期での開示", MSI 각주 "…2026年10月末までに開示します", Sompo Japan 각주 "…2026年10月末の予定です".
- 폰트 인코딩 함정 발견: Sompo Japan PDF 는 숫자/기호(`0-9`·`.`·`%`)가 U+3EDC 대역으로 **+16044(0x3EAC) 오프셋**된 PUA 유사 코드포인트로
  추출된다(임베디드 폰트 ToUnicode CMap 이상, TMNF/MSI 는 정상) — `ord(ch)-16044` 가 32~126 이면 ASCII 로 치환하는 디코더로 우회.
  `docs/domains/jp_esr_disclosure_template.md` §10-7 에 재현법 기록.
- 미확보 3사는 행을 지우지 않고 사유를 남김: Aioi Nissay Dowa(disclo_policy/ir 페이지에 PDF href 없음, ms-ad-hd.com 은 403/커넥션거부,
  WebSearch 로도 직접 URL 미발견), Kyoei Fire & Marine(도메인 curl 2회 연결거부+WebFetch 인증서 오류), Nisshin Fire & Marine(WebSearch 로
  정확한 URL은 특정 — `https://www.nisshinfire.co.jp/ir/pdf/disclosure2026.pdf` — 그러나 curl 차단으로 원문 미열람, 손해율 실측 안 함).
- 산출물: census csv 4행(TMNF/MSI/Sompo Japan/Nisshin) `disclosure_url`·`checked_at`·`notes` 갱신(TMNF `sector` 공백 버그도 함께
  수정 — `損保` 자회사인데 빈 문자열이라 sector 필터에서 누락되고 있었음), `docs/domains/jp_esr_disclosure_template.md` §10-7 신설,
  `J-ESR/esr_disclosure_schema.json` 라벨 보강 2건. `jp/*.html`·builder·서브에이전트·커밋·git push 없음.

## 2026-09-13 (14) -- jesr.html 단일 표([+] 펼침)·손익 선별·재보험 다리·収益性指標·자회사 dedup 해제 (orchestrator 직접)

- owner 피드백 6건(부호/계층·하위리스크 미표시·손익 항목·손해율 별도·원수/출재·자회사 삭제 이유) 처리. designer 2회(32분+13분 연장) 미완으로 종료·되돌린 뒤
  orchestrator 가 jesr.html 직접 수정(88595f4): capital_tree+risk_tree 단일 표(K-ICS.html subtoggle, 다단 접기, 符号, ✓/差/相関統合), profit_flow+재보험 다리 [+],
  details 전 항목, 収益性指標(카드+5개년 SVG+연도표). DOM 검증 au 30행/Meiji 41행·pageerror 0. 스키마 라벨 2건 정정.
- 자회사 dedup 해제(b9c3f23): 한국 K-ICS 는 법인 단위(교보생명 155.43·교보라이프플래닛 162.97 각각 게시) → 일본도 법인마다 한 행, 지주 連結값은 10월 単体로 교체.
- 데이터: 재보험 다리 6항목(au 원수 166억엔 중 출재 85억엔=51%, Meiji 9%), 5개년 history 13항목, 손익 profit 36항목.
- 교훈: jp designer 라운드 45~57분의 원인은 ECharts CDN 차단 검증 루프 → jp 차트는 SVG/CSS 만, 티켓은 DOM 검증만, 30분 초과 시 orchestrator 인수.

## 2026-09-13 (16) -- publishing: `jp/jesr_detail.json` 에 `capital_tree`/`risk_tree`/`profit_flow` 구조화 블록 신설

티켓 `inbox/publishing/20260913T0005Z__owner__JP_MULTI__jesr_detail_trees.md`. owner 09-12 피드백(① 자본구성표 하위합≠상위
② 보험위험·대재해위험 하위분해 화면에 없음 ③ 손익 항목 선별 나쁨 ④ 손해율 별도패널)의 데이터 쪽. designer 가 formula 를 파싱하지 않도록
builder 가 트리·흐름을 완성해서 넘긴다.

**`J-ESR/build_jesr_detail_json.py` 신규 함수**: `build_tree(root_id, merged, items_by_id, children_map)` — 스키마 `parent`
링크를 따라가는 전위순회 공용 함수, `capital_tree`(`eligible_capital` 뿌리)·`risk_tree`(`rc_pre_tax` 뿌리) 둘 다 이걸로 만듦.
`build_profit_flow(profit_raw, items_by_id, sector)` — 손보 13행/생보 10행 고정 순서, `pl_other_ordinary`(=경상이익-引受利益-
운용손익)·`pl_extraordinary_net`(=특별이익-특별손실) 2개 파생 id(스키마에는 안 넣고 `_meta.labels` 에만 추가).

**설계에서 티켓 문구를 리터럴대로 안 따르고 바꾼 지점 2개** (실측 근거, 답변에 상세):
1. `is_total` 판정 — 티켓은 "formula 보유 = is_total" 이라고 썼으나, `tier1_ni_capital_surplus`/`tier1_ni_aoci`/
   `tier1_ni_ev_adjustment` 3항목은 formula 가 있지만(`== ebs_capital_surplus` 등) 이 tree 안에서 자식이 0개인 alias 라
   리터럴대로면 "합계 0개짜리 total" 이 된다. **스키마상 자식 존재 여부**(구조)로 판정하도록 바꿔 이 예외를 별도 분기 없이 해결.
2. total 노드 check 의 tolerance — 티켓은 `±1` 로 명시했으나 risk_tree 루트(`rc_pre_tax`, 9-term 공식)는 au/meiji 둘 다 ±1
   을 못 지킨다(diff 2/3). 기존 추출기 자체 체크 `C12_rc_pre_tax` 가 이미 이 공식에 `tol=9`("n terms, 각 항 절사")를 쓰고 있어
   그 근거를 따라 `tol=max(1, 실제 합산 항 개수)` 로 일반화(2-3항 노드는 사실상 ±1~2 와 동일, 회귀 없음).

**실측** (재현 `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_detail_json.py`,
exit 0, SELF-CHECK OK): capital_tree/risk_tree correlated 노드(`rc_nonlife`/`rc_catastrophe`/`rc_cat_natural`/`rc_market`)의
`simple_sum` 이 기존 체크 C14/C15/C16/C17 의 rhs 와 2사 전부 정확히 일치(교차검증 통과) — au 1190/87/247, meiji 2458/2666/2523/7567.
profit_flow 검산 3개는 `ordinary_ok`=true(설계상 항등) 둘 다, `underwriting_ok`/`net_ok`=**false 둘 다** — 선별 6행 합이 保険引受利益
과 실제로 차이남(au 806~866·meiji 690~829, 스키마에 없는 責任準備金等繰入額 등 항목 추정), 특별이익 cur 미공시로 net 재현도 어긋남.
정직하게 false 로 실어 self_check() 하드게이트에는 안 걸었다(root check 2개 + ordinary_ok 만 게이트). `git diff` 로 확인: 세 신규
키 + `_meta.labels` 2개 + `generated_at` 외의 `jp/jesr_detail.json` 변경분은 전부 이번 세션 시작 전부터 있던 (15)번 재보험
브릿지 스키마/추출기 미커밋 변경(관여 안 함). 상세: `TODO_jp.md` (16), 티켓 답변란.

## 2026-09-13 (15) -- 손익 층에 재보험 다리(bridge) `table:"profit:bridge"` 6항목 신설 — 元受/受再/出재 분해

티켓 `inbox/jp/20260913T0025Z__owner__JP_MULTI__reinsurance_bridge.md`. owner: "정미(正味) 숫자 말고 원수(元受, 출재 전) 숫자를 따로 볼
수 없나." 디스클로저지 「保険引受の状況」 절의 6개 종목별(火災/海上/傷害/自動車/自動車損害賠償責任/その他) 표에서 元受正味保険料·受再正味保険料·
支払再保険料(→正味収入保険料) 와 元受正味保険金·受再正味保険金·回収再保険金(→正味支払保険金) 을 `{cur,prev}` 百万円 으로 추출한다.

**스키마**: `J-ESR/esr_disclosure_schema.json` `layer:"profit"` 신규 6항목(`pl_gross_premiums_written`/`pl_assumed_premiums`/
`pl_ceded_premiums`/`pl_gross_claims_paid`/`pl_assumed_claims`/`pl_recovered_reinsurance_claims`, `table:"profit:bridge"`,
sector_scope=nonlife) + 기존 `pl_net_premiums_written`/`pl_net_claims_paid` 에 formula 필드 추가(둘 다 `PROFIT_ITEMS` 리스트
수정만으로 `build_schema()` 가 자동 반영 — 스키마 항목 42개, 이전 36개에서 +6).

**추출** (`extract_esr_template_samples.py::extract_bridge_block`/`_bridge_row_value`/`BRIDGE_ORDER`): 두 회사 모두 같은 이번
표본 PDF 안에 이미 있다 — au 는 業績데이터 4of5 분책 p3~4(curl 불필요), Meiji Yasuda 는 본편(§9-6 에서 확보) 60p p33~34. 6개
하위표는 페이지에 순서대로 나열되지만 **회사마다 순서가 다르고**(au: 支払→元受料→受再料→元受金→回収金→受再金 / Meiji: 元受料→受再金→
回収金→受再料→支払→元受金) 라벨 문자열이 페이지 후반 각주에 재등장한다(예: au "従業員1人当たり元受正味保険料"). `BRIDGE_ORDER` 로
회사별 문서순서를 명시하고, 각 항목은 "직전 항목의 `合計` 행 다음부터" 커서를 전진시키며 탐색해 각주와의 충돌을 회피했다. au 受再 두
항목은 원문에 표 자체가 없고 `該当事項はありません`(해당없음) 문구뿐 — 0으로 채운다(null 아님, 항등식이 0으로 닫혀야 하므로).

**버그 1건 발견·즉시 수정**: `_bridge_row_value()`에서 `合計` 행을 처음엔 `grab(lines, h+1, [r"^合計$"], stop=h+80)` 로 좁혀 찾았는데,
`grab()` 은 `stop` 파라미터로 **라벨 탐색과 값 캡처 구간을 동일하게** 자른다 — 라벨이 그 경계 바로 앞에서 매치되면 캡처할 여지가 0이
되어 버린다(au 保険料 두 항목의 合計 가 heading+79 위치라 stop=heading+80 과 거의 맞닿아 toks=[] 로 나왔고, 첫 실행에서 P14 두 건이
0/0 으로 깨졌다). `stop` 을 제거(표 안 첫 `合計` 가 항상 정답이므로 무제한 탐색이 안전)해 해결.

**검산** (`run_profit_checks` 확장): P14_premium_bridge(`정미수입보험료 = 元受+受再-出再`) · P15_claims_bridge(`정미지급보험금 =
元受+受再-回収`), cur·prev 각각 ±1 百万円. **실측**(exit 0): au 4/4, Meiji Yasuda Non-Life 4/4 전부 통과 — au 保険料
16,646+0-8,509=8,137(정미 실측과 정확 일치, prev 17,165+0-9,188=7,977 vs 실측 7,976 ±1), Meiji 保険料 16,363+811-1,482=15,692
(정확 일치, prev 16,086+688-1,447=15,327 정확), 保険金 은 百万円 절사로 양사 모두 ±1(au cur 9,595+0-7,655=1,940 정확·prev
10,303+0-8,434=1,869 vs 1,868 ±1, Meiji cur 4,733+552-176=5,109 vs 5,108 ±1·prev 4,654+727-282=5,099 vs 5,098 ±1).

**`_meta.labels` 자동생성 확인** (티켓 할 일 3): `build_jesr_detail_json.py` 는 이번 라운드에 손대지 않았다(publishing 편집 중).
`build()` 함수(434~446행)가 `for it in schema["items"]: labels[it["id"]] = {...}` 로 스키마 전체를 순회해 `_meta.labels` 를
자동 조립하므로, 새 6항목이 `esr_disclosure_schema.json` 에 들어간 이상 **오케스트레이터가 그 빌더를 재실행하기만 하면** 라벨이
자동 추가된다(수동 등재 불필요). `build_profit_block()`(화면용 `items`/`ratios`/`core` 뷰 조립)이 이 6개를 어느 뷰에 얹을지는
publishing 판단 — 이번 라운드는 스키마·추출·검산까지만.

`docs/domains/jp_esr_disclosure_template.md` §9-7 신설(항목표·추출특이점·버그 기록·회사별 수치표). `jp/*.html`·
`build_jesr_detail_json.py`·서브에이전트·커밋 없음.

## 2026-09-12 (14) -- 시계열 층 `layer:"history"` 신설 + 손보 2사 5개년(FY2021~FY2025) 추출

티켓 `inbox/jp/20260912T1440Z__owner__JP_MULTI__pl_history_5y.md`. owner: "손해율·사업비율·합산비율 시계열을 쭉 보여줘도 좋겠다. 당기/전기만
있어 허전하다." profit 층({prev,cur} 2개년)이 이미 읽던 「主要な経営指標等の推移」 5개년표(au 業績データ편 p2 / Meiji Yasuda 본편 p9, profit
층의 `profit_pages["summary5"]` 재사용, 문서를 새로 열지 않음)를 5개 사업연도 전부 뽑도록 확장했다.

**스키마**: `J-ESR/esr_disclosure_schema.json` `layer:"history"` 13항목 — `hist_net_premiums_written`/`hist_ordinary_profit`/`hist_net_income`/
`hist_loss_ratio_pct`/`hist_expense_ratio_pct`/`hist_combined_ratio_pct`/`hist_total_assets`/`hist_net_assets`/`hist_smr_old_pct`/`hist_esr_pct`
(값 10) + 생보용 `hist_core_profit`/`hist_premium_income`/`hist_policy_reserves`(id 만 정의, 표본 손보 2사엔 미적용). 값은
`{"FY2021": v, ..., "FY2025": v}` 사업연도 키 dict.

**추출** (`extract_esr_template_samples.py::extract_history`): 새 헬퍼 `strip_paren`/`PAREN_NUM_RE`/`PAREN_DASH_RE` 로 괄호 안 실제 숫자(구기준
SMR)와 괄호 안 대시(적립계정 0 등 노이즈)를 구분. 회사별 함정 2건: ① Meiji 正味収入保険料 행은 값 뒤에 `（対前期増減率）` 가 같은 줄 스트림에
끼어 있어 `drop_paren=True` 로 통째 스킵. ② Meiji 단체SMR 라벨을 세로쓰기로 찍을 때 "ソルベンシー" 안의 장음부호 "ー" 가 대시 문자와 코드포인트가
같아 `merge_vertical` 이 라벨을 "単体ベ"/"ー"/"スの"/"ソルベンシー・マージン比率" 로 쪼갬 → 느슨한 부분일치 `HIST_SMR_LABEL_RE` 로 우회(au 무회귀).
③ Meiji 는 손해율/사업비율이 5개년표 자체엔 없어 profit 층이 이미 읽는 3개년표(p35 `(6)正味損害率…`)에서 FY2023~2025 만 백필, FY2021~2022 는
null 로 남김(억지 채움 없음, raw_tokens 에 "BACKFILL" 문자열로 구분 가능).

**旧基準 SMR ↔ 新基準 ESR**: 두 회사 다 한 행에 같이 있고 괄호 유무로 나뉜다 — 괄호 있는 토큰(구기준 실측) → `hist_smr_old_pct`, 괄호 없는
토큰(신기준) → `hist_esr_pct`(공통 파서, 회사별 분기 없음). au 는 구기준 자리가 전부 대시(각주: 신제도 시행으로 구기준 기재 생략)라
`hist_smr_old_pct` 5개 다 null 이 정상. Meiji 는 4개 non-null(2,847.6/2,940.4/2,814.7/2,642.5%). 둘 다 `hist_esr_pct` FY2025 한 칸만 채워짐.

**검산** (`run_history_checks`): H01(FY2025==profit 층 동일 id 의 cur, FY2024==prev, 금액 ±1·비율 ±0.1) + H02(연도별 合算率=損害率+事業費率
±0.1). 결과 **au 17/17, Meiji Yasuda Non-Life 15/15** — `extract_esr_template_samples.py` 전체 gate(`all_checks`)에 합류, exit 0.

**publishing 블록**: `J-ESR/build_jesr_detail_json.py::build_history_block()` 신설 — 같은 값을 `{"fiscal_years":[...], "unit":"JPY_million",
"series":{"<hist_id>":[v,...]}}` (연도 배열, ticket 지정 형태)로 재편, `companies_out[].history` 로 노출. `self_check()` 에도 같은 검산(구조
정합·FY2025/2024 교차·合算率 항등식) 추가 — exit 0, SELF-CHECK OK.

**부작용**: `aggregation.checks_pass/checks_total` 이 (11) 항목과 같은 이유로 자연 증가(au 62→79, Meiji 66/70→81/85) — 새 H01/H02 가 같은
summary gate 에 합류했을 뿐, 기존 esr/article_axes/profit 블록·키는 바이트 무변경(스키마 diff = 신규 항목 + layers/tables/column_note 설명문
추가뿐).

문서: `docs/domains/jp_esr_disclosure_template.md` §0(한 줄 요약에 4번째 층 추가)·§10(표 위치·연도 수·라벨 렌더링 특이점·SMR/ESR 괄호 분리·
검산·회사별 편차·중간기(中間期) 공시 메모 — 일본은 연차+9월말 中間期만 법정, 분기는 상장 지주 決算短信 헤드라인뿐이라 history 층은 연 1회만
갱신). `TODO_jp.md` (14) 갱신, (10) 항목은 `docs/todo_archive_jp.md` 로 이동. `jp/*.html`·서브에이전트·커밋 없음.

## 2026-09-12 (12) -- jp/jesr.html 損益の内訳 패널 (designer, orchestrator 종결)

티켓 `inbox/_resolved/20260912T1330Z__owner__JP_MULTI__jesr_profit_panel.md`. `jp/jesr_detail.json` profit 블록(2사 extracted, J-GAAP)으로 会計基準 한 줄·
当期純利益 워터폴(소요자본 워터폴과 같은 custom renderItem, △ 표기)·当期/前期/増減 표(損害率·事業費率·合算率 포함)·✓ 合算率 배지(클라이언트 재계산).
생보 분기(基礎利益·3이원)는 `profit.core` 유무로 배선만(10월 생보 표본 후 확인). designer 세션이 CDN 차단 우회 검증을 반복해 52분 소요 → 산출물
확인 후 orchestrator 가 커밋(92863df)·에이전트 종료. 교훈: designer 티켓에 "시각 검증 1회, 이후 DOM 검증으로 마무리" 명시.

## 2026-09-12 -- Meiji Yasuda Non-Life 본편 확보 후 profit 층 채움(스키마 무변경) + 세션 중 소스 PDF 소실 사고

owner 가 티켓 `inbox/_resolved/20260912T1150Z__owner__JP_MULTI__profit_layer_schema.md` 회차(위 09-12 항목들의 profit 층 신설)에서
本編 미확보였던 Meiji Yasuda Non-Life 손익 데이터를 `J-ESR/raw/fy2025_samples/meijiyasuda_nonlife_20260729_main.pdf`(60p)로 직접
넣어줘, 추출기에 경로·페이지·라벨을 배선하고 재실행했다.

**발견한 회사별 레이아웃 특이점 3개** (모두 `extract_esr_template_samples.py` 에 회사별 opt-in 으로만 배선, au/NN 무회귀 확인):
1. 損益計算書(p42)가 한 구획(경상수익 12항목 등)의 라벨을 전부 나열한 뒤 그 구획 전체 3개년 값을 한꺼번에 찍는 방식 — 기존 `grab()`
   방식(라벨 뒤 값)이 안 먹어서, 라벨을 무시하고 제목~注記 사이 값 토큰만 순서대로 읽는 `pl_flat_tokens`+`MEIJI_PL_FLAT_MAP`(120개
   고정 위치) 신설.
2. 明細表·比率표는 라벨을 글자 하나씩 세로줄로 찍어(`保`→`険`→`引`→`受`…) 정규식 라벨 매칭이 아예 안 됨 — 기존에 summary5 전용이던
   `merge_vertical()` 를 `vertical_labels=True` 로 uw/ratio 에도 적용. 회계기준 근거문 판정도 같은 이유로 깨져 있어서
   `"\n"→" "` 치환 후 공백을 전부 제거한 사본(`basis_ns`/`doc_ns`)으로 판정하도록 고쳤다(CJK 는 원래 공백이 없어 매치를 늘리기만
   하고 기존 회사의 매치는 그대로 유지).
3. 資産運用損益(実現ベース) 합계행을 그대로 쓰면 積立保険料等運用益 이 保険引受収益 안에도 들어 있어 이중계상(P07 이 ±15 로 깨짐) —
   손익계산서의 資産運用収益-資産運用費用 으로 대체하는 `pl_investment_override="pl_stmt"` 신설.

**스키마 불변식 유지.** `pl_uw_operating_general_admin` 행 라벨이 明細表에선 그냥 "営業費及び一般管理費"(注記로만 보험인수 귀속분
확인)라 스키마 정본 라벨 "保険引受に係る営業費及び一般管理費" 를 못 찾았는데, 스키마 항목의 `labels` 자체를 고치지 않고 회사별
`label_overrides` 딕셔너리로만 별명을 추가했다 — `esr_disclosure_schema.json` 173항목 바이트 무변경(`git diff --stat` 로 확인).

**세션 중 사고: 소스 PDF 가 로컬에서 사라짐.** 페이지를 다 읽고 검증까지 마친 뒤 재확인하려는데 파일이 없어졌다(홈 디렉터리 전체
검색 + git 이력 대조 — 애초 git 미추적이라 이력도 없음, 원인 불명, Claude 가 지우지 않았음). 사라지기 전 읽은 원문(p9·35·36·42·45
의 `get_text('text')`)을 `meijiyasuda_nonlife_main_pages_fixture.json` 으로 남겨 뒀고, `main()` 을 "① 실물 PDF ② fixture 재현
③ NOT_ACQUIRED" 순으로 동작하게 고쳤다(`FixtureDoc`). 이번 결과는 fixture 경로 산출 — 새 코드 경로(`pl_flat_tokens`/
`MEIJI_PL_FLAT_MAP`/`vertical_labels`/`label_overrides`/`pl_investment_override`) 자체는 실제 파일에서 읽은 실제 텍스트를
재생해 검증했으므로 추정이 아니다. 실물 PDF 가 돌아오면 다음 실행이 자동으로 그쪽을 우선하고, fixture 결과와 대조해 볼 것.

**결과.** meiji profit 25/25 applicable 전항목 추출, 검산 17/19(2건은 P13 이자배당↔투자손익 informational, au 도 같은 사유로
실패), accounting_basis=jgaap/ifrs17_applied=false(B 티어, au 와 같은 판정 근거 구조). 상세 수치·페이지 매핑식·검산표는
`docs/domains/jp_esr_disclosure_template.md` §9-1(갱신)·§9-6(신설). publishing 의 `jp/jesr_detail.json` profit 블록은 아직
Meiji 가 not_obtained 로 박혀 있어 재실행이 후속 필요(이번 라운드는 `jp/` 미접촉 원칙 유지).

## 2026-09-12 (owner 결정) -- jp 비공개 프리뷰: main 배포 경로를 `jp-f9027362/` 로 (deploy-time 매핑)

owner "당분간 비공개, 그러나 라이브 배포는 해서 확인" → 선택지 3(비밀 경로 / JS 비밀번호 / Cloudflare Access) 중 1번. GitHub Pages 는 서버 인증 불가,
JS 비밀번호는 소스·JSON 직접 접근으로 우회되므로 비권장. 구현은 저장소 구조를 안 바꾸고 `android_push_and_deploy.sh` 에 `JP_PRIVATE_DIR` +
`deploy_path()` 매핑(CHANGED 계산·NEW_FILES 존재 확인·워크트리 checkout→mv·blob 검증·라이브 URL 출력 5곳). 첫 라운드에 main 의 공개 `jp/` 자동 삭제.
임시 워크트리 시뮬레이션으로 6파일 이동·blob 일치·커밋 확인(push 없이). 공개 전환 체크리스트는 `TODO_jp.md`.

## 2026-09-12 (owner 확인) -- jp/terms.html 4건 확정: 運営者 표기 유지·관할 = ソウル中央地方法院(한국판과 동일)·GA 보유 최대 14개월·施行日 2026-09-12

owner "4건 다 확인" → 관할만 한국 `privacy.html` 과 맞춰 "運営者の所在地を管轄する裁判所" → "ソウル中央地方法院(大韓民国)" 로 1문장 수정(orchestrator 직접, 텍스트 1줄). 나머지 3건은 초안 그대로 확정.

## 2026-09-12 (12) -- `jp/terms.html` 신규 + `/jp/` GA4·CSP·오류제보 팝업 + `jp/jesr.html` nit 3건 (designer)

- 티켓 `inbox/designer/20260912T1215Z__owner__JP_MULTI__jp_terms_privacy.md`(answered). owner: "일본 사이트에 이용약관이 없다 — 해외야말로
  유료화·사업화 여지가 있어 약관을 잘 써 둬야 한다."
- `jp/terms.html`: 利用規約 第1条~第8条(本サイト/許諾/禁止+編集著作物·データベース 第12条·第12条の2/有料サービス・ライセンス留保/出典表/免責/変更/
  運営者·問い合わせ·準拠法) + プライバシーポリシー 1~8(GA4·誤り報告フォーム 設置済み/利用目的/外国第三者提供表+Google DPF/Cookie 무효화/保有期間/
  開示等請求/安全管理/施行日 2026-09-12). 運営者 표기는 第8条 한 문단에만(법인 전환 시 그 문단만 교체). chrome·CSP·GA4·hreflang·noindex 는
  `jp/index.html` 관례, 읽기 페이지 스타일은 루트 `privacy.html` 이식.
- `jp/report-widget.ja.js`: 루트 `report-widget.js` 복제·일본어화. 시트 2개, payload sheet 에 `JP:` 접두(백엔드 무변경). 회사 목록·期 는
  `jesr_esr.json`+`jesr_detail.json` fetch 로 유도(14사, `_meta.as_of`→`jaFiscalQuarter`), fetch 실패 시만 정적 폴백 — 분기 리터럴 하드코딩 함정 회피.
  루트 대비 A11y 추가: `label[for]` 연결, 오류문 `role=alert`, 허니팟 `aria-hidden`.
- `jp/index.html`·`jp/jesr.html`: CSP 를 루트 index.html 6행과 동일 문자열로(googletagmanager·google-analytics·analytics.google.com apex·
  script.google.com·script.googleusercontent.com), GA4 스니펫(iq_internal) 추가, 푸터 링크, 본문 끝 `../forms-config.js`+`report-widget.ja.js`.
- `jp/jesr.html` nit: ① 워터폴 y축 하한이 패딩 때문에 음수(au △2.2·MY △11.5 억엔)로 내려가던 것을 `lo<0` 일 때만 음수 허용, 제목 `(億円)`+
  `nameGap 12`+`grid.top 20→40` ② 構成比 세부행(tier basic 대비 100.0%)이 총액 대비로 오독 → Tier1/Tier2/適格資本の額 3행만 총액 대비 표시,
  세부행 빈칸, 각주 교체 ③ 375px 에서 `#capitalTable{min-width:0}`+항목명 `overflow-wrap:anywhere`+숫자열 nowrap.
- `scripts/android_push_and_deploy.sh` NEW_FILES 에 `jp/terms.html jp/report-widget.ja.js`.
- 검증: 로컬 8931 + Playwright 3페이지×(1280/375) 콘솔에러 0(jsdelivr/gtag 차단만 ignore)·링크 200·팝업 제출 POST 시도 확인, echarts 는 이 PC 외부
  443 차단(curl/requests 000, WSAEACCES)으로 `add_init_script` setOption 스텁으로 옵션 검증(yMin=0, grid.top=40, 8막대), `test_deploy_assets.py`
  11 passed, 5개 파일 UTF-8 BOM 없음·LF.
- owner 확인 필요: 運営者 표기·準拠法/관할·GA 보유기간·시행일. `TODO_jp.md`·`docs/changelog_jp.md` 는 publishing 세션의 미커밋 (11) 과 같은 파일이라
  이 라운드 designer 커밋에서 제외(갱신만).

## 2026-09-12 (11) -- `jp/jesr_detail.json` profit 블록 추가 (publishing)

- 티켓 `inbox/publishing/20260912T1240Z__owner__JP_MULTI__jesr_detail_profit_block.md`(answered). 위 (10) 이 스키마·추출을 끝낸
  `layer:"profit"` 값을 배포 JSON 에 실제로 붙이는 조립 작업.
- `J-ESR/build_jesr_detail_json.py` 에 `build_profit_block(profit_raw, items_by_id)` 추가. 스키마 `table` 태그로 그룹 분리:
  `items` = 값이 있는(non-null) 전체 profit id (`{cur,prev}` 쌍, 양쪽 다 null 이면 항목째 생략), `ratios` = `profit:ratio`(손보
  손해율/사업비율/합산율), `core` = `profit:core`+`profit:three`(생보 基礎利益 분해 3개 + 三利源 3개) — capital/risk 블록이 이미
  쓰던 "items 전체 + 부분집합 편의 뷰" 패턴을 그대로 따름(티켓 예시는 core 에 4개 id 만 나열했지만, 그 4개가 정확히 스키마
  `profit:core`/`profit:three` 두 테이블의 교집합 절반이라 스키마 태그로 일반화 — 10월 62사가 三利源 을 다르게 공시해도 손 안 대고 맞음).
  나머지 필드는 티켓 그대로: `accounting_basis`/`ifrs17_applied`/`evidence`(← `accounting_basis_evidence`)/`source_doc`(←
  `profit_source_doc`)/`unit`("JPY_million" 고정)/`status`(`profit_source_doc` 가 `"NOT_ACQUIRED"` 로 시작하면 `not_obtained`,
  아니면 `extracted`).
- `_meta.labels` 에 `pl_item_ref` 필드 신규 추가(모든 항목에 균일 — profit 36개는 값, 기존 esr/article_axes 는 null). 라벨 총
  137→173.
- meijiyasuda_nonlife 본편 PDF(`J-ESR/raw/fy2025_samples/meijiyasuda_nonlife_20260729_main.pdf`)는 이번에도 로컬에 없어
  `extract_esr_template_samples.py` 재실행 스킵, 기존 추출값(profit 전부 null, `status="not_obtained"`) 그대로 사용.
- self-check 확장: au `pl_ordinary_profit`/`pl_net_income` 존재 확인, 손보 合算率 항등식(`損害率+事業費率==合算率`, ±0.1, cur·prev
  각각) 확인, meiji `status=="not_obtained"` + `items=={}` 확인, profit 하위 모든 id 가 `_meta.labels` 에 존재하는지 확인.
- 실행 결과(exit 0): au_nonlife profit.status=extracted, accounting_basis=jgaap, ifrs17_applied=false, 経常利益 cur=1,654/prev=1,451,
  当期純利益 cur=1,171/prev=961, 合算率 cur=71.1(=31.8+39.2)/prev=72.1(=29.4+42.7). meijiyasuda_nonlife profit.status=not_obtained,
  items/ratios/core 전부 `{}`.
- `git diff jp/jesr_detail.json` 로 부작용 감사: `generated_at` 갱신과 신규 `pl_item_ref`/`profit` 필드 외에 유일한 변화는
  `aggregation.checks_pass/checks_total` 이 43/43→62/62(au)·49/51→50/52(meiji) 로 증가한 것 — 이는 이번 코드 변경이 아니라
  입력 `extracted_sample_values.json` 이 이미 (10) 라운드에서 profit 검산(au 19개·meiji 1개)을 포함하도록 갱신돼 있었고,
  `aggregation` 필드가 원래부터 회사 전체 검산 요약(esr 전용이 아님)을 그대로 읽는 로직이었기 때문. headline/risk/market_sub/
  capital/axes/sensitivity 등 다른 블록은 바이트 무변경. `jp/*.html`·`esr_disclosure_schema.json`·루트 마스터 미접촉(같은
  워크트리에서 designer 세션이 `jp/index.html`·`jp/jesr.html` 을 동시에 수정 중인 것을 확인, 미개입).
- 재현: `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_detail_json.py`.
- 라이브 미반영(owner 승인 후 별도 배포 라운드, designer 의 `jp/jesr.html` profit 렌더 작업 대기).

## 2026-09-12 (10) -- 스키마 손익 층(profit) + 표본 3건 추출·검산 + 회계기준 메타 (jp)

- 티켓 `inbox/jp/20260912T1150Z__owner__JP_MULTI__profit_layer_schema.md`(answered). 일본 법정 결산은 J-GAAP 원가법이라 CSM 이 없고,
  생보 基礎利益·三利源 / 손보 保険引受利益·資産運用損益·비율 3종 / 공통 経常利益·当期純利益 이 공시 표로 있다 → `layer:"profit"`.
- 스키마: 36항목(값 32 + 메타 4). id 접두 `pl_`, `sector_scope` life/nonlife/both, `column:"prev+cur"`(전기 비교값 동반), `pl_item_ref`
  (루트 PL_breakdown 항목번호: 24·22·23 정확, 20·1·17 근사, 그 외 null), 헤더 `pl_ref_note`·`accounting_basis_note`. 기존 두 층 무변경.
- 추출기: 회사별 `profit_pages`(pl/uw/ratio/inv/core/three/summary5/basis) + `pl_layout`(prev_cur_diff au / prev_pct_cur_pct NN). P&L 라벨은
  `^…$` 앵커라 커서 없이 매칭(처음엔 esr 층처럼 순차 커서를 썼다가 항목 순서≠행 순서로 8항목 NOT_FOUND — 제거). 손보 비율·운용 표는 `合計` 행이
  여러 표에 반복되므로 `(6)正味損害率`·`(3)資産運用利回り` 제목 뒤 첫 `合計` 만. au 5개년표는 라벨이 세로쓰기(한 글자 한 줄)라 `merge_vertical`.
- 검산 P01~P13(cur·prev 각각): au 19/19, NN 12/12, MY P00 informational. 티켓식 대응 — 合算率=損害率+事業費率(P06 ±0.15, 반올림),
  経常≈引受+運用±その他(P07, その他 를 その他経常収益−その他経常費用−(営業費及び一般管理費−保険引受係る営業費) 로 명시하니 ±1),
  基礎利益≈三利源(P02 informational, NN 미공시 → 대신 基礎利益 정의식 P01 정확). P12 = profit ↔ article_axes core_profit 교차.
- 회계기준: (A) 会計方針 절 인용(標準責任準備金/大蔵省告示48号/企業会計基準) 또는 (B) 법정 P&L 양식+会社法436条/保険業法111条 감사문 → jgaap;
  `ifrs17_applied=false` 는 jgaap 단체 법정재무제표에서만(법령 사실), 그 외 unstated. au B·NN A → jgaap/false, MY 별책만 → unstated.
- Meiji Yasuda 본편: census disclosure 페이지를 WebFetch 로 열어 `pdf/20260729.pdf` 링크 특정, 그러나 443 차단(curl 000×3, requests ×3)·WebFetch
  10MB 초과 → 미확보. URL·사유 COMPANIES 등재.
- 문서: `jp_esr_disclosure_template.md` §9(항목표·위치·검산표·생손보 차이·판정 규칙·publishing `profit` 블록 JSON 제안) + §0 요약,
  `claude-agent-jp.md` §4b-3. `jp/`·마스터·detail builder 미접촉.

## 2026-09-12 (9) -- `jp/jesr.html` 신규(K-ICS.html 대응 회사별 ESR 상세) + `jp/index.html` 링크·표 개편 (designer)

- 티켓 `inbox/designer/20260912T1120Z__owner__JP_MULTI__jesr_company_page.md`(answered). 산출물: `jp/jesr.html`(신규, K-ICS.html
  패널 구조·chrome·`../common.css` 재사용) · `jp/index.html`(一覧表 링크 + 표 개편). owner 중간지시 2건: 파일명 `company.html`→
  `jesr.html`(제도명 관례), `jp/index.html` 一覧表 業態·基準日 열 제거 + 基準日 표기를 일본 회계연도 분기(`基準時点 2025年度 4Q`,
  실제 날짜는 title 툴팁)로 변경 — 날짜 그대로 쓰면 한국식 "2026.1Q" 로 오독됨.
- 데이터는 publishing 이 이 라운드에 병행 완성한 `jp/jesr_detail.json`(au_nonlife·meijiyasuda_nonlife 2사). 개발 중 임시
  `jp/_fixture_jesr_detail.json` 을 계약대로 만들었으나 실 파일이 곧 도착해 삭제, 실사용은 안 됨(코드는 실패시에만 폴백).
- 페이지 구성 9개: 헤더+뒤로가기 · 회사선택(URL `?company=` 동기) · 헤드라인 3카드 · Tier1/Tier2 구성 스택바+표 ·
  소요자본 워터폴(ECharts custom renderItem, IFRS17.html 관례 — 0선 넘는 항목 zero-crossing 안전) + 規定再現 배지 ·
  시장리스크 세부 6개(비-null만) · 감응도 표+미니바(기준행 포함) · 기사3축(숫자값만, dict/문자열/배열은 자동 제외).
- 실측 버그 3건 발견·직접수정(발주범위 밖이지만 명백한 버그): (1) 실 데이터 `doc_type` 에 파이프라인 내부 한국어 메모
  혼입(`…업적데이터편, 2026-07-30 발행)`) → `jp/index.html` 의 기존 `jaOnly()` 를 이식해 화면표시 직전 제거. (2) 適格資本
  구성표 비중을 전부 총액 대비로 계산하면 중간항목(tier1_basic 등)이 149.6% 로 찍힘 → 최상위 2행만 총액 대비, 나머지는
  자기 tier 의 basic 대비로 분모 교체. (3) 모바일(375px)에서 워터폴 x축 8라벨 겹침(짧은 라벨+45도 회전으로 수정) +
  echarts.init 이 컨테이너 폭 안정 전에 불려 뒤쪽 2개 막대가 안 그려지는 타이밍버그(`requestAnimationFrame` 안전망 resize
  추가) + 메타줄이 줄바꿈 없이 뷰포트 밖으로 밀려나감(`overflow-wrap:anywhere`).
- 검증: 로컬서버 `python -m http.server 8917`. 2사 전환(select + URL 직접이동) 확인, 콘솔에러 0(jsdelivr
  `ERR_NETWORK_ACCESS_DENIED` 만 — 이 PC 공통현상, `typeof echarts==='undefined'` 가드로 무해). echarts 는 로컬 임시사본
  (`jp/_tmp_echarts.min.js`, SRI 해시 사전대조)으로 렌더 확인 후 삭제, CDN 참조·integrity 원복을 `grep` 로 재확인. 최종
  스크린샷은 msedge headless `--screenshot` 가 RAF resize 타이밍과 안 맞아(반복 동일 파일크기) Playwright 로 전환해 확보:
  `artifacts/designer/jesr_jp_jesr_{desktop,mobile}_20260912.png`(모바일 워터폴 막대 8개 전부 표시 확인).
- 동시편집 조정: 같은 라운드에 jp-collector 세션이 `TODO_jp.md`Status 에 "(9) profit 층" 항목을 병행 추가해 내 항목과
  번호(9)가 충돌 — profit 항목을 (10) 으로, 6개로 늘어난 Status 에서 가장 오래된 (5) `jp/index.html` ECharts→리스트 항목을
  `docs/todo_archive_jp.md` 로 무수정 이관해 5개 유지 규칙 복구(내용은 안 건드리고 번호·위치만 조정).
- 배포는 owner 승인 후 별도 라운드(`scripts/android_push_and_deploy.sh` NEW_FILES 는 오케스트레이터 처리, 미접촉).

## 2026-09-12 (8) -- `jp/jesr_detail.json` 신규 조립 (publishing)

- 티켓 `inbox/publishing/20260912T1120Z__owner__JP_MULTI__jesr_detail_json.md`(answered). owner: "2개사에 대해 K-ICS.html 에
  대응되는 페이지 만들어라" — `jp/company.html`(designer 병렬 티켓 `inbox/designer/20260912T1120Z__..._jesr_company_page.md`,
  이 세션은 미접촉)이 fetch 할 회사별 상세 데이터.
- 신규 `J-ESR/build_jesr_detail_json.py`(stdlib only, self-check 내장 — 실패 시 exit 1). 입력: `extracted_sample_values.json`
  (이미 존재, 없으면 `extract_esr_template_samples.py` 자동 선실행) · `esr_disclosure_schema.json`(137 items) ·
  `esr_aggregation_rules.json`(포인터로만 읽음 — known_deviations 는 이미 각 check 의 note 필드에 반영돼 있어 재병합하지 않음) ·
  `jp/jesr_esr.json`(self-check 대조 소스).
- `census.status == "posted"` 인 2사만 채택(au_nonlife·meijiyasuda_nonlife). nnlife 는 ESR 미공시(`not_yet`)라 제외.
- **source_url/doc_type/doc_date/preliminary 는 `J-ESR/jesr_master.json` 에서 조인.** `jp/jesr_esr.json` 은 부모-자회사 중복
  제거(2026-09-12 (3) 항목, archive 이관)로 明治安田損害保険 을 `_meta.excluded_subsidiaries` 에만 `esr_pct` 없이 남겨 저 4필드가
  비어 있다 — `jesr_master.json`(제외 전 15사 원본)에서 회사명(`company_en`)으로 조인해 채웠다. au_nonlife 는 두 파일 값이 동일함을
  확인(중복 아님).
- 계약 고정 키(designer 와 확정, 리네임 금지): `risk` 블록은 `rc_diversification`→`diversification_effect`,
  `rc_tax_effect`→`tax_effect` 로 표시 키를 바꿔 매핑(값은 그대로), `market_sub` 6항목, `sensitivity[]`(scenario 별
  `delta_pp`=기준 대비, `base` 시나리오·미공시 값은 제외), `aggregation.deviations`(informational 실패 체크만, hard fail 은
  자동으로 0 이라 `reproduced`=true).
- 실측(exit 0): au_nonlife esr_pct=791.7·eligible=9,278·required=1,171·reproduced=true·checks=43/43·deviations=0(민감도
  공시 생략사라 sensitivity=[]) / meijiyasuda_nonlife esr_pct=743.2·eligible=40,290·required=5,420·reproduced=true·
  checks=49/51·deviations=2(`G06_nonlife` 다지역 상관통합 순서 차이·`G07_catastrophe`, 둘 다 `esr_aggregation_rules.json
  known_deviations` 등재분과 동일)·sensitivity=7행(엔금리+50bp→esr_pct 736.7/delta -6.5pp 등, 티켓 예시값과 정확히 일치).
  `_meta.coverage`={detail_posted:2, posted_total:13(=`jp/jesr_esr.json` records 길이), census_total:79}.
- self-check 4종 통과: companies==2 · 각 headline.esr_pct 가 `jp/jesr_esr.json`(records ∪ excluded_subsidiaries) 대조 일치 ·
  `risk.rc_post_tax == headline.required_capital` · `items` 의 모든 id 가 `_meta.labels` 에 존재 · 단위 무변환 통과(items.eligible_capital
  == headline.eligible_capital, 억엔 환산 없음).
- 파일 위생: BOM 없음(`xxd` 첫 바이트 `7b0a`=`{\n`) · `ast.parse` 통과 · `git status --short J-ESR/ jp/` = 신규
  `build_jesr_detail_json.py`·`jp/jesr_detail.json` 뿐(루트 마스터·xlsx·public_exports·keep-list·HTML 무변경; `jp/_fixture_jesr_detail.json`
  은 designer 병렬세션 산출물이라 손대지 않음).
- 배포 준비만: `scripts/android_push_and_deploy.sh` `NEW_FILES` 한 줄에 `jp/company.html jp/jesr_detail.json` 추가. 실제 push 는
  `jp/company.html` 완성 + owner 승인 후 별도 라운드.
- 재현: `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_detail_json.py`.

## 2026-09-12 (7) -- 소요자본 합산 규정(상관행렬) 기계화 + √(xᵀRx) 재계산 검산 (jp)

- 티켓 `inbox/jp/20260912T1005Z__owner__JP_MULTI__esr_aggregation_rule.md`(answered). owner 지적: 직전 티켓이 "부모 ≤ Σ하위" 부등식으로 끝냈는데
  당연히 상관행렬 통합이니 규정을 찾아 공시 합산액이 재현되는지 검산해야 한다(K-ICS mmult 검산과 같은 것).
- 규정 원문 확보 `J-ESR/raw/regulation/`: 令和7年金融庁告示第74号(1柱, 167p, fsa.go.jp 통합본 — 2026-03-23 개정 반영 확인)·第75号(3柱 별지양식,
  67p — curl 35KB 절단이라 WebFetch 바이너리 저장본)·令和8年告示第6号(개정 8p, 합산 조문 무변경). 미확보 4건(概要·Q&A·필드테스트 仕様書·3柱
  개정)은 curl 000 으로 남김, 추정으로 채우지 않음.
- 기계본 `J-ESR/esr_aggregation_rules.json`: 최상위 第155条 행렬(生保–損保 0.00, 그 외 0.25) + オペ 선형가산, オペ 상한 第154条(20%×(√+G)),
  세효과 第156条(0.8×法定実効税率×(√+F+G) vs DTA 분기 min), MA 上限超過 第46条, 生保 第81条(死亡–長寿 −0.25 등), 損保 第89条 4단계+別表七,
  巨大災害 第100条(0.00), 市場 第127条(스프레드 上昇/下降 2행렬, 資産集中 0.00), 信用 第128条 단순합, 分散効果 정의(75호 注 6(5)),
  공시 하위행 정의(注 3(2)·4(4)), MA 행은 정보행(注 6(3)). known_deviations 등재부 포함.
- `extract_esr_template_samples.py`: `run_aggregation_checks` G01~G10(gate/informational 구분, known_deviations lookup), `rc_life_*` 6 id
  추가(스키마 esr 109→115, K-ICS 29/30/31/33/34 대응, `stop_before` 로 생보 MA 행이 巨大災害 MA 행을 삼키는 사고 예방). exit 0.
- 재현: 分散効果 au 273.6/274·MY 2,529.5/2,530, 세효과 두 회사 ±1(역산 세율 28.0%), 시장 MY 4,611.8/4,613, au 損保 정확, au オペ 20% 캡 바인딩.
  미재현: MY 損保 +41(다지역 구조, informational 규칙) · MY 巨大災害 +109(注 4(4) 위반 방향 — `その他の巨大災害` 단순합 가설, 10월 재확인).
- 문서: `docs/domains/jp_esr_disclosure_template.md` §8 신설 + §0/§3/§4/§6/§7-4 동기, `claude-agent-jp.md` §3 포인터.

## 2026-09-12 (6) -- ESR 규제 공시 양식 지도 + 기계 스키마 + 표본값 (jp)

- 티켓 `inbox/jp/20260912T0905Z__owner__JP_MULTI__esr_disclosure_template_map.md`(answered). owner 취지: 10월 말 62사가 낼 규제 양식
  (令和7年金融庁告示第74号·第75号)을 지금 표본 2건으로 해부해 두면 회사마다 다른 표를 같은 열로 뽑을 수 있다. 발주 직후 범위 확장(6~8번):
  `kics_item_ref` 열, 기사 3축(異常危険準備金·재보험/AIR·基礎利益/逆ざや) 같은 문서에서 추출, 생보 표본 NN Life 추가, 생보/손보 양식 차이.
- 산출: (A) `docs/domains/jp_esr_disclosure_template.md` (B) `J-ESR/esr_disclosure_schema.json` (C) `J-ESR/raw/fy2025_samples/extracted_sample_values.json`
  + 생성기 `J-ESR/extract_esr_template_samples.py`(fitz, NFKC 정규화, 라벨 순차 커서, 절사 구간 검산; exit 0 게이트). 스크래치 `_item_table_fragment.md` 는
  생성기가 다시 만드는 문서 조각.
- 실측: 스키마 131항목(esr 109 / article_axes 22). 검산 C01~C34 + A01~A05: au 34/34, Meiji Yasuda Non-Life 41/41, NN Life 4/4. census 헤드라인
  791.7 / 743.2 일치, NN `not_yet` 일치.
- 규칙으로 승격한 발견: ① `esr = 適格資本/所要資本` 는 百万円 절사 때문에 소수 첫째자리 반올림으로 안 맞고 구간 [E/(R+1), (E+1)/R] 로만 맞는다.
  ② 리스크 부모(損保·巨大災害·市場)는 Σ하위보다 작다(상관 통합) — 등식 검산 금지. ③ `Tier1 基礎項目 == EBS 純資産`, `EBS 純資産 = 회계 純資産 +
  規制上の準備金 + 経済価値調整額` 이 T2↔T4 교차 게이트. ④ 정성 플래그는 정성 페이지에서만 검색(전체 문서 검색 시 T3 행 라벨 `マネジメント・
  アクションの効果の額` 에 걸려 "적용" 오판 — 실측 후 수정). ⑤ au 는 EBS 빈 행을 생략하므로 미매치 = 0 으로 허용(`ROW_OMITTED`).
- 편차·한계는 티켓 답변란과 문서 §7. MY 3축은 별책에 없어 본편 미열람(로컬 3건 조건). `calc_method=standard_implied` 는 추정.
- `docs/domains/claude-agent-jp.md` §3 에 양식 지도 포인터 1줄 추가.

## 2026-09-12 (5) -- `jp/index.html` ESR 랭킹 ECharts 가로막대 → 루트 모바일 리스트 이식 (designer)

- 티켓 `inbox/designer/20260912T0810Z__owner__JP_MULTI__jesr_jp_page_v3_korean_list.md`. owner 지적 원문 취지: "한국
  insurequant 모바일 리스트(막대) 레이아웃을 그대로 쓰면 되는데 왜 새로 ECharts 막대를 만들었나. 기준 하나 정해서
  그보다 높으면 진한 초록, 낮으면 진한 빨강이 더 직관적이다."
- **삭제**: `#esrChartLife`/`#esrChartNonlife` echarts 컨테이너·CSS(`#esrChartLife, #esrChartNonlife{width:100%}`)·
  `renderChart()` 전체(그리드/축/툴팁/시리즈 옵션, target 삼각 마커 scatter 시리즈 포함)·`chartInst`·`GROUP_COLOR`·
  `isMobile()`·`parseTargetNum()`·`debounce()`·resize 리스너(리스트는 뷰포트 무관 렌더라 불필요, 위 4개 함수는 이
  변경으로 orphan 이 돼 같이 제거).
- **이식**: 루트 `index.html` 82~98행 `.map-list`~`.li-chip` CSS 블록 + 877~948행 `renderList()` + 531~547행
  `_ratioHsl()`/`colorForRatio()` 를 그대로 복사. id 만 jp 스코프로 조정(`esrListLife`/`esrListNonlife`). 원본의
  `#bubble-list .li-name{display:flex}`(칩 병기용 변형)을 jp 의 기본 `.li-name` 규칙으로 채택 — jp 리스트는 速報 칩이
  항상 붙을 수 있어야 하므로.
- **색 상수**: `RATIO_SCALE={esr:{base:100,strong:300}}`. base=일본 금융청 감독기준 100%(미달 시 早期是正措置 대상),
  strong=규제수치 아닌 표시용 끝점(13사 분포 p90≈300 — 루트 kics 색상의 p90 채택과 같은 근거). 상수 옆 2줄 주석으로
  이유 명시(티켓 지시).
- **fold**: FOLD=5 더보기를 `isMob` 조건 없이 데스크톱·모바일 모두 적용(jp 기존 동작 유지 — 원래도 isMob 체크가
  없었다). 生保 9사→top5+더보기, 損保 4사=버튼 없음(≤FOLD). 리스트·표는 `expanded{life,nonlife}` 상태 공유(기존과 동일).
- **인터랙션 제거**: 루트는 행 클릭/`role="link"`/`tabindex`/keydown 으로 K-ICS.html 상세로 이동하지만, jp 에는 상세
  페이지가 없어 이 부분은 이식하지 않음(티켓 명시). `title`/`aria-label` 에는 이전 echarts 툴팁 내용(ESR·範囲·基準日·
  算定基準)을 요약 텍스트로 유지. `.li-row` 의 `cursor:pointer`/`:active` 도 복사하지 않음 — 클릭 동작이 없는데
  포인터 커서를 남기면 오탐 어포던스가 되므로(직접판단, 렌더링되는 수치·레이아웃 변경 아님).
- **▲目標水準 제거**: 리스트에 마커 자리가 없어 표(一覧表) 備考 열에 `目標 190%+`(`target_pct` 그대로) 텍스트로 이관.
- **범례**: 業態 색상 스와치(生保 파랑/損保 주황) 제거 → 감독기준 색 설명 2줄("監督基準100%以上ほど濃い緑"/
  "監督基準100%未満ほど濃い赤")로 교체. 상단 설명 문단도 "色は業態、▲は目標水準" → "色は監督基準(100%)を…" 로 수정.
- **검증**: `python -m http.server 8896`(기존 실행 중) + Claude Browser preview, 데스크톱 1280px·모바일 375px 렌더
  확인(콘솔 에러 0 — jsdelivr `ERR_NETWORK_ACCESS_DENIED` 는 이 PC 크로미움 공통 현상으로 echarts CDN 못 받는 도넛만
  영향, 순수 CSS 인 리스트는 무관). 더보기 클릭 → 生保 9사 전체 펼침 + 표 동시 펼침 확인(DOM 텍스트로 회사 9개 전부
  대조). `scripts/a11y_contrast_check.py contrast "#212529" "#ffffff"` → 15.43:1(AA, `.li-name`/`.li-val`).
  Playwright(headless, CDN 차단 없어 도넛도 렌더) 로 `artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png`
  덮어씀 — 이번엔 실제 막대가 스크린샷에 보임(직전 (4) 의 echarts CDN 차단 문제가 애초에 구조적으로 사라짐).
- Status 아카이브: `TODO_jp.md` Status 최신 5개 유지 원칙에 따라 가장 오래된 (1) FY2025 census 항목을
  `docs/todo_archive_jp.md` 신설 파일로 무수정 이관.

## 2026-09-12 (4) -- `jp/index.html` 2차 개선, owner 실사용 피드백 5건 (designer)

- 티켓 `inbox/designer/20260912T0530Z__owner__JP_MULTI__jesr_jp_page_v2.md`. owner 가 초안(2026-09-12 (2))을 직접 보고
  지적. `jp/jesr_esr.json` 은 publishing 작업(위 (3))으로 이미 13사(부모-자회사 중복 2건 제외) 상태 — 이 페이지에서
  재필터링하지 않고 그대로 fetch.
- **① 정렬 2단 버킷**: `isBucketA(category)` = `/^(HD上場|相互会社|上場)/` 매칭 여부로 버킷A/B 분리, 각 버킷 내
  `esr_pct` desc, `sortBucketed()`. 실측: 生保 9사 전원 버킷A(相互会社/上場/HD上場)라 사실상 esr_pct 단순 desc과 동일하게
  나옴. 損保 4사는 SOMPO/東京海上/MS&AD(버킷A, HD上場) 뒤에 au損害保険(버킷B, `子会社(KDDI)`)이 esr_pct 791.7%로
  압도적 1위임에도 맨 뒤로 밀림 — 의도된 동작(총자산 미공시라 category 로 "주요 시장 플레이어 vs 자회사"를 대신 구분).
- **② sector 별 top5+더보기**: `FOLD=5`, 루트 `index.html` MOB-INDEX-FOLD 패턴(버튼 텍스트만 이 페이지 UI 언어에 맞춰
  일본어 "もっと見る（他N社）"/"閉じる"로 현지화). `groupKey()` 로 reinsurance 를 nonlife 섹션에 합류(현재 0건, 10월
  재census 대비 미리 배선). ESRランキング(차트)·一覧表(표) 두 section 모두 生保/損保 서브섹션으로 재구성, 섹션당 버튼 1개씩
  총 4개지만 `expanded{life,nonlife}` 상태를 공유해 차트/표 어느 버튼을 눌러도 같이 펼쳐짐/접힘. 損保(4사)는 FOLD 이하라
  버튼 자체를 렌더링 안 함(`btn.hidden=true`). **함정 재확인(claude-agent-designer.md §4)**: `.more-btn{display:block}`
  이 특이도 동점으로 UA 기본 `[hidden]{display:none}` 을 이기므로 `.more-btn[hidden]{display:none}` 가드 명시 추가.
- **③ 出所 열 제거 + 공시일자 링크**: 표 헤더 6번째 열을 `出所`→`公表日` 로 교체, 셀 내용을 `doc_type` 텍스트가 아니라
  `jaDateFlexible(doc_date)` 텍스트에 `source_url` 링크(`target="_blank" rel="noopener noreferrer"`, aria-label 에 회사명+
  doc_type(있으면) + "별タブで開く" 유지). `基準日`(as_of) 열은 그대로.
- **④ 연결 시각 인코딩 제거**: ECharts bar `itemStyle.decal`(빗금) 및 범례 `グループ連結` 항목 삭제, `.hatch-sw` CSS 도
  같이 제거(내 편집으로 인한 dead code). `scope` 값은 表 範囲 열(기존 그대로 유지, 원래도 있었음)과 차트 tooltip 신규
  1행(`範囲: 連結/単体`)으로만 텍스트 유지. 차트 bar 색상도 sector 개별색이 아니라 GROUP_COLOR(섹션당 단색, 생보=blue,
  손보=orange)로 단순화 — 섹션 헤더가 이미 業種을 명시하므로 bar 색은 섹션 식별용으로 충분.
- **⑤ 速報 배지**: 무변경.
- 검증: `python -m http.server 8896` + Playwright(`sync_playwright`, chromium) 로 DOM 텍스트·정렬 순서·fold 버튼
  라벨·hidden 상태를 확인(get_page_text 로 生保 top5 순서·損保 4사 全出·표 공표日 링크 텍스트 실측 일치). 콘솔은 이
  세션 진행 중 `cdn.jsdelivr.net`(echarts/pretendard) 이 간헐적으로 `ERR_NETWORK_ACCESS_DENIED` — **jp 페이지만의 결함이
  아님**: 같은 순간 무수정 상태의 루트 `index.html`(같은 CDN 참조)도 동일 에러 재현(`root_verify.py`), 재시도해도 같은
  프로세스 내에서는 지속(브라우저 프로세스 단위로 걸리는 현재 네트워크/보안에이전트 상태로 추정, `project_pc_cannot_push`
  메모리의 "VPN 끄면 외부443 WSAEACCES" 와 정합). ECharts 막대 시각 자체는 이번 세션에서 렌더 확인 불가(canvas count=0,
  `window.echarts===undefined`) — 로직(정렬 리스트→bar/scatter 데이터 변환, aria-label 갱신)은 코드로 확인, 다음 세션
  네트워크 정상화 시 재스크린샷 권장. 데스크톱 1280px·모바일 375px 스크린샷은
  `artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png` 덮어쓰기(레이아웃·표·버튼은 정상 렌더 확인됨).

### 종결 재확인 (orchestrator, 같은 날)

designer 가 "다음 세션 재확인 권장"으로 넘긴 ECharts 렌더를 orchestrator 가 즉시 재검증했다 — echarts.min.js
로컬 임시 사본(검증 후 삭제, `jp/index.html` 은 시종 CDN 참조만 유지, git diff 로 확인)으로 실제 렌더 확인.
2단 정렬(au損害保険 損保 최하단 이동)·top5 폴드·빗금 제거 전부 스크린샷으로 육안 확인. 그 과정에서 **버그 1건 추가
발견·직접수정**: 모바일(375px) 生保 차트 x축 눈금이 값 범위(0~333%)에 눈금 8개가 좁은 폭에 들어차 "50%00%050%060%090%00%"
로 겹쳐 읽을 수 없었음(원인: `xAxis.axisLabel` 에 겹침 방지·모바일 눈금수 조정이 없었음). `hideOverlap:true` +
모바일 `splitNumber:4`(데스크톱 6 유지)로 수정, "0% 100% 200% 300% 400%" 정상 표시로 재확인.
스크린샷 재덮어쓰기(같은 파일명). 티켓 `status: resolved` 로 종결.

## 2026-09-12 (3) -- `jp/jesr_esr.json` 부모-자회사 중복 제거 (publishing)

- 티켓 `inbox/publishing/20260912T0530Z__owner__JP_MULTI__jesr_dedup_parent_subsidiary.md`. owner 실측 지적: 소니생명保険(solo
  162%)의 parent 소니FG(group 177%, posted), 明治安田損害保険(solo 743.2%)의 parent 明治安田生命保険(group 208%, posted) —
  같은 자본이 두 단위(개별법인/그룹연결)로 두 번 랭킹에 올라가 있었음.
- `J-ESR/build_jesr_page_json.py` 에 `apply_subsidiary_dedup()` 추가. 회사명 하드코딩 없이 일반 로직: census `category` 가
  "子会社"로 시작하는 posted 행에 대해, `jp_insurers.csv` 의 `parent_group` 을 다른 posted `company_jp` 안의 (직접 또는
  "HD"→"ホールディングス"/"FG"→"フィナンシャルグループ" 확장) 부분문자열로 매칭 — 걸리면 그 자회사 행을 `jp/jesr_esr.json`
  에서만 제외. `J-ESR/jesr_master.json` 은 15사 전부 그대로(정본).
- self-check 을 "두 파일 바이트 동일" 에서 "master 레코드 수 - 제외 수 == deploy 레코드 수" 로 교체. `_meta.excluded_subsidiaries`
  신설(deploy 파일에만, company_en·parent·esr_pct 3필드, 화면 미사용·감사용).
- 실행 결과: `jesr_master.json` 15 레코드 유지, `jp/jesr_esr.json` 15→13 레코드. 제외 2건 = Sony Life Insurance(parent Sony
  Financial Group) · Meiji Yasuda Non-Life(parent Meiji Yasuda Life Insurance). au Non-Life(parent KDDI, 보험사 아님·미공시)는
  그대로 남음 — 재현: `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_page_json.py`.

## 2026-09-12 -- jp 레인 신설 + FY2025 ESR census 79사 + `/jp/` 초안

- owner 결정 3건: (1) J-ESR 소스 정본은 EDINET 이 아니라 회사별 공시 사이트 PDF(기한 2026-10-31) — 이전 세션 구두 결론이 repo 에 없어
  오케스트레이터가 EDINET 조회를 다시 제안하는 사고 후 재기록. (2) 일본 화면은 IP 차등·`.co.jp` 대신 같은 사이트 `/jp/`. (3) jp 는
  한국 stage 에이전트와 **별개 에이전트**로 부린다(한국 프롬프트 11만 자에 일본 언급 0건 — 비대화 + 규칙 오염).
- census: downloader 에이전트 2개(행 1~41 / 42~81) → `J-ESR/fy2025_esr_census_20260912.csv` 79사, posted 15 / not_yet 62 / not_found 2.
  posted 이상치 2건(au 791.7%·Meiji Yasuda Non-Life 743.2%) 원문 PDF fitz 재확인. `jp_insurers.csv` ir_url 41→2. 커밋 `ca54fca`.
- 초안: publishing 이 `J-ESR/build_jesr_page_json.py` → `J-ESR/jesr_master.json` + `jp/jesr_esr.json`(15사, preliminary 5), designer 가
  `jp/index.html`(일본어 UI, 요약 카드·ESR 랭킹 막대·커버리지 도넛·출처 표·hreflang). 기존 4페이지 무수정.
- 레인 뼈대: `docs/domains/claude-agent-jp.md`, `TODO_jp.md`, 이 파일, `inbox/jp/`, `.claude/agents/jp-collector.md`(로컬).
  `CLAUDE.md` 는 같은 날 룰만 남기고 202→94줄로 축약(전문은 `docs/claude-md-history.md`).

## 2026-09-01 -- 9월 말 킥오프 확정 (owner)

인스뉴스 기사(일본 금융청 2026 보험 모니터링 보고서) 계기. 상세 루트 `TODO.md` J-ESR 항목.

## 2026-07-21 -- MVP 페이지 revert (`167cba1`)

그룹 연결값 11사뿐이라 화면 보류(owner). 근거 메모리 `project_jesr_scope_timing`.

## 2026-06-24 -- 트랙 신설 (당시 downloader/parser 가 처리)

`docs/changelog_downloader.md` 2026-06-24 항목 2건 · `inbox/_resolved/2026062*__*jesr*` 8건.
