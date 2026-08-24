# PM-2026-08-24 — 부재형 면제가 축을 통째로 눈감겨 틀린 적용후 값이 살아남았다

> 상태: `closed` (5칸 전부 채움)
> 발견 경로: 면제 26버킷 재감사 (validation, 2026-08-24) — `artifacts/validation/reaudit_20260824_KR0097_KR0049_KR0079_plus_ledger_quality.md` §1-A
> 관련 문서: `artifacts/validation/reaudit_20260824_*.md` 5건 · 선행 `PM-2026-08-24_i47_scope_misread.md`

## 0. 사실관계 (blameless)

하나생명(KR0097) 2024.4Q 의 마스터 `kics_disclosure.json` 에서 **적용후 4셀이 틀려 있었다**:

| 항목 | 마스터(정정 전) | 참값 | 근거 |
|---|---|---|---|
| `item33후`(해지위험) | **942.86** | 1,377.71 | 2024.3Q 의 같은 항목 값과 **바이트 동일** = 직전분기 복사(stale) |
| `item34후`(사업비위험) | **896.15** | 714.73 | 동상 |
| `item30후`(장수위험) | (결측) | 0 | phase-in 식 `max(0, 전 − 0.9×최초산출액)` |
| `item35후`(대재해위험) | (결측) | 0 | 동상 |

`942.86`·`896.15` 는 원문 347p 어디에도 없다(`probe_20260824_pdf_grep.py` 로 `94,286`·`89,615`·
`942.86`·`896.15` 전부 0 hit). 참값을 넣으면 R7 집계가 공시 `item17후`(p281, 200,189,811천원
= 2,001.90억)를 **잔차 −0.004** 로 재현하고, 정정 전 값으로는 −201.08 로 tol 100.10 을 2배 넘긴다.

**게이트는 이 셀들을 한 번도 본 적이 없다.** 실측 증거(2026-08-24): parser 가 4셀을 정정한 뒤
게이트를 다시 돌렸는데 findings 가 **타임스탬프 한 줄 빼고 바이트 동일**했다. 재현:

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
  scripts/_probes/probe_20260824_v_mutate_kr0097.py <스크래치>/kics_stale.json
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe \
  scripts/validate_kics_disclosure.py --master <스크래치>/kics_stale.json
# 수정 전: 진짜 마스터 출력과 diff 0줄 (= 값이 바뀌어도 게이트가 모른다)
# 수정 후: mmult 미판정 내역 · 부재 census · provenance RED 가 전부 갈린다, 그리고 EXIT 2
```

영향 범위: KR0097 2024.4Q 적용후 4셀. **라이브 노출 없음**(화면은 `item17후` 집계값을 쓰고
그 값은 원문 그대로였다). 즉 화면 숫자는 안 틀렸고 **마스터와 게이트가 틀렸다.**

같은 뿌리의 2차 발견 2건:
- `_POST_PARENT_NOT_DISCLOSED`(악사손해 2024.3Q)도 같은 구조 — 검증된 claim 은 15~23후 부재인데
  면제 효과는 `item1/2/3/14/27/28후` continuity 까지 덮었다(claim 보다 넓은 면제).
- `_AFTER_SUBRISK_NOT_DISCLOSED` 는 claim(29~35후 부재)보다 넓어 **축 15후까지** 사각으로 넣었다.
  축 15후는 원문 p281 에 여섯 값이 다 인쇄돼 있고 실제로 닫힌다(실측 diff +0.0043, tol 2.0).

---

## 1. 무엇이 통과했나 (어떤 게이트가 왜 못 잡았나)

- 통과 당시 게이트 상태: `validate_kics_disclosure.py` **EXIT 0** · blocking RED 0 ·
  `적용후 mmult 불일치 (item15/17/19, 전사 39사): 0` · `validate_data_contract.py` **RED 0**
- **못 잡은 이유 — 면제가 축을 순회에서 통째로 뺐다.** `_transition_mmult_after` 가 부모 조회
  **전에** 빠져나갔다:

```python
exempt = (c, q) in _AFTER_SUBRISK_NOT_DISCLOSED
for parent, (subs, mat, add_item, tol_kind) in _TRANS_PARENT_SUBS.items():
    if exempt:
        skipped[f"item{parent}:DOCUMENTED_EXEMPT"] += 1
        continue
```

  같은 `(회사,분기)` 집합이 5곳에서 같은 방식으로 쓰였다: mmult 3축 · `_after_parent_missing_
  child_present` · `_parent_present_child_incomplete_after` · `_diversification_negative`
  적용후 · 축 평가율 census. 즉 그 버킷은 **적용후 검사망 전체 밖**이었다.

> **false-green 메커니즘 한 문장**: 면제가 "이 잔차를 용인한다"가 아니라 "이 축을 순회하지
> 말라"로 구현돼, 박제된 셀이 결측인지 stale 값이 앉아 있는지조차 게이트 출력에 한 줄도
> 안 나왔다 — 값이 바뀌어도 산출이 바이트 동일했다.

기존 유형표 대조: **"검사 축 누락"(PM-2026-07-07)의 변종**이다. 그때는 룰이 적용후 컬럼을
아예 안 읽었고, 이번엔 룰은 읽는데 **면제가 그 버킷만 순회에서 뺐다.** 그리고 두 번째 겹이
있다 — 면제를 풀어도 **결측 2칸이 mmult 를 입력결측 SKIP 으로 만들어** stale 쌍이 여전히 hard
RED 를 못 냈다("입력 결측이 검사를 무력화", PM-2026-07-15 유형).

---

## 2. 어떤 룰이었으면 잡았나 (구체 룰 정의)

### 룰 A — 부재 박제 부분충전

| 항목 | 내용 |
|---|---|
| 룰 id | `EXEMPTION_ABSENCE_PIN_PARTIAL_FILL` |
| 입력 | `_AFTER_SOURCE_ABSENT_CELLS` / `_POST_PARENT_SOURCE_ABSENT_CELLS` 에 박제된 (회사, 분기, 항목번호) 집합 × `값_적용후` 필드. 그룹 단위 = `_PARENT_CHILD_AFTER` 의 부모별 자식집합(15→16~21 · 17→29~35 · 19→36~40), 요구자본 부모 박제는 그 자체가 한 그룹 |
| 판정식 | 그룹 안에서 `0 < |값_적용후 present| < |그룹 크기|` |
| 임계값 | 없음(존재/부재 판정). 0 은 값이지 결측이 아니다 |
| severity | **RED (차단)** |
| 오탐 억제 | ① 전부 결측 = 면제가 지키는 바로 그 상태 → 정상 ② 전부 present = 파생값이고 항등식이 검산한다 → 정상. **섞인 상태만** RED. 박제 밖 셀의 결측은 이 룰이 아니라 기존 추출갭 census 소관 |

라이브 실측: 정정 후 0건. 정정 **전** 상태(사고 재현)에서는 `[item17 세부] 부재 박제 7셀 중
5셀만 값이 있다 (값존재 29·31·32·33·34 · 결측 30·35)` 로 RED, 게이트 **EXIT 2**.

### 룰 B — 면제가 축을 빼지 않는다(구조 변경 + 되살아남)

| 항목 | 내용 |
|---|---|
| 룰 id | (구조) `SOURCE_ABSENT_PINNED` 미판정 태그 + `EXEMPTION_ABSENCE_PIN_VALUE_PRESENT` review |
| 입력 | 위와 같음 + 각 축의 적용후 입력 완비 여부 |
| 판정식 | 축의 적용후 입력이 **완비되면 면제와 무관하게 검산한다.** 결측인 입력이 **전부** 박제 셀일 때만 그 축을 `SOURCE_ABSENT_PINNED(항목목록)` 으로 미판정 처리하고 **셀 번호를 인쇄**한다 |
| 임계값 | 축의 기존 tol 그대로(`_eff_tol` / dyn5) — 면제가 허용오차를 느슨하게 하지 않는다 |
| severity | 미판정은 집계·인쇄(비차단), 값이 나타나면 review + 축 RED 는 축 자신의 등급 |
| 오탐 억제 | 박제 밖 셀이 하나라도 결측이면 부재 박제 갈래로 안 내려가고 기존 추출갭 갈래로 간다(`_all_missing_are_pinned`) |

### 룰 C — 원장 ↔ 코드 박제 대조

| 항목 | 내용 |
|---|---|
| 룰 id | `EXEMPTION_PIN_LEDGER_DISAGREE` · `EXEMPTION_PIN_RE_REGISTERED` |
| 입력 | 코드 박제(`_TIER2_ISSUER_INCONSISTENT.findings.residual` · `_LIFE8_ISSUER_INCONSISTENT` · `IRR_DERIVE_ISSUER_INCONSISTENT` · 두 부재 박제) ↔ 원장 `expected_residual` / `absent_cells` / `contradicted_pins` |
| 판정식 | ① 축 키 집합이 다르다 ② 같은 키의 잔차가 `pin_tol=0.01` 밖 (None↔숫자도 불일치) ③ `absent_cells` 항목집합이 다르다 ④ `contradicted_pins` 에 적힌 축이 코드 박제에 다시 나타났다 |
| 임계값 | 0.01 (기존 박제 tol 과 동일) |
| severity | **RED (차단)** |
| 오탐 억제 | 원장에 기록 자체가 없는 항목은 `EXEMPTION_PROVENANCE_MISSING` 소관이라 여기서 중복 발화하지 않는다. `expected_residual_alt_reading`(종전 읽기 보존)은 대조 대상 아님. `status=CONTRADICTED` 고아 기록도 제외 |

**이 룰이 즉시 잡은 것(회귀 증거)**: KR0075 2024.3Q 원장이 존재하지 않는 축 이름
`47_tier2_census|적용후` 를 적고 있었고(코드는 `_post` 접미사), 2024.4Q·2025.1Q 는 census 두 축이
통째로 빠져 있었다. 숫자는 맞았고 **어떤 축을 박제했는가**가 어긋난 상태였다.

### 룰 D — 마커 행 귀속

| 항목 | 내용 |
|---|---|
| 룰 id | `verify.present_rows` 행 귀속 검사 → 어긋나면 `EXEMPTION_CITATION_CONTRADICTED` · 잔여는 `EXEMPTION_MARKER_UNANCHORED` review |
| 입력 | `[{row, value}]` 쌍 + 인용 PDF 페이지 |
| 판정식 | 라벨과 값의 y-중심 거리 ≤ `_ROW_ANCHOR_BAND`(3.0pt) **이고** 값이 라벨 오른쪽(x). 단어 run 은 같은 행 안에서만 누적 |
| 임계값 | 3.0pt. 캘리브레이션 15케이스(참 9 + 음성대조 6): 참 최대 Δ 0.21pt · 거짓 최소 Δ 8.87pt |
| severity | 반증 RED · 미앵커 잔여 YELLOW(review) |
| 오탐 억제 | 라벨이 두 행에 실재하면 두 쌍을 각각 적는다(중복행이 곧 claim 인 버킷이 있다). 자동 승격은 앵커되는 라벨만, 접두사 관계는 **같은 y 에서만** 제거 |

---

## 3. 그 룰이 지금 배선됐나

| | 함수/규칙 | 파일 | scope | exit-code 반영 |
|---|---|---|---|---|
| K-ICS 게이트 | `_absence_pin_census` (룰 A·B) | `scripts/validate_kics_disclosure.py` | 전분기 | ✅ (`exempt_red` → 차단집계) |
| K-ICS 게이트 | `_pin_ledger_agreement_findings` (룰 C) | `scripts/validate_kics_disclosure.py` | 전분기 | ✅ |
| K-ICS 게이트 | `_verify_present_rows` / `_row_anchor_check` / `_marker_grade_census` (룰 D) | `scripts/validate_kics_disclosure.py` | 전분기 | ✅ (반증 RED) / YELLOW |
| K-ICS 게이트 | `_transition_mmult_after` · `_parent_present_child_incomplete_after` · `_after_parent_missing_child_present` · `_diversification_negative` 의 **(회사,분기) 통째 skip 제거** | `scripts/validate_kics_disclosure.py` | 전분기 | ✅ |
| **push 게이트** | `_absence_pin_census` + `_pin_ledger_agreement_findings` 를 `check_census` **1b(vi-b)** 에서 **위임 호출** | `scripts/validate_data_contract.py` | 전분기(면제 축은 `_emit` 필터 없음) | ✅ |

- 회귀: `tests/test_exemption_absence_pin.py` **34 케이스**(라이브 마스터·라이브 원장 변이시험)
  · `scripts/_data_contract_selftest.py` **N8 · N8b · N9 · N10** (합성 주입, 55/55)
  · `tests/test_tier2_issuer_inconsistent_exemption.py` 에 `_post` 박제 회귀 2건 추가
- 위임 강제: `tests/test_exemption_absence_pin.py::test_the_push_blocking_gate_lifts_these_rules_too`
  가 소스에서 위임(재구현 금지)을 확인한다. **K-ICS 게이트에만 배선하면 push 를 못 막는다.**
- 골든: `tests/fixtures/kics_rules_golden.json` 재생성(6차, `--update`) — RED 37→36 ·
  GREEN 9,522→9,523. 사유는 `tests/test_kics_rules_golden.py` `_update()` 의 ⑩ 항목.

---

## 4. documented exception

**있음 — 다만 형태가 바뀌었다.** 종전 "축을 순회에서 뺀다" 형태는 **폐지**했고, 두 항목 다
**셀 단위 부재 박제**로 재등재했다:

| 등재 | 박제 셀 | 등재 위치 | 근거 |
|---|---|---|---|
| KR0097 하나생명 2024.4Q | `29~35후` · `36~40후` (축 15후는 **박제하지 않는다**) | `_AFTER_SOURCE_ABSENT_CELLS` (`scripts/validate_kics_disclosure.py`) + 원장 `absent_cells` | 29~35: raw p281 이 적용후를 대분류까지만 공시, 표준서식 헤딩 2개가 347p 전체 부재(매 실행 `absent_markers` 재확인). 36~40: p301~309 B.2 시장리스크 절에 `경과조치` 0회(2026-08-24 재감사 신규 확인) |
| KR0049 악사손해 2024.3Q | `15~23후` (1·2·3·14·27·28후는 **제외**) | `_POST_PARENT_SOURCE_ABSENT_CELLS` (동 파일) + 원장 `absent_cells` | FY2024_Q3 에 섹션 자체 없음(각주 "지급여력비율은 2024년 12월말 공시 예정임") + FY2024_Q4 p36 총괄표는 과거분기로 3줄만, p42 세부표는 당분기 1열 전용, p43 은 분기 컬럼 없음 |

**해제 1건**: KR0087 동양생명 2025.2Q `2_tier1_bridge` — 재감사 판정 `OUR_RULE_DEFECT`.
`_TIER2_ISSUER_INCONSISTENT` 에서 그 축을 뺐고 원장 `contradicted_pins` 에 남겨 재등재를 막는다.

> exemption 추가는 **owner 권한.** 이 라운드는 **새 면제를 하나도 추가하지 않았다** — 기존
> 2건의 형태를 바꾸고 범위를 claim 에 맞게 **좁혔으며**, 1건을 **해제**했다.

---

## 5. 미배선 잔여 + 후속 티켓

| 잔여 | 왜 위험 | 후속 티켓 / 우선순위 |
|---|---|---|
| **UH-10** 마커 행 귀속 미완 11개 (9 항목) — `32,949`(KR0075 2024.4Q) · `30,450`(KR0075 2025.1Q) · `1,543,723`(KR0087 2025.2Q) · `1,933,391`(KR0003 2024.4Q) · `1,753,563`(KR0003 2025.1Q) · `447,254`(KR0032 2025.4Q) · `13,746`(KR0003 2023.1Q) · `23,584`·`2,069`·`2,098`(KR0075 2024.3Q) · `886,613`(KR0032 2024.3Q) | 전부 **라벨이 여러 줄로 감기는 행**(`해약환급금 부족분 상당액 중 / 해약환급금 상당액 초과분` 계열)이라 3.0pt 밴드로 앵커되지 않는다. 밴드를 키우면 음성대조군(최소 Δ 8.87pt)이 무너진다. 그 값들은 여전히 "페이지 어딘가 있다" 만 검사된다 | 매 실행 `EXEMPTION_MARKER_UNANCHORED` review 로 **전건 인쇄**된다(조용해지지 않는다). 해결 방향: 밴드 상수 대신 **페이지별 행 피치 추정**(단어 y-중심 군집의 중앙값 간격)으로 적응. 측정 후 별건 / **P3** |
| **UH-11** `36_irr` 의 상대 허용오차 `max(2.0, 5%×기대값)` 이 **발행사 상시 편의를 흡수**한다 | 교보생명(KR0073) 6개 짝수분기에서 공시값이 **매번** 도출값보다 크고 절대 잔차가 커지는데(+23 → +241) 5분기가 통과한다. 2025.2Q 만 RED 인 것은 편차가 유별나서가 아니라 기준금액이 작아져 상대비가 5% 를 넘었기 때문 | 이번 라운드는 **허용오차를 건드리지 않았다**(전 버킷 영향 측정 선행 필요). 원장 KR0073 항목의 `open_lead` 에 박아 뒀다. 검토 방향: 절대·상대 병용 또는 **부호 일관성 검사**(같은 부호가 N분기 연속) / **P2** |
| **UH-12** 부재 박제 셀 집합이 `_absence_pin_census` 에서는 주입 가능한데 `_transition_mmult_after` · `_parent_present_child_incomplete_after` 에서는 **모듈 상수 직접 참조** | 라이브에서는 셋이 같은 상수를 보므로 무해하다. 다만 selftest 합성 주입이 세 축에 고르게 닿지 않아, 합성 회귀는 census 축만 덮는다(축 자체는 `tests/test_exemption_absence_pin.py` 가 라이브 마스터 변이로 덮는다) | 세 함수에 같은 `pins` override 인자를 붙이면 해소. 측정된 이득이 작아 이번 라운드에 하지 않았다 / **P3** |
| KR0032 2024.3Q **as-disclosed vs as-restated** | 발행사가 FY2024_Q4 p43 에서 같은 분기 Ⅲ행을 8,867 → 9,390 으로 정정했고, 그 값이면 다리가 +1 로 닫힌다. 지금 마스터는 as-disclosed 라 면제가 유지된다 | **owner 정책 결정 사안**(validation 이 정하지 않는다). 원장 `release_condition` 을 새 조건으로 재작성해 뒀다 — as-restated 채택 시 `TIER2_EXEMPTION_INPUT_DRIFT` RED 가 자동으로 뜬다 / **owner** |

---

## close 체크

- [x] 1 무엇이 통과했나 — 면제가 축을 순회에서 통째로 뺐다(5곳). 변이시험으로 "출력 바이트 동일" 실측
- [x] 2 구체 룰 정의 — 룰 A·B·C·D (입력·판정식·임계값·severity·오탐억제)
- [x] 3 배선 위치 + scope — K-ICS 게이트 + **push 게이트 위임**(`check_census` 1b(vi-b)), 위임 강제 테스트 포함
- [x] 4 exception 근거·등재 위치 — 2건 재등재(셀 단위, 범위 축소) · 1건 해제 + tripwire
- [x] 5 미배선 잔여 + 후속 티켓 — UH-10 · UH-11 · UH-12 + owner 결정 1건
