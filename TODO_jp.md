# Insurequant TODO — jp 레인 (일본 ESR)

> Last updated: 2026-09-13 (20) · 도메인 문서: `docs/domains/claude-agent-jp.md` · Changelog: `docs/changelog_jp.md` · inbox: `inbox/jp/`
> Status 는 최신 5개만 유지, 밀린 항목은 [`docs/todo_archive_jp.md`](docs/todo_archive_jp.md) 로(무수정).

## Status

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
