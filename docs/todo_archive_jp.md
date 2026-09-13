# TODO archive — jp 레인 (일본 ESR)

**🟢 2026-09-13 (21) J-GAAP 貸借対照表 요약 층 `bs` 신설 — 상세 10사 중 7사 extracted, T자형 BS 패널용 tree 18행·checks 3종(jp).**
티켓 `inbox/jp/20260913T1300Z__owner__JP_MULTI__jgaap_balance_sheet.md`(answered). `J-ESR/extract_bs.py`(신규, `extract_esr_template_samples.py` 헬퍼 재사용) →
`extracted_bs_values.json` → builder `build_bs_block()`+`BS_LABELS`+self_check(id↔labels·합계 3행, checks False 는 WARN) → `jp/jesr_detail.json` 10사 전부 `bs` 블록,
`_meta.coverage.bs_extracted=7`, SELF-CHECK OK. 손보 4사(au·TMNF·MSI·Sompo)+NN Life 는 단체 2개년 百万円 checks 3/3 True; 日本生命·明治安田生命은 5월 설명자료 연결 요약(億円→×100,
当期末만, group) 으로 equity 검산 True·준비금 검산 None. not_obtained 3(明治安田損保 별책엔 純資産 없음·住友生命 요약 없음·第一生命 PDF 없음). 함정 3: NN Life `△ 7,608`
부호 뒤 공백, MSI 「純資産の部資本金」 라벨 접합, Sompo 資本剰余金/利益剰余金 은 合計 행에만 값. 문서 §12. 32분(상한 30분 소폭 초과). 다음 = 오케스트레이터 `jgaap.html` T자형 렌더.

**🟢 2026-09-13 (20) 損益表 상단을 元受収支 / 再保険収支 두 블록으로 + 出再保険手数料 추출(5사) — `jp/jesr.html`·builder·extractor(jp).**
owner "원수/수재/출재를 상대방 기준으로 묶자 → 수재는 출재 재원이니 元受·再保険 둘로" + "출재보험수수료(재보험자→출재사)도 재보험 수지에". extractor 에 `src:"note"`
2항목(`pl_commissions_gross`·`pl_ceded_commission`, 注記 단년 → prev 없음, P16 ±1 5/5 통과, au 제어문자 \x08 함정), builder `NONLIFE_PROFIT_FLOW` 를
`pf_direct_balance`/`pf_reins_balance`(row.parts 로 구성항목)/`pf_commissions_row`(총액)/`pf_uw_other_residual`(잔차) 로 교체 — 종전 `underwriting_ok` 는
5사 전부 False 였음(積立·準備金 행 누락) → 잔차 행으로 닫고 checks 는 bridge 3종으로. 화면 각주(풀 경유·前期 공란·잔차 정의). 실측 TMNF FY2025 元受収支
1조3,939억엔 / 再保険収支 △2,016억엔(手数料 505억엔 포함). 문서 §9-7-b. **다음**: FY2024 出再保険手数料(前期欄) 는 전년 결산단신 注記 — 10월 재조사 때.

**🟢 2026-09-13 (19) 손보 5사 종목별 층 `by_line` + 생보 5사 기초이익·三利源 `core_history` → `jp/jesr_detail.json` 10사(jp).**
티켓 `inbox/jp/20260913T0400Z__owner__JP_MULTI__lob_ratios_and_life_margins.md`(answered). owner "손해율·사업비율·합산율이 종목별로 찢어져 있지 않나? 생보는
이차·사차·비차 마진 통계가 있을 것" → ① 「保険引受の状況」 種目別 3표(正味収入保険料/正味支払保険金/比率)에서 火災·海上·傷害·自動車·自賠責·その他·合計 ×
{prev,cur} 5항목(`lob_*`), 5사 gate 실패 0(B01 Σ종목=合計 는 6개 종목 각각 百万円 절사라 ±1 불가 → tol 6, 실측 차 0~3 / B02 合計=profit 층 30/30 / B03 종목 合算率
항등식 전부 통과 / B04 정보성: TMNF その他 FY2025 損害率이 두 표에서 52.9 vs 55.0 — 원문 차이, 比率표 정본). au 는 자동차 0·傷害 78.6%(티켓 가정과 다름), 自賠責은
4사 合算率 118~140%. ② 생보: curl 전 도메인 차단 → WebFetch 바이너리 저장으로 住友生命·日本生命·明治安田生命 결산설명자료 확보(`others/`), 第一生命 404 2회
미확보(행 보존). **三利源 3분해 공시 0사** — 利差(順ざや)+保険関係(危険差+費差) 2분해가 표준, 住友生命만 「うち危険差」로 費差 파생 가능(L01 基礎利益≈Σ ±2 통과),
5개년은 住友 그룹 기초이익만, 明治安田는 基礎利益 대신 業務利益. 5월 설명자료 기준이라 7월 본편에 三利源·5개년 표 가능성 남음(10월 재census). ③
`extract_life_core_history.py`(신규, fitz words 위치 파싱)·builder `build_by_line_block`/`build_core_history_block`·생보 `esr_status:"life_core_only"`·self_check 확장,
`_meta.coverage` detail_total 10 / esr_posted 2 / esr_not_yet 3 / life_core_only 5 / by_line_total 5, SELF-CHECK OK. 문서 §11·§9-9. 45분 규칙 10분 초과(생보 URL 탐색).
`jp/*.html`·커밋·서브에이전트 없음. 다음 = 오케스트레이터 화면(`by_line.labels_ja`·`_meta.labels.hist_*`).

**🟢 2026-09-13 (18) 대형 손보 3사(東京海上日動·三井住友海上·損保ジャパン) ESR 외 전 층 추출 → `jp/jesr_detail.json` 5사(jp).**
티켓 `inbox/jp/20260913T0330Z__owner__JP_MULTI__big3_partial_detail.md`(answered). owner "손해율 있다면서 왜 사이트엔 2사만" → (17)에서 확보한 본편 3 PDF 에서
profit(損益計算書·保険引受利益 明細·損害率/事業費率/合算率·재보험 다리 6항목)·history 5개년·article_axes(異常危険準備金/普通責任準備金·出再先数/上位5社/格付)·회계기준을 추출,
`extract_esr_template_samples.py` 에 3사 배선(id `tokiomarine_nichido`/`mitsui_sumitomo`/`sompo_japan`). **실측: 3사 profit 31/31·history 10/10, 게이트 실패 0, exit 0**;
`build_jesr_detail_json.py` 가 ESR not_yet 회사를 허용(headline ESR null·트리 빈 리스트·self-check 분기), `_meta.coverage` = detail_total 5 / esr_posted 2 / esr_not_yet 3,
SELF-CHECK OK. 기존 2사 블록·`_meta.labels` 무변경(추가 키 `esr_status`/`esr_placeholder` 뿐, 스크립트 diff 확인). FY2025 合算率 TMNF 93.0 / MSI 93.2 / Sompo 97.0,
当期純利益 731,125 / 459,965 / 295,649 百万円, 出재 비중 17.0 / 20.6 / 16.4%. 발견 5건: ① TMNF·Sompo 元受 표는 含む収入積立保険料 뿐 → P&L 収入積立保険料 를
adjustments 로 뽑아 P14 차감(추정 없음) ② P07 에 `−その他収支` 누락(TMNF −3,152 에서 드러남, au/Meiji 불변) ③ 본편 뒷부분 그룹 연결 IFRS17 때문에 単体 회계기준이
ifrs 로 오판 → IFRS 검색을 basis 페이지로 한정 ④ Sompo 폰트 함정은 숫자만이 아니라 한자·가나 전부 글리프 id — MS Gothic 글리프 순서와 일치해 로컬 msgothic.ttc
cmap 으로 복원(`GidDoc`) ⑤ MSI 5개년표는 p31 에 있음(직전 티켓 "없음" 오판, 損害率 2자리 소수·SMR 新旧 쌍 구조). 커밋 e67bc36 이 손으로 고친 `_meta.labels`
4개는 builder `LABEL_JA_DISPLAY_OVERRIDES` 로 고정. 문서 §9-8·§10-8. `jp/*.html`·커밋·서브에이전트 없음. 다음 = 오케스트레이터가 `jp/jesr.html` 을 5사·not_yet 분기로.

**🟢 2026-09-13 (17) 손보 6사 표본 실측(정본 3사 확보) — 손해율/사업비율/합산율 5개년표는 owner 가정대로 이미 공시, ESR 만 표본 전원 미공표(jp).**
티켓 `inbox/jp/20260913T0230Z__owner__JP_MULTI__nonlife_ratio_availability.md`(answered). owner "손해율 5개년이 다른 손보사에도 다
있는지" → 대형4(東京海上日動·損保ジャパン·三井住友海上·あいおいニッセイ同和)+중형2(共栄火災·日新火災) 표본 중 세션 중반 curl 이 전
도메인 차단(`google.com` 포함)으로 바뀌어 **3사만 원문 확보**(Tokio Marine & Nichido Fire·Mitsui Sumitomo Insurance·Sompo Japan
Insurance, `J-ESR/raw/fy2025_samples/others/`). 확보 3사 전부 손해율/사업비율 5개년(또는 3개년) 시계열 실측 완료: TMNF FY2025
損害率61.6%/事業費率31.4%(合算率 행 없음, 파생93.0%), MSI 3개년표 合計행 FY2025 損害率62.8%/事業費率30.4%/**合算率93.2%(직접공시)**,
Sompo Japan 5개년표 FY2025 損害率63.8%/事業費率33.3% + 별도 3개년표 合算率(合計행)97.0%. **ESR 은 3사 전부 not_yet**(2026年10月末),
문구는 회사마다 신규 변형 3종(TMNF 표셀 "別時期での開示", Sompo 각주 "…の予定です", MSI 각주 "…開示します") — `esr_disclosure_schema.json`
`esr_status`/`hist_combined_ratio_pct` labels_ja 에 반영(合算率 단독 라벨도 추가). Sompo Japan PDF 는 숫자/기호가 U+3EDC 대역
+16044 오프셋 PUA 로 추출되는 폰트함정 발견(디코더 필요, 문서에 재현법 기록). 미확보 3사(Aioi·Kyoei·Nisshin)는 사유 남기고 행 보존
(Aioi=PDF링크 미발견, Kyoei=도메인 접속거부, Nisshin=URL은 WebSearch로 특정했으나 curl 차단으로 원문 미열람). census csv 4행
(disclosure_url·checked_at·notes) 갱신, `docs/domains/jp_esr_disclosure_template.md` §10-7 신설. `jp/*`·builder·서브에이전트·
커밋·git push 없음.

**🟢 2026-09-13 (14) jesr.html 한 표([+] 펼침)·손익 선별·재보험 다리·収益性指標 + 자회사 dedup 해제 — 라운드 종결(orchestrator).**
owner 피드백: 자본표 부호/계층, 보험·대재해 하위 미표시(괘씸), 손익 항목 선별, 손해율 별도, 원수/출재 분해, 자회사 삭제 이유(한국은 교보생명·교보라이프플래닛
각각) → K-ICS.html 방식 단일 표(capital_tree+risk_tree), profit_flow+다리, 収益性指標(5개년 SVG), SUBSIDIARY_DEDUP=False(15사). designer 2회 시간 초과(32+13분)로
orchestrator 직접 구현(88595f4). 교훈: jp HTML 은 ECharts 검증 루프 때문에 designer 라운드가 45~57분 — 다음부터 jp 차트는 SVG/CSS 만, 티켓은 DOM 검증만.
다음 = 번들(비공개 경로 jp-f9027362/) → owner 확인.

**🟢 2026-09-13 (16) `jp/jesr_detail.json` 에 `capital_tree`·`risk_tree`·`profit_flow` 구조화 블록 추가 — 2사 실측, underwriting_ok/net_ok 는 실제 갭으로 false(publishing).**
티켓 `inbox/publishing/20260913T0005Z__owner__JP_MULTI__jesr_detail_trees.md`(answered). owner 09-12 피드백(① 자본구성표 하위합≠상위 ②
보험/대재해 하위분해 안 보임 ③ 손익 항목 선별 나쁨 ④ 손해율 별도패널)의 데이터 쪽. `J-ESR/build_jesr_detail_json.py` 에 `build_tree()`(스키마
`parent`/`formula` 전위순회, `capital_tree`=`eligible_capital` 뿌리·`risk_tree`=`rc_pre_tax` 뿌리 공용) + `build_profit_flow()`(손보 13행 고정
흐름, `pl_other_ordinary`/`pl_extraordinary_net` 2개 파생 id — `_meta.labels` 에만 추가, 스키마 항목 정의는 무변경) 신설. 설계 결정 2개는 티켓
문구를 그대로 안 따르고 실측 근거로 바꿈(답변란에 상세): (a) `is_total` 을 "formula 보유" 대신 "스키마상 자식 존재"로 구조화 — tier1_ni_capital_surplus
등 3개 항목이 alias formula(`== ebs_*`)라 리터럴대로 하면 자식 0개인데 total 로 표시되는 오류 발생, 구조화 규칙이 이 alias 예외를 별도 코드 없이 자동
해결. (b) risk_tree 루트(9-term rc_pre_tax 공식) 재현 tolerance 를 ±1 고정 대신 `max(1, 항 개수)` 로 — 기존 추출기 자체 체크
`C12_rc_pre_tax` 가 이미 이 9-term 공식에 tol=9 를 쓰고 있음(각 항 절사 오차 누적), ±1 로는 au/meiji 둘 다 fail. **실측**(재현
`PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_detail_json.py`, exit 0,
SELF-CHECK OK): au capital_tree 14행·root check `9278=9102+175`(diff 1, tol 2) ok — risk_tree 12행·root check
`1510≈1119+87+247+78+251-274=1508`(diff 2, tol 6) ok, rc_nonlife/rc_catastrophe/rc_market 3개 correlated 노드의
simple_sum 이 기존 체크 C14/C15/C17 rhs(1190/87/247)와 정확 일치(교차검증) — meiji capital_tree 15행 root ok(diff 1,
tol 2), risk_tree 22행 root ok(diff 3, tol 6), rc_cat_natural 포함 4개 correlated 노드 전부 기존 C14-C17 rhs(2458/2666/
2523/7567)와 정확 일치. profit_flow: au 11행(`pl_underwriting_other`·`pl_extraordinary_net` 값 없어 missing 2), meiji 13행(missing
0). 검산 3개 — `ordinary_ok`=true 둘 다(설계상 항등, `pl_other_ordinary` 가 잔차로 정의돼 항상 닫힘) / `underwriting_ok`=**false 둘 다**
(선별 6행 합 vs 保険引受利益 차이 au 806~866·meiji 690~829, 원인 추정: 責任準備金等繰入額 등 스키마에 없는 保険引受費用 행이 원문엔 있음 —
`pl_underwriting_other`(その他収支) 는 실제로 작은 값이라 이 갭을 못 메움, 정직하게 false 유지·억지 보정 없음) / `net_ok`=**false 둘 다**(cur
기 特別利益 미공시로 `pl_extraordinary_net` cur 이 null → 그 항을 0취급하고 재현하면 diff 2(au)/20(meiji); meiji prev 만 단독 검산하면
1216+26-465=777=실측 net_income prev 일치). self_check() 는 root check 2개(capital/risk)와 ordinary_ok 만 하드게이트(모두 true 로 통과),
underwriting_ok/net_ok 는 실측치 그대로 JSON 에 싣고 게이트에는 안 건다(실제 데이터 공백이지 코드 버그가 아님). **부작용 확인**: `git diff`
상 `jp/jesr_detail.json` 의 나머지 차이는 전부 이번 세션 시작 전부터 워킹트리에 이미 있던 (15)번 재보험 브릿지 스키마/추출기 미커밋 변경분(내가
안 건드림, `git diff --stat HEAD -- J-ESR/esr_disclosure_schema.json` 이미 +107 줄) — 내 추가분은 `capital_tree`/`risk_tree`/`profit_flow`
3키 + `_meta.labels` 2개(`pl_other_ordinary`/`pl_extraordinary_net`) + `generated_at` 뿐. `jp/*.html`·스키마 항목 정의·커밋 없음.

> `TODO_jp.md` Status 최신 5개 유지 원칙에 따라 밀려난 항목을 한 글자도 고치지 않고 여기로 옮긴다.
> 최신이 위. 필요할 때만 연다(changelog 와 같은 원칙).

**🟢 2026-09-13 (15) 손익 층에 재보험 다리(bridge) 6항목 추가 — 元受/受再/出再 분해, 손보 2사 검산 P14/P15 전부 통과(jp).**
티켓 `inbox/jp/20260913T0025Z__owner__JP_MULTI__reinsurance_bridge.md`(answered). owner "정미(正味) 말고 원수(元受) 숫자를 따로 볼 수
없나" → 디스클로저지 「保険引受の状況」 6개 하위표(元受/受再正味保険料·支払再保険料, 元受/受再正味保険金·回収再保険金)에서 추출. `esr_disclosure_schema.json`
`layer:"profit"` 에 `table:"profit:bridge"` 6항목(`pl_gross_premiums_written`/`pl_assumed_premiums`/`pl_ceded_premiums`/
`pl_gross_claims_paid`/`pl_assumed_claims`/`pl_recovered_reinsurance_claims`, `{cur,prev}` 百万円) + 기존 `pl_net_premiums_written`/
`pl_net_claims_paid` 에 formula 추가(=元受+受再-出再). au 는 業績데이터 4of5 분책 p3~4(같은 분책, curl 불필요), Meiji Yasuda 는 본편
60p p33~34(§9-6 에서 이미 확보한 파일). `extract_esr_template_samples.py` 에 `extract_bridge_block()`/`_bridge_row_value()`/
`BRIDGE_ORDER`(회사별 6표 문서순서, au≠Meiji) — 각 항목은 "직전 항목의 合計 행 다음부터" 커서 전진 탐색(같은 라벨이 페이지 후반 각주에
재등장하는 함정 회피). **버그 1건 발견·수정**: 처음 `grab(..., stop=heading_idx+80)` 로 합계 탐색을 좁혔더니 `grab()` 이 `stop` 으로
라벨탐색과 값캡처 둘 다 잘라 au 保険料 두 항목이 빈 리스트로 나옴(P14 0/0 실패) → `stop` 제거(표 안 첫 合計가 항상 정답)로 해결.
**실측**(exit 0): au P14/P15 cur·prev 4/4, Meiji 4/4 — au 保険料 16,646+0-8,509=8,137(정미 실측 8,137과 정확 일치), Meiji
保険料 16,363+811-1,482=15,692(정미 실측과 정확 일치). 保険金 쪽은 백만원 절사로 ±1(au 9,595+0-7,655=1,940 vs 정미 실측 1,940
정확, Meiji 4,733+552-176=5,109 vs 정미 실측 5,108, ±1). au 受再(수재) 두 항목은 원문 `該当事項はありません` → 0(null 아님). 스키마 42항목(36+6),
`build_schema()` 자동생성이라 `pl_item_ref`/`table` 등 파생 필드 무손 반영. `docs/domains/jp_esr_disclosure_template.md` §9-7 신설(표·
검산·추출특이점·회사별 순서표). **`build_jesr_detail_json.py` 는 손대지 않음**(publishing 편집 중) — `_meta.labels` 는
`for it in schema["items"]` 로 스키마 전체를 자동 순회해 채우므로(434~446행), 오케스트레이터가 그 빌더를 재실행하기만 하면 새 6항목
라벨이 자동 추가됨(수동 등재 불필요). `jp/*`·builder·서브에이전트·커밋 없음.

**🟢 2026-09-12 (14) 스키마에 시계열 층 `layer:"history"` 13항목(FY2021~FY2025) + 손보 2사 5개년 추출·검산 H01~H02(jp).**
티켓 `inbox/jp/20260912T1440Z__owner__JP_MULTI__pl_history_5y.md`(answered). owner "손해율·사업비율·합산비율 시계열을 쭉 보여줘도
좋겠다" → profit 층({prev,cur} 2개년)의 확장. `J-ESR/esr_disclosure_schema.json` 에 history 13(값 10 + 생보 id 3개 정의만:
`hist_core_profit`/`hist_premium_income`/`hist_policy_reserves`), 값은 `{"FY2021":v,...,"FY2025":v}`. `extract_esr_template_samples.py`
에 `extract_history`/`run_history_checks`/`strip_paren`(괄호 안 숫자 vs 괄호 안 대시 구분) — profit 층이 이미 읽던
`profit_pages["summary5"]` 페이지를 재사용(문서 새로 안 염). **실측**(exit 0): au_nonlife 정미수입보험료/경상이익/당기순이익/
손해율/사업비율/총자산/순자산 5개년 전부 표에서 직접 추출(31.8/29.4/26.9/36.4/30.9 등), 합산율은 파생(=손해율+사업비율).
Meiji Yasuda Non-Life 는 손해율/사업비율/합산율이 5개년표 자체엔 없어 profit 층이 이미 읽는 3개년표(p35)에서 FY2023~2025 만
백필, FY2021~2022 는 null(로 남김, 억지 채움 없음). 단체SMR/ESR 행은 **괄호 유무로 구기준/신기준을 나눔**(Meiji: 괄호
4개=旧基準 2,847.6/2,940.4/2,814.7/2,642.5%, 비괄호 1개=신기준 743.2%; au: 旧基準 자리가 전부 대시라 `hist_smr_old_pct` 5개
다 null 이 정상, `hist_esr_pct` FY2025 만 791.7%). Meiji SMR 라벨의 "ー"(장음부호)가 대시 문자와 동일 코드포인트라
`merge_vertical` 이 라벨을 쪼개는 버그를 느슨한 부분일치 정규식(`HIST_SMR_LABEL_RE`)으로 우회. 검산: **au 17/17, Meiji
15/15**(H01 FY2025==profit.cur·FY2024==profit.prev, H02 合算率=손해율+사업비율 ±0.1) — `extract_esr_template_samples.py`
전체 게이트(all_checks)에 합류해 exit 0. `J-ESR/build_jesr_detail_json.py` 에 `build_history_block()` 추가(같은 값을
`fiscal_years`+`series`(연도 배열) 형태로 재편) + companies_out `history` 키 + self_check 에 같은 검산(구조 정합·FY2025/2024
교차·合算率 항등식) — exit 0, SELF-CHECK OK. `jp/jesr_detail.json` companies[].history 확인. 기존 esr/article_axes/profit
블록·키 바이트 무변경(스키마 diff = 신규 항목·layers/tables/column_note 설명문 추가뿐, `aggregation.checks_pass/checks_total`
만 (11) 항목과 같은 이유로 자연 증가: au 62→79, Meiji 66/70→81/85 — 이번 신규 H01/H02 가 같은 gate 에 합류했기 때문).
문서 `docs/domains/jp_esr_disclosure_template.md` §0·§10(표 위치·연도 수·라벨 렌더링 특이점·SMR/ESR 괄호 분리·검산·회사별
편차·중간기 공시 없음 메모). `jp/*.html`·서브에이전트·커밋 없음.

**🟢 2026-09-12 (12) `jp/jesr.html` 損益の内訳 패널 + 비공개 프리뷰 경로 + terms/GA/오류제보 팝업 — 라운드 종결(orchestrator).**
손익 패널: 会計基準 한 줄(J-GAAP·IFRS17 未適用)·当期純利益 워터폴(引受→運用→その他→経常→特別→法人税等△→純利益)·当期/前期/増減 표·損害率/事業費率/合算率·✓ 배지
(티켓 `inbox/_resolved/20260912T1330Z`). designer 가 CDN 우회 검증 반복으로 52분 소요 → 산출물 커밋 후 종료. 배포는 main 에서 `jp-f9027362/`
(비공개 프리뷰, `android_push_and_deploy.sh` JP_PRIVATE_DIR). 다음 = 게이트 → 번들 → owner 폰 배포 2회 실행.

**🟢 2026-09-12 (13) Meiji Yasuda Non-Life 본편 확보 후 profit 층 채움 — 25/25 추출, 검산 17/19(2건 informational), jgaap/ifrs17=false.**
티켓 `inbox/_resolved/20260912T1150Z__owner__JP_MULTI__profit_layer_schema.md` 말미에 "본편 확보 후 추가" 절 append(status 는
resolved 유지). owner 가 `J-ESR/raw/fy2025_samples/meijiyasuda_nonlife_20260729_main.pdf`(60p)를 직접 넣어줌. `extract_esr_template_samples.py`
에 페이지 매핑(pl=42·uw=36·ratio=35·summary5=9·basis=42,45, 인쇄쪽↔pdf인덱스 환산식)·`MEIJI_PL_FLAT_MAP`(損益計算書가 라벨 전체
나열 후 값 전체 나열하는 구획식이라 `pl_flat_tokens` 로 라벨 무시하고 고정 위치 120토큰 읽음)·`vertical_labels`(세로줄 라벨 렌더링
→ `merge_vertical` 을 uw/ratio 에도 적용)·`label_overrides`(스키마 정본 라벨은 안 바꾸고 회사별 別名만 추가)·`pl_investment_override`
(자산운용손익 이중계상 방지, 손익계산서 기준으로 대체)를 배선. **세션 중 소스 PDF 가 로컬에서 사라진 사고 발생**(홈 디렉터리
전체검색+git 이력 대조로 부재 확인, 애초 git 미추적) — 사라지기 전 읽은 원문을 `meijiyasuda_nonlife_main_pages_fixture.json`
으로 남겨 `main()` 이 실물PDF→fixture→NOT_ACQUIRED 순으로 재시도하게 배선(`FixtureDoc`), 이번 결과는 fixture 경로.
**실측**(exit 0, au 19/19·NN 12/12 무회귀 확인): meiji profit_items_nonnull=25/25 applicable, checks 17/19(P13 이자배당↔투자손익
2건만 informational, au 도 같은 사유), accounting_basis=jgaap/ifrs17_applied=false(B 티어: p42 법정 損益計算書 양식+p45
10.会計監査 会社法436条/保険業法111条). 경상이익 1,594(prev 1,216)·당기순이익 1,003(777)·보험인수이익 963(729)·손해율/사업비율/
합산율 37.7/51.7/89.5(38.3/51.5/89.8). 스키마(`esr_disclosure_schema.json`, 173항목) 바이트 무변경(`git diff --stat` 확인) —
라벨 별명은 회사별 `label_overrides` 로만, 항목 정의 무변경. `docs/domains/jp_esr_disclosure_template.md` §9-1·§9-6(신설: 페이지
매핑·라벨 렌더링 특이점·이중계상 발견·검산·회계기준·파일소실 사고). publishing 의 `jp/jesr_detail.json` profit 블록(TODO(11))은
Meiji 가 아직 not_obtained 로 박혀 있어 **재실행 필요**(후속 티켓, jp/ 미접촉 원칙상 이번 라운드에서 직접 안 돌림).

**🟢 2026-09-12 (12) `jp/terms.html`(利用規約·プライバシー) 신규 + `/jp/` 2페이지 GA4·CSP·푸터 링크·오류제보 팝업 + `jp/jesr.html` nit 3건(designer).**
티켓 `inbox/designer/20260912T1215Z__owner__JP_MULTI__jp_terms_privacy.md`(answered, 본문+추가 절). 산출: `jp/terms.html`(利用規約 第1~8条 +
プライバシーポリシー 1~8, 한국 `privacy.html` 구조 이식·著作権法 第12条/第12条の2·有料ライセンス 유보·運営者 표기는 第8条 한 문단에만·hreflang
ko=/privacy.html), `jp/report-widget.ja.js`(루트 위젯 복제·일본어화, 시트 `JP:jesr_esr|jesr_detail`, 회사 14·期 는 JSON `_meta.as_of` 에서 유도 — 리터럴
하드코딩 없음), `jp/index.html`·`jp/jesr.html`(CSP 루트 6행 동일 문자열 + GA4 iq_internal 스니펫 + 푸터 「利用規約・プライバシーポリシー」 +
`../forms-config.js`·`report-widget.ja.js`), nit ① 워터폴 yMin 0 고정(au △2.2→0·MY △11.5→0)·`(億円)` 제목 grid.top 40 ② 構成比 상위 3행만
총액 대비, 세부행 빈칸 ③ 375px `#capitalTable{min-width:0}` 로 금액·構成比 열 노출(마지막 열 우측 351.5px<375), 배포 스크립트 NEW_FILES +2.
**실측**: Playwright 3페이지×2뷰포트 콘솔에러 0(CDN 차단 ignore 외)·링크 전부 200·팝업 열기→빈 제출 오류→제출 시 `POST script.google.com/…/exec`
시도 확인·`label[for]` 18/18, echarts 는 이 PC 443 차단으로 setOption 스텁으로 옵션값 검증(2사×2뷰포트 yMin=0), `test_deploy_assets.py` 11 passed.
스크린샷 `artifacts/designer/jesr_jp_terms_mobile_20260912.png`·`jesr_jp_report_mobile_20260912.png`·`jesr_jp_jesr_mobile_nits_20260912.png`.
**owner 확인 대기**: 運営者 표기(Cho Sangwook 병기)·準拠法/관할(운영자 소재지 법원 초안)·GA 보유기간(最長14か月)·시행일 2026-09-12. 라이브 미반영.

**🟢 2026-09-12 (11) `jp/jesr_detail.json` 에 손익(`profit`) 블록 추가 — au_nonlife 정상 추출, meijiyasuda_nonlife not_obtained(publishing).**
티켓 `inbox/publishing/20260912T1240Z__owner__JP_MULTI__jesr_detail_profit_block.md`(answered). `J-ESR/build_jesr_detail_json.py`
에 `build_profit_block()` 추가 — 회사별 `comp["profit"].values/meta`(위 (10) 항목이 이미 추출해 둔 것)에서 조립, 다른 블록·키는
무변경(labels 에 `pl_item_ref` 필드만 전 항목에 균일 추가 — profit 36개는 값 채움, 기존 esr/article_axes 항목은 null). 스키마
`table` 태그로 그룹 분리: `items`=null 아닌 전체(`{cur,prev}` 쌍, 둘 다 null 이면 항목 자체 생략) · `ratios`=`profit:ratio`(손보
손해율/사업비율/합산율) · `core`=`profit:core`+`profit:three`(생보 基礎利益 분해+三利源, capital/risk 기존 관례처럼 items 의
부분집합을 다시 노출하는 편의 뷰) · `accounting_basis`/`ifrs17_applied`/`evidence`/`source_doc`/`unit`/`status`("extracted"|
"not_obtained", 판정은 `profit_source_doc` 이 `"NOT_ACQUIRED"` 로 시작하는지로 기계 판정). meijiyasuda 본편 PDF
(`…/pdf/20260729.pdf`)는 이번에도 로컬에 없어(`meijiyasuda_nonlife_20260729_main.pdf` 미확인) `extract_esr_template_samples.py`
재실행 스킵 — 기존 `extracted_sample_values.json`(status "not_obtained") 그대로 사용.
**실측**(재현 `PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_detail_json.py`,
exit 0): au_nonlife profit.status=extracted, accounting_basis=jgaap, ifrs17_applied=false, 経常利益(pl_ordinary_profit)
cur=1,654/prev=1,451, 当期純利益(pl_net_income) cur=1,171/prev=961, 合算率(pl_combined_ratio_pct) cur=71.1/prev=72.1(=損害率
31.8+事業費率 39.2, ±0.1 이내). meijiyasuda_nonlife profit.status=not_obtained, items/ratios/core 전부 `{}`, source_doc 에
NOT_ACQUIRED 사유 그대로. self-check 내장 통과: companies==2, au `pl_ordinary_profit`/`pl_net_income` 존재, 손보 合算率 항등식
cur·prev 둘 다 ±0.1 이내, meiji status=="not_obtained"+items=={}, profit 하위 모든 id 가 `_meta.labels` 에 존재(라벨 173개=
기존 137+profit 36). `git diff jp/jesr_detail.json` 로 부작용 확인: `generated_at` 갱신 외에는 (a) 모든 라벨에 `pl_item_ref`
추가(신규 필드, 기존 값 무변경) (b) `aggregation.checks_pass/checks_total` 이 43/43→62/62(au)·49/51→50/52(meiji) 로 증가 —
이건 이번 수정이 아니라 입력 `extracted_sample_values.json` 이 이미 (10) 라운드에서 profit 검산 19개(au)/1개(meiji) 를
포함하도록 갱신돼 있었기 때문(그 요약을 그대로 읽는 기존 로직, `aggregation` 필드 자체는 처음부터 esr 전용이 아니었음).
headline/risk/market_sub/capital/axes/sensitivity 등 다른 블록은 바이트 무변경. BOM 없음·`ast.parse` 통과.
`jp/*.html`·`esr_disclosure_schema.json`·루트 마스터 미접촉(designer 병렬세션이 같은 워크트리에서 `jp/index.html`·
`jp/jesr.html` 을 수정 중인 것을 `git status` 로 확인·미개입).

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

**🟢 2026-09-12 (5) `jp/index.html` ESR 랭킹 ECharts 가로막대 폐기 → 루트 `index.html` 모바일 리스트 그대로 이식(designer).**
티켓 `inbox/designer/20260912T0810Z__owner__JP_MULTI__jesr_jp_page_v3_korean_list.md`(answered). owner 지적: "한국 사이트
모바일 리스트 레이아웃을 그대로 쓰면 되는데 새로 ECharts 막대를 만들었다" → `#esrChartLife/Nonlife`(echarts bar) 전부
삭제, 루트 `index.html` 82~98행 `.map-list`~`.li-chip` CSS + 877~948행 `renderList()` + 531~547행
`_ratioHsl`/`colorForRatio` 를 그대로 복사해 `esrListLife`/`esrListNonlife` 로 이식. 색 상수만
`RATIO_SCALE={esr:{base:100,strong:300}}`(base=일본 금융청 감독기준 100%, strong=13사 분포 p90 표시 끝점). 데스크톱·모바일
모두 리스트(jp 는 트리맵이 없어 `.map-list{display:block}` 로 상시 표시), top5+더보기(FOLD=5, `isMob` 조건 없이 데스크톱도
적용 — 기존 jp 동작 유지) · 生保/損保 2섹션 · 速報 는 `.li-chip` 로 이름 옆에 이동. 행 클릭/role="link"/keydown 은 뺐다(jp
에 상세 페이지 없음, 티켓 지시) — `title`/`aria-label` 요약 텍스트만 유지. ▲目標水準 마커 제거, 表 備考열에
`目標 190%+` 텍스트로 이관(`target_pct`). 업태색 범례(生保/損保 스와치) 제거 → 감독기준 색 설명으로 교체. 편차 1건:
`.li-row` 의 `cursor:pointer`/`:active` 는 복사하지 않음(클릭 없는데 포인터 커서면 오탐 어포던스 — a11y 관점 직접판단,
값 변경 아닌 어포던스 수정). 정리(orphan 제거): `chartInst`/`GROUP_COLOR`/`isMobile()`/`parseTargetNum()`/`debounce()`
+ resize 리스너(리스트는 뷰포트 무관 렌더라 불필요). 검증: `python -m http.server 8896`(기존 실행 중) +
Claude Browser preview 로 데스크톱 1280px·모바일 375px 렌더 확인(콘솔 에러 0, jsdelivr `ERR_NETWORK_ACCESS_DENIED`
는 이 PC 크로미움 공통 현상— echarts CDN 못 받는 도넛만 영향, 순수 CSS 인 리스트는 무관하게 정상 렌더됨 확인),
더보기 클릭 → 9사 전체 펼침 + 표 동시 펼침 확인. `scripts/a11y_contrast_check.py contrast "#212529" "#ffffff"` →
15.43:1(AA 통과, `.li-name`/`.li-val` 글자색). Playwright(`C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`,
headless는 CDN 차단 없어 도넛도 렌더됨)로 최종 스크린샷 `artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png`
덮어씀(재현: 로컬 스크립트로 1280×1400 / 375×900 viewport full-page capture).

**🟢 2026-09-12 (4) `jp/index.html` 2차 개선 — owner 지적 5건 반영(designer) + orchestrator 재검증·버그 1건 직접수정.**
티켓 `inbox/_resolved/20260912T0530Z__owner__JP_MULTI__jesr_jp_page_v2.md`(resolved). ① category 2단 버킷 정렬
(`HD上場`/`相互会社`/`上場` 선두 vs 그 외, 각 버킷 내 `esr_pct` desc — au損害保険 791.7%가 손보 최하단으로 이동)
② sector 별 top5+더보기(生保 9사→top5+4, 損保 4사=버튼 없음, reinsurance는 損保에 합류) ③ 表의 出所 열 제거 →
公表日 텍스트에 `source_url` 링크 ④ 막대차트 빗금(연결) 인코딩·범례 항목 제거, `scope` 는 表·툴팁 텍스트로만
⑤ 速報 배지 그대로. designer 세션은 Playwright 캡처가 cdn.jsdelivr.net `ERR_NETWORK_ACCESS_DENIED`(이 PC 크로미움
공통 현상)로 차트가 빈 화면으로 찍혀 "다음 세션 재확인 권장"으로 넘겼는데, **orchestrator 가 즉시 재검증**함:
echarts 로컬 임시 사본(검증 후 삭제, `jp/index.html`은 CDN 참조만 유지)으로 실제 렌더 확인 — 2단 정렬·top5 폴드·
au 최하단 이동·빗금 제거 전부 스크린샷으로 확인됨. 그 과정에서 **버그 1건 추가 발견·직접수정**: 모바일(375px)
생명보험 차트 x축 눈금이 "50%00%050%060%090%00%" 로 겹쳐 읽을 수 없었음 → `xAxis.axisLabel.hideOverlap:true` +
모바일 `splitNumber:4`(데스크톱 6)로 수정, "0% 100% 200% 300% 400%" 정상 표시 확인. 최종 스크린샷
`artifacts/designer/jesr_jp_draft_{desktop,mobile}_20260912.png`(덮어씀).

**🟢 2026-09-12 (3) `jp/jesr_esr.json` 부모-자회사 중복 제거 — 15→13 레코드(publishing).**
티켓 `inbox/publishing/20260912T0530Z__owner__JP_MULTI__jesr_dedup_parent_subsidiary.md`. 소니생명保険(parent 소니FG)·明治安田損害保険
(parent 明治安田生命保険) 제외, au損害保険(parent KDDI, 미공시)은 유지. `J-ESR/build_jesr_page_json.py` 에 회사명 비하드코딩 일반 로직
(`jp_insurers.csv` `parent_group` 조인) 추가. `J-ESR/jesr_master.json` 은 15사 그대로. 재현:
`PYTHONIOENCODING=utf-8 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe J-ESR/build_jesr_page_json.py`.

**🟢 2026-09-12 (2) `/jp/` 일본어 페이지 초안 — 데이터 `jp/jesr_esr.json`(15사, publishing) + `jp/index.html`(designer).**
티켓 `inbox/_resolved/20260912T0446Z__owner__JP_MULTI__jesr_page_json.md` · `..._jesr_jp_page_draft.md`. owner 결정: IP 차등·`.co.jp` 대신
같은 사이트 `/jp/` 경로(나중에 `jp.insurequant.com` 승격 가능). 라이브 반영은 owner 가 초안을 본 뒤.

**🟢 2026-09-12 (1) FY2025 ESR 공시 게재 census 79사 — posted 15 / not_yet 62 / not_found 2, ir_url 공란 41→2.**
`J-ESR/fy2025_esr_census_20260912.csv`. 손보 원문 11/13건이 "신기준 비율 2026년 10월 말 공표 예정" 명시. 소스 루트 정정(EDINET 보조, 회사별
공시 사이트 정본)은 이날 owner 발언 재기록. 티켓 `inbox/_resolved/20260912T0307Z__owner__JP_MULTI__jesr_fy2025_disclosure_census.md`.
