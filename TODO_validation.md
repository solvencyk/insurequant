# Insurequant Validation TODO (Stage 3)

> Last updated: 2026-09-20 (경영공시 PL 백필 ⑤ 병합 후속 — **`_check_pl_bridge`(leg-coverage 2e · ZERO_LEGS 2b) 소스인식**; 12차가 `coverage_holes` 만 바꾸고 이 두 축을 빠뜨려 `pl_new=153` 으로 push 가 막혀 있었다. 같은 resolver(`pl_cell_source_ids`) 재사용 · 가드는 '원천이 정말 안 실은 모양'으로 좁힘 · SKIP 을 `src_na(DISCLOSURE)` 로 세어 인쇄. `pl_new` 153→0 · `zero_legs` 97→9(DART 9 보존) · 거짓 PASS 2건도 SKIP 으로 닫힘 · selftest 69→75(killer 변이 7종, 6/6 사망) · 골든은 2×2 귀속 대조 후 `--update`. 마스터·등재부 무수정; 직전 경영공시 PL 백필 **병합 선행조건 ②③④ 배선** — 계보 등재 4건 + `SOURCE_ID_LINEAGE_MISMATCH` 를 capsec guard 밖으로(비-capsec 계보가 그동안 무검사였다: `kics_rate_sensitivity` 138셀 판정 None) · PL provenance 첫 검증(호출처가 0 이었다 → published 731셀) · `coverage_holes` 기대그리드를 셀 계보별로(병합 후 real hole 118→6, 오늘은 바이트 동일이라 골든 불변) · `CONCEPT_REGISTRY` 에 `pl_disclosure_vs_dart` 등재 + **리더**(allowlist 강제). `DERIVED` 는 계보 미등재(널 경로 라벨 = 보편적 탈출구) 대신 게이트 재계산 기반 좁은 면제. selftest 57→69(BS_KICS 2축 잔여 해소 포함), 12건 전부 killer 변이로 반증. 마스터 미수정; 직전 항목4/12/13 미러링 **재감사 정정** — "오염 170셀" 은 과다계상, 실제는 `item13` 55셀뿐이고 `item4`·`item12` 114셀은 정상. 1차 발주의 "170셀 삭제" 를 실행했으면 정상 셀 114개가 지워졌다. 버킷 판정을 셀 판정으로 승격시킨 것이 원인 — Δ의 귀착 항목을 안 쟀다; 직전 경영공시 출처 PL 백필 **계약 판정** — 항목 3개·회사 1개 제외 + 병합 순서 확정; 지금 규격대로면 census RED 0→80; 새 사각 2종 적발: PL provenance 사이드카가 죽어 있음(638셀 source_file 0) · "자식 present·부모 None" 29버킷 무검사; 직전 UH-25 게이트 축 해소 — `JP_ESR_UNVERIFIED_VALUE` 신설: 값 검증 두 축이 동시에 침묵하는 상태를 YELLOW 로 세고 push 묶음이 막는다; 직전 UH-23 정식 해소 — 한정어 정본 §3 표 ↔ `ADJUSTED_QUALIFIERS` 양방향 대조 배선 + TODO 과장 정정; 직전 jp `JP_ESR_ADJUSTED_FIGURE` 배선 — 조정치 축, UH-21 해소 → PM-2026-09-13 `closed`; 직전 jp `JP_ESR_NOT_IN_SOURCE` 배선; 직전 push 범위 판정을 훅에 구현 — CLAUDE.md §5 가 문서로만 있던 규칙을 코드로; 직전 jp false-green 포스트모템·UH-18 등재; 직전 2026-09-02 MASTER_XLSX_* 축 신설 — 마스터 JSON ↔ 마스터 xlsx 13시트 전수 대조를 CHECK 8 로 배선) · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Changelog: docs/changelog_validation.md

Session start: read this file + `claude-agent-validation.md` + domain refs (`docs/domains/claude-agent-{kics,ifrs17}.md`). English where Korean encoding is fragile (`CLAUDE.md` rule).

## Status

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
