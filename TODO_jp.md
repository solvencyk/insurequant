# Insurequant TODO — jp 레인 (일본 ESR)

> Last updated: 2026-09-12 (13) · 도메인 문서: `docs/domains/claude-agent-jp.md` · Changelog: `docs/changelog_jp.md` · inbox: `inbox/jp/`
> Status 는 최신 5개만 유지, 밀린 항목은 [`docs/todo_archive_jp.md`](docs/todo_archive_jp.md) 로(무수정).

## Status

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
