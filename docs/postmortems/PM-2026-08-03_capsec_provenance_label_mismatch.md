# PM-2026-08-03 — 자본성증권 provenance 라벨 거짓이 게이트를 통과 (false-green)

> 발주: `inbox/validation/20260803T0056Z__owner__MULTI__capsec_provenance_source_id_dart.md`
> 후속 발주(§6, 같은 사건의 두 번째 얼굴):
> `inbox/validation/20260803T0310Z__owner__MULTI_2026.1Q__capsec_coverage_census_regression.md`
> 상태: **closed** (룰 배선 + 사이드카 재발행 + 회귀 케이스 완료 / §6 커버리지 census 배선 완료)
> · 잔여 UH-7 1건 + §6의 데이터측 잔여(raw 재추출, RED 15건 = 의도된 push 차단)
> 계통: PM-2026-06-16 "맞는 산수·틀린 소스"의 **provenance 축 변종** — 이번엔 산수도 소스도 맞고
> **소스 라벨만 거짓**이었다. 게이트는 그 거짓 주장을 "검증"해 통과시켰다.

## 1. 무엇이 통과했나

`scripts/validate_data_contract.py`(push 게이트)는 capital-securities 마스터 3종
(`forward_capital` · `tier1_utilization` · `tier2_utilization`)의 provenance 사이드카에
**`source_id == "FSC_BONDS"` 를 하드코딩 요구**하고 있었다.

```python
if cell.get("source_id") != "FSC_BONDS" or cell.get("effective_filtered") is not True:
    ... rule="EFFECTIVE_LIST_NOT_FILTERED"
```

그런데 **tier1/tier2는 2026-06-20부터 FSC가 아니라 DART가 원천이다**
(`scripts/wire_capital_securities_to_utilization.py:28` → `data/bonds/capital_securities_fy2025.json`,
DART FY2025 사업보고서 per-bond 추출물; 산출 JSON에도 `data_source: "dart_bonds_fy2025_경과조치"`).
근거 발주: `inbox/_resolved/20260620T0238Z__owner__MULTI__capital_securities_issuance_from_dart.md`.

사이드카(하드 작성, publishing `faa34cd`, `generated_at: 20260721T115831Z` = DART 전환보다 한 달 뒤)는
게이트의 하드코딩 요구를 만족시키려고 **DART 파일에 FSC 라벨**을 달았다:

```json
"source_id": "FSC_BONDS",
"source_file": "data/bonds/capital_securities_fy2025.json"   ← DART
```

**통과 당시 push 게이트 RED = 0.** 즉 게이트가 "소스를 검증한다"면서 **틀린 주장을 확인해주고**
통과시키는 상태였다. 불변식 1("게이트가 검사하는 파일 = 사용자가 보는 파일") 정면 위배.

부수적으로 **더 큰 사각**이 같이 드러났다: effective-list 증거 검사
(`Env._load_bond_evidence` → CHECK2 2c)는 `data/bonds/normalized/<최신stamp>/bonds_by_insurer.json`
(**FSC 전용**) 한 파일만 봤다. tier1/tier2가 이미 DART로 옮겨간 뒤에도 그 FSC 스냅샷이 통과해주면
끝이라, **실제로 서빙되는 DART per-bond 파일의 도넛-버그 가드는 아무도 검사하지 않았다.**

> owner 발주 §3의 "파일 없음 = `snapshot_present=False` = 그냥 통과" 진단은 **사실과 달랐다** —
> 그 경로는 이미 `MISSING_EFFECTIVE_LIST` RED를 방출한다(`:559`). 실제 사각은 위 문단, 즉
> **틀린 파일(FSC)을 보고 있었다**는 쪽이다. 결론(재조준 필요)은 동일하게 유효.

## 2. 어떤 룰이었으면 잡았나

| 항목 | 내용 |
|---|---|
| 룰 id | **`SOURCE_ID_LINEAGE_MISMATCH`** |
| 입력 | capital-securities 사이드카 셀의 `source_id` + `source_file` |
| 판정식 | `source_id != lineage(source_file)` → RED. `lineage()`는 경로 접두사 → 원천 매핑: `data/bonds/capital_securities_*`·`data/bonds/disclosure/**`·`data/dart/**` → `DART` / `data/bonds/normalized/**`·`data/bonds/raw/**` → `FSC_BONDS`. **계보 미등록 경로도 RED**(검증 불가 = 통과 아님, owner 원칙 0) |
| 임계값 | 없음(정확일치) |
| severity | **RED**(push 차단) |
| 왜 enum 확대가 답이 아닌가 | `{FSC_BONDS, DART}` 둘 다 허용으로 넓히면 **아무 라벨이나 통과** = 검증력 소멸. 라벨을 경로 계보에 묶어야 "선언"이 검증 가능한 주장이 된다 |

동반 조치 2건:

| # | 내용 |
|---|---|
| (a) | `effective_filtered == true` 요구는 **유지** — 그게 진짜 불변식(상환·콜 도래분이 outstanding 총액에 섞이는 도넛 버그 가드). 단 `source_id` 검사와 **분리**해 어느 쪽이 깨졌는지 구분되게 함 |
| (b) | effective 증거를 **사이드카가 선언한 계보마다** 요구하도록 재조준. `capsec_sources_in_use()`가 사이드카에서 `{계보: {source_file}}`를 뽑고, 계보별 로더가 **그 선언된 파일**을 검사한다. 사이드카 전무 시 fallback = FSC_BONDS(검사 축이 사라지지 않게) |

DART per-bond 증거의 두 축(신설):
1. **아티팩트 자체 as-of 기준**: 콜/만기가 이미 도래했는데 `outstanding_mn > 0`이면 미행사 사실을
   `past_call_outstanding: true`로 명시해야 한다(흥국식 콜경과 예외). 미표기 = 상환분이 인정액에 섞임.
2. **소비 시점 갭**: 아티팩트 as-of(2025-12-31) < 마스터 as-of(2026-03-31) 구간에 콜이 도래한 채권.
   후순위는 `wire_capital_securities_to_utilization.amort()`가 0으로 떨어뜨리지만 **신종(hybrid)은
   `new_hyb += out`로 tier1 분자에 무조건 합산**되므로 이 검사만이 막는다.

## 3. 그 룰이 지금 어디에 배선됐나

| 룰/조치 | 함수·파일 | scope | exit code |
|---|---|---|---|
| `SOURCE_ID_LINEAGE_MISMATCH` | `source_id_for_lineage()` + `verify_provenance_sidecar()` — **`scripts/validate_data_contract.py`** | 사이드카 있는 capital-securities 마스터 3종(발행 분기) | ✅ **push 게이트 RED → exit 2** (`prepush_check.py` → `validate_data_contract`) |
| `EFFECTIVE_LIST_NOT_FILTERED` (분리·유지) | 같은 함수 | 동일 | ✅ push 차단 |
| 계보별 effective 증거 | `capsec_sources_in_use()` + `Env._load_bond_evidence` / `_load_dart_bond_evidence` / `_load_fsc_bond_evidence` → `check_as_of` **2c** | 사이드카가 선언한 계보 전부 | ✅ push 차단 (`MISSING_EFFECTIVE_LIST` / `EFFECTIVE_LIST_NOT_FILTERED`) |
| 사이드카 재발행(계보에서 **도출**, 하드코딩 금지) | **`scripts/emit_capsec_provenance.py`** (신설) · `--check`는 drift 시 exit 2 | 루트 사이드카 3개 | 게이트가 drift를 RED로 잡음 + 아래 pytest |
| 회귀 보호 | `scripts/_data_contract_selftest.py` **G1**(`SOURCE_ID_LINEAGE_MISMATCH`) | 합성 mutation | ✅ `--selftest` **16/16 PASS** |
| 발행 주체 존재 강제 | `tests/test_deploy_assets.py::test_capsec_provenance_source_id_matches_lineage` | 루트 사이드카 3개 + `--check` drift | ✅ pytest **9 passed** |

**K-ICS 게이트(`validate_kics_disclosure.py`)에는 배선하지 않았다** — 이 룰은
`kics_disclosure.json` 스코프 밖(자본성증권 사이드카)이라 그 게이트의 소관이 아니다.
push 차단력은 push 게이트 단독으로 확보된다(절반-경화 아님).

### 이빨 검증 (mutation, owner 완료조건 #2)

| 단계 | 결과 |
|---|---|
| 룰 배선 **전** 라이브 게이트 | RED **0** ← 룰이 죽어 있었다는 증거 |
| 룰 배선 **후**, 사이드카 정정 **전** | RED **2** (`tier1_utilization`·`tier2_utilization` `SOURCE_ID_LINEAGE_MISMATCH`) |
| 사이드카 재발행 후 | RED **0** |
| `source_id_for_lineage`를 무력화(선언값 그대로 인정) | selftest G1 **FAIL**(미검출) = 룰이 실제로 판정을 하고 있음 |

> forward_capital은 착지 도중 **DART로 재기준**됐다(병행 parser 세션,
> `inbox/parser/20260803T0055Z__owner__MULTI_2026.1Q__forward_capital_rebase_fsc_to_dart.md`
> — manifest `bonds_source`가 FSC stamp에서 repo-상대 경로로 변경). 사이드카가 **도출식**이라
> 라벨이 `FSC_BONDS → DART`로 자동 추종했다. 이 자동 추종이 이번 배선의 요점이다.

## 4. documented exception

**없음.** 라벨 거짓은 예외 사유가 될 수 없다(선언과 실제가 다른 것 자체가 결함).
`effective_filtered` 예외도 없음. 유일한 정당 예외 유형은 per-bond 데이터의
`past_call_outstanding: true`(콜 미행사로 실제 잔존 — 흥국화재 2016 신종 등 6건, 라이브 실측
7건 중 6건 표기·1건은 스냅샷 as-of 이후 콜이라 대상 아님)이며, 이는 registry가 아니라
**원천 데이터의 필드**로 근거를 남긴다.

## 5. 미배선 잔여 + 후속 티켓

| ID | 내용 | 티켓 |
|---|---|---|
| **UH-7** (신규) | `kics_forward_capital.json` 셀 키가 `baseline_2025_4Q`인데 실제 데이터는 `BASELINE_QUARTER = "2026.1Q"` 필터 산출물(`scripts/forward_capital_simulation.py:45,93,442`). **값은 맞고 키 이름만 거짓** — as-of 정본 판단을 흐린다(owner §4가 이걸 stale로 의심한 원인). HTML이 이 키를 읽으므로 rename은 designer/publishing 동시 변경 필요 → validation 단독 수정 금지 | `inbox/publishing/20260803T0210Z__validation__MULTI_2026.1Q__forward_baseline_key_misnomer.md` |
| ~~**UH-3**~~ | ~~provenance end-state(no-sidecar=RED) 미전환~~ | ✅ **해소 2026-08-03 (c)** — §7 참조 |
| **UH-8** (신규) | `kics_rate_sensitivity`는 `MASTER_FILES`에 있으나 **CHECK 2 검사 대상이 아니다**(사이드카 없음 → 소스 신선도 미검증). UH-3가 닫은 것과 같은 부류의 잔여 축 | `inbox/parser/20260803T0520Z__validation__MULTI__rate_sensitivity_provenance_sidecar.md` (lane: kics) |
| 절반-경화(확인) | `prepush_check.py`가 `validate_kics_disclosure.py`를 **호출하지 않음**을 재확인(`:23` import는 `validate_data_contract`·`triage_anomaly_candidates`뿐). 이번 룰은 push 게이트 배선이라 무관하지만, K-ICS 게이트 전용 룰(현 documented RED 8건 포함)은 여전히 push를 못 막는다. 체인 추가는 push 의미를 바꾸므로 **owner 결정 사항** | ~~owner 판단 대기~~ → **✅ 해소 2026-08-21** (아래 각주) |

> **정정 각주 (2026-08-25).** 위 표의 마지막 행 "절반-경화(확인)" 은 **더 이상 유효하지 않다.**
> 2026-08-21 에 `prepush_check.py` 단계 1b 로 `validate_kics_disclosure.py` 가 배선됐고
> (`scripts/prepush_check.py:49`, `n_kics` 가 `blocked` 계산에 들어간다), `tests/test_push_gate_wiring.py`
> 가 그 배선을 기계로 강제한다. 즉 **K-ICS 게이트 전용 룰도 이제 push 를 막는다** — 이 행이 owner
> 결정 사항으로 올려 둔 질문은 이미 답이 났다. 이력 보존을 위해 원문은 그대로 두고 각주만 단다
> (같은 stale 문장이 `docs/launch_runbook.md` 등 4곳에 복사돼 있던 것을 2026-08-25 publishing
> 라운드에서 일괄 정정했다 — `docs/changelog_publishing.md` 참조).

## 6. 후속 — 같은 사건의 두 번째 얼굴: 커버리지 census (2026-08-03 b)

§1~5는 **"소스를 틀리게 말하는 것"**을 막았다. 같은 날 owner가 나머지 절반을 지적했다 —
**"소스가 통째로 비어도 통과하는 것"**(`20260803T0310Z`). 라벨 룰 배선 직후에도 게이트 RED=0이었다.

### ① 무엇이 통과했나

`20260803T0055Z`(parser)로 `kics_forward_capital.json`의 채권 원천이 FSC → DART per-bond로
교체되면서, **DART FY2025 annual raw가 없는 회사의 채권이 통째로 빠졌다.**

| 회사 | main(라이브) | 교체 후 | 2030 지급여력비율 |
|---|---|---|---|
| KR0050 하나손해보험 | 1,000억 | **0** | 124.47% → **146.09%** |
| KR0076 아이엠라이프생명보험 | 2,700억 | **0** | 93.65% → **152.12%** (권고선 130% 아래→위) |

상환 차감이 사라져 비율이 **낙관 방향으로** 틀린다. 그런데 게이트는 RED=0 —
`bond_coverage`가 **"스캔 후 무발행"과 "소스에 아예 없음"을 한 값(`no_bonds_in_dart`)으로 뭉개서**
구분 자체가 불가능했기 때문이다. `feedback_coverage_census_mandatory`("빠진 cell 절대 불가,
기대그리드 census는 1급")의 사각.

### ② 어떤 룰이었으면 잡았나

| 항목 | 내용 |
|---|---|
| 룰 id | **`CAPSEC_COVERAGE_REGRESSION`** (+ 축 소실 가드 `CAPSEC_SOURCE_UNRESOLVED`) |
| 입력 | 마스터가 **발행한 회사 행**(self-census, 하드코딩 모집단 없음) × 사이드카가 **선언한** per-bond 소스 파일 |
| 판정식 | 소스에 회사 레코드 **없음** → RED / 있고 해당 슬라이스 잔액 0 → **통과**(정당한 무발행) / 있고 잔액>0 인데 마스터 presence 합 0 → RED(어댑터 drop) |
| 임계값 | 금액 불일치(0은 아님)는 `max(1억, 1%)` 초과 시 **YELLOW** `CAPSEC_AMOUNT_MISMATCH`(관찰기) |
| severity | **RED**(push 차단). 보조축 `CAPSEC_COVERAGE_DROP_VS_PRIOR`(직전 스냅샷 대비 후퇴)는 YELLOW 그물 |
| 오탐 억제 | (a) 슬라이스별 자기검열 — 신종만 발행한 회사의 후순위 0은 검사 대상 아님. (b) tier 마스터는 소진율 분자(신규분)가 아니라 **경과조치 면제분까지 더한 총액**을 존재 신호로 씀(전액 pre-2023인 회사가 정당한 0으로 오탐되는 것 방지) |
| 왜 git diff가 1차 축이 아닌가 | 직전 배포본 대조는 **같은 버그로 두 번 생성되면 눈이 먼다.** 1차 판정은 git 없이 되는 축(소스 내 존재 여부)이어야 한다 |

**라벨을 믿지 않는다**는 §2의 교훈을 그대로 적용했다 — 게이트는 마스터의 `bond_coverage` 값을
읽지 않고 **선언된 소스 파일을 직접 읽어** 존재 여부를 도출한다.

### ③ 그 룰이 지금 어디에 배선됐나

| 룰/조치 | 함수·파일 | scope | exit code |
|---|---|---|---|
| `CAPSEC_COVERAGE_REGRESSION` | `_capsec_coverage_findings()` ← `check_census` **1e** — `scripts/validate_data_contract.py` | 3 마스터(`forward_capital`·`tier1`·`tier2`) 발행 행 전부, display 분기 | ✅ **push 게이트 RED → exit 2** |
| `CAPSEC_SOURCE_UNRESOLVED` | 같은 함수 | 소스 미선언 마스터 | ✅ push 차단 (검사축 소실 = 통과 아님) |
| `CAPSEC_AMOUNT_MISMATCH` / `CAPSEC_COVERAGE_DROP_VS_PRIOR` | 같은 함수 / `_capsec_prior_snapshot_drop()` | 동일 / 직전 `output/kics_forward_capital/<stamp>` | YELLOW(비차단, 그물) |
| 소스 인덱싱(2계보 스키마) | `index_bond_source()` + `Env._resolve_capsec_source_files` / `_load_capsec_bond_source` / `_load_forward_prior_rows` | DART per-bond + FSC normalized | — |
| 3-way 상태값(배포 에셋, **추가만**) | `_bond_coverage()` — `scripts/forward_capital_simulation.py` | `bond_coverage: dart_listed \| no_bonds_in_dart \| **absent_in_source**` | — |
| 회귀 보호 | `scripts/_data_contract_selftest.py` **H1~H5** | 합성 mutation | ✅ `--selftest` **21/21 PASS** (16→21) |

**이빨 검증**: 룰 배선 전 라이브 RED=0 → 배선 후 **RED=15**(KR0050·KR0076 포함) ·
`_capsec_coverage_findings`를 monkeypatch로 죽이면 H1~H5 전부 미검출 FAIL(21→16) = 판정이 실제로 일어남.
`pytest tests/test_deploy_assets.py` 9 passed. 배포 에셋 재생성 diff = `bond_coverage` 15행 +
KR0069 confidence 사유 1건뿐(수치 무변).

### ④ documented exception

**없음 — 그리고 이번 RED을 exception으로 닫지 않는다**(owner 완료조건 #3). raw 부재가 원인이므로
정상 경로는 raw 도착 → 재추출 → RED 자연 소멸이고, **그때까지 push가 막히는 것이 의도된 동작**이다
(`feedback_red_blocks_push`). 정당한 무발행도 registry가 아니라 **소스의 빈 레코드
(`bonds: []`)** 로 근거를 남긴다 — 이미 `20260803T0123Z` 티켓이 요구한 계약이고,
KR0069 삼성생명이 그 형태의 유일한 실례다.

### ⑤ 미배선 잔여 + 후속 티켓

| ID | 내용 | 티켓 |
|---|---|---|
| 데이터 잔여 (RED 15) | raw 있음 12사(KR0008·0029·0050·0051·0074·0075·0076·0080·0095·0100·1011·1098) = 추출 또는 무발행 빈 레코드 명시 | `inbox/parser/20260803T0400Z__validation__MULTI_FY2025__capsec_source_census_records.md` |
| 데이터 잔여 (RED 3) | FY2025 annual raw 자체 부재 3사(KR0049 악사손해·KR1010 교보라이프플래닛·KR0150 서울보증) | `inbox/downloader/20260803T0405Z__validation__KR0049_KR1010_KR0150_FY2025__capsec_annual_raw_missing.md` |
| YELLOW→RED 승격 | `CAPSEC_AMOUNT_MISMATCH`(부분 유실) 라이브 실측 0건 → 1~2 릴리스 관찰 후 RED 전환 | 본 PM(다음 릴리스 검토) |

> **데이터 잔여 진행 (2026-08-03 c)**: RED **15 → 13**. parser가 KR0050·KR0076 레코드를 적재해
> 애초 사고의 두 회사(발행잔액 3,700억·2030 비율 낙관 뒤집힘)가 해소됐다. 잔여 13사는
> `20260803T0400Z`(raw 있음) / `20260803T0405Z`(raw 부재 3사) 처리 대기 = **의도된 push 차단**.

## 7. UH-3 종결 — 사이드카 부재 = RED (2026-08-03 c)

§1~6이 "라벨이 거짓" / "소스가 비어도 통과"를 막았다면, 남은 문 하나는 **사이드카 자체가
사라지는 경우**였다. 2026-07-21 이후 그건 YELLOW라 **push를 못 막았다.**

### ① 무엇이 통과했나 (구조적 위험)

`check_as_of._fallback_note`는 사이드카 부재를 YELLOW로만 방출했다. 이유는 정당했다 — 그 시점엔
CHECK 2 대상 4종이 전부 미발행이라 RED로 두면 push가 영구 차단됐다. 문제는 **발행이 끝난 뒤에도
그 상태가 남아 있었다**는 것: §2의 emitter가 라벨을 도출식으로 바꿨어도, **사이드카 파일이 리빌드에
씻겨 없어지면** 게이트는 YELLOW 하나 남기고 통과했다. 라벨 검사·계보 검사·effective 증거 검사가
**전부 사이드카를 입력으로 쓰므로**, 파일 부재는 §1~6에서 세운 세 축을 한꺼번에 무력화한다.

### ② 전환 근거 (선행조건 실측)

| 마스터 | 사이드카 | 발행 주체 |
|---|---|---|
| `forward_capital` · `tier1_utilization` · `tier2_utilization` | ✅ | publishing `faa34cd` → 2026-08-03 `scripts/emit_capsec_provenance.py` 도출식 전환(§2) |
| `sensitivity_heatmap` | ✅ `data/dart/viz/sensitivity_heatmap_provenance.json` | parser `scripts/emit_sensitivity_provenance.py` (UH-3 잔여 1건) |

라이브 `MISSING_PROVENANCE_SIDECAR` YELLOW **1 → 0** 확인 → RED 승격. parser의 emitter 독스트링이
이미 같은 계약을 명시하고 있었다("once this sidecar exists, CHECK 2 flips … no-sidecar=RED") —
상류가 통보받고 발행한 전환이다.

### ③ 배선

| 항목 | 위치 |
|---|---|
| `MISSING_PROVENANCE_SIDECAR` **RED** | `check_as_of._fallback_note` — `scripts/validate_data_contract.py` · ✅ push 차단 |
| Phase-1 추론 블록 | **존치**(삭제 안 함). 그 분기가 이제 RED라 통과 경로가 아니고, 무엇이 어긋났는지 진단을 함께 보여준다 — 작동하는 검사를 버리지 않는다 |
| 회귀 보호 | `_data_contract_selftest.py` **C3** + baseline에 유효 사이드카 4종(`base_sidecars()`) 주입 · `--selftest` **22/22** |
| 이빨 검증 | `GateResult.add`를 가로채 severity를 YELLOW로 **강등**하면 C3 미검출 FAIL |
| 오탐 | **0** — 전환 후 라이브 CHECK 2 RED=0 유지 |

### ④ documented exception

**없음.** 사이드카 부재에 예외를 두면 §1~6의 세 축이 그 회사·마스터에서 동시에 죽는다.
CHECK 2 대상이 아직 아닌 마스터(`kics_rate_sensitivity`)는 예외가 아니라 **미배선 축**이다 → UH-8.

### ⑤ 미배선 잔여

**UH-8**: `kics_rate_sensitivity` 사이드카 발행(parser lane=kics `20260803T0520Z`) → **발행 후**
CHECK 2 2a(iv) 배선. 발행 전 배선은 즉시 red-out이므로 순서를 지킨다(UH-3에서 검증된 절차).

## as-of 정본 (owner §4 회신)

| 축 | 정본 | 근거 |
|---|---|---|
| forward_capital / tier1 / tier2 사이드카 `as_of_date` | **2026-03-31 (2026.1Q)** | 발행 분기 = `manifest.baseline_quarter` / tier doc `quarter` = 2026.1Q. `wire_capital_securities_to_utilization.py:25` `AS_OF = 2026-03-31`로 인정액을 산출 |
| per-bond 스냅샷 자체 | 2025-12-31 (DART FY2025) | **다른 축이다** — 채권 스냅샷 기준일이지 K-ICS baseline이 아니다. 스냅샷→발행 as-of 사이의 콜 도래분은 2번 룰의 축(2)이 검사 |
| `baseline_2025_4Q` 키 | **stale 키 이름**(값은 2026.1Q) | UH-7, 위 표 |

→ `STALE_AS_OF`는 발화하지 않는 것이 정상이며 실제로 발화하지 않는다(RED=0).
