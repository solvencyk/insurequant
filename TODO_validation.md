# Insurequant Validation TODO (Stage 3)

> Last updated: 2026-08-30 (public_exports 축 배선 + wiring 테스트의 <script src> 사각 해소) · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Changelog: docs/changelog_validation.md

Session start: read this file + `claude-agent-validation.md` + domain refs (`docs/domains/claude-agent-{kics,ifrs17}.md`). English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

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
