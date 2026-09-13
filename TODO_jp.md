# Insurequant TODO — jp 레인 (일본 ESR)

> Last updated: 2026-09-13 (22) · 도메인 문서: `docs/domains/claude-agent-jp.md` · Changelog: `docs/changelog_jp.md` · inbox: `inbox/jp/`
> Status 는 최신 5개만 유지, 밀린 항목은 [`docs/todo_archive_jp.md`](docs/todo_archive_jp.md) 로(무수정).

## Status

**🟢 2026-09-13 (22) 회사별 상세 3페이지 분리(jesr 자본 / jgaap 회계 / disclosure 기타공시) + 所要資本 워터폴 폐지 + 貸借対照表 T자형 패널(orchestrator).**
owner "한국처럼 자본·회계·기타공시로 나눠라, 워터폴은 분산효과만 보여주니 빼라, jgaap 에 IFRS17.html 식 T자 BS". 종전 `jp/jesr.html` 인라인 CSS/JS 를
`jp/jp.css`·`jp/jesr_app.js`(공용, `<body data-page>` 분기·byId 가드·`?company=` 탭 동기화)로 빼고 `jgaap.html`(主要指標 4카드·損益 2블록·워터폴·収益性·
種目別·基礎利益·準備金·**貸借対照表 T자**)·`disclosure.html`(再保険 의존도·その他) 신설, axes 라우팅 reserve→jgaap / reins→disclosure / smr→esr.
`jp/index.html`·`terms.html` 헤더 3탭. T자 패널은 (21)의 `bs.tree` 를 IFRS17.html Panel 1 규칙(존 3개·[+]·負債:純資産 flex 비율·2기 비교표·資産=負債+純資産 배지)로 렌더,
7사 표시(TMNF 資産 97,596.8억엔 등)·3사 숨김. Playwright 12케이스×2폭 pageerrors 0, `test_deploy_assets` 11 passed. 배포 NEW_FILES +4(폰 2회).
**다음**: ① Meiji Yasuda Non-Life 본편 PDF 는 로컬에 있다(`meijiyasuda_nonlife_20260729_main.pdf` p39~40, 3개년 **열 우선** 세로글리프 표) — `extract_bs.py` 에
column-major 레이아웃 1개 추가하면 bs 8사. ② 住友生命·第一生命 7월 ディスクロージャー誌 확보 → bs 10사(10월 재조사와 병행). ③ 準備金 표 `cat_reserve_fire` 라벨
"火災 行 × 異常危険準備金 列" → builder `LABEL_JA_DISPLAY_OVERRIDES` 로 「異常危険準備金（火災）」. ④ 前期 出再保険手数料(20).

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
