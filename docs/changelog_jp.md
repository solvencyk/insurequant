# Changelog — jp 레인 (일본 ESR)

> 이력 저장소. 세션 시작 시 읽지 않는다. 현황은 `TODO_jp.md`.

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
