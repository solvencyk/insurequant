# Insurequant TODO — jp 레인 (일본 ESR)

> Last updated: 2026-09-13 (16) · 도메인 문서: `docs/domains/claude-agent-jp.md` · Changelog: `docs/changelog_jp.md` · inbox: `inbox/jp/`
> Status 는 최신 5개만 유지, 밀린 항목은 [`docs/todo_archive_jp.md`](docs/todo_archive_jp.md) 로(무수정).

## Status

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

## Active follow-ups

- **비공개 프리뷰 경로(owner 2026-09-12 결정).** 저장소는 `jp/` 그대로, main 배포만 `jp-f9027362/`(`scripts/android_push_and_deploy.sh`
  `JP_PRIVATE_DIR`, `deploy_path()` 매핑; 첫 전환 라운드에 main 의 공개 `jp/` 는 자동 삭제). 라이브 주소 = `https://www.insurequant.com/jp-f9027362/`.
  noindex 유지, 한국 페이지 링크 없음. 공개 repo 라 폴더명은 repo 열람자에겐 보인다("링크·검색 비노출" 수준). **공개 전환 체크리스트:**
  ① `JP_PRIVATE_DIR=""` ② 그 라운드 main 에서 `git rm -r jp-f9027362` ③ `jp/*.html` noindex 제거·robots/sitemap 등재 ④ 루트 index.html hreflang·언어전환·안내띠 삽입
  (designer 답변 조각) ⑤ Cloudflare Access 는 유료 인증이 필요해질 때.
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
