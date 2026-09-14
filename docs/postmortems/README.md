# 사고 포스트모템 (blameless) — 게이트 룰로 종결

> owner 발주 `inbox/validation/20260721T0233Z__owner__MULTI__adopt_incident_postmortem_practice.md`
> 운영 스킬: `.claude/skills/incident-postmortem/SKILL.md` · 스테이지 프롬프트 링크: `docs/agents/claude-agent-validation.md` §5.1

## 왜 이 관행인가

이 저장소의 사고는 대부분 이 경로를 탔다:

> 사고 발생 → 메모·changelog 기록 → **게이트 룰로는 안 굳음** → 다른 형태로 재발

기록만으로는 재발을 못 막는다. **포스트모템은 "어떤 룰이 어디에 배선됐다"로 종결돼야 한다.**
비난 없음(blameless) — 사람이 아니라 **게이트의 사각**을 원인으로 본다.

## 종결 조건 (5칸 — 하나라도 비면 close 불가)

| # | 칸 | 반드시 담을 것 |
|---|---|---|
| 1 | **무엇이 통과했나** | 어떤 게이트가 **왜** 못 잡았나 (통과 당시 RED 수, false-green이면 그 이유) |
| 2 | **어떤 룰이었으면 잡았나** | 추상적 교훈 금지. **구체 룰 정의**(입력 항목·판정식·임계값·severity) |
| 3 | **그 룰이 지금 배선됐나** | 함수명 + 파일(`validate_kics_disclosure.py` / `validate_data_contract.py`) + **scope(display-only / 전분기)** + exit-code 반영 여부 |
| 4 | **documented exception** | 있으면 근거 + **등재 위치(registry 변수명·파일)**. 없으면 "없음" 명시 |
| 5 | **미배선 잔여 + 후속 티켓** | 2번 룰 중 아직 안 굳은 부분 + inbox 티켓 파일명. 없으면 "없음" |

**3번이 "아니오"인데 5번이 비어 있으면 그 포스트모템은 미완이다.** 그 상태가 바로 재발 경로다.

## 두 게이트의 차이 (3번 칸을 채울 때 반드시 구분)

> ⚠️ **아래 표는 2026-08-21 에 바뀌었다.** 그전까지 `prepush_check.py` 는
> `validate_data_contract.py` **하나만** 불렀고, 그래서 K-ICS 게이트·마스터테이블 게이트에만
> 배선한 룰은 push 를 못 막았다(그 사실이 UH-1 이었다). 지금은 훅이 여러 게이트를 부른다 —
> **2026-08-21 이전 포스트모템의 "K-ICS 게이트에만 배선 = push 못 막음" 서술은 stale 로 읽어라.**

| 게이트 | 파일 | 언제 도나 | 무엇을 막나 |
|---|---|---|---|
| K-ICS 게이트 | `scripts/validate_kics_disclosure.py` | **훅 단계 1b** (2026-08-21부터) | ✅ **push 차단** (`n_kics` → `blocked`) |
| 도메인 게이트 7종 | `validate_{csm_continuity,kics_rate_sensitivity,nb_csm_multiple,csm_waterfall,live_artifacts,disclosure_freshness,stale_quarter_tables}.py` | **훅 단계 1c** (2026-08-21부터) | ✅ **push 차단** (`n_dom` → `blocked`) |
| 마스터테이블 게이트 | `scripts/validate_master_tables.py` | 수동 실행(**`--no-build` 필수**) | ❌ 자기 exit code(2)만. **push를 자동으로 막지 않는다** (골든 `tests/test_master_tables_golden.py` 는 훅 묶음에 있다) |
| 일반 이상치 발견 | `scripts/scan_generic_anomalies.py` | 수동 (2026-08-25 게이트 밖으로 분리) | ❌ YELLOW 전용 — 원래 막은 적 없다 |
| **push 게이트** | `scripts/validate_data_contract.py` (← `prepush_check.py` 단계 1) | 훅이 push 직전 | ✅ **실제 push 차단.** display 7분기 scope |

⚠️ **여전히 "배선했다" 와 "실제로 push 를 막는다" 는 다른 말이다.** 바뀐 것은 답이지 확인
의무가 아니다 — 3번 칸을 채울 때 룰을 어느 스크립트에 넣었는지만 적지 말고 **그 스크립트가
`prepush_check.py` 에서 실제로 호출되고 그 exit code 가 `blocked` 계산에 들어가는지**를
소스에서 확인해라. `tests/test_push_gate_wiring.py` 가 그 선언을 매니페스트로 강제한다
(새 `validate_*.py` 나 새 `check_*` 를 추가하면 선언 없이는 테스트가 막는다).

> **실제 발화 사례 (2026-08-15)**: CSM 연속성(`CONT`)이 `validate_master_tables.py` 에만 있어서,
> 파서가 5사 기초를 override 해 FY 경계를 새로 깬 뒤에도 push 경로는 초록이었다. 게다가 그
> 게이트의 골든이 `1cont → 6cont` 로 재생성되며 위반을 흡수해 **테스트까지 통과**했다.
> owner 지시로 `validate_data_contract.py` 에 `CSM_CONTINUITY_FY_BOUNDARY` 신설(RED, 면제
> 없음, 분기목록 하드코딩 대신 FY 도출 → 2026.2Q 자동 편입). **골든 `--update` 는 의도된 변경
> 기록용이지 새 위반 흡수용이 아니다** — 카운트가 늘었는데 초록이면 그건 굳은 게 아니라 덮인 것.

## 파일 규칙

`docs/postmortems/PM-<YYYY-MM-DD>_<slug>.md` — 템플릿은 [`_TEMPLATE.md`](_TEMPLATE.md).

## 색인

| ID | 사고 | 룰 배선 | 상태 |
|---|---|---|---|
| [PM-2026-06-16](PM-2026-06-16_two_month_glitch.md) | 두 달 글리치 — 맞는 산수·틀린 소스 false-green | ✅ push 게이트(data-contract 5 CHECK) | `closed` (UH-3·UH-4 **모두 해소** 2026-08-03) |
| [PM-2026-07-07](PM-2026-07-07_after_capture_blindspot.md) | 경과조치 **적용후** 전면 미검증 | ✅ 양쪽 (2026-07-21 lift) | `closed` |
| [PM-2026-07-08](PM-2026-07-08_v17_mirror_fill.md) | V17 가짜복사(적용후=round(적용전)) | ✅ 양쪽 (2026-07-21 lift) | `closed` |
| [PM-2026-07-15](PM-2026-07-15_post_parent_census.md) | 적용후 요구자본 **부모** 결측 → 라이브 공란 | ✅ 양쪽(K-ICS + push) | `closed` |
| [PM-2026-07-30](PM-2026-07-30_kr0075_csm_100x_unit.md) | KR0075 CSM_waterfall 100x 단위과대 — 절대값 cap은 있었으나 상대규모 검사축 없음 | ✅ push 게이트 `CSM_WATERFALL_PLAUSIBILITY` (2026-08-03 배선, 초기 YELLOW) | `closed` (UH-6 해소) |
| [PM-2026-08-03](PM-2026-08-03_capsec_provenance_label_mismatch.md) | 자본성증권 provenance **라벨 거짓**(DART 파일에 `FSC_BONDS`)이 통과 — 게이트가 틀린 주장을 "검증" | ✅ push 게이트 `SOURCE_ID_LINEAGE_MISMATCH` + 계보별 effective 증거 + 사이드카 도출 emitter | `closed` (잔여 UH-7) |
| [PM-2026-08-03 §6](PM-2026-08-03_capsec_provenance_label_mismatch.md#6-후속--같은-사건의-두-번째-얼굴-커버리지-census-2026-08-03-b) | **같은 사건의 두 번째 얼굴** — 소스가 통째로 비어도 통과(커버리지 후퇴). DART 전환으로 raw 없는 회사의 채권이 사라져 비율이 낙관 방향으로 틀림(KR0076 94→152%) | ✅ push 게이트 `CAPSEC_COVERAGE_REGRESSION` + `CAPSEC_SOURCE_UNRESOLVED` (+YELLOW 그물 2종) | `closed` (데이터 잔여 RED 15 = 의도된 push 차단, parser·downloader 발주) |
| [PM-2026-08-24](PM-2026-08-24_i47_scope_misread.md) | 룰의 `item47` 스코프 가정이 틀려 만든 잔차를 **발행사 모순으로 오진** — owner 판단 면제까지 갔다(false-green 의 쌍둥이: 룰의 결함이 발행사의 결함으로 세탁된다) | ✅ 공유 룰엔진 `_tier2_i47_scope_map` + `_tier2_branch(scope=)` → **두 게이트 동시** + 회귀시험 3종 | `closed` (잔여 UH-9) |
| [PM-2026-08-24 (b)](PM-2026-08-24_absence_exemption_blinded_axis.md) | **부재형 면제가 축을 통째로 눈감겼다** — 하나생명 2024.4Q 적용후 4셀이 stale/결측인데 어떤 룰도 그 셀을 순회하지 않았다. 실측: 4셀을 정정해도 게이트 출력이 **바이트 동일** | ✅ 면제를 **셀 단위 부재 박제**로 재설계(`_absence_pin_census` `EXEMPTION_ABSENCE_PIN_PARTIAL_FILL`) + 원장↔코드 박제 대조(`_pin_ledger_agreement_findings`) + 마커 **행 귀속**(`present_rows`) → **두 게이트 동시**(push 위임 1b(vi-b)) + 회귀 34 + selftest N8~N10 | `closed` (잔여 UH-10·UH-11·UH-12) |

| [PM-2026-08-25](PM-2026-08-25_gate_read_the_wrong_file.md) | **게이트가 배포본이 아닌 파일을 검사했다 (불변식 1번 위반)** — 라이브 HTML 이 fetch 하는 .json 16개 중 **6개를 어떤 검사기도 안 읽었고**, `validate_master_tables` 의 PL 축은 파서 중간산출물을 읽어 배포본 1,307셀이 항등식 미검사 + `HOLE-PL` 24건이 24/24 phantom. tier1/tier2 는 배포본을 **등록만** 하고 값은 상류를 읽어 **라이브 4사가 0% 로 오표시** | ✅ `scripts/validate_live_artifacts.py` 신설(prepush 1c) + PL 축 배포본 재조준 + `tests/test_push_gate_wiring.py::LIVE_ARTIFACT_READERS`·`DEPLOYED_VS_UPSTREAM` 매트릭스(변이 5/5 발화) + baseline 2종(pl_bridge 26 · live_artifact 1,086) | `closed` (잔여 UH-13·UH-14) |

| [PM-2026-09-02](PM-2026-09-02_master_xlsx_stale_unchecked.md) | **마스터 JSON 의 하류 사본이 둘인데 검사기는 하나였다** — `PUBLIC_EXPORT_*` 는 `public_exports/` 스냅샷만 보고 **마스터 ↔ `insurequant_master_tables.xlsx` 를 대조하는 룰이 0건**. owner 라이브 QA 로 `자본비율전망` 이 2026.1Q 베이스라인에 멈춘 것이 발견됐고(38개사 2090칸 중 1219칸), 전수 재측정에서 `K-ICS공시` 도 stale(33셀·121행). 모든 게이트가 RED=0 이었다 | ✅ push 게이트 `check_master_xlsx` (CHECK 8, `scripts/check_master_xlsx_drift.py` 13시트 전수) + 매니페스트·변이시험 18종. **되돌려 재본 실측**: 수정 전 워크북에서 RED=5(두 수정 커밋의 자체 기록과 셀 단위 일치) | `closed` (잔여 UH-15·UH-16·UH-17) |
| [PM-2026-09-13](PM-2026-09-13_jp_secondary_source_and_dead_url.md) | **jp 레인이 2차보도·조정치를 헤드라인으로 올렸고 출처 URL 은 무관한 문서였다** — 東京海上HD 238(원문 268) · かんぽ 220(「大量解約リスクを除いた場合」 조정치, 원문 181) · 明治安田生命 208.0(원문 208.7) · MS&AD 출처가 합병 보도자료(ESR 미수록). jp 빌더 self-check(범위·형식·합계)는 **전부 통과** — census 안에서만 닫히는 자기참조 | ✅ **차단 룰 5종 전부 배선** (2026-09-13 UH-18·UH-19 해소). `build_jesr_page_json.py::source_gate_check` — `JP_SOURCE_EXPIRING_HOST` · `JP_SOURCE_URL_DEAD` · **`JP_ESR_NOT_IN_SOURCE`**(수집기 `check_esr_in_source.py` → 증거 `esr_in_source_health.json`, 키는 (url, esr_pct)) · `JP_SOURCE_EVIDENCE_STALE` · `JP_SOURCE_EVIDENCE_INCOMPLETE` → **exit 1 실증** · **`JP_ESR_ADJUSTED_FIGURE`**(조정치 축 — 화면값의 라벨동반 조각이 전부 한정어 + 같은 문서에 한정어 없는 대안값이 있다. YELLOW 지만 배포본 증거에 발화가 남으면 push 묶음이 exit 1). 회귀 83+26 · 이빨 10/10 | `closed` (2026-09-13, UH-18·UH-19·**UH-21** 해소 / UH-23 은 2026-09-14 해소 / **UH-22 만 잔여**) |

## ✅ 2026-07-21 해소 (owner 승인)

| ID | 조치 |
|---|---|
| **UH-1** | 적용후 검증 7종을 `validate_data_contract.py` `check_census` **1b(iv)** 로 lift (display 7분기 scope). 6종 RED + `_ratio_series_spikes`만 YELLOW(휴리스틱이라 단독 차단 금지). **주입 테스트로 방출 경로 검증**: display-scope를 2023.1~3Q로 임시 확장 시 baseline RED 0 → lifted RED 4건 |
| **UH-2** | push 게이트 체인 3종(`validate_data_contract.py`·`prepush_check.py`·`triage_anomaly_candidates.py`) **git 등재**. gitignore가 아니라 단순 미추가였음(scripts/ 163개는 이미 tracked) |

## 2026-07-21 (2차) — UH-4 해소 · UH-3 부분강화 · UH-5 선행조건 확정

| ID | 조치 |
|---|---|
| **UH-4 ✅ 해소** | `scripts/_data_contract_selftest.py` 신설 — `Env(inject=…)` 합성데이터 mutation suite **14/14 PASS**. 기존 spec §5 회귀(census·impossible-0·stale as-of·donut·concept-guard·tier2 identity) + **1b(iv) lift 5종(F1~F5) 회귀 보호**. **이빨 검증**: 룰을 죽이면(`_item12_equals_item1`·`_post_transition_parent_census` monkeypatch) 해당 케이스가 미검출→FAIL 처리됨을 확인 |
| **UH-3 ⚠️ 부분강화** | 종전 `notes`에만 적혀 **집계도 안 되고 조용히 통과**하던 sidecar 부재를 집계되는 **YELLOW `MISSING_PROVENANCE_SIDECAR`** 로 승격(현 4건: sensitivity_heatmap·forward_capital·tier1/tier2_utilization). **RED 전환은 발행 후** — 지금 RED로 두면 미발행 마스터가 전부 red-out돼 push가 영구 차단. 발행 발주: publishing `20260721T0530Z…provenance_sidecar_emission` · parser(ifrs17) `20260721T0530Z…sensitivity_heatmap_provenance` |

## 🔴 아직 룰로 안 굳은 것

| ID | 내용 | 상태 |
|---|---|---|
| **UH-3 ✅ 해소 (2026-08-03 c)** | **end-state 도달 = no-sidecar RED 전환.** 4종 사이드카 전부 발행 완료(publishing `faa34cd` → forward_capital·tier1·tier2 / parser `scripts/emit_sensitivity_provenance.py` → `data/dart/viz/sensitivity_heatmap_provenance.json`) → 라이브 `MISSING_PROVENANCE_SIDECAR` YELLOW **1→0** 확인 후 `_fallback_note`를 **YELLOW→RED** 승격(`validate_data_contract.check_as_of`). 이제 사이드카 부재 = "미발행 정상"이 아니라 **발행 경로가 씻겨나간 신호**이므로 push 차단. Phase-1 추론 블록은 진단용으로 존치(그 분기가 이미 RED라 통과 경로가 아니다). 회귀 케이스 **C3** + 이빨 검증(YELLOW로 강등하면 미검출 FAIL). **전환 후 라이브 CHECK2 RED=0 유지** = 오탐 0 |
| **UH-8** | `kics_rate_sensitivity`는 `MASTER_FILES`에 있으나 **CHECK 2 provenance 검사 대상이 아니다**(사이드카 없음·as-of 축 미검사). 다른 검증기(`data/_derived/kics_rate_sensitivity_validation.json`)가 값은 보지만 **소스 신선도는 아무도 안 본다** — UH-3가 닫은 것과 같은 부류의 잔여 축 | 신규 — 발주 `inbox/parser/20260803T0520Z__validation__MULTI__rate_sensitivity_provenance_sidecar.md` (lane: kics). 사이드카 발행 후 CHECK 2에 배선 |
| **UH-6 ✅ 해소 (2026-08-03)** | `CSM_WATERFALL_PLAUSIBILITY` 배선 완료 — `_csm_magnitude_implausible()` → `validate_data_contract.check_census` **1d**. 판정식 `기말CSM ÷ item1지급여력금액`(회사별 최신 분기, KR코드 조인) > `median × 10`. **임계값은 parser 초안 ×20에서 ×10으로 조정** — 초안 근거(KR0075 r=153)는 정정 전 값이고 정정 후 라이브 36사 분포는 median 0.563 / 최대 1.530(=median의 2.7배)이라 ×20(r>11.3)은 중간규모사의 ×10 단위오류를 놓친다. severity **초기 YELLOW**(관찰 1~2 릴리스 후 RED, UH-3 선례). 오탐 억제 4종(K-ICS 미공시사 skip·표본<10 skip·상한만·지급여력금액≤0 skip). 회귀 케이스 `_data_contract_selftest.py` **G2** + 이빨 검증(룰 죽이면 FAIL) |
| **UH-7** | `kics_forward_capital.json`의 셀 키가 `baseline_2025_4Q`인데 실제 데이터는 `BASELINE_QUARTER="2026.1Q"` 산출물 — **값은 맞고 키 이름만 거짓**, as-of 정본 판단을 흐린다(`forward_capital_simulation.py:442`). HTML이 이 키를 읽으므로 rename은 publishing+designer 동시 변경 → validation 단독 수정 금지 | 신규 — 발주 `inbox/publishing/20260803T0210Z__validation__MULTI_2026.1Q__forward_baseline_key_misnomer.md` (PM-2026-08-03 §5) |
| **UH-10** | **면제 근거 마커 11개가 아직 행 귀속 미검사다** (9 항목). 전부 라벨이 여러 줄로 감기는 행(`해약환급금 부족분 상당액 중 / 해약환급금 상당액 초과분` 계열)이라 3.0pt 밴드로 앵커되지 않는다. 밴드를 키우면 음성대조군(거짓 최소 Δ 8.87pt)이 무너진다 — 그 값들은 여전히 "페이지 어딘가 있다" 만 검사된다 | 매 실행 `EXEMPTION_MARKER_UNANCHORED` review 로 **전건 인쇄**되므로 조용해지지 않는다. 해결 방향: 상수 밴드 대신 **페이지별 행 피치 추정**(단어 y-중심 군집의 중앙값 간격)으로 적응. 155개 마커 중 51개는 이번에 행 귀속으로 승격됐다(ANCHORED 51 · LABELLED 23 · UNIQUE 75 · AMBIGUOUS 11). PM-2026-08-24(b) §5 / P3 |
| **UH-11** | **`36_irr` 의 상대 허용오차 `max(2.0, 5%×기대값)` 가 발행사 상시 편의를 흡수한다.** 교보생명(KR0073) 6개 짝수분기에서 공시값이 **매번** 도출값보다 크고 절대 잔차가 +23 → +241 로 커지는데 5분기가 통과한다. 2025.2Q 만 RED 인 것은 편차가 유별나서가 아니라 기준금액이 작아져 상대비가 5% 를 넘었기 때문이다 | 허용오차 변경은 **전 버킷 영향 측정이 선행**돼야 해서 이번 라운드에 하지 않았다(원장 KR0073 `open_lead` 에 박아 뒀다). 검토 방향: 절대·상대 병용 또는 **부호 일관성 검사**(같은 부호가 N분기 연속). PM-2026-08-24(b) §5 / P2 |
| **UH-12** | 부재 박제 셀 집합이 `_absence_pin_census` 에서는 주입 가능한데 `_transition_mmult_after` · `_parent_present_child_incomplete_after` 는 **모듈 상수를 직접 참조**한다. 라이브에서는 셋이 같은 상수를 보므로 무해하지만, 합성 selftest 주입이 세 축에 고르게 닿지 않는다 | 세 함수에 같은 `pins` override 인자를 붙이면 해소. 지금은 `tests/test_exemption_absence_pin.py` 가 **라이브 마스터 변이**로 그 축들을 덮는다(합성보다 강한 증거라 측정된 이득이 작다). PM-2026-08-24(b) §5 / P3 |
| **UH-13** | **`data/dart/viz/csm_waterfall_history.json` 은 아무도 재생성하지 않는 정적 스냅샷이다.** 선언 빌더 `scripts/ifrs17_batch_historical.py` 가 2026-06 에 아카이브된 뒤 마스터만 백필·정정을 받아 벌어졌다. 실측 2026-08-25: 대조 1,581셀 중 **933건(59.0%) drift**, 최대 Δ 43,852억(삼성화재 2023.3Q closing) · 스냅샷 자체 단계 항등식 파탄 41건 · 마스터에 있는데 스냅샷에 없는 회사 14사. IFRS17.html 워터폴 이력 패널이 그 값을 그린다 | **검사는 배선됐다**(`HIST_MASTER_DRIFT`·`HIST_STAGE_IDENTITY`·`HIST_CENSUS_MISSING`, baseline 등재 YELLOW). **파일의 처분이 미결** — 발주 `inbox/parser/20260825T1125Z__validation__MULTI__live_viz_artifacts_unchecked.md` §A. 권고: 마스터 파생으로 교체(drift 가 구조적으로 0 이 된다). PM-2026-08-25 §5 |
| **UH-14** | **배선 매트릭스(R-1/R-2)가 소스 문자열 검사다.** 정본 증거는 런타임 추적(`scripts/_probes/probe_20260825_trace_validator_reads.py`)인데 `validate_data_contract` 한 번 도는 데만 수십 초라 push 묶음에 넣지 않았다. 경로 리터럴이 소스에 있으면 통과하므로, 리터럴은 남았는데 코드경로가 죽은 경우를 못 잡는다 | 변이시험 M2b(상류를 직접 로드)가 가장 흔한 회귀형을 덮는다. 검토 방향: 추적 프로브를 릴리스 전 수동 실행으로 규정하거나 검사기별 read-manifest 를 산출물로 남겨 대조. PM-2026-08-25 §5 |
| **UH-15** | **루트 마스터의 하류 사본을 열거하는 매니페스트가 없다.** 지금까지 세 개(라이브 HTML 이 fetch 하는 .json · `public_exports/` · `insurequant_master_tables.xlsx`)가 **전부 사고가 난 뒤에** 하나씩 검사 대상이 됐다. 네 번째 사본이 생기면 같은 순서를 또 밟는다 — 사본이 느는 것을 탐지하는 장치가 없고 **사람의 기억**에 걸려 있다 | **PM-2026-08-25 의 UH-14 와 같은 뿌리**(정본 증거인 런타임 추적 프로브가 push 묶음 밖에 있다)라 그쪽에 합류시킨다. 먼저 실측이 선행돼야 한다 — 누가 루트 마스터를 읽어 파일을 쓰는지 추적. 추측으로 매니페스트를 만들면 그 자체가 또 다른 honor-system 이다. PM-2026-09-02 §5 / P2 |
| **UH-16** | `sync_master_xlsx_sheet.py` 는 **시트에 변경이 있을 때만** `요약` 행수를 고친다(L210-212 조기반환이 L273 요약 블록보다 앞). 데이터 시트는 전부 동기인데 `요약` 만 틀어지면 `MASTER_XLSX_SUMMARY_ROWCOUNT` RED 을 그 스크립트로 못 고친다 | 현재 무해(실측: 요약 전 행 일치). 발생하려면 워크북을 손으로 편집해야 하는데 그것 자체가 금지된 동작이다. 발화하면 그때 `--summary-only` 를 추가한다 — **미리 만들지 않는다**(측정된 이득 0. UH-5·UH-9 선례: 필요가 확인되기 전에 배선하지 않는다). PM-2026-09-02 §5 / P3 |
| **UH-17** | `check_master_xlsx` 는 **워킹트리 xlsx ↔ 워킹트리 마스터**를 대조한다. `PUBLIC_EXPORT_*` 는 마스터 쪽을 `git show HEAD:` 로 읽는데(`read_committed_json`) 이쪽은 아니다 → xlsx 를 sync 하고 **커밋 없이** push 하면 게이트는 깨끗한데 커밋된 상태는 어긋난다 | 새 클론에서는 즉시 RED 이라 자기치유되고, 더러운 워킹트리는 `git status` 에 보인다. 커밋 기준으로 바꾸면 워크북 재읽기(+10초) + **정상 sync 중 상시 발화** — 오탐 억제를 설계하기 전에는 배선하지 않는다(UH-5·UH-9 선례). PM-2026-09-02 §5 / P3 |
| **UH-18 ✅ 해소 (2026-09-13)** | 차단 룰 **5종 전부** 배선 — `J-ESR/build_jesr_page_json.py::source_gate_check` → `self_check()` errors → `main()` **exit 1**. 오프라인/온라인을 갈라 걸었다: netloc 만 보면 되는 `JP_SOURCE_EXPIRING_HOST` 는 빌더가 직접, 네트워크가 필요한 두 판정은 선행 단계가 박제하고 빌더가 박제를 읽는다 — URL 생존은 `check_source_urls.py` → `source_url_health.json`(`JP_SOURCE_URL_DEAD`), **값이 그 문서 안에 있나**는 `check_esr_in_source.py` → `esr_in_source_health.json`(`JP_ESR_NOT_IN_SOURCE`). 두 증거가 **같은 봉투**라 신선도 검사가 한 벌(`_load_evidence_envelope`)이고, 증거가 낡으면 두 룰이 같이 낡는다(한 쌍). 증거 키가 **(url, esr_pct)** 라 '값만 고치고 수집기를 안 돌린' 상태가 옛 `found` 를 물려받지 못한다. 오탐 억제는 실측 기반: RED 로 읽는 verdict 는 `not_found` 하나(`skip_landing` 1사·`skip_no_text` **0사**는 YELLOW). 초안의 '같은 문장' 규격은 되돌려 재보니 **거짓 RED 7/14**, 확정 규격(±200자 / 같은 표 행)은 **14/14 통과·거짓 RED 0**. 회귀 `tests/test_jp_source_gate.py` **63** + `tests/test_jp_deploy_matches_census.py` **26** · 이빨 **8/8** 발화 | **사고 재현 실측**: 東京海上HD 를 238 로 되돌리면 `JP_ESR_NOT_IN_SOURCE` RED(exit 1) — 238 은 56페이지 어디에도 없다(문턱을 100,000자로 풀어도 `not_found`). MS&AD 를 사고 당시 URL(합병 보도자료)로 되돌려도 RED — 그 URL 은 지금도 `ok_requires_headers`(살아 있음)라 **먼저 배선한 4종으로는 못 잡는다**. **단 かんぽ 220 은 못 잡는다** — 그 자료에 실재하는 조정치라 이 축의 원리상 `found` 다(→ **UH-21**) |
| **UH-19 ✅ 해소 (2026-09-13, 같은 날)** | **jp 빌더 self-check 는 빌더를 돌릴 때만 돈다** — census 를 고치고 빌드 없이 커밋하면 게이트가 한 번도 안 돈다. 실측 사례: 커밋 `62eed63` 이 census·`esr_target_ranges.json` 만 고쳐 HEAD 의 배포 JSON 이 census 와 어긋났다(2사 `basis`=`unconfirmed`, SOMPO `high_pct`=270) | **해소 2단**: ① 배포 JSON·마스터를 census 기준으로 재생성(`fafa546` 이후 라운드) ② `tests/test_jp_deploy_matches_census.py` 신설 — 빌더를 임시 경로로 재실행해 커밋본과 `generated_at` 제외 전량 비교, 즉 **"빌더를 돌렸는가"가 검사 대상**이 됐다. 이빨: 배포본 수치 하나를 흔들면 즉시 FAIL(원본 md5 복원 확인). 그 테스트와 `tests/test_jp_source_gate.py` 를 `scripts/prepush_check.py` offline 묶음 + CLAUDE.md §5 jp 축소범위에 넣어 **훅이 실제로 부른다** |
| **UH-20** (신규 2026-09-13) | **훅이 push refspec 을 게이트에 안 넘긴다.** `prepush_check.py` §0 의 범위 판정은 `merge-base(@{upstream},HEAD)..HEAD` + 스테이지 + 워킹트리 + 미추적으로 "이번에 밀 것" 을 **근사**한다. git 은 pre-push 훅에 stdin 으로 `<local ref> <local sha> <remote ref> <remote sha>` 를 주는데 훅이 그걸 버리고 있다 | 근사가 빗나가는 경우(다른 remote·다른 branch 로 push, 격리 워크트리 cherry-push 등)에도 **fail-closed 로 전체 게이트가 돈다**(안전 방향) — 즉 지금은 "느려질 뿐 뚫리지 않는다". 그래서 P3. 고치려면 `.githooks/pre-push` 가 stdin 을 `--refspec` 류로 넘기고 `collect_changed_paths` 가 그 범위를 쓰면 된다. 회귀는 `tests/test_prepush_scope.py` 에 케이스 추가 / P3 |
| **UH-21 ✅ 해소 (2026-09-13)** | **문서 안에 실재하지만 정의가 다른 값**을 가르는 축이 없었다. `JP_ESR_NOT_IN_SOURCE` 는 "그 숫자가 그 문서에 있나" 만 묻기 때문에 かんぽ 220%(「大量解約リスクを除いた場合」 조정치)를 `found` 로 통과시킨다(실측 p35, d=1) | **`JP_ESR_ADJUSTED_FIGURE` 정의·배선 완료.** 판정식 = ① 화면값이 나오는 ESR 라벨동반 산문 조각이 1개 이상(0개면 **기권**) ② 그 조각이 **전부** 한정어를 달았다 ③ 같은 문서에 **한정어 없는 다른 ESR 값**이 있다 — ③ 까지 서면 `adjusted_alt`(본 룰), ②까지면 `adjusted_only`(보조). 수집기 `check_esr_in_source.py::scan_adjusted` 가 판정해 기존 증거 `esr_in_source_health.json` rows 에 필드로 박제하고(새 증거파일 없음 = 신선도 검사 재사용), 게이트 `build_jesr_page_json.py::_adjusted_figure_check` 가 읽는다. **③ 이 본 룰인 이유는 실측**: 한정어 목록에 definition marker(`ベース`·`内部管理`·`規制`·`速報値`)를 넣으면 ①② 단독은 정상 3사(日本生命·住友·朝日)가 거짓 발화하는데 ③ 을 붙이면 전부 조용하다. 기권 조건이 없으면 표·차트 전용 문서 7사가 거짓 발화. severity 는 **YELLOW**(빌더 exit 0)지만 배포본 증거에 면제 없는 발화가 남으면 push 묶음이 막는다(`test_live_esr_evidence_has_no_unexempted_adjusted_figure`) — 필드 부재·모르는 verdict 는 RED | **엔드투엔드 재현**: 사본 census 를 かんぽ 220 으로 되돌리면 `JP_ESR_NOT_IN_SOURCE` 는 여전히 `found`(조용)인데 조정치 축이 `adjusted_alt`·대안 181% 로 발화하고 **push 묶음 exit 1**. 현재값 181 은 `unqualified` — 발화 안 함. 회귀 83+26 · 이빨 10/10 · PM-2026-09-13 §4d |
| **UH-22** (신규 2026-09-13) | **`JP_ESR_ADJUSTED_FIGURE` 의 이빨이 빌더가 아니라 push 묶음에 있다.** severity 가 YELLOW 라 빌더는 exit 0 이고, 차단은 라이브 증거 테스트가 한다 — RED 였다면 빌더가 직접 막는다. YELLOW 로 시작한 것은 판단이다(한정어 목록이 휴리스틱이고, 조건부 값을 정당하게 헤드라인으로 쓰는 회사가 있으면 RED 오탐 1건이 정상 배포를 막는다. UH-5·UH-9 선례) | **승격 조건을 미리 못 박았다**: 다음 census 라운드(10/31 J-ICS 공시기한 직후, posted 15 → 최대 77사)에서 ① `adjusted_alt` 오탐 0 ② 한정어 목록을 오염판으로 바꿔도 정상사 발화 0 ③ 발화 회사가 원문 대조에서 조정치로 확인 — 셋이 서면 `ESR_ADJUSTED_YELLOW` → RED 분류로 옮긴다 | **P2** · PM-2026-09-13 §5 |
| **UH-23 ✅ 해소 (2026-09-14)** | **한정어 목록(`ADJUSTED_QUALIFIERS`)의 정본이 코드에만 있었다.** ESR 라벨 목록은 정본이 `docs/domains/claude-agent-jp.md §3` 이고 테스트가 한 줄씩 대조하는데(라벨을 지어내면 검증기가 정본과 다른 목록으로 검증한다), 한정어는 같은 장치가 없었다. **2026-09-13 에 절반만 닫혔다** — §3 에 한정어 절이 서긴 했으나 (a) 대조 테스트가 없었고 (b) §3 이 적은 것은 관측 3종뿐이라 코드 10종과 어긋나 있었다(실측: 코드 10종 중 §3 에 문자열로라도 있던 것 **4종**, 그중 `調整後` 는 §3 이 「추측으로 넣지 말 것」 으로 **지목한** 어휘인데 코드가 실제로 들고 있었다) | **정본 표 등재 + 양방향 대조 테스트 2건 배선.** §3 이 한정어 10종(관측수·채택근거 열)과 정의 표지 4종을 **표**로 싣고, `tests/test_jp_source_gate.py::test_adjusted_qualifiers_match_the_domain_doc` 이 §3 표 ↔ `ADJUSTED_QUALIFIERS` 를 **집합일치**로(코드에만 있어도 FAIL·문서에만 있어도 FAIL), `::test_definition_markers_named_in_the_doc_stay_out_of_the_code_list` 가 §3 이 지목한 정의 표지의 **코드 부재**를 강제한다. 기존 `test_qualifier_list_is_not_empty_and_excludes_definition_markers` 는 **문서를 안 따라가는 하드코딩 바닥선**으로 남긴다(역할 반대 — 아래 변이가 근거) | **변이 6/6 발화**(사본에서만, 원본 md5 복원 확인): 코드에 가짜 한정어 추가 · §3 표에서 행 삭제 · 코드에서 항목 삭제 · 정의 표지를 양쪽에 일관 추가 · §3 한정어 표 통째 삭제 · §3 정의 표지 표 통째 삭제 — **6건 모두 기존 83건은 침묵**(중복 아님). 음성대조 2건: 집합일치를 부분집합으로 약화하면 '코드에서 항목 삭제' 가 **빠져나간다**(양방향이 load-bearing) · `規制` 를 §3 정의 표지 표에서 빼 한정어로 승격하면 새 2건은 조용하고 **하드코딩 바닥선만** 발화한다(바닥선도 중복 아님). 축소 묶음 87 passed · `REDUCED(jp-scope)` | **해소** · PM-2026-09-13 §5 |
| **UH-9** | **회사 단위 `item47` 스코프 투표는 관행이 시간에 따라 바뀌는 발행사를 못 담는다.** KB손해(KR0010)는 2023.1Q~2025.1Q 가 INCL, 2025.2Q부터 EXCL 로 깨끗하게 갈리는데(item47 66,275 → 14,398) 지금은 CONFLICT 로 묶여 종전 관행 EXCL 로 처리된다. **현재는 무해** — CONFLICT 4사(KR0010·KR0050·KR0051·KR0069) 전 버킷이 한도 미구속이라 어느 읽기로 읽든 한도초과액이 0 이고, INCL 로 뒤집는 전수 시뮬(V3)에서도 status 전이 0건이었다 | 분기 단위 판정은 **측정된 이득이 0 이라 만들지 않았다**(오탐억제를 설계할 수 없으면 배선하지 않는다는 UH-5 선례). 발화 조건과 감지 경로를 대신 박아 둔다: CONFLICT 회사에 한도가 구속하는 버킷이 생기면 `3_tier2_composition` 이 먼저 RED 를 낸다. 재현 `scripts/_probes/probe_20260824_kr0075_scope_evidence.py` (CODES 에 CONFLICT 4사 투입) / P3 |
| **UH-25 ◐ 게이트 축 해소 (2026-09-14) · 화면 축 잔여** | **비-PDF `source_url` 인 posted 행은 값 검증 두 축이 *둘 다* 안 돌고, 그 사실이 exit code·배포본·화면 어디에도 안 남았다.** `check_esr_in_source.py::check_row` 의 `is_pdf` 분기가 비-PDF 를 `scan_landing` 으로 보내 `verdict=skip_landing`(`ESR_VERDICT_YELLOW` = 인쇄만) + `adjusted_verdict=not_applicable`(`ESR_ADJUSTED_ABSTAIN` = 기권)으로 적는다 → `JP_ESR_NOT_IN_SOURCE` 도 `JP_ESR_ADJUSTED_FIGURE` 도 **침묵**하고 빌더는 exit 0 · RED 0. **비대칭이 근거였다**: 같은 YELLOW 인 조정치 축은 `test_live_esr_evidence_has_no_unexempted_adjusted_figure` 로 push 묶음에 이빨이 있는데, skip 축에는 라이브 대조가 **하나도 없었다** — 유일한 테스트 `test_skip_verdicts_are_yellow_not_red` 는 *침묵을 단언한다*. 2026-09-13 에 **T&D 222% 1건이 실제로 그 상태로 라이브**였다(증거 evidence 는 「본문에 222 표기가 안 보인다」 인데도 게이트 green). 게이트 요약도 조정치 축만 분포를 찍고 1차 축은 안 찍었다 | **✅ 게이트 축 해소 — `JP_ESR_UNVERIFIED_VALUE` 정의·배선 완료(2026-09-14).** 판정식 정본 = `build_jesr_page_json.py::unverified_value_reasons()` (게이트도 테스트도 **이 함수 하나**를 부른다 — 재타이핑 금지). **논리합**이다: (a) `verdict ∈ ESR_VERDICT_YELLOW`(skip_landing·skip_no_text) **또는** (b) `adjusted_verdict ∈ ESR_ADJUSTED_NOT_JUDGED`(not_applicable). 곱(=0축)으로 걸면 수집기가 반쪽만 회귀한 상태가 빠져나간다. 호출은 `_esr_in_source_check` 의 **verdict 분기보다 앞**이라 회사·verdict 필터 없이 전 행을 돈다. **오탐 억제의 선은 `abstain_no_prose` 를 (b) 에서 뺀 것이고 실측이 근거다** — 그건 PDF 를 읽고 「라벨동반 산문 조각 0개」 로 판정한 결과(표·차트 전용)라 1차 축이 `found` 로 살아 있다; (b) 에 넣으면 **정상 8사가 거짓 발화**(2026-09-14 실측, posted 16사 중). severity 는 **YELLOW**(빌더 exit 0)고 이빨은 조정치 축과 **같은 자리** — 배포본 증거에 면제 없는 발화가 남으면 `tests/test_jp_source_gate.py::test_live_esr_evidence_has_no_unexempted_unverified_value` 가 push 묶음에서 막는다. 면제는 `J-ESR/jp_source_exceptions.json` 에 `JP_ESR_UNVERIFIED_VALUE` 로 등재(**owner 권한**, 셀 단위, fail-closed, `expires_on`); 현재 **0건**. 기존 `test_skip_verdicts_are_yellow_not_red` 와 **역할을 docstring 에 갈라 적었다** — 그쪽은 *빌더 exit code 가 skip 으로 안 바뀐다*(합성), 새 것은 *배포본 증거에 그런 행이 안 남는다*(실데이터). 모순 아님. remedy ② 도 같이 닫았다: 요약이 `1차 축 판정 분포` + `값검증 축 census(판정됨/무검증/면제)` 를 조정치 축과 **대칭으로** 인쇄한다 | **배선 시점 실측 발화 0**(전제): `verdict {found:16}` · `adjusted {abstain_no_prose:8, unqualified:8}` · `doc_kind {pdf:16}` · 0축 **0사** — T&D 출처가 목록 페이지 → 統合報告書 PDF 로 바뀌어 점유가 사라진 창에 걸었다(UH-5·UH-9 선례). 배선 후 실데이터 `YELLOW 0건 · RED 0건 · 판정됨=16 무검증=0`. **회귀 85 → 101** · **변이 10/10 발화**(사본에서만, 원본 md5 `fe0021bc…` 복원 확인): 두 필드 **각각**(M1 verdict·M2 adjusted_verdict)·둘 다·skip_no_text·다른 회사·면제 등재로 침묵·다른 회사 면제는 여전히 발화·다른 룰 면제도 발화·진짜 빌더 엔드투엔드 exit 0. **중복 아님(M6)**: M3 변이를 남긴 채 새 라이브 테스트만 지우면 **나머지 100건 전부 통과**. **훅 실증**: 진짜 증거를 일시 변이 → `prepush_check.py` 가 `1 failed, 257 passed` · **`BLOCKED`**, 복원 md5 동일. **⚠ 잔여 = 화면 축(미배선)**: 배포본 `jp/jesr_esr.json` 에서 0축 검증 행과 2축 검증 행의 **키 집합 차이가 여전히 공집합**이고 `jp/jesr_app.js` L307 이 둘 다 같은 「根拠資料 ↗」 로 그린다 — 게이트는 막지만 **사용자는 여전히 "검증 못 함" 과 "검증 통과" 를 구분 못 한다**(불변식 1 의 화면 판). designer·publishing 소관, 티켓 `inbox/jp/20260914T0740Z__validation__JP_MULTI__uh25_screen_axis_residual.md` / **P2** |

## ✅ 2026-07-21 (3차) — UH-5 종결 (owner 승인, premise-refined)

**UH-5 = 요구자본(15~21) 부모 COPY 검사** → **신설 불요로 종결.** 선행조건이던 FSS 2023-03-20
붙임-1(`trend20230320_3.pdf` p6, 회사별 경과조치 종류)을 좌표추출로 전수 복원(총계 검증 4/19/12/8
일치) → `_TRANSITION_KIND` registry(`validate_kics_disclosure.py`)로 등재.

- **전제 falsify**: "TAC형(가용자본만·요구자본 무영향) 회사"는 **0사.** 가용자본(AC) 경과조치 신청은
  4사(케이디비·IBK연금·하나생명·푸본현대)뿐이고 이 4사 전부 요구자본 보험리스크(IR)도 신청. elective
  18사 **전원**이 요구자본(보험리스크) 경과조치 신청사.
- **실측 78 "부모후=전" 셀 분류**: **A(subrisk후≠전인데 부모후=전 = 모순) = 0** [owner 지적 그대로,
  기존 `_transition_mmult_after`가 부모후=sqrt(subrisks후·상관행렬)를 이미 강제 → 모순이 살아남지 못함]
  · **C(item14후는 다른데 부모후=전) = 52, 전부 item19(시장위험)** [한화손·롯데손·악사·처브는 주식/금리
  미신청사 → 정당 / 농협손·DB생명·에이비엘은 신청사이나 금리·주식 경과조치가 *조건부*(K-ICS리스크
  60%>RBC일 때만 발동)라 실효과 0 가능 + identity·mmult 전부 통과=내부정합] · **D(subrisk후 부재) =
  26** [census 소관, 기존 `_parent_present_child_incomplete_after` 담당]. **진짜 미검출 = 0.**
- **결론**: 부모 COPY 룰은 item17=mmult 중복·item19=오탐 52건·진짜미검출 0 → **신설이 오히려 게이트를
  더럽힘.** headline(지급여력비율 item27/28)은 이미 `_transition_ratio_after_capture`가 18사 전원 검증.
  registry는 소비 룰 없는 **문서 registry**(향후 근거)로만 존치.

> owner Socratic 지적("subrisk 다르면 상위 risk도 당연히 달라야")이 결론의 핵심이었다 — 그 논리는 참이며
> **이미 mmult가 강제**하고 있어서 A=0. 즉 UH-5가 없어도 사각이 아니다.

## ⚠️ 도메인 경계 — 경과조치는 K-ICS 전용 (owner 2026-07-21)

경과조치(적용전/적용후 이중공시)는 **K-ICS 고유**다. **IFRS17에는 대응 개념이 없다** — 전환방법
(수정소급/공정가치/그 외)은 도입시점 측정방법이지 이중컬럼이 아니므로 **복사할 짝 자체가 없다.**
따라서 `TRANSITION_AFTER_*` 룰군의 IFRS17 유사룰을 만들지 말 것.
(상위 패턴 *"presence만 검사하면 세탁된다"* 는 도메인 무관이며, IFRS17에서는 분기 복붙·impossible-0
형태로 나타나 `CSM_WATERFALL_PLAUSIBILITY` / `IMPOSSIBLE_ZERO_*` 가 이미 담당.)
