# TODO archive — `TODO_validation.md` (Status 이력, 읽기 지연)

## 2026-10-07 정리 — 정리 전 `TODO_validation.md` 전문 (무수정)

# Insurequant Validation TODO (Stage 3)

> Last updated: 2026-10-06 (공개 다운로드 내부 진단 문자열 룰 `PUBLIC_EXPORT_INTERNAL_JARGON` 신설 — 후보 정규식의 `_eok` 버그 수정 · 현재 스냅샷 4패턴 0건 · 넓은 스캔 잔여 4건 보고) · 2026-09-23 (`kics_duration_gap.json` 라이브 배선 — `check_kics_duration_gap` 신설로 무검사 아티팩트 0 복귀) · 2026-09-21 (금리민감도 RS6_PHASE_LEVEL_CENSUS(RED) 신설 + RS2 적용후 앵커 + 36_irr 티켓 판정(c) — 마스터 무수정, 흥국생명 2칸 RS2 RED 로 push 게이트 차단 중, parser 발주 `20260921T1400Z`) · (배포 HTML JS 런타임 게이트 신설 — `DEPLOYED_JS_UNDEFINED_CALL` 을 `prepush_check.py` §1f 에 배선. 배포 HTML 의 `<script>` 를 읽는 검사기가 저장소에 0개였다; 오탐 0 · 정의삭제 변이 172/183 · 0.09초; 잔여 UH-26/UH-27) · (경영공시 PL 백필 ⑤ 병합 후속 — **`_check_pl_bridge`(leg-coverage 2e · ZERO_LEGS 2b) 소스인식**; 12차가 `coverage_holes` 만 바꾸고 이 두 축을 빠뜨려 `pl_new=153` 으로 push 가 막혀 있었다. 같은 resolver(`pl_cell_source_ids`) 재사용 · 가드는 '원천이 정말 안 실은 모양'으로 좁힘 · SKIP 을 `src_na(DISCLOSURE)` 로 세어 인쇄. `pl_new` 153→0 · `zero_legs` 97→9(DART 9 보존) · 거짓 PASS 2건도 SKIP 으로 닫힘 · selftest 69→75(killer 변이 7종, 6/6 사망) · 골든은 2×2 귀속 대조 후 `--update`. 마스터·등재부 무수정; 직전 경영공시 PL 백필 **병합 선행조건 ②③④ 배선** — 계보 등재 4건 + `SOURCE_ID_LINEAGE_MISMATCH` 를 capsec guard 밖으로(비-capsec 계보가 그동안 무검사였다: `kics_rate_sensitivity` 138셀 판정 None) · PL provenance 첫 검증(호출처가 0 이었다 → published 731셀) · `coverage_holes` 기대그리드를 셀 계보별로(병합 후 real hole 118→6, 오늘은 바이트 동일이라 골든 불변) · `CONCEPT_REGISTRY` 에 `pl_disclosure_vs_dart` 등재 + **리더**(allowlist 강제). `DERIVED` 는 계보 미등재(널 경로 라벨 = 보편적 탈출구) 대신 게이트 재계산 기반 좁은 면제. selftest 57→69(BS_KICS 2축 잔여 해소 포함), 12건 전부 killer 변이로 반증. 마스터 미수정; 직전 항목4/12/13 미러링 **재감사 정정** — "오염 170셀" 은 과다계상, 실제는 `item13` 55셀뿐이고 `item4`·`item12` 114셀은 정상. 1차 발주의 "170셀 삭제" 를 실행했으면 정상 셀 114개가 지워졌다. 버킷 판정을 셀 판정으로 승격시킨 것이 원인 — Δ의 귀착 항목을 안 쟀다; 직전 경영공시 출처 PL 백필 **계약 판정** — 항목 3개·회사 1개 제외 + 병합 순서 확정; 지금 규격대로면 census RED 0→80; 새 사각 2종 적발: PL provenance 사이드카가 죽어 있음(638셀 source_file 0) · "자식 present·부모 None" 29버킷 무검사; 직전 UH-25 게이트 축 해소 — `JP_ESR_UNVERIFIED_VALUE` 신설: 값 검증 두 축이 동시에 침묵하는 상태를 YELLOW 로 세고 push 묶음이 막는다; 직전 UH-23 정식 해소 — 한정어 정본 §3 표 ↔ `ADJUSTED_QUALIFIERS` 양방향 대조 배선 + TODO 과장 정정; 직전 jp `JP_ESR_ADJUSTED_FIGURE` 배선 — 조정치 축, UH-21 해소 → PM-2026-09-13 `closed`; 직전 jp `JP_ESR_NOT_IN_SOURCE` 배선; 직전 push 범위 판정을 훅에 구현 — CLAUDE.md §5 가 문서로만 있던 규칙을 코드로; 직전 jp false-green 포스트모템·UH-18 등재; 직전 2026-09-02 MASTER_XLSX_* 축 신설 — 마스터 JSON ↔ 마스터 xlsx 13시트 전수 대조를 CHECK 8 로 배선) · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Changelog: docs/changelog_validation.md

Session start: read this file + `claude-agent-validation.md` + domain refs (`docs/domains/claude-agent-{kics,ifrs17}.md`). English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

**🔌 2026-10-06 (17차) 공개 다운로드 문구의 내부 진단 문자열 재발방지 룰 `PUBLIC_EXPORT_INTERNAL_JARGON` 신설 — `validate_live_artifacts.check_public_exports` 의 6번째 축.** 티켓 `inbox/validation/20260921T0335Z`(publishing 제안, `status: answered`). 마스터·`public_exports/` 무수정.

> - **시뮬레이션을 먼저 돌렸다**(티켓 §시킬 일 2): 사고 직전 스냅샷(`git show c130062^:public_exports/자본비율전망.json`, 2090행)에 후보 정규식 4개. **후보 `\b…_eok\b` 는 `numerator_eok_fallback` 처럼 `_eok` 뒤에 접미가 붙은 필드명을 못 잡아 660행 중 550행만 걸렸다.** `…_eok(?![a-z0-9])` 로 고쳤고, 4패턴 합집합은 660/660 검출. 후보 주석이 "numerator_eok_fallback 도 잡는다"고 적었던 것은 틀렸다.
> - 현재 14개 시트 전수 4패턴 **0건** — clean-state 테스트 통과, 새 룰로 인한 신규 RED 없음.
> - 스캔 범위는 `비고`·`구분` 만이 아니라 **모든 열의 문자열 셀**이다(새 열로 새는 것을 막는다). 정상 한글 라벨 오탐 0 을 실측으로 확인.
> - 회귀 fixture: 사고 문자열 5개(양성) + 티켓이 "데이터 단서"로 판정한 문구 4개(음성, 가정민감도 `비고`·자본성증권발행현황 `구분` 포함) → `test_public_export_jargon_patterns_hit_incident_strings_only`. 변이시험 `jargon` 추가(자본비율전망 1행에 사고 문자열 주입 → 발화). `PUBLIC_EXPORT_RULES` 매니페스트 +1.
> - 검증: `pytest tests/test_rule_coverage_manifest.py -k public_export` 10 passed · `validate_live_artifacts` RED=0.
> - **🟡 새로 보인 잔여(이 룰은 건드리지 않음 — 4패턴 밖이라 게이트는 통과한다)**: 넓은 snake_case 스캔을 현재 스냅샷에 돌리면 같은 유형이 더 있다. 가정민감도 `비고` 1행("status=unavailable; No sensitivity_analysis block in MVP extract") · 기본자본소진율 `비고` 22행(`docs/tier1_hybrid_utilization_definition.md` 파일 경로 노출) · 자본성증권발행현황 `비고` 123행("step_up·lock_in 플래그") · 같은 시트 `콜근거` 59행(`derived_issue_plus_5y` 등 코드값). 공개 문구로 바꿀지(코드값은 데이터 열이라 둘 수도 있다)는 owner/publishing 판단.

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

---

> `TODO_validation.md` 의 Status 이력 블록을 2026-09-11 에 **한 글자도 고치지 않고** 옮긴 것(최신순). 세션 시작 시 읽지 않는다 — `docs/changelog_*.md` 처럼 특정 과거 결정의 배경이 필요할 때만 연다. 활성 TODO 의 Status 에서 밀려난 항목은 이 줄 바로 아래에 그대로 잘라 붙인다(최신이 위).

---

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

**(2026-09-19 → 2026-09-20 재감사 정정, 11차) 항목4/12/13 `값_적용후` 미러링 전수 감사 — 2026-07-21 owner 가 "후속 감사 필요" 라고 적어 두고 티켓이 안 만들어져 2개월 방치됐던 건. 결론: 미러링 셀 738(251버킷·21사), tier 가 실제로 움직인 버킷 58(+코리안리 기준선 2). 🔴 그러나 "오염 170셀" 은 과다계상이었다 — 실제로 틀린 것은 `item13` 55셀뿐이고 `item4`·`item12` 114셀은 정상이다.** 1차 세션이 API 한도로 죽어 재발주됐고, 2차 세션이 디스크 산출을 승인하지 않고 **마스터에서 독립 재계산**해 잡았다. 마스터는 양 세션 다 한 셀도 안 고쳤다. 티켓 `inbox/validation/20260919T1136Z`(status: answered, A-9 절), 발주 `inbox/parser/20260919T1400Z…`(lane: kics, **「(1) 정정판」으로 지시 교체**).

> - 🔴 **2026-09-20 정정 1 — 셀 수.** 1차는 **버킷 판정을 셀 판정으로 그대로 승격**했다("이 버킷 tier 가 움직였다" → "이 버킷 미러링 셀 3개 전부 오염"). **Δ의 귀착 항목을 안 쟀다.** 공통적용 TFI 는 Ⅰ(순자산)·Ⅱ(불인정항목)이 아니라 **Ⅲ(보완자본 재분류)** 을 움직인다. `item2_적용후`(발행사 공시값)로 참값을 역산: `item13_후 = item4_전 − item12_전 − item2_후`. 독립 참조 2개 전건 통과 — **R1**(가정 없음, 적용전 `item13==item3` 인 버킷) **8/8**(잔차 −0.53~+0.42) · **R2**(재분류 외 보완자본 TFI 불변) **60/60**(−1.26~+1.26). → **틀린 셀 = item13 56(기계확정 55 + 메리츠 2026.2Q 1, 그 버킷은 item2/3 후가 stale 이라 가려짐) · 정상 = item4 58 + item12 56 = 114.** 발주 원문의 "170셀 삭제" 를 그대로 실행했으면 **정상 셀 114개가 지워졌다.**
> - 🔴 **2026-09-20 정정 2 — A-3 의 계산가능 6버킷 중 동양생명 2024.1Q 는 stale.** 그 셀 `값_적용후` 는 **이미 결측**(2026-07-16 revert). 표의 19,645 는 `값`(적용전)이었다. 살아 있는 건 **코리안리 5개**. 그리고 **"나머지 52버킷 계산 불가" 도 틀렸다** — 역산식이 60버킷 전부 성립해 **55셀 전부 참값 계산 가능**(채울지 비울지는 owner, 기본값은 삭제).
> - **방향 재진술(owner 가 원래 물은 것)**: 틀린 것은 **Ⅲ 행 55~56칸이고 전부 과대(+Δ, +398~+17,858)**. **화면의 가용자본·기본자본비율은 과대도 과소도 아니다** — item1/2/3/27/28 적용후는 원문에서 따로 읽은 공시값이라 맞다(검산: 동양생명 2024.1Q 23,969.34/22,665×100 = 105.75 = 마스터값). 피해는 **적용후 세부표에서 Ⅲ 행이 바로 위 기본자본 행과 산수가 안 맞는 것** — 한 화면 안 두 줄이 모순. 데이터 RED 은 맞되 **범위는 Ⅲ 한 줄**이다.
> - **2차에서 재현된 것(독립 재계산 전건 일치)**: census 738/251/21 · 항목별 251·239·248 · `값_적용후==값` 738/738 · 다리 차분 시뮬 FIRE 55·PASS 183·SKIP 300(순진형 59) · item48 pre≠post 3칸 · C 교집합 538/39 · C 잔차 P1 0.5622%·P2 0.2949% · 게이트 적용후 다리 `RED=0 YELLOW=101 GREEN=137 SKIP=300`(직접 실행, exit 0) · 원문 2건(메리츠 2023.1Q L152-153 · 2026.2Q L377-378). **소소한 어긋남**: 게이트 `RED=36`(1차 기재 35, blocking 0 동일) · A-1 표의 TFI미적용 18/53·못쟀다 29/83 은 프로브 원값 17/50·30/86 과 다름(서울보증 2026.1Q 수기 재분류 1버킷 3셀, 추적 가능하나 **적힌 재현 명령만으로는 표가 그대로 안 나온다**).
> - **교훈**: 이건 게이트가 놓친 false-green 이 아니라 **감사가 만들어 낸 false-red** 다. "몇 칸이 틀렸나" 를 쓰기 전에 **"그 칸이 왜 틀렸는지 항목 단위로 역산되나"** 를 먼저 물어야 한다.
> - 재현(2차): `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/_probe_20260920_mirror_channel.py` → `verdict {"cells_actually_wrong_item13_only":55,"cells_corroborated_correct_item4_item12":114}`.
> - **"18사" 는 owner 서술이었고 실측은 21사 251버킷 738셀이다.** 738셀 전부 `값_적용후 == 값`(불일치 0). 계보 2중 확인 — ① `git show e1aa8ae`(2026-07-11, `backfill_post_transition_when_not_applied.py` 최초 실행)에서 4/12/13 미러링 674셀, 지금도 672셀 생존 ② 파서의 행→항목 매핑 `COMMON_ROW_MAP`(L99-105)은 **27/14/1/2/3 다섯뿐** — 4/12/13 은 애초에 추출 대상이 아니다. 원문 대조로도 **251버킷 전부 공통적용 2열표에 4/12/13 행 0개**.
> - **판정 5축 독립**: A 골든 추출기(`fill_post_transition_to_disclosure._extract_post_values` — 마스터의 item1/2/3/14/27 적용후를 만든 그 코드) · B docling 헤더깨짐 대응 스캐너 · C `kics_transition_applicability.json` TFI · D 마스터 자신의 item2/3 적용후 · E raw PDF fitz word-box. 판정 소스 실적 A 59버킷 · E 1버킷.
> - **전수 표**(회사·분기·항목·미러링값·적용전값·판정·Δ·방향) = `data/_derived/_probe_20260919_mirror_audit_v4.csv`. 오염 58 / 기준선뒤집힘 2 / 전=후 144 / TFI미적용 18 / **못쟀다 29버킷 83셀**(칸 단위 사유 기록, 29버킷 전부 raw PDF 까지 열어 텍스트량·앵커페이지 실측 — "MD 키워드 0" 으로 끝내지 않았다. 이 방식으로 5버킷 회수).
> - **오염의 기계적 증거**: `item2 = item4 − item12 − item13` 다리가 **적용전 잔차 ≈ 0, 적용후 잔차 ≈ −Δ**. Δ 는 회사별 상수(메리츠 2,850→2,837.3→1,791.95 · KB라이프 498.0 · 신한라이프 3,000 · DB손해 398.4 · 한화생명 17,857→4,983 · 코리안리 989.76~3,291.97) = 공통적용 TFI 금액.
> - ~~**방향**: 미러링값은 Ⅲ 과대 → 기본자본 과소. 6버킷만 실제값 확정, 나머지 52버킷은 계산 불가 → 삭제가 정답.~~ **← 2026-09-20 정정으로 대체됨**(위 3번째 불릿). 6버킷 중 1건 stale, 52버킷도 전부 계산 가능, "기본자본 과소" 는 표시값이 아니라 독자가 `Ⅰ−Ⅱ−Ⅲ` 를 직접 계산했을 때의 이야기.
> - **화면에 보인다(메타 아님, 데이터 RED)**: `K-ICS.html` 의 `NO_POST_TRANSITION_DISCLOSURE={4,12,13}`(L293)은 **결측일 때만** "미공시" 를 찍고(L443), `getRowValue`(L320-327)는 `값_적용후` 가 있으면 무조건 그 값을 쓴다.
> - **왜 게이트가 통과시켰나(실측)**: 룰은 이미 있다 — 축 `2_tier1_bridge`. 다만 `_TIER2_POST_UNESTABLISHED`(`validate_kics_disclosure.py` L144)에 들어 있어 적용후가 **비차단 YELLOW** 다. 이번 실행: `[적용전] RED=7 YELLOW=146 GREEN=376 SKIP=9` vs `[적용후] RED=0 YELLOW=101 GREEN=137 SKIP=300 ※ 적용후 관계식 미확립 → review(YELLOW), blocking 아님`. **`RED=0` 은 "깨끗" 이 아니라 "RED 로 안 올린다" 였다.** 오염 170셀이 저 YELLOW 101 안에 있다. 게이트 전체는 exit 0.
> - **룰 후보 + 편집 전 전 버킷 시뮬레이션(배선은 안 함)**: `2_tier1_bridge_post` 를 **잔차 차분** `|resid_post − resid_pre| > 2.0` 으로 RED 승격. 538버킷 실측 — 제안형 FIRE 55·PASS 183·SKIP 300 / 순진형(`resid_post==0`) FIRE 59. **오염 60버킷 중 55 포착, 정상 161버킷 오탐 0.** 순진형을 쓰면 적용전 다리에 박제 잔차가 있는 19버킷을 red-out 시킨다. 미포착 5건 사유까지 개별 기록.
> - **감사 중 새로 나온 것 2건**: ① 🔴 **메리츠화재 2026.2Q item2/item3 `값_적용후` 가 stale**(원문 PDF p18 = MD L377-378 기본자본 5,253,762→5,432,957 / 보완자본 9,289,444→9,110,249 백만원인데 마스터는 양쪽 다 적용전값). 470버킷 헤드라인 스윕에서 이 형태는 이 1버킷뿐. ② 코리안리 2023.4Q·2024.2Q 는 `[경과조치 적용 전 세부]` 표가 실제로는 **적용후 기준** — 다리가 두 컬럼 다 닫히는 이유가 "미러링이 맞아서" 가 아니라 "기준선이 같이 밀려서" 다. 값은 안 건드렸다(issuer-inconsistent keep as disclosed).
> - **B(item47/48 축)는 owner 판단으로 폐기** — 데이터는 원문과 일치(KR0104 2026.2Q·KR0080 2023.3Q), 축 개선 미착수. 등재·룰 변경 없음.
> - **C(17BS ↔ K-ICS 크로스체크) 설계 판정만**(배선 금지 지시 준수). 커버리지 = 교집합 **538버킷 39사 = K-ICS 의 100%**(17BS 전용 분기는 2021.4Q·2022.4Q 둘). 8쌍 열거 후 전수 잔차 측정: **P1 이익잉여금(중앙 0.56%) · P2 AOCI(0.29%) 만 등식 후보**, P3~P6·P8 은 중앙 30~70% 로 정의 차이(K-IFRS 장부가↔건전성감독기준 등) → 등식 금지, P7(법정준비금 4항목 합)은 한 버킷에 4개가 다 있는 경우가 **538 중 0** 이라 측정 자체가 불가. P1/P2 는 **이봉**이고 주범은 별도/연결(K-ICS item10 비지배지분 비영 버킷 중앙 6.94% vs 0.37%) → **회사별 기준 레지스트리가 선행조건**, 없이 걸면 약 55% 발화(red-out). 좁힌 코호트(P1 15사 161버킷·P2 19사 211버킷)에서 p95 1.3% → tolerance `max(0.5%, 5억원)` 근거 확보, 기대 발화 P1 16 · P2 19. **검출력 증거**: 코호트 안에서 NH농협손보 2023.2Q·3Q·2024.4Q 의 K-ICS 이익잉여금이 **정확히 0**(17BS 는 9,577억·9,115억·1조279억) — 지금 어느 룰도 안 본다.
> - 재현: `scripts/_probes/_probe_20260919_{mirror_census,mirror_audit_v4,headline_sweep,bridge_delta_sim,bs_kics_crosscheck,bs_kics_split}.py` (전부 읽기전용) + `scripts/validate_kics_disclosure.py`(exit 0).


**(2026-09-18, 10차) 경영공시(감독회계 업무보고서) 출처 셀이 PL_breakdown 에 처음 들어오는 건의 데이터계약 판정 — 오케스트레이터 티켓 `20260918T0205Z` 3문항 + 별건 2건. 결론: 지금 규격대로 병합하면 push 게이트가 막힌다(census RED **0 → 80**). 항목 8→5 · 회사 16→15 로 줄이고 병합 순서를 뒤집어야 한다.** 코드는 한 줄도 안 고쳤다(배선은 사이드카 발행 후 다음 라운드 — 지금 넣으면 red-out). 기준선 실측 `SUMMARY RED=0 YELLOW=90 provisional=False`.

> - **결정 1 — 계보 등록은 승인, 단 자물쇠가 3개 직렬이라 튜플만 넣으면 no-op 이다.** `("data/disclosure/","DISCLOSURE")` 는 무회귀(접두 충돌 0 · 디스크 사이드카 7종이 선언한 `source_file` 전수 10접두에서 판정 변화 0). 그러나 ① `source_id_for_lineage()` 는 `validate_data_contract.py:1190` 의 `if master in _CAPITAL_SECURITIES_MASTERS:` 안에서만 불리고 ② **`verify_provenance_sidecar()` 가 PL_breakdown 에 대해 아예 호출되지 않으며**(호출처 4곳 = sensitivity_heatmap·forward_capital·tier1/2·kics_rate_sensitivity) ③ **지금 사이드카로는 통과 자체가 불가능**하다 — `PL_breakdown_provenance.json` 은 638셀 전부 `source_file` 부재(파일이 스스로 `fields_pending_downloader` 라고 적고 있다) · `source_id` 전부 DART · 최신 2026.1Q(마스터 2026.2Q) · 33사(마스터 39사) → 계보 판정 **638/638 `None`**.
> - **🔴 같이 잰 것: provenance 축이 등록 마스터 10종 중 5종만 본다.** 읽히기만 하고 검증 안 되는 것 = `kics_disclosure`(1,123셀) · `CSM_waterfall`(327) · `PL_breakdown`(638) · `IFRS17_BS`·`dividend`(사이드카 파일 자체 없음). `_fallback_note`(=`MISSING_PROVENANCE_SIDECAR` RED)도 그 5개 분기 **안에서만** 도달 가능해서 "사이드카가 없다" 는 RED 조차 안 난다. 부수: L1391 주석은 kics_rate_sensitivity 에 "source_id 계보 일치" 를 검사한다고 **적어 놨지만 실제로는 안 한다**(같은 guard). 그 138셀은 `md_inbox/...` ↔ `DISCLOSURE_MD` 인데 계보 판정 `None` — `md_inbox/` 도 미등록.
> - **결정 2 — 투자손익(#17)·영업이익(#20)·영업외손익(#21) 백필 제외.** 4Q 중첩 43칸 전수 실측(tol `max(1억,0.5%)`): #1 보험손익 3F/39 · #16 2F/35 · #22 3F/32 · #23 4F/34 · #24 3F/30 인데 **#17 19F/38(50.0%) · #21 18F/38(47.4%) · #20 11F/22(50.0%)**. 동일개념 5항목의 FAIL 은 **3개 셀에 집중**(KR0004 2025.4Q·KR1010 2023.4Q·KR0150 2024.4Q), #17/#21 의 FAIL 은 **13개사에 분산** — 셀 사고가 아니라 구조다. 기전 확정: 마스터 `#17 = #18 투자이익 + #19 보험금융손익` 이 **336/336 성립(위반 0)**, 경영공시 `투자손익 = 투자수익 − 투자비용` 이 166/168 성립, 차이는 **투자손익↔영업외손익 경계 재분류**이고 합은 보존(KR0050 2023.4Q −360 vs −359.7 · 24년 33 vs 33.5 · 25년 28 vs 28.3). **발행사가 문서로 인정**한다 — KR0004 FY2024 공시 주3) "감독회계에서는 **투자손익**, 일반회계에서는 **영업외손익** 관련 계정으로 분류". → (a) provenance 표기만으로는 불가(PL 셀 단위 source 라벨을 읽는 소비자가 **0개**), (c) 화면 구분표기는 불요(남는 5항목은 동일개념이라 계단이 안 생긴다). `CONCEPT_REGISTRY`(L1475)에 `pl_disclosure_vs_dart` 등재 — 5항목 `comparable` tol `max(8억,1.5%)`(비-hold 최악 4.35억/1.67% 대비 1.8배), 3항목 `reference_only`(값 실으면 RED).
> - **결정 3 — "4Q 셀은 건드리지 마라" 는 지켜질 수 없다. 파서가 아니라 빌더가 만든다.** `build_root_masters.py:201-203` `build_pl()` 이 **모든 행의 `값_당분기` 를 버리고** `_flow_dangi(YTD)` 로 무조건 재계산한다 — 3Q YTD 를 채우는 순간 `4Q 당분기 = DART 4Q − 공시 3Q` 가 자동 생성된다(대상사 **334칸**, 억제 장치 없음. `pl_intentional_nulls.json` 은 `값` 전용). 오염 실측: 167 측정칸 중 22칸이 |Δ|>max(5억,10%)이고, KR0004 제외 17칸이 **전부 #21(10)·#17(5)·#20(2)** — 남는 5항목 오염 **0칸**. 화면에도 나간다(`IFRS17.html` L505·L712·L1844, `wfPeriod=quarter` → field `q`). → **결정 2 에 흡수**. 3항목을 빼면 4Q 당분기 문제도 같이 사라지고, 남는 5항목은 4Q 당분기를 **채우는 게 맞다**(명시적 결측 박제 불요, census 완전충족).
> - **🔴 결정 4 — census: 지금 병합하면 RED 0→80.** 읽기전용 시뮬(마스터 미수정): `coverage_holes` real **3→125** · display scope **0→80** · struct **15→0**, 해소는 서울보증 2024.1~3Q **3건(전부 비표시)**. 기전 = 대상 15사가 오늘 present 2~3분기뿐이라 전원 `struct`(검사 제외)인데, 11분기를 채우면 `active_min=7` 을 넘겨 **`active` 로 승격**되고 안 채우는 `생명장기손익` 때문에 전 분기가 "부분 hole" 이 된다. **2026-09-12 KR0150 서울보증 선례와 글자 그대로 같은 모양**(`validate_master_tables.py:532-537` 주석). 80건 중 **5건은 백필 탓이 아니다**(KR0004 2024.4Q/2025.4Q·KR0029 2024.4Q/2025.4Q·KR0051 2024.4Q = 오늘 `active_min` 뒤에 숨은 진짜 결손) → 오케스트레이터 질문의 답은 "**드러난다**". 판정 = **(B) `coverage_holes` 기대그리드를 소스별로**(계보 `DISCLOSURE` → §2-1 5항목, `DART` → 현행). **(A) `LOB_LEG_NA` 등재는 금지** — 그 회사들 DART 4Q 셀에 생명장기손익이 실재한다(12사 3종 전부 present). 개념이 없는 게 아니라 이 소스가 안 싣는 것이고, 등재하면 거짓 면제다.
> - **결정 5 — 스테이징 수용 등식 6개(즉시 반영).** 프로브 `status: OK` 198칸 중 **7칸(3.5%)이 표 자체 산수로 깨진다.** 자릿수 병합형 5칸: KR0074 2023.1Q 투자비용 **1,079,739,340억** · KR0074 2023.3Q 보험손익 **31,713,461억** · KR0095 2024.2Q 보험손익 **1,107,923,184억** · KR0095 2024.3Q 보험손익 **16,161,788억** · KR0095 2025.1Q 영업외손익 **−3,633**(정답 −36). 파급 1칸이 아니라 **3칸**(YTD 1 + 당분기 2) — KR0095 2024.3Q 를 실으면 2024.4Q 당분기 보험손익이 **−16,160,349억**. → E1~E6 자기폐쇄(tol 2.5억), 깨지면 `REJECT_SELF_CLOSURE` 로 값 미적재. 부수: **섹션 번호로 표를 찾지 마라** — KR0004 FY2025 는 `3-2-1)`, AIG 는 `2-1-1)`. 캡션 앵커.
> - **결정 6 — KR0004 예별손해 2025.4Q: 마스터가 맞다. 오케스트레이터 가설 반증.** DART 감사보고서 원문(제13기, `…20260406003175_00760.xml`)과 **5항목 전건 일치**(보험손익 −221.36 · 투자손익 −248.83 · 영업이익 −470.19 · 세전 −1,483.46 · 순이익 −1,542.87), 전년 비교열도 전건 일치. 경영공시 p.12 추출도 정확(△489/△4,203/△4,692/△4,697, 표 내부 산수 닫힘). **양쪽 다 맞는데 다르다.** 관측만(결론 아님): 공시 §3-2-1 의 `2024년`·`증감` 열이 **전부 공란**(FY2024 공시본엔 정상) · 공시 총자산 38,191억 vs 감사보고서 `TOT_ASSETS` 728억·`TOT_EMPL` 6명 · 본문에 `계약이전` 35회·`2025년 9월 3일` 6회. → 마스터 수정 발주 **없음**, KR0004 는 백필 대상에서 **제외**(16→15사), 질문형 티켓만.
> - **🔴 결정 7 — 이미 만들어진 스테이징에 "읽기 실패 → 0.0" 30칸이 들어 있다. 원문으로 반증했다.** parser 가 판정 전에 `data/_derived/pl_backfill_disclosure_20260918.json` 을 만들어 뒀길래(172셀 · OK 145 · 값 1,133 · 8항목 · 16사) 감사했다 — **마스터·사이드카는 아직 무손상**(`git status` clean). 값 1,133개 중 **89개(7.9%)가 정확히 0.0**, 그중 **30개(12셀)는 `raw_value` 가 빈 문자열** = 못 읽었는데 0.0 을 썼다. **반증**: `KR0075 BNP 2024.3Q` 스테이징 `보험손익=0.0`(`dash_zero=True`,`raw_value=''`) vs 원문 `…FY2024_Q3/raw/KR0075_…_amended.pdf` p.4 **`보험손익 -80`**. 0 이 아니다(그 PDF 는 텍스트가 두 번 그려진 레이어드 PDF — 단정은 안 한다). 항목별: **당기순이익 9 · 투자손익 7 · 영업외손익 6 · 보험손익 3 · 영업이익 3 · 법인세 1 · 세전이익 1**, **5항목 유지분에만 14칸**. 나머지 25칸(22셀)은 진짜 `-`(법인세 19 · 영업외 6)인데 **지금 둘이 같은 플래그로 뭉쳐 있어 구분이 안 된다**. → `dash_zero` 를 `READ_FAILED`(값 미적재) / `PRINTED_DASH`(일단 null, 판정 후 0 승격)로 분할. **결정 5 의 수용 등식이 이 사고를 실제로 잡는다는 실증도 얻었다** — 스테이징 8항목만으로 E3/E5/E6 을 돌리면 **9셀 FAIL**(E3 4·E5 4·E6 7 / 145)이고 12셀 중 5셀이 거기서 잡힌다. 부수: 스테이징 4Q 셀은 `KR0150 2023.4Q` 1칸뿐이고 마스터가 빈 칸 → **덮어쓰기 충돌 없음**. 축소 영향 값 1,133 → 704(#17·20·21 폐기 429 = 37.9%) → KR0004 제외로 **649**.
> - **🔴 새 사각 적발 — "자식 present · 부모 None" 29버킷(display 10), 어느 룰도 안 본다.** `#2 생명장기손익`=None 인데 자식(#3~#12)이 값을 갖고 있다. KR0004 3 · KR0029 3(전부 2023~2025.4Q) · KR0074/KR0075/KR0095/KR0097 각 1(2023.4Q) + 2023.1~3Q 19. **KR0075 2023.4Q 는 #3~#7 이 다 있는데 #2 하나만 비었다.** 사각 3중: ① `coverage_holes(active_min=7)` 가 그 6개사를 `struct` 로 제외 ② 나머지는 2023 이라 `known` ③ **PL 에 `_parent_present_child_incomplete` 대응 룰이 없다**(K-ICS 에만 있다). 파생 금지(#2=#3+#8 인데 KR0029 는 #3·#8 도 None) → 원문 재판독 발주.
> - 라우팅 3건(전부 `inbox/parser/`, `lane: ifrs17`): `20260918T0700Z__…backfill_scope_amend`(범위 정정 + 사이드카 발행) · `20260918T0705Z__…KR0004…scope`(질문형) · `20260918T0710Z__…pl_lob_parent_null_child_present`(29버킷). 티켓 `20260918T0205Z` → `answered`.
> - **병합 순서 확정(어기면 red-out 또는 거짓 면제)**: ① 사이드카 실물 발행[parser] → ② 계보 등록 + `verify_provenance_sidecar` 를 guard 밖으로[validation] → ③ `coverage_holes` source-aware[validation] → ④ `CONCEPT_REGISTRY` 등재[validation] → ⑤ 5항목 병합[parser→publishing] → ⑥ 게이트 RED=0 확인 후 push. 배선 시 같이: `_data_contract_selftest.py` 케이스 · `test_rule_coverage_manifest.py` · `test_master_tables_golden.py` `--update`(`coverage_holes` 를 고치면 SUMMARY 가 바뀐다).
> - 훅 확인(UH-1 교훈, 그 자리에서): `prepush_check.py` L288-290 이 `gate.run_gate(env)` 를 in-process 로 부르고 `n_red` → L556 `blocked` → L574 `exit 2`. **새 RED 은 실제로 push 를 막는다.** `check_as_of` 는 `DATA_CONTRACT_CHECKS` 에 이미 `WIRED` 라 매니페스트 수정은 불요.
> - 검증: `validate_data_contract.py` **RED=0 YELLOW=90** · `check_inbox_hygiene.py` 활성 5 · **위반 0** · 마스터·게이트·골든·`data/_gold/` 미수정(작업 전체가 읽기전용, 산출은 scratchpad 프로브 7종뿐).
> - 재현: `$py scripts/validate_data_contract.py` → `$py <scratchpad>/{sim_census,hypo_test,dangi_impact,accept_eqs,pl_orphan,kr0004_raw,kr0004_disc2}.py` (`$py` = `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`).

**(2026-09-14, 9차) UH-25 배선 — `JP_ESR_UNVERIFIED_VALUE` 신설. "이 화면값은 **어떤 축으로든** 판정된 적이 있나" 를 묻는 3번째 축이고, UH-25 가 지적한 비대칭(조정치 축에만 라이브 이빨이 있고 skip 축에는 하나도 없다)을 **대칭으로** 채웠다.** 전제는 8차가 등재만 하고 룰을 안 만든 이유였던 "오탐 억제를 실측할 수 없다" 인데, 오늘 T&D 출처가 목록 페이지 → 統合報告書 PDF 로 바뀌면서 그 점유가 사라져 **발화 0 을 실측으로 증명할 수 있는 창**이 열렸다(UH-5·UH-9 선례의 선행조건 충족).

> - **재측정: 오케스트레이터 숫자 4/4 정확, 단 한 개는 낡았다.** `verdict {'found': 16}` · `adjusted {'abstain_no_prose': 8, 'unqualified': 8}` · `doc_kind {'pdf': 16}` · 값 검증 0축 행 **0사** — 전부 일치. 낡은 것은 **posted 수**: 8차가 적은 15사가 아니라 **16사**(第一ライフグループ 220% 가 posted 로 들어왔다). T&D 222% 는 지금 `found`+`abstain_no_prose`+`pdf` = **1축 검증**이라 새 룰이 안 문다. census ↔ 증거 집합이 정확히 일치(증거에만 있는 행 0 · posted 중 증거 없는 행 0).
> - **배선 후 실데이터 발화 0 재확인**: `[source-gate] … YELLOW 0건 · RED 0건` · `1차 축 판정 분포: found=16` · `값검증 축 census: 판정됨=16 무검증=0 (그중 면제=0)`. **전제가 유지돼서 배선했다** — 깨졌으면 배선 안 하고 보고하는 것이 지시였다.
> - **판정식은 논리곱(=0축)이 아니라 논리합이다.** (a) `verdict ∈ (skip_landing, skip_no_text)` 또는 (b) `adjusted_verdict == not_applicable`. 곱으로 걸면 수집기가 반쪽만 회귀한 상태(한 축만 죽은 행)가 빠져나간다 — 이 저장소가 반복해서 데인 "룰이 순회는 하는데 그 칸은 안 본다" 의 모양이다. 호출 위치도 **verdict 분기보다 앞**이라 회사·verdict 필터 없이 전 행을 돈다.
> - **오탐 억제의 선은 `abstain_no_prose` 를 (b) 에서 뺀 것이고, 그 선이 load-bearing 임을 실측했다.** 그건 PDF 를 실제로 읽고 「라벨동반 산문 조각 0개」 로 판정한 결과(표·차트 전용 문서)라 1차 축이 `found` 로 살아 있다. 변이 M11 — `ESR_ADJUSTED_NOT_JUDGED` 에 `abstain_no_prose` 를 넣고 **증거는 손대지 않은 채** 돌리면 정상 **8사**가 한꺼번에 거짓 발화한다(東京海上HD·MS&AD·SOMPO·T&D·ソニー生命·ライフネット·au損保·明治安田損保).
> - **severity 는 YELLOW, 이빨은 push 묶음.** 조정치 축(`test_live_esr_evidence_has_no_unexempted_adjusted_figure`)과 **같은 모양**으로 맞췄다 — 근거 셋: ① 빌더 RED 로 걸면 기존 `test_skip_verdicts_are_yellow_not_red` 와 정면 모순 ② UH-25 가 적은 구조적 긴장(T&D 의 비-PDF URL 은 만료호스트 회피로 고른 것이라 데이터 오류가 아니다) 에서 정상 재빌드가 막힌다 ③ 비대칭의 근거가 "skip 축에 라이브 대조가 없다" 였으니 그 자리를 채우는 것이 해소다. 기존 테스트와 **역할을 docstring 에 갈라 적었다**: 그쪽은 *빌더 exit code 가 안 바뀐다*(합성), 새 것은 *배포본 증거에 그런 행이 면제 없이 남지 않는다*(실데이터). 모순 아님.
> - **면제 경로는 열려 있고 owner 권한이다.** `JP_ESR_UNVERIFIED_VALUE` 를 `SOURCE_RULE_IDS`+`EXEMPTABLE_RULE_IDS` 와 레지스트리 `_README` 에 등재했다(`exceptions` 는 **0건 그대로**). 10/31 에 정당하게 비-PDF 밖에 없는 회사가 나오면 그 경로로 간다. 등재 전에 먼저 물을 것은 「판정 가능한 1차 문서(PDF·有報)로 바꿀 수 있는가」 라고 레지스트리에 적었다.
> - **UH-25 remedy ② 도 같이 닫았다**: 게이트 요약이 종전에는 조정치 축 분포만 찍고 **1차 축은 안 찍었다**. 이제 `1차 축(JP_ESR_NOT_IN_SOURCE) 판정 분포` + `값검증 축 census(판정됨/무검증/면제)` 를 대칭으로 인쇄한다 — 분포가 skip_* 로 쏠렸는데 RED 0 이면 깨끗한 게 아니라 안 본 것이다.
> - **케이스 16건 추가**(85 → **101 passed**, 새 파일 없이 기존 `tests/test_jp_source_gate.py` 에 얹었다 — 새 파일을 만들면 §0 이 `tests/` 를 전체 게이트로 판정한다).
> - **변이 10/10 발화 + 음성대조 2건**(전부 사본 트리 `uh25_sand/` 에서만. 진짜 증거·census md5 작업 전후 동일: `fe0021bc…` · `ba79154d…`). M1 `verdict→skip_landing` **필드 (a) 단독** · M2 `adjusted_verdict→not_applicable` **필드 (b) 단독** · M3 둘 다(실제 UH-25 모양) · M4 `skip_no_text` · M5 다른 회사(かんぽ) · M8 그 회사 면제 등재 → **조용해진다** · M9 다른 회사 면제 → **여전히 발화**(셀 단위) · M10 다른 룰 면제 → 여전히 발화 · M12 진짜 빌더 엔드투엔드 → **exit 0**(YELLOW 설계대로) + 두 축을 이름으로 적는 발화 + `skip_landing=1 · 무검증=1`.
> - **🔴 중복이 아님을 증명했다(M6).** M3 변이를 남긴 채 **새 라이브 테스트만 삭제**하면 나머지 **100건이 전부 통과**한다(`100 passed`, 실패 0). 즉 기존 85건 + 내 합성 15건 어느 것도 이 상태를 못 잡는다. 반대 방향(M7, 판정식을 `return []` 로 gut)에서는 라이브 테스트가 조용해지고 **합성 6건이 발화**한다 — 라이브는 데이터를, 합성은 판정식을 지킨다(둘 다 필요).
> - **🔴 훅이 실제로 막는지 그 자리에서 실증했다(UH-1 교훈).** 진짜 증거 파일을 T&D 행만 UH-25 모양으로 **일시 변이**(백업 후 trap 복원) → `python3 scripts/prepush_check.py` → `FAILED tests/test_jp_source_gate.py::test_live_esr_evidence_has_no_unexempted_unverified_value` · `1 failed, 257 passed, 2 skipped` · **`offline tests(jp 묶음)=FAIL → BLOCKED (fix or owner-escalate)`**. 복원 후 md5 `fe0021bc…` 동일. 깨끗한 상태에서는 `258 passed, 2 skipped → gate-clear`(축소 전 242 → 258). 새 테스트가 `REDUCED_TEST_BUNDLE`(L111)·전체 묶음(L513) 양쪽에 이미 있는 파일 안이라 매니페스트 수정은 불필요했다.
> - **잔여(이번 범위 밖, UH-25 에 명시)**: **화면 축**. 배포본 `jp/jesr_esr.json` 에서 0축 검증 행과 2축 검증 행의 키 집합 차이가 여전히 공집합이고 `jesr_app.js` L307 이 둘 다 같은 「根拠資料 ↗」 로 그린다 — 게이트는 이제 막지만 **사용자는 여전히 구분 못 한다**. designer·publishing 소관이라 `inbox/jp/20260914T0740Z__validation__JP_MULTI__uh25_screen_axis_residual.md` 로 발주. UH-22(조정치 축 severity 승격)도 10/31 재census 대기로 계속 열려 있다.
> - 검증: `pytest tests/test_jp_source_gate.py -q` **101 passed**(85→101) · 축소 묶음 **258 passed · 2 skipped** · `prepush_check.py --scope-only` = **`REDUCED (jp-scope)`**(변경 3개 전부 jp) · 전체 실행 **`gate-clear`** · inbox 활성 1(내가 방금 낸 것) · 위반 0 · 한국 축은 이 컨테이너에서 미검사(`data/disclosure` 없음).
> - 재현: `python3 -m pytest tests/test_jp_source_gate.py -q` → `python3 /tmp/…/scratchpad/probe_gate.py`(실데이터 게이트, 산출 안 씀) → `python3 /tmp/…/scratchpad/uh25_mutate.py`(사본 변이 12종) → `python3 scripts/prepush_check.py`.

**(2026-09-14, 8차) 第一ライフグループ posted 전환 경로를 **사본으로** 전증 — 6종 전건 반응 실측 + 새 사각 **UH-25** 등재(비-PDF 출처 = 값 검증 2축 동시 침묵).** 진짜 census·`jp/*.json` 은 한 바이트도 안 건드렸다(작업 전후 md5 5개 동일). UH-19 교훈("census 만 고치고 빌더를 안 돌리면 게이트가 한 번도 안 돈다")대로 **경로를 먼저 증명**하고 무엇이 막을지 미리 쟀다.

> - **오케스트레이터 서술 5개 중 4개 맞고 1개 틀렸다.** 6종 룰 id · 증거 2종 봉투(`source_url_health` `2026-09-13T14:30Z` scope=all rows=254 · `esr_in_source_health` `2026-09-13T16:54Z` scope=all rows=15) · census 보다 낡은 증거 = STALE RED · PDF 만 기계검증 — 전부 맞다. **틀린 것**: "비-PDF 는 `not_applicable`". `not_applicable` 은 **`adjusted_verdict`** 값이고, 비-PDF 의 **`verdict`** 는 `skip_landing` 이다. 빌더의 `verdict` 어휘(`ESR_VERDICT_*`)에는 `not_applicable` 이 **없어서** 거기 들어오면 오히려 "모르는 verdict → RED" 로 걸린다. 결론(두 축 다 침묵)은 같지만 **경로가 둘**이라 룰을 설계할 때 갈라 봐야 한다.
> - **사본 드라이런 11 시나리오, 6종 전건 발화 실증**(`/tmp/…/scratchpad/dryrun_driver.py`, 사본 트리에서만). S1 둘 다 미실행 → STALE×2 + INCOMPLETE×2 **exit 1** / S2 URL 수집기만 → STALE×1 + INCOMPLETE×1 **exit 1** / S3 둘 다 실행 → **exit 0 · RED 0** / S4 `release.tdnet.info` → EXPIRING_HOST RED / S5 `classification=dead` → URL_DEAD RED / S6 `verdict=not_found` → NOT_IN_SOURCE RED / S7 `adjusted_alt` → ADJUSTED_FIGURE **YELLOW · exit 0**(이빨은 push 묶음) / S9 `adjusted_*` 필드 누락 → INCOMPLETE RED / S10 `scope=partial` → STALE RED.
> - **🔴 새 사각 UH-25 — S8.** 비-PDF URL 로 posted 하면 `verdict=skip_landing`(인쇄만) + `adjusted_verdict=not_applicable`(기권) 이라 **`JP_ESR_NOT_IN_SOURCE`·`JP_ESR_ADJUSTED_FIGURE` 가 둘 다 침묵**하고 빌더는 **exit 0 · RED 0건**. 배포본에서 **구분이 안 된다** — 0축 검증 행과 2축 검증 행의 **키 집합 차이가 공집합**이고 `jesr_app.js` L307 은 둘 다 같은 「根拠資料 ↗」 로 그린다. 즉 "검증 못 함" 과 "검증 통과" 가 사용자에게 같은 모양이다.
> - **세고 나서 말한다(UH-5·UH-9 선례).** posted 15사 중 `skip_landing`·`not_applicable` = **1사**(0 아님). **T&D 222%** 이고, 그 증거행 evidence 는 「본문에 222 표기가 **안 보인다**」 인데도 게이트는 green — **이미 라이브인 false-green** 이다. 10/31 노출: not_yet 62행의 ir_url 60/62 가 비-PDF, disclosure_url 도 비-PDF 33 · pdf 5. 有報 스윕이 쓰는 EDINET 뷰어 URL 도 **.html**(`…WZEK0040.html?…&S100YC7A` = 第一ライフグループ 근거 docID) 이라 이번 라운드에 2건째가 될 수 있다.
> - **비대칭이 근거다.** 같은 YELLOW 인 조정치 축은 `test_live_esr_evidence_has_no_unexempted_adjusted_figure` 로 push 묶음에 이빨이 있는데, skip 축에는 라이브 대조가 **하나도 없다**(유일한 테스트가 *침묵을 단언한다*). 게이트 요약도 조정치 축만 분포를 찍고 1차 축(found/not_found/skip_*)은 **분포를 안 찍는다** — 「기권은 세지 않으면 사각이 된다」 를 한쪽에만 적용했다.
> - **룰은 안 만들었다.** 필드는 이미 있다(`doc_kind` pdf 14·other 1, `content_type` pdf 52·html 194) 라서 새 수집기 없이 셀 수 있지만, 지금 RED 로 걸면 **데이터 오류가 아닌 T&D 1건이 정상 배포를 막는다**(그 행이 비-PDF 인 이유가 만료호스트 회피라, 고칠 대상이 URL 인지 룰인지 미확정). `docs/postmortems/README.md` **UH-25 / P1** 로 등재만.
> - **덤으로 확인한 것 2개.** ① 2026-09-13 4차가 발주한 census ragged row(第一ライフグループ 16열 헤더에 18열)는 **이미 고쳐져 있다** — 79행 전수에 `None` 키·결측 셀 0. 즉 `JP_CENSUS_SHAPE` 는 이번 전환을 막지 않는다. ② `check_source_urls.py` 모듈 docstring 은 census 대상이 `ir_url/disclosure_url` 이라 적었지만 **코드는 `source_url` 도 읽는다**(`collect_targets` L89) — 문서가 낡은 것이고, 덕분에 "새 URL 을 넣었는데 증거 수집 대상이 아님" 인 교착은 **없다**.
> - 검증: 실트리 md5 5개 불변(census·증거 2종·마스터·배포본) · `git status` 에 내 변경 0 · `prepush_check.py` = **`REDUCED(jp-scope)` … `gate-clear`** · 축소 묶음 **242 passed · 2 skipped** · inbox 활성 1(내 것 아님) · 위반 0.
> - 재현: `python3 /tmp/…/scratchpad/dryrun_driver.py S0 S1 … S10` (사본 트리 `pristine/` 에서 매 시나리오 재구성).

**(2026-09-14, 7차) UH-23 정식 해소 — 한정어 정본(도메인 문서 §3) ↔ 기계본(`ADJUSTED_QUALIFIERS`) **양방향** 대조 배선. 겸해서 TODO 의 과장을 정정했다 — UH-23 은 어제 절반만 닫혀 있었다.** `TODO_jp.md`(28) ③ 은 "한정어 목록 정본을 도메인 문서 §3 에 등재(**UH-23 해소**)" 라고 적었지만, PM 이 요구한 정식 해소는 「§3 절 신설 **+** 코드↔문서 대조 테스트」 둘이고 테스트가 없었다(`tests/test_jp_source_gate.py` 의 코드↔문서 대조는 **ESR 라벨만** 봤다). CLAUDE.md §3 대로 재서 확인했다.

> - **③ 자체도 과장이었다(내 실측).** §3 은 관측 3종(`除いた場合`·`適正水準`·`ターゲットレンジ`)만 산문으로 적고 코드는 **10종**을 들고 있었다. 코드 10종 중 §3 에 문자열로라도 있던 것은 **4종**뿐이고, 그중 `調整後` 는 §3 이 「추측으로 넣지 말 것」 으로 **지목한** 어휘인데 코드가 실제로 들고 있었다 — 정본과 기계본이 **서로 반대를 말하고 있었다**. 즉 UH-23 은 "테스트만 없는" 상태가 아니라 **정본이 기계본과 어긋난** 상태였다.
> - **고친 방향은 "문서를 코드에 맞춘다" 가 아니다.** 10종 전부에 15사 관측수와 채택근거(이형 / PM seed)를 열로 달아 §3 표에 올렸다 — 관측 0인 7종이 **추측 어휘가 아니라 관측된 구문의 이형·공시 관행 표기**임을 문서가 스스로 말하게 했다. 맨 `を除く`·`レンジ`·`目安`·`参考` 같은 **넓은 형태는 여전히 금지**(각주 기호·목차와 충돌)라고 §3 에 남겼고, "늘리려면 §3 표를 먼저 고치고 15사에 다시 돌려 정상사 발화 0 을 확인" 을 정본에 못 박았다.
> - **양방향이어야 하는 이유는 실측이다.** 집합일치를 부분집합(코드⊆문서)으로 약화하면 "코드에서 `ターゲットレンジ` 삭제" 가 **그대로 빠져나간다**(음성대조 M7, `2 passed`). 코드가 넓어지는 쪽만 막으면 *정본이 잡는다고 적힌 것을 코드가 안 잡는* 반쪽이 무검사로 남는다 — `適正水準` 을 코드에서 빼면 かんぽ 220 이 빠져나간다(6차 실측).
> - **기존 테스트와 역할을 갈랐고, 중복이 아님을 변이로 증명했다.** `test_qualifier_list_is_not_empty_and_excludes_definition_markers` 는 4종을 **테스트에 하드코딩한 바닥선**(문서를 고쳐도 안 흔들린다), 새 `test_definition_markers_named_in_the_doc_stay_out_of_the_code_list` 는 **문서를 따라간다**(§3 표에 5번째 정의 표지가 서면 코드 검사가 자동으로 넓어진다). 음성대조 M8 — `規制` 를 §3 정의 표지 표에서 빼 한정어로 승격하면 **새 2건은 조용하고 바닥선만 발화**(`old 83건 rc=1`). 반대로 M4(5번째 정의 표지 `暫定値` 를 코드·표 양쪽에 일관 추가)는 **바닥선이 조용하고 새 것만 발화**. 둘 다 필요하다.
> - **변이 6/6 발화**(사본 트리 `mut/` 에서만 — J-ESR·docs/domains·tests 만 복사, 종료 후 원본 md5 복원 확인: 수집기 `255d643f…` · 도메인 문서 `7a98fe6e…` · 테스트 `678a361e…`): ① 코드에 가짜 한정어 `参考` 추가 ② §3 표에서 `ターゲットレンジ` 행 삭제 ③ 코드에서 `ターゲットレンジ` 삭제 ④ 정의 표지 `暫定値` 를 양쪽에 일관 추가 ⑤ §3 한정어 표 통째 삭제 ⑥ §3 정의 표지 표 통째 삭제. **6건 전부 기존 83건은 침묵** — 새 2건을 deselect 하면 `83 passed`. 즉 중복 테스트가 아니다(이게 "새 테스트를 죽이면 기존으로 못 잡는다" 의 증거다).
> - **🔴 훅이 실제로 부르는지 — 절반만 참이다(UH-1 교훈대로 그 자리에서 확인했다).** 새 테스트는 `tests/test_jp_source_gate.py` 안이고 그 파일은 `prepush_check.py` 의 `REDUCED_TEST_BUNDLE`(L111)과 전체 오프라인 묶음(L513)에 **둘 다** 있다 — 게이트를 돌리면 실제로 돈다(실측 240→**242 passed**). **그러나 이 리눅스 컨테이너에서는 git 훅 자체가 안 돈다**: `.githooks/pre-push` 가 **mode 100644**(실행권한 없음)라 git 이 조용히 건너뛰고(**UH-24**, 같은 날 다른 세션이 루트 `TODO.md` 에 등재), 설령 chmod 해도 훅이 `PY="C:/Users/sangwook.cho/venvs/…/python.exe"` 를 하드코딩해 리눅스에선 `[ ! -f "$PY" ] → exit 1` 로 **게이트를 한 줄도 안 돌리고 죽는다**. 그러니 이 라운드의 정확한 주장은 "**`prepush_check.py` 가 부른다**" 이지 "훅이 강제한다" 가 아니다. 훅 수정은 `.githooks/` = 전체 게이트 경로라 이 컨테이너에서 손대지 않았다(UH-24 에 귀속).
> - **정정한 문서**: `TODO_jp.md`(28) ③④ + "다음" 줄 · `docs/postmortems/README.md` UH-23 행 + PM-2026-09-13 색인행 잔여표기 · PM 본문 §5 표 + 5번 칸 + 종결문. jp 도메인 문서는 jp 레인 소유라 티켓으로 통지: `inbox/jp/20260914T0425Z__validation__JP_MULTI__qualifier_canon_registered.md`.
> - **잔여**: PM-2026-09-13 의 미배선은 **UH-22 하나**(severity 승격 판단 — 10/31 재census 에서 재측정). cross-stage 로 **UH-24**(훅이 리눅스에서 무력) 가 열려 있다.
> - 검증: `pytest tests/test_jp_source_gate.py -q` **85 passed**(83→85) · 축소 묶음 **242 passed · 2 skipped**(그 2건은 `test_push_gate_wiring.py` 의 기존 skip, 내 것 아님) · inbox 활성 0 · 위반 0 · `prepush_check.py` = **`REDUCED(jp-scope)` … `gate-clear`**(한국 마스터 축은 미검사 — 이 컨테이너엔 `data/disclosure` 가 없다).
> - 재현: `python3 -m pytest tests/test_jp_source_gate.py -q` → `python3 scripts/prepush_check.py --scope-only` → `python3 scripts/prepush_check.py`.

**(2026-09-13, 6차) jp `JP_ESR_ADJUSTED_FIGURE` 배선 — "있는 숫자 중 틀린 것을 골랐나" 축. UH-21 해소 → PM-2026-09-13 `closed`.** 직전 5차의 `JP_ESR_NOT_IN_SOURCE` 는 "그 문서에 그 숫자가 있나" 만 물어서 かんぽ 220% 를 원리상 못 잡았다(220 은 그 자료 p35 에 **실재**하는 「大量解約リスクを除いた場合」 조정치, 실측 d=1 → `found`). 이번에 판정식을 정의해 같은 수집기·같은 증거 봉투에 얹었다 — `check_esr_in_source.py::scan_adjusted`(판정식 정본) → `esr_in_source_health.json` rows 의 필드 6개 → `build_jesr_page_json.py::_adjusted_figure_check`. **새 증거 파일을 만들지 않아 신선도 검사(`_load_evidence_envelope`)를 그대로 재사용한다.**

> - **본 룰은 "대안값 조건" 이다(이번 라운드의 판단거리).** 판정식 = ① 화면값이 나오는 ESR 라벨동반 **산문 조각**(`。`·개행 분할)이 1개 이상(0개면 **기권**) ② 그 조각이 **전부** 한정어를 달았다 ③ **같은 문서에 한정어 없는 다른 ESR 값이 있다** → `adjusted_alt`. ②까지만이면 `adjusted_only`(보조).
> - **③ 을 본 룰로 고른 근거는 실측이다.** 한정어 목록 4변형 × 15사: 확정본 → ①② 단독 발화 1 · ①②③ 발화 1(둘 다 정상사 오탐 0) / `適正水準` 을 빼면 **사고를 놓친다**(p18 「ESR適正水準 150~220%」 가 한정어 없는 조각이 되어 220 이 빠져나간다) / definition marker 4종(`ベース`·`内部管理`·`規制`·`速報値`)을 넣은 오염판 → **①② 단독은 정상 3사(日本生命·住友·朝日)가 거짓 발화**, ③ 을 붙이면 전부 조용 / 빈 목록 → 0. 즉 정상 상태에선 둘이 같은 답이지만 **룰이 망가지는 현실적 경로(다음 사람이 목록을 넓힌다)에서 ③ 만 버틴다**. 그 경로가 가설이 아닌 이유: `適正水準` 은 かんぽ **정답값 181 의 조각에도** 붙어 있고(「適正水準の範囲内にある」), 朝日의 정답 헤드라인은 「ESR(グループ)(内部管理ベース)は258.9%」다.
> - **한정어 목록은 15사 실측으로 확정**(seed 를 그대로 쓰지 않았다). 라벨동반 조각 전체에서 실제 관측된 것은 `除いた場合`(2, かんぽ) · `適正水準`(4, かんぽ) · `ターゲットレンジ`(1, 富国)뿐이고 `を除く`·`レンジ`·`目安`·`調整後`·`参考` 는 **관측 0**. definition marker 4종은 **일부러 뺐다**(코드 주석에 이유까지).
> - **오탐억제**: 정상 14사 중 **7사가 라벨동반 산문 조각 0개**(표·차트 전용 문서) — 기권 조건 없이 걸면 거짓 YELLOW 7건. 기권은 SKIP 이 아니라 **따로 세는 분류**다(수집기 summary + 게이트 요약이 분포를 인쇄: `unqualified=7 adjusted_alt=0 adjusted_only=0 abstain_no_prose=7 not_applicable=1`).
> - **severity 는 YELLOW 인데 이빨은 push 묶음에 뒀다.** 한정어 목록이 휴리스틱이라 RED 는 오탐 1건이 정상 배포를 막는다(UH-5·UH-9 선례). 하지만 **"인쇄만 하는 YELLOW" 는 통제가 아니다** — 2026-09-12 에는 census notes 에 「特定条件を除いた場合の ESR は 220%」 라고 **적혀 있었는데도** 그 값이 나갔다. 그래서 `test_live_esr_evidence_has_no_unexempted_adjusted_figure` 가 **배포본 증거**(= 게이트가 읽는 파일, 불변식 1)에 면제 없는 발화가 남으면 FAIL 한다. 고치는 길은 값 수정 또는 owner 면제 등재뿐이다.
> - **축이 조용히 사라지는 경로도 막았다.** YELLOW 라 exit code 를 안 바꾸므로 유일한 소멸 경로는 "수집기를 옛 버전으로 돌려 필드가 빠지는 것" → **필드 부재는 RED**(`JP_SOURCE_EVIDENCE_INCOMPLETE`, 면제 불가), 모르는 `adjusted_verdict` 도 RED. 진짜 빌더를 돌려 exit 1 실증(`test_gate_adjusted_axis_missing_changes_exit_code`).
> - **사고 재현(엔드투엔드, 사본에서만)**: census 를 かんぽ 220 으로 되돌리고 수집기를 그 원문 바이트로 재실행 → `verdict=found (p35,d=1)`(NOT_IN_SOURCE 는 여전히 조용) · `adjusted_alt`, 대안 `181` → 빌더 **exit 0** + 메시지 「같은 문서에 **한정어 없는 대안값 181%(p35) 가 있다**」 → **push 묶음 exit 1**. 현재값 181 은 `unqualified` = 발화 안 함.
> - 회귀는 **새 파일 없이** 기존 jp 2종에 얹었다(63→**83** + 26). 이빨 변이 **10/10 발화**(사본에서만, 원본 md5 복원 확인): 한정어 목록 비우기 2 FAIL · 기권 조건 제거 1 · 대안값 조건 제거 1 · 게이트 배선 호출 제거 8 · 룰 no-op 9 · 필드 부재 통과 3 · 모르는 verdict 통과 1 · 발화를 기권으로 강등 4 · 면제가 절차 룰까지 덮게 1 · 배포본 증거에 발화 심기 2.
> - **PM 종결**: 5칸이 다 차 `PM-2026-09-13` 을 **`closed`** 로 바꾸고 README 색인·UH 표를 갱신했다. 잔여는 **UH-22**(severity 승격 판단 — 10/31 라운드 재측정, 승격 3조건을 문서에 못 박음 / P2) · **UH-23**(한정어 목록 정본이 코드에만 있다. 라벨은 `docs/domains/claude-agent-jp.md §3` 이 정본이고 테스트가 대조하는데 한정어는 그 장치가 없다 — 도메인 문서는 jp 레인 소유라 손대지 않았다 / P3).
> - 검증: 수집기 `found=14 · skip_landing=1`(종전 동일) · 빌더 **exit 0** · `RED 0건 · YELLOW 1건(T&D)` · `jp/jesr_esr.json`·`jesr_master.json` 이 `generated_at` 외 **전량 동일** · `prepush_check.py` = `REDUCED (jp-scope)` · **238 passed · 4 skipped** · `gate-clear`.
> - 재현: `python3 J-ESR/check_esr_in_source.py --all --out J-ESR/esr_in_source_health.json` → `python3 J-ESR/build_jesr_page_json.py` → `python3 -m pytest tests/test_jp_source_gate.py tests/test_jp_deploy_matches_census.py -q` → `python3 scripts/prepush_check.py`.

**(2026-09-13, 5차) jp `JP_ESR_NOT_IN_SOURCE` 배선 — "그 문서에 그 숫자가 있나" 축. PM-2026-09-13 의 마지막 미배선 축이었다.** 오프라인/온라인을 갈랐다: 수집기 `J-ESR/check_esr_in_source.py`(신규, 네트워크)가 posted 행의 `source_url` 문서를 열어 `J-ESR/esr_in_source_health.json` 에 박제하고, 빌더는 **박제만 읽는다**(`source_gate_check` → `_esr_in_source_check`). 증거 봉투는 `source_url_health.json` 과 동일해서 신선도 검사를 **같은 함수**(`_load_evidence_envelope`)가 잰다 — 증거가 낡으면 두 룰이 같이 낡는다(한 쌍).

> - **증거 키는 (url, esr_pct).** url 만으로 잡으면 값만 고치고 수집기를 안 돌린 상태가 옛 값의 `found` 를 그대로 물려받는다 — 그게 정확히 2026-09-12 의 사고 모양이다.
> - **분포 실측이 PM §4c-pre-실측 과 정확히 일치**: posted 15사 전수 `found=14 · not_found=0 · skip_landing=1(T&D) · skip_no_text=0`. 최소거리 0~72 로 전부 `text_window` 안. `ソニー生命` 은 파이썬 TLS 악수 실패라 curl 폴백(UA 는 `jesr_http.UA_BROWSER` 그대로 — 헤더 기본값은 한 군데에만).
> - **초안 규격을 되돌려 재봤다**: "같은 문장" 으로 걸면 `found=7/14` = **거짓 RED 7건**(PM 예고치와 정확히 같다). 확정 규격(±200자 / 같은 표 행)은 14/14·거짓 RED 0.
> - **사고 재현 — 잡히는 것과 안 잡히는 것을 실측으로 갈랐다.** ① 東京海上HD 238 → `JP_ESR_NOT_IN_SOURCE` RED(exit 1). 238 은 56페이지 **어디에도 없다**(문턱을 100,000자로 풀어도 not_found) — 즉 200자 문턱은 사고 탐지가 아니라 **거짓 RED 억제**가 전부인 파라미터다. ② MS&AD 를 사고 당시 URL(합병 보도자료)로 되돌려도 RED — 그 URL 은 지금도 `ok_requires_headers`(살아 있음)라 **먼저 배선한 4종으로는 못 잡는다**. ③ **かんぽ 220 은 못 잡는다** — 그 자료 p35 에 「大量解約リスクを除いた場合のESRは220%」로 실재해 `found` 다. 값만 고치고 수집기를 안 돌린 상태에서는 `JP_SOURCE_EVIDENCE_INCOMPLETE` 로 걸리지만, 수집기까지 돌리면 통과한다.
> - **PM 의 주장이 틀렸음을 기록에 남겼다.** PM §5 는 "이 축이 東京海上HD·かんぽ 2건을 잡는다" 고 적고 있었다. 실제로 잡는 2건은 **東京海上HD·MS&AD** 이고 かんぽ 는 원리상 못 잡는다. PM 상태는 **`open` 유지**하되 사유를 3번 칸(배선)에서 **2번 칸(룰 정의)**으로 옮겼다 — かんぽ형을 잡을 룰이 정의된 적이 없다(**UH-21 신규 / P1**).
> - **UH-21 의 오탐억제까지 실측해 뒀다**(배선은 안 함, UH-5·UH-9 선례): 한정어(`を除いた場合`·`調整後`·`適正水準`·`ターゲットレンジ`) 없는 라벨동반 등장이 0개면 조정치 후보 → かんぽ 220 발화 / 181 미발화로 둘을 가른다. **단 정상 14사 중 7사는 라벨동반 산문 조각이 0개**(표·차트 전용 문서)라 "라벨동반 조각 ≥ 1 일 때만 판정" 조건이 필수 — 붙이면 표본 발화 1건·오탐 0.
> - 오탐억제: RED 로 읽는 verdict 는 `not_found` 하나. `skip_landing`(1사)·`skip_no_text`(**0사**, 방어용)는 YELLOW 인쇄만. `skip_no_text` 문턱은 **공백 제외 0자** — "몇 자 안 나오니 SKIP" 으로 올리면 그게 SKIP-on-missing 이다. 문서를 못 받으면 판정이 아니라 `fetch_failed` 로 적고 게이트가 절차 룰(면제 불가)로 잡는다.
> - **라벨 정본은 `docs/domains/claude-agent-jp.md §3`**, 코드는 기계본이고 테스트가 한 줄씩 대조한다. 구기준 단독 `ソルベンシー・マージン比率` 는 ESR 이 아니라 같은 페이지에 신기준 표지(`所要資本`·`適格資本`·`UFR`)가 있을 때만 라벨로 친다 — 이 조건이 없으면 au損保·明治安田損保의 5개년 구기준 표가 라벨로 읽혀 **거짓 통과**가 난다.
> - **fixture 가 게이트를 덮고 있던 것도 같이 고쳤다.** `tests/test_jp_deploy_matches_census.py` 의 10/31 flip 시뮬레이션(1·30·62사)은 census 만 뒤집고 선행 단계를 안 돌린 라운드를 흉내 내고 있어 새 룰에 전부 걸렸다 — **거짓 RED 가 아니라 게이트가 제 일을 한 것**(아무도 원문을 확인한 적 없는 posted 행). 게이트를 안 풀고 fixture 를 완성(`_synthetic_esr_evidence`)한 뒤, fixture 가 게이트를 덮지 않았음을 음성대조군(`test_flipped_census_without_fresh_esr_evidence_is_red`)으로 못 박았다.
> - 회귀는 **새 파일 없이** 기존 jp 2종에 얹었다(63 + 26). 이빨 변이 **8/8 발화**(사본에서만, 원본 md5 복원 확인): 배선 호출 제거 9 FAIL · 룰 no-op 9 · `not_found` YELLOW 강등 1 · 모르는 verdict 통과 1 · 증거 키 느슨화 2 · YELLOW 에 not_found 끼워넣기 3 · 봉투 신선도 무력화 6 · `fetch_failed` 통과 1. 수집기 쪽: 라벨 목록을 비우면 정상 문서가 무너져 거짓 RED — 그래서 목록 비어있지 않음을 테스트가 강제.
> - 검증: 빌더 **exit 0** · `RED 0건 · YELLOW 1건(T&D)` · `jp/jesr_esr.json`·`jesr_master.json` 이 `generated_at` 외 **전량 동일** · `prepush_check.py` = `REDUCED (jp-scope)` · **218 passed · 4 skipped** · `gate-clear`.
> - 재현: `python3 J-ESR/check_esr_in_source.py --all --out J-ESR/esr_in_source_health.json` → `python3 J-ESR/build_jesr_page_json.py` → `python3 -m pytest tests/test_jp_source_gate.py tests/test_jp_deploy_matches_census.py tests/test_deploy_assets.py -q`.

**(2026-09-13, 4차) jp 빌더 self-check 의 `records count != 15` 를 census 파생 항등식으로 교체 — 게이트가 사실이 아니라 옛 숫자를 지키고 있었다(TODO_jp(27) ②).** 10/31 J-ICS 공시기한 직후 census 의 posted 가 15사 → 60~70사로 뒤집히면 이 self-check 가 **정상 데이터를 RED 로 막는다**. 실측 재현(격리 사본, not_yet 62사를 posted 로 뒤집은 합성 census): HEAD 빌더 `SELF-CHECK FAIL: records count = 77, expected 15` · **exit 1**, 새 빌더 **exit 0 · posted 77 · RED 0건**. 2026-08-29 분기 지평 사고(게이트 3곳이 리터럴 분기목록을 들고 있다가 2026.2Q 를 순회조차 안 함)와 같은 형태라 그 교훈("하드코딩 자체가 재발 구조다")을 그대로 적용했다.

> 신설: `check_census_identity`(+`check_census_row_shape`·`check_preliminary_vocabulary`) · `check_deploy_identity` · 회귀 23케이스를 **기존 `tests/test_jp_deploy_matches_census.py` 에 얹었다**(새 파일을 만들면 `prepush_check.py` §0 이 `tests/` 를 전체 게이트로 판정한다 — 실측: 빈 테스트 파일 하나 추가 시 판정이 `REDUCED` → `FULL`).
>
> - **숫자가 아니라 항등식.** `census posted 행 수 == _meta.census.posted == len(마스터 records) == len(배포 records) + len(excluded)`. 수는 한 건 빠지고 한 건 중복돼도 맞으므로 **집합으로** 건다(company_jp·company_en).
> - **0 으로 닫히는 등식은 등식이 아니다.** posted==0 이면 산수는 전부 맞고 화면만 빈다 → `JP_CENSUS_EMPTY` 로 RED. 종전에는 리터럴 15 가 우연히 이 구멍을 막고 있었다.
> - **일부러 둔 리터럴**: `ESR_PCT_MIN/MAX`(100~1000%, 규제 하한·단위오류 상식선 — 데이터에서 파생하면 틀린 값이 스스로 범위를 넓힌다) · `AS_OF_TARGET`(기간 선언, 10/31 은 같은 기간에 회사만 느는 이벤트라 안 깨진다) · `SECTOR_MAP`·`PRELIM_KEYWORDS`·`_SUFFIX_ABBREV`·`DEAD_CLASSIFICATIONS`. 근거는 파일 주석에.
> - **덤으로 닫은 것**: `AS_OF_LABEL_JA` 를 `AS_OF_TARGET` 에서 파생(같은 사실 두 벌) · `SECTOR_VALUES` 를 `SECTOR_MAP.values()` 에서 파생(재타이핑) · `company_en` 중복 검사(2026-09-13 `6e051be` 실사고인데 게이트는 침묵했다; 하류가 이 키로 조인) · `preliminary` 모르는 값 RED(결측이 아니라 오독) · esr_pct 결측 시 정렬 TypeError → 이름 붙은 RED.
> - **새 사각 발견 → jp 로 발주**: census 14행 第一ライフグループ 이 따옴표 없는 쉼표로 **18열**(헤더 16열)이라 notes 가 잘려 읽힌다. 지금은 `not_yet` 이라 화면 무영향이지만 10/31 에 posted 로 뒤집히면 실린다 → `JP_CENSUS_SHAPE` 를 posted 행 한정 RED 로 걸고 티켓 `inbox/jp/20260913T1730Z__validation__JP_MULTI__census_ragged_row.md` 발주. `jesr_sources_2026Q1.csv` 6행·`jp_insurers.csv` 4행도 같은 모양이나 **이 빌더가 읽는 열은 넘침 앞쪽**이라 영향 0(실측) — RED 로 걸지 않았다.
> - **변이시험 11/11 발화**(사본에서만, 종료 후 원본 md5 `c03fad75…` 동일 확인): 리터럴 15 재삽입 · 항등식 호출 삭제 · 열수검사 삭제 · preliminary 검사 삭제 · 집합검사 제거(개수만) · posted==0 가드 제거 · main() 배포항등식 호출 삭제 · company_en 중복검사 제거 · None-취약 정렬 복귀 · as_of 라벨 리터럴 복귀 · unknown status 검사 제거.
> - **배선 ≠ 돈다**: 단위 테스트는 검사 함수를 직접 부르므로 호출 한 줄을 지워도 통과한다. 그래서 ① 진짜 빌더를 돌려 exit code 를 재는 케이스 5종(빈 census·ragged·preliminary·company_en 중복·esr_pct 결측) ② 데이터로 도달 불가능한 배포 항등식은 AST 배선 검사로 못 박았다.
> - 검증: 빌더 exit 0 · `[source-gate] … RED 0건` · `jp/jesr_esr.json`·`jesr_master.json` 이 `generated_at` 외 **바이트 동일** · `pytest tests/test_jp_source_gate.py tests/test_jp_deploy_matches_census.py tests/test_deploy_assets.py -q` **79 passed** · 축소 묶음 5종 **197 passed·4 skipped** · `prepush_check.py --scope-only` = `REDUCED (jp-scope)`.
> - **잔여**: `NEXT_UPDATE="2026-10-31"` 은 데이터에서 파생할 수 없는 편집상 약속이라 리터럴로 두고 **경고만** 인쇄한다(지난 날짜가 되면). RED 로 하면 데이터가 안 바뀐 날짜 경계에서 빌더와 배포 테스트가 동시에 터지는 시한폭탄이 된다.

**(2026-09-13, 3차) push 게이트 범위 판정을 `prepush_check.py` 안에 구현 — 규칙이 문서에만 있어서 강제도 완화도 안 되던 자리다.** owner 지적: "한국 거 안 고쳤는데 한국 게이트 때문에 일본 작업이 BLOCK 되면 안 된다". `CLAUDE.md` §5 는 2026-09-12 에 이미 "번들 diff 가 jp 범위뿐이면 한국 마스터 게이트를 안 돌린다" 고 적어 뒀는데 훅은 **그 규칙을 코드로 보지 않았다**(무조건 전부 실행). 실측 재현: jp 만 바꾼 번들에서 `PRE-PUSH VERDICT … gate RED=197 · K-ICS rule gate=BLOCK … BLOCKED`(exit 2) — 197건 전부 한국 원문 `data/disclosure/` 부재 때문이고 jp 변경과 인과 0.

> 신설: `prepush_check.py` §0(`classify_path`/`decide_scope`/`collect_changed_paths`/`resolve_scope`/`print_scope` + `_run_korean_master_gates()` 로 한국 축 묶음 분리) · `tests/test_prepush_scope.py`(65케이스) · `tests/test_push_gate_wiring.py::test_wired_means_wired_in_the_full_gate_only`.
>
> - **fail-closed.** 축소는 "변경된 **모든** 경로가 명시 목록 안"일 때만. upstream 없음 · git 실패 · 빈 diff · 미분류 경로 1개 → 전부 전체 게이트. 비교 기준 = `merge-base(@{upstream}, HEAD)..HEAD` + 스테이지 + 워킹트리 + 미추적(뒤 셋은 push 대상이 아니지만 **일부러 포함** — 커밋 안 한 한국 마스터 수정이 트리에 있는데 축소하면 다음 커밋이 무검사로 나간다).
> - **jp 범위 목록**: `jp/`·`J-ESR/`·`docs/`·`inbox/`·`.claude/`·루트 `TODO*.md`·`scripts/android_push_and_deploy.sh`·jp 테스트 2종·`CLAUDE.md`. **CLAUDE.md 를 넣은 근거**: 이 파일에서 기계가 검사하는 주장은 골든 표 동기화(`test_deploy_assets`)와 게이트 배선(`test_push_gate_wiring`) 둘뿐이고 **둘 다 축소 묶음에 있다**. 그 전제는 `test_claude_md_guards_stay_in_the_reduced_bundle` 이 지킨다. `scripts/*.py`(배포 .sh 제외)·루트 마스터 JSON·루트 HTML·`src/`·`data/`·`tests/`(jp 2종 제외)는 무조건 전체.
> - **"안 돌렸다" ≠ "통과했다".** 축소 시 verdict 는 `SKIPPED(jp-scope)` 로 찍고 0 을 pass 로 인쇄하지 않는다. 판정 근거(비교 ref·파일 수·결정적 파일 목록)를 매 실행 인쇄한다. 우회 환경변수는 **일부러 안 만들었다**; 수동은 `--full`(강제 전체)·`--scope-only`(판정만, 게이트 미실행) 둘뿐.
> - **실측(격리 클론, jp 3파일만 변경)**: 축소 `exit=0` **4.97초**(오프라인 173 passed·4 skipped, 한국 게이트 5종 전부 SKIPPED) ↔ 같은 트리 `--full` `exit=2` 16초(`RED=197`·K-ICS BLOCK·도메인 FAIL). 재현: `python3 scripts/prepush_check.py --scope-only` → 판정만.
> - **변이시험 12/12 발화**(사본에서만, 원본 md5 동일 확인): jp/ 목록삭제 · fail-closed 개방 · 빈 diff 축소 · git 실패 축소(fail-open) · `--no-renames` 제거 · `-z` 제거(한글 경로) · 미추적 제외 · 축소묶음에서 wiring 테스트 제거 · 축소 모드에서도 한국 게이트 호출 · `SKIPPED` 대신 `pass` 인쇄 · 전체묶음에서 셀프테스트 제거.
> - **잔여 UH-20**: 훅(`.githooks/pre-push`)은 stdin 의 refspec 을 게이트에 안 넘긴다 — 판정은 `@{upstream}` 근사다. 다른 remote/branch 로 미는 경우(격리 워크트리 cherry-push)는 근사가 빗나갈 수 있고, 그때는 fail-closed 로 전체 게이트가 돈다(안전 방향). refspec 전달은 후속.

---

**(2026-09-13 후속) UH-18 배선 완료 · UH-19 신규·같은 날 해소 — jp 레인에도 "게이트가 검사하는 파일 = 사용자가 보는 파일"이 걸렸다.** `build_jesr_page_json.py::source_gate_check` 4종(`JP_SOURCE_EXPIRING_HOST`·`JP_SOURCE_URL_DEAD`·`JP_SOURCE_EVIDENCE_STALE`·`JP_SOURCE_EVIDENCE_INCOMPLETE`)이 `self_check` 경유로 **exit 1 에 실제 반영**된다(변이시험: extend 한 줄 제거 시 exit-code 케이스 3개만 정확히 FAIL). 회귀 43케이스 + 이빨 변이 5/5. **네트워크를 안 타는 설계**: 판정은 `check_source_urls.py --all` 이 `source_url_health.json` 에 박제하고 빌더는 박제를 읽는다 — 그래서 `JP_SOURCE_URL_DEAD` 의 이빨은 `JP_SOURCE_EVIDENCE_STALE` 에 전적으로 의존한다(한 쌍, 독립 룰 아님). 오탐억제: RED 로 읽는 분류는 `dead` 하나뿐(254건 실측에서 "ok 아니면 RED" 는 48건 거짓 RED). 예외 등재처 `J-ESR/jp_source_exceptions.json`(0건, fail-closed, 절차 룰 2종은 면제 불가, 등재는 owner 권한). **UH-19**: jp 게이트는 빌더를 돌릴 때만 도는 구조라 census 만 고친 커밋이 검사를 통째로 비껴갔다(실측 사례 `62eed63`) → `tests/test_jp_deploy_matches_census.py` 로 "배포 JSON = census 재빌드 결과" 를 강제, 두 테스트를 `prepush_check.py` offline 묶음 + CLAUDE.md §5 jp 축소범위에 등재해 **훅이 실제로 부른다**. 포스트모템 `PM-2026-09-13` 은 **open 유지** — 사고 3건 중 2건(東京海上HD·かんぽ)은 URL 이 살아 있었고, 그 축(`JP_ESR_NOT_IN_SOURCE`)은 오탐억제 3종의 실측 분포가 선행조건이라 아직 안 걸었다(UH-5·UH-9 선례).

---

**(2026-09-13) jp 레인에서 false-green 3건 — 포스트모템 `PM-2026-09-13` 신설, 룰 4종 정의했으나 **전부 미배선(UH-18)**.** jp 빌더 self-check(범위·형식·합계)는 통과했는데 화면 수치 2건이 2차보도·조정치였고(東京海上HD 238→268 · かんぽ 220→181 · 明治安田生命 208.0→208.7), 출처 URL 1건은 ESR 이 한 줄도 없는 합병 보도자료였다(MS&AD). **메커니즘: self-check 가 census 안에서만 닫히는 자기참조라 "출처가 살아 있나 / 그 문서에 그 숫자가 있나" 축이 없다** — PM-2026-06-16("산술만 검사")의 jp 판. 룰 4종(`JP_SOURCE_URL_DEAD`·`JP_SOURCE_EXPIRING_HOST`·`JP_ESR_NOT_IN_SOURCE`·`JP_ESR_EDINET_MISMATCH`)을 오탐억제까지 정의하고 도구는 만들었으나(`J-ESR/check_source_urls.py`·`edinet_esr_probe.py`) 어느 게이트에도 안 걸려 있다 = honor system. 배선 방향은 **증거 신선도 검사**(`source_url_health.json` 의 `checked_at` 이 census 보다 오래되면 RED) — 네트워크 없이 "점검을 안 돌리고 census 를 고쳤다" 를 잡는 형태. 티켓 `inbox/jp/20260913T1500Z__validation__JP_MULTI__jp_source_gate_wiring.md` / P1.

---

**(2026-09-11) `public_exports/` 변이시험이 실제 배포 파일을 제자리에서 흔들다 끊긴 잔해(가짜 회사 행 1건)가 워킹트리에 남아 prepush 오프라인 테스트를 막았다 — 3번째 재발이라 구조를 바꿨다.** `check_public_exports(fd, out_dir=None)` 로 검사 폴더를 주입 가능하게 하고, `test_mutation_public_export_fires` 는 pytest 임시 폴더에 복사한 사본만 훼손한다. dirty-check·백업·`finally` 복원 코드 삭제(필요 없어짐). 실측: 관련 테스트 149 passed, 변이시험 후 `git status public_exports/` 깨끗, `validate_live_artifacts.py` RED=0. 밀려난 Status 항목(09-01 소급재작성 축)은 `docs/todo_archive_validation.md` 로.

> 📦 **Status 이력은 `docs/todo_archive_validation.md` 로 이동했다** (2026-09-11, 내용 무수정 — (2026-09-01) 판정 사이드카 및 그 이전 항목). 세션 시작 시 읽지 않는다; changelog 처럼 특정 과거 결정의 배경이 필요할 때만 연다. **이 Status 는 최신 5개 항목만 유지**하고, 밀려난 항목은 그 파일 헤더 바로 아래에 그대로 잘라 붙인다.


**(2026-09-02) 마스터 JSON 의 하류 사본이 둘인데 검사기는 하나였다 — `MASTER_XLSX_*` 축을 신설해 닫았다.**

> owner 승인(2026-09-02 "신설한다 — 14개 시트 전수"). 신설:
> `scripts/check_master_xlsx_drift.py`(비교기) · `validate_data_contract.py` CHECK 8
> `check_master_xlsx`(게이트, `run_gate` → `prepush_check.py` §1 → 훅) ·
> `tests/test_push_gate_wiring.py` WIRED 선언 · `tests/test_rule_coverage_manifest.py` 18개 테스트 ·
> `scripts/_probes/probe_20260902_master_xlsx_retrodiction.py`(되돌려 재보기).
>
> - **무엇이 사각이었나.** 루트 마스터의 하류 사본은 둘(`public_exports/` 스냅샷 ·
>   `insurequant_master_tables.xlsx`)인데 검사기는 `PUBLIC_EXPORT_*` 하나뿐이었다 —
>   **마스터 ↔ xlsx 를 대조하는 룰이 0건.** xlsx 만 뒤처져도 RED 가 구조적으로 나올 수 없었다.
>   `sync_master_xlsx_sheet.py` 는 요청받은 시트만 동기화하고 스스로 뒤처짐을 탐지하지 않으므로,
>   정합성이 **"누가 어느 시트를 동기화할지 기억하는 것"** 에 걸려 있었다.
> - **사고 2건.** ① owner 라이브 QA — NH농협손해 2026 기본자본비율 전망이 라이브·마스터 102.77
>   인데 xlsx 만 79.8(그 회사 2026.1Q 값). 38개사 전부 2090칸 중 **1219칸 stale**.
>   ② owner 반문("소진율 2종도 stale 하겠네")으로 13시트 전수 측정 → **가설과 결과가 달랐다**:
>   소진율 2종은 깨끗, 아무도 안 보던 `K-ICS공시` 가 stale(33셀·121행).
>   **어느 시트가 stale 한지 추측하지 말고 전수로 재라.** 데이터 수정은 `d1f1e7f`·`ee11c1d`.
> - **배선 전 시뮬레이션(규율)**: RED=0 · YELLOW=0 확인(13시트 **53,288행** = 워크북 전 데이터 행).
> - **되돌려 재본 실측**: 두 수정 커밋이 xlsx 만 건드렸으므로 그때 워크북을 꺼내 오늘 마스터로
>   대조 → `d1f1e7f~1` **RED=5** · `ee11c1d~1` **RED=2** · `HEAD` **RED=0**. 셀 수가 두 커밋의
>   자체 기록과 **정확히 일치**(1111/169/33/121) — 이 룰이었으면 사람보다 먼저 막았다.
> - **스키마는 import 한다.** 시트목록·평탄화·타입강제는 `build_master_xlsx`, 목표행·비교정규화·
>   행식별키는 `sync_master_xlsx_sheet` 에서 가져온다. 베끼면 빌더가 바뀌는 순간 갈라진다.
>   비교 기준은 동기화와 **정확히 같다** — 느슨하면 값 차이를 놓치고 **엄하면 어떤 도구도 만들 수
>   없는 상태를 요구**해 영원히 못 고치는 RED 이 된다. `'154'` vs `154.0` 은 셀 타입 차이라
>   드리프트가 아니다(양방향으로 테스트에 박아 뒀다).
> - **`요약` 은 행수만 검사한다** — 설명 열은 다른 레인이 손으로 관리하는 문구다(sync L21-22).
>   `MASTERS` 밖 수기 시트는 허용된 설계라 RED 이 아니라 YELLOW census.
> - **변이시험은 워크북을 재저장하지 않는다.** `compare_sheet`/`scan(sheets=...)` 을 순수 함수로
>   분리해 메모리 안에서만 흔든다(openpyxl load+save 는 다른 시트 수식 캐시를 날린다). 픽스처가
>   읽기 전후 바이트 해시로 무변경을 실측한다. 변이 8종 + 사고 재생 1종 전부 발화.
> - 회귀: `--selftest` **57/57 유지** · 게이트 **RED=0 유지**(YELLOW 96→97) · 오프라인 묶음 통과.
>   **실행 비용 +11.9초**(게이트 15.2→27.1초, 훅 17분 33초 대비 +1.1%).
> - 잔여 **UH-15**(하류 사본 매니페스트 부재 — 세 사본이 전부 사고 후에야 검사 대상이 됐다.
>   UH-14 와 같은 뿌리라 합류) · **UH-16**(sync 가 시트 무변경 시 `요약` 행수 미갱신, 현재 무해) ·
>   **UH-17**(워킹트리 기준 대조라 sync 후 커밋 없이 push 하면 안 잡힌다 — 커밋 기준으로 바꾸면
>   정상 sync 중 상시 발화라 오탐억제 설계 전까지 배선 안 함).
>   포스트모템 `docs/postmortems/PM-2026-09-02_master_xlsx_stale_unchecked.md`.

**(2026-09-01) item23(기타요구자본) 자식 24/25/26 적용후 결측 227버킷 판정 완료 — 등재부 신설로 SKIP-on-missing 사각을 닫았다.**

> 티켓: `inbox/validation/20260901T1200Z__orchestrator__MULTI__post_transition_item23_children_227_buckets.md`.
> 227버킷 = 196(부모≈0, 등식 0=0+0+0 자명, 원장 불요) + 31(부모 material, 원문대조 필요 —
> 교보생명 18·흥국생명 12·삼성화재/DB손해/한화생명/코리안리 각 1). 이미 오늘 오전 두 커밋
> (`e684f69`·`345b3a4`)이 227의 대부분(196+실제 채운 106칸 등)을 처리했고 `data/_derived/
> item23_children_audit/verdict_group3.json`에 31버킷×3칸=93셀 건별 판정(POST_EQUALS_PRE_LEGIT
> 54·SOURCE_ABSENT 36·UNMEASURED 3)까지 남겨 뒀는데 **게이트가 읽는 자리가 없어** 매 실행
> 미분화 SKIP("추출갭 후보")으로 재발할 상태였다. 이 세션이 KR0071 raw PDF(fitz) 직접 재확인으로
> 독립 검증(2023.2Q 사례 일치) 후 `data/_gold/kics_item23_children_post_absent.json`(31버킷,
> verdict+pin) 신설 + `scripts/validate_kics_disclosure.py::_other_capital_children_sum`(3-tuple
> 반환으로 확장, ledger lookup)·`scripts/validate_data_contract.py`(호출부 동기화 + 등재값 이탈시
> `OTHER_CAPITAL_CHILDREN_LEDGER_DRIFT` RED) 배선. **원장은 finding을 지우지 않는다** — skip
> 집계는 그대로고 태그에 판정만 붙는다, 등재값에서 벗어나면 RED로 승격.
> 검증: gate 전/후 상태카운트 바이트동일(RED=39/YELLOW=1658/GREEN=11102/SKIP=2803, 요구자본 축만
> 재태깅), `validate_data_contract.py` RED=0 유지, pytest 842 passed(BS golden 제외) +
> `_data_contract_selftest.py` 57/57.
> KR0071 2024.4Q(UNMEASURED)는 raw PDF가 정기경영공시가 아니라 DART 사업보고서(538p, K-ICS
> 수치표 0회) — 스캔이 아니라 **잘못된 파일**이라 OCR로 안 풀린다. `inbox/downloader/
> 20260901T1329Z__validation__KR0071_2024.4Q__wrong_document_not_periodic_disclosure.md`로 라우팅.

**(2026-09-01, 이전) 판정 사이드카 2종이 2026.2Q 전체에 대해 스테일이었다 — 게이트가 39사를 조용히 "판정 불가"로 흘리며 exit 0 이었다. 경로·지표·스테일 검사 셋 다 고쳤다.**

> 수정: `scripts/_disclosure_pdf_paths.py`(신설, raw//pdf/ 단일 해석기) ·
> `scripts/build_kics_source_textlayer.py` · `scripts/extract_transition_applicability.py` ·
> `scripts/validate_kics_disclosure.py`(freshness 경로 + 신규 룰 `SIDECAR_STALE_LATEST_QUARTER`)
>
> - **원인 ① 디렉토리 축.** 13분기 동안 공시 PDF 는 `data/disclosure/<period>/raw/` 에 있었는데
>   **2026.2Q 부터 `pdf/` 로 바뀌었다**(실측 `FY2026_Q2: raw=1 · pdf=39`, 그 전 분기는 전부
>   `raw=38~40 · pdf=0`). `raw/` 만 glob 하던 두 생성기가 2026.2Q 를 통째로 스킵했다. 같은 버그가
>   이 저장소에서 **세 번째**다(`rebuild_combined_transition_after._pdf` · `fill_market_subitems`
>   에 이어). 그래서 개별 패치 대신 해석기 하나로 모았다.
> - **원인 ② 판정 지표(owner 지적).** 판독성을 **문서 전체 평균 chars/page** 로 쟀다. 그 지표는
>   "앞은 스캔·뒤는 감사보고서 텍스트" 문서를 영원히 READABLE 로 부른다(흥국생명 FY2024_Q4:
>   p1-112 이미지인데 전체평균 532.8 → READABLE). 이 오판이 owner 의 옳은 `image-only` 등재를
>   2026-08-21 에 뒤집게 만들었고 처방을 OCR 대신 재수집으로 오라우팅했다. 이제 페이지별 분포 +
>   K-ICS 절 밀도로 재고, 신규 상태 **`SCANNED_SECTION`**(문서는 맞고 절만 이미지 → 처방=OCR)을
>   가른다. 두 판정 중 **엄한 쪽**을 써서 이 지표가 절대 느슨해지지 않게 했다.
> - **원인 ③ 스테일 자체가 무검사.** 사이드카가 최신 분기를 안 담아도 게이트가 통과했다 →
>   신규 RED `SIDECAR_STALE_LATEST_QUARTER` + YELLOW `SIDECAR_COVERAGE_GAP` 배선.
>   역방향 검증: 구 사이드카를 되돌리면 **RED 2건(2026.2Q 39 + 3 버킷)** 으로 정확히 터진다.
>   `prepush_check.py` 는 이미 이 게이트를 부르고 `blocked = ... or n_kics` 로 강제한다(확인함).
> - **실측 이동.** textlayer 486→538셀(2026.2Q 39사 신규) · applicability `NO_RAW_PDF` 8→0 ·
>   게이트 "판정 불가" **57칸/34버킷 → 37칸/20버킷**, `UNMEASURED` **25→0**.
>   사이드카만 A/B 한 결과 blocking RED **1→7**(+6). 값 flip 은 전부 `UNKNOWN→known` 이고
>   기존 판정을 뒤집은 것은 0건.
> - **새 RED 6건은 진짜 결함이었고 같은 라운드에 닫혔다** (KR0009·KR0069·KR0150 2026.2Q ×
>   값/값_적용후): 항목 47~54 가 마스터에 없는데 **원문 MD 에는 숫자가 있고 2026.1Q 에는 적재돼
>   있었다**(커버리지 회귀 `item47` 37/39 → 35/39). parser/kics 발주 → 적재 완료 →
>   **셀 단위로 원문과 대조 확인**(예 KR0069 item47 118,528.22억 = 원문 11,852,822백만 ✅).
>   `item47` 보유 **38/39**, 그 RED **6→0**, blocking RED **7→1**.
>   티켓은 `inbox/_resolved/20260901T0400Z__validation__MULTI_2026.2Q__tier2_tfi_rows_47_54_absent.md`.
> - **잔여 blocking RED 1건은 `19_market` 이고 내 변경과 무관하다** — 사이드카 A/B 양쪽에 똑같이
>   있었다(구 사이드카로 돌려도 나온다). 이 세션에서 원인 규명 안 함.
> - **골든:** `tests/test_kics_rules_golden.py` 는 사이드카 교체 직후 해시가 어긋났으나
>   (구 사이드카로는 PASS 확인 = 내 변경이 원인, 의도된 산출 변경) **손으로 고치지 않았고**,
>   parser 백필 라운드가 재생성하면서 현재 **PASS**. 오프라인 74개 전부 통과.
> - **경고:** `extract_transition_applicability` 의 "표가 있으면 TFI=O" 휴리스틱이 삼성생명 6분기를
>   오판한다(원문은 "공통 및 선택 경과조치를 적용하지 않았습니다"). 일반화 수정("전=후면 X")은
>   **198칸을 O→X 로 뒤집어** blocking RED 을 SKIP 으로 바꾸므로 **기각**했다. 좁은 대안(문서수준
>   부정문 + `외에` 배제)을 시뮬(10버킷 매치 / 6칸 정정 / 대조군 4칸 일치)해 parser 에 발주함.

**(2026-09-01) 미결 — owner 판단이 필요한 것 2건**

> 1. **“분기별 원공시본 기준” 정책이 선언된 적이 없다.** 실측: 가장 가까운 서술은
>    `data/_gold/kics_exemption_provenance.json` KR0032 2024.3Q 엔트리의 “as-disclosed 를
>    그대로 두는 것이 이 저장소의 ‘발행사 기재대로’ 원칙과 일치한다” 인데, **같은 엔트리가
>    ‘as-disclosed 를 유지할지 as-restated 를 채택할지는 owner/parser 정책 결정이고 이
>    세션은 정하지 않았다’ 라고 명시**한다. 관행일 뿐 결정이 아니었다. 게다가 **IFRS17 CSM
>    축에서는 owner 가 반대로 결정했다**(2026-06-20: 후속 분기 비교표에서 재작성값을 pull 해
>    마스터를 재작성 기준으로 통일 — `validate_master_tables.py` L797-799 ·
>    `inbox/_resolved/20260620T0600Z__validation__KR0073__kyobo_csm_priorperiod_pull_from_comparative.md` ·
>    `data/_gold/user_csm_cells.json` “교보 재작성 기준 통일 58,249.2”). 즉 **저장소가 전부
>    as-filed 로 정렬돼 있다는 말은 사실이 아니다** — K-ICS 는 as-filed, CSM 은 일부 셀이
>    as-restated. 새 등재부가 선언하는 것은 **K-ICS 마스터의 기준**이며, 바꾸려면 owner 결정이
>    필요하다.
> 2. **과거 122칸을 등재부에 백필할지.** 지금 등재부는 검증된 2026.1Q 라운드 10칸뿐이다.
>    과거 시뮬레이션 결과는 `_history_probe` 에 **미검증 표시로** 넣어 뒀다(컨트롤 컬럼 대조·
>    잔여셀 육안 판독 안 함, 쌍당 3~9개사 미판독). 검증 없이 박제하면 그 박제 자체가
>    무검사가 된다.

**(2026-09-01) 소급재작성(restatement) 축을 등재·배선했다 — 그때까지 이 축을 재는 검사기가 저장소에 0개였다.**

> 신설: `scripts/detect_kics_restatement.py`(탐지기) · `data/_gold/kics_restatement_ledger.json`(등재부) ·
> `validate_data_contract.py` CHECK 7 `check_kics_restatement`(게이트, `run_gate` → 훅) ·
> `tests/test_push_gate_wiring.py` WIRED 선언 · `tests/test_rule_coverage_manifest.py` 18개 테스트
>
> - **무엇이 사각이었나.** 공시본 `[경과조치 적용 전 지급여력비율 세부]` 표는 **해당·직전·전전분기
>   3열**을 인쇄한다 → 같은 (회사,분기) 값이 두 번 인쇄된다. 발행사가 그걸 다르게 인쇄하면
>   소급재작성인데, **그 두 인쇄값을 대조하는 검사기가 하나도 없었다.** 교보생명(KR0073)
>   2026.1Q 재작성이 분기 변동 분석 중 **손으로** 발견됐다.
> - **39사 전수 재스캔(실측).** 필링 대 필링(1Q본 해당분기 열 vs 2Q본 직전분기 열)으로
>   **830칸 비교 · 미비교 0칸 · 미판독 0개사**. 결과: **재작성 1개사(교보생명) 10칸**,
>   나머지 38사 무변동. 오케스트레이터 1차 손스캔의 오탐(기타포괄손익누계액·신종자본증권)은
>   재현되지 않았다 — 원인 3가지를 전부 막았다(표 특정 / 소수자리를 원 토큰에서 셈 /
>   item27 파생값 제외).
> - **교보 10칸**: item1·2·4·11 각 +1 · item14 +871 · item15 +888 · item16 +445 ·
>   item19 +779 · item20 +553 · item22 +16. 발행사 사유가 원문에 있다(“종속회사 인수에 따른
>   기타요구자본 증가, 감독원 계리적가정 가이드라인 반영”). 파생 item27 은 161.92→160.41.
> - **마스터는 안 건드렸다.** 등재·탐지만 했다. 마스터 2026.1Q 는 34개사 전부에서 1Q
>   원공시본과 **셀 단위로 일치**(`m!=1Q본 = 0`) — K-ICS 마스터가 as-filed 기준이라는 것을
>   추정이 아니라 실측으로 확인했다.
> - **심각도 = YELLOW.** 과거 13개 분기쌍 전수 시뮬레이션: (회사,분기) 재작성 버킷 **37개 ·
>   셀 122칸**, raw 가 갖춰진 2023.4Q 이후로는 **매 분기 1~5개사**. RED 로 내면 거의 매
>   라운드 push 가 막히는데 막아서 고칠 것이 없다. **RED 은 마스터가 원공시본 기준을 벗어날
>   때만** — `MASTER_ADOPTED_RESTATED` / `PIN_DRIFT` / `CELL_MISSING` / 등재부 위생 3종.
> - 게이트 실측: **RED 0 유지**, YELLOW 201 → 203(버킷 1줄 + census 1줄), exit 0.
> - 변이시험 **15/15 검출**(재작성값 채택·제3값·행삭제·값null·근거필드삭제·키불일치·
>   등재부깨짐·등재부부재·스캔stale·미판독), tol 안(+0.4) 변이는 침묵, **등재 밖 200칸 변이
>   신규 RED 0**(오탐 없음). `scripts/_probes/probe_20260901_restatement_rule_simulation.py`
> - **⚠️ 정책이 저장소 어디에도 선언돼 있지 않았다** — 아래 “미결”의 첫 항목.

**(2026-09-01 10:16~10:30 KST) 미종결 inbox 8건 전수 재검증 — 5건 실측 종결, 3건 open 확정.**

> 종결(`_resolved/` 이동, 각 티켓에 명령·수치 기록): downloader `KR0011`·`KR0029` 2026.2Q 재탕 PDF
> (재수집 확인 — sha 교체·MD "26.2Q" 라벨·`validate_disclosure_freshness --period FY2026_Q2`
> RED=0/GREEN=39·게이트 두 회사 RED 0) · validation `KR0029 2025.3Q 2_tier1_bridge`
> (`kics_exemption_provenance.json` L1826~1891 등재 + `validate_kics_disclosure.py` L2442 배선,
> 박제잔차 −58.0 = 실측 −58.0, blocking RED 0) · designer `capsec_numerator_as_of`
> (커밋 `a4bfddf`, `K-ICS.html` L971-979 이 행별 `numerator_as_of` 를 찍음; 둘 다 null 인 14사는
> 전부 발행 0) · parser `KR0008 market_subitem_total_row_labels`
> (`_TOTAL_ROW_CORE_RE`/`_table_risk_item_from_header` 신설, `extract_mkt_subs` 재현 36-40 5건 전부,
> `19_market` 2026.2Q GREEN 38·YELLOW 1·RED 0, 36-40·41-46 결측사 0/39).
>
> **open 확정 3건 (전부 parser/kics lane)** — 각 티켓에 "남은 것 한 줄" 로 명시:
> ① `20260831T0700Z` docling window: 데이터 증상은 소멸했으나 **요청 2(`source_page_ranges` 가드)
> 배선 0** (`grep -rn source_page_ranges --include=*.py scripts/ src/ tests/` = probe 뿐), 세 번째
> 실패양식 원인 미규명, **신규 실측 반례** KR0069 2026.2Q MD 에 금리·주식위험액 절이 여전히 없어
> 마스터와 MD 가 갈라짐. ② `20260831T0800Z`: `compute_tier2_utilization.py` 가 아직 마스터
> item47~54 를 안 읽고(MD_DIR 기본값도 FY2025_Q4) 한도 대조 검산도 없음, `--ocr-scale` 정식화 미답.
> ③ `20260901T0500Z`: `_pdf()` 는 고쳐졌고(39/39 해석) 4버킷도 보존됐으나 **요청 2(스킵 비율 인쇄 +
> 50% 초과 시 non-zero exit) 미반영** — 지금도 스킵이 exit 0 이다.
>
> 신규 발주: `inbox/downloader/20260901T0140Z__validation__MULTI__disclosure_selector_hardening.md`
> (KR0011 위치고정 xpath · KR0029 하드코딩 `pancId` · KR0150 중복 `id="test1"` — 재발 자체는
> `validate_disclosure_freshness` 가 `prepush_check.py` L94·L228 로 push 를 막는다).
> `scripts/check_inbox_hygiene.py` = 활성 5 · 종결보관 369 · **위반 0**.

**(2026-09-01) `TRANSITION_AFTER_MMULT_MISMATCH` 흥국생명(KR0071)·농협생명(KR0104) 4건 = 우리 유도 오류. 원문 정정 완료, 해당 축 RED 0.**

> 처리: `scripts/_probes/fix_20260901_kr0071_kr0104_combined_transition.py --apply` ·
> 라우팅 `inbox/parser/20260901T0500Z__validation__MULTI_2026.2Q__combined_transition_rebuild_skips_pdf_dir.md`
>
> - **판정 = 발행사 자기모순 아님.** 원문은 결합(②+③) 시나리오의 `item15/16/22/23후` 를
>   **인쇄하지 않는다**. 인쇄된 건 헤드라인(1·14·27후)·②표(17후+29~35후)·③표(19후+36~40후)와
>   ②·③ **각각의** 15/22/23후(단일 시나리오)뿐이다. 마스터는 결합 헤드라인 `14후` 에 **②단독**
>   `22후/23후` 를 붙여 `15후` 를 역산해 뒀다 — 22후/23후는 시나리오마다 다르므로(흥국 ② 4,764.60
>   vs ③ 5,930.51) 그 가정이 거짓이고, 그래서 R4 재조합과 어긋났다.
> - **R4 가 발행사 산식이라는 증거**: 같은 문서의 **인쇄된 기본요구자본 8개 컬럼 전부**
>   (2사 × 2분기 × {적용전, ②후, ③후})를 잔차 ≤0.01억 으로 재현한다.
> - 정정은 정본 methodology(`scripts/rebuild_combined_transition_after.py` docstring) 그대로 —
>   `15후=R4(17~20후)+21후` · `14후`는 원문 헤드라인 앵커라 불변 · `23후`는 KR0071 관계회사
>   (KR0005) 환산(비율 0.400607, 14분기 실측 스팬 0.400568~0.400628) / KR0104 0 · `22후`는 잔차 ·
>   `16후=sum(17..21)후−15후`. 정본 검사 4종(적용전 재현·R7/M 재현·단조성·잔차범위) 전부 통과.
> - 실측: 게이트 `validate_data_contract.py` RED **75 → 69**. 이 축 REDs 흥국생명 2건·농협생명
>   2건 소멸, 덤으로 `TRANSITION_AFTER_IDENTITY` 3건(흥국생명 R5·R6, 농협생명 R6)도 소멸.
>   셀 14개만 변경, 범위 밖 변경 0, 행수 25,202 불변, 중복 콤보 0.
> - **남은 사각(보고용, 미배선)**: `mmult15` 축이 **유도값을 검사하는 동어반복**인 버킷이 12개다
>   (`15후`가 R4로 쓰이고 `22후`가 잔차라 두 식이 구성상 닫힌다). 그 12개에서 "적용후 mmult
>   불일치 0" 은 증거가 아니다: KR0032 2024.1Q · KR0068 2026.2Q · KR0071 2023.2Q/2024.4Q/2025.3Q/
>   2026.1Q/2026.2Q · KR0082 2023.1Q · KR0097 2024.4Q · KR0104 2025.3Q/2026.2Q · KR1011 2026.2Q.
>   진짜 독립 검사로 남는 건 `mmult17`(R7×인쇄된 29~35후)·`mmult19`(M×인쇄된 36~40후)·
>   `27후=1후/14후×100`(양쪽 인쇄)·②③ 단일표 대비 단조성 넷이다. 룰 신설은 발주 대기.
> - 골든 2건(`test_kics_rules_golden` · `test_post_transition_golden`) 실패는 **내 변경과 무관**
>   함을 실측 확인: 룰엔진 골든 해시는 정정 전 백업과 **바이트 동일**(84705b8486fd66ec),
>   post_transition 골든은 `값`(적용전)만 읽는다. 둘 다 2026.2Q 데이터 적재로 이미 드리프트 상태.

**(2026-08-30 c) 사용자가 내려받는 `public_exports/` 12개 파일을 어떤 검사기도 읽지 않았다 — 배선했다. 그리고 그 사각을 잡았어야 할 테스트 자신이 못 보고 있었다.**

> 처리: `inbox/_resolved/20260830T1500Z__validation__MULTI__public_exports_uncovered.md` · commit `8c702fc`
>
> - `validate_live_artifacts.py` check 6 `check_public_exports` — 공개 스냅샷을 루트 마스터
>   (`git show HEAD:`, exporter 자신과 같은 기준)와 셀 단위 대조. 룰 15개: DRIFT ·
>   MISSING_CELL · EXTRA_CELL · INTERNAL_COL_LEAKED(`원보험사코드` 유출) · KEY_AMBIGUOUS ·
>   FILE_MISSING · UNREADABLE · SOURCE_UNREADABLE · MANIFEST_* 5종 등.
> - **시트 목록을 베껴 쓰지 않았다** — `export_public_sheets.MASTERS` 를 import 한다. 베끼면
>   13번째 시트가 조용히 무검사가 된다(CLAUDE.md ①b "룰을 한 개씩 베껴 심는" 패턴).
>   `test_rule_coverage_manifest.py` 가 시트 수 대조로 그 결합을 강제한다.
> - **조인 키 함정**: public 쪽엔 `원보험사코드` 가 없다(owner 지시로 드롭). 키가 유일하지
>   않으면 값 비교를 건너뛰지 않고 `KEY_AMBIGUOUS` 로 막는다 — 조용한 전건 미스 경로 제거.
> - 요청받은 `PUBLIC_EXPORT_STALE`(mtime YELLOW)은 **안 넣었다**: exporter 가 워킹트리가 아니라
>   HEAD 를 읽으므로 마스터 mtime 은 스냅샷 신선도와 무관하고(저장만 해도 움직인다) 오탐만
>   만든다. 진짜 낡음은 값 대조가 잡는다.
> - **더 깊은 구멍**: `test_push_gate_wiring._origin_main_fetches` 가 배포 HTML 만 훑고
>   `<script src="download-survey.js">` 를 안 따라가 그 12개 경로를 **한 번도 본 적이 없었다** —
>   "라이브가 fetch 하는 건 전부 검사기 선언이 있어야 한다" 는 테스트가 통과하는 채로 구멍이
>   열려 있었다. 같은 저장소 JS 까지 따라가도록 고치고 접두 선언(`public_exports/`) 형식 도입.
> - 변이시험 8/8 검출(값 1칸·행 삭제·행 추가·내부열 유출·manifest 거짓·파일 삭제·깨진 파일),
>   원본 바이트 복원 확인. 역방향(선언 삭제 시 12개 undeclared) 확인. `prepush_check` L83-93 이
>   이미 이 게이트를 부르므로 배선 즉시 강제된다.
> - **첫 실사용**: 오늘 `PL_breakdown.json` 이 커밋된 뒤 스냅샷을 재생성하지 않았다면 그대로
>   `PUBLIC_EXPORT_DRIFT` RED 였다. 재생성 후 RED=0.

**(2026-08-30 b) gold 오버레이가 115칸을 아무 탐지기 없이 덮고 있었다 — 이제 게이트가 그 숫자를 인쇄하고, 마스크가 벗겨지면 막는다.**

> 처리: `inbox/_resolved/20260830T0710Z__validation__MULTI__gold_overlay_mask_undetected.md`
> → `status: resolved`
>
> **사각의 정체.** `build_root_masters` 의 `_apply_csm_overrides()` / `_apply_pl_overrides()` 는
> gold `set` 의 값을 **비교 없이 UPSERT** 한다. 전 저장소에서 gold 를 빌더 소스와 대조하는
> 게이트·테스트는 **0건**이었다 → **gold 셀 밑에서 빌더가 회귀해도 화면은 옳고 모든 게이트가
> clean 을 찍는다.** KR0079 두 결함이 2025.2Q~2026.1Q 화면에서 안 보였던 이유가 이것이다.
>
> **배선.** `validate_data_contract.py` **CHECK 6 `check_gold_overlay`** 신설(→ `run_gate()`
> → `prepush_check.py` 1) 단계가 그 `run_gate` 를 부른다 = 훅에 걸린다). 룰 7개 —
> `GOLD_OVERLAY_{REDUNDANT(census YELLOW) · DRIFT(RED) · PIN_MOVED · NEWLY_REDUNDANT ·
> LEDGER_STALE · DUPLICATE_KEY · SOURCE_UNREADABLE(RED)}`.
> **티켓 범위를 CSM 하나에서 CSM+PL 두 오버레이로 넓혔다** — PL 도 똑같이 비교 없이 UPSERT 한다.
>
> **비교 기준 = `_additive_merge` 이전의 fresh 소스.** 그 폴백은 루트 마스터(= 직전 실행의
> gold 값)를 되먹이므로 기준으로 쓰면 검사가 자기 자신을 확인한다(ROW_ABSENT/NULL 14칸이 전부
> SAME 으로 보인다). PL 의 `_zero_other_expense` 도 같은 이유로 재현하지 않는다.
>
> **census 실측** — CSM 270칸: SAME_EXACT 28 · SAME_AT_1DP 58 · LOAD_BEARING 170 · ROW_ABSENT 12 ·
> NULL 2 → **마스크 86**. PL 198칸: 26 · 3 · 46 · 0 · 123 → **마스크 29**. 합 **115칸을
> `data/_gold/gold_overlay_ledger.json` 에 셀 단위 박제**(통째 skip 아님, 매 실행 재검산).
> 원 티켓 83 → 86 의 경로 셋: KR0079 parser 정정 +2 · 중복키 제거로 stale 5칸 정리(순증 0) ·
> **경계를 float 잡음이 가르던 것 +2**(`4727.25 vs 4727.2` = 정확히 0.05 인데 0.050000000000181
> 로 계산돼 마스크에서 빠짐 → `round(|Δ|,9)`).
>
> **양방향 전수 시뮬레이션 ALL PASS**(`probe_20260830_val_gold_overlay_simulation.py`):
> 닫힘 **115/115 = 100.0%**(SKIP 0 — 소스가 null 인 1칸도 "값을 얻으면" 을 변이로 삼았다) ·
> tol 안 변이 신규 RED **0**(밴드 아님) · 박제 안 된 216칸 변이 신규 RED **0**(오탐 없음) ·
> 등재부 전삭제 시 RED 0 + NEWLY_REDUNDANT 115(침묵 아님) · **이 축을 뺀 나머지 RED=0 YELLOW=92
> = 종전 baseline 그대로**. 게이트 총계 YELLOW 92 → **94**(오버레이당 census 한 줄), RED **0**.
>
> **배선 중 오탐 14건을 내고 잡았다.** 등재부 키를 `회사|분기|항목` 으로 만들었더니 CSM 과 PL 이
> 그 공간을 **공유해서**(`KR0072 2023.2Q 항목4` 가 양쪽에 있고 값이 전혀 다르다) 한쪽 박제가
> 다른 쪽 셀에 붙었다. 키에 overlay id 를 넣어 고쳤고 회귀 테스트로 박았다.
>
> **곁가지 — gold 중복키 7건 제거**(CSM 6 = KR0076 2025.4Q 항목1~6 · **PL 1 = KR0087 2025.3Q
> 항목11, 티켓이 몰랐던 건**). 둘 다 뒤 엔트리가 앞을 명시적으로 supersede 하고 있었고 적용이
> last-wins 라 **정합성이 리스트 순서에 걸려 있었다**. 적용 전후 last-wins 축약이 동일함을
> 확인하고 앞 엔트리만 삭제(값 변화 0, diff 는 삭제 56줄뿐).
>
> **곁가지 2 — `public_exports/CSM워터폴.json` 은 이미 동기화됐다**(2,172행 · 값 불일치 **0**).
> 다만 **`public_exports/` 를 읽는 검증기가 여전히 0개**다(`validate_live_artifacts.py` 포함
> grep 0건) — 불변식 1번의 미배선 구멍이라 후속 티켓으로 분리:
> `inbox/validation/20260830T1500Z__validation__MULTI__public_exports_uncovered.md`.
>
> **테스트.** `test_rule_coverage_manifest.py` 에 축 등재(룰 id 대조 · **마스크 칸 수 박제**
> `GOLD_OVERLAY_CENSUS={"CSM":(270,86),"PL":(198,29)}` — tol 을 넓히면 마스크가 부풀어 여기서
> 막힌다 · 박제 완전성 0 · 키 네임스페이스 회귀 · 변이시험 4종 · 훅 배선) 10개.
> `test_identity_registry.py` 에 `GOLD_OVERLAY_DRIFT`(IDENTITY, abs 0.05/rel 0.0) 등재 —
> `test_no_undeclared_threshold_constants` 가 **설계대로 먼저 FAIL 해서** 임계 등재를 강제했다.
> `test_mutation_delegation_is_real` 이 `DECLARED_RULES`(K-ICS 전용)만 봐서 이 축의 정당한 위임을
> "회피" 로 오판 → 그 파일이 선언한 **두 계열**을 보도록 고쳤다.
> `test_push_gate_wiring.py` 에 `check_gold_overlay: WIRED` 등재.
>
> **게이트/훅.** 오프라인 묶음 288 → **299 passed / 1 skipped**. `--selftest` **57/57**
> (inject 모드에서 축이 격리돼 합성 케이스를 오염시키지 않는다). 골든 재생성 **불요**
> (`validate_master_tables` SUMMARY·산출 무변동). **`prepush_check.py` exit 0 · gate-clear.**
>
> **이 축이 여전히 못 보는 것(명문화).** ⓐ LOAD_BEARING 216칸 밑의 빌더 이동 — 그 칸은 애초에
> gold 가 정답이고 빌더는 이미 다르므로 박제하면 파서 개선마다 오탐(C 시뮬레이션으로 확인).
> census 줄이 그 숫자를 매 실행 인쇄한다. ⓑ gold 가 유일 소스인 셀(CSM ROW_ABSENT 12 · NULL 2)의
> **원문 재확인 가능성** — 이 축은 "gold 가 유일 소스" 라고 말할 뿐 그 값이 옳은지는 안 본다.

**(2026-08-30) 폐쇄식이 양쪽 후보를 다 통과시킨 자리를 원문으로 갈랐다. 그리고 gold 오버레이가
83칸을 아무 탐지기 없이 덮고 있다는 걸 census 로 세웠다.**

> 처리: `inbox/validation/20260830T0400Z__orchestrator__KR0079__gold_vs_fixed_builder_adjudication.md`
> → `status: answered`
>
> **① KR0079 2025.2Q 항목4/5 = raw 채택(-685.50 / -992.07), gold(-886.27/-791.3) 폐기.**
> 두 후보의 **합계가 같아** 폐쇄식(항목6=Σ1~5)은 어느 쪽이든 `+0.00` 으로 닫힌다 — 산수로는
> 판별 불가인 자리다. 원문으로 갈랐다: 같은 필링 안에서 **네 표**(연결/별도 CSM 측정요소표 ×2,
> 연결/별도 보험수익표 ×2), 그리고 **1년 뒤 필링(2026.2Q 반기, rcept 20260814004054)의 전반기
> 비교열 두 표** — 총 **6개 독립 표**가 -685.50/-992.07 을 인쇄한다(소급재작성 없음).
> 행 식별은 캡션이 아니라 **IFRS ACODE** 로 했다(라벨 변형에 안 흔들린다).
> gold 값은 원문 어디에도 없다 — 문자열 0회, 상품별·CSM 하위열별 부분합 전수 조합 불일치,
> 연결/별도 동일, 출재 차감(-38.42억)도 아님. owner 답지(`gold/CSM waterfall_미래에셋생명*.xlsx`)는
> **2025.1Q·2025.4Q 만 있고 2025.2Q 는 없다**(두 답지는 raw 와 완전 일치 재현 확인).
> 소수자리 지문: KR0079 gold 27건 중 **-791.3 만 1자리**, `-1677.57 - (-886.27) = -791.30` —
> 구코드 잔차흡수값을 손으로 가른 **plug** 였다.
> **폐쇄식이 못 보는 축 = 개연성**: raw 채택 시 분기 상각 483.70/508.37/539.14억(완만 상승),
> gold 유지 시 483.70/**307.60**/**739.91**억(급락 후 급등). 게이트 귀결: `CSM_AMORT` 잔차
> `+200.77억(25.372%)` → `0.00억`, 등재부 `미래에셋생명보험|2025.2Q`(WATERFALL_SUSPECT) **삭제 대상**.
> 발주 → `inbox/parser/20260830T0700Z` (소수 **2자리** 유지 필수 — 1자리면 폐쇄식 0.1억 어긋남).
>
> **② gold 19건 = 존치, 단 조건부.** 원 티켓의 "코드가 gold 와 오차 0 재현" 은 부정확하다:
> `csm_waterfall_master_diag.json` 은 소수 1자리, gold 는 2자리라 19건 전부 `SAME_AT_1DP`
> (±0.05억)이고 `SAME_EXACT` 는 0건이다. 제거해도 폐쇄식 게이트는 안 깨진다(허용 max(0.1%, 2.0억)) —
> 즉 정밀도 문제가 아니라 **마스크 대 보호** 문제다.
> **`_apply_csm_overrides()`(build_root_masters.py L198-207)는 무조건 UPSERT 만 하고 소스와
> 비교하지 않는다. 전 저장소에서 gold 를 빌더 소스와 대조하는 게이트·테스트는 0건.**
> 전수 census(276): `SAME_EXACT` 28 · `SAME_AT_1DP` 55 · `LOAD_BEARING` 179 ·
> `ROW_ABSENT_IN_SOURCE` 12 · `NULL_IN_SOURCE` 2 → **마스크 후보 83건 / 9개사**(19건이 아니다).
> "지우면 방어막이 사라진다" 는 절반만 맞다 — gold 는 회귀를 막는 게 아니라 **가린다**(화면만
> 지키고 코드는 깨진 채, gold 없는 다음 분기가 깨진 값을 싣는다). 실제로 KR0079 두 결함이
> 2025.2Q~2026.1Q 화면에서 안 보였던 이유가 이것이다.
> 발주 → `inbox/validation/20260830T0710Z` (`GOLD_OVERLAY_REDUNDANT` census YELLOW +
> `GOLD_OVERLAY_DRIFT` RED 배선). **배선이 거부되면 그때는 제거가 옳다.**
>
> **③ 곁가지 2건.** gold `set` **중복 키 6건**(KR0076 2025.4Q 항목1~6) — 의도된 supersession
> 이지만 last-wins 라 **리스트 순서에 정합성이 걸려 있다**(앞 6건은 `why` 공란, `note` 만).
> `public_exports/CSM워터폴.json` 이 루트 마스터보다 **뒤처짐**(KR0079 2025.2Q 항목1 `값_당분기`
> public 20840.7 vs 루트 20847.3) — 지금 **게이트가 보는 파일 ≠ 사용자가 보는 파일**이다.
>
> **baseline 재현**: `validate_data_contract.py` → **RED=0 YELLOW=93 exit 0**.
> 마스터·gold·등재부 바이트 무변경(판정만, 실행은 발주).
> 재현 스크립트 4종: `scripts/_probes/probe_20260830_val_{raw_csm_table_scan,raw_csm_html_scan,
> kr0079_2025q2_adjudication_sim,gold_vs_source_census}.py`

**(2026-08-29 e) `PL_BRIDGE` 의 pass 절반 이상이 구성상 참이었다 — 이제 게이트가 그 사실을 인쇄한다. item22 는 메웠다.**

> 처리: `inbox/_resolved/20260829T2130Z__validation__MULTI__pl_eqs_constructive_tautology.md`
> → `status: resolved` (owner 가 제안 1·2·3·4 승인)
>
> **문제.** 빌더가 우변의 한 항을 좌변에서 빼서 만들기 때문에(`item7 = 3−(4+5+6)` ·
> `item12 = 8−(9+10+11)` · `item18 = 17−19` · `item21 = 22−20` · `item23 = 22−24`) 그 등식들은
> **산수상 깨질 수가 없다.** `pass=3057` 중 **1,608(52.6%)이 그런 pass** 다. CONSTRUCTIVE
> 변이시험(그 칸을 흔들고 빌더가 계산하는 하류 항을 빌더와 똑같이 재계산) 실측 탐지율:
> item5·6·9·10·11·19·22·23 **전부 0.0%** — `validate_master_tables` + `validate_data_contract`
> 를 다 물려도 신규 RED 0 건이었다.
>
> **① 명문화.** `PL_EQ_EVIDENCE`(등식별 `REAL`/`TAUTOLOGY`/`PARTIAL` **상수** — 주석이 아니라
> 게이트가 읽는 값) 신설 + `_assert_pl_eq_evidence_declared()` 가 import 시점에 판정 없는 등식을
> 죽인다. SUMMARY 인쇄 `pl_bridge:3057P/…` → **`pl_bridge:3057P(진짜1135·구성상1608·부분314)/…`**.
> 본문에 등식×증거력 pass 표와 `NOEQ`(등식으로 영원히 못 보는 항목) 건별 인쇄 추가.
>
> **② item22 배선.** 게이트 2f `TAX22_SOURCE_CROSSCHECK` = `|item22−item24| == |원천 법인세
> 계정|`(`ifrs-full_IncomeTaxExpenseContinuingOperations`). 그 값이 418/418 FS-API 캐시에
> 있는데 `assemble()` 이 곧바로 잔차로 덮어써서 버려지고 있었다. 부호는 안 본다(발행사 관행이
> 갈리고 그게 애초에 plug 를 도입한 이유). **전 버킷 시뮬레이션 선행**: 대조가능 282 · PASS 282 ·
> FAIL 0, 잔차 median=p90=max **0.000백만원**. 배선 후 게이트 `tax22_src:282P/0F/74S` 로 동일.
> 변이시험 탐지율 **0.0% → 100.0%**(282/282).
> **오프라인·결정적**으로 만든 것이 핵심이다 — `resolve_corp()` 는 gitignore 된 30MB
> `CORPCODE.xml` 을 읽고 없으면 **네트워크로 받아** 환경마다 커버리지가 갈린다. 그래서 추적
> 파일만 쓴다(`data/_derived/alotmatter_fetch_census.json` 39/39 + 추적된 `_fs_api_cache/`),
> 두 매핑이 **36/36 일치 · 불일치 0** 임을 실측했다. 캐시 파싱은 `fetch_dart_fs._parse` 를
> **그대로 호출**한다(재구현하면 게이트가 빌더와 다른 값을 본다).
>
> **③ 매니페스트 박제.** `tests/test_rule_coverage_manifest.py` 에 PL 축 신설 —
> `PL_CONSTRUCTIVE_BLIND`(5·6·9·10·11·19·23 무검사) · `PL_CONSTRUCTIVE_GUARDED`(3·4·8·17·20·
> 22·24·25) · `PL_DOWNSTREAM`(빌더 plug 재계산 표, 소스 문자열로 대조). 검사면 = PL 을 읽는
> 차단성 룰 전부(PL_BRIDGE·TAX22·CSM_AMORT·COVERAGE·data-contract RED). **매니페스트 자신의
> 변이시험 3종 전부 발화 확인**(`probe_20260829_pl_manifest_falsifiability.py`) — 선언이 면제가
> 아님을 기계가 증명한다. `-k pl_` 18 passed / 19.5초.
>
> **④ item9 판정 = 대안 축 없음.** `CSM_waterfall.json` 은 2,172행 **6항목 단일 축**이고
> **출재 항목 0** 이다. `build_csm_waterfall_master.py` 가 `_EXCLUDE_KW`·캡션 필터·소수 클러스터
> drop 으로 전 단계에서 배제하고, **그 배제는 옳다**(출재는 보유 재보험계약자산의 별도 워터폴 —
> `원수+재보험` 식은 346버킷 중 245건이 ±1% 밖, `원수+수재`는 20건). 즉 `CSM_AMORT_PL_LEGS` 를
> 넓히는 방식은 답이 아니다. 원문에는 있으므로(캡션 "원수 및 출재 …") **파서가 출재
> rollforward 를 별도 마스터로 추출**해야 하고, 그건 신규 과제라 발주하지 않고 명문화만 했다.
>
> **⑤ `test_identity_tautology.py` 를 PL 에 배선하지 않는다 — 그 결론도 명문화.** 귀무모형이
> 각 항이 등식 단위로 반올림됐다고 가정하는데 PL 마스터는 원÷1e6 이라 **건전한 항등식도 잔차가
> 정확히 0** 이다. 실측 9축 전부 RED 이고 excess 1위(1.93)가 하필 진짜 검산 축인 EQ9 였다.
> "배선을 잊었다"가 아니라 **"이 탐지기는 이 마스터에서 작동하지 않는다"** 가 결론이고, 그 파일
> docstring 에 절로 남겼다.
>
> **골든/게이트.** `master_tables_golden.json` `--update`(SUMMARY 한 줄, exit_code 2 불변).
> `test_identity_registry.py` 에 `tax22_source_crosscheck` 등재 — 그 파일의
> `test_no_undeclared_threshold_constants` 가 **설계대로 즉시 실패해서** 등재를 강제했다.
> `validate_golden_input_fingerprints` **갱신 불요**(RED=0, 6 spec ok — SPECS 의 `code_entries`
> 는 빌더만 추적하고 게이트는 골든이 매 실행 서브프로세스로 재실행해 stale 불가).
> `validate_data_contract` RED=0 YELLOW=92 **불변**. 훅 경로 확인: `validate_master_tables` 는
> `test_master_tables_golden.py` 경유(NOT_A_PUSH_GATE 선언대로), `test_rule_coverage_manifest.py`
> 는 이미 훅 목록 L169.
>
> **잔여(이 티켓 밖).** ⓐ item5·6·9·10·11·19·23 은 여전히 무검사 — plug 제거는 owner 결정
> (2026-06-08) 사안이라 제안까지만. ⓑ 출재 CSM rollforward 추출(parser/ifrs17 신규 과제).
> ⓒ tax22 SKIP 74버킷(FS-API 캐시 없음 56 + 22/24 결측 18)의 item22 무검사.

**(2026-08-29 d) 어제 신설한 leg-coverage 룰이 코리안리재보험 12분기를 오탐했다 — 데이터가 아니라 **등식**이 틀렸다.**

> 처리: `inbox/_resolved/20260829T1700Z__validation__MULTI__pl_item1_leg_coverage.md` → `status: resolved`
>
> **오탐 구조.** 룰은 "item13(자동차) 결측이 1,456~53,464백만원을 싣고 있다"고 12분기 내내
> 찍었다. parser 가 전 분기 원문 XML 을 grep 한 결과 **자동차 LOB 자체가 없다**(재무제표 표
> 안에 "자동차" 0회 — 걸린 것은 전부 관계기업 펀드명·임원 이력 문장). 코리안리는 재보험사라
> LOB 이 생명/장기/일반이고, 네 번째 다리인 item`2-1`(장기재보험 손익)이 마스터에 정상
> 발행돼 있는데 **검증 등식만 표준 3슬롯(2/13/14)이 LOB 의 전부라고 가정**했다.
> **빌더의 Tier-2 RC 게이트는 같은 항을 이미 `_extra_lob` 으로 더하고 있었다**
> (`build_pl_breakdown.py` L249-252) — 즉 빌더와 검증기가 서로 다른 등식을 쓰고 있었다.
> 이 저장소의 "게이트가 검사하는 것 ≠ 실제 계약" 사고의 한 변종이다.
>
> **조치(회사 하드코딩 아님).** `load_pl_extra_lob()` 신설 → 항목번호 패턴 `^2-\d+$` 를 ΣLOB
> 에 가산. 회사명으로 박으면 다음 재보험사에서 같은 사각이 조용히 재발한다. 자식
> `3-N`~`12-N` 은 그 다리의 하위 분해라 미가산(이중계상 방지).
>
> **실측(코드 수정 전 356 버킷 전수 시뮬레이션 → 수정 후 게이트, 정확히 일치).**
> `2e LEG-COVERAGE 닫힘 18→30 · 깨짐 34→22 · 좌변없음 18 불변`,
> `pl_bridge 3045P/47F → 3057P/35F` (468S·0NEW 불변). **새로 깨지는 버킷 0건.**
> 코리안리 12분기 잔차 |≤2.8|백만원(lhs 5만~24만 백만원 → 상대 ~0.001%).
> 재현: `scripts/_probes/probe_20260829_extra_lob_simulation.py`.
>
> **하이픈 서브 LOB census (이 라운드의 최대 산출).** 마스터의 하이픈 항목번호는
> **코리안리재보험 단독**, 11종(`2-1`~`12-1`) × 14분기 = **154셀**(루트·viz 동일, 항목명
> 충돌 0). 그런데 **그중 어떤 룰이라도 읽던 것은 `4-1`(수재 CSM상각, `CSM_AMORT_PL_LEGS`)
> 14셀뿐이었다 — 나머지 10종 140셀은 어떤 룰도 순회하지 않았다.** `2-1` 배선 후 남은
> 무검사는 9종 126셀. 재현: `scripts/_probes/probe_20260829_hyphen_lob_census.py`.
>
> **그 126셀의 부모-자식 3식은 일부러 배선하지 않았다 — 동어반복이다.**
> `2-1=3-1+8-1` · `3-1=4-1+5-1+6-1+7-1` · `8-1=9-1+10-1+11-1+12-1` 은 14/14 통과지만
> **잔차가 전건 정확히 0.000000000** 이다. `pl_breakdown/companies.py::leg()` 가 item7·12 를
> plug 로, item2 를 합으로 만들기 때문에 구성상 참이라 영원히 발화하지 않는다. 배선했으면
> 126셀이 GUARDED 로 보이면서 실제로는 아무것도 검증하지 않는 **false-green 을 내 손으로
> 만드는 것**이었다. 무검사로 두되 무검사임을 기록하는 쪽을 택했다(아래 census + 등재부).
> 재현: `scripts/_probes/probe_20260829_hyphen_tautology.py`.
>
> **미지 하이픈 census 배선 + 변이시험.** 등식이 아는 형태(`2-N` 가산 / `3-N`~`12-N` 자식)
> **밖의** 항목번호가 나타나면 2e 가 `LEGUNK` 로 건별 인쇄한다(오늘 0건). "0건" 이 "검사가
> 죽었다"가 아님을 보이려고 변이시험을 붙였다 —
> `scripts/_probes/probe_20260829_legunk_mutation.py` 5케이스 전부 PASS(`2-1` 가산 / 자식
> 미가산 / 가짜 `13-1` 발화 / `2-1`+`2-2` 복수 부모 / 정수 항목번호 무영향).
>
> **baseline.** `data/_gold/pl_bridge_baseline.json` 에서 코리안리 12건 삭제(`_promote` (1),
> 게이트가 `FIXED?` 로 인쇄). entries **47→35**, `등재부에만 남은 것 0`. `_counts` 도 실제
> entries 로 재계산(선언 52 vs 실제 47 로 이미 드리프트해 있었다). 데이터 결함이 아니었으므로
> documented exception 승격이 아니라 **삭제**다.
>
> **골든/지문.** `tests/fixtures/master_tables_golden.json` `--update`(SUMMARY 한 칸,
> exit_code 2 불변). 오프라인 484 passed/1 skipped. `validate_data_contract` RED=0 YELLOW=92
> (불변). **`validate_golden_input_fingerprints.py` 는 갱신 불요** — RED=0, 6 spec 전부 ok.
> 그 게이트의 SPECS 는 **빌더**만 `code_entries` 로 추적하는데 이번에 고친 것은 게이트
> (`validate_master_tables.py`)이고, `test_master_tables_golden.py` 는 매 실행 게이트를
> 서브프로세스로 재실행하므로 구조적으로 stale 해질 수 없다(그래서 SPECS 에 없는 게 맞다).
>
> **잔여 LEGRED 22건** — 전건 baseline 등재(`route: parser/ifrs17`, `deadline: 2026-10-31`,
> 신규 0). 예별손해 2024.4Q·2025.4Q item2(후보 표까지 특정했으나 폐쇄식 불일치로 미확정) ·
> AIG 3분기 · 신한이지 2분기(원문에 LOB 분해 표 자체가 없음, parser 재확인) · 2023 다수
> (사이트 비노출, 미착수).
>
> **곁가지(미조치, 기록용).** 같은 두 식을 **전 회사**로 돌리면 `3=4+5+6+7` 315건 중
> 284건(90.2%) · `8=9+10+11+12` 300건 중 258건(86.0%)이 잔차 정확히 0 이고 최대 잔차가
> 0.35·0.49백만원 = floor(200백만)의 1/400 이다. 이 두 식은 코리안리만이 아니라 저장소
> 전반에서 **거의 동어반복**으로 보인다. `2=3+8` 은 최대 잔차 10,169백만원이라 내용이 있다.
> 별도 조사 대상.

**(2026-08-29 c) 분기 지평 하드코딩 — 게이트가 최신 분기(2026.2Q)를 순회조차 안 했다. `RED=0` 이 "안 봤다"였다.**

> 처리: `inbox/validation/20260829T1910Z__orchestrator__MULTI__qs_ends_at_2026q1.md` → `status: answered`
> 신규 발주: `inbox/parser/20260829T2010Z__validation__KR0005_2026.2Q__pl_lob_legs_missing.md`
> (`lane: ifrs17` · `route: reparse`) — **현재 push BLOCKED (RED=1)**
>
> **원인 = 하드코딩, 그것도 세 곳.** `validate_master_tables.QS` 는 이 파일 **최초
> 커밋(`9243445`)부터** `2026.1Q` 로 끝나는 리터럴이었고 아무도 안 늘렸다. 같은 병이
> `validate_data_contract._DISPLAY_QUARTERS`(census RED 발화 스코프)와
> `validate_kics_rate_sensitivity.ALL_Q`(RS4 census)에도 있었다. `validate_master_tables`
> 안에는 **두 번째 지평**까지 따로 있었다 — `FY_Q["2026"] = ["2026.1Q"]` 라 연속성 검사도
> 2026.2Q 를 안 봤다.
>
> **자물쇠가 직렬 두 개였다.** `_DISPLAY_QUARTERS` 만 열면 델타 **0** — IFRS17 hole 은
> `validate_master_tables.coverage_holes`(→ 그쪽 QS)를 통해 오기 때문이다. 둘 다 열어야
> RED 이 나온다. 게이트 하나만 보고 "열었다"고 하면 안 된다.
>
> **아는 사람이 있었는데 정본을 안 고쳤다.** `validate_data_contract` 안의 두 검사(배당·CSM
> 연속성)는 주석에 "`_DISPLAY_QUARTERS` 는 2026.2Q 를 아직 포함하지 않는다"고 **적어 놓고
> 자기만 스코프를 비켜갔다.** 개별 우회가 재발 구조 자체였다.
>
> **실측(지평에 2026.2Q 넣기 전/후).**
> `validate_master_tables --no-build` SUMMARY: `coverage_hole 0PL→1PL` ·
> `qoq_warn 211Y→235Y` · `oci_vs_bs_aoci 13Y→14Y`. `plausibility`(dup/spike/cont/wfy/zamort)는
> 변화 0. `validate_data_contract` SUMMARY: `RED 0→1` (YELLOW 92 불변).
> 유일한 RED = **`MASTER_HOLE 흥국화재 2026.2Q`** — PL 항목 2/8/12/13/14 결측인데 직전
> 2026.1Q 는 다섯 항목 전부 정상 = 최신 분기 회귀. raw 는 디스크에 있고 라벨 빈도도 2026.1Q
> 와 같다 → refetch 아님, parser(ifrs17) 발주.
>
> **조치 = 파생.** `scripts/_quarter_horizon.py` 신설(하한 `2023.1Q` 고정, 상한은 마스터 5개의
> `공시분기` high-water mark). **여러 마스터의 max 를 쓰는 이유** — 한 마스터에서만 파생하면
> 그 마스터가 최신 분기를 통째로 빠뜨렸을 때 지평도 같이 줄어 결측이 안 보인다(자기참조 사각).
> `display_quarters()` 는 owner 스코프 규칙(연말 전부 + 2025.1Q 이후 전부)을 파생하며
> 종전 7개를 정확히 재현한다(회귀 가드 테스트 있음).
>
> **트립와이어 배선.** `tests/test_quarter_horizon.py` 신설 → `prepush_check.py` 오프라인
> 테스트 목록에 등록(배선 안 하면 또 honor-system). 변이시험 확인: QS 를 옛 리터럴로 되돌리면
> 2건 FAIL(`test_gate_horizon_includes_latest_quarter` + `test_no_gate_retypes_the_quarter_horizon`).
>
> **다른 게이트 census(AST, 주석·독스트링 제외).** 지평형 하드코딩은 위 3곳뿐. 나머지 게이트
> 8개는 데이터 파생(`validate_kics_disclosure` 의 `quarters = sorted(by_q)` 등)이고, 남은 분기
> 리터럴은 전부 **(회사, 분기) 예외 등재부**라 지평이 아니다. `validate_kics_disclosure.SPOT_QUARTER`
> 도 단일 spot-check 앵커. 재현: `scripts/_probes/probe_20260829_gate_horizon_audit.py`.
> 미조치(게이트 아님, 기록용): `scripts/_csm_goldmap.py` L20 · `scripts/_csm_status_matrix.py` L29
> 가 `QS = [q for q in QS if q != "2026.2Q"][:13]` 로 **2026.2Q 를 명시적으로 배제**한다 —
> 리포트 헬퍼라 push 를 막지 않지만, 그 리포트를 근거로 판단할 때는 최신 분기가 빠져 있다.
>
> **골든/지문.** `tests/fixtures/master_tables_golden.json` `--update` 재생성(위 SUMMARY 3칸
> 이동, exit_code 2 불변). `validate_golden_input_fingerprints.py` 는 **갱신 불요** — 빌더를
> 안 건드렸고 실행 결과 RED=0.

**(2026-08-29 b) 보험손익 leg-coverage 신설 — "등식이 없다"가 아니라 "등식이 결측을 만나면 도망갔다".**

> 처리: `inbox/validation/20260829T1500Z__orchestrator__MULTI__insurance_result_closure_missing.md`
> → `status: answered` (**발주 전제를 뒤집었다 — 오케스트레이터 재확인 필요**)
> 신규 발주: `inbox/parser/20260829T1700Z__validation__MULTI__pl_item1_leg_coverage.md`
> (`lane: ifrs17` · `route: reparse` · 40셀)
>
> **발주 전제는 틀렸다.** `1 = 2+13+14+15−16` 은 `PL_EQS` 밖 dual-form 블록에 **파일 최초
> 커밋(`135e6ff`)부터 있었고**, 그 실패 10건은 이미 `pl_bridge_baseline.json` 에 등재돼 있다.
> KB손해도 "item16 전 분기 None" 이 아니라 14분기 중 6분기만 None 이고, 2025.4Q 잔차는
> 1억이 아니라 **정확히 0.0**(억원 반올림 착시).
>
> **그런데 결론은 맞았다 — 원인이 달랐다.** 진짜 사각은 **결측 시 통째 SKIP**:
> `if bo is None or any(x is None for x in lob): pb_skip += 1` 이 356 버킷 중 **71(19.9%)**
> 을 무검사로 넘겼다. 게다가 coverage census 의 `key_items` 는
> `보험손익/생명장기손익/당기순이익` 셋뿐이라 **13(자동차)·14(일반) 결측은 세지도 않는다** —
> 두 검사가 같은 구멍을 공유했다.
>
> **실측(전 버킷 356).** SKIP 71 을 0-fill 로 재판정: **13 닫힘 / 40 깨짐 / 18 좌변없음**.
> 깨진 40건 잔차 median 43,415 · max 454,352 백만원, **합계 3.4조원이 어떤 룰의 시야에도
> 없었다**(2024+ 22건). 그중 **30건은 coverage census 도 구조적으로 못 잡는다.**
> 대표: **코리안리재보험이 13분기 내내 `item13` 없이 두 검사를 모두 통과**했고(형제 다리
> `item14` 는 정상 추출), 0-fill 로 재보면 2024+ 10분기가 전부 안 닫힌다(최대 4,105억).
>
> **조치 — 새 등식이 아니라 결측 처리 확장.** 등식을 한 벌 더 만들면 같은 식이 두 개가 된다.
> dual-form 의 결측 분기만 고쳐 **결측 LOB 다리를 0 으로 채워 판정**한다:
> 닫히면 PASS(그 다리는 정말 0), 깨지면 FAIL(잔차 = 미검사 금액의 하한).
> 라벨 `보험손익(leg-coverage)`. **결측을 SKIP 도 무조건 RED 도 아닌 "산수로 판정"으로 바꾼
> 것**이 요점이다 — 13건은 실제로 정확히 닫히므로(NH농협손해 12분기 ±1.0 이내) 무조건 RED 는
> 정당한 0 을 결함이라 부르는 두더지가 된다.
> `item1`(좌변) 결측 18건은 등식 성립 불가라 FAIL 로 안 올리되 `NOLHS` 로 건별 인쇄하고,
> 오늘 전건이 2023 분기이므로 **2024+ 가 뜨면 회귀 경고**를 찍는다.
>
> **적용 전 시뮬레이션 = 회귀 0건.** 오늘 검사받던 285 버킷 판정이 한 건도 안 바뀐다
> (`scripts/_probes/probe_20260829_item1_legcoverage_final.py` 가 old/new 대조).
> 0-fill 경로에 기타영업수익/기타사업비용 후보를 **추가하지 않았다**(masking 면 확대 방지,
> 실측상 불필요 — 13건 전부 기존 adj 로 닫힘).
>
> **게이트 실측.** `pl_bridge:3025P/13F/522S/0NEW` → `3038P/53F/469S/0NEW`.
> `exit=2` 는 전후 동일(기존 미종결 실패). 드러난 40건은 `pl_bridge_baseline.json` 에
> **건별** 등재(13→53, 기한 2026-10-31) — 통째 skip 이 아니고 F 로 계속 계상된다.
> 마스터 데이터는 한 셀도 안 건드렸다.
>
> **훅 배선 확인.** `prepush_check.py` 는 `validate_master_tables.py` 를 직접 안 부른다 —
> 강제점은 `tests/test_master_tables_golden.py`(SUMMARY+exit 박제)이고 그것은 훅 `fast`
> 묶음 **L167 에 실제로 있다**. `tests/test_identity_registry.py` 도 **L179 에 있다**(허용오차를
> 몰래 넓히면 `tol_from` 대조에서 막힌다). `test_rule_coverage_manifest.py` 는 K-ICS 전용이라
> PL 축이 없어 손대지 않았다. 지문 게이트는 빌더 전용이라 `--update` 불요(`RED=0 → clear` 확인).
>
> **남은 사각(별도 판단 요망).** `validate_master_tables.QS` 가 `2026.1Q` 에서 끝나 **2026.2Q
> 24버킷**을 `QS` 기반 검사(coverage census · qoq_scan · net_quarterly)가 통째로 안 본다.
> PL_BRIDGE 는 `pl.items()` 를 직접 돌아 무관(그래서 코리안리 2026.2Q 도 잡혔다). `QS` 확장은
> 여러 룰 판정을 동시에 움직여 전 버킷 재시뮬이 필요하므로 이 티켓에서 손대지 않았다.

**(2026-08-29) 골든 입력지문 게이트 배선 완료 — 빌더 재실행 골든 6개 중 훅이 돌리던 것은 1개뿐이었다.**

> 처리: `inbox/validation/20260829T0300Z__orchestrator__MULTI__golden_input_fingerprint_gate.md`
> → `status: answered` (오케스트레이터 확인 필요 — 운영 계약 1건 전파 + 무관 RED 1건 보고)
>
> **사고 배경.** `tests/test_ifrs17_bs_golden.py` 는 빌더를 통째로 재실행해 **실측 492·514초**라
> 훅 예산(~5분)을 넘어 오프라인 묶음에서 빠져 있었다. 그 사각으로 2026-08-26 삼성생명 OFS
> 캐시 정정(8c1666b)이 BS 마스터에 반영 안 된 채 **이틀간 미검출**됐다. `CLAUDE.md` 골든 표의
> "~2분" 추정이 4배 이상 틀렸던 것이 그 제외 결정의 근거였다 —
> `prepush_check.py` 주석에도 같은 오추정이 남아 있어 실측치로 정정했다.
>
> **신설.** `scripts/validate_golden_input_fingerprints.py` — 빌더를 **안 돌리고**
> 입력·코드·산출 3축(+fixture) 지문만 대조해 "마스터가 자기 입력보다 낡았는가"를 판정.
> in-process **3.0~3.15초**. 입력 경로는 추정이 아니라 **런타임 트레이스**로 확정했고
> (`scripts/_probes/probe_20260829_trace_builder_reads.py`, 박제:
> `tests/fixtures/builder_read_traces/`), `tests/test_golden_input_fingerprint.py` 가
> 선언이 관측치를 덮는지 매 push 마다 대조한다. 그 대조가 `src/__init__.py` 와
> `data/ifrs17/table_scoring_keywords.yaml`(import 두 단계 아래 lru_cache) 누락을 실제로 잡았다.
> **무거운 골든은 그대로 둔다 — 지문은 대체가 아니라 층이다.**
>
> **이번에 발견한 구멍.** 지문 게이트는 훅에 걸렸는데 그 **매니페스트 테스트가 오프라인
> 묶음에 없었다.** 게이트만 걸고 매니페스트를 안 돌리면 SPECS 를 좁히는 변경이 무저항
> 통과한다 — "배선했다 ≠ 강제된다"의 재발이다. 묶음에 추가하고,
> `test_this_manifest_itself_runs_in_the_push_hook` 으로 자기 등재를 자기가 검사하게 했다.
>
> **재현.** `data/dart/extracted/` 에 스크래치 파일 1개를 넣어 입력을 현실측으로 흔들었더니
> `git push --dry-run` 이 `골든 입력지문=FAIL` → `PUSH BLOCKED — exit=2` → `error: failed to
> push some refs` 로 막혔다(448초). 삭제 후 `RED=0 → clear`.
>
> **운영 계약(두 파서 레인에 전파 요망).** 마스터를 정당하게 재빌드하면 골든 `--update` 뒤에
> `validate_golden_input_fingerprints.py --update` 도 같이 돌려야 한다. 실제로 이번 세션에
> ifrs17 레인의 동시 재빌드로 `[pl_breakdown] FIXTURE_MOVED` RED 이 났다(정상 동작).
>
> **커밋 `0ebb0ca`** (14 files, +5,126/-4).
>
> **배선 직후 야생에서 첫 건을 잡았다.** 커밋 직후 재실행에서
> `[viz_ifrs17_panels] CODE_MOVED + FIXTURE_MOVED` RED 2건 — 파서 레인이
> `scripts/viz_build_ifrs17_panels.py` 를 고치는 중이다(`inbox/parser/20260829T0200Z...
> csm_amort_asof_placeholder`). **빌더 코드가 움직이면 입력이 그대로여도 마스터는 낡는다** —
> 종전에는 이 축을 보는 것이 8분짜리 골든뿐이라 훅에서 안 돌았다. 남의 in-flight 변경을
> 내가 `--update` 로 축복하면 그게 false-green 이라 **RED 을 일부러 남겨 뒀다.**
>
> **미해결(내 작업과 무관) 2건 — 둘 다 push 를 계속 막는다.**
> ① `[PL_breakdown] PL_YTD_COLLAPSE_TO_ZERO 에이비엘생명보험 2024.4Q`
>   (`inbox/parser/20260828T2100Z...KR0070` 진행 중)
> ② 위 `viz_ifrs17_panels` 지문 RED (그 빌더 변경을 랜딩하는 쪽이 골든 통과 후 지문 `--update`)

**(2026-08-26 b) 🔴 prepush exit 2 · gate RED=1 YELLOW=92 — BLOCKED, 그리고 이게 맞는 상태다.**
**오케스트레이터가 요청한 documented exception 을 등재하지 않았다. 등재했으면 거짓 면제였다.**

> 처리: `inbox/validation/20260826T2000Z__orchestrator__MULTI__pl_amort_crosscheck_blindspot.md`
> → `status: answered` (원 sender 재확인 필요 — 판정을 뒤집었다)
> 신규 발주: `inbox/parser/20260826T2200Z__validation__KR0049_2023.4Q__axa_tier2_header_empty.md`
> (`lane: ifrs17` · `route: reparse`)
>
> ### ① 면제 요청을 반려했다 — "어느 DART 문서에도 없다" 가 틀렸다
>
> 악사손해 2023.4Q `PL_CSM_AMORT_VS_WATERFALL` RED 은 **진짜 추출불가가 아니다.** 값은 이미
> 받아 놓은 감사보고서 첨부 안에 있다 — `20240402002008_00760.xml` 의
> `'(5) 보험손익 상세내역'` 표, `당기손익으로 인식한 보험계약마진 금액 · 장기 = 22,272,512천원`
> = **222.7억** = 게이트가 인쇄하던 그 워터폴 상각액. 2024.4Q 는 같은 표(`'(6) ...'`)로 추출에
> **성공**한다. 선행 티켓들이 판별식으로 쓴 `계약유형별` 은 **양쪽 다 0회**라 애초에 아무것도
> 증명하지 않는 키워드였다(성공하는 2024 필링에도 0회).
>
> 근본원인까지 특정 — `companies.py::extract_tier2_axa` 가 `for hr in note.header:` 로 도는데
> 2023 필링은 `t.header == []` 이고 컬럼 헤더행이 `t.rows[0]` 안에 들어온다 → `col` 이 None →
> `return {}`. 2차 결함: 섹션 라벨 `재보험수익`/`재보험비용`(2023) vs `_AXA_SEC` 의
> `출재보험수익`/`출재보험비용`(2024). parser 티켓에 기대값 13셀 + 정합식 3개를 붙여 발주.
>
> **교훈: 키워드 0회는 원천 부재의 근거가 아니다.** 성공 사례에서 판별기를 먼저 교정하고 세라.
>
> ### ② 사각 12건 — 커버리지 룰 `3z-b` 신설
>
> 룰 3z 가 `for (co,q) in env.pl` 이라 **PL 버킷이 통째로 없으면 방문조차 못 해 완전 침묵**했다.
> `env.wf` 쪽에서도 한 번 더 도는 census 를 배선(`check_cross_source` 3z 바로 뒤). 신규 결손은
> RED, 기존 12건은 `data/_gold/pl_amort_coverage_baseline.json` 에 **건별 열거 + 워터폴 상각
> 박제**로 비차단. 버킷이 생기면 `_INERT`, 박제가 흔들리면 `_DRIFT` RED — 매 실행 재검산한다.
> 전 버킷 시뮬레이션 + 변이 6종 ALL PASS(`probe_20260826_coverage_rule_simulation.py`),
> selftest 57/57(종전 55, `L3`/`L4` 신설 · `M1` 픽스처 격리 보정).
>
> **삼성화재 2023.1Q(워터폴 상각 3,760.4억)는 진짜 구멍으로 확정**했다 — raw 에
> `'(10) … 주요 보종별 보험수익 및 재보험비용의 내역 · 1) 제74(당)기 1분기'` 의
> `보험계약마진 상각 376,038백만원` 이 있다. 나머지 11건은 **판정 보류(`UNADJUDICATED`)** —
> 내 노트 판별기가 대조군 7건 중 5건 위음성이라 "원천에 없다"고 말할 근거가 없다.
>
> ### 다음 행동
>
> parser(ifrs17)가 `extract_tier2_axa` 헤더 폴백을 넣고 PL 골든을 `--update` 로 재생성하면
> RED 이 0 이 된다. 그 뒤 재검증 요청할 것. **그 전에는 push 하면 안 된다.**

## Status (이전 라운드)

**(2026-08-26 a, answered 4건 재확인) 🟢 4건 전부 종결(resolved) · prepush exit 0 ·
RED=0. 마스터 JSON 은 한 셀도 안 고쳤다. 고친 것은 내 소유 게이트 2곳 + 등재부 2종이다.**

> 종결: `inbox/_resolved/20260825T1520Z`(CSM 상각 항등식) · `20260825T1120Z`(PL bridge) ·
> `20260825T0800Z`(단위판별) · `20260825T1415Z`(IR 기준 판정, `escalate` 해제)
> 신규 발주: `inbox/parser/20260826T0500Z`(별도 복원 잔여 3건)
>
> ### 이번에 잡은 것 — 게이트 두 곳이 자기가 잡으라는 것을 못 잡고 있었다
>
> **① IR 교차검증 축은 발화하는데 눈이 멀어 있었다.** 파싱본 6개가 들어와
> `csm_steps_dart_vs_ir` 이 36 step-pair 를 실제로 대조하기 시작했다(종전 "IR JSON 미납품,
> SKIP"). 실측 잔차는 전건 |Δ| ≤ **0.055억**인데 허용오차는 `max(5%, 100억)` — **1,700배**
> 넓었다. 그래서 커밋 `8a3b930` 의 연결 누출(6항목 Δ 69.6~1,043.9억)을 **0/6 으로 놓친다.**
> `max(0.5%, 1.0억)` 로 조였다(live RED 0 · leak 6/6 검출 · worst Δ/tol 0.0188).
> `IR_STEP_TOL_REL`/`IR_STEP_TOL_ABS_EOK` 를 모듈 상수로 빼고 `test_identity_registry.py`
> `tol_from` 에 배선 — 앞으로 몰래 넓히면 테스트가 막는다.
>
> **② PL 생명장기 등식이 발행사 표의 세 번째 다리를 안 보고 있었다.** 교보라플·BNP카디프
> 3건은 데이터가 아니라 룰의 갭이었다. raw(교보라플 `20250328001411_00760.xml`, 단위 원):
> Ⅰ.보험손익 = 보험영업수익 − 보험서비스비용이고 그 비용 안에 **(3)기타사업비용**이 원수·
> 재보험과 나란히 들어 있다 → `item2 = item3+item8−item16` 이 **원 단위까지** 닫힌다.
> `PL_EQ_ADJ` 로 adj 후보를 주고, 전 버킷 시뮬레이션(3 닫힘 · **파손 0** · 잔존 0) 후 반영.
>
> **③ 원장이 두 시간 만에 화석이 됐다.** parser 답변이 박제한 `pinned=22 stale=0` 은
> `b2293c8` 시점 값이고, 같은 레인의 `8c1666b`(PL 별도 정정)가 **11건을 저절로 닫았다**
> — 실측 `pass=335 pinned=11 stale=11`. FIXED 11줄 삭제 + 남은 삼성생명 5분기 note 에
> "고칠 대상은 PL 이다" 명시. YELLOW 96 → 85.
>
> ### 재확인에서 갈라진 판정 (전부 raw 로 직접 잼)
>
> - **삼성생명·신한라이프 84셀 별도 복원 = 확인.** 3-way 대조(8a3b930^ / 8a3b930 / 현재):
>   값 84셀 · 2개사, 한화생명·현대해상 0셀.
> - **교보생명 미복원 = 옳다. 단 사유가 틀렸다.** parser 는 "연결/별도 축이 아니라 당기/전기
>   버그" 라고 했는데 raw 는 정확히 연결/별도다 — `20230515002764.xml` 에서 버린 105,807 은
>   **연결재무제표 주석**(line 19282), 채택한 104,567 은 **재무제표 주석=별도**(line 38283).
>   이 회사는 문서 순서가 연결 먼저라 구코드가 연결을 집고 있었고, **코드가 아니라 gold
>   override 로만** 고쳐졌다 → 픽커는 여전히 이 회사에서 연결을 선호한다.
> - **코리안리 판정불가 = 맞다.** PL 과 맞는 값(70,611 / 92,311)이 연결·별도 **양쪽 절에 같은
>   숫자로** 인쇄돼 있다(재보험사라 이 줄의 연결효과 0). basis 로는 못 가른다.
> - **gold `set` 30셀 제거는 반대.** `csm_waterfall_master_diag.json` 이 **2026-08-17** 로
>   stale 해서 옛 1000배 값(AIG 928,075.0 등)을 그대로 들고 있다. 지금 지우면 다음
>   `build_csm()` 에서 그대로 되돌아간다. diag 재생성(owner 승인) → 삭제 → 산출 동일 확인 순서.
>
> ### 아직 확인 못 한 것 (후속 티켓 `20260826T0500Z`)
>
> ① 삼성생명 item3/item4 **10셀**이 복원 전 값과 다르다(이자부리 최대 +70.1억). item3+item4 가
> 정확히 상쇄돼 항등식은 안 깨지지만 **어느 원천으로도 확인이 안 된다**(워터폴이 3블록 합이라
> 단일 인쇄값 대조 불가, IR 은 그 5분기를 안 덮는다). parser 답변의 "8a3b930^ 와 일치" 는 틀렸다.
> ② 삼성생명 PL **5분기가 아직 연결**(2026.2Q 는 IR 로 확증) — 반기 필링 전부 + FY2024 분기.
> ③ diag stale.
>
> ### 게이트 (2026-08-26 재확인 후)
>
> ```
> validate_master_tables --no-build : pl_bridge 2518P/13F/317S/0NEW · csm_amort_identity 335P/11PIN/0F/0S(stale 0)
> validate_data_contract            : RED=0 YELLOW=85 · DART↔IR 36 step-pairs
> prepush_check.py                  : exit 0 (gate-clear, offline tests 230 passed/1 skipped)
> ```

