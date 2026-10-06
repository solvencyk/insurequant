# TODO archive — `TODO.md` (Status 이력, 읽기 지연)

## 2026-10-07 정리 — 정리 전 `TODO.md` 전문 (무수정, 예외 등재부·라운드 절차는 별도 문서로 이동)

# Insurequant TODO

> Last updated: 2026-09-22 · Stage: cross-stage
> Index: CLAUDE.md (5-stage; parser 2-lane since 2026-06-13) · Stage TODOs: TODO_<stage>.md

Pipeline organized as **downloader / parser / validation / publishing / designer** — each stage has its own prompt (`docs/agents/claude-agent-<stage>.md`), TODO (`TODO_<stage>.md`), and changelog (`docs/changelog_<stage>.md`). See `CLAUDE.md` for the full index. This root file carries cross-stage items + project-wide policy only.

## Status

**🆕 2026-09-22 K-ICS 금리 듀레이션 갭 마스터 신설 — 분모를 '금리위험액 현황' 자산총계로 확정(cross-stage, owner 지시).** owner 가 기존 산식의 분모(순자산)를 자산 기준으로 바꾸라고 지시했고, 조사 과정에서 **어느 자산이냐**가 갈렸다 — 건전성감독기준 재무상태표의 전체 자산이 아니라 **경영공시 '금리위험액 현황' 표의 Ⅰ.자산총계**가 맞다. 근거: 분자(순자산가치 변동)가 금리위험 측정 대상에서만 나오므로 범위를 맞춰야 `갭 = 자산D − 부채D` 항등식이 닫힌다(삼성생명 2026.2Q 실측 — 260조 분모에서 5.94−6.20=△0.26 으로 닫히고, 481조 전체자산 분모에서는 △0.14 로 어떤 듀레이션 차이로도 분해되지 않는다). 전체자산 분모는 회사마다 다른 배율로 희석돼(삼성생명 1.85배) 회사 간 비교가 깨진다. **산출물**: 루트 마스터 `kics_duration_gap.json`(39사 × 짝수분기 7기 = **270셀 전수**, 자산·부채 6시나리오 + 자산D/부채D/부채D_자산대비/갭/부채자산비율) · 마스터 xlsx 신규 시트 `금리듀레이션갭` · 추출기 `scripts/extract_kics_irr_balance.py` · 빌더 `scripts/build_kics_duration_gap.py`. **추출 경로**: 자동 254셀(앵커=순자산가치 행이 마스터 항목41/43/44 와 일치해야 채택, 컬럼→시나리오 사상과 단위배율을 동시 확정 / 라벨 실패 시 `자산−부채=순자산` 항등식으로 행 탐색 / 표가 다음 반기 보고서의 `직전반기` 열에만 있는 경우까지 교차분기 탐색), 나머지 16셀은 표가 글리프 이미지라 원본 PDF 렌더링 후 사람이 읽어 `data/_gold/kics_irr_balance_vision.json` 에 박제(미래에셋 7·KB손보 5·AIA 2·하나생명 1·카카오페이손보 1). **산출불가 3셀**은 카카오페이손보 2024.2Q~2025.2Q — 금리부자산 충격전이 △18백만원이라 분모 불성립(정상 부재). **owner 2차 지시 2건 반영** — ⓐ 부채듀레이션은 부채로 나눠 `D_L` 에서 끝내고 `L/A` 는 갭 식에서만 곱한다(`갭 = 자산D − (L/A)×부채D`). 중간열 `부채듀레이션_자산대비` 는 제거(시트 23→22열, 삭제 후 재생성·나머지 시트 값 불변 검증). `L0 ≤ 0` 인 라이나생명·AIG손해는 `D_L` 만 비우고 갭은 유효. ⓑ **라이나생명 2023.4Q PL 20칸 신규 충전** — 같은 회사 2024.4Q·2025.4Q 는 `_GOLD_CELL_OVERRIDE` 로 채워져 있는데 2023.4Q 만 `income_statement` 블록이 통째 비어 있었다(계보 `source_file=null · NO_PUBLISHED_VALUE_IN_BLOCK · published_items=0`). 원인은 FS-API status 013(이 회사 전 연도) + 'Ⅰ−Ⅱ' 도출형 IS 를 tier1 HTML 이 못 읽는 것이고, 아무도 이 분기만 손으로 안 넣었다. FY2024 사업보고서의 **전기 비교컬럼 + 주석23**(기존 item4/9 와 같은 재작성 기준)으로 채웠고 산식은 2024.4Q·2025.4Q 기존값으로 전부 역검증. 게이트가 `MISSING_PROVENANCE`+`SOURCE_ID_LINEAGE_MISMATCH` RED=2 를 정확히 냈고 계보 셀 1개를 `OWNER_GOLD` 로 고쳐 RED=0 복귀. pl_bridge 3309P→3317P·실패 0 증가, `master_tables_golden` `--update` 재생성. **단서: FY2023 은 소급재작성됐다** — 자기 보고서 당기순이익 463,997 vs 채택한 재작성 511,309(차이 47,312).

**부수 발견**: ① AIA 2024.4Q 항목46 이 억원 아닌 백만원(100배)으로 마스터에 들어가 있다 — `max(base−steep,0)` 뒤로 숨어 `36_irr` 룰이 구조적으로 못 보는 자리(`inbox/parser/20260922T1200Z` 발주 → **2026-10-06 정정 완료**, parser-kics 19회차). ② 발행사 표가 스스로 안 맞는 2셀(BNP카디프 2023.2Q 6시나리오 0.74%·DB생명 2025.2Q 2시나리오) — 공시대로 두고 `비고` 박제.

**🔴 2026-09-21 라이브 K-ICS `IQP is not defined` 사고 — 복구·게이트 신설·배포 완료(cross-stage: designer → validation → parser-kics → publishing).** owner 가 라이나생명 2026.2Q 금리민감도 "아직 없습니다" + 세부항목 표 "JSON 파일을 불러오는 중 오류 발생: ReferenceError: IQP is not defined" 로 발견. 원인은 데이터가 아니라 2차 디자인 배포 `2dbc4ca` 가 `K-ICS.html` 의 `function IQP()` 정의만 지운 것(36/39사 패널 사망, 부팅 `.then` 전체가 죽어 표까지 덮임). 처리: designer 복구 `197d15e`(정의 + try/catch 안전망) · validation 신설 `scripts/validate_deployed_js.py` → `prepush_check.py` §1f 배선(`cf6fd77`, 구 main RED=2 재현·복구본 RED=0, 변이시험 24케이스) · parser-kics 라이나 원문 대조 수정 0건 + 2026.2Q 적용후 결손 3사 9칸(`a03ac79`) · publishing main `92159dd`(5파일, 라이브 블롭 5/5·헤드리스 4사 렌더 확인). **열린 후속 3건**: 신한라이프 `36_irr` 2분기 −28%/−15% 가 RED 안 됨(`inbox/validation/20260921T0215Z`) · 금리민감도 phase 레벨 census 사각 RS6(`inbox/validation/20260921T0100Z`) · 자본비율전망 시트 비고 내부 진단 용어(`inbox/publishing/20260921T0320Z`). 헤드리스 런타임 게이트 타당성(`20260921T0630Z`)은 UH-26 으로 보류. 상세 `docs/postmortems/PM-20260921_kics_sens_iqp_referenceerror.md`.

**🔁 2026-09-18 경영공시 PL 백필 라운드 진행 중(cross-stage: parser-ifrs17 → validation → publishing).** PL_breakdown 비-4Q 결손을 정기경영공시 §2-1 요약 포괄손익계산서로 메우는 작업. 결손 실측 39사x14분기 546칸 중 172칸, 전부 DART 분기보고서를 안 내는 비상장 16사의 1~3Q. **오케스트레이터 직접 실측(9/18 12:35)**: 스테이징 `data/_derived/pl_backfill_disclosure_20260918.json` 172칸 중 OK 159 + vision_manual 7 + NO_PDF 6(KR0150 서울보증 2023.1~3Q·2024.1~3Q = **원천 부재 확정**, SGIC 사이트가 과거 분기를 게시 안 함). 자기폐쇄 E3/E5/E6 **실패 0건**, `|값|>200,000억` 이상치 **0건**, `dash_zero` 이면서 `raw_value==''` 인 읽기실패 **0칸** — validation 이 결정 5·7 로 지적한 오파싱은 파서 재실행으로 이미 해소됐다(반증 사례 KR0075 2024.3Q 보험손익도 `-80` 으로 정확). validation 판정 수용: **항목 8개→5개**(#1 보험손익·#16 기타사업비용·#22 세전·#23 법인세·#24 순이익. #17 투자손익·#20 영업이익·#21 영업외손익은 감독회계 재분류로 **다른 개념** — 경영공시 = 투자수익−투자비용, 마스터 = 투자이익+보험금융손익 336/336 성립), **16사→15사**(KR0004 예별손해는 DART·경영공시 양쪽 다 내부정합인데 값이 달라 범위 규명까지 보류). 계보 축 실측 재확인: `verify_provenance_sidecar()` 호출처 4곳에 PL_breakdown **없음**, `PL_breakdown_provenance.json` 638셀 **전부 `source_file` 부재**, `_SOURCE_LINEAGE` 에 `data/disclosure/` **미등록**. **병합 순서 고정(어기면 census RED 0→80 으로 push 차단)**: ① 사이드카 실물 발행[parser] → ② 계보 배선(guard 밖으로)[validation] → ③ `coverage_holes` source-aware 기대그리드[validation] → ④ CONCEPT_REGISTRY 등재[validation] → ⑤ 5항목 병합[parser→publishing] → ⑥ 게이트 RED=0 후 push. 같이 드러난 새 사각: `#2 생명장기손익` 부모 None 인데 자식 `#3~#12` present 가 **29버킷**(display 10), PL 에 "자식 present·부모 None" 룰이 아예 없다(K-ICS `_parent_present_child_incomplete` 대응물 부재). **(2026-09-20 진척) ①②③④ 완료 — 남은 것은 ⑤⑥.** ① parser 사이드카 재발행(커밋 `fa08bfe`, 638→748셀 · 마스터 실재 셀과 1:1 · `source_file` 730/748 · 디스크 부재 0). ②③④ validation 배선 완료(계보 등재 4건 + `SOURCE_ID_LINEAGE_MISMATCH` 를 capsec guard 밖으로 · PL provenance 첫 검증 published 731셀 · `coverage_holes` 기대그리드를 셀 계보별로 · `CONCEPT_REGISTRY["pl_disclosure_vs_dart"]` 등재 + allowlist 리더). **라이브 RED=0 YELLOW=123 불변 · selftest 57→69 · 골든 SUMMARY 불변(`--update` 불요) · `prepush_check` FULL gate-clear.** 병합 후 예측은 census RED **0→80 이 아니라 0→3** 이다(소스인식 규격에서 real hole 118→6, 그중 3건은 이미 있던 서울보증 원천부재). **⑤ 전에 parser 가 처리할 차단 2건**: (가) 스테이징 `항목번호 23` 항목명이 `법인세비용` 인데 마스터는 `법인세` — 이대로 병합하면 같은 번호에 이름이 둘 생긴다, (나) 병합으로 드러나는 진짜 DART 결손 3건(AIG 2024.4Q·2025.4Q · 신한이지 2024.4Q 의 생명장기손익). 회신 티켓 `inbox/parser/20260920T1500Z__validation__ALL_2023.1Q-2026.2Q__disclosure_pl_merge_authorized.md`.

**✅ 2026-09-16 UH-24 해소 — owner 로컬 PC 세션이 훅을 실행권한 부여·이식 가능하게 고치고 실제로 두 번 끝까지 돌려서 검증했다(cross-stage).** `.githooks/pre-push` `chmod +x` + `PY` 를 owner venv 우선·부재시 `python3`/`python` 폴백으로 재작성. 1차 실행에서 `test_jp_source_gate.py::test_gate_prints_the_adjusted_finding_end_to_end` RED(콘솔이 cp949 인 이 PC에서 `build_jesr_page_json.py` 가 일본어 산문을 print 하다 `UnicodeEncodeError`, 클라우드는 콘솔이 UTF-8 이라 46개 커밋 내내 안 걸렸던 버그) → `build_jesr_page_json.py`·`tests/test_jp_source_gate.py::_run_builder` 에 UTF-8 인코딩 고정 → 2차 `567 passed, 2 skipped` · `PRE-PUSH VERDICT ... gate-clear` · exit 0. 상세 `docs/postmortems/README.md` UH-24.

**🚀 2026-09-14 jp 프리뷰 라이브 배포 + 폰 배포 스크립트 rot 2건 제거 + 훅 강제점이 리눅스 클론에서 무력인 것 발견(cross-stage).**
① **라이브 배포 나갔다** — `jp-f9027362/` 4개(`index.html`·`jesr_app.js`·`jesr_detail.json`·`jesr_esr.json`), 배포 커밋 `e797f61`.
검증은 "커밋했다" 가 아니라 **라이브에서 바이트를 받아 `git hash-object` 로 커밋 블롭과 대조 4/4 일치**. `generated_at` 2026-09-13T07:36:23Z → **17:08:02Z**, 화면 15사 = census posted 15.
배포 커밋 name-status 가 4파일 전부 jp 라 **한국 자산은 한 바이트도 안 바뀌었다**.
② **`scripts/android_push_and_deploy.sh` rot 2건** — (a) 번들 인자가 필수라 *브랜치가 이미 origin 에 있는* 경우(클라우드 세션이 직접 push)를 배포할 방법이 없었다 → `--from-origin` 신설.
(b) 기본 브랜치가 `fix/csm-product-segmented-columns` 로 굳어 있어 인자 없이 돌리면 **옛 브랜치가 라이브로 나간다** → 문서 경고가 아니라 **기본값 자체를 제거**했다(`--from-origin` 은 `--branch` 필수, 번들 모드는 `git bundle list-heads` 로 번들에서 읽고 0개·2개 이상이면 중단).
헤더 사용법도 틀렸었다 — main 은 slim(실측 55파일, `scripts/` 없음)이라 clone 직후 HEAD 에는 이 스크립트가 **없다**. 커밋 `f35603f`·`a8de4ae`.
③ **UH-24 (신규, cross-stage, P1)** — `.githooks/pre-push` 가 저장소에 **mode 100644**(실행권한 없음)로 들어 있다. `git config core.hooksPath .githooks` 를 해도 git 이 훅을 **조용히 건너뛴다**.
이번 push 에서 git 이 직접 인쇄했다: `hint: The '.githooks/pre-push' hook was ignored because it's not set as executable.`
즉 **리눅스·macOS·Termux 클론에서는 CLAUDE.md §5 의 "훅으로 강제" 가 강제가 아니다** — 이 클라우드 컨테이너도, 배포용 폰 클론도 해당된다.
`docs/todo_archive_root.md` 의 2026-08-21 항목이 "실제 `git push` 차단 확인" 이라고 적은 것은 **owner Windows PC 기준**이고(Git for Windows 는 exec 비트를 안 보는 경우가 많다), 그래서 3주 넘게 안 드러났다. **UH-1("배선한 룰이 push 를 못 막았다")의 재발형.**
**정정(같은 날, 2차 조사)**: 처음에 "`git update-index --chmod=+x` 한 줄" 이라고 적었는데 **틀렸다. chmod 만 하면 더 나빠진다.** 훅이 `PY="C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe"` 를 **하드코딩**하고 `[ ! -f "$PY" ] → exit 1` 로 죽는다 — 리눅스·Termux 에서는 그 경로가 없으므로 **게이트를 한 줄도 안 돌리고 push 를 통째로 막는다**. 즉 현재(실행권한 없음) = 조용히 무게이트 통과, chmod 만 하면 = 리눅스 클론에서 전면 차단. **둘 다 게이트가 안 도는 것은 같다.** 제대로 된 수정은 ① `chmod +x` ② `PY` 를 이식 가능하게(Windows 경로가 있으면 그것, 없으면 `python3`) **둘 다**이다. `.githooks/` 는 범위판정상 full-gate 경로이고 이 컨테이너는 `data/disclosure` **0개**·`data/kidi` **0개**라 full gate 를 못 돌린다 → **작업 PC 몫**. (레지스트리 등재는 `docs/postmortems/README.md`, 이번 라운드 병렬 에이전트가 같은 파일을 쓰고 있어 그 뒤에 넣는다.)
④ 이번 라운드 두 커밋은 훅이 무시된 채 그냥 나간 게 아니다 — `prepush_check.py` 를 **손으로 돌려** `REDUCED(jp-scope)` 판정 + offline 240 passed 를 확인하고 밀었다.


> (L34-122 「상시 점검」 2026.2Q 라운드 절차 → `docs/flows/kics_quarterly_round.md` 로 이동)

### 최근 종결 (2026-08-30)

- [x] **`assemble()` "미공시 시 0표시" 규칙 — owner 가 option 1 승인, 구현 완료** (`cd79127`).
  회사가 다른 분기에서 실제로 뽑는 항목이면 이번 분기의 0-fill 을 건너뛰고 null 을 남긴다.
  마스터 38칸(+당분기 40칸)이 숫자→null(5사). 억제된 null 은 `data/_derived/pl_intentional_nulls.json`
  로 `_additive_merge` 폴백에서 제외 — 안 그러면 재빌드마다 예전 0 이 되살아난다.
- [x] **`public_exports/` 무검사 해소** (`8c702fc`). 사용자가 내려받는 12개 파일을 어떤 검사기도
  안 읽고 있었다. `validate_live_artifacts` 에 축 신설(15룰, 변이시험 8/8). 같이 발견: 그
  사각을 잡았어야 할 `test_push_gate_wiring` 이 `<script src>` 를 안 따라가서 그 12개를 한
  번도 본 적이 없었다 — 그것도 닫았다.
- [x] **gold 오버레이 무검사 해소** (`93c68db`). gold 를 빌더 소스와 대조하는 게이트·테스트가
  저장소에 0건이었다 = gold 셀 밑에서 빌더가 회귀해도 전 게이트가 clean. 마스크 115칸 원장 등재,
  drift 는 RED.
- [x] **inbox 전건 종결** — answered 28 + open 3 을 검증 후 `_resolved/` 로 이동, 활성 0.


> 📦 **Status 이력은 `docs/todo_archive_root.md` 로 이동했다** (2026-09-11, 내용 무수정 — 2026-08-21 이전 서술 + 종결된 data-contract 예외 절 및 그 이전 항목). 세션 시작 시 읽지 않는다; changelog 처럼 특정 과거 결정의 배경이 필요할 때만 연다. **이 Status 는 최신 5개 항목만 유지**하고, 밀려난 항목은 그 파일 헤더 바로 아래에 그대로 잘라 붙인다.

**J-ESR (일본 ESR) — 2026-09월말 킥오프 목표 (2026-09-01 owner, 보류 해제).** 기존 보류 사유(개별사 ESR이 EDINET 有価証券報告書 제출기한 전에는 미공개)는 유효했으나, `J-ESR/jesr_pipeline_status.md` 실측상 有報 제출이 6~9월에 몰려있어(최종기한은 2026-10-31이지만) 9월 말이면 이미 다수 사가 제출 완료 상태 — 더 늦출 이유 없음. MVP는 2026-07-21 revert(`167cba1`)됐고, scaffold(EDINET fetch API키 확보·mutual IR-PDF·`jp_insurers.csv` 74사)는 그대로 살아있어 재개 시 처음부터 다시 할 필요 없음. 재개 시 downloader/parser inbox로 신규 발주 — 과거 스레드는 `inbox/_resolved/*jesr*` 4건 참조.

> **소스 루트 정정 (owner 2026-09-12, 구두 결정 재기록).** EDINET 은 주 소스가 아니다 — FY2024 XBRL 실측에서 ESR 구성요소가 0건(`inbox/_resolved/20260624T0337Z__owner__JP_MULTI__jesr_datalayer_asof.md` probe 보고). 개별사 ESR 은 **회사별 공시(IR) 사이트의 결산설명·디스클로저 PDF** 가 정본이고, 그 공시 기한이 **2026-10-31** 이다(owner 발언; 이전 세션 결론인데 repo 에 미기록이어서 오케가 09-12 에 EDINET 전수조회를 다시 제안하는 사고 발생). 킥오프 1차 조각 = `J-ESR/jp_insurers.csv` 의 `ir_url` 공란 41/81 채우기 + 회사별 사이트에 FY2025 ESR 공시가 이미 게재됐는지 census. EDINET 은 보조(상장사 교차확인)로만. **09-12 census 실행 완료(downloader 티켓 20260912T0307Z, resolved):** 79사 중 posted 15 / not_yet 62 / not_found 2, ir_url 공란 41→2, `J-ESR/fy2025_esr_census_20260912.csv`. 손보 원문 11/13건이 "10월 말 공표 예정" 명시 → 9월 말 킥오프는 분모·15사 값으로 시작, 전수 값은 10월 말 재census.

> **취지 참고 (owner 공유 기사, 2026-09-01) — 일본 금융청 '2026년 보험 모니터링 보고서'.** 출처: [insnews #92437](https://www.insnews.co.kr/news/articleView.html?idxno=92437). ESR 비율 자체보다 넓게, 금융청·시장이 실제 주목하는 축 3개: ① **자산집약형 재보험(AIR) 활용** — 생보 약 절반(주로 외국계·상장사)이 AIR 보유, 활용 목적에 "ESR 개선"이 명시적으로 들어가고 금융청은 재보험사 신용위험 + 특정 자산/지역/재보험사 집중위험을 경고. ② **손보 이상위험준비금(화재보험) 적립 부족** — 2025-03말 기준 화재보험 취급 28사 중 12사에서 부족 확인, 자연재해 빈발로 상시 이슈화. ③ **생보 이익구조 전환** — 이차손익이 금리상승으로 역마진→이익 구조로 전환 중, 예정이율 인상 확산(K-ICS/IFRS17에서 이미 다루는 위험률차손익·이차손익 구조와 대응됨). **지금 스코프(ESR 헤드라인 숫자)를 이 3축까지 넓힐지는 미결 — 재개 시 EDINET 有報에서 실제로 뽑히는지 확인 후 판단.** 지금은 방향성 참고만.

**Stage files:**

- **Downloader** (Stage 1): `TODO_downloader.md` + `docs/changelog_downloader.md` + `docs/agents/claude-agent-downloader.md`
- **Parser** (Stage 2, **2-lane since 2026-06-13**): `TODO_parser_kics.md` · `TODO_parser_ifrs17.md` + `docs/changelog_parser_{kics,ifrs17}.md` (pre-split frozen: `docs/changelog_parser.md`) + shared `docs/agents/claude-agent-parser.md` + domain `docs/domains/claude-agent-{kics,ifrs17}.md`
- **Validation** (Stage 3): `TODO_validation.md` + `docs/changelog_validation.md` + `docs/agents/claude-agent-validation.md`
- **Publishing** (Stage 4, **merged gathering + pushing**): `TODO_publishing.md` + `docs/changelog_publishing.md` + `docs/agents/claude-agent-publishing.md` (**complete** — §5/§9/§10 + launch-runbook skill, 2026-07-21)
- **Designer** (Stage 5, **new — HTML/CSS/responsive**): `TODO_designer.md` + `docs/changelog_designer.md` + `docs/agents/claude-agent-designer.md` (**complete** — §5.1~5.5 design system, 2026-06-16)

Items previously here that have moved out:

- Downloader (F2 done, F7–F10, F14, MISC-BOND-*, MISC-IR-MERITZ, MISC-SEIBRO, decisions #5/#6) → `TODO_downloader.md`
- Parser (KICS-PARSER-SPLIT/REPARSE-Q4/KR0069/KR0097/RED-FIX2/RED-FIX3/SUB/POST/RATIO28/HIST/IMG + IFRS-A1~B5-KICS/B3-UNIFY/NORMALIZE/HIST/SEN-TABLE) → `TODO_parser_{kics,ifrs17}.md`
- Validation (KICS-VALIDATE, IFRS17-NB-RECONCILE) → `TODO_validation.md`
- Publishing (F4 v2, F13, INDEX-IFRS17-BUBBLE, INDEX-BUBBLE-V2, MISC-IR-PROTOTYPE, MISC-IR-NB-DENOM, IFRS17-CSM-BUBBLE, KICS-TIER1/2-UTIL, KICS-FORWARD-CAPITAL, KICS-HTML-SUB, IFRS17-HTML-DASH, F5/F6 data) → `TODO_publishing.md`
- Designer (MOB-KICS, MOB-IFRS17, VIS-DONUT, VIS-CHARTLEGEND, INDEX-C12, F1-HTML, F6-HTML, F17-PANEL3 HTML, M1/M2) → `TODO_designer.md`


> (L164-503 K-ICS gate documented exceptions → `docs/kics_gate_exceptions.md` 로 이동)

---

## 🚧 CROSS-STAGE — CSM waterfall 신한EZ 제외 후속 (owner xlsx 검토 2026-06-10, 보정 06-11)

~~3사 제외~~ → **하나손해(KR0050)·하나생명(KR0097)은 복원**(자사 감사보고서 별도 변동표 실재 — 경영서술 수치와
정확 일치 검증, owner 재지시 2026-06-11). **신한이지(KR0051)만 제외 유지**: 감사보고서 변동표가 천원 단위인데
백만원 오인(×1000 인플레) + PAA 중심사로 일반모형 CSM ~2억 = 워터폴 무의미. override `data/dart/viz/csm_manual_overrides.json`.

- [x] **designer**: 완료 확인 2026-08-20 — `IFRS17.html` L604에 `PAA_ONLY = new Set(["KR0051", "신한이지손해보험"])`(코드+표시명 양쪽) 배선됨. 마스터에도 KR0051 행이 0이라 렌더 대상 자체가 없다.
- [x] **publishing**: 인지 완료. 단 **경로가 바뀌었다** — 2026-08-20 gold-overlay 통일(`71914c3`)로 `data/dart/viz/csm_manual_overrides.json` → **`data/_gold/user_csm_cells.json`**(PL은 `user_pl_cells.json`). 훅 자동 적용은 그대로.

---

## 🚧 CROSS-STAGE — K-ICS 금리민감도 신규 feature (2026-06-10 발주 → 06-12 publishing만 잔여)

경영공시 `6-8. 위험 민감도` → 금리민감도 표(경과조치 × measure × ±50/±100bp)를 신규 루트 마스터 `kics_rate_sensitivity.json`으로. 38사 서베이 완료, 스펙 정본 `docs/agents/kics-rate-sensitivity-spec.md`.

- [x] parser: 추출 스크립트 + 마스터(435행)/diag — RS1·RS2 자기검증 통과 (2026-06-10)
- [x] validation: RS1–RS4 룰 구현, 게이트 RED=0 (consolidate_inbox 핸들러 배선만 후속 잔여) (2026-06-10)
- [x] **publishing: 커밋 번들 + master xlsx 재생성** — 완료 확인 2026-08-20. xlsx 4개 시트가 마스터와 행수 일치(17BS 6,855 · 손익분해PL 8,650 · CSM워터폴 2,136 · 배당 2,043), 수식 캐시 정상. 원 inbox 티켓도 종결(`_resolved/20260612T0900Z`).
- [x] designer: K-ICS.html 민감도 패널 (F-SENS-PANEL, 커버리지 29/30) (2026-06-11)

---

## 📬 2026-06-12 — 전 스테이지 backlog digest 발송 (owner 전수 점검)

5개 스테이지 inbox에 `20260612T0900Z__owner__ALL__backlog_digest.md` 발송 (publishing/designer inbox 신설,
`inbox/README.md` layout + route `backlog` 추가). 각 스테이지는 다음 호출 시 자기 다이제스트 드레인.

---

## 중장기 목표 (Mid-long-term goals) — 신규 마스터 테이블 (cross-stage)

(2026-06-06 owner 제안. 착수 전 단계 — 소스 위치만 슥 확인. 우선순위/일정 미정.)

### MLG-1. 듀레이션갭 (Duration Gap) 지표 마스터
- **목표**: 자산·부채 듀레이션 및 듀레이션갭(금리리스크 ALM) 전사·전분기 마스터 테이블.
- **소스 확인 결과**: 정기경영공시 MD(`data/disclosure/FY*/parsed/*.md`)에 "듀레이션" 단어 **0회**(삼성화재/삼성생명/DB 확인) → 표준 경영공시엔 없음. **소스 추가 조사 필요**:
  - 1순위 후보: DART 사업보고서 주석의 **금리위험 민감도 / 자산·부채 듀레이션** 표 (사별 상이, K-ICS 금리위험액 산출 부속).
  - 2순위: 사별 IR 자료 / K-ICS 공시 부속서.
- **다음 스텝(대략)**: (a) DART 사업보고서 1~2개사(삼성화재·한화생명) 금리위험 주석에서 듀레이션 표 존재 확인 → (b) 있으면 parser 시그니처 추가, 없으면 IR 소스로 전환. PL/CSM 마스터와 동일 8-field 스키마 재사용.
- **[조사완료 2026-06-07 야간]** DART 본문(한화생명/삼성생명 주석 50)에 **듀레이션갭 서술 + 만기사다리(16버킷) + 100bp 금리민감도(손익/OCI)** 존재하나 **자산/부채 듀레이션 숫자·갭 자체는 없음**(만기+할인곡선 유도 필요). 손보(삼성화재/DB)는 sparse. → **owner 결정 필요**: (i) 100bp 민감도만 추출(직접 가능), (ii) 듀레이션 유도식 정의(만기가중/할인). 다세션 작업. 상세 → `changelog_parser.md` (j).

### MLG-2. K-ICS 요구자본 세부 도해 (시장위험액→금리위험 / 해지위험액 세부)
- **목표**: 지급여력기준금액 중 **시장위험액 하위(금리/주식/부동산/외환/자산집중)**, **해지위험액 세부**를 분해한 마스터/도해.
- **소스 확인 결과**: `kics_disclosure.json`은 top-level만 캡처(`3. 시장위험액`, `1-5. 해지위험액` 등). **하위 분해 미캡처**. 단 경영공시 MD(`data/disclosure`)에 **"금리위험"·"주식위험" 텍스트 존재**(삼성화재·DB·삼성생명 확인) → **기존 데이터에서 parser 확장으로 추출 가능 (답지 불요)**.
- **다음 스텝(대략)**: (a) K-ICS 요구자본 detail 섹션 표 확인(시장위험액 하위행: 금리/주식/부동산/외환/자산집중) → (b) 기존 K-ICS parser에 하위 항목번호(예 `3-1` 금리위험…) 추가 — 코리안리 `2-1` 시리즈처럼 문자 항목번호 패턴 재사용 → (c) validation gate에 합산검증(Σ하위 = 시장위험액) 추가.
- **[조사완료 2026-06-07 야간]** `fill_subitems_to_disclosure.py`(생명장기 1-1~1-7 파서)가 템플릿이나, 시장위험은 **통합 ①시장위험액 현황 표 부재** + 하위가 사별·위험별 **이질 표**(금리=충격전후 shock표 → 위험액 *유도* 필요·모호, 주식=헤더 embed, 부동산=합계행). clean disclosed 총액 사별 불일치(삼성화재 금리·주식만, 삼성생명 금리만, DB손해 전무). → **PL-Tier2급 사별 핸들러 다수 + 금리위험액 유도규칙 owner 결정 필요.** R11(Σ=시장위험액)은 금리 확정 후. 다세션. 상세 → `changelog_parser.md` (j).

---

## 🔀 Cross-stage follow-ups (multi-stage; detail in stage files)

| # | Task | Stages involved | Detail location |
|---|------|-----------------|-----------------|
| F12 | K-ICS 시장위험 하위위험액 전체 파싱 + 분산효과 validation | parser + validation | `TODO_parser.md` F12 + `TODO_validation.md` V3 |
| F17 | 당기순이익 분해 (Tier1 전사 + Tier2 손보 LOB) | parser + publishing (+ designer for Tier2 panel) | `TODO_parser.md` F17 (body) + `TODO_publishing.md` F17 viz + `TODO_designer.md` F17 Tier2 |
| F18 | IR factsheet 정형화 + DART↔IR cross-validation | parser + validation + publishing | `TODO_parser.md` F18 + `TODO_validation.md` V1 + `TODO_publishing.md` F18 viz |
| F13 | 재보험 영업 지표 세트 | downloader (F8) + parser + publishing | `TODO_downloader.md` F8 + `TODO_publishing.md` F13 |

## 📋 Policy / User decisions (cross-stage)

| # | Decision | Date |
|---|----------|------|
| 1 | K-ICS skip cohort: KR0029 AIG, KR0150 SGI permanent skip. KR0051 / KR0074 partial-coverage by design | 2026-05-24 |
| 2 | Meritz IR source: Meritz Financial Group factsheet xlsx (replaces Meritz Hwajae standalone). AIG IR: skip low-priority | 2026-05-24 |
| 3 | NB CSM ratio denominator: **월납환산 신계약보험료**. IR PDF for 6 cos; assoc crawl (KIDI/KLIA/KNIA) for 23-co computed multiple | 2026-05-24 |
| 4 | First HTML viz: CSM Movement Waterfall (IFRS17 A1 23-co) | 2026-05-24 |
| 5 | API keys: repo root `.env` only (gitignored). Never commit/log key values | 2026-05-24 → `TODO_downloader.md` D5 |
| 6 | Bond Call rule: issue + 5y for ALL bonds. Past 5y = assume `called` | 2026-05-24 → `TODO_downloader.md` D6 |
| 7 | Pushing: subagent **reports + recommends only**. Human runs `git push` | 2026-05-30 |
| 8 | DART attachments (별첨/감사보고서 zip): **don't fetch**. Body XML has all IFRS17 disclosures | 2026-05-30 → `TODO_downloader.md` DL-NOATTACH |

## 🌐 Universe (cross-stage)

- **K-ICS**: 38 insurers (`kics_disclosure.json` `원수사명`); skip cohort KR0029/KR0150
- **IFRS17**: 28 insurers (`src/ifrs17/universe.py`) — 23 listed + 5 foreign-affiliate life via audit reports (F11, `AUDIT_REPORT_ANNUAL`, annual-only). Historical 13Q cohort = 23 listed.
- **K-ICS↔IFRS17 mismatch**: AIA (에이아이에이생명보험) is in IFRS17 universe but NOT in `kics_disclosure.json`. Cohort joins must handle this.

## ✅ Done — cross-stage anchors

| ID | Task | Notes |
|----|------|-------|
| ~~F1~~ | index.html → IFRS17 cross-nav | `fcdd544`. ECharts on('click') → URL param + auto-select. Data hook = publishing; HTML = designer |
| ~~F3~~ | CSM 상각 schedule 전수 조사 | `4b06492`. 19/24 → 22/24 ok |
| ~~F5~~ | No-bond insurer forward sim 추가 | `b02e24d`. 24 → 37 cohort |
| ~~F6~~ | CSM 상각 schedule yearly granularity | 2026-05-28. 16 yearly / 6 coarse / 2 no-data |
| ~~F11~~ | 외국계 생보 5사 IFRS17 추가 | DONE 2026-05-29. 23→28 (생보 13→18). corp_codes: 라이나 00504232 / 메트라이프 00171104 / AIA 01295517 / 하나생명 00187123 / 처브 00203102. universe.py `AUDIT_REPORT_ANNUAL`. NOTE: AIA not in kics_disclosure.json |
| ~~IFRS-Q~~ | Open Q1-Q9 | done. All 9 confirmed |

## 📚 Long-term / roadmap

> 📈 **중장기 제품·수익화·전략 로드맵 → `docs/roadmap.md`** (2026-05-26 신설)

Active long-term tracks now live in their respective stage TODOs:

- **IFRS17 bubble + market map evolution** → `TODO_publishing.md` (data) + `TODO_designer.md` (HTML)
- **Forward solvency simulation** → `TODO_publishing.md` (KICS-FORWARD-CAPITAL done v3 archive)
- **Roadmap §1A-2 priority 6 추가지표** (요구자본 위험액 분해 / RA / P&L 보험·투자 분해 / 출재율 / 유지율 / 운용자산이익률) → distributed across parser + publishing
- **Roadmap §1E 규제 뉴스 피드** → `TODO_downloader.md` F14

## 🧾 Meta

- Encoding rule: `CLAUDE.md` "Document/TODO Encoding Rule" added 2026-05-24
- .gitignore: `data/dart/raw/`, `data/dart/reports/` excluded
- 2026-05-25 doc trim: changelog 124KB→11KB (latest 5 entries detailed + historical archive 1-liners)
- git: initialized + pushed to github.com/solvencyk/insurequant (main). GitHub Pages → solvencyk.github.io/insurequant
- 2026-05-26: `docs/roadmap.md` 신설
- 2026-05-28 HTML single-source refactor (P1+P4): templates/*.html 4개 삭제. ⚠️ 데이터 JSON 중복 남음 (P2)
- 2026-05-28 모바일 반응형 M1/M2 적용
- 2026-05-28 IFRS17 패널 정리: 파생 KPI 카드 + BS 스냅샷 제거 → `docs/archived_metrics.md`
- 2026-05-30j Reorg #2: `data/assoc` → `data/_derived`, KIDI/DART → `FY####_Q#`. DART batch script refactor 잔여 → `TODO_downloader.md`
- 2026-05-30k 5-stage workflow split (downloader/parser/validation/gathering/pushing 초안)
- 2026-05-31 Stage 2/3/4/5 split fully populated: parser/validation TODO+changelog (오전), publishing(=gathering+pushing 머지)+designer(MOB/VIS HTML 별도 stage) TODO+changelog (오후). Root TODO is now genuinely cross-stage only

## ✓ MVP checklist (IFRS17)

- [x] A1 A2 A3 A4 B1 B5 all 23/23 MVP (B5 K-ICS primary ingest done FY2025_Q4)

## 🎯 Next priorities (cross-stage)

1. **KICS-IMG manual OCR** (user-owned): KR0010 KB Sonhae rule 2 ×2 — only remaining RED. Parser policy → `TODO_parser.md`; validation gate exception → `TODO_validation.md` V6
2. **F17 decision**: 9/11 손보 Tier2 LOB commit vs debug 삼성·DB vs IR-clean only. Parser detail → `TODO_parser.md`. Tier2 panel rendering → `TODO_designer.md` after decision
3. **F18 activation**: parser delivers IR JSON → V1 validation rules activate → publishing assembles cross-source viz
4. **REORG2-DART**: 3 batch scripts canonical-layout refactor → `TODO_downloader.md`
5. **Stage prompts 마무리**: parser / publishing / designer prompts still skeleton (TBD bodies); validation + downloader prompts are owner-authored complete

---

**📡 2026-09-13 클라우드에서 한국 원천 도달성 실측 — 회사망 제약이 보편 제약이 아니었다(cross-stage).** owner 질문("접근 막혀 미검증인 것들 다시 볼 수 있나")에 답하려 이 컨테이너에서 재봤다: **DART 200 · OpenDART API 200 · 금융감독원 200 · 생명보험협회 공시(pub.insure.or.kr) 200 · FISIS 200 · data.go.kr 200 · 손해보험협회 200(브라우저 헤더 필요)**. **KIPRIS 도 살아 있다** — 기본 `requests`/`curl` 은 클라이언트 핑거프린팅으로 끊기지만 브라우저 헤더(`J-ESR/jesr_http.get`)로는 루트·`/khome/main.do` 둘 다 200(MS&AD·ソニーFG 와 같은 `ok_requires_headers` 유형). 실패: 한화생명(TLS)·교보생명(프록시) 2사 — 재확인 대상. **CLAUDE.md §10 의 "go.kr·KIPRIS 는 브라우저·WebFetch 금지(영구 행)" 은 회사망 PC 의 제약이다** — 이 문장을 보편 제약으로 읽으면 클라우드 라운드에서 할 수 있는 일을 스스로 막는다. 규칙 문구 조정은 owner 판단(이 항목은 실측 기록일 뿐 규칙을 고치지 않았다). **경영공시 PDF 재수집·OCR 은 owner 지시로 범위 밖**(2026-09-13: "건들면 골치아프다").
**🔧 2026-09-13 push 게이트가 변경 범위를 코드로 판정한다(cross-stage).** owner 지적 *"한국 거 안 고쳤는데 한국 게이트 때문에 일본 작업이 BLOCK 되면 안 된다"*. CLAUDE.md §5 의 범위 규칙(owner 09-12)이 **문서에만 있고 훅은 무조건 전부 돌리고 있었다** — `prepush_check.py` §0 에 판정을 구현했다. jp 범위 번들이면 한국 마스터 축 5종을 건너뛰고 ~5초(실측), 한국 파일이 하나라도 섞이면 자동 FULL. **fail-closed**(upstream 없음·git 실패·빈 diff·모르는 경로 → 전체), 우회 환경변수 없음, verdict 에 `SKIPPED(jp-scope)` 로 "안 돌렸다"와 "통과했다"를 구분. 회귀 65케이스·변이 12/12 발화. 잔여 UH-20(훅이 refspec 을 안 넘겨 범위가 근사 — 빗나가면 전체가 도는 안전 방향). 상세 `docs/claude-changelog.md` 2026-09-13(2차).

> `TODO.md` 의 Status 이력 블록을 2026-09-11 에 **한 글자도 고치지 않고** 옮긴 것(최신순). 세션 시작 시 읽지 않는다 — `docs/changelog_*.md` 처럼 특정 과거 결정의 배경이 필요할 때만 연다. 활성 TODO 의 Status 에서 밀려난 항목은 이 줄 바로 아래에 그대로 잘라 붙인다(최신이 위).

---

**🔧 2026-09-13 서브에이전트 정의·스킬이 저장소 밖에 있던 것을 안으로 들였다(cross-stage).** `.gitignore:91` 의 `.claude/` 한 줄 때문에 `.claude/agents/*.md` 7개(모델 매핑: validation=Opus 5, 나머지 Sonnet 5)와 스킬 4개가 머신 로컬에만 있었고, 클라우드 세션은 CLAUDE.md §10 의 병렬 발사 규칙만 읽고 실행체를 못 읽었다. ignore 를 머신별 설정 파일만으로 좁히고 정의·스킬을 커밋, CLAUDE.md §10 에 위치·매핑 등재. 상세 `docs/claude-changelog.md` 2026-09-13.

---

**🧹 2026-09-11 지침 부채 정리 1차 — TODO Status 이력을 `docs/todo_archive_*.md` 6개로 분리(내용 무수정, HEAD 대비 바이트 재조립 검증 6/6).** 실측: stage TODO 7개 합계 ~288k → ~64k 토큰(−78%), `TODO_parser_ifrs17.md` 128k → 14k. 규칙(CLAUDE.md 핸드오프 절): Status 는 최신 5개만, 밀려난 것은 아카이브 헤더 아래에 잘라 붙임. 2차 후보(미착수, owner 판단): CLAUDE.md·stage 프롬프트의 '왜 생겼나' 서술 → 규칙 한 줄 + 포인터로 압축; `TODO.md` K-ICS 면제 등재부(340줄) 안의 superseded 스냅샷 분리.

**🟢 2026-08-30 현재 — 게이트 전부 통과, 라이브 배포 정상.** 실측:
`validate_data_contract` RED=0 exit 0 · `validate_kics_disclosure` RED=0 exit 0 ·
`validate_live_artifacts` RED=0 exit 0 · `prepush_check.py` exit 0 · inbox 활성 스레드 **0건**
(위생 위반 0). 2026-08-29~30 에 브랜치 push 3회 + `main` 라이브 배포 1회가 실제로 나갔다.

> **아래 2026-08-21 문단의 "현재 push 는 차단 상태" · "라이브(main) 배포도 이것 때문에 대기중"
> 은 그 시점의 사실이고 지금은 아니다.** `R2_순자산합` IDENTITY_TAUTOLOGY 는 해소됐고,
> main 의 `kics_disclosure.json` 은 브랜치와 **바이트 동일**(2026-08-30 실측: main 이 추적하는
> 39개 파일 중 브랜치와 다른 것은 `.gitignore` · `PL_breakdown.json` · `public_exports/` 3개뿐).
> 이 문단들은 이력으로 남겨 두되 현황으로 읽지 말 것.

> **📊 2026-08-30 듀레이션 공시현황 census (owner 지시: "공시현황부터 체크")**
>
> **결론: 듀레이션 수치는 어느 원천에도 없다. 갭은 유도할 수밖에 없고, 그 유도 입력은
> 96.6% 차 있다.**
>
> | 원천 | 실측 |
> |---|---|
> | DART 사업보고서 본문 (39사 최신 연차) | '듀레이션' 언급 37사인데 **전부 회계정책 서술문**("보장단위 수는 … 예상 듀레이션에 의해 결정됩니다"). 자산·부채 듀레이션 수치 **0사** |
> | K-ICS 정기경영공시 MD (497개) | 언급 66개 파일·28사, **전부 서술만**("듀레이션 갭 한도를 설정하여…"). '`X.X년`' 형태 수치 **0사** |
> | 금리 시나리오별 순자산 (항목41~46) | **완비 226/234 = 96.6%** — 아래 표 |
>
> 시나리오표는 반기·연차에만 공시되므로 짝수분기 6개 × 39사 = 234셀이 모집단이다.
>
> ```
> 분기별 완비(6/6) 회사수: 2023.2Q 37 · 2023.4Q 38 · 2024.2Q 37 · 2024.4Q 38 ·
>                        2025.2Q 37 · 2025.4Q **39/39**
> 구멍 8칸뿐 — AIG손해보험 5칸(2023.2Q~2025.2Q, 2025.4Q부터 적재) ·
>              서울보증보험 3칸(반기 미공시, 연차만 낸다)
> ```
>
> **함정 기록**: 1차 탐지기가 `듀레이션[^<]{0,80}(\d+\.\d+)` 였는데 DART 표는 라벨과 값이
> 서로 다른 `<TD>` 에 있어 **0사**가 나왔다. 태그를 벗기고 다시 재서야 실체(서술문뿐)가
> 확인됐다 — "키워드 0회 = 원문 없음" 으로 결론내지 말 것(이 저장소가 세 번 데인 함정).
>
> **다음 단계**: 유도식은 owner 가 이미 준 형태(base 대비 시나리오별 gap → max(상승,하락)²
> + max(평탄,경사)² 의 제곱합 계열)와 같은 축이고, 그 계산은 이미 `36_irr` 로 구현돼 돌고 있다.
> 남은 것은 그 결과를 **듀레이션 연수로 환산할지, 순자산 민감도 그대로 보여줄지** 의 표현 결정뿐이다.
> owner 지시: **당장 착수하지 말 것.**

**🔒 2026-08-21 — push 게이트가 이제 git 훅으로 강제된다. 새 클론/워크트리면 먼저 `git config core.hooksPath .githooks`.**
그 전까지 `prepush_check.py` 를 부르는 코드가 0이었다(참조 11곳 전부 문서, CI 없음, 훅 없음) — "배선했다"와
"강제된다"가 달랐다. 훅 체인 = 데이터계약 게이트 + inbox 위생(`scripts/check_inbox_hygiene.py`) +
오프라인 테스트 126개(`tests/test_rule_coverage_manifest.py` 포함), ~84초. 실제 `git push` 차단 확인.
상세: `docs/claude-changelog.md` 2026-08-21.

**🔴 2026-08-21 (2차) — 그 훅이 정작 `validate_kics_disclosure.py` 를 안 불렀다.** 바로 위 문단이
"강제된다"고 선언한 그 커밋이, `CLAUDE.md` 가 **mandatory** 라고 못박은 K-ICS 룰게이트(5.9초)를
빠뜨렸다. 전수확인: `scripts/validate_*.py` **8개 중 훅이 부르던 것은 1개**. 3개는 통과 중인데
미배선, 1개(`validate_csm_waterfall`)는 **실패 중인데 미배선이라 아무도 몰랐다**. 흔적은
`validate_data_contract.py` L305 주석에 남아 있었다 — *"(prepush_check 는 이걸 호출하지 않는다)
여기서 같이 건다"*, 즉 빠진 게이트를 눈치챌 때마다 **룰을 한 개씩 베껴 심고** 있었다.
지금 1b(K-ICS 룰게이트)·1c(도메인 게이트 3종)로 배선했고, **`tests/test_push_gate_wiring.py`**
(12 tests, 훅 묶음에 포함)가 새 `validate_*.py` 는 WIRED 이거나 사유 있는 NOT_A_PUSH_GATE 여야
한다고 강제한다. **현재 push 는 차단 상태** — 원인은 `R2_순자산합` IDENTITY_TAUTOLOGY 2건
(적용전·적용후). parser 가 넘긴 "image-only 24셀이 원인" 가설은 실측 반증됐고(제외해도
excess 1.25→1.23 / 1.43→1.40), 진짜 신호는 회사 단위 이봉분포다(KR0069 9/9 · KR0008 12/13 ·
KR0050 12/13 이 비스캔사 / 반대로 KR0073 은 13칸 중 1칸). 티켓 `inbox/validation/20260821T1830Z`.
**라이브(main) 배포도 이것 때문에 대기중** — main 의 `kics_disclosure.json` 은 2026-07-21 판이라
지난 한 달(적용후 710칸 변경 + 신규 204칸)이 미반영이고, 배포 사본은 `deploy/20260821-json` 준비완료.

Cross-stage focus (2026-08-20): K-ICS gate **RED=12**, all three offenders already documented below as image/scan-only source (KR0087 동양 2023.2Q ×7 · KR0097 하나생명 2024.2Q ×4 · KR0079 미래에셋 2023.2Q 8_life ×1) → gate contract satisfied. **✅ 닫힘 (parser 2026-08-20, inbox `20260706T0502Z` iter-2):** 적용후 하위 census 결측 4→**0** · 적용후 요구자본 continuity break 34셀/5(회사,분기)→**0** · 적용후 조정항목(22/23) review 17→**5**(전부 사유 기재). Open cross-stage tails: 항목4/12/13 값_적용후 18사 미러링 오염 후속 감사. (**tier2 소진율 분자 정의는 2026-08-20 종결** — DART per-bond 리베이스로 100%+ 0건.) Mid-long-term: duration-gap (MLG-1), K-ICS 시장위험 분해 (MLG-2) blocked on owner decisions.

**🔴 2026-08-21 업데이트 — validation이 면제 근거 raw 재검증으로 위 "gate contract satisfied"를 반증.** `INTERNAL_MODEL_36IRR_EXEMPT`(5건)·`_AFTER_SUBRISK_NOT_DISCLOSED`(5→1)·`_POST_PARENT_NOT_DISCLOSED`(3→1) 등재사유가 raw 대조에서 거짓으로 확인돼 해제됨(상세: 아래 `INTERNAL_MODEL_36IRR_EXEMPT` 항목 갱신분 + `inbox/parser/20260821T1600Z`·`20260821T1620Z`). parser(kics) 처리 결과: **하나생명(KR0097) 2024.4Q item16/17 값_적용후 = 실제 결함으로 확정, raw p281 값으로 fix 완료**(1건 종결). 36_irr 5건은 raw에서 items 41-46 정식 로드했으나(더는 결측 아님) 표준 derive식이 공시 금리위험액을 5.25~25.6% 벗어나 **RED 잔존**(같은 근본원인이 완전성 확보로 `TRANSITION_AFTER_IRR_MISMATCH` 4건도 새로 노출 — 이전엔 41-46후 결측이라 미판정이었을 뿐 통과였던 적이 없음, false-green 아님). 흥국생명(KR0071)×4·흥국화재(KR0005)×1 은 **디스크의 raw가 K-ICS 공시가 아니라 DART 사업보고서임을 validation이 확인**(`inbox/downloader/20260821T1625Z` refetch 대기) — parser 손 안 댐. `validate_data_contract.py` RED: 10(면제 해제 직후 노출분, display-scope) → **13**(TRANSITION_AFTER_IRR_MISMATCH 4건 신규 노출 − 하나생명 1건 종결). RED 증가는 회귀가 아니라 이전에 결측이라 못 보던 동일 결함이 완전성 확보로 드러난 것. 남은 13건 전부 parser 소관 밖 결정 대기 — 36_irr/TRANSITION_AFTER_IRR_MISMATCH 8건(같은 근본원인)=공식·스코프 불일치 owner 검토, 흥국생명·흥국화재 5건=downloader refetch 대기.

**규칙문서 리팩토링 (2026-08-06, 리팩토링 6차 — 상세는 `docs/claude-changelog.md`).** 코드가 아니라 프롬프트·인덱스 층의 context rot을 `claude-md-management` 6축 rubric으로 실측. 고침: ① `CLAUDE.md` 진행도표가 designer/publishing을 "skeleton"으로 오표기(실제론 §5.1~5.5·§5/§9/§10로 종결) → 실측 교체 + 잔여 TBD 정본을 각 프롬프트로 단일화, ② venv 경로 미기재(맨 `python`은 docling 없어 `--stage parse` 즉사) → `## 🐍 실행 환경` 신설, ③ kics 도메인doc 플로우 링크 4개 깨짐 수정. **잔여 2건:**

- [x] **DOC-1 단일소스 위반** — owner 결정(2026-08-06): **문서 재배치 대신 게이트**. keep-list는 이미 `test_docs_agree_with_what_pages_fetch`가 현실과 대조 중이었고(4곳 중 2곳), 무방비였던 골든표에 `test_golden_table_docs_agree_with_tests` 신설 — 신설 골든 누락 + dangling 개명 양방향 차단, mutation 2종으로 실발화 확인. 나머지 사본은 문서로 안 지키고 기계로 지킨다.
- [x] **DOC-2 publishing 프롬프트 자기모순** — §1(L107) "`data/ifrs17/viz` cutover 대기" vs §9(L266) "2026-06-16 LANDED". publishing이 드레인·처리: `git ls-tree -r main` 실측으로 §9가 맞음을 확인(라이브는 `data/dart/viz/*`, `data/ifrs17/viz`는 repo 어디에도 없음) → stale한 §1 Path note 삭제, §9 문구를 실측 근거로 교체, §9 delete-list 예시에서 죽은 경로 제거. orchestrator 독립 재확인 후 `inbox/_resolved/`로 아카이브.

**🟢 소스 교체 (2026-08-19, owner 발견) — 항목5 발주의 전제가 바뀜.** owner: "dart 공시 5. 재무건전성 등 기타 참고사항 부분에 깔끔한 표로 잘 있는데 왜자꾸 삽질해? 기적립액+신규전입액 자시고 할것도 없이 여기 기말 기준 적립액 다 들어가 있잖아". 실측 확인(메리츠 2026.2Q rcpNo 20260814002253): `II. 사업의 내용 → 5. 재무건전성 등 기타 참고사항 → 가.`에 **기말 적립액이 3개 기간치 표**로 있고 단위(백만원)도 명시. 해약환급금준비금 3,536,425 / 2,976,566 / 1,793,089 — 같은 필링 BS의 기적립액 2,976,566 + 예정액 559,859 = 3,536,425로 검산 일치. **이 표가 A(기적립액+전입액 산술)·D-1(6사 주석 추출 실패)·B(역방향 채움)·C(2022년말)를 대부분 없앤다** — 3기간치라 결측이 실값으로 채워지고, FY2024 필링의 전전기 열이 곧 2022년말이다(소급 가정치 아님). 덤: 같은 표에 보험계약자산/부채·재보험계약자산/부채·투자계약부채(항목 14/20/21/22), 바로 아래 "나. 지급여력비율"까지 있다. **함정**: 소제목이 회사마다 다르고(메리츠 "보험계약자산부채 및 준비금현황"/현대해상 "준비금 적립내역"/삼성화재 "보험계약부채 및 자산 현황") 문자열 find()로 절을 찾으면 목차·본문에 오탐한다(오케스트레이터 실측 — 한화생명·삼성생명·교보생명에서 발생). 구조적으로 절 경계를 잡을 것. 커버리지 census 선행. 종결조건(업권 합계 32.2조 ±5%)은 불변. 발주문에 배너로 반영됨.

**🔴 17BS 항목5(해약환급금준비금) 3건 + 2026.2Q 결측 10사 (2026-08-19 owner, 마스터 xlsx 리뷰).** owner가 "17BS" 시트에서 발견. 발주 2건:
> - **downloader** `inbox/downloader/20260819T0116Z__owner__MULTI_2026.2Q__fs_api_halfyear_negative_cache.md` — 2026.2Q가 14사뿐(2026.1Q는 24사). 원인은 파싱이 아니라 **빈 응답이 캐시에 굳은 것**: `_fs_api_cache/<corp>_2026_11012_*.json`이 `status 013(데이터 없음)/0건`인데 mtime이 전부 08-15 새벽 — 반기보고서 접수(08-14) 직후라 API 적재 전에 긁었다. **08-19 라이브 재호출로 메리츠·삼성생명·현대해상 모두 `000 정상` 확인** → 재취득만 하면 된다. 재발방지로 `013`은 캐시에 굳히지 말 것(안 고치면 다음 분기 그대로 재현).
> - **parser/ifrs17** `inbox/parser/20260819T0116Z__owner__MULTI__surrender_reserve_item5_semantics_and_backfill.md` — ① **항목5 = 기적립액 + 당기 전입액**으로 정의 변경(owner 재지시, 과거 중단분 재개). 지금은 기적립액 단독이고 전입액은 다음 FY Q1 롤포워드에만 쓰여 **FY말 값이 그 해 전입액만큼 과소 + 시리즈가 1년 밀린다**(raw 확정: 현대해상 2023년말 3,422,425인데 마스터 2023.4Q=0·2024.1Q=3,422,425. 메리츠·한화손보·롯데·삼성화재 동일 패턴). ② 미공시 분기 **역방향 채움** 추가(현행 순방향만) — 스코프는 FY 내부로 한정(FY 넘으면 삼성생명류가 2026 값으로 과거를 덮는다). ③ **2022년말 = 채워야 한다** (오케스트레이터 2회 오판 후 정정, owner가 기사 2건으로 반박). 폐기된 근거 2개: (1차) "31개 전수 스캔, 비영 0건" → 실제 13개만 매칭·대형생보 전부 미탐, (2차) "기사 23.7조 = 2023년말" → 부분합 16사 + DB손보 부호오류 + 한화생명 `3`으로 만든 23.0조를 잘못 맞춘 것. **21사로 재측정하면 2023년말 28.2조, 누락사 더하면 31조대 = 기사의 32.2조와 일치.** 따라서 23.7조(2022년말)는 별개 실재 수치. 소스는 FY2023 필링의 **준비금 반영후 조정이익 표 전기 열**(`parse_filing()`이 `r[-1]`을 버리는 중) — 성격은 한화생명 각주대로 "전기초부터 적용 가정 산출치"(전기 1,269,282백만). 단 전기 열 수확이 까다롭다(발주자 스캔은 이연법인세 표를 오인해 10.6조로 실패). **수용기준 = 업권 합계 대 보도치: 2022말 23.7조 / 2023말 32.2조 / 2024.6말 38.5조 / 2026.6말 58.1조, ±5% 안에 들 때까지 닫지 말 것.** ④ **2023년말 회사별 census 완료(2026-08-19, owner "2023년말부터는 딱 다 맞아야")** — FY2023 raw 31사 전수: 추출성공 18사 27.7조 vs 기사 32.2조, **차액 4.5조의 출처를 전부 특정.** 값은 있는데 못 뽑은 6사(한화생명 2,504,752=처분계산서에 있음·현재 마스터는 `3` / DB생명 1,633,087 · KB라이프 790,407 · 동양 640,201 · 하나생명 62,137 · 흥국생명 6,257 = 라벨접미사 없는 이익잉여금 내역 표·전입액 표기) → 채우면 33.3조. 진짜 0 2사(삼성생명·교보생명 "적립한 내역은 없습니다" 명시 → 삼성생명 0 오탐 철회). 값 깨진 2사(DB손보 필링 4,278,867 vs 마스터 △2,645,780 부호+값 불일치 / 라이나 2,251,256 = 총자산 대비 과대, 1000배 전례). 미확인 5사(ABL·처브라이프 언급없음 / 엠지·KDB·푸본현대 숫자미발견). **종결조건 = 2023.4Q 합계 32.2조 ±5%, 못 들면 남은 회사 명시.** ⑤ 같은 재빌드에서 항목5 오염 동반 수정(DB손보 부호반전·한화생명 2024.1Q `3`·AIG 2년 밀림·메트라이프 스케일·삼성생명 2025.4Q `0`).
> 선후관계: downloader 재취득 → parser 재빌드(골든 `test_ifrs17_bs_golden.py` `--update`) → xlsx 재생성(**`build_master_xlsx.py`는 파일 전체를 새로 씀** — 현재 시트 9개, changelog가 말하는 "17BS_PIVOT"은 이미 소실된 상태라 owner 확인 후 진행).

**🔴 2026.2Q 반기 + 2026.1Q 정정공시 = 현재 최우선 (2026-08-14 owner).** 오늘이 반기보고서 법정기한 — 한화생명(KR0068)·한화손보(KR0002) 2사만 확보(body XML + FS API `*_2026_11012_*` 둘 다 실측 확인), 나머지 37사는 오늘~내일 순차 제출 예상. 2026.1Q는 **18사가 정정공시**를 냈고 raw는 정정본으로 교체됨(commit `33111fb`) — 라이브 2026.1Q 숫자가 구버전 기준일 수 있어 **정정 재추출이 신규 분기보다 앞선다**. 발주: downloader `20260814T0149Z`(반복 스카우팅 + **body XML과 FS API 캐시를 같이** 받을 것 — equity 마스터는 FS API를 먹는다 + 정정 18사 FS 캐시 stale 여부 확인), parser `20260814T0149Z`(기존 open 2건의 순위 상향: `20260814T0000Z` 정정 18사 → `20260813T0600Z` 한화 2사, 2026.2Q는 CSM/PL/equity 3개 마스터 동시). **BS 세부항목 = 그 다음** — 아래 BS-TACCOUNT로 승계(그 예고 파일명 `..._bs_line_items_full`은 생성된 적 없음).

**BS-TACCOUNT + 배당 탭 (2026-08-14 owner 저녁 발주, cross-stage).** owner 원문: *"OpenDart API 이용해서 BS 추가항목들 좀 추가 (…) 17.html 맨 위로 올리고 재무상태표처럼 왼쪽 자산 & 우상단 부채 & 우하단 자본 (…) + 아이콘 클릭하면 세부"* / *"배당현황도 전부 OpenDart API로 크롤링 & 별도 탭에 게시"*. 발주 3건:
> - **parser/ifrs17** `inbox/parser/20260814T1250Z__owner__MULTI__ifrs17bs_detail_lines_for_taccount.md` — `IFRS17_BS.json` 항목 1-7에 BS 세부계정 추가. **신규 fetch 불필요**(오케스트레이터 실측: `fnlttSinglAcntAll` = 전체 재무제표라 `_fs_api_cache` 261파일/24사 안에 BS account_id 95개가 이미 있음). 스키마 계약 = 기존 8열 + `섹션`(자산|부채|자본|준비금)·`레벨`(1|2), 항목번호 블록 자산10-29/부채30-49/자본50-69. 수용기준 = **섹션별 폐쇄검산**(Σ L2 == L1 총계, 잔차는 명시 항목으로 emit·5% 초과 시 매핑 미완 보고). 최대 함정 = 부모/자식 태그 공존(상각후원가 계열)의 **이중계상**. 세부는 Tier-1 24사만(비상장 15사는 총계뿐 → 문서화 예외).
> - **designer** `inbox/designer/20260814T1250Z__owner__IFRS17__bs_taccount_top_panel.md` — Panel 7을 **최상단**으로 이동 + T자(좌 자산 / 우상 부채 / 우하 자본) + `+` 버튼 2단 드릴다운. **항목번호 하드코딩 금지, 섹션·레벨로 그룹핑** → 파서 랜딩 시 HTML 무수정. `IFRS17.html:172-176`의 "L2/L3는 오케스트레이터 과도주문" 주석은 **오늘 owner 직접 요구로 무효** — 보존된 L2 코드 재사용. 파서 대기 없이 착수 가능.
> - **downloader** `inbox/downloader/20260814T0746Z__...__dividend_disclosure_recurring_onboard.md`(기존 스레드에 스코프 확정 추가) — alotMatter 전사 39사 × FY2023~FY2026 × reprt 4종(owner: 반기 전부 + manageable하면 분기까지 → ~620콜/4-5분으로 전부 확정), raw는 `data/dart/_alotmatter_cache/`에 원본 그대로. **탭은 빈 `공시보고서.html`을 배당으로 채운다**(owner 확정, 새 탭 신설 아님). 체인 진행(2026-08-15 00:30 기준): downloader ✅(raw 624파일) → parser ✅(`dividend.json` 1,924행 · 24사 × 14분기 · `scripts/build_dividend.py` · xlsx `배당` 시트) → **designer 진행중**(`공시보고서.html` 아직 "준비 중" 껍데기) ∥ **publishing 대기**(`inbox/publishing/20260814T2230Z`에 P-1~P-4 추가: dividend.json **git 미추적** · keep-list 문서 2곳 · xlsx 재생성 불필요 · 게이트 통지 전 push 금지) ∥ **validation 신규 발주**(`inbox/validation/20260814T1625Z`: `MASTER_FILES` 미등록 = 게이트가 이 마스터를 안 봄 → 배선 + 룰 3개(payout identity 46셀 / census 336-310=26셀 결측이 013인지 / 항목6 전행 0·항목5 264행 0의 0값 맹점) + 루트 배당 xlsx 교차대사).

**EQUITY-AOCI (신규, 2026-08-13 owner 발주) — 자본구성 마스터 `equity_composition.json`.** 회계법인 발표자료가 K-ICS 비율과 나란히 기타포괄손익누계액(AOCI)을 핵심지표로 쓰는 걸 owner가 보고 발주. **타당성 확인 완료(오케스트레이터 실측)**: 주 소스는 이미 디스크에 있다 — `data/dart/_fs_api_cache/`(DART `fnlttSinglAcntAll.json`)의 BS/SCE에 표준 account_id로 전부 잡힌다(`ifrs-full_AccumulatedOtherComprehensiveIncome`, `dart_SurrenderValueReserve` 등). SCE `account_detail`의 AOCI 컬럼이 **자산측 FVOCI 평가손익 vs 부채측 보험계약순금융손익 미스매치**로 분해되고 BS 스톡과 정확히 닫힌다(흥국화재 2025.4Q 실측). 커버리지: 24개사 × 11분기 즉시 / 15개사 XBRL 부재 → Tier-2(본문 XML) / 2023.1Q·2Q 백필 필요. **분류 정정**: 해약환급금준비금은 AOCI가 아니라 **이익잉여금 내 법정적립금** — 두 축으로 분리해 설계(발주문에 명시). 5개 stage inbox 발주 완료(`inbox/*/20260813T0422Z__owner__MULTI__*`). 순서: downloader(백필·카탈로그) → parser/ifrs17(마스터) → validation(항등식·census·게이트) → publishing(keep-list·xlsx) ∥ designer(패널 목업, 게이트 통과 전 배포 금지).

> **⚠ 범위 정정 (2026-08-14, owner) — 위 발주가 과설정이었다(오케스트레이터 오류).** owner 원문은 "high level 17BS(자산/부채/자본/AOCI)를 **빠르게** OpenDART API로, 가능하면 해약환급금준비금까지 **안되면 pass**"였는데, 발주문이 항목 30개·항등식 6개·census RED·Tier-2 본문XML 폴백·워터폴 패널로 부풀었다. 결과 RED 182 중 **160건이 "안되면 pass"라던 해약환급금준비금(항목10)을 필수 코어로 못박은 탓.** 정정 발주 2건: ① validation `20260814T0035Z` — census 코어를 **[1 자본총계, 6 AOCI, 40 자산총계, 41 부채총계]** 로 축소, 항목 10/11·5·20-31은 optional(YELLOW), ② parser `20260814T0035Z` — **Tier-2 중단**(15개사 본문XML 파싱 취소), Tier-1(FS API) 24개사×11분기로 종결. 이미 만든 마스터·빌더·골든은 **롤백하지 않는다**(같은 API 응답에 딸려온 항목이라 유지비 0).
**owner 2차 결정 (2026-08-13, iter 2 — `inbox/{parser,designer}/20260813T0436Z__*`):** ① **배치 확정 = `IFRS17.html` 신규 섹션 `7) 재무상태표 · 자본의 질`** (신규 페이지·K-ICS.html 아님, 기존 6개 섹션 불변). designer의 "배치안 owner 결정" 질문 종결. ② **범위 = 3단 드릴다운** — L1 자산총계/부채총계(그중 보험계약부채)/자본총계 → L2 자본 구성 6종 → L3-a AOCI 분해(자산측 FVOCI vs 부채측 보험계약순금융손익 미스매치) · L3-b 이익잉여금 내 법정준비금 3종(해약환급금 강조). ③ L1이 비어 있어 **파서에 BS 상위 항목 40~49 추가 발주**(`ifrs-full_{Assets,Liabilities,InsuranceContractsIssuedThatAreLiabilities,...}` — 오케스트레이터가 같은 캐시에서 67/67 실측). 신규 항등식 3개(`40==49`, `40==41+1`, `42<=41`). 마스터 파일명은 `equity_composition.json` 유지(5개 문서 동시수정 회피, DOC-1 패턴). ④ 패널 C(업권 추이)는 이번 범위에서 제외(별건).

**Reorg #2 (2026-05-30j)** — `data/assoc/` → `data/_derived/`; KIDI/DART → `FY####_Q#` 컨벤션 통일. **DART batch script refactor 잔여** → `TODO_downloader.md` REORG2-DART.

Session start: read this root file first, then the relevant stage's `TODO_<stage>.md`.

NOTE: English only where Korean encoding is fragile. See `CLAUDE.md` "Document/TODO Encoding Rule".

---

## ✅ data-contract gate pending exceptions — **종결 (2026-08-20)**

2026-06-20에 열었던 `RED=4, 전부 tier2(보완자본 소진율)` 건은 **전량 해소됐다.** 실측:

```
validate_data_contract.py     RED=0  YELLOW=276  exit=0
kics_tier2_utilization.json   100% 초과 = 0 / 39사  (data_source: dart_bonds_fy2025_경과조치)
신한이지 분모                  2.68억(오파싱) → 268.0억 = SCR 536 × 50%
```

원인 제거는 **FSC Face → DART per-bond 리베이스**(`_resolved/20260803T0055Z`)가 했다 — 분자를
후순위채 발행잔액으로 교체하는 원래 처방과 같은 방향이었고, 동양생명 240%·KB손해 218%·
미래에셋 126%가 전부 100% 아래로 내려왔다(동양 84.2%). 면제행 OCR도 불필요해졌다.
경위: `inbox/_resolved/20260616T1529Z` · `20260616T0506Z` 종결 노트.

---

