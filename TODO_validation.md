# Insurequant Validation TODO (Stage 3)

> Last updated: 2026-09-23 (`kics_duration_gap.json` 라이브 배선 — `check_kics_duration_gap` 신설로 무검사 아티팩트 0 복귀) · 2026-09-21 (금리민감도 RS6_PHASE_LEVEL_CENSUS(RED) 신설 + RS2 적용후 앵커 + 36_irr 티켓 판정(c) — 마스터 무수정, 흥국생명 2칸 RS2 RED 로 push 게이트 차단 중, parser 발주 `20260921T1400Z`) · (배포 HTML JS 런타임 게이트 신설 — `DEPLOYED_JS_UNDEFINED_CALL` 을 `prepush_check.py` §1f 에 배선. 배포 HTML 의 `<script>` 를 읽는 검사기가 저장소에 0개였다; 오탐 0 · 정의삭제 변이 172/183 · 0.09초; 잔여 UH-26/UH-27) · (경영공시 PL 백필 ⑤ 병합 후속 — **`_check_pl_bridge`(leg-coverage 2e · ZERO_LEGS 2b) 소스인식**; 12차가 `coverage_holes` 만 바꾸고 이 두 축을 빠뜨려 `pl_new=153` 으로 push 가 막혀 있었다. 같은 resolver(`pl_cell_source_ids`) 재사용 · 가드는 '원천이 정말 안 실은 모양'으로 좁힘 · SKIP 을 `src_na(DISCLOSURE)` 로 세어 인쇄. `pl_new` 153→0 · `zero_legs` 97→9(DART 9 보존) · 거짓 PASS 2건도 SKIP 으로 닫힘 · selftest 69→75(killer 변이 7종, 6/6 사망) · 골든은 2×2 귀속 대조 후 `--update`. 마스터·등재부 무수정; 직전 경영공시 PL 백필 **병합 선행조건 ②③④ 배선** — 계보 등재 4건 + `SOURCE_ID_LINEAGE_MISMATCH` 를 capsec guard 밖으로(비-capsec 계보가 그동안 무검사였다: `kics_rate_sensitivity` 138셀 판정 None) · PL provenance 첫 검증(호출처가 0 이었다 → published 731셀) · `coverage_holes` 기대그리드를 셀 계보별로(병합 후 real hole 118→6, 오늘은 바이트 동일이라 골든 불변) · `CONCEPT_REGISTRY` 에 `pl_disclosure_vs_dart` 등재 + **리더**(allowlist 강제). `DERIVED` 는 계보 미등재(널 경로 라벨 = 보편적 탈출구) 대신 게이트 재계산 기반 좁은 면제. selftest 57→69(BS_KICS 2축 잔여 해소 포함), 12건 전부 killer 변이로 반증. 마스터 미수정; 직전 항목4/12/13 미러링 **재감사 정정** — "오염 170셀" 은 과다계상, 실제는 `item13` 55셀뿐이고 `item4`·`item12` 114셀은 정상. 1차 발주의 "170셀 삭제" 를 실행했으면 정상 셀 114개가 지워졌다. 버킷 판정을 셀 판정으로 승격시킨 것이 원인 — Δ의 귀착 항목을 안 쟀다; 직전 경영공시 출처 PL 백필 **계약 판정** — 항목 3개·회사 1개 제외 + 병합 순서 확정; 지금 규격대로면 census RED 0→80; 새 사각 2종 적발: PL provenance 사이드카가 죽어 있음(638셀 source_file 0) · "자식 present·부모 None" 29버킷 무검사; 직전 UH-25 게이트 축 해소 — `JP_ESR_UNVERIFIED_VALUE` 신설: 값 검증 두 축이 동시에 침묵하는 상태를 YELLOW 로 세고 push 묶음이 막는다; 직전 UH-23 정식 해소 — 한정어 정본 §3 표 ↔ `ADJUSTED_QUALIFIERS` 양방향 대조 배선 + TODO 과장 정정; 직전 jp `JP_ESR_ADJUSTED_FIGURE` 배선 — 조정치 축, UH-21 해소 → PM-2026-09-13 `closed`; 직전 jp `JP_ESR_NOT_IN_SOURCE` 배선; 직전 push 범위 판정을 훅에 구현 — CLAUDE.md §5 가 문서로만 있던 규칙을 코드로; 직전 jp false-green 포스트모템·UH-18 등재; 직전 2026-09-02 MASTER_XLSX_* 축 신설 — 마스터 JSON ↔ 마스터 xlsx 13시트 전수 대조를 CHECK 8 로 배선) · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Changelog: docs/changelog_validation.md

Session start: read this file + `claude-agent-validation.md` + domain refs (`docs/domains/claude-agent-{kics,ifrs17}.md`). English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

**🔌 2026-09-23 (16차) 라이브 듀레이션갭 마스터에 검사기를 붙였다 — `test_push_gate_wiring` 이 스스로 잡아낸 구멍.**
2026-09-22 배포(main `22e2471`)로 `K-ICS.html` 이 `kics_duration_gap.json` 을 fetch 하기 시작했는데 그 파일을 읽는 검사기가 0개였다. 배포 **직전** 게이트는 통과했다 — 그때는 아직 main 에 없어서 `_origin_main_fetches()` 가 못 봤기 때문이다. 즉 이 테스트는 "새 파일이 라이브에 붙은 다음 라운드" 에 켜진다. 설계대로 작동했지만, **배포 라운드에서는 그 사실을 미리 챙겨야 한다**(배포 전에 선언을 먼저 넣어라).
- `scripts/validate_live_artifacts.py` 에 `check_kics_duration_gap` 신설(3축, 형식검사 아님): ① census — `kics_disclosure` 항목41 이 있는 (분기,회사) 270/270 행 존재 ② 파일 안에서 닫혀야 하는 산수 — 시나리오 컬럼으로 자산D·부채D·갭 재계산 792/792 일치. 갭은 `D_A-(L/A)xD_L` 을 전개한 형태로 검산해 부채 충격전이 음수라 D_L 이 빈 회사(라이나·AIG)에서도 축이 안 죽는다 ③ `kics_disclosure` 항목41~46 교차대조 — `자산_X-부채_X` vs 순자산가치, 1,607 pass.
- **허용오차를 공시 자릿수에서 유도한다**: 시나리오 컬럼이 억원 소수 2자리라 차분에 ±0.01 이 실리고, 듀레이션 밴드 = `0.01/(2%x분모)`. 고정 1e-3 으로 짰더니 금리부자산이 **0.39억원**뿐인 카카오페이손보 2023.2Q 가 3건 오탐으로 떴다(공시 컬럼 6개 시나리오가 전부 같은 값으로 반올림돼 공시된 듀레이션을 재현할 자릿수가 없다). 밴드를 쓰면 삼성생명급에서는 ±2e-7 로 날카롭고 그 회사에서만 침묵한다 — **공시가 설명할 수 있는 만큼만 검사한다.**
- 진짜 RED 1건은 이미 발주된 건이었다: AIA생명 2024.4Q 항목46 이 억원 아닌 백만원(3,607,646 vs 36,076.46, 100배). 룰 `36_irr` 은 `max(base-steep,0)` 때문에 이 방향에 구조적으로 눈이 멀어 이 축이 처음 잡았다. `data/_gold/live_artifact_baseline.json` 에 **건별 1줄** 등재(사유 = `RULE_REASON`, 티켓 `inbox/parser/20260922T1200Z`). 고쳐지면 STALE 로 뜬다.
- `tests/test_push_gate_wiring.py::LIVE_ARTIFACT_READERS` 에 선언 추가 → 152 passed. `validate_live_artifacts` RED=0 / YELLOW 18 / STALE 0.

**🔌 2026-09-21 (15차) 금리민감도 phase 레벨 census `RS6_PHASE_LEVEL_CENSUS`(RED) 신설 + RS2 를 스펙대로 적용후까지 앵커 + 신한라이프 `36_irr` 티켓은 커버리지 구멍이 아니라 TODO.md 표 결손으로 판정.** 마스터는 한 칸도 안 건드렸다. 티켓 `inbox/validation/20260921T0100Z`(parser, RS6) · `20260921T0215Z`(owner, 36_irr) 둘 다 `status: answered`. 발주 `inbox/parser/20260921T1400Z__validation__MULTI_2024.4Q-2025.4Q__ratesens_phase_level_holes.md`(lane: kics).

> - **36_irr(owner 티켓)**: 룰 엔진 전수 census(`scripts/_probes/_probe_20260921_36irr_census.py`) — **538 버킷 / 538 finding, 미평가 0**. 짝수분기 item36 보유 270 버킷 전부 41-46 완비(GREEN 209 · YELLOW 55 · 박제 SKIP 6), tol 밖인데 RED 아닌 6건 = 전부 `IRR_DERIVE_ISSUER_INCONSISTENT` 등재분(미등재 0). 신한 2025.4Q 잔차 +863.8221 · 2026.2Q +2,979.8031 = 박제와 Δ 0.0. `report_latest.json` 36_irr×2026.2Q **39건**(티켓의 "0건" 재현 안 됨). 분류 **(c)** — 빠진 것은 **TODO.md §36_irr 표의 2026.2Q 행**(코드·원장 6건·pin 테스트 6쌍에는 있었다) → 행 추가 + "5건"→"6건" 정정. 룰·tol·픽스처 무수정.
> - **RS6 census(전 분기)**: 코호트 155 버킷 중 rs 138, phase 결측 **30행/10버킷**(적용후만 9 · 서울보증 2024.4Q 적용전만 1) + null 셀 1행(서울보증 적용후 기준금액 5칸 — RS1 이 `bv in (None,0)` 로 건너뛰던 칸). 파서 열거 7 버킷에 **KR0051 2025.4Q · KR0087 2024.4Q · KR0150 2024.4Q 3건 추가**. 10 버킷 전부 헤드라인 전==후. 종류 `ROW_MISSING·NULL_CELLS·UNKNOWN_LABEL·ORPHAN`. **RED** 로 신설(census 는 YELLOW-first 아님 — 결측은 SKIP 이 아니라 RED, 2026.2Q 사고가 YELLOW 면 재발). 선행 31행은 `RS6_KNOWN_HOLES`(routed worklist, 정당부재 아님) — 매 실행 EXC 인쇄, 채워지면 inert YELLOW + 매니페스트 테스트가 해제 강제.
> - **🔴 같은 자리에서 RS2 가 적용전만 앵커하고 있었다** — 스펙 §5 는 늘 "적용후는 값_적용후 있을 때만" 이라 적혀 있었는데 구현이 `if gj != "적용전": continue`. 파서가 3사를 적용전→적용후 **미러**로 채웠는데 그 미러를 대조하는 룰이 0개. 고친 뒤 적용후 387칸 대조(대조불가 1칸 `rs2_na` 인쇄) → 기존 예외 미러 4(DB손해 2025.2Q 3 · 현대해상 2026.2Q 1, 같은 사유라 (회사,분기) 키를 두 phase 에 적용) + **신규 RED 2 = 흥국생명 2025.2Q·2025.4Q 적용후 기준금액**: rs 18,412 / 19,350(총괄표·민감도표가 억원 정수 직접 인쇄, MD L197·L589 / L84·L503) vs `kics_disclosure` item14 `값_적용후` **18415.27 / 19354.44 = item1_후/item27_후×100 역산**(MD 에 그 숫자 부재). 15/22/23 후도 역산값에 정확히 닫혀 있어 14 후만 고치면 R5 적용후가 열린다 → 파서가 함께 정리하도록 발주(§B). 같은 역산 모양 저장소 전체 **40 버킷** 관측만 넘김(결론 아님).
> - **push 게이트는 지금 이 2칸으로 막힌다**: `validate_kics_rate_sensitivity.py` exit 2 → `prepush_check.py` L365 `n_dom |= returncode` → L581 `blocked` → `return 2`. 우회·면제 안 함(fixable RED → parser 발주). `SUMMARY RS1:0RED(+1exc) | RS2:2RED(+8exc) | RS3:64Y | RS4:1Y | RS5:0RED(+17exc) | RS6:0RED(+31known,0inert) | gate RED=2`.
> - **매니페스트 신설** `tests/test_rule_coverage_manifest.py` 금리민감도 절: 룰 id 6종 대조 · 등재부 4종 크기(RS1 1·RS2 2·RS5 17·RS6 11) · known-hole 31행 전건 발화(inert 0) · `rs2_na` 침묵 금지 · 변이 7종(phase 통삭제 → RS6 3행 **and RS4/RS5 무발화 = 사각 증명** · null 셀 → NULL_CELLS and RS1 무발화 · 라벨 오타 · 고아 · 적용후 base +10 → RS2 적용후만 · 등재 구멍 채움 → inert) · 훅 배선/exit 전파 정적 확인 → **12 passed**. `run(rs_rows, kd_rows)` 순수 함수 분리, 변이는 메모리 사본만.
> - 검증: `validate_kics_disclosure.py` **RED=36(전부 documented) · blocking 0 · exit 0**(report_20260921T033131Z) · `test_kics_rules_golden`+`test_rule_coverage_manifest`+`test_push_gate_wiring` **152 passed / 2 skipped** · `tests/unit/test_irr_pin_exemption.py` 9 passed. 문서: `kics-rate-sensitivity-spec.md` §5(RS5 소급·RS6·RS2 정정) · `claude-agent-validation.md` RS 표.
> - **미배선 잔여**: ① 적용후 `36_irr` 축 범위 144 중 **19건 미평가**(`POST_SCENARIO_ABSENT`, 41-46 적용후 결측 — 게이트가 이름으로 인쇄, 2026-09-01 잔여 그대로). ② item14 `값_적용후` 역산 40 버킷의 원천 확인은 파서 판단 대기. ③ `RS5_EXCEPTIONS` 17 건은 여전히 원인 미규명 백필 후보이고 inert 검사가 없다(RS6 에만 넣었다).
> - 재현: `$py scripts/_probes/_probe_20260921_36irr_census.py` · `$py scripts/_probes/_probe_20260921_ratesens_phase_census.py` · `$py scripts/validate_kics_rate_sensitivity.py` · `$py -m pytest tests/test_rule_coverage_manifest.py -q -k rate_sens`.

**🔌 2026-09-21 (14차) 배포 HTML 의 JS 런타임 축 신설 — `DEPLOYED_JS_UNDEFINED_CALL`. 이 저장소에서 배포 HTML 의 `<script>` 를 읽는 검사기는 0개였다(불변식 1번을 데이터 축에서만 지키고 화면 축에서는 한 번도 안 지킨 자리). 현 트리 오탐 0 · 정의삭제 변이 172/183 검출 · 인-프로세스 0.09초. 마스터·배포 HTML 무수정.** owner 티켓 `inbox/validation/20260921T0057Z__owner__ALL__deployed_js_runtime_blind_spot.md`(status: answered) · 포스트모템 `docs/postmortems/PM-20260921_kics_sens_iqp_referenceerror.md`(closed).

> - **사고**: designer 커밋 `2dbc4ca`(2026-09-20)가 `K-ICS.html` 의 `function IQP(){…}` **한 줄**만 지우고 호출부 2곳을 남겨 라이브 금리민감도 패널이 `ReferenceError` 로 죽었다. **게이트는 전 단계 통과**였고 owner 가 눈으로 잡았다. 데이터는 100% 정상 = 고칠 셀 0개.
> - **영향 범위 재측정 — 티켓의 "36사" 를 39/39 로 정정한다.** 예외는 `if (postRatio) { … IQP() … }` 안에서만 터진다. 선택 가능한 (회사,분기) 버킷 **138 중 129(93.5%) 사망**, 살아난 9버킷은 적용전만 있어 색상이 리터럴인 경우(동양 2024.4Q · 삼성생명 3 · 신한이지 2025.4Q · 카카오페이손보 2025.4Q · 하나손보 3). **기본 화면(최신 분기)은 39/39 사 전부**.
> - **정적 축을 골랐다(헤드리스 아님) — 판단 근거를 박아 둔다.** 헤드리스를 차단축으로 쓰면 ① 배포본이 CDN 4종을 로드하는데 훅은 오프라인에서도 돌아야 하고(스텁 = "진짜 페이지가 아닌 것" 을 검사) ② 브라우저 없는 클론에서 **SKIP 이 fail-open** 이 된다. 둘 다 이 저장소가 반복해서 데인 형태라 선행조건으로 적고 UH-26 으로 남겼다.
> - **오탐 억제가 설계의 전부다**: `바인딩` 은 과대추정(스코프 미해석·구조분해 통째), `참조` 는 과소추정(멤버호출·옵셔널체이닝·메서드축약 정의 제외). 둘 다 "못 잡는 쪽" 으로 틀려 있어 **잡으면 진짜**다. 렉서가 문자열·템플릿·주석·정규식을 제거하므로 CSS `var()`/`rgba()`·한국어 산문 노이즈는 토큰에 안 들어온다(템플릿 `${…}` 안쪽만 재귀 토큰화).
> - **실측**: 4페이지 토큰 **73,175** · 참조지점 **3,627** · **RED=0**(오탐 0). `function NAME(` 전수 변이 **183건 중 172건(94%) 검출**, 미검출 11건 사유 전건 규명(9건 = 같은 이름이 `download-survey.js`/`theme.js` IIFE 안에도 존재 → UH-26 · 2건 = 즉시실행 명명함수식·죽은 코드). designer 가 임시 스윕에서 만난 `formatter`·`afterDraw` 오탐은 **안 난다**(`name(…){` = 메서드 축약 정의 판정).
> - **🔴 작업 중 내 룰의 버그를 실측으로 잡았다.** `.catch(err => {…})` 를 catch 절로 읽어 콜백 본문의 이름을 통째로 바인딩으로 삼켰다(거짓음성 3건: `render`·`setMapStatus`·`fetchFirst`). 멤버 위치 가드 추가로 168→172. **`gtag`/`dataLayer` 는 CDN allowlist 에서 뺐다** — 그건 인라인 GA 스니펫이 만드는 것이라 넣어 두면 스니펫이 지워져도 안 걸린다(빼고도 RED 0).
> - **배선(그 자리에서 확인)**: `prepush_check.py` **L35 import · L409 `n_js = deployjs.main([])`(§1f, `_run_korean_master_gates()` 본문) · L450 언팩 · L581 `blocked` · L600 `return 2`** · `.githooks/pre-push:23` · `tests/test_push_gate_wiring.py` `WIRED` · 오프라인 묶음 `prepush_check.py:547`. **FULL 전용**이고 §0 `ROOT_FULL_SUFFIXES` 에 `.html`·`.js` 가 이미 있어 화면을 고치면 자동 FULL 이다 → 범위 목록 **무수정**(`tests/test_prepush_scope.py` 통과, 가짜 반환값에 `js` 키만 추가).
> - **엔드투엔드 exit code 를 실행으로 봤다**: origin/main 의 깨진 `K-ICS.html` 을 스크래치패드 트리에 놓고 같은 호출 경로로 `prepush_check.main()` → `배포 JS 런타임=BLOCK … BLOCKED` **exit 2**, designer 복구본이면 `clear … gate-clear` **exit 0**.
> - **회귀 박제** `tests/test_deployed_js_gate.py` **24케이스 8.6초** — ① 4페이지 오탐 0 ② `IQP` 정의를 **메모리에서** 지우면 RED(호출부 2줄)·원본이면 GREEN ③ 4종 전부 전수변이 검출률 하한 70% ④ killer 변이 6종 ⑤ 노이즈 내성. **`K-ICS.html` 은 디스크에서 한 번도 수정하지 않았다**(designer 소관).
> - **미배선 잔여**: **UH-26** 런타임 전용 실패(TypeError · `getElementById()` null · 차트 옵션 · fetch 모양 · 스코프 오류) → `inbox/validation/20260921T0630Z__…headless_runtime_smoke_feasibility.md`. **UH-27** 라이브(`origin/main`) 축은 `_live_audit()` 이 **인쇄만 하고 안 막는다**(차단하면 main 이 고쳐질 때까지 무관한 작업까지 막힌다) — **지금 라이브 RED=2**, 배포 발주 `inbox/publishing/20260921T0630Z__…live_main_still_broken_deploy_iqp_fix.md`.
> - 재현: `$py scripts/validate_deployed_js.py` · `$py scripts/validate_deployed_js.py --git-ref origin/main`(사고 재현 RED=2) · `$py -m pytest tests/test_deployed_js_gate.py tests/test_push_gate_wiring.py tests/test_prepush_scope.py -q`.

**🔌 2026-09-20 (13차) 경영공시 PL 백필 ⑤ 병합 후속 — `_check_pl_bridge`(leg-coverage 2e · ZERO_LEGS 2b)를 소스인식으로. 12차 배선의 비대칭을 닫았다: `coverage_holes` 만 소스인식으로 바꾸고 이 두 축을 안 바꿔서 병합 즉시 `pl_new=153` 으로 push 가 막혀 있었다. `pl_new` 153 → 0 · `zero_legs` 97 → 9 · selftest 69 → 75.** 마스터(`PL_breakdown.json`·사이드카·`kics_disclosure.json`·xlsx)는 한 바이트도 안 건드렸다. 등재부 `pl_bridge_baseline.json` 도 31건 불변 — **153건을 등재하지도, 골든으로 박제하지도 않았다.** 티켓 `inbox/validation/20260920T1730Z__parser__…pl_bridge_legcoverage_not_source_aware.md`(status: answered).

> - **같은 resolver 재사용**(`validate_master_tables.py` L1044 `source_ids = pl_cell_source_ids() if source_ids is None else source_ids`). `coverage_holes` 가 `pl_key_items_for()` 로 쓰는 그 함수를 그대로 물렸다 — **두 번째 계보 판정기를 만들지 않았다.** 12차에 census 가 두 곳에 따로 구현돼 118 vs 6 으로 갈릴 뻔한 것과 같은 실수를 피한 것이 이번 티켓의 핵심 지시였다.
> - 배선: `_check_pl_bridge()` 에 `source_ids`·`src_na_out` 키워드 추가(L1020~, **반환 arity 5 유지** — `tests/test_rule_coverage_manifest.py:745` 보호) · 2e 판정 L1091-1105 · 2b 판정 L1225-1227 · `src_na_out` L1317 · `main()` L1833 · SUMMARY L1868.
> - **🔴 "계보가 DISCLOSURE 면 SKIP" 으로 짜지 않았다.** 그렇게 하면 거짓 면제가 된다. 가드를 **원천이 정말 안 실은 모양**으로 좁혔다 — leg-coverage 는 `LOB 3다리 전부 결측 + 추가 LOB(2-N) 없음`, ZERO_LEGS 는 `생명장기 10개 sub-leg 전부 결측`. 한 칸이라도 값이 있으면 계보와 무관하게 검산한다. 라이브 숫자는 같지만(155/112 불변) 나중에 그 버킷에 `0.0` 이 섞여도 축이 안 죽는다.
> - **SKIP 을 조용히 하지 않는다.** SUMMARY 에 `src_na(DISCLOSURE):155legcov/112zleg` 신설 + 본문에 `LEGNA` 155줄 · `ZLEGNA` 112줄 건별 인쇄. "안 봤다"가 "통과했다"로 읽히면 그게 false-green 이다.
> - **거짓 PASS 2건도 같이 닫혔다** — 처브라이프 2023.1Q·2024.1Q 는 다리가 하나도 없는데 `bare+기타영업수익-기타사업비용` 후보가 우연히 허용오차에 들어 PASS 였다. 이제 SKIP(`진짜(REAL)` pass 1173 → 1171).
> - **시뮬레이션은 같은 함수를 토글해서 쟀다**(`source_ids={}` = 수정 전 동작). 수정 전 leg-coverage FAIL 172(DISCLOSURE 153/DART 19)·ZERO_LEGS 97(88/9) → 수정 후 **19(DART 19)·9(DART 9)**. strict 토글이 수정 전과 **집계·`fail_ids`·`zleg_ids` 집합까지 전건 동일** = 계보 미상 경로 회귀 0. **새로 생긴 FAIL 0**(단방향).
> - **🔴 골든이 `병합 전` 기준이라 diff 를 통째로 내 몫으로 읽으면 안 됐다.** `e83b619^` 에서 마스터·사이드카·등재부를 꺼내 2×2(`{병합전,병합후}×{strict,aware}`)로 `main()` 을 돌려 귀속을 갈랐다. **① 골든 == ② 병합전+수정후 (전 필드 일치) = 내 룰은 병합 전 마스터에서 완전한 no-op.** 병합(①→③)이 움직인 축 = `pl_bridge`·`tax22_src`·`zero_legs`·`lob_na` 4개(parser 티켓 §1 표와 숫자까지 일치). **내 수정(③→④)이 움직인 축 = `pl_bridge`·`zero_legs`·신설 `src_na` 3개뿐.** `zero_legs` 는 9 → 97 → **9** 로 골든 값에 정확히 되돌아왔다.
> - **ZERO_LEGS DART 9건은 살렸다** — 아이엠라이프 2024/2025.4Q · AIA 2024.4Q · 예별 2024/2025.4Q · 카카오페이 2024/2025.4Q · 하나손보 2024/2025.4Q. **9/9 가 4Q(DART 사업보고서)** 이고 이 5사는 12차에 "DART 4Q 에 생명장기손익 실재" 로 실측한 12사 안에 있다 → 원천 부재가 아니라 **DART sub-leg 추출 갭** 가능성이 높다. 수치가 병합 전(=골든)과 같으므로 push 는 안 막는다. 원문 확정은 parser 레인.
> - **selftest 69 → 75**(`_data_contract_selftest.py` `_mt()` L933 · `MT_CASES` L948 · `run_master_tables_cases()` L971). 이 축은 `run_gate` 안에 **없어서** `Env(inject=)` 로 못 찌른다 — `run_gate` 에 억지로 얹으면 "그 룰이 거기 있다"는 거짓말이 되므로 `_check_pl_bridge` 를 **직접** 부르는 가족을 만들었다. S1 DART 생존 · S2 DISCLOSURE 는 SKIP 이고 세어진다 · S3 다리 일부결측이면 검산 · S4 계보 미상 엄격(fail-closed) · S5 sub-leg 값 있으면 ZERO_LEGS 문다 · S6 추가 LOB 있으면 검산.
> - **killer 변이 7종으로 반증**(게이트 파일 직접 변조 후 복원, md5 `365d8f25cbacc8f4f2a298e039b3b18f` 전후 동일). M-A 2e 가드 무력화→S2·S5 / M-B 2e 가드를 계보만 보게→S3·S6 / M-C 2b 가드 제거→S2·S3·S6 / M-D 2b 가드를 계보만 보게→S5 / M-E 계보 미상을 DISCLOSURE 로→S4 / M-F leg-coverage 항상 SKIP→S1·S3·S4·S6 / M-G ZERO_LEGS 발화 제거→S1·S4·S5. **6/6 케이스가 최소 1변이로 사망(동어반복 0) · 7/7 변이가 최소 1건 사망(안 보이는 변이 0).**
> - **S3 는 처음에 내 fixture 가 틀려서 FAIL 했다** — LOB 3다리를 다 넣으면 라벨이 `보험손익(dual)` 로 가서 leg-coverage 축을 안 찌른다. 룰이 아니라 케이스를 고쳤다(다리를 **일부만** 비우는 형태가 가드를 정확히 찌른다).
> - **미배선 잔여(honor-system 방지용)**: ① `tests/test_rule_coverage_manifest.py:749` 의 `coverage_holes(pl, …)` 는 아직 resolver 없이 부른다 — 매니페스트의 `holes` 축만 게이트보다 엄격한 그리드를 쓴다. 오늘은 무해(그 변이는 **값만** 흔들고 결측을 안 만들어 `holes` 가 양쪽 동일, 162 passed 불변)하지만 결측을 만드는 변이가 생기는 날 커버리지를 과대선언한다. ② `zleg_exc`(회사단위 `ZLEG_LEGIT` 면제 카운터)는 세기만 하고 인쇄되지 않는다(내 수정 이전부터).
> - 검증: `validate_master_tables.py --no-build` **`pl_bridge:3309P/31F/1950S/0NEW · zero_legs:9 · src_na(DISCLOSURE):155legcov/112zleg`**(exit 2 = pb_fail 31 기지, 골든과 동일) · `validate_data_contract.py` **RED=0 YELLOW=123 exit 0 불변** · `--selftest` **75/75** · `tests/test_master_tables_golden.py` `--update` 후 1 passed · `test_rule_coverage_manifest`+`test_identity_registry`+`test_push_gate_wiring`+`test_identity_tautology` **162 passed / 2 skipped**(매니페스트 수정 불요) · `prepush_check.py` **FULL 범위 gate-clear**.
> - 재현: `$py scripts/validate_master_tables.py --no-build` · `$py scripts/validate_data_contract.py --selftest` · `$py scripts/_probes/_probe_20260920_pl_bridge_after_merge.py`(신규=0 · 등재부에만=0) · `$py -m pytest tests/test_master_tables_golden.py -q`.

**🔌 2026-09-20 (12차) 경영공시 PL 백필 병합 선행조건 ②③④ 배선 — 계보 등재 + PL provenance 첫 검증 + 기대그리드 소스화 + 개념 등재부에 리더 달기. 라이브 `RED=0 YELLOW=123` 불변, selftest 57→69, 골든 불변.** 마스터(`PL_breakdown.json`·`kics_disclosure.json`·마스터 xlsx)는 한 셀도 안 건드렸다. ⑤ 병합은 parser 소관이라 하지 않았고, 조건부 승인으로 회신했다(`inbox/parser/20260920T1500Z__validation__ALL_2023.1Q-2026.2Q__disclosure_pl_merge_authorized.md`).

> - **② 계보 등재 4건 + `SOURCE_ID_LINEAGE_MISMATCH` 를 capsec guard 밖으로**(`validate_data_contract.py` `_SOURCE_LINEAGE` L906~ · `verify_provenance_sidecar()` · `check_as_of()` §2a(v) · `Env._build_pl_cells()`). 등재 = `data/disclosure/`→DISCLOSURE · `md_inbox/`→DISCLOSURE_MD · `data/_gold/`→OWNER_GOLD · `scripts/build_pl_breakdown.py`→OWNER_GOLD.
> - **🔴 등재와 guard 해제는 반드시 같이 해야 한다(실측).** 등재 없이 guard 만 풀면 `kics_rate_sensitivity` **138셀이 한꺼번에 RED**(사이드카가 `md_inbox/…` ↔ `DISCLOSURE_MD` 인데 계보 미등록 → 판정 None). 등재만 하고 guard 를 안 풀면 PL 은 여전히 무검증. 둘을 같이 해서 회귀 0. 부수 수확: **L1391 주석이 "계보 일치를 검사한다"고 적어 놓고 실제로는 안 하던 상태가 해소**됐다(138/138 MATCH).
> - **`OWNER_GOLD` 는 등재, `DERIVED` 는 등재 금지.** 계보 판정기는 `source_file` **경로**에서 라벨을 유도하는데 빌더 파생값엔 경로가 없다(`null`). 널에 라벨을 주려면 빈 접두를 등재해야 하고 그러면 `source_id_for_lineage(None)` 이 라벨을 돌려주어 **전 마스터의 모든 null source_file 이 계보 검사를 통과**한다 = 보편적 탈출구. 대신 `builder_derived_keys` 로 **게이트가 마스터에서 재계산한 셀**(생보·contract_notes·published⊆{13,14}·값 정확히 0.0)에만 좁은 면제를 준다. 사이드카의 자기 라벨은 근거가 아니다(PM-2026-08-03). 양방향으로 건다 — 라벨 도용도, 파생값에 필링 경로 다는 것도 RED.
> - **PL provenance 는 호출처가 0 이었다.** 사이드카는 2026-06-20 부터 있었는데 `verify_provenance_sidecar()` 호출처 4곳(sensitivity_heatmap·forward_capital·tier1/2)에 PL 이 없어 한 번도 검증되지 않았고, `_fallback_note`(=부재 RED)조차 그 4개 분기 **안에서만** 도달 가능해서 "사이드카가 없다"는 RED 도 안 났다. 배선 후 **published 731셀 검증 · 빌더파생 면제 1셀 · RED 0**. `published_cells` 는 사이드카가 아니라 **마스터에서 독립 재계산**한다(사이드카가 검사 대상을 고르면 빠뜨린 셀이 영원히 무검사 — selftest Q1 이 그 형태를 고정).
> - **🔴 `as_of_date` 축은 지금 통째로 침묵한다(748/748 null).** `STALE_AS_OF` 가 못 문다. "안 봤다"를 "통과했다"로 읽지 않도록 게이트가 매 실행 **세어서 인쇄**하게 했다. 채우는 주체는 downloader(필링 meta 의 보고기간 종료일). **분기말일을 기계적으로 넣으면 안 된다** — 항등식일 뿐 검증력 0.
> - **③ `coverage_holes` 기대그리드를 셀 계보별로**(`validate_master_tables.py` `PL_DISCLOSURE_*` L48~ · `pl_cell_source_ids()` · `pl_key_items_for()` · `coverage_holes(key_items_for=)` · `_check_coverage()`). DISCLOSURE → §2-1 5항목(#1·#16·#22·#23·#24), 그 외·**계보 미상 → 종전 전량(fail-closed)**. 사이드카 부재·파손·중복계보는 전부 엄격 쪽으로 떨어진다 — 사이드카를 지워 검사를 느슨하게 만들 수 없다.
> - **배선된 실제 함수로 잰 전후**: `LIVE 종전규격 real=3/known=32/struct=15` = `LIVE 소스인식 real=3/32/15`(**바이트 동일 → 골든 `--update` 불요, 0칸 이동**) · `MERGED 종전규격 real=118` → `MERGED 소스인식 real=6`. 전임자 시뮬의 125 와 다른 것은 스테이징이 그 사이 축소됐기 때문(8→5항목 · KR0004 제외 · KR0150 6칸 NO_PDF).
> - **🔴 `LOB_LEG_NA` 등재를 금지한 근거를 회사별로 실측했다.** 백필 15사 중 12사는 DART 4Q 에 생명장기손익이 **실재**(악사·아이엠라이프·AIA·처브·교보라플·IBK연금·카카오페이·하나손보 3/3, 라이나·BNP·메트라이프·하나생명 2/3). 개념이 없는 게 아니라 이 소스가 안 싣는 것이다. 예외 2사 — **AIG(KR0029)는 3개 4Q 전부·3개 LOB 전부 결측**(원문 확인 전엔 등재 금지), **신한이지(KR0051)는 2025.4Q 에 −3,392.2 실재**라 2024.4Q 결측은 확정 결손이다.
> - **병합하면 진짜 RED 3건이 드러난다**(AIG 2024.4Q·2025.4Q · 신한이지 2024.4Q, 전부 `부분`). 소스인식 규격에서도 남으므로 **경영공시 탓이 아니라 DART 추출 갭**이다. 서울보증 2024.1~3Q 3건은 **병합으로 해소되지 않는다**(parser 가 `NO_PDF` = 원천 부재로 확정한 6칸이 그 분기들). 전임 세션의 "서울보증 3건 해소" 는 옛 스테이징 기준이라 지금은 틀리다.
> - **🔴 병합 차단 1건 추가 적발**: 스테이징 155칸이 `항목번호 23` 을 **`법인세비용`** 으로 적는데 마스터는 374/374 **`법인세`** 다. `load_long()` 이 항목명으로 색인하므로 이대로 병합하면 같은 번호에 이름이 둘 생기고 `법인세` 를 찾는 소비자가 백필분을 못 본다. parser 티켓 §5-1 로 발주.
> - **④ `CONCEPT_REGISTRY["pl_disclosure_vs_dart"]` 등재 + 리더**(`check_cross_source()` §3d). 경영공시 `투자손익=투자수익−투자비용`(감독회계) vs 마스터 `투자손익(#17)=투자이익(#18)+보험금융손익(#19)`(336/336 성립). **등재만 하면 다음 라운드에 또 샌다**("Ledger needs a gate reader") → DISCLOSURE 계보 셀의 항목을 **allowlist `{1,16,22,23,24}`** 로 강제, 위반 시 `CONCEPT_MIXED_DISCLOSURE_INTO_DART` RED. 금지 3항목 열거가 아니라 허용 5항목인 이유는 fail-closed(새 항목이 조용히 못 들어온다). **라벨과 경로를 둘 다 본다** — 라벨만 보면 `source_id` 를 DART 로 고쳐 다는 것으로 빠져나간다.
> - **🔴 배선 도중 같은 census 의 두 번째 구현을 발견했다.** `validate_data_contract.check_census` §1c 가 PL 에 대해 `coverage_holes` 를 **resolver 없이** 부르고 있었다 — ③ 을 `validate_master_tables` 에만 넣고 끝냈으면 병합 후 이쪽만 `MASTER_HOLE` **118 RED**, 저쪽은 6 이 된다(같은 등식을 두 파일에 다르게 구현해 둔 것이 CSM상각 대조 사고의 절반이었다). 같은 resolver 를 `Env.pl_source_ids` 로 한 번만 만들어 양쪽에 물렸고, **병합 전/후 둘 다 두 게이트 숫자가 정확히 일치**함을 실측했다(LIVE 3=3 · MERGED 6=6).
> - **selftest 57 → 69**(`scripts/_data_contract_selftest.py`). 신설 Q1~Q8b(PL provenance + guard 탈출 + census 1c 소스인식) · **R1~R2(`BS_KICS_HARD_ZERO`·`BS_KICS_BASELINE_BREAK`) = 직전 라운드가 "미배선 잔여" 로 박제해 둔 잔여분 해소.** 오탐 금지 케이스 2건 포함(Q5b §2-1 5항목만은 정상 병합 · Q8b 경영공시 계보 결측은 hole 아님).
> - **🔴 12건 전부 killer 변이로 반증했다(=동어반복 아님).** M1b 비-capsec 계보 침묵→Q2·Q7 사망 / M2b `published_cells` 비움→Q1·Q2·Q3·Q4 사망 / M3 개념 guard 무력화→Q5 / M3b 면제를 `sf is None` 으로 넓힘→Q3·Q4 / M4 면제를 사이드카 라벨로 판정→Q3·Q4 / M5 HARD_ZERO 제거→R1 / M6 BASELINE_BREAK 제거→R2 / M7 PL 사이드카 부재 묵인→Q6 / M8 allowlist 축소→Q5b(오탐) / M9 census 1c resolver 제거→Q8b / M10 census 1c 를 항상 느슨하게→Q8. 전부 백업·복원했고 `validate_data_contract.py` md5 `aa75912a86d1c585bd5d1d736aab73f9` 작업 전후 동일.
> - **1차 변이 2개는 무의미했다(기록해 둔다).** M1·M2 는 "옛 동작 복원"이 아니라 **다른 버그 주입**이라 63/65 건이 한꺼번에 터졌다 — Q2/Q3/Q4 가 여전히 통과해 아무것도 증명 못 했다. 변이는 **되돌리려는 그 동작과 정확히 같아야** 한다.
> - 매니페스트: `check_as_of`·`check_cross_source` 는 `tests/test_push_gate_wiring.py::DATA_CONTRACT_CHECKS` 에 이미 `WIRED` 라 수정 불요(실측 65 passed·2 skipped). `tests/test_rule_coverage_manifest.py` **83 passed 불변** — PL 등식 커버리지는 안 건드렸다.
> - 검증: `validate_data_contract.py` **RED=0 YELLOW=123 exit 0** · `--selftest` **69/69** · `validate_master_tables.py --no-build` **SUMMARY 불변**(`tests/test_master_tables_golden.py` 1 passed, `--update` 불요) · `prepush_check.py` **FULL 범위 gate-clear**.
> - 재현: `$py scripts/validate_data_contract.py` · `$py scripts/validate_data_contract.py --selftest` · `$py scripts/validate_master_tables.py --no-build` · `$py -m pytest tests/test_master_tables_golden.py tests/test_push_gate_wiring.py tests/test_rule_coverage_manifest.py -q` · `$py scripts/_probes/_probe_20260920_pl_merge_precondition.py`(읽기전용 — 계보 census · 소스인식 기대그리드 · 두 게이트 일치를 한 번에 인쇄).
> - **미배선 잔여(honor-system 방지용으로 여기 적는다)**: ① `PL_breakdown` 사이드카의 `as_of_date` 748/748 null → `STALE_AS_OF` 침묵(downloader 발주 필요). ② `kics_disclosure`(1,123셀)·`CSM_waterfall`(327셀) 사이드카는 **존재하는데 `source_file` 이 전건 null 이고 `verify_provenance_sidecar` 호출처도 없다** — PL 과 똑같은 상태다. `IFRS17_BS`·`dividend` 는 사이드카 파일 자체가 없다. 즉 provenance 축은 등록 마스터 10종 중 **6종**만 본다(PL 배선으로 5→6). ③ `pl_disclosure_vs_dart` 의 `comparable` tol `max(8억,1.5%)` 는 **리더가 없다** — 병합 후 두 소스가 같은 칸에 겹치지 않아(4Q 중첩 0칸) 잴 대상이 없기 때문이고, 겹치는 날 배선해야 한다. ④ 개념 guard 는 **경로나 라벨 중 하나가 DISCLOSURE 일 때**만 문다 — 경영공시에서 읽은 값에 `data/dart/…` 경로를 달면 두 그물이 다 비껴간다(값 단위 대조가 없어서다). 오늘은 emitter 가 필링 값과 대조해 경로를 고르므로 그런 산출이 나오지 않지만, 손으로 쓴 사이드카에는 열려 있다.

**🔌 2026-09-20 17BS ↔ K-ICS 교차대조 배선 — 두 마스터가 처음으로 서로를 본다(owner 지시).**
`IFRS17_BS.json`(DART 별도)과 `kics_disclosure.json`(정기경영공시)은 **서로 다른 원천**인데 같은 실체
(이익잉여금·AOCI)를 각자 들고 있으면서 지금까지 교차 축이 **통째로 비어 있었다**. `check_cross_source`
(`validate_data_contract.py` §3-cc)에 축 2개를 넣었다. **실행 결과 RED=0 유지 · YELLOW 90 → 129(+39).**
- `BS_KICS_HARD_ZERO` — 한쪽이 정확히 0 인데 반대쪽은 100억 이상. **전수 발화 6**(NH농협손보 2023.2Q·
  2023.3Q·2024.4Q 의 이익잉여금·AOCI). K-ICS 이익잉여금 0 vs 17BS 9,577억·9,115억·1조279억.
  **폐쇄식은 0 들로도 닫히므로 단일 마스터 룰로는 구조적으로 못 본다** — 교차대조만이 탐지기다.
- `BS_KICS_BASELINE_BREAK` — 회사 **자신의 평소 잔차(중앙값)** 대비 이탈. 발화 33.
- **절대 허용오차를 안 쓴 이유(실측)**: 17BS 는 DART 별도 고정인데 K-ICS 는 연결로 내는 회사가 섞여
  전수 중앙값은 0.29~0.56% 인데 p90 이 17~28% 다. **owner 제안 "비지배지분=0 이면 별도=연결" 필터도
  실측으로 안 닫혔다** — 중앙값은 0.29% 로 내려가지만 p90 8.7%, 0.5% 기준 발화 **164건(red-out)**.
  100% 자회사를 가진 회사는 비지배지분이 0 이어도 연결≠별도이기 때문이다(흥국생명·ABL·라이나).
  회사별 기준선 방식은 **레지스트리가 아예 필요 없고** 발화가 164 → 39 로 준다.
- **일부러 YELLOW 로 시작했다.** 신설 룰을 RED 로 걸면 그날로 push 가 막히고, 발화분이 추출 갭인지
  원문 부재인지 아직 원문으로 안 갈랐다. HARD_ZERO 축은 parser 회신
  (`inbox/parser/20260920T0430Z__orchestrator__KR0032__bs_kics_hard_zero.md`) 이 "추출 갭" 으로
  확정하는 즉시 **RED 로 승격**한다. 그 전까지는 승격하지 않는다.
- ~~**미배선 잔여(honor-system 방지용으로 여기 적는다)**: `scripts/_data_contract_selftest.py` 에
  이 두 축의 주입 케이스가 **아직 없다**(현재 57/57 은 기존 축만).~~ **← 2026-09-20 12차에서 해소.**
  케이스 `R1 BS_KICS_HARD_ZERO`(RED) · `R2 BS_KICS_BASELINE_BREAK`(YELLOW) 추가(57→69 중 2건).
  killer 변이로 반증 완료(M5 HARD_ZERO 제거 → R1 미검출 / M6 BASELINE_BREAK 제거 → R2 미검출).
- 판정 원본·재현 명령: `inbox/_resolved/20260919T1136Z__orchestrator__MULTI__post_transition_mirror_audit_and_item48_blindspot.md` §C.


## 🔴 Open — P1

### V19 — 사고 포스트모템 관행 도입 + 기존 4건 소급 (owner `20260721T0233Z`, 2026-07-21)
"포스트모템이 게이트 룰로 종결되지 않으면 같은 부류가 재발한다" → 5칸(무엇이 통과/어떤 룰이면 잡았나/
지금 배선됐나/exception 근거·등재위치/미배선 잔여+후속티켓) 미충족 시 close 불가인 관행 신설.
- [x] **구현형태 = 로컬 스킬** (`.claude/skills/incident-postmortem/`). 외부 스킬 미채택 — 5칸이 이
  저장소의 게이트 파일·registry 변수명·display-scope를 직접 지목해야 강제력이 생기는데 범용 스킬은 불가.
  기존 로컬스킬(`kics-parser`·`ifrs17-parser`) 패턴 + 금융데이터.
- [x] 정본 `docs/postmortems/README.md` + `_TEMPLATE.md`, 스테이지 프롬프트 §5.1에서 링크.
- [x] **소급 4건 기록**: PM-2026-06-16(두 달 글리치, closed) · PM-2026-07-07(적용후 사각, **open**) ·
  PM-2026-07-08(V17 가짜복사, **open**) · PM-2026-07-15(부모 census, closed).
- [x] **소급의 실질 산출물 = 미배선(UH) 적발 → P1 2건 즉시 배선(owner 승인 2026-07-21)**:
  - [x] **UH-1 해소**: 적용후 검증 7종(`_transition_ratio_after_capture`/`_transition_mmult_after`/
    `_transition_identities_after`/`_parent_present_child_incomplete_after`/`_diversification_negative`/
    `_item12_equals_item1`/`_ratio_series_spikes`)을 `validate_data_contract.py` `check_census`
    **1b(iv)** 로 lift(display 7분기 scope). 6종 RED + spikes만 YELLOW(휴리스틱 단독차단 금지).
    **주입 테스트 검증**: scope를 2023.1~3Q 임시확장 시 baseline RED 0 → lifted RED 4건 방출 =
    함수→`_emit`→`res.add` 경로 작동. 배선 후 실 push 게이트 **RED=0 유지**(현 findings 전부 non-display).
  - [x] **UH-2 해소**: push 게이트 체인 3종(`validate_data_contract.py`·`prepush_check.py`·
    `triage_anomaly_candidates.py`) **git 등재**. gitignore가 아니라 단순 미추가였고 나머지 의존성
    (`validate_kics_disclosure.py`·`validate_master_tables.py`·`kics_json_rules.py`)은 이미 tracked.
  - [x] **도메인 경계 명문화(owner)**: 경과조치=K-ICS 전용(적용전/후 이중공시). **IFRS17엔 대응 개념
    없음**(전환방법=도입시점 측정방법, 이중컬럼 아님) → 복사할 짝 자체가 없으므로 `TRANSITION_AFTER_*`
    IFRS17 유사룰 금지. 상위 패턴("presence만 검사→세탁")만 도메인 무관(IFRS17은 기존 plausibility/
    impossible-0가 담당). postmortems README·SKILL에 기록.
  - [x] **UH-4 해소 (2026-07-21)**: `scripts/_data_contract_selftest.py` 신설 — `Env(inject=)` 합성
    mutation suite **14/14 PASS**. 기존 spec §5 회귀 + **1b(iv) lift 5종(F1~F5) 회귀 보호**.
    **이빨 검증**: `_item12_equals_item1`·`_post_transition_parent_census`를 monkeypatch로 죽이면
    해당 케이스 미검출→FAIL 확인. 이후 신규 룰은 여기 케이스 추가 필수.
  - [x] **UH-3 부분강화 (2026-07-21)**: sidecar 부재가 `notes`(비집계)로 조용히 통과하던 것을 집계되는
    **YELLOW `MISSING_PROVENANCE_SIDECAR`**로 승격. **RED 전환은 발행 후** — 지금 RED면 미발행 마스터
    전부 red-out으로 push 영구차단. **진행: sidecar YELLOW 4→1** — publishing(`faa34cd`)이
    forward_capital·tier1·tier2 발행 → 3종 Phase-2 strict 전환. **sensitivity_heatmap만 잔여**
    (parser(ifrs17) `20260721T0530Z__…sensitivity_heatmap_provenance` 발주 대기). 4종 전부 발행 후
    no-sidecar=RED 보편룰 활성화.
  - [x] **UH-5 종결 (owner 승인 2026-07-21, premise-refined)**: 선행조건이던 FSS 2023-03-20 붙임-1
    (`trend20230320_3.pdf` p6, 회사별 경과조치 종류)을 좌표추출 전수 복원(총계 검증 4/19/12/8 일치)
    → `_TRANSITION_KIND` registry(`scripts/validate_kics_disclosure.py`) 등재. **전제 falsify**:
    "TAC형(가용자본만)" 회사 = **0사**(가용자본 신청 4사 전부 요구자본 보험리스크도 신청, elective
    18사 전원 요구자본 경과조치사). **실측 78 "부모후=전" 셀** = A(subrisk후≠전·부모후=전 모순) **0**
    [기존 `_transition_mmult_after`가 이미 강제] + C(item14후 다름·부모후=전) 52 **전부 item19(시장위험)**
    [주식/금리 미신청사 정당 + 신청 3사도 조건부 미발동 가능·내부정합] + D(subrisk후 부재) 26 [census
    소관]. **진짜 미검출 0** → 부모 COPY 룰은 item17=mmult 중복·item19=오탐 52 → **신설 불요.**
    owner Socratic 지적("subrisk 다르면 상위도 달라야")이 결론 핵심 — 참이며 이미 mmult가 강제(A=0).
    postmortem README 3차 종결 기록.

### V18 — 적용후 요구자본 **부모** census blind spot 정정 (owner `20260715T0801Z`, 2026-07-15)
07-12 V17 census(`_parent_present_child_incomplete_after`)는 **부모후가 present일 때** 자식후 결측만 봄 →
**부모(15~21) 자체가 통째 결측이면 census/identity/mmult 전부 skip = false-green.** 2026.1Q 5적용사
(한화생명·교보·하나·롯데손해·농협) 요구자본 부모후 결측인 채 push 게이트 통과사고.
- [x] **게이트 신설 `_post_transition_parent_census`** (scripts/validate_kics_disclosure.py): 적용후 공시
  회사의 부모 15~21(코어)·22/23(조정) 값_적용후 **continuity break**(직전분기 present인데 당분기 결측 +
  이후재출현=SANDWICHED/최신=TRAILING) = RED. onset·항구적중단 flag 안 함(오탐억제). 22/23 단독=review(비차단).
  **적용사 판정=continuity 자체**(18사 하드코딩 아님) → 공통경과조치사 한화생명(KR0068)·삼성생명(KR0069)도
  포착(기존 18사룰 사각). 면제 registry `_POST_PARENT_NOT_DISCLOSED`=비어있음(owner "오면제 금지").
- [x] **양쪽 배선**: K-ICS 게이트(전분기 exit2) + **push 게이트 `validate_data_contract.py check_census`
  (display 분기만 차단)** ← "push 게이트가 통과"의 정정 지점. 두 스크립트 compile OK, 기존검사 무회귀.
- [x] **2026.1Q 라이브 해소 확인**: 병행 parser 세션이 5사 15~23 값_적용후 UPSERT(mtime 17:32) →
  2026.1Q census RED=0 + mmult/항등식/분산효과후 0 통과(fill 정합). **게이트가 갭→RED, fill→통과 검증.**
- [x] **parser 발주 `20260715T0835Z` 처리+적대검증 완료 (2026-07-16, resolved)**: push 게이트 census
  RED **47→4**. parser fill(삼성생명 2025.1Q·동양생명 4분기·한화생명 2025.2Q/3Q·흥국생명 17~21) 검증:
  - **미러fill(후=전) 정당성 PASS** — 삼성/동양/한화는 공통경과조치사(요구자본 후=전, 가용자본 item1만
    2025.2Q Δ실효과). V17 가짜복사 아님. 무회귀(mmult/항등식/ratio COPY/분산효과 전부 0).
- [🔴→👤] **잔여 push-block 2건 = owner escalate (raw 도출불가, `_POST_PARENT_NOT_DISCLOSED` 결정 필요)**:
  - **흥국생명(KR0071) 2024.4Q [15,16,22]**: image PDF + TIR+TER 다중경과조치 R4 재현불가(역산 item15
    14,747 vs 헤드라인 16,987, Δ2,240 비반올림). parser 비전판독 17~21은 채움, 15/16/22 결합불명.
  - **하나생명(KR0097) 2024.4Q [16]**: 비표준 공시(감사보고서 재무상태표, 이미 `_AFTER_SUBRISK_NOT_DISCLOSED`).
    item16후 산술파생 가능(=1369.09)이나 입력 item17후=1757.32가 raw page(2001.90) 불일치(partial-mmult
    아티팩트 의심) → 파생값 불신. owner 택일: item16 파생채움 vs 부모후 exemption.
  - **owner 결정 대기** — 둘 다 `_POST_PARENT_NOT_DISCLOSED`(scripts/validate_kics_disclosure.py) 등재
    또는 parser 재추출 지시. validation 자체 waiver 안 함.
- non-display 비차단 워크리스트(push 무관): 코리안리 KR1000 3분기·악사 2024.3Q·처브 2024.3Q·IBK연금
  2023.2Q(다중경과 결합불가 기지)·하나손/하나생 2023.2Q. git-purge raw, 저우선.
- 완료기준: 게이트 `post_transition_parent_census.red` display분 = 0 (현 4, owner 2셀 처리 시 0).
- [x] **건2 `8_post` dynamic tol (publishing `20260712T0219Z`)**: 이미 코드반영(07-12) 확인 —
  KR1098 2023.4Q 8_post=YELLOW(diff -92.82 tol내), `7_post` 룰 부재(누락 없음). resolved.

### V17 — 🚨 경과조치 "적용후" 전수 재추출 (owner 전수건 21/22 미처리, 2026-07-05 재발주)
owner `20260703T1138Z`(경과조치 적용후 컬럼 구조적 유실, 22 적용사) = **여전히 open, IBK연금 1개만 처리.** 이번 라운드 최대 미완건. validation 라이브 실측 후 최우선 재발주.
- [🔴] **parser "복사버그 정정" = 가짜수정 적발·반려 `20260705T2150Z`**: 파서가 커밋 5건(31bcead 등)으로 처리 주장했으나 검증 결과 **적용후 = round(적용전) 복사**(exact-identical만 피한 위장). item27 22적용사 285셀 중 **164 가짜/결측**(복사139+결측19+역전6), 진짜 후>전 121뿐(정상마진 50~190%p). → 진짜 raw 재추출 강력 반려.
- [x] **게이트 하드룰 신설 `_transition_ratio_after_capture`** (owner #6): 적용사(owner 22 seed ∪ 동적) item27 적용후 ≤ 적용전+1%p(복사/반올림) OR 결측 OR 역전 = **RED, exit 2 차단**. IBK연금만 0=정상재추출 통과(오탐0). self-test 7/7. 재검툴 `scratchpad/verify_item27.py`·`adversarial.py`.
- [🔴] **2차 적대적 검증 → 파서 회피 재적발 `20260706T0434Z`**: 파서 재수정(168→112) 후 적대검증 = 두 회피. **(A) "진짜동일 재확인" 5사(한화생명·코리안리·신한라이프·KB라이프·동양) 거짓** — 동양 2025.2Q 후>전 실재(172→177)로 반증, 나머지 유실. 게이트 seed로 63셀 RED 유지=재분류 거부. **(B) item27만 패치·금액(item1/14)후 미수정 정합붕괴 9건**(한화손해 item27후283≠도출190). → **게이트 AMT_MISMATCH 검사 추가**(item27후≠item1후/item14후×100 >2%p=RED). 현 **121 RED**(COPY50·MISSING19·LOWER43·AMT_MISMATCH9). iter3, 다음 회피 owner escalate.
- [x] **선택 경과조치 적용사 정본 확정(2026-07-06) = 18사**: owner가 **FSS 2023-03-20 보도자료 붙임-1**(`trend20230320_3.pdf` p6, 원수사별 신청현황) 제공 → 22-seed·그간 추정 전부 폐기. **생보 12**(ABL·흥국생명·케이디비·교보생명·아이엠라이프[=구DGB]·DB생명·푸본현대·하나생명·처브·교보라플·IBK·농협생명) **+ 손보 6**(AXA·한화손보·롯데손보·예별손보[=구MG]·흥국화재·NH손해). SCOR재보험=데이터부재. 나머지=공통(TFI) 후=전 정상. 코리안리·메리츠·한화생명·신한라이프=미적용 확정(오탐 해소).
- [x] **게이트 item27+item28 이중검사 + AMT_MISMATCH**: 18사 하드코딩, 두 비율 후≤전+1%p OR 결측 OR 항등식붕괴=RED exit2. 현 **139셀**(item27 68·item28 71; 케이디비·하나생명 최다=전량유실). self-test 7/7. 정본 발주 `20260706T0502Z`(2150Z·0434Z supersede).
- ⚠️ **publish = 보류 확정**: 적용후=화면 표시값. 18사 item27·28 적용후 진짜 재추출(item1·2·14 정합) + 게이트 139→0 전엔 불가.
- [x] **(2026-07-12 c) 전수 헤드라인 대조 + 파서 IBK fix 반려**: 18적용사×전분기 raw '경과조치 후' vs item27후(anchor 오탐0) → 110정합·**예별손해 KR0004 2023.1Q/2Q/3Q 불일치**(item27후=②표단독 74.67 vs 헤드라인 82.56, IBK동형 혼합)·119 자동파싱불가. **파서 IBK fix(0430Z) 반려**: item1후를 TAC단독 8241.63으로=**공통TFI 누락**(정답 9164.38=원래값, item14후 5179.08). 발주 `20260712T0700Z`(IBK반려+예별3+per-company 재조정). 케이디비 2025.4Q=내 오탐(데이터 205.7 정상).
- [x] **(2026-07-12 b) 파서 census-fill 적대검증 + 분산효과 부호 sanity**: parser 322→2 fill(a797681) 독립검증 = **견고**(item18=0이월·carry·mmult·한화손해 item19후=전 raw확인·롯데/교보 2026.1Q exemption raw정당). **단 적대스윕이 파서무관 기존오류 1건 적발**: IBK연금 2023.2Q 적용후가 ②표(시장불변)·③표(시장감소) 혼합→분산효과 -246.66(음수)+item27후 135.19≠헤드라인 176.95. **`_diversification_negative` 신설**(전·후 전체회사 item16<0/Σ(17~21)<15, RED blocking). parser 발주 `20260712T0430Z`. 현 게이트 분산효과음수 1(IBK) 차단.
- [x] **(2026-07-12) 적용후 요구자본 census 신설 = blind spot 정정**: owner가 아이엠라이프 2025.4Q 적용후 신용·분산효과 결측 지적 → 적용후 게이트가 mmult(item17/19 leaf)만 보고 **요구자본 구성(15→16~21) census 부재** 확인(항등식 R6은 결측셀 skip → 양쪽 샘). **`_parent_present_child_incomplete_after` 신설**(적용전 census 미러, 부모맵 15/17/19, RED blocking, exit-code 배선). **적발 322 항목셀(149 부모·분기)**: DERIVE 96(분산효과=Σ(17~21후)−15후)·CARRY 206(신용/운영/시장하위 후=전)·EXTRACT 20(raw재추출 14 회사·분기). 분류 `data/_derived/after_census_gaps.json`. parser 발주 `20260712T0230Z__…__after_requirement_census_322cells.md`. **현 게이트 census 149 RED 정상차단, parser fill 후 0 확인→재publish.** (owner가 앞서 현버전 라이브 push함 — 이 부분충전은 요구자본 detail, headline 지급여력비율후는 정상.)

### V16 — parser IFRS17 재빌드 검증 + IBK연금 무재보험 false-positive 해소 (2026-07-05, owner "cell 등록")
parser IFRS17 레인 재빌드(viz+마스터) 후 게이트 전수 검증. 코어 무손상 확인 + push RED 오탐 1종 해소.
- [x] **코어 정합성 검증**: closing 324P/0F · crosscheck 0F · cont 0 · dup 0 유지. tier2 data-contract RED **4→0**(소진율/분모 이슈 해소).
- [x] **IBK연금 재보험손익=0 ×4 = 오탐 확정**: 순수 연금사 무재보험(재보험 5 leg 전부 0 + 원수분해 정확히 닫힘). owner "cell 등록" → `user_pl_confirmed_cells.json` 4셀 + `validate_data_contract._pl_impossible_zero_leg` registry 존중 배선 + 마스터게이트 `IMPOSSIBLE_ZERO_EXEMPT`/`ZLEG_LEGIT` 면제. **prepush RED=1, 마스터 impossible0 0/zero_legs 3**.
- [x] **KR0083 2025.2Q 19_market 해소 (2026-07-05 b)**: downloader 오슬롯 PDF 교체(KR0075 BNP가 덮던 것) → parser 재추출(subs 29-46 복원, 19_market reconcile ✓). **prepush RED 1→0 = GATE-CLEAR**, K-ICS RED 9→8(전부 documented: KR0079 8_life SKIP + KR0087 동양 2023.2Q 이미지전용).
- [x] **parser 0745Z 처리 완료(2026-07-05 c)**: PARTIAL 14→3·FULL_ABSENT 14→2. 시계열 검증으로 잔여 판정 — 진짜갭 2건(교보 item35·BNP item37) 재발주 `0805Z`, 카카오 micro-0 수용, 신한이지 LTC는 floor 1.0→5.0 자체정리, KR0104·KR1010 legit-absent 수용.
- [x] **전건 해소 (2026-07-05 d): PARTIAL 14→0.** 교보 item35 백필·BNP item37/38 genuinely-0 적재(파서 MD근거 "변액주식 139억 감소"=내 통계추론 오판 인정)·카카오 item40 0.0 적재·신한이지 floor 자체정리. `0805Z` resolved. 잔여 = FULL_ABSENT 2(KR0104·KR1010 legit-absent 비차단) + census-missing 3(documented).
- [→] **follow-up: prepush에 `_parent_present_child_incomplete` 배선** — 지금은 PARTIAL 0이라 무영향이나, 향후 push 권위 게이트가 이 축을 정직하게 강제하도록 배선 권장.
- 참고: `_data_contract_selftest.py` 부재(pre-existing purge) — 게이트 정상, 회귀는 라이브 실측 대체. 메모리 [[owner-confirmed-registry]].

### V15 — 게이트 사각 2종 신규룰 (parser blind_spot 0703): 부모-자식 census + 지급여력비율 스파이크
owner 워크스루가 게이트 RED=0 통과분에서 잡은 2부류를 parser가 blind_spot으로 이관 → 룰 강화(데이터는 parser 수정 완료). 둘 다 `scripts/validate_kics_disclosure.py` 구현, self-test 7/7.
- [x] **`_parent_present_child_incomplete` (RED)**: 부모(item17/19)>0인데 회사별 self-census상 '평소 유의미 보고' 자식(29-35/36-40) 결측=행누락. 기대=과반present&중앙값≥1억(회사유형 아님 — 손보 장수리스크 실보고사 DB손해/코리안리/삼성화재 검출유지; 구조적0 LTC 제외). **PARTIAL만 RED(14)**, FULL_ABSENT even-Q(16, 2023.2Q 도입초 클러스터)는 원천확인 review 비차단. 역방향(`_parent_zero_child_nonzero`는 부모0·자식≠0만) 사각 닫음.
- [x] **`_ratio_series_spikes` (YELLOW)**: item27 인접 2분기 양방 이탈 단일분기=소스오염(부호역전 자체는 자본잠식사 정상이라 flag 안 함). 라이브 0, 옛 KR0083 25.2Q +318 주입 발화 확인. item27 중복행 dedup.
- [→] **parser 백필 발주**: PARTIAL 14 RED(KR0050 34·35 등) + FULL_ABSENT 16 review → `inbox/parser/20260704T0745Z…parent_child_census_gaps`. 재파싱 후 게이트 재확인.
- 부수발견(동봉): item27 중복행(삼성생명·메트라이프 이중정밀도), 세션중 kics_disclosure.json 재작성(parser 활성). blind_spot 0703 + owner 1529Z → `_resolved/`. 메모리 [[coverage-census-mandatory]]·[[validation-blind-spots]].

### V10 — KICS gate coverage census + 19_market SKIP blind spot (2026-06-12 owner 적발)
Root cause: gate didn't census "cells that should exist" + treated SKIP as pass. RED=292 after fix.
- [x] **19_market 과잉 RED 수정** (2026-06-13c, source-grounded cadence): 내 06-12 RED 승격이 cadence 미처리로 홀수 간이공시를 과잉flag. `_scan_breakdown_presence()`(disclosure MD 직접확인) + 짝수=항상RED·홀수=MD표유무로 판정. **RED 148→21**(EVEN 18 + 삼성생명 odd 3 = 진짜갭), cadence-SKIP 127(전부 홀수 간이공시). raw 확증(삼성화재/현대 홀수 MD에 세부표 부재).
- [→] **parser 재추출 (19_market 진짜갭 21건만)**: 짝수 full-form 결측 18(KB손해2024.4Q/2025.2Q·한화생명2023.4Q/2024.2Q·흥국생명/흥국화재2024.4Q·DB생명2025.2Q·DB손해2024.4Q·NH2025.4Q·신한이지3·처브3·AIA2025.4Q·카카오2025.4Q) + 삼성생명 odd 3(2023.3Q/2024.1Q/2024.3Q, MD에 표 있음). gold: 하나손해·삼성생명 2025.4Q(이미 GREEN). 148→21로 정정 inbox 발송.
- [→] **2026.1Q 항목 절단 (parser)**: 30사 적재됐으나 전 회사 항목 1–28까지만, 29–46 전무 → backfill.
- [→] **census 미싱셀 28건 (parser)**: 미래에셋(7분기)·코리안리(6분기)·동양·하나생명 등 MD는 parsed인데 JSON 추출 누락.
- [x] **`36_irr` SKIP맹점 폐쇄** (2026-06-13): cadence-aware RED 승격 — item36 공시·41–46 결측이 **짝수분기(2Q/4Q)면 RED**(시나리오표는 2Q/4Q 서식에만 존재, 실증: 41–46 전 분기 짝수에만 적재), **홀수분기는 SKIP**(원천부재 정당). `IRR_SCENARIO_EXEMPT` 면제셋(빈값). 결과: RED 23(전부 짝수, 홀수 false 0). 19_market 동형. → parser 41–46 재추출(아래 23건, market_subrisk inbox 후속).
- [x] **`report_latest.json` fresh-write** (2026-06-13): 게이트가 매실행 `artifacts/kics_validation/report_latest.json` 덮어쓰게 함 → stale glob 함정 제거(소비자 코드 0, orphan 5/25본이 문제였음).
- inbox: `20260611T2200Z__validation__MULTI_ALL__kics_market_subrisk_systemic_underparse.md`. 메모리: `coverage-census-mandatory`.

### V12 — CSM 민감도 전수 재추출(25.4Q 경영공시 기준) + direction sanity (2026-06-15, parser 대기)
owner: IFRS17.html 흥국생명 CSM 민감도 이상 지적. 진단 = 현 소스가 FY2024 DART 사업보고서(1년 stale·비전수), parser 추출 자체는 정확.
- [→] **parser(ifrs17) 전수 재추출 발주**: `sensitivity_heatmap.json`을 25.4Q 경영공시(`data/disclosure/FY2025_Q4`) 기준으로. inbox `20260615T0415Z__validation__MULTI_2025.4Q__csm_sensitivity_refill_disclosure_basis`. risk 전수(사망/해지/사업비/장해질병 정액·실손/…), 당기말만, csm_delta=CSM·pl_impact=손익효과, 억원 정규화, unavailable 정직표기. 미다운로드면 downloader bounce.
- [x] **SENSITIVITY_DIRECTION_SANITY 룰 신설**(`validate_master_tables.py` 5b): sign(csm_delta)≠sign(pl_impact) YELLOW. fill 후 재검증 시 sign-opposition 전수 triage(real vs 파싱오류).
- 참고: 흥국 해지율 역행=source-faithful(건강보험 견인), 장해질병 누락=FY2024 사업보고서 부재 → 경영공시로 해결. recency는 사업보고서≈경영공시(둘다 2025.12.31), 전수·granular가 경영공시 우위.

### V13 — 부모-자식 정합 룰 + INTERNAL_MODEL_36IRR 등록 + 카카오 cadence 정정 (2026-06-16, owner 라이브 QA 3차)
owner SGI 게이트 사각 + parser INTERNAL_MODEL 승인 inbox 드레인.
- [x] **`_parent_zero_child_nonzero` 룰 신설**(`validate_kics_disclosure.py`): 부모 위험액 present&≈0인데 하위 비0 = 구조상 불가능 RED(게이트 차단). item17→29-35, item19→36-40 명시매핑. 전수 3셀: 서울보증 2025.4Q(item35=5212)·2023.4Q(5264)·카카오 2023.3Q(4.72) 전부 대재해 오정렬.
- [x] **parser 발주(3셀 재파싱) → ✅ RESOLVED (2026-06-20 게이트 재확인)**: `Parent-zero / nonzero-child: 0` 실측. parser round3 K3가 서울보증/카카오 orphan item35 제거(parent17=0 가드) → 게이트 parent-zero 0 수렴. (`inbox/parser/20260616T0130Z__validation__MULTI__parentzero_catastrophe_plus_kakao_19market`.)
- [x] **INTERNAL_MODEL_36IRR_EXEMPT 등록**(owner 승인 2026-06-15): `kics_json_rules.py` frozenset 5셀(KR0073 2025.2Q·KR0094 ×4) RED→SKIP. **36_irr RED 11→6**. pytest 110 passed.
- [→] **카카오 2023.3Q 19_market 재특성화**: parser "cadence SKIP" 제안 = 부적절(MD L177-186에 분해표 실재 = 19_market RED 참). micro 억원-coarse라 카카오 2023.2Q 동류 artifact. 처분(파서 적재 후 micro / owner micro exception) = owner 결정. TODO.md(root) line 79-80 카카오 cadence 분류 정정 필요(owner 갱신).

### V14 — backlog #6/#7/#8/#9 (2026-06-16, owner "전부다 진행", 4-에이전트 Workflow)
- [x] **#6 삼성화재 FY2024 IR benchmark RESOLVED**: `validate_nb_csm_multiple.py` `load_fy2024_ir_anchors`(IR series 2024.4Q.multiple_derived_ytd) + 삼성화재 PREFERRED_SCOPE monthly_avg_from_ytd → computed 14.76/IR 15.16 rel 0.026 fallback_used=False. **fallback_pass 2→1**.
- [x] **#6 현대해상 = 영구 fallback 확정 (owner 2026-06-16: "현대해상 IR은 CSM배수 없어 패스")**: 현대 IR이 신계약 CSM 배수를 아예 미공시 → benchmark 불가, fallback(2025.2Q=18.9)이 정상·영구. fetch 불요. V2 line 87 "현대 IR multiple 부재→영구 fallback"과 일치. fallback_pass=1은 이 1건(현대)으로 고정.
- [x] **#7 CONT 면제 → REVERT (owner 2026-06-16)**: 한때 CONT에 documented-재작성 면제를 넣었으나 owner 지시로 즉시 되돌림 — **continuity break(기시≠직전기말)는 무조건 RED, "소급재작성"이라 면제 금지**. cont=15 유지(면제 0), WFY 면제만 존치. pytest 110. 메모리 [[continuity-break-is-red]] + [[route-by-raw-availability]] 저장.
- [→] **#7 2026.1Q boundary = 파싱오류 (정정 2026-06-16, owner 원본검증; 내 #7 오진 시인)**: 5사 2026.1Q 기시 CSM이 misparse — 정답은 직전 2025.4Q 기말(교보 65,110·메리츠 111,037·신한라이프 75,537·에이비엘 9,702·푸본현대 1,907.45). self-closing identity는 opening 검증 못 함(오진 원인). **재작성 아님 = RESTATEMENT_EXCEPTIONS 등록 금지, CONT RED 유지.** `data/dart/FY2026_Q1/` 부재(purge) → downloader raw 복원(`inbox/downloader/…restore_fy2026q1_dart_raw`) → parser/ifrs17 재추출(`inbox/parser/…csm_2026q1_opening_misparse`). 복원 후 재검증.
- [i] **#7 저배수 4사 = scope 오류 아님**(framing 정정): 교보 6.61/한화 9.84=2026.1Q Q1 계절저점 YTD(한화는 IR FY 7.6 초과), 교보플래닛 2.0·처브 2.4=micro 실제 저배수. 분자 전부 waterfall item2 일치. **조사 종결, 액션 없음.**
- [x] **#8 verify_parser_change.py 신설**: snapshot/diff(blast-radius, kics cell-diff)/validate(6검증기 일괄)/all. 추출기 변경 회귀 1커맨드. 통합 validate 검증 완료.
- [x] **#9 QoQ yaml loader = 이미 배선**: `validate_master_tables.py:84` 이미 `yaml.safe_load(config/qoq_thresholds.yaml)`. backlog 항목 stale, no-op.

### V11 — 2026-06-14 (b) 정합성 전수검증 후속 (라우팅 발주 + owner 예외 결정 대기)
근본원인 검증 Workflow(8 에이전트 raw 대조) 후 비-시장 등식 RED 4종 disposition:
- [x] **메리츠 KR0001 rule5 reparse → ✅ RESOLVED**: parser가 item23+item25 12분기 적재(항등도출=공시값 일치). 재검증 **rule5 12 RED→0**. `_resolved/` 이관.
- [x] **코리안리 KR1000 2025.2Q reparse → ✅ RESOLVED**: parser가 코어 1-28 + item28 파생(156.19) + 시장37-40 fitz 적재. 재검증 **7 RED + 19_market→0**. `_resolved/` 이관.
- [x] **푸본현대 sensitivity (ifrs17 발주) → ✅ RESOLVED**: parser 근본원인=mis-tag 롤포워드(shock행0), `_has_shock_rows` 가드로 KB·푸본현대 ok→partial 정직화. 재검증 **SENSITIVITY YELLOW 1→0**. `_resolved/` 이관.
- [x] **(종결 2026-08-20) AIA KR0080 2025.1Q rule2** — owner 예외 등재 **이미 완료**: `TODO.md` L115 *"rule 2 × 1: KR0080 AIA 2025.1Q (diff=−789) — scan-only(아래 documented)"*. 게이트 계약 충족.
- [x] **(종결 2026-08-20) 미래에셋 KR0079 8_life** — owner 예외 등재 **이미 완료**: `TODO.md` L117 *"rule 8_life × 1: KR0079 미래에셋 2023.2Q — scan-only. 8_life는 SKIP=게이트 비차단"*. 게이트 계약 충족.
- [ ] **(owner 결정) parser irr_exempt v2 잔여**: INTERNAL_MODEL_36IRR = **신한라이프 KR0094×4 + 교보 KR0073 2025.2Q = 5건만**(IBK KR1011은 parser fitz로 41-46 적재·derive rel 0.0% GREEN → 면제 불요, 2026-06-14 정정) + OCR(KB/한화생명/흥국×2) + micro(신한이지 KR0051×3) EXEMPT — 전부 owner 권한. inbox/validation answered 참조.
- [x] **scan false-positive fix**: `_scan_breakdown_presence` clean-cell화 → 삼성생명 odd-Q 3 false RED 제거(19_market 15→10). parser D 종결.
- [x] **SENSITIVITY_UNIT_SANITY 룰 신설**(owner 0712Z claim2): `validate_master_tables.py` RED>1000x/YEL>100x. 640배 회귀가드. 푸본현대 YEL 1(÷100 미정규화 의심) + 미래에셋·롯데·한화손해 sensitivity 0건 → parser/ifrs17.
- [x] **TOOLING_FAIL census 배선 완료**(2026-06-14, owner "AB go"): `validate_kics_disclosure.py._market_tooling_fail()` — nonok.json을 현 데이터와 대조해 여전히-갭 셀만 're-localize' 노출(stale 제외, 비차단). 현 0건. parser fitz-fallback 안착분 이행.
- [x] **hyundai_pl ZLEG 등록 완료**(KR0009): 현대 2024.1Q~2025.2Q `ZLEG_LEGIT_CQ` 등록 → zero_legs 6→1. thread 종결.
- [→] **KR0083 푸본현대 2026.1Q continuity**: FY_BOUNDARY 2025.4Q기말 1906≠2026.1Q기초 1669(Δ12.4%) 현 RED + sensitivity flagged = 실데이터 의심, 잔여 유지.

### V7 — NB CSM cross-source + 시계열 전수 (parser P1/P2 회귀 잔여)
Rule `NB_CSM_DART_VS_IR_ANNUAL_SUM` codified (§1.2, RED, tol max(5%·|IR|, 100억)). Tools: `check_nb_csm_widespread.py` (FY24 snapshot, 6/7 OK) + `check_nb_csm_history.py` (13Q×9사 baseline). FY24 widespread: 롯데 1.233 (+23%, FY25 의존), 나머지 ~1.00 OK.
- [→] **Parser P1**: 롯데 FY2025 구성요소별 차이조정 표 capture + NB override (412,168 = IR FY25 일치). Raw: `data/dart/FY2025_Q4/raw/KR0003_롯데손해보험_20260319001293/_00760.xml:27375`.
- [x] **🚨 Parser P2 회귀 = 재확인 완료 (2026-06-16)**: off-by-one-year **해소 확정**(현 `data/ir/series/` Q1 YTD-reset 정합, 삼성화재 6782.7→14426→...→2024.1Q 8855.5 리셋). `check_nb_csm_history.py` **복원**(self-contained, 컨벤션 series 메타 도출) + `nb_csm_history_check.json` 갱신. **systemic-3 = 실재(정렬 아티팩트 아님), 근본원인 = DART CSM_waterfall partial/no_csm_block 추출**: 롯데 2025.2Q partial→NB_YTD=0→delta −1098.5(음수 불가) / 미래에셋 2025.2Q·3Q partial→collapse-then-catchup spike(=↑↓ 교대) / 2025.2Q cohort-wide 동일. DB 부호반전은 DB DART 2025.2Q+ 부재로 재현 안 됨. 삼성생명 2025.2Q OVER(+26%)=status ok=진짜 scope 차이(별건). → parser/ifrs17 `20260616T0230Z__...nb_csm_partial_extract_corrupts_history` 발주.
- [→] **한화손해 stale carryover** (별도 parser 버그): 2025.1Q DART NB가 2024.1Q 값 그대로 복제됨. 한화손해 IR note에 기록.
- [ ] (passive) V1 활성화 시 `CSM_WATERFALL_DART_VS_IR` new_business step과 overlap → retire 검토.
- Regression cmds (parser P1+P2 후): `check_nb_csm_widespread.py` → ok=7/7; `check_nb_csm_history.py` → OVER/UNDER 0 수렴.
- Gate enforcement는 publishing stage 측(사용자가 publisher에 전달).

## 🟠 Open — P2

### V8 — DART 자기완결 정합성 (CSM_waterfall 도메인 잔여)
PL_BRIDGE + CSM_CROSSCHECK 소비자 코드 구현 완료(2026-06-07). 빌드→검증 통합(`validate_master_tables.py`가 `build_root_masters.py` 자동 선행, idempotent; `--no-build`로 끔). 회귀 명령: `python scripts/validate_master_tables.py`. 현재 dup:0 spike:1 cont:12 crosscheck:0F closing:0F.
- [→] **데이터 채움 (parser/수집)**: 미래에셋 CSM상각 2025.2Q·3Q·2026.1Q 누락(2025.1Q는 있음), 롯데 생명장기손익 2025.2Q 누락(1Q·3Q는 있음). closing/pl_bridge가 skip하던 진짜 hole.
- [x] **cont 6건 = 둘 다 데이터 정정 → ✅ RESOLVED·검증완료 (2026-06-20)**: boundary break 2종 모두 후속 공시 '전기(비교)' rollforward로 과거 cell 정정 → cont 자연 해소. **parser 처리 완료, validation 재검증 `cont 6→0` 확인**.
  - **교보생명 2024(cont 2 + wfy 1) = legit 소급정정**. owner: "24.3Q부터 회사가 기초 58249로 소급정정 → 2024.4Q+ 보고서 '전기'열에 재작성 2023말값". **처음엔 면제(`CONT_RESTATEMENT_CONFIRMED`) 등록했으나 owner가 데이터정정 방식 제안 → 면제 코드 원복, 정정 발주로 전환**(더 정확, 시계열 통일). parser `inbox/parser/20260620T0600Z__validation__KR0073__kyobo_csm_priorperiod_pull`. raw XML purge지만 **extracted 살아있음**(`data/dart/extracted/교보생명보험_<rcept>_measurement.json`).
  - **삼성생명 2024(cont 4) = misparse**. owner: "2023.4Q 기말 122474 정답, 현 123926 오류". parser `0545Z`(owner-gold + 동일 extracted-전기 기법 교차검증).
  - 둘 다 정정 후 **cont 6→0**. 케이디비 spike(2024.1Q→2Q +58%)는 별건 잔여.
- [→] **PL 잔여 14F**: (1) 2023 분기 사이트 비노출 → 넘어감. (2) 소액 잔차(흥국 2025.1Q +714·KB라이프 +1,136·악사 +3,483) — 종목합산 기타비 내재 또는 미세, 지나감. (3) bare로 닫히는 분기(흥국 2024.4Q 등)는 정상.
- 참고: dual-form은 의도된 설계(사용자 확인) — bare 통과 분기 flag 안 함. 과잉진단 금지(§1.5). 단위: pl 백만원 / waterfall 억원 (cross-check ×100 정렬).

### V9 — 사용자 xlsx 수기검수 후속 (룰 3종 WFY/ZAMORT/ZLEG, parser 대기)
영속성 해결(`csm_manual_overrides.json` + `_apply_csm_overrides()` 훅, 빌드 생존). WFY 10/10 판별 완료(wfy 0). ZLEG 23→1(동양 2025.3Q 잔여). 메모리 `validation-blind-spots`·`master-xlsx-review-loop`.
- [ ] 교보(6.61)·한화생명(9.84)·교보플래닛(2.0)·처브(2.4) 저배수 별도 원인 조사(분자 scope?).
- [→] **신규 (parser)**: 메트라이프 영업이익 등식 2분기 FAIL(+12,086/+12,897) + 코리안리 crosscheck 2F(wf 상각 1년 lag 의심) + 동양 2025.3Q zleg 1건.
- [→] **현대해상 PL 8분기 재추출 (parser, 경고 inbox)**: 생명장기원수/기타원수/재보험손익/기타재보 — legit_absent 오판, 답지 anchor. 2025.2Q 패스.
- inbox: `20260611T0900Z__validation__MULTI_ALL__user_xlsx_audit_followup.md`.
- 참고: 보험손익 잔차 = LOB 별도/연결 기준 오선택부터 의심(§1.5). 신계약 CSM은 pl_breakdown_master에 구조상 없음 → V7 NB_CSM_DART_VS_IR + closing identity가 검증 담당.

### V1 — DART↔IR cross-source 2개 룰 활성화 (segment 폐기로 3→2)
룰 [§1.2 + §1.4]. RED → DART parser loopback. **현재 IR-side 정형 JSON 부재로 전사 SKIP.** (segment 룰 폐기 → V8 대체)
- [ ] **IR parser delivery 대기**: `data/ir/<period>/parsed/<KR>.json` (root TODO F18). 도착 cohort 9사: 메리츠·삼성화재·현대·KB·DB·한화생명·삼성생명·미래에셋·동양. 도착 즉시 룰 자동 ON. ⚠️ **2026-08-20 실측: 1년째 미도착.** `data/ir/**/parsed/` 전체에 파일이 **1개뿐**(KR0087 동양생명 FY2026_Q2, 2026-07-30). 9사 cohort는 오지 않았다 — 재개하려면 IR 파서 레인을 별도 발주해야 한다.

> **⚠ 2026-08-30 실측 정정 — "미도착"이 아니라 "미파싱"이다.** `data/ir/` 에 raw IR
> 자료가 **130개 파일** 있다: 현대해상 13분기 · 한화생명 13분기 · 미래에셋생명 13분기 ·
> DB손해 11분기 · KB금융(_groups) 14분기 + 삼성화재·삼성생명·롯데손해·코리안리·동양생명
> 각 1분기. 없는 것은 **`parsed/<KR>.json` 산출물**뿐이고(2개 분기 6개 파일만 존재),
> 즉 수집이 안 된 게 아니라 파싱 단계를 아무도 돌리지 않았다. owner 2026-08-30: IR 은
> 파싱 검증용 보조 소스이니 **꼭 필요할 때만** 착수할 것.
- [ ] **Threshold v1 튜닝**: 활성화 후 실제 diff 분포 보고 조정. v1: `CSM_WATERFALL_DART_VS_IR` max(5%·|IR|,100억)/step; `CSM_BREAKDOWN_DART_VS_IR` max(5%·|IR|,100억)/item (메리츠는 보종 비교 영구 SKIP — 측정요소별 표만, total만). ⚠️ **2026-08-20 실측: 1년째 미도착.** `data/ir/**/parsed/` 전체에 파일이 **1개뿐**(KR0087 동양생명 FY2026_Q2, 2026-07-30). 9사 cohort는 오지 않았다 — 재개하려면 IR 파서 레인을 별도 발주해야 한다.
- IR factsheet NB CSM multiple 가용성: 부재(현대해상·KB손해); 간접 산출 가능(DB손해 = 신계약 CSM + 월납보험료 derive).

### V2 — IFRS17-NB-RECONCILE 정합성 (한화 fallback retire 완료)
`validate_nb_csm_multiple.py` period-aware denominator + fallback flagging. 한화 fallback retire 완료(2026-06-12 재검증, `fallback_used=False`). 결과: tested 5 / pass 5 / fallback_pass 2(삼성화재·현대).
- [ ] 삼성화재 IR annual benchmark 보강 — 잔여 fallback 1건 해소. 2026-06-12 재확인: aligned FY2024 행 실패 → 2025.3Q fallback(rel 0.244=tol 0.25 턱밑, tolerance-loophole 경고). FY2024 연간 IR 분모 소싱 필요. (현대는 IR multiple 부재 → fallback 영구 유지.)

### V3 — K-ICS 시장위험 분산효과 validation (F12 cross-stage)
validation 룰 2개 구현 완료(2026-06-09b, `kics_json_rules.py`): `19_market`(item19=sqrt(V'·M·V), V=[36–40], MARKET_M 5×5) + `36_irr`(금리위험액 시나리오 분해). 정본 `docs/agents/kics-market-risk-decomposition.md`. 골든 3/3 일치. 화면 노출 X.
- [→] parser stage가 item36–46 적재(시장위험 세부표 5종 + 금리 시나리오 순자산가치 6종) — 진행 중. (V10 재추출과 동일 작업축.)
- [ ] 적재 단위(억원 vs 백만원) parser 회신 확인 → 백만원이면 대조식 ×100 조정. 적재 후 게이트 RED=0 확인.

### V4 — QoQ threshold registry
`config/qoq_thresholds.yaml` §2 + `QOQ_DELTA_WARN` 소비자 코드 구현 완료(2026-06-09, `validate_master_tables.py` 4번). CSM 항목 대상(누적→YoY / 시점→QoQ, floor 50억), PL 손익 제외. 193 YELLOW, 진짜 의심=이자부리 부호반전 3건(동양·교보·코리안리) → parser inbox. 전체 `data/_derived/qoq_warn.json`.
- [ ] (잔여 미구현) yaml loader precedence(item→domain→global) + prior-snapshot fetch + 누적 net-quarterly 변환 + finding emit(YELLOW, summary 기록, loopback 안 함). 진입점: K-ICS는 `validate_kics_disclosure.py` hook, IFRS17은 `validate_csm_waterfall.py` / 별도 스크립트 결정 필요.

## 🟡 Open / waiting

### V5 — 누적 항목 등록 목록 확장
§2.3 등록: IFRS17 `new_business_csm`, `csm_amortization`, `insurance_revenue`. 신규 누적 항목 발견 시 등록 + net 분기 기준 비교로 자동 전환.
- [ ] (운영 중 발견 시 갱신)

### V6 — KR0010 KB손해 OCR 잔여 RED 2건
K-ICS rule 2 OCR 미정확 (KR0010, KR0079도 image-only). 사용자 owned (`TODO.md` `KICS-IMG`). validation gate는 documented exception 처리 중.
- [x] **(종결 2026-08-20) 수기 OCR → RED 2→0** — 무효. 현재 게이트는 **RED=12이고 전건 `TODO.md` documented exception**이라 계약을 이미 충족한다(RED 2라는 전제 자체가 stale). OCR은 owner가 2026-08-15 *"됐어 패스"*로 **명시 보류** — 재요청 전 미착수(`TODO_downloader.md` OCR-MARKETRISK 행이 정본).

## ✅ Done (archive)
완결 항목(V10 census·V-RS 금리민감도 RS1–RS4·V8 PL_BRIDGE/CSM_CROSSCHECK/CSM_PLAUSIBILITY/MASTER_COVERAGE·V9 WFY/ZAMORT/ZLEG·V2 한화 fallback retire·V7 history check·V4 QoQ v1, 2026-05-31~06-12). 각 항목의 날짜별 상세는 `docs/changelog_validation.md`(당시 이미 `(changelog MM-DD)`로 인덱싱됨) + git log.

## 🛡️ Documented exception 관리
운영자(사용자)만 `TODO.md`에 `(도메인, 회사코드, 분기, rule_id, 사유)` 추가 가능. 서브에이전트가 자체 RED waiver 쓰지 말 것. `escalate_to_human` 단계에서만 "재파싱 5회 실패" 사유 기록.

현재 활성 exception:
- KR0010 KB손해 / KICS rule 2 / image-only PDF OCR 미정확 (V6)
- KR0079 미래에셋생명 / KICS rule 2 / image-only PDF OCR 미정확
- KR0097 하나생명 2024.4Q(item30·35)·2026.1Q(item35) / 적용후 세부위험 mmult / **적용후 세부 미공시**(raw는 phase-in 인식비율 10%만, 실값 부재→도출불가) — owner 확정 2026-07-12. 게이트 `_AFTER_SUBRISK_NOT_DISCLOSED`로 추출갭 제외.
- KR0104 농협생명 2023.1Q / 적용후 세부위험 / **다중 경과조치(①②③) 결합공식 불명**(개별표 어느것도 헤드라인과 불일치, 파서 재파싱해도 도출불가) — owner 확정 2026-07-12. `_AFTER_SUBRISK_NOT_DISCLOSED`.
- KR0100 처브 2024.3Q / 적용후 세부위험 / **②표 값이 행별로 다른 컬럼 착지**(일반화 규칙 없음) — owner 확정 2026-07-12. `_AFTER_SUBRISK_NOT_DISCLOSED`.
- KR0005 흥국화재 2024.4Q / 적용후 세부위험 mmult / **image-only PDF**(텍스트레이어0, 재수집=같은이미지) — owner GOLD-SCAN 대기, 확정 2026-07-12. `_AFTER_SUBRISK_NOT_DISCLOSED`.
- KR0097 하나생명 2024.2Q / KICS rule 2·4·5·6 / **스캔이미지 PDF**(items 1-26 미추출, item27/28만 OCR) — OCR 재처리 후속. documented.
- KR0002 한화손해 2024.2Q / KICS rule 9 / **4억(0.015%) 반올림 비물질**(tolerance-too-tight, 카카오 8_post 동류) — documented, 무해.
- (fixed, 예외아님) 카카오 2023.4Q 8_post: item14후=20억 coarse 반올림 → **8_post에 rule8 dynamic tol 배선(2026-07-12)**으로 통과. prepush RED 1→0.

## 📞 Loopback contract
§3. **max 5회**. RED packaging에 `suspected_source: "DART" | "IR" | "internal"` 명시. cross-source 룰은 항상 `"DART"`.

| 조건 | next_action | exit |
|---|---|---|
| RED=0 | `pass` | 0 |
| YELLOW만 (RED=0) | `pass` | 0 |
| loop_iteration==5 & RED>0 | `escalate_to_human` | 2 |

## 🔗 참조 룰셋 / 코드
- 권위 doc: [`docs/agents/kics-json-validation-rules.md`](docs/agents/kics-json-validation-rules.md) (R1–R10 formulas, tolerance, R4/R7 matrices, item-label mapping)
- K-ICS 구현: [`src/solvency/validation/kics_json_rules.py`](src/solvency/validation/kics_json_rules.py)
- 러너: K-ICS `python scripts/validate_kics_disclosure.py` · IFRS17 CSM `scripts/validate_csm_waterfall.py` · NB CSM multiple `scripts/validate_nb_csm_multiple.py` · reconcile loop `scripts/run_ifrs17_csm_reconcile_loop.py`
- Output: `artifacts/validation/<domain>_<timestamp>.json`
