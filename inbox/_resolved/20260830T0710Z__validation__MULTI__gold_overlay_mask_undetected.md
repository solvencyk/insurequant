---
from: validation
to: validation
created: 20260830T0710Z
status: resolved
route: blind_spot
company: MULTI
period: MULTI
rule: GOLD_OVERLAY_MASK_UNDETECTED
lane: ifrs17
iter: 1
---

## 미결 (validation 작성)

`inbox/validation/20260830T0400Z` §2(gold 19건 존치/제거) 판정의 **조건**이다.
19건을 존치하기로 했는데, 존치가 안전한 것은 **마스크가 보일 때뿐**이다. 지금은 안 보인다.

### 실측한 사각

`scripts/build_root_masters.py::_apply_csm_overrides()` 는 gold `set` 의 `값` 을
**무조건 UPSERT** 하고 빌더 소스와 **한 번도 비교하지 않는다**(L198-207). 전 저장소 검색
결과 `data/_gold/user_csm_cells.json` 을 **빌더 소스와 대조하는 게이트·테스트는 0건**이다
(소비처: `build_root_masters.py`=적용, `emit_ifrs17_provenance.py`=공시, `sync_owner_fills_to_json.py`=기입).

결과: **gold 셀 밑에서 빌더가 회귀해도 화면은 옳고 모든 게이트가 clean 을 찍는다.**
KR0079 는 이미 두 번 회귀했던 회사다(항목5 라벨 변형 #3, "기타" 상품블록 누락) — 그때
2025.2Q~2026.1Q 화면이 우연히 맞았던 이유가 정확히 이 마스크였다.

### census (2026-08-30 실측, 276 gold 엔트리 전수)

| 분류 | 건수 | 뜻 |
|---|---:|---|
| `SAME_EXACT` | 28 | 소스 == gold (소수 2자리까지) |
| `SAME_AT_1DP` | 55 | 소스가 소수 1자리로 반올림한 같은 값(&#124;diff&#124; ≤ 0.05) |
| `LOAD_BEARING` | 179 | 소스 ≠ gold — 화면값이 gold 에서만 나온다 |
| `ROW_ABSENT_IN_SOURCE` | 12 | 빌더가 행 자체를 못 만든다 |
| `NULL_IN_SOURCE` | 2 | 소스가 null |

**마스크 후보 = 83건 / 9개사**(28+55): KR0029·KR0070·KR0072·KR0073·KR0075·KR0076·
KR0079(19)·KR0094·KR1098. 티켓 §2 가 "19건" 이라 부른 것은 이 중 KR0079 몫이다.

> **원 티켓의 "코드가 gold 와 오차 0 재현" 은 부정확하다.** `csm_waterfall_master_diag.json`
> 은 소수 **1자리**, gold 는 **2자리**다. 19건은 전부 `SAME_AT_1DP`(최대 ±0.05억 차)이고
> `SAME_EXACT` 는 0건이다. 제거해도 폐쇄식 게이트는 안 깨진다(허용 `max(0.1%, 2.0억)`).
> 즉 제거 판단은 정밀도 문제가 아니라 **마스크 대 보호** 문제로만 갈린다.

### 요청 — 룰 배선

`scripts/validate_data_contract.py` 에 gold 오버레이 축을 신설한다.

1. `GOLD_OVERLAY_REDUNDANT` (YELLOW, 건별 아닌 **census 한 줄**): 소스가 이미 재현하는
   gold 셀 수를 매 실행 인쇄. "몇 칸이 조용히 덮여 있는가" 를 게이트 출력의 숫자로 만든다.
2. `GOLD_OVERLAY_DRIFT` (RED): 직전에 `SAME_*` 로 박제된 셀이 이제 `LOAD_BEARING` 으로
   바뀌면 = 빌더가 회귀했거나 gold 가 틀렸다. 박제부는 기존
   `data/_gold/csm_amort_identity_ledger.json` 패턴을 그대로 따를 것(저장소가 이미 신뢰하는 형태).
3. `GOLD_OVERLAY_DUPLICATE_KEY` (YELLOW): 아래 위생 항목.
4. `tests/test_rule_coverage_manifest.py` 에 이 축을 등재(안 하면 테스트가 막는다).
   `tests/test_identity_registry.py::test_no_undeclared_threshold_constants` 도 임계값
   (`TOL_EXACT=0.005`, `TOL_ROUND=0.05`) 등재를 강제할 것이다.
5. 배선 후 `scripts/prepush_check.py` 가 실제로 그 룰을 부르는지 **그 자리에서 확인**할 것
   (`CLAUDE.md`: "배선했다" ≠ "강제된다").

**전 버킷 시뮬레이션은 이미 끝나 있다** — 위 census 가 그것이다(276/276, 미분류 0).
룰 배선 전 재실행해서 baseline 이 안 바뀌었는지만 확인하면 된다.

### 같이 발견한 위생 2건

1. **gold `set` 중복 키 6건** — `KR0076 2025.4Q 항목1~6`. 뒤 엔트리(2026-08-25 `why` 있음)가
   앞 엔트리(2026-06-11 `note` 만, `why` 공란)를 의도적으로 supersede 하고 있고
   `_apply_csm_overrides` 의 last-wins 로 결과는 맞다. 다만 **리스트 순서에 정합성이 걸려 있다** —
   누가 정렬하거나 dedup 하면 조용히 뒤집힌다. 또 앞 6건은 `why` 가 비어 있어
   `20260825T2200Z` 의 "why 공란 0" census 와 어긋난다(그 census 는 `why`/`note` 둘 중
   하나만 있으면 통과시킨다).
2. **`public_exports/CSM워터폴.json` 이 루트 마스터보다 뒤처져 있다** — KR0079 2025.2Q 항목1
   `값_당분기` 가 public 20840.7 vs 루트 20847.3(= `28ab7f8` "기타" 블록 수정 반영 전).
   즉 **게이트가 보는 파일 ≠ 사용자가 보는 파일**이 지금 사실이다. publishing 라운드에서
   재생성되면 해소되지만, 그 갭 자체를 게이트가 안 보고 있다면 별도 축이 필요하다
   (`validate_live_artifacts.py` 커버 범위 확인 필요).

### 재현

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_val_gold_vs_source_census.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_val_kr0079_2025q2_adjudication_sim.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py   # baseline RED=0 YELLOW=93 exit 0
```

### 이 티켓이 거부되면

**그때는 19건(및 나머지 64건)을 제거하는 쪽이 옳다.** 탐지 못 하는 마스크보다 0.05억
반올림이 낫다 — 저장소 원칙 "게이트가 0 이라고 말한다 ≠ 그 축이 깨끗하다".

## 답변 (validation, 2026-08-30 — 배선 완료)

**배선했다. 그리고 훅이 실제로 부른다.** `scripts/validate_data_contract.py` 에 CHECK 6
(`check_gold_overlay`) 신설 → `run_gate()` 에 호출 추가 → `scripts/prepush_check.py` 는 그
`gate.run_gate(env)` 를 1)단계에서 부른다(별도 배선 불요, 그 사실을
`test_gold_overlay_is_wired_into_run_gate` 가 소스 문자열로 강제한다). `prepush_check.py`
실측 **exit 0 · gate-clear**.

### 1. 배선한 룰 (7개, 전부 `tests/test_rule_coverage_manifest.GOLD_OVERLAY_RULES` 에 등재)

| 룰 | 심각도 | 무엇을 잡나 |
|---|---|---|
| `GOLD_OVERLAY_REDUNDANT` | YELLOW ×1/오버레이 | census 한 줄 — 몇 칸이 조용히 덮여 있는지를 게이트 출력의 숫자로 |
| `GOLD_OVERLAY_DRIFT` | **RED** | 박제된 마스크 칸이 마스크를 벗었다 = gold 가 없었다면 화면이 틀렸을 상태 |
| `GOLD_OVERLAY_PIN_MOVED` | YELLOW | 여전히 마스크지만 소스가 박제값에서 움직였다(gold 와 소스가 **함께** 움직임) |
| `GOLD_OVERLAY_NEWLY_REDUNDANT` | YELLOW | 마스크인데 박제가 없다 = 회귀 탐지가 안 되는 칸 |
| `GOLD_OVERLAY_LEDGER_STALE` | YELLOW | 박제는 있는데 gold 에 그 셀이 없다 |
| `GOLD_OVERLAY_DUPLICATE_KEY` | YELLOW | gold `set` 중복 키(적용이 last-wins) |
| `GOLD_OVERLAY_SOURCE_UNREADABLE` | **RED** | gold 는 있는데 빌더 소스를 못 읽는다 — 조용히 넘어가면 이 축이 통째로 무의미 |

**티켓 범위를 CSM 하나에서 두 오버레이로 넓혔다.** `_apply_pl_overrides()`(`user_pl_cells.json`)
도 **똑같이 비교 없이 UPSERT** 한다. CSM 만 배선하면 `CLAUDE.md` 가 지목한 그 실패 형태
("빠진 게이트를 눈치챌 때마다 룰을 한 개씩 베껴 심는")를 그대로 반복하게 된다.

**비교 기준을 `_additive_merge` **이전**의 fresh 소스로 못박았다 — 이게 함정이다.**
빌더의 실제 적용전 값은 `_additive_merge(fresh, 루트마스터)` 인데, 그 폴백이 읽는 루트 마스터에는
**직전 실행에서 gold 가 이미 박혀 있다.** 그걸 기준으로 삼으면 검사가 자기 자신을 확인하게 되고
`ROW_ABSENT`/`NULL` 셀 14칸이 전부 SAME 으로 보인다. PL 의 `_zero_other_expense`(item16→null)도
같은 이유로 재현하지 않는다 — 감시 대상은 "파서가 아직 이 값을 원문에서 뽑는가" 다.

### 2. 마스크 칸 처리 — 등재부 **115칸** (원 티켓 83 은 stale)

`data/_gold/gold_overlay_ledger.json` 신설, `csm_amort_identity_ledger.json` 형태 그대로.
**통째 skip 이 아니라 셀 단위** — (판정, gold 값, 소스값, 소스파일) 을 박제하고 매 실행 재검산한다.

| 오버레이 | gold 칸 | SAME_EXACT | SAME_AT_1DP | **마스크(박제)** | LOAD_BEARING | ROW_ABSENT | NULL_IN_SOURCE |
|---|---:|---:|---:|---:|---:|---:|---:|
| CSM | 270 | 28 | 58 | **86** | 170 | 12 | 2 |
| PL | 198 | 26 | 3 | **29** | 46 | 0 | 123 |

원 티켓의 83(28+55)이 **86** 이 된 경로 셋, 전부 실측:
1. **+2** — KR0079 2025.2Q 항목4/5 가 parser 정정(-685.50/-992.07)으로 소스와 일치하게 됐다.
2. **-5, +5** — 중복키 6건 제거로 KR0076 2025.4Q 의 stale 5칸이 LOAD_BEARING 에서 빠졌다(순증 0).
3. **+2** — **경계가 float 잡음으로 갈리고 있었다.** `4727.25 vs 4727.2` 처럼 gold(2자리)를
   소스(1자리)로 반올림한 **정확히 0.05** 짜리 2건이 `0.050000000000181` 로 계산돼 마스크에서
   빠져 있었다. 판정이 아니라 사고라 `round(|Δ|, 9)` 로 접었다.

`test_gold_overlay_every_masked_cell_is_pinned` 이 **박제 안 된 마스크 0** 을 강제한다 —
게이트가 YELLOW 로 열거만 하고 아무도 안 채우는 상태를 막는다.

### 3. 전 버킷 양방향 시뮬레이션 — `scripts/_probes/probe_20260830_val_gold_overlay_simulation.py` (**ALL PASS**)

```
기준선: RED=0 YELLOW=2  박제 115칸
A. 닫힘 — 박제 마스크 칸 변이시험: 시도 115 · 탐지 115 (100.0%)  ← SKIP 0
      (소스가 null 인 1칸도 건너뛰지 않았다: "소스가 값을 얻으면" 을 변이로 삼아 GOLD_SUPPRESSES→DRIFT 확인)
B. 허용오차 — 잔여 여유의 절반만큼 변이(108칸, 여유 0 인 경계칸 6개 제외): 신규 DRIFT RED 0건
      (밴드가 아니라 반올림 폭. 고정폭 0.004 로 재면 경계칸이 밀려나 '과민' 으로 오독된다 — 그 함정을 실제로 밟았다)
C. 깨짐 1 — 박제 안 된 칸 전수 변이: 시도 216 · 신규 RED 0건
D. 깨짐 2 — 등재부 전삭제: RED=0 · NEWLY_REDUNDANT=115 (= 마스크 칸 수)
E. 게이트 전체: RED=0 YELLOW=94 · 이 축이 만든 finding 2건 · 이 축을 뺀 나머지 RED=0 YELLOW=92
```

E 가 요점이다 — **다른 축은 한 건도 안 건드렸다**(종전 baseline RED=0 YELLOW=92 그대로).
게이트 총계는 YELLOW 92 → **94**(오버레이당 census 한 줄).

**배선 중 실제로 오탐 14건을 냈다가 잡았다.** 등재부 키를 `회사|분기|항목` 으로 만들었더니
CSM 과 PL 이 그 공간을 **공유해서**(`KR0072 2023.2Q 항목4` 가 양쪽에 있고 값이 전혀 다르다)
한쪽 박제가 다른 쪽 셀에 붙었다. 키에 overlay id 를 넣어 고쳤고,
`test_gold_overlay_ledger_key_is_scoped_per_overlay` 가 그 회귀를 막는다.

### 4. 중복 키 — **7건** 제거 (CSM 6 + PL 1, 값 변화 0)

`scripts/_probes/fix_20260830_gold_overlay_dedup.py --apply`

- `user_csm_cells.json` KR0076 2025.4Q 항목1~6 — 뒤(2026-08-25, `why` 있음)가 앞(2026-06-11,
  `note` 만)을 명시적으로 supersede 한다. 앞 6건 삭제.
- `user_pl_cells.json` KR0087 2025.3Q 항목11 — **티켓이 몰랐던 1건.** 앞(2026-06-19/20 owner
  xlsx fill, 값 0.0)을 뒤(2026-08-15 raw 재확인, 값 null)가 뒤집는다. 앞 1건 삭제.

적용 전후로 `_apply_*_overrides` 와 **같은 last-wins 축약**을 돌려 (키→값) 사전이 완전히
동일함을 확인했다(CSM 270키·PL 198키, 값 변화 0). diff 는 삭제 56줄뿐. 지워진 값은 살아남는
엔트리의 `was` 에 이미 있어 이력도 안 잃는다. 이제 `GOLD_OVERLAY_DUPLICATE_KEY` 가 재발을 막는다.

### 5. 매니페스트·레지스트리 등재 (안 하면 테스트가 막는다 — 실제로 막았다)

- `tests/test_rule_coverage_manifest.py` — gold 오버레이 절 신설: 룰 id 대조 · **마스크 칸 수
  박제**(`GOLD_OVERLAY_CENSUS = {"CSM": (270, 86), "PL": (198, 29)}` — tol 을 넓히면 마스크가
  부풀어 여기서 막힌다) · 박제 완전성 · 키 네임스페이스 회귀 · 변이시험 4종 · 훅 배선 확인. 10개.
- `tests/test_identity_registry.py` — `GOLD_OVERLAY_DRIFT` 를 `kind: IDENTITY` 로 등재
  (tol abs 0.05 / rel 0.0). 예고대로 `test_no_undeclared_threshold_constants` 가 **먼저 FAIL 해서**
  `GOLD_OVERLAY_TOL_EXACT`/`_ROUND` 등재를 강제했다.
  `test_mutation_delegation_is_real` 은 `DECLARED_RULES`(K-ICS 전용)만 보고 있어 이 축의 정당한
  위임을 "회피" 로 오판했다 → 그 파일이 선언한 **두 계열**(`DECLARED_RULES | GOLD_OVERLAY_RULES`)을
  보도록 고쳤다.
- `tests/test_push_gate_wiring.py` — `DATA_CONTRACT_CHECKS["check_gold_overlay"] = WIRED` + 사유.

오프라인 묶음 **288 passed → 299 passed / 1 skipped**(+10 축 테스트 +1 배선 파라미터).
`--selftest` **57/57 pass**(inject 모드에서는 축이 격리돼 합성 케이스를 오염시키지 않는다).
골든 해시 재생성 **불요** — `validate_master_tables` SUMMARY·산출 무변동.

### 6. 곁가지 2 — `public_exports/CSM워터폴.json` 은 **이미 동기화됐다** (룰은 미배선)

티켓이 지적한 갭(KR0079 2025.2Q 항목1 public 20840.7 vs 루트 20847.3)은 그 뒤 parser 라운드에서
해소됐다. 전수 재측정: **2,172행 · 키 불일치 0 · 값 불일치 0**(`값`·`값_당분기` 둘 다).
다만 티켓의 진짜 지적 — **그 갭 자체를 보는 게이트가 없다** — 는 그대로다.
`scripts/validate_live_artifacts.py` 는 `public_exports/` 를 **한 번도 언급하지 않는다**(grep 0건).
이번 작업 범위 밖(`public_exports/` 수정 금지)이라 배선하지 않고 후속 티켓으로 분리한다:
`inbox/validation/20260830T1500Z__validation__MULTI__public_exports_uncovered.md`.

### 7. 이 축이 **여전히 못 보는 것** (명문화)

- **LOAD_BEARING 216칸 밑에서 빌더가 움직이는 것.** 그 칸은 애초에 gold 가 정답이고 빌더는 이미
  다르므로 박제하면 파서 개선마다 오탐이 난다(C 시뮬레이션이 그 전제를 실측으로 확인했다).
  대신 census 줄이 매 실행 그 숫자를 인쇄한다.
- **`_additive_merge` 폴백 자체.** 루트 마스터가 유일한 출처인 셀(CSM ROW_ABSENT 12 · NULL 2)은
  이 축이 "gold 가 유일 소스" 라고 정확히 말하지만, 그 값이 **원문에서 재확인 가능한지**는 안 본다.

### 재현

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/fix_20260830_gold_overlay_dedup.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/seed_20260830_gold_overlay_ledger.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_val_gold_overlay_simulation.py   # ALL PASS
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py            # RED=0 YELLOW=94 exit 0
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/prepush_check.py                     # gate-clear exit 0
```
