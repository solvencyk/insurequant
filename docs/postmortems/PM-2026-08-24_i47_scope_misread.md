# PM-2026-08-24 — 룰의 `item47` 스코프 가정이 틀려 만든 잔차를 **발행사 모순으로 오진**, owner 판단 면제까지 갔다

> 상태: `closed` (5칸 전부 채움)
> 발견 경로: 게이트 RED 추적 → 후속 티켓 분리 → raw 대조 (validation 자체 발견)
> 관련 inbox: `inbox/_resolved/20260824T0410Z__validation__KR0068_2025.2Q__tier1_bridge_residual_unexplained.md`
> 관련 골든 재생성: `tests/fixtures/kics_rules_golden.json` (5차, 사유는 `tests/test_kics_rules_golden.py` `_what`)

## 0. 사실관계 (blameless)

`2_tier1_bridge` 는 발행사 각주가 정의한 식 `item2 = item4 − (item12 − 한도초과) − item13` 을
검산한다. 한도초과액을 `max(0, item47 − item48)` 로 계산하는데, 이는 **`item47`(보완자본 한도
적용 전)이 채무성 자본만이라는 가정**에 서 있다.

그 가정은 전사 참이 아니다. 발행사가 `item47` 을 두 관행으로 인쇄한다:

| 관행 | 뜻 | 보완자본 재현식 | 원문 증거 |
|---|---|---|---|
| EXCL | `item47` = 채무성 자본만 | `min(47, 48) + 49` | IBK연금 2025.3Q p16 — 한도적용전 403,778 **<** 보완자본 695,572, `min(403,778, 352,469) + 343,103 = 695,572` |
| INCL | `item47` 이 `item49`(해약환급금 초과분)를 **포함** | `min(47 − 49, 48) + 49` | 한화생명 2025.2Q p18 — 한도적용전 14,012,828 **>** 보완자본 13,930,253, 채무성 = 14,012,828 − 6,999,555 = 7,013,273 이 한도 6,930,699 를 82,574백만 초과 |

INCL 회사에서 한도가 **구속하지 않는** 분기에는 두 읽기가 같은 값을 내므로 오분류가 드러나지
않는다(룰은 그 칸들을 `UNCAPPED` = "한도로 안 자름" 이라는 별개 관행으로 분류했다). 한도가
실제로 구속하는 분기에서만 한도초과액이 `item49` 만큼 과대해진다 — 한화생명 KR0068 2025.2Q 가
13분기 중 유일한 그 분기였고, 과대값 70,821.29(참값 825.74)가 다리에 그대로 들어가 잔차
**−30,095** 를 만들었다.

**그 −30,095 를 우리는 발행사 자기모순으로 진단했다.** 값이 전부 원문과 일치했기 때문에
"발행사가 그렇게 인쇄했는데 이유를 모르겠다" 로 정리됐고, owner 가 raw 를 직접 열어 보고
"원문대로 오차 용인" 을 결정해 `VERIFIED_BY_OWNER` 면제로 등재됐다(2026-08-24 오전).
같은 날 오후 `item12`·`item47` 스코프를 끝까지 밀어 인과가 규명됐다.

영향 범위:
- **차단 RED 1건** — KR0068 2025.2Q `2_tier1_bridge`. 라이브 화면 숫자는 안 바뀌었다
  (`kics_disclosure.json` 은 이 라운드 내내 읽기만 했다).
- **잠재 사각** — INCL 로 판정되는 5사(KR0004·KR0068·KR0075·KR0079·KR0080)의 한도 미구속
  칸 79개가 `UNCAPPED` 로 통과하고 있었다. 값은 맞았지만 **맞는 이유가 틀렸다** — 그 회사에서
  한도가 구속하는 분기가 새로 생기면 같은 형태로 또 깨진다.
- **오진된 면제 1건** — 등재된 채로 두면 그 셀은 아무도 다시 안 본다.

---

## 1. 무엇이 통과했나 (어떤 게이트가 왜 못 잡았나)

- 통과 당시 게이트 상태: K-ICS 게이트 `exit 0`, RED=38 / **blocking RED=0**(전부 documented
  exception). push 게이트 `RED=0`. 즉 **두 게이트 다 초록이었다.**
- **못 잡은 이유 — 이건 false-green 이 아니라 그 쌍둥이다.** 룰이 낸 RED 는 실재했지만
  **원인 귀속이 틀렸고**, 그 틀린 귀속이 면제 경로로 흡수돼 게이트가 초록이 됐다. 게이트에는
  "이 RED 의 원인이 발행사냐 우리 룰이냐" 를 되묻는 축이 없다 — 면제 원장은 근거의 *존재*는
  검사하지만 근거의 *귀속*은 검사하지 않는다.

> false-green 메커니즘 한 문장: **룰이 한 관행만 알고 있으면, 다른 관행 회사에서 나온 잔차는
> '발행사가 이상하다' 로 읽히고 면제로 조용해진다 — 룰의 결함이 발행사의 결함으로 세탁된다.**

부수적으로 확인된 두 번째 사각: `3_tier2_composition` 의 `UNCAPPED` 갈래는 매니페스트에
*"target == item47 — 한도로 안 잘림(**49 가 47 안에 포함된 관행**)"* 이라고 이미 적혀 있었다.
**두 관행의 존재를 코드가 알고 있었는데 갈래 이름이 그 차이를 담지 않아**, 스코프가 다르다는
사실이 한도초과액 계산에 전달되지 않았다. 이름이 뜻을 못 담으면 그 지식은 없는 것과 같다.

## 2. 어떤 룰이었으면 잡았나 (구체 룰 정의)

| 항목 | 내용 |
|---|---|
| 룰 id | `2_tier1_bridge{,_post}` 의 **스코프 인식 한도초과액** + 갈래 `I49_IN_I47_CAPPED` / `I49_IN_I47_UNCAPPED` |
| 입력 | `item3`(공시 보완자본) · `item47` · `item48` · `item49`, `값`·`값_적용후` 두 컬럼. 스코프는 **회사 단위**로 그 회사 자신의 결정적 버킷에서 투표 |
| 판정식 | 스코프 판정: 버킷이 `item3 == min(47,48)+49` 만 재현하면 EXCL 표, `item3 == min(47−49,48)+49` 만 재현하면 INCL 표. 회사에 INCL 표만 있으면 `scope=INCL`. 그때 채무성 자본 `debt = item47 − item49`, **한도초과 = `max(0, debt − item48)`** (EXCL 은 종전대로 `max(0, item47 − item48)`). 다리는 `item2 == item4 − (item12 − min(한도초과, item12)) − item13` |
| 임계값 | `eff_tol` = 2.0억(억원 정수 4항 반올림 ±0.5×4). 이미지 OCR 회사(KR0010·KR0079)는 10.0 — **스코프 투표도 같은 tol 을 쓴다**(다르면 투표가 검사와 다른 잣대로 갈린다) |
| severity | 적용전 RED(차단) · 적용후 YELLOW(적용후 관계식 미확립, `_POST_UNESTABLISHED`) |
| 오탐 억제 | ① 스코프는 **회사 하드코딩 리스트가 아니라 데이터 투표** — 두 읽기 중 하나만 성립하는 결정적 버킷만 센다(모호·NEITHER 는 표에서 제외). ② 한 회사 안에서 두 표가 갈리면(CONFLICT 4사) **종전 관행 EXCL 로 남긴다** — 근거 없이 새 읽기를 넓히지 않는다. ③ `item12` 상한 클램프는 그대로 유지(그 9칸의 근거는 독립적이다) |

**전 버킷 시뮬레이션(반영 전 필수 단계, 양방향):**

| | 건수 |
|---|---|
| 새로 닫히는 칸 | **1** (KR0068 2025.2Q `2_tier1_bridge` −30,095.00 → **0.26**) |
| 새로 깨지는 칸 | **0** |
| status 무변동 | 13,663 (findings 총계 13,664 불변) |
| 갈래 이름만 바뀐 칸 | 272 (`UNCAPPED`/`BOTH` → `I49_IN_I47_*`) |
| status 동일 + diff 이동 | 12 (KR0075 3분기 × 축 B·F × 전·후 — 면제 박제값 갱신) |

재현: `scripts/_probes/probe_20260824_findings_snapshot.py dump|diff` (룰 수정 전후 스냅샷 대조).
기각된 대안 가설: "모든 회사가 INCL" → 구성식 461칸 + 다리 31칸 파손
(`probe_20260824_kr0068_excess_convention_sim.py`).

## 3. 그 룰이 지금 배선됐나

| | 함수/규칙 | 파일 | scope | exit-code 반영 |
|---|---|---|---|---|
| K-ICS 게이트 | `_tier2_i47_scope_map` → `_tier2_branch(scope=)` → `_validate_tier2_limit` / `_validate_tfi_tier_rows` | `src/solvency/validation/kics_json_rules.py` | 전분기 | ✅ |
| **push 게이트** | **같은 함수** — `validate_data_contract.py` 가 `kics_run_validation` 을 직접 부른다(재구현 없음, L322) | `scripts/validate_data_contract.py` | display 7분기 | ✅ |

**두 게이트가 같은 함수를 부르므로 절반만 굳는 경로가 없다.** (이 저장소의 대표 함정 —
`prepush_check.py` 가 `validate_kics_disclosure.py` 를 호출하지 않는다 — 은 여기서는 발생하지
않는다. 룰이 게이트 스크립트가 아니라 **공유 룰엔진**에 있기 때문이다.)

회귀 방지 배선 3종:

| 시험 | 무엇을 막나 | 파일 |
|---|---|---|
| `test_bridge_uses_the_debt_only_excess_for_i49_in_i47_issuers` | 이 사고 자체의 재현 — 갈래가 `I49_IN_I47_CAPPED` 이고 한도초과 825.74 로 다리가 닫히는지 | `tests/test_tier2_limit_rules.py` |
| `test_every_excess_bearing_branch_is_declared` | **갈래를 늘리면서 `_TIER2_EXCESS_BEARING_BRANCHES` 를 안 고치는 것** — 그러면 새 갈래는 조용히 초과액 0 이 되어 수정이 아무 효과도 못 낸다(작업 중 실제로 밟았다) | `tests/test_rule_coverage_manifest.py` |
| `test_branch_names_are_not_prefixes_of_each_other` | `"branch=CAPPED" in detail` 이라는 **부분문자열 판독**이 `CAPPED_INCL` 같은 이름을 뭉개는 것 | `tests/test_rule_coverage_manifest.py` |

골든은 `--update` 로 재생성했고 사유를 `tests/test_kics_rules_golden.py` `_what` 5차 항목에
남겼다(RED 38→37 · GREEN 9,521→9,522, findings 총계 불변).

## 4. documented exception

- **해제 1건**: `("KR0068","2025.2Q")` 를 `_TIER2_ISSUER_INCONSISTENT`
  (`scripts/validate_kics_disclosure.py`)에서 **제거**했다. 게이트가 먼저
  `TIER2_EXEMPTION_INERT` review 로 "박제한 축에 RED 가 없다 — 등재를 풀어라" 를 인쇄했고
  그에 따랐다. 원장(`data/_gold/kics_exemption_provenance.json`)의 기록은 지우지 않고
  `status: CONTRADICTED` + `resolved_note` 로 남겼다 — 같은 (회사,분기)가 다시 등재되면
  `EXEMPTION_CITATION_CONTRADICTED` RED 가 즉시 뜬다. 시험:
  `test_the_released_hanwha_record_is_kept_as_a_tripwire`.
- **박제값 정정 3건**: `("KR0075","2024.3Q"/"2024.4Q"/"2025.1Q")` 의
  `3_tier2_composition`·`51_tfi_tier2_composition` 잔차를 새 식 기준으로 갱신했다
  (−220.98/−221.31 → +14.86/+14.53 등, 6개 값). **마스터 셀은 한 칸도 안 움직였다** — 박제
  `cells` 가 그대로 통과한다. 면제의 대상(발행사 자기모순)은 그대로이고 측정자만 정확해졌다.
  종전 값은 원장 `expected_residual_alt_reading` 에 사유와 함께 남겼다.
  방증: 정정 후 구성 잔차가 **다리 잔차와 같은 값으로 수렴**한다(2024.3Q +14.86 vs 다리 +15 ·
  2024.4Q +87.22 vs 다리 +87) — 종전 값은 서로 다른 두 불일치가 있는 것처럼 보이게 했다.
- **owner 권한 경계**: 이 라운드는 **면제를 새로 만들지 않았다.** 푼 것 하나, 사유·측정자를
  정정한 것 셋이다. 새 면제 발급은 owner 권한이라는 규칙은 그대로다.

## 5. 미배선 잔여 + 후속 티켓

| 잔여 | 왜 위험 | 후속 티켓 / 우선순위 |
|---|---|---|
| **UH-9 (신설)** — 회사 단위 스코프 투표는 **관행이 시간에 따라 바뀌는 발행사**를 못 담는다. KB손해(KR0010)는 2023.1Q~2025.1Q INCL, 2025.2Q부터 EXCL 로 깨끗하게 갈린다(item47 66,275 → 14,398). 지금은 CONFLICT 로 묶여 EXCL 처리 | 그 회사에서 **한도가 구속하는 분기**가 새로 생기면 이 사고가 그대로 재현된다. 현재는 CONFLICT 4사 전 버킷이 한도 미구속이라 어느 읽기든 초과액 0 = 결과 동일(V3 시뮬 status 전이 0건)이라 무해 | 없음(측정된 이득 0). **발화 시점은 자동으로 보인다** — CONFLICT 회사에 구속 버킷이 생기면 `3_tier2_composition` 이 먼저 RED 를 낸다. 그때 분기 단위 판정으로 내리면 된다. 재현: `scripts/_probes/probe_20260824_kr0075_scope_evidence.py` 의 `CODES` 에 CONFLICT 4사 투입 / P3 |
| 면제 원장이 근거의 **존재**는 검사하지만 **귀속**(발행사 탓이냐 우리 룰 탓이냐)은 검사하지 않는다 | 이 사고의 상위 원인. 다른 축에서 같은 형태가 또 나온다 | 이번에 부분 대응: `VERIFIED_BY_OWNER` 는 매 실행 `EXEMPTION_STANDS_ON_OWNER_JUDGEMENT` review 로 "이건 산수로 증명된 게 아니다" 를 인쇄한다(2026-08-24 오전 신설). 완전한 룰화 경로는 아직 없다 / P2 |
| push 게이트가 `kics_run_validation` 을 `tfi_applicability` 없이 부른다 | 두 게이트가 같은 축에서 다른 status 를 낼 수 있다 | **실측 결과 무해**: RED 는 양쪽 37 로 동일하고, 차이는 `47_tier2_census{,_post}` 28칸이 SKIP → YELLOW 로 **더 엄격해지는 방향**뿐이다. 기록만 남긴다 / P3 |

---

## close 체크

- [x] 1 무엇이 통과했나 — 두 게이트 다 초록. RED 의 원인 귀속이 틀렸고 면제가 그걸 흡수했다
- [x] 2 구체 룰 정의 — 입력·판정식·임계값·severity·오탐억제 + 양방향 시뮬(1 fix / 0 break)
- [x] 3 배선 위치 + scope — 공유 룰엔진이라 두 게이트 동시 적용, 회귀 시험 3종
- [x] 4 exception 근거·등재 위치 — 해제 1 · 박제값 정정 3, 원장 위치·시험까지 명시
- [x] 5 미배선 잔여 + 후속 티켓 — UH-9 신설(발화 조건과 감지 경로 명시) + 상위 원인 2건
