# Validation Changelog (Stage 3)

> Last updated: 2026-08-29 (f) · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Authoritative rules: docs/agents/kics-json-validation-rules.md

Validation-only history. Cross-stage changes also keep a 1-line cross-reference in [`docs/claude-changelog.md`](claude-changelog.md).

## 2026-08-29 (f) — PL 등식의 절반이 구성상 참이었다: 판정을 상수로 선언 + item22 원천 대조 신설

티켓 `inbox/_resolved/20260829T2130Z__validation__MULTI__pl_eqs_constructive_tautology.md`
(owner 가 제안 1·2·3·4 승인). **마스터 값 무변경 — 룰·문서·매니페스트만.**

### 무엇이 문제였나

빌더가 우변의 한 항을 좌변에서 빼서 만든다(`build_pl_breakdown.assemble` ·
`fetch_dart_fs._parse`): `item7 = 3−(4+5+6)` · `item12 = 8−(9+10+11)` · `item18 = 17−19` ·
`item21 = 22−20`(410/418) · `item23 = 22−24`(418/418 무조건). 그래서 그 등식들은 **산수상 깨질
수가 없고**, `PL_BRIDGE` 의 `pass=3057` 중 **1,608(52.6%)이 그런 pass** 다.

CONSTRUCTIVE 변이시험(그 칸을 흔들고 빌더가 그 칸으로부터 계산하는 하류 항을 빌더와 똑같이
다시 계산 — 파서가 틀리면 실제로 일어나는 형태) 실측:

| 주입 | 버킷 | NAIVE | CONSTRUCTIVE | 잡은 룰 |
|---|---|---|---|---|
| item5 원수RA | 334 | 94.3% | **0.0%** | 없음 |
| item6 원수예실차 | 324 | 97.2% | **0.0%** | 없음 |
| item9 재보험CSM상각 | 321 | 93.5% | **0.0%** | 없음 |
| item10 재보험RA | 317 | 94.6% | **0.0%** | 없음 |
| item11 재보험예실차 | 318 | 94.3% | **0.0%** | 없음 |
| item19 보험금융손익 | 326 | 97.9% | **0.0%** | 없음 |
| item22 세전이익 | 338 | 100.0% | **0.0%** | 없음 |
| item23 법인세 | 338 | 100.0% | **0.0%** | 없음(빌더가 덮음) |

`validate_data_contract.run_gate()` 를 같이 물려도 신규 RED **0 건**이다. 즉 `RED=0` 이
"검사했더니 깨끗"이 아니라 **"검사 대상이 아니었다"** 인 항목이 8개였다.

### 무엇을 했나

1. **판정을 상수로 선언.** `validate_master_tables.PL_EQ_EVIDENCE` — 11개 라벨(PL_EQS 9 +
   dual 2)마다 `(REAL|TAUTOLOGY|PARTIAL, 근거)`. 주석이 아니라 게이트가 읽는 값이고,
   `_assert_pl_eq_evidence_declared()` 가 **import 시점에** 판정 없는 등식을 죽인다.
   SUMMARY: `pl_bridge:3057P/35F/468S/0NEW` → **`pl_bridge:3057P(진짜1135·구성상1608·부분314)/…`**.
   본문에 등식×증거력 pass 표 + `NOEQ`(등식으로 영원히 못 보는 항목) 건별 인쇄 추가.
2. **게이트 2f `TAX22_SOURCE_CROSSCHECK` 신설** — `|item22−item24| == |원천 법인세 계정|`.
   `ifrs-full_IncomeTaxExpenseContinuingOperations` 가 418/418 FS-API 캐시에 있는데
   `assemble()` 이 곧바로 잔차로 덮어써서 버려지고 있었다. 부호는 안 본다(발행사 관행이 갈리는
   것이 애초에 plug 를 도입한 이유). **전 버킷 시뮬레이션 선행**: 대조가능 282 · PASS 282 ·
   FAIL 0, 잔차 median=p90=max **0.000백만원**. 배선 후 게이트 `tax22_src:282P/0F/74S`.
   변이시험 탐지율 **0.0% → 100.0%**.
   - **오프라인·결정성이 이 배선의 어려운 부분이었다.** `resolve_corp()` 는 gitignore 된 30MB
     `CORPCODE.xml` 을 읽고 없으면 네트워크로 받아 환경마다 커버리지가 갈린다 → 골든이 흔들린다.
     추적 파일만 쓴다: `data/_derived/alotmatter_fetch_census.json`(KR→corp_code 39/39) +
     추적된 `data/dart/_fs_api_cache/`. 두 매핑 **36/36 일치 · 불일치 0** 실측.
     캐시 파싱은 `fetch_dart_fs._parse` 를 **그대로 호출**(재구현하면 게이트가 빌더와 다른 값을
     본다). `BASIS_CFS` 가 비어 있다는 전제도 코드로 확인한다.
   - **증명하지 못하는 것도 적었다**: 22·24·23 을 일관되게 잘못된 기준(연결 vs 별도)에서
     골랐다면 셋 다 같이 틀려 등식이 닫힌다. SKIP 74버킷의 item22 도 여전히 무검사.
3. **매니페스트 박제.** `tests/test_rule_coverage_manifest.py` PL 축 —
   `PL_CONSTRUCTIVE_BLIND`(5·6·9·10·11·19·23) · `PL_CONSTRUCTIVE_GUARDED`(3·4·8·17·20·22·24·25) ·
   `PL_DOWNSTREAM`(빌더 plug 재계산 표, 소스 문자열 대조). 검사면 = PL 을 읽는 차단성 룰 전부.
   **매니페스트 자신의 변이시험 3종 전부 발화**(`probe_20260829_pl_manifest_falsifiability.py`).
4. **item9 판정 = 대안 축 없음.** `CSM_waterfall.json` 2,172행 **6항목 단일 축, 출재 0**.
   `build_csm_waterfall_master.py` 가 전 단계에서 의도적 배제(`_EXCLUDE_KW`·캡션 필터·소수
   클러스터 drop)하고 **그 배제는 옳다** — 출재는 보유 재보험계약자산의 별도 워터폴이라
   `원수+재보험` 식은 346버킷 중 245건이 ±1% 밖, `원수+수재`는 20건. 원문에는 있으므로(캡션
   "원수 및 출재 …") 파서가 별도 마스터로 추출해야 하고, 그건 신규 과제라 명문화만 했다.
5. **`test_identity_tautology.py` 를 PL 에 배선하지 않는다 — 그것도 명문화.** 귀무모형이 각 항의
   등식 단위 반올림을 가정하는데 PL 은 원÷1e6 이라 **건전한 항등식도 잔차가 정확히 0** 이다.
   9축 전부 RED 이고 excess 1위(1.93)가 하필 진짜 검산 축 EQ9 였다. 판별자는 통계가 아니라
   **write-path 추적 + 변이시험**이다.

### 왜 이 형태로 남겼나

"무력한 줄 모르고 pass 를 세는 것"이 이 저장소가 반복해서 당한 false-green 의 정확한 형태다.
등식을 지우면 커버리지가 줄고, 그대로 두면 3,057 이라는 숫자가 계속 오독된다. **선언 + 인쇄 +
변이시험 박제**가 그 사이의 답이다 — 무검사라는 사실이 코드에 남고, 나중에 커버리지가 생기면
매니페스트가 갱신을 강제하고, 있던 커버리지가 사라지면 막는다.

### 골든/게이트

`master_tables_golden.json` `--update`(SUMMARY 한 줄, exit_code 2 불변). `test_identity_registry`
에 `tax22_source_crosscheck` 등재 — 그 파일의 `test_no_undeclared_threshold_constants` 가
**설계대로 즉시 실패해서** 등재를 강제했다(`EQ_TAUTOLOGY` 는 임계가 아니라 라벨이라 allowlist).
`validate_golden_input_fingerprints` **갱신 불요**(RED=0, 6 spec ok — SPECS `code_entries` 는
빌더만 추적하고 게이트는 골든이 매 실행 서브프로세스로 재실행해 stale 불가).
`validate_data_contract` RED=0 YELLOW=92 불변. 훅 경로: `validate_master_tables` 는
`test_master_tables_golden.py` 경유(`NOT_A_PUSH_GATE` 선언대로), `test_rule_coverage_manifest.py`
는 이미 훅 목록에 있다.

## 2026-08-29 (e) — leg-coverage 오탐: 등식이 재보험사의 4번째 LOB 다리를 몰랐다

발주 `inbox/parser/20260829T1700Z` §2 회신 재확인(parser commit `15a61d1`).
**어제 (c) 라운드에서 내가 신설한 leg-coverage 룰이 코리안리재보험 12분기를 오탐했다.**
데이터가 아니라 **룰**이 틀린 경우라 기록해 둔다 — 이 저장소의 사고 기록은 대부분 반대
방향(데이터가 틀렸는데 룰이 통과)이라, 반대 사례의 진단 경로가 남아 있는 편이 낫다.

### 무엇이 틀렸나

룰은 "item13(자동차) 결측이 1,456~53,464백만원을 싣고 있다"고 12분기 내내 찍었다. parser 가
전 분기 원문 XML 을 grep 하니 **자동차 LOB 자체가 없었다**(재무제표 표 안 "자동차" 0회 —
걸린 것은 관계기업 펀드명·임원 이력 문장뿐). 코리안리는 재보험사라 LOB 이 생명/장기/일반
3종이고, 네 번째 다리 item`2-1`(장기재보험 손익)이 마스터에 정상 발행돼 있는데
**검증 등식만 표준 3슬롯(2/13/14)이 LOB 의 전부라고 가정**했다.

**빌더는 이미 맞게 하고 있었다.** `build_pl_breakdown.py` L249-252 의 Tier-2 RC 게이트가
같은 항을 `_extra_lob` 으로 더한다. 즉 **빌더와 검증기가 서로 다른 등식을 쓰고 있었다** —
"게이트가 검사하는 것 ≠ 실제 계약" 의 한 변종이다. 새 룰을 만들 때 **같은 축을 이미 계산하는
빌더 코드가 있는지 먼저 읽으라**는 교훈으로 남긴다(있으면 그 식을 그대로 가져와야 한다).

### 조치 — 회사명이 아니라 항목번호 패턴으로

`load_pl_extra_lob()` 신설: `((co,q) -> Σ 항목번호 `2-N`, 미지 하이픈 항목 목록)`.
`load_long()` 이 **항목명**으로 색인해 항목번호를 못 보기 때문에 이 축만 번호로 따로 읽는다.
코리안리로 하드코딩하지 않은 이유는 단순하다 — 오늘 하이픈 항목을 가진 회사가 하나뿐이라는
사실은 **다음 재보험사가 들어오면 바뀐다**. 자식 `3-N`~`12-N` 은 그 다리의 하위 분해라
미가산(이중계상 방지).

### 실측 (코드 수정 **전** 356 버킷 전수 시뮬레이션 → 수정 후 게이트, 정확히 일치)

| | 수정 전 | 수정 후 |
|---|---|---|
| 2e LEG-COVERAGE 닫힘 | 18 | 30 |
| 2e LEG-COVERAGE 깨짐(LEGRED) | 34 | **22** |
| 2e 좌변없음(NOLHS) | 18 | 18 |
| pl_bridge | 3045P/47F/468S/0NEW | **3057P/35F/468S/0NEW** |
| 새로 깨지는 버킷 | — | **0건** |

코리안리 12분기 잔차 |≤2.8|백만원(lhs 5만~24만 백만원 → 상대 ~0.001%). 마스터의 `2-1` 은
14분기인데 판정이 바뀐 것은 12분기 — 나머지 2분기(2023.1Q·2023.2Q)는 item1 자체가 결측이라
NOLHS 로 남는다. **"12건만 바뀌었다"를 "2건이 조용히 숨었다"로 오독하지 않도록 14분기 전건을
따로 세었다**(`probe_20260829_coreanre_allq.py`).

### 하이픈 서브 LOB census — 이 라운드의 최대 산출

마스터의 하이픈 항목번호는 **코리안리재보험 단독**, 11종(`2-1`~`12-1`) × 14분기 = **154셀**
(루트·viz 동일, 항목명 충돌 0). 그런데 **그중 어떤 룰이라도 읽던 것은 `4-1`(수재 CSM상각,
`CSM_AMORT_PL_LEGS`) 14셀뿐이었다 — 나머지 10종 140셀은 어떤 룰도 순회하지 않았다.**
`2-1` 배선 후 남은 무검사는 9종 126셀.

**그 126셀의 부모-자식 3식은 일부러 배선하지 않았다 — 동어반복이기 때문이다.**
`2-1=3-1+8-1` · `3-1=4-1+5-1+6-1+7-1` · `8-1=9-1+10-1+11-1+12-1` 은 14/14 통과지만
**잔차가 전건 정확히 0.000000000** 이다. 원인은 핸들러다 — `pl_breakdown/companies.py::leg()`
가 `{2: suje+chuljae, 3: suje, 7: suje-csm-ra-yes, 8: chuljae, 12: chuljae-recsm-rera-reyes}`
로 item7·12 를 **plug**, item2 를 **합**으로 만든다. 배선했으면 126셀이 GUARDED 로 보이면서
실제로는 아무것도 검증하지 않는 **false-green 을 스스로 만드는 것**이었다. 무검사로 두되
무검사임을 기록하는 쪽을 골랐다.

> **"커버리지를 늘렸다" 와 "검증을 늘렸다" 는 다르다.** 룰을 추가하기 전에 잔차 분포를
> 먼저 보라 — 전건 정확히 0 이면 그 값은 공시값이 아니라 파생값이다.

### 미지 하이픈 census + 변이시험

등식이 아는 형태(`2-N` 가산 / `3-N`~`12-N` 자식) **밖의** 항목번호가 나오면 2e 가 `LEGUNK`
로 건별 인쇄한다(오늘 0건). **"0건" 이 "검사가 죽었다" 가 아님을 보이려고 변이시험을 붙였다**
— `probe_20260829_legunk_mutation.py` 5케이스 전부 PASS(`2-1` 가산 / 자식 미가산 / 가짜
`13-1` 발화 / `2-1`+`2-2` 복수 부모 합산 / 정수 항목번호 무영향).

### baseline · 골든 · 지문

`data/_gold/pl_bridge_baseline.json` 에서 코리안리 12건 삭제(`_promote` (1), 게이트가
`FIXED?` 인쇄). entries **47→35**, `등재부에만 남은 것 0`. 데이터 결함이 아니었으므로
documented exception 승격이 아니라 **삭제**다. `_counts` 도 실제 entries 로 재계산했다
(선언 52 vs 실제 47 로 이미 드리프트해 있었다).

`tests/fixtures/master_tables_golden.json` `--update`(SUMMARY 한 칸, exit_code 2 불변).
`tests/test_identity_registry.py` 의 `pl_bridge` statement/measured 갱신.
`scripts/prepush_check.py` 전체 **exit 0 / gate-clear**(RED=0 · offline 270 passed).

**`validate_golden_input_fingerprints.py` 는 갱신 불요** — RED=0, 6 spec 전부 ok. 그 게이트의
`SPECS` 는 **빌더**만 `code_entries` 로 추적하는데 이번에 고친 것은 게이트이고,
`test_master_tables_golden.py` 는 매 실행 게이트를 서브프로세스로 **재실행**하므로 구조적으로
stale 해질 수 없다(그래서 SPECS 에 없는 것이 맞다).

### 잔여

LEGRED **22건** — 전건 baseline 등재(`route: parser/ifrs17` · `deadline: 2026-10-31` · 신규 0).
예별손해 2024.4Q·2025.4Q item2(후보 표까지 특정, 폐쇄식 불일치로 미확정) · AIG 3분기 ·
신한이지 2분기(원문에 LOB 분해 표 자체가 없음) · 2023 다수(사이트 비노출, 미착수).

**곁가지(미조치, 기록용).** 같은 두 식을 **전 회사**로 돌리면 `3=4+5+6+7` 315건 중
284건(90.2%) · `8=9+10+11+12` 300건 중 258건(86.0%)이 잔차 정확히 0 이고 최대 잔차가
0.35·0.49백만원 = floor(200백만)의 **1/400** 이다. 이 두 식은 코리안리만이 아니라 저장소
전반에서 거의 동어반복으로 보인다. `2=3+8` 은 최대 잔차 10,169백만원이라 내용이 있다.
별도 조사 대상.

## 2026-08-29 (d) — 분기 지평이 하드코딩이라 게이트가 최신 분기를 순회조차 안 했다

발주 `inbox/validation/20260829T1910Z`. **`RED=0` 이 "검사했더니 깨끗" 이 아니라 "안 봤다"
였던 사고.** 2026.2Q 데이터를 라이브에 배포한 날, `validate_master_tables` 의 coverage
census · qoq · spike · wfy · continuity 와 `validate_data_contract` 의 census RED 스코프가
그 분기를 한 번도 방문하지 않았다.

### 원인 — 손으로 적은 분기 목록, 세 곳 + 죽은 것 하나

`validate_master_tables.QS` 는 이 파일 **최초 커밋 `9243445` 부터** `2026.1Q` 로 끝나는
리터럴이었다(파생이 멈춘 게 아니라 처음부터 리터럴). 같은 병:

| 위치 | 상수 | 가두고 있던 축 |
|---|---|---|
| `validate_master_tables.py` | `QS` | census · qoq · spike · wfy · continuity · `prev_quarter()`(→ OCI-vs-BS) |
| `validate_master_tables.py` | `FY_Q` / `PREV_CLOSE` / wfy-year | **두 번째 지평** — `FY_Q["2026"]=["2026.1Q"]` 이라 `QS` 만 고쳐도 연속성은 여전히 사각 |
| `validate_data_contract.py` | `_DISPLAY_QUARTERS` | census RED 의 **발화 스코프 전체**(`_emit` 24곳) |
| `validate_data_contract.py` | `QS` | 참조 0 = 죽은 값. 지평처럼 보이는 자리라 제거 |
| `validate_kics_rate_sensitivity.py` | `ALL_Q` | RS4 census. K-ICS 최신이 아직 2026.1Q 라 **미발현**(공시가 오면 조용히 건너뛸 자리) |

**이 저장소에서 배울 것 두 가지.**

1. **자물쇠가 직렬로 두 개일 수 있다.** `_DISPLAY_QUARTERS` 에만 2026.2Q 를 넣으면
   **델타 0** 이다 — IFRS17 hole 이 `validate_master_tables.coverage_holes`(→ 그쪽 `QS`)를
   거쳐 오기 때문. "게이트 A 의 스코프를 열었다" 는 "그 축이 검사된다" 가 아니다.
2. **알고도 정본을 안 고치면 그게 재발 구조다.** `validate_data_contract` 안의 두 검사
   (배당 L2275 · CSM 연속성 L2519)가 주석에 *"`_DISPLAY_QUARTERS` 는 2026.2Q 를 아직
   포함하지 않는다"* 고 적어 놓고 **자기만 `_in_scope` 를 비켜갔다.** 개별 우회가 두 번
   쌓이는 동안 정본은 그대로였다.

### 실측 (지평 확장 전 → 후)

```
validate_master_tables --no-build (exit 2 불변)
  coverage_hole 0CSM/0PL → 0CSM/1PL   ← HOLE-PL 흥국화재 2026.2Q (부분)
  qoq_warn        211Y → 235Y  (+24, 전부 2026.2Q)
  oci_vs_bs_aoci   13Y →  14Y  (+1, 에이비엘생명 2026.2Q)
  plausibility(dup/spike/cont/wfy/zamort) · closing · pl_bridge · csm_amort · sens = 변화 0
validate_data_contract   RED 0→1, YELLOW 92 불변 (exit 0→2)
  RED [PL_breakdown] MASTER_HOLE  흥국화재 2026.2Q
```

RED 원인: 흥국화재 2026.2Q PL 항목 **2/8/12/13/14** 결측(직전 2026.1Q 는 전부 정상 = 최신
분기 회귀). 자식 item9/10/11 은 살아 있고 부모 item8·item12 만 비어 산술로도 못 닫는다.
raw 는 디스크에 있고 라벨 빈도도 2026.1Q 와 같다 → **추출 실패**, refetch 아님.
`inbox/parser/20260829T2010Z` (`lane: ifrs17` · `route: reparse`) 발주. **push 는 이 RED 으로
막혀 있다** — documented exception 감이 아니라 fixable 이다.

서울보증보험도 같은 3항목 중 생명장기손익이 없지만 hole 이 아니다: 핵심항목 보유 분기 6개
(<`active_min`=7)라 `struct` 로 분리되고, 보증보험이라 생명장기 leg 자체가 없다
(`ZLEG_LEGIT["서울보증보험"]="ALL"`). 카테고리 추론이 아니라 회사별 실데이터로 확인.

### 조치 — `scripts/_quarter_horizon.py` (파생 정본)

- 하한 `2023.1Q` **고정**(데이터 파생하면 `IFRS17_BS` 의 2021.4Q 까지 끌려와 허수 hole).
- 상한 = 마스터 **5개**의 `공시분기` high-water mark. **한 마스터에서만 파생하면 안 된다** —
  그 마스터가 최신 분기를 통째로 빠뜨렸을 때 지평도 같이 줄어 결측이 안 보인다(자기참조 사각).
- `"공시분기"` 필드만 읽는다(파일 전체 정규식은 `비고` 산문의 분기까지 주워 지평이 허수로 는다).
  실측 81ms.
- `display_quarters()` = owner 스코프의 **규칙**(연말 전부 + 2025.1Q 이후 전부)을 파생 →
  종전 7개를 정확히 재현. 회귀 가드 테스트 있음.

### 트립와이어 — 배선했고, 변이시험으로 확인했다

`tests/test_quarter_horizon.py`(17 tests) → `prepush_check.py` `fast` 목록에 등록.
① 파생 지평이 마스터 최신 분기를 품는가 ② 게이트 상수가 최신 분기를 담는가
③ `_DISPLAY_QUARTERS` 가 최신 분기를 담는가 ④ 게이트가 리터럴 지평을 다시 심지 않았는가
(AST — `QUARTER_FLOOR` 에서 시작하는 분기 컬렉션만 잡아 (회사,분기) 예외 등재부는 통과).
**변이시험**: `QS` 를 옛 리터럴로 되돌리면 ②④가 FAIL, 되돌리면 17/17 통과.

### 다른 게이트 census (AST, 주석·독스트링 제외)

지평형 하드코딩은 위 3파일뿐. 나머지 8개 게이트 + `kics_json_rules` 는 데이터 파생이고 남은
분기 리터럴은 전부 (회사,분기) 예외 등재부다. `validate_kics_disclosure.SPOT_QUARTER` 는
단일 spot-check 앵커, `validate_nb_csm_multiple` 의 `2024.4Q` 는 FY2024 IR 앵커(고정이 맞다).
재현: `scripts/_probes/probe_20260829_gate_horizon_audit.py`.
**미조치(게이트 아님, 기록용)**: `scripts/_csm_goldmap.py` L20 · `_csm_status_matrix.py` L29 가
`QS = [q for q in QS if q != "2026.2Q"][:13]` 로 2026.2Q 를 명시 배제한다 — 리포트 헬퍼라
push 를 막지 않지만 그 리포트엔 최신 분기가 없다.

### 골든 / 지문

`tests/fixtures/master_tables_golden.json` `--update` 재생성(위 SUMMARY 3칸, exit_code 2 불변).
`validate_golden_input_fingerprints.py` 는 **갱신 불요** — 빌더 미변경, 실행 결과 6/6 ok RED=0.

## 2026-08-29 (c) — 등식은 있었다. 도망간 것은 결측 처리였다 (보험손익 leg-coverage)

발주(`inbox/validation/20260829T1500Z`)는 *"`PL_EQS` 9식에 `보험손익` 폐쇄식
`1 = 2+13+14+15−16` 만 없다. item13·14·15·16 이 통째로 틀려도 상위 등식은 전부 닫힌다"* 였다.
**전제는 틀렸고 결론은 맞았다 — 원인이 달랐다.**

### 1) 전제 정정 — 그 등식은 파일 최초 커밋부터 있었다

`PL_EQS` 안이 아니라 **그 바로 위 dual-form 블록**에 있다(수정 전 L563-580, 라벨
`보험손익(dual)`). `git log -L563,581:scripts/validate_master_tables.py` → 최초 커밋
`135e6ff`. 실패 10건은 이미 `data/_gold/pl_bridge_baseline.json` 에 건별 등재돼 있었다.
발주가 인용한 KB손해보험도 *"item16 이 전 분기 None"* 이 아니라 **14분기 중 6분기만 None**
이고, 2025.4Q 잔차는 *"반올림 1억"* 이 아니라 백만원 원장에서 **정확히 0.0**
(`773,945 − 107,694 − 39,556 = 626,695 = item1`). 억원으로 반올림해 손으로 재서 생긴 착시다.

> **교훈: `PL_EQS` 같은 선언 테이블만 읽고 "그 축은 무검사" 라고 결론내지 말 것.**
> 특수 케이스가 루프 밖에 손코딩돼 있을 수 있다. 등식의 유무는 **테이블이 아니라 실행**으로
> 확인해야 한다(전 버킷 판정 census).

### 2) 진짜 사각 — 결측을 만나면 등식이 버킷을 통째로 버렸다

```python
if bo is None or any(x is None for x in lob):
    pb_skip += 1          # 356 버킷 중 71 (19.9%)
```

그리고 그 결측은 **coverage census 도 못 봤다.** `coverage_holes` 의 `key_items` 는
`보험손익 / 생명장기손익 / 당기순이익` 셋뿐이라 **13(자동차)·14(일반) 의 결측은 애초에 세지
않는다.** 두 검사가 같은 구멍을 공유했고, 그래서 **코리안리재보험은 13분기 내내 `item13` 이
없는 채로 양쪽을 다 통과**했다 — 형제 다리 `item14(일반)` 는 정상 추출되는데도.

실측(전 버킷 356, `scripts/_probes/probe_20260829_item1_skip_zerofill.py`):
SKIP 71 을 0-fill 로 재판정하면 **13 닫힘 / 40 깨짐 / 18 좌변없음**.
깨진 40건 잔차 median 43,415 · p90 251,088 · max 454,352 백만원 — **합계 3.4조원(34,438억)이
어떤 룰의 시야에도 없었다**(2024+ 22건). 그중 **30건은 coverage census 도 구조적으로 못 잡는다.**

### 3) 조치 — 새 등식이 아니라 결측 처리 확장

등식을 한 벌 더 만들면 같은 식이 두 개가 되고 둘이 어긋날 자리가 생긴다. dual-form 의
**결측 분기만** 고쳤다: **결측 LOB 다리를 0 으로 채워 판정한다.** 닫히면 PASS(그 다리는 정말
0), 깨지면 FAIL(잔차 = 미검사 금액의 하한). 라벨 `보험손익(leg-coverage)`.

**결측 처리는 SKIP 도 무조건 RED 도 아니고 "산수로 판정" 이다.** SKIP-on-missing 이 검증
무력화인 것은 맞지만(40건이 그 증거), 무조건 RED 도 틀리다 — 13건은 0-fill 로 **정확히**
닫힌다(NH농협손해 12분기 잔차 ±1.0 이내). 정당한 0 을 결함이라 부르면 룰이 두더지가 된다.
카테고리("손보니까 자동차가 있다")로 추론하지 않고 회사별 실데이터가 판정하게 두는 형태이며,
코리안리를 잡아낸 것이 정확히 그 덕분이다.

`item1`(좌변) 결측 18건은 등식이 성립하지 않으므로 FAIL 로 올리지 않되 `NOLHS` 로 건별
인쇄하고, 오늘 전건이 2023 분기이므로 **2024+ 가 하나라도 뜨면 회귀 경고**를 찍는다.

### 4) 적용 전 시뮬레이션 = 회귀 0건 (필수 절차)

`scripts/_probes/probe_20260829_item1_legcoverage_final.py` 가 old/new 판정을 버킷별로 대조 —
**오늘 검사받던 285 버킷의 판정이 한 건도 바뀌지 않는다.** 0-fill 경로에 기타영업수익·
기타사업비용 후보를 **추가하지 않았다**(masking 면 확대 방지, 실측상 불필요 — 13건 전부 기존
adj 로 닫힘).

게이트 실측: `pl_bridge:3025P/13F/522S/0NEW` → `3038P/53F/469S/0NEW`, `exit=2` 전후 동일.
드러난 40건은 `pl_bridge_baseline.json` 에 **건별** 등재(13→53, class 4종, 기한 2026-10-31) —
통째 skip 이 아니라 F 로 계속 계상되고, 등재 밖 실패는 `NEW` 로 push 를 막는다.
**마스터 데이터는 한 셀도 안 건드렸다.** 전건 parser/ifrs17 발주
(`inbox/parser/20260829T1700Z__validation__MULTI__pl_item1_leg_coverage.md`).

### 5) 훅 배선 — "배선했다 ≠ 강제된다" 재확인

`prepush_check.py` 는 `validate_master_tables.py` 를 **직접 부르지 않는다.** 강제점은
`tests/test_master_tables_golden.py`(SUMMARY+exit 박제)이고 그것은 훅 `fast` 묶음 **L167 에
실제로 있다**. `tests/test_identity_registry.py` 도 **L179 에 있다** — 허용오차를 몰래 넓히면
`tol_from` 대조에서 막힌다. 그 registry 의 `pl_bridge` 항목에 leg-coverage 를 `statement` ·
`measured` 로 등재했다. 새 임계 상수는 안 만들었다(`DEFAULT_FLOOR` 재사용).
`test_rule_coverage_manifest.py` 는 K-ICS 전용이라 PL 축이 없어 손대지 않았다.
지문 게이트는 빌더 전용이라 `--update` 불요(`RED=0 → clear` 확인).

### 6) 남은 사각 — `QS` 가 2026.1Q 에서 끝난다

`validate_master_tables.QS` 는 `2026.1Q` 까지인데 마스터에는 `2026.2Q` 가 있고 **24버킷**이 그
밖에 있다. `QS` 를 도는 검사(coverage census · `qoq_scan` · `net_quarterly`/`prev_quarter`)는
**최신 분기를 통째로 안 본다.** PL_BRIDGE 는 `pl.items()` 를 직접 돌아 무관(그래서 코리안리
2026.2Q 도 잡혔다). `QS` 확장은 여러 룰의 판정을 동시에 움직여 전 버킷 재시뮬이 필요하므로 이
티켓에서 손대지 않고 오케스트레이터 판단으로 넘겼다.

## 2026-08-26 (b) — 요청받은 면제를 거부하다: "원천에 없다"가 틀렸고, 사각 12건에 룰을 놨다

오케스트레이터가 `inbox/validation/20260826T2000Z` 로 **documented exception 등재**를 요청했다
(악사손해 2023.4Q `PL_CSM_AMORT_VS_WATERFALL`, "어느 DART 문서에도 그 값이 없다"). 등재하면
그 한 건이 push 를 여는 자리였다. **등재하지 않았다 — 실측해 보니 값이 디스크에 있었다.**
게이트는 여전히 `RED=1`, prepush `exit 2`. 이게 맞는 상태다.

### 1) 면제 반려 — 판별 키워드가 성공 사례에서도 0회였다

발주문과 그 앞 두 티켓(`_resolved/20260826T1200Z`)은 *"PL Tier-2 가 쓰는 '계약유형별 보험수익/
보험서비스비용' 노트는 사업보고서 본문에만 있고, 악사는 비상장이라 사업보고서가 0건 → 값이
존재하지 않는다"* 로 결론냈다. 사업보고서 0건은 사실이다. **틀린 것은 그 다음 고리다.**

첫 반증: `계약유형별` 은 악사 필링에 **2023·2024 양쪽 다 0회**인데 **2024.4Q 는 추출에
성공한다**(원수CSM상각 26,340.86백만원). 성공하는 필링에도 없는 단어를 부재의 근거로 쓴 것이다.

악사의 실제 소스 표는 `'보험손익 상세내역'` 이고, 이미 받아 놓은 감사보고서 첨부 안에 있다:

```
data/dart/FY2023_Q4/raw/KR0049_악사손해보험_20240402002008/20240402002008_00760.xml
  '(5) 보험손익 상세내역 (단위: 천원)1) 당기'    <- 2024.4Q 는 '(6) ...' (번호만 다르다)
  구분 [자동차|일반|장기|합계] · 40행
  당기손익으로 인식한 보험계약마진 금액 · 장기 = 22,272,512천원 = 222.7억
```

**222.7억 = 게이트가 인쇄하던 그 워터폴 상각액이다.** 그리고 그 표는 **마스터에 이미 있는**
Tier-1 두 셀과 원 단위로 닫힌다 — `총 보험서비스결과 합계 11,957,786천원` vs
`보험손익 5,842.899358 + 기타사업비용 6,114.887984 = 11,957.787342백만원`(Δ 1,300원).
파생값 대입이 아니라 같은 표를 같은 핸들러로 읽는 것이다.

근본원인까지 특정했다(`scripts/_probes/probe_20260826_axa_tier2_extract.py`):

| | 2023.4Q(실패) | 2024.4Q(성공) |
|---|---|---|
| `t.header` | **`[]`** | `[['구 분','자동차','일반','장기','합계']]` |
| `t.rows[0]` | **`['구 분','자동차','일반','장기','합계']`** | `['보험수익']` |
| 반환 | **`{}`** | `{4: 26340.86, ...}` |

`companies.py::extract_tier2_axa` 의 `for hr in note.header:` 가 한 바퀴도 안 돌아 `col` 이
`None` 인 채 `if not col or "jang" not in col: return {}` 로 빠진다. 2차 결함: 섹션 라벨이
2023 은 `재보험수익`/`재보험비용` 인데 `_AXA_SEC` 는 `출재보험수익`/`출재보험비용` 만 맵핑한다.
→ `inbox/parser/20260826T2200Z`(lane ifrs17 · route reparse) 로 기대값 13셀 + 정합식 3개 첨부.

> **이 저장소 관행에 남길 것: 키워드 0회는 원천 부재의 근거가 아니다.** 이미
> `feedback_keyword_absence_is_not_source_absence` 로 3인 연속 오판 전례가 있고(흥국생명 스캔본),
> 이번은 그 XML 판이다. **판별기는 성공 사례로 먼저 교정하고 세라** — 교정 안 된 탐지기의
> 음성은 정보가 0 이다.

### 2) 사각 12건 — 룰 `3z-b` 신설 (`PL_BUCKET_ABSENT_VS_WATERFALL`)

룰 3z 는 `for (co,q), m in sorted(env.pl.items())` 로 돈다. **PL 에 버킷이 통째로 없으면
루프가 방문조차 못 해 완전 침묵한다.** 악사가 RED 로 뜬 유일한 이유는 그 회사만 PL 버킷이
부분적으로 존재해서다 — 더 나빠서가 아니라 **보여서**다. 실측: 워터폴 상각 ≥ 10억인데 PL
버킷이 없는 자리 **12건**, 그중 **삼성화재 2023.1Q 는 3,760.4억**이다. 이 룰이 태어난 사고
(2026-08-15 삼성화재 2026.2Q PL 생명장기 분해가 통째 null 인 채 라이브 배포)와 **같은 회사·
같은 모양**인데 룰이 조용했다.

`check_cross_source` 에 3z 바로 뒤로 **워터폴 쪽 census** 를 배선했다:

| 룰 | 심각도 | 조건 |
|---|---|---|
| `PL_BUCKET_ABSENT_VS_WATERFALL` | RED | 상각 ≥ 10억 · PL 버킷 부재 · baseline 미등재 |
| `PL_BUCKET_ABSENT_BASELINE_DRIFT` | RED | 박제한 워터폴 상각이 tol(0.5억/5%) 밖으로 이동 |
| `PL_BUCKET_ABSENT_BASELINE` | YELLOW | 등재된 기존 결손 |
| `PL_BUCKET_ABSENT_BASELINE_INERT` | YELLOW | 버킷이 생겼다/임계 아래 → 줄을 지워라 |

등재부 `data/_gold/pl_amort_coverage_baseline.json`(신규) — 12건 건별 열거 + 워터폴 상각 박제
+ status + raw 경로 + 라우팅. 로더 `csm_amort_coverage_baseline()` 은 **파일이 없으면 빈
등재부 = 전부 RED** 로 읽는다(등재부를 지우면 검사가 느슨해지는 형태를 막는다).

기존 12건은 main(라이브)에도 이미 없는 선행 결함이라 비차단으로 뒀다 — 이번 브랜치 회귀가
아니다(main PL 354버킷 → 브랜치 356, 사라진 버킷 0). **면제가 아니라 래칫이다**:
`statutory_reserve_baseline.json` 과 같은 계약이고, `_CSM_CONTINUITY_EXCEPTIONS` 가
2026-08-25 에 실격당한 '버킷 통째 무조건 통과' 형태가 되지 않도록 매 실행 재검산한다.

전 버킷 시뮬레이션 + 변이 6종 **ALL PASS**
(`scripts/_probes/probe_20260826_coverage_rule_simulation.py`):
평시 RED 0 / YELLOW 12 · M1 등재 줄 삭제 → RED 1 부활 · M2 박제값 변조 → DRIFT RED ·
M3 버킷 생김 → INERT · M4 새 결손 → RED 차단 · M5 스코프 누출 0.
selftest 에 `L3`(사각 검출) · `L4`(임계 아래는 결함 아님) 신설 → **57/57**(종전 55).
`M1 CSM_SIGN_CONVENTION` 픽스처는 PL 버킷이 없어 새 룰이 정당하게 같이 터지길래 PL 버킷을
줘서 부호룰 단독 측정으로 되돌렸다.

### 3) 판정을 확정한 것과 보류한 것

**확정 — 삼성화재 2023.1Q 는 진짜 구멍.**
`FY2023_Q1/raw/KR0008_삼성화재해상보험/xml/20230515002508.xml` 의
`'(10) 당분기와 전분기 중 주요 보종별 보험수익 및 재보험비용의 내역 · 1) 제74(당)기 1분기'`
에 `보험계약마진 상각 376,038백만원`(=3,760.38억)이 있다. 2023.2Q 이후는 같은 노트가
`'당반기와 전반기 …/제74(당)기 반기'` 표기이고 그쪽은 성공한다 → 분기(1Q) 어미 변형 미탑재.

**보류 — 나머지 11건은 `UNADJUDICATED` 로 등재.** 발주문은 감사보고서-only 4사(AIA·
아이엠라이프·하나손해·교보라플)를 "악사와 같은 사유면 legit-absent" 로 제안했으나 그 사유가
①에서 무너졌고, 내 노트 판별기는 **대조군 7건 중 5건이 위음성**이었다(추출에 성공한 버킷을
"노트 없음"으로 셌다). 교정 안 된 판별기로 legit-absent 를 등재하는 것은 근거 없는 면제다.
정황상 2023.1Q 축 결손 4사는 셋 다 같은 방향을 가리킨다 — raw 는 디스크에 있고, 2023.1Q 에
PL 을 가진 **19사 전원**이 Tier-2 가 채워져 있으며, 그 4사도 2023.2Q 는 채워져 있다.

### 측정치

- 게이트 `SUMMARY RED=1 YELLOW=92`(종전 RED=1 YELLOW=80 — 사각 12건이 올라옴)
- prepush **exit 2** · `gate RED=1 · K-ICS rule gate=clear · domain gates=pass ·
  DART raw 유실=0 · inbox 기계적위반=0 · offline tests=pass → BLOCKED`
- 오프라인 테스트 **230 passed · 1 skipped**. 골든 해시는 하나도 안 건드렸다(룰만 추가라
  산출 불변). 마스터 JSON 은 **한 셀도 안 고쳤다** — 고친 것은 게이트 2파일 + selftest +
  신규 등재부 1개다.

## 2026-08-26 (a) — answered 4건 전건 종결: 게이트 룰 갭 2곳을 실측으로 조이다

내가(그리고 parser 가) 보낸 `answered` 4건을 재확인해 **전부 resolved** 로 닫았다. 마스터
JSON(`CSM_waterfall.json` · `PL_breakdown.json`)은 한 셀도 안 고쳤다 — 재확인 세션이고 PL 은
병렬 세션이 작업 중이었다. 고친 것은 게이트 2곳 + 등재부 2종 + 골든 1개다.

### 1) `csm_steps_dart_vs_ir` — 축이 살아났는데 허용오차가 데이터보다 1,700배 넓었다

IR 파싱본 6개(`data/ir/*/parsed/`)가 들어오면서 이 축이 처음으로 실제 대조를 한다:
**36 step-pair, RED 0.** 종전엔 `check_cross_source` docstring 이 "IR JSON 미납품, validation
V1 SKIP" 이라고 적힌 채였다.

문제는 그 다음이다. 실측 잔차는 **전건 |Δ| ≤ 0.055억**(worst Δ/tol 0.0006)인데 허용오차는
`max(5%, 100억)` — IR 파싱본이 하나도 없던 시절의 추정치였다. 그 밴드는 **자기가 잡으라고
만들어진 결함을 통과시킨다**: 커밋 `8a3b930` 이 삼성생명 2026.2Q 를 연결로 옮겼을 때 6항목
Δ 는 69.6~1,043.9억이었는데 전부 밴드 안이다(상각 Δ187.6 < tol 366.8) → **0/6 검출**.

전 후보 시뮬레이션(live 36건 + 누출 6건, 양방향):

| tol_rel | tol_abs | live RED/36 | leak 검출/6 | worst Δ/tol |
|---|---|---|---|---|
| 0.05 | 100.0 | 0 | **0** | 0.0006 (종전) |
| 0.01 | 10.0 | 0 | 4 | 0.0040 |
| **0.005** | **1.0** | **0** | **6** | **0.0188** (채택) |
| 0.0005 | 0.1 | 0 | 6 | 0.1879 |

`IR_STEP_TOL_REL = 0.005` · `IR_STEP_TOL_ABS_EOK = 1.0` 을 모듈 상수로 빼고
`tests/test_identity_registry.py` 의 `tol_from` 에 배선했다(종전 `tol_from: []` 이라 선언과
코드가 갈라져도 아무도 못 잡았다). 레지스트리의 옛 사유 *"IR 은 잠정치이거나 연결이고 DART 는
확정·별도일 수 있다"* 는 폐기했다 — IR = 별도가 문서 라벨로 확정됐고(삼성생명 `CSM 상세 (별도)`,
한화생명 `※ SAP 기준(별도)`) 마스터도 별도라 **같은 숫자여야 한다.** `kind` 는 RANGE 유지
(원천마다 인쇄 정밀도가 다르다).

### 2) PL 생명장기 등식이 발행사 표의 세 번째 다리를 안 보고 있었다

`20260825T1120Z` §4 의 3건(교보라플 2024.4Q · BNP카디프 2024.4Q/2025.4Q)이 "데이터가 아니라
룰 갭" 이라고 넘어왔다. raw 로 확정했다 — 교보라플 `20250328001411_00760.xml` `(단위 : 원)`:

```
Ⅰ. 보험손익 (26,015,543,184) = 1.보험영업수익 19,825,745,982 − 2.보험서비스비용 45,841,289,166
   원수  19,783,534,758 − 37,629,857,356 = −17,846,322,598 = item3
   재보험     42,211,224 −  1,950,010,570 =  −1,907,799,346 = item8
   (3) 기타사업비용 6,261,421,240          ← 원수·재보험과 나란한 세 번째 다리
   item3 + item8 − 기타사업비용 = −26,015,543,184 = item2   (원 단위까지)
```

`보험손익(dual)` 이 이미 쓰던 bare/adj 패턴을 `생명장기손익` 층에도 준다(`PL_EQ_ADJ` 신설).
전 버킷 시뮬레이션 **3 닫힘 · 파손 0 · 잔존 0**(309/3 → 312/0). 비용도 기록했다: min-|잔차|
후보라 통과 버킷은 못 깨지지만, **잔차가 하필 기타사업비용과 같은 크기인 미래의 추출결함은
통과시킨다.** 등재부에서 `sub_leg_gap` 3건 삭제(16 → 13건).

### 3) 원장이 두 시간 만에 화석이 됐다 — 답변이 박제한 수치의 유효기간

`20260825T1520Z` 답변은 `pinned=22 fail=0 stale=0` 을 재현 명령과 함께 박제했다. 그 값은
커밋 `b2293c8` 시점 것이고, **같은 레인의 다음 커밋 `8c1666b`(PL 을 별도로)가 두 시간 뒤에
11건을 저절로 닫았다.** 실측 `common=346 pass=335 pinned=11 stale=11`.

닫힌 11건 = 삼성생명 5분기 + 신한라이프 6분기. 신한라이프 2026.1Q/2Q 는 내가 iter2 반려문에
"연결·별도 차일 가능성이 매우 높다"고 적은 가설이 그대로 확인된 것이다. FIXED 11줄을 지우고
`_population` 갱신 · 남은 삼성생명 5분기 note 에 "이 분기는 8c1666b 범위 밖, 고칠 대상은 PL"
을 명시했다. `validate_data_contract` YELLOW 96 → 85.

**교훈**: 답변의 게이트 수치는 커밋 시점 스냅샷이다. 재확인은 그 수치를 믿지 말고 다시 재야
한다 — 특히 같은 레인에서 병렬 커밋이 흐를 때.

### 4) census 판정 재검증 — raw 로 직접 갈랐다

- **삼성생명·신한라이프 84셀 = 확인.** 3-way 셀 대조(`8a3b930^` / `8a3b930` / 워킹트리,
  키 2,148 전건 일치): 값 84셀 · 값_당분기 84셀 · 2개사. 한화생명·현대해상 세 대조 전부 0셀.
- **교보생명 미복원 = 옳다, 사유는 틀렸다.** parser 는 "당기/전기류 후보선택 버그" 라 했는데
  `20230515002764.xml`(54,435줄)에서 절 마커로 가르면 버린 105,807 은 **연결재무제표 주석**
  (line 19282), 채택한 104,567 은 **재무제표 주석=별도**(line 38283) — 삼성생명과 같은 축이고
  문서 순서만 반대다. 그리고 이 회사는 **gold override 로만** 고쳐져 픽커는 여전히 연결을
  선호한다. census 의 "나머지 33사 판정불가" 를 낙관적으로 읽으면 안 되는 이유다.
- **코리안리 판정불가 = 맞다.** PL 과 맞는 값 70,611(FY2023_Q2) · 92,311(FY2023_Q3)이
  연결·별도 **양쪽 절에 같은 숫자로** 인쇄돼 있다. 재보험사라 이 줄의 연결효과가 0이다.
- **gold `set` 30셀 제거는 반대.** `csm_waterfall_master_diag.json` mtime **2026-08-17** 로
  stale — AIG 2025.4Q 기말이 아직 928,075.0(1000배)이다. `build_csm()` 은 diag + gold overlay
  라 지금 지우면 그대로 되돌아간다. diag 재생성(owner 승인) → 삭제 → 산출 동일 확인 순서.

### 5) 못 닫은 것 (후속 `inbox/parser/20260826T0500Z`)

① 삼성생명 item3/item4 **10셀**이 `8a3b930^` 와 다르다 — parser 답변의 "결과적으로 일치" 는
틀리다. 두 항이 정확히 상쇄돼 closing 항등식은 안 깨지지만 `이자부리`는 화면 계열이고
2024.4Q 에서 70.1억이 움직였는데 **어느 원천으로도 확인이 안 된다**(워터폴이 상품라인 3블록
합이라 단일 인쇄값 대조 불가, IR 은 그 5분기 미포함). vintage 혼재(stale diag vs 새 실행)가
유력.
② 삼성생명 PL 5분기가 아직 연결 — 반기(2Q) 필링 전부 + FY2024 분기. 2026.2Q 는 IR 파싱본이
별도 −7,336.61 / 연결 −7,524.2 를 둘 다 명시해 **확증**된다.
③ diag stale + `_LXML_LINE_NO_SENTINEL` 죽은 상수.

### 6) 그밖에 기록만

- IR 파싱본 5개가 근거 티켓으로 `20260825T2300Z…` 를 인용하는데 **그 파일은 없다**(실제는
  `20260825T1415Z`). provenance 사슬이 없는 곳을 가리킨다.
- `_UNIT_TO_UDIV` 에 `억원`(0.01)·`십억원`(0.001)이 있어 `lit-doc`(문서 최다) 경로가 그걸
  뽑으면 100~1000배가 난다. 지금 68건 전부 값 불변이라 실현되진 않았다.
- `user_csm_cells.json` `set` 277건 중 `why` 빈 항목 **44건**(KR0003 12 · KR0072 5 · KR0079 27).

### 7) 티켓을 닫자 게이트가 막혔다 — 두 개를 같이 고쳤다

4건을 `_resolved/` 로 옮기고 prepush 를 돌리니 **exit 2** 가 났다. 원인 둘:

- `test_identity_registry.py` 의 `36_irr` `documented_widening.ticket` 이
  `inbox/parser/20260825T1520Z…` 를 가리키는데 그 파일을 내가 옮겼다. 검사 자체는 옳다
  ("없는 파일을 가리키는 면제는 방치다"). 하지만 **티켓이 종결되면 옮겨지는 것이 정상 수명주기**라
  그때마다 게이트가 막히면 "닫으면 막히니 닫기를 미루자"가 된다. 경로를 `_resolved` 로 갱신하고,
  검사가 **활성·_resolved 양쪽을 보도록** 고쳤다(어느 쪽에도 없으면 여전히 FAIL).
- 그 실패를 **prepush 가 보여주지 못했다.** `subprocess.run(..., encoding="utf-8")` 리더가
  pytest 의 한국어 assert 메시지(콘솔 cp949 바이트 0xb7)에서 죽어 stdout 이 통째로 사라지고
  "offline tests=FAIL" 만 찍혔다. 실패 이유를 못 보여주는 게이트는 나쁜 게이트다 —
  `errors="replace"` 를 붙였다(2곳). 정상 통과할 때는 안 드러나던 자리다.

등재부 2종의 `routed` 포인터 14개도 `_resolved` 로 재지정했다(강제되지 않지만 다음 세션이 읽는다).

### 재현

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_master_tables.py --no-build
#   pl_bridge:2518P/13F/317S/0NEW · csm_amort_identity:335P/11PIN/0F/0S (stale 0)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
#   RED=0 YELLOW=85 · cross_source comparable (DART↔IR CSM steps): 36 step-pairs checked
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825b_csm_unit_fix_simulation.py
#   same=293 changed=8 both_none=30 (파손 0)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/prepush_check.py
#   PRE-PUSH VERDICT: gate-clear (exit 0, offline tests 230 passed/1 skipped)
```

## 2026-08-25 (f) — answered 3건 재확인: CSM 워터폴이 연결로 넘어간 회귀 적발 · 불변식 1번 배선

내가 sender 인 `answered` 3건을 재확인했다. **A·B 반려(iter++) · C 종결.** 마스터 데이터는
한 셀도 안 고쳤다(재확인 발주). 고친 것은 내 소유 게이트 파일 하나뿐이다.

### 티켓 A `20260825T1520Z` (CSM 상각 항등식 28버킷) — 반려

오케스트레이터 대필 답변이라 평소보다 세게 봤고, **전제가 틀렸다.**

- **답변이 서술하지 않은 변경 2개.** 커밋 `8a3b930` 의 빌더 diff 는 세 곳인데 답변은
  `pick_pattern2` 한 곳만 적었다. 나머지 둘은 `pick_combined_agnostic` 안의
  `code == "KR0069"` 워커 우선 · `code == "KR0094"` 65535 드롭 = **회사코드 하드코딩**.
  코드 주석에만 있는 더 큰 회귀 사실("blanket 적용 시 11~12 other companies 회귀")이
  답변에도 커밋 메시지에도 없다.
- **회귀 범위는 깨끗하다.** `waterfall_for_dir` read-only import 로 신·구 코드
  426 company-quarter 전수 스윕 → 변화 **14/426**, 회사 2곳뿐. 한화생명·현대해상 무변화.
  마스터 실변경은 `값` 126 + `값_당분기` 132 = **258**셀(답변의 126 은 `값` 만).
- **그런데 그 14건이 전부 잘못된 방향이다.** "line_no 65535 손상 near-repeat" 은
  손상 사본이 아니라 **`연결`(consolidated) 주석**이다. 파일별 grep:
  삼성생명 FY2024 `_00760`(감사보고서=별도)에 1,369,541 · `_00761`(연결감사보고서)에
  1,393,380 / 신한라이프 FY2025 별도에 6,969,672 4회, 커밋이 고른 6,972,351 은 별도에 0회.
  두 값 차 2,679백만이 2024.4Q(7,226,793−7,224,114)와 같은 상수 = 연결효과.
  `blocks_for_dir` 는 `_00761` 만 버리는데 **본문 XML 이 두 기준을 다 담고 있다.**
- **PL_breakdown 이 연결 기준**(삼성생명 1,393,380 / 1,384,276 · 신한라이프 735,862 /
  732,881 전부 `_00761` 에만 존재). 항등식 깨짐은 워터폴 오추출이 아니라 **기준 불일치**였고,
  이번 수정은 워터폴을 연결로 옮겨 등식을 닫았다.
- **삼성생명은 혼합 기준**(item1/item6 별도 앵커 + item2~5 연결). 항등식은 닫히지만 어느
  공시에도 없는 조합이다.
- **회귀 확인**: 티켓 B 가 닫은 신한라이프 FY 경계가 Δ=+26.8 로 재개방 + 2026 경계 2건 신규.
  경계 census 231/20/1 (답변 보고 233/18/1 재현 안 됨).
- 남은 8건: DB손해 `RESTATEMENT_BASIS` **근거 raw 확인**(311,850 이 2024.1Q 필링에만 존재) ·
  미래에셋 "불가능" 논증은 과장이고 raw 확정 불가 + 루트값이 `why` 없는 gold override ·
  하나생명 충돌 재현(Δ+57.2, 단 인과 서술 부정확 → `RESTATEMENT_BASIS` 재분류 권고) ·
  `UNRESOLVED` 4건은 정직하게 적혔다.

### 티켓 B `20260825T1340Z` (FY 기초 4사) — 반려

- **신한라이프 별도 판정은 옳다.** raw 로 검산(별도 = `_00760` 감사보고서, 연결 =
  `_00761` 연결감사보고서; `blocks_for_dir`/`_xml_files_for_dir` 가 `_00761` 만 제외).
  CSM 축도 BS 와 같은 별도(OFS) 규약이 맞다.
- **그 정정이 같은 커밋 안에서 되돌아갔다** — §A 참조.
- **"넷 다 tol 근처 = 선택효과" 는 논증이 아니라 서사.** 4사는 `0<잔차≤tol` 버킷에서
  골라낸 것이라 동어반복이고, 실측 크기가 0.03%~0.44%(15배 차)라 "같은 스케일" 이 성립하지
  않는다. 답해야 할 질문(왜 tol 초과가 하나뿐인가)은 다루지 않았다. 행동이 걸려 있지 않아
  무해하지만 "설명됨" 으로 읽힐 문단이라 명시.
- **tol 시뮬레이션은 표까지 정확히 재현**(5배 조여도 롯데 1건, abs 축 0건). 결론 유지.
- **미래에셋 분리발주가 inbox 에 없다** — `spawn_task` 는 handoff 계약이 아니다.
  `inbox/parser/20260825T2200Z` 로 내가 다시 냈고, 범위에 **gold `why` 공란 44건**
  (KR0003 12 · KR0072 5 · KR0079 27)을 포함했다.

### 티켓 C `20260825T1130Z` (배포본 소진율) — 종결 · **불변식 1번 배선**

- **캡 제거 확인**: 빌더를 쓰지 않고 per-bond 원천에서 39사 직접 재계산 → 6사 값
  (192.9/187.0/144.1/139.8/138.5/113.4)·`>100%` 집합 일치, 배포본↔빌더 전 필드 diff 0.
- **불변식 1번은 안 닫혀 있었다(변이시험).** 배포본 `tier1_hybrid_issued_eok` 를 0 이나
  절반으로 틀어도 두 게이트 **양쪽 exit 0**. 화면이 "발행 0억 + 도넛 144.1%" 라는 자기모순을
  그리는데 아무 룰도 안 걸렸다.
- **고쳤다**: `scripts/validate_live_artifacts.py` 의 배포본↔빌더 대조를 `utilization_pct`
  한 필드 → **K-ICS.html 이 읽는 5필드 전부**(`_TIER_SCREEN_FIELDS`)로 확대, 한쪽 결측도 RED.
  재측정 M2/M3/M5/M9 전건 exit 2, 무변이 exit 0. **화면 밖 3필드는 여전히 미검사**(명시).

### 이번 라운드의 교훈

**소스 3개가 일치한다는 것은 기준이 같다는 뜻이지 옳다는 뜻이 아니다.** 원 티켓을 쓴 것이
나였고, diag·viz·history 셋이 PL 편이라는 것을 "루트만 틀렸다" 로 읽었다. 셋 다 같은
**연결** 블록을 보고 있었을 뿐이다. 앞으로 별도/연결이 한 파일에 공존하는 마스터에서는
**다수결이 아니라 파일 신원(`_00760`/`_00761`)으로 판정한다.**


## 2026-08-25 (e) — answered 2건 sender 재확인: 면제 1건 기각 · 화면 6칸 캡 오적용 적발

내가 sender 인 티켓 2건이 `answered` 로 돌아와 재확인했다. **재확인은 전부 독립 재측정으로
했다** — recipient 가 남긴 probe 를 재실행하지 않고 raw XML·per-bond 원천을 직접 다시 읽었다.
결론은 **둘 다 iter++**. 마스터 데이터는 한 셀도 안 고쳤다.

### 확인된 것 (다시 볼 필요 없음)

- **에이비엘 복사셀 3건 — 내 발주가 틀렸고 parser 가 맞았다.** 나는 "2024 가 2025 를 복제"
  라고 썼는데 반대였다. raw 삼중 확증: FY2024 `1) 당분기`=22,447/44,994/66,762 ·
  FY2025 `1) 당분기`=20,087/40,080/61,207 · FY2025 의 `2) 전분기` 열이 2024 값과 동일.
  세 분기 전부 `|전분기|>|당분기|` 라 `max(abs)` 폴백이 반드시 전분기를 집는다.
  **독립 확인** — 이번 커밋(`aa47315`)이 손대지 않은 `CSM_waterfall.json` 의 CSM상각이
  정정 후 값과만 맞는다(2025.1~3Q = -200.9/-400.8/-612.1억).
- **basis_mix 5건.** 단 `assemble(): item7 = item3-(item4+item5+item6)` 이라 `item3=Σ(4..7)` 은
  **설계상 항등식** — 닫힘은 증거가 아니다. 대신 원천 교차대조로 봤고
  KR0070/0072/0087/0001 전 분기 `PL item4 ÷ (WF item5×100)` = 0.9999~1.0002.
- **잔존 6건 중 5건**은 "못 닫았다"를 그대로 적었고 인용 probe 6종이 전부 디스크에 실재한다.
- **tier 배포본 == 빌더**: 39사×2파일 전 필드 재대조 어긋남 0. 바뀐 4칸과 0.0% 정답 3건을
  `data/bonds/capital_securities_fy2025.json` per-bond 에서 직접 재계산해 전건 일치
  (예: 아이엠라이프 tier2 = 1,000×3.629/5 + 750×3.99/5 = 1,324.3 / 3,262.5 = 40.6%).

### 기각한 것

**`issuer_structural_residual`(DB생명 2023.1Q).** 사유가 "이 회사 보험손익 캡션이 재보험을
구조적으로 제외한다" 는 **회사 단위 주장**인데, 그 회사의 다른 분기가 반증한다 — 재보험
포함형이 닫히는 분기 **12**, 원수 단독형 **1**(2023.1Q뿐). raw 가 원인을 보여준다:
부모행 `I. 보험서비스손익 24,548,248,470` 아래 자식행 `1. 보험손익 22,946,356,594` 가 있고
마스터 item1 이 자식행을 집었다(`item2−item16 = 24,548.248` 이 부모행과 3자리 일치).
**parent/child 오선택, 2023.1Q 한정.** recipient 는 한 분기의 raw 만 보고 회사 성질로
일반화했다 — 같은 회사의 다른 분기가 가장 싼 반증쿼리였다.

### 새로 적발한 것 — 화면 6칸이 틀리다 (owner 승인 대기)

publishing 이 하나손해 tier1 144.1%→100.0 캡을 "owner 결정" 으로 정당화했는데, 근거로 든
`changelog_publishing.md:411` 의 결정은 **같은 날 번복됐다**
(`changelog_designer.md:783-789` "owner 결정 복원" + designer 프롬프트 L177 LOCKED).
owner 논거: 분자=KOFIA 발행액·분모=공시 한도라 **독립 소스라 사전 cap 이 애초 불가능**,
원호(`Math.min`)만 캡. `K-ICS.html` 은 이미 그렇게 구현돼 있으나(L841 `pct>100 ? '100%+'`,
L879 툴팁 "실제 144.1%") 빌더가 잘라 보내 그 분기가 죽는다. 전수 census **6사**
(NH농협 192.9 · 하나생명 187.0 · 하나손해 144.1 · 코리안리 139.8 · 한화생명 138.5 ·
KDB생명 113.4)가 평평한 `100%` 로 그려진다 — 한도에 정확히 걸친 것과 구분 불가.
2026-07-22 `a629e34`(인라인→fetch)로 데이터쪽 캡이 화면에 도달한 것이 발현 시점이고,
이번 §1 동기화로 0.0% 가 걷히면서 6사가 전부 캡에 걸렸다.
**tier1/tier2 비대칭이 스스로 증거** — 같은 빌더 L140 은 tier2 를 안 자르고 `>100` 이면
`util_over_100_legit` 플래그를 붙인다.

> `validate_live_artifacts.py:465` 도 `exp = min(100.0, ...)` 로 그 캡을 **축복**하고 있고,
> 주석은 memory `reference_kics_capital_tiering` 의 "owner 결정 = 화면 100%+ 표기" 를
> 인용하면서 정반대로 구현했다. 인용한 근거와 코드가 어긋난 자리다. 빌더와 **같은 커밋**에
> 고쳐야 6사가 transient RED 으로 뜨지 않는다.

### 게이트 사각 2개 (validation 이 가져감)

1. **PL 등재부가 값을 안 본다.** `_report_pl_baseline`(L783-807)은 `회사|분기|라벨` 키만 보고
   등재부의 `lhs`·`diff` 를 읽는 코드가 0곳 → 등재 6건은 값이 움직여도 영원히 YELLOW.
   같은 파일 L151 `csm_amort_ledger_verdict` 는 `residual_eok` 를 tol 로 박제하고 `PIN_DRIFT`
   를 띄운다. 옳은 패턴이 함수 하나 옆에 있는데 PL 축만 안 쓴다.
2. **불변식 1번이 tier 축에서 아직 안 닫혔다 — publishing 이 닫은 것은 증상이다.**
   나는 처음에 "`tier1_hybrid_issued_eok` 는 CAPSEC 이 잡겠지" 하고 내 판정을 누그러뜨리려
   했다(`validate_data_contract._CAPSEC_SLICE_FIELDS` 에 그 필드가 있다). **변이시험이
   반대로 나왔다** — 매회 바이트 백업→변이→게이트→복원, sha256 원복·`git status` 청결:

   | # | 무엇을 틀었나 | live_artifacts | data_contract |
   |---|---|---|---|
   | M2 | **배포본** `tier1_hybrid_issued_eok` 1000→0 | exit 0 | exit 0 |
   | M3 | **배포본** 같은 필드 1000→500 | exit 0 | exit 0 |
   | M4 | **빌더 산출물** 같은 필드 1000→0 | — | **exit 2 `CAPSEC_COVERAGE_REGRESSION`** |

   CAPSEC 룰은 멀쩡한데 **보는 파일이 다르다.** `_load_tier`(L1844)가 `ROOT/"output"/sub` 를
   glob 해 빌더 산출물을 읽는다. L1641-1643 의 배포본 매핑은 mtime·provenance·
   ARTIFACT_UNREADABLE 축 전용 — 원 발주문의 *"mtime·provenance 는 배포본을 보고 숫자는
   상류를 본다"* 가 **지금도 사실**이다. 배포본과 화면 사이에 서 있는 것은 이번에 신설된
   `validate_live_artifacts` 의 `utilization_pct` **한 필드 대조**뿐이고, 화면이 인쇄하는
   `tier1_hybrid_issued_eok`(이번 사고에서 실제로 0 이었던 그 필드)는 어느 RED 룰도
   배포본에서 보지 않는다(항등식은 `..._recognized_eok` 를 쓴다).
   → ① 배포본↔빌더 대조를 화면 4필드로 확대 ② `_load_tier` 배포본 재조준(부수효과 커서
   전 버킷 시뮬레이션 먼저). 둘 다 validation 이 가져간다.

### 조립 단계 강제 여부

`sync_tier_utilization_to_deploy.py` 를 **호출하는 코드는 0곳**(참조 7곳 전부 문서)이지만
결과는 강제된다 — `validate_live_artifacts` 가 `prepush_check.py:83` 도메인 게이트 루프에
있고 exit 가 `n_dom |= _p.returncode` 로 전파된다. 위 변이시험 M1 이 실증(exit 2).
"문서에만 있고 아무도 안 부르는 단계" 는 아니다.

### 부수 실측

`PL item4 ÷ (WF item5×100)` 346 버킷 전수: 현행 밴드 `0.4~2.5` 를 벗어나는 것 **0건**.
정정 전 에이비엘 2025 는 1.09~1.12 였으므로 이 밴드는 이번 결함을 구조적으로 볼 수 없었다.
코리안리 14버킷이 0.41~0.71 로 계통적(수재 레그 누락 방향)이고, 삼성생명 1.02·미래에셋
2025.2Q 1.25 가 다음 후보다.

### 검증

- `scripts/validate_master_tables.py --no-build` → exit 0,
  `pl_bridge:2513P/16F/319S/0NEW`, `PL_BRIDGE BASELINE 기지=16 신규=0 등재부에만 남은 것=0`.
- `scripts/validate_live_artifacts.py` → `RED=0 YELLOW(baselined)=1082 STALE_BASELINE=0` exit 0.
- 변이시험 후 `kics_tier1_utilization.json` sha256 원복 확인 + `git status` 청결.
- `scripts/prepush_check.py` → **exit 0** (gate RED=0 · K-ICS clear · domain pass ·
  DART raw 유실 0 · inbox 기계적위반 0 · offline tests **230 passed/1 skipped**, 9분46초).
- **마스터 JSON·배포본·HTML 무수정.** 편집한 것은 티켓 2개 + 이 문서 2개뿐.
- ⚠️ **공유 트리 — 위 exit 0 은 provisional.** 검증 중 다른 세션이 `PL_breakdown.json` ·
  `data/_gold/user_pl_cells.json` · `data/dart/viz/insurance_pl_breakdown.json` ·
  `scripts/viz_build_ifrs17_panels.py` 를 수정 중이었다. 그 여파로 같은 세션 안에서
  `validate_live_artifacts` 가 `YELLOW 1082/STALE 0` → `YELLOW 1038/STALE 44` 로 움직였다
  (INSPL_* 축). 내가 잰 tier·PL 수치는 재측정해도 동일했고, 변이시험 3회는 tier 파일만
  건드렸다(전부 원복). **커밋 시 내 4파일만 골라 담을 것.**


---

## 2026-08-25 (d) — 산술 항등식 레지스트리: **등식을 밴드로 구현하는 것을 기계로 막는다**

owner 지시: *"별도 축이 아니라 기존 rule 이 의무적으로 돌게 하면 된다고. 내가 정해준 rule 을
성실하게 다 돌리기만 했어도 진작에 잡혔잖아."* / *"0.7~1.4 band 가 아니라 당연히 1 이어야돼."*

마스터 데이터는 한 셀도 안 고쳤다. 게이트 코드 · 등재부 · 테스트만.

### 1. 진단 — 룰이 없어서가 아니라 등식을 밴드로 구현했다

owner 가 지정한 등식 "워터폴 CSM상각 = PL CSM상각(부호 반대)" 의 구현:

```
scripts/validate_data_contract.py:791   _XCHK_LO, _XCHK_HI = 0.4, 2.5
```

배수 2.5배까지 봐주는 범위검사였고, **대조 가능한 346버킷 중 잡은 것 0건**이다. 에이비엘생명
2025.1~3Q 의 복사 결함(비율 1.09~1.12)이 그냥 통과했다. 정정 후 그 6분기 비율은 0.9999~1.0001 —
등식은 원래 성립한다.

그리고 **대조식 자체가 틀려 있었다**: PL 쪽을 `원수 + 재보험`으로 더했는데 재보험(출재)은
별도의 **보유** 재보험계약자산 워터폴이라 더하면 안 된다. 인과가 이렇게 돈다 —
틀린 식 → 잔차가 커 보임 → 밴드를 넓힘 → 진짜 결함이 지나감.

같은 등식이 `validate_master_tables._check_csm_crosscheck` 에도 있었는데 **대조식(원수+수재)은
맞고 폭은 다르고(OK≤max(5%,300mn)/FAIL>10%) 스코프는 4Q 한정**이었다. 즉 정답을 아는 구현이
저장소 안에 이미 있었는데 push 를 막는 쪽이 틀린 식을 쓰고 있었다.

### 2. 대조식 확정 — 원수 + 수재 (전 버킷 실측)

| 대조식 | ±1% 밖 |
|---|---|
| 원수 + 재보험 (종전 data-contract) | 245 |
| 원수 단독 | 31 |
| **원수 + 수재** | **20** |

증명: 코리안리재보험 2023.4Q · 2024.1Q~2026.2Q **11분기가 정확히 1.0000**(원수 단독이면
0.41~0.71). 워터폴은 "발행한 보험계약" 의 CSM 이라 원수(direct) + 수재(assumed)를 포함하고,
출재(코리안리 항목 `9-1` / 타사 항목 `9`)는 보유 자산이라 제외한다.

### 3. 허용오차 — 반올림 폭만

`max(0.1억, 0.05%)`. 근거는 저장 granularity 실측:

- 워터폴 억원 1자리 → ±0.05억 · PL 백만원 → ±0.005억 → 결합 상한을 억원 그리드로 올려 **0.1억**
- 워터폴 상각은 **상품라인 블록의 합**(관측 최대 5블록, `summed_product_lines`)이라 블록별
  반올림이 누적된다 → **0.05%**

전 분기 346버킷 중 **318건이 이 안에서 닫힌다**(잔차 p50 0.029억 · p75 0.040억 · p90 0.21억).
`4Q-only` 제한("1~3Q 는 분기배분 차이로 틀어진다")은 근거 없는 전제였고 실측으로 반증됐다.

구현은 `validate_master_tables` 한 곳(`csm_amort_tol` / `csm_amort_residual` /
`csm_amort_ledger*`)에 두고 data-contract 는 import 한다 — 상관행렬을 재타이핑하지 않는 것과
같은 이유다.

### 4. 걸린 28버킷 — 전건 원인 분류 + 잔차 박제

`data/_gold/csm_amort_identity_ledger.json`. 통째 skip 이 아니라 **건별 + 잔차값까지** 박제라,
고쳐지거나 나빠지면 `PIN_DRIFT` RED 가 되고 등재부에만 남으면 `LEDGER_STALE` YELLOW 가 뜬다.

| 원인 | 건수 | 대상 |
|---|---|---|
| `WATERFALL_MISEXTRACT` | 10 | 삼성생명 2024.1Q~2026.2Q — **raw 확정** |
| `WATERFALL_SUSPECT` | 4 | 코리안리 2023.1~3Q · 미래에셋 2025.2Q |
| `RESTATEMENT_BASIS` | 3 | DB손해 2023.1~3Q — 원인 규명, 화면 무영향 |
| `UNRESOLVED` | 11 | 교보생명 4 · 신한라이프 6 · 하나생명 1 — **원인 미규명** |

**삼성생명 (raw 확정).** FY2024 사업보고서 `20250312001063` 의 `보험계약 상품라인 측정요소별
변동내역` 3개 상품라인 `제공한 서비스에 대해 인식한 보험계약마진` 합
`563,990 + 691,566 + 137,822 = 1,393,378` 백만원 = PL `1,393,380` 인데 루트 마스터는
`1,369,540`(−238.40억). `csm_waterfall.json`(viz) 과 `csm_waterfall_history.json` **둘 다
−1,393,378** 로 PL 편이다 → diag→루트 경로의 회귀. 2023 분기는 세 소스가 소수 둘째자리까지
일치하므로 FY2024 필링부터 생겼다. 잔차가 분기당 +57억(2024) → +71억(2025) → +94억(2026)로
꾸준히 커지는 것이 "구성요소 하나가 빠진다" 는 모양이다.

**코리안리 — owner 가설 기각.** owner 는 "수재 leg 누락" 을 지목했는데 실측으로 아니다:
PL 에 수재 leg 는 있고(항목 `4-1`, 14분기 전부) 원수+수재로 11/14 분기가 1.0000 이다.
남는 2023.1~3Q 는 루트 워터폴 쪽이 의심된다 — `csm_waterfall_history` 의 2023.2Q(706.11)·
2023.3Q(923.11)가 PL(706.12 · 923.11)과 일치하고 루트만 1,042.40 · 1,560.10 이다.

**DB손해 — 원인 규명.** 루트의 2023.1~3Q 는 2024년 필링의 비교(전기) 컬럼 = 소급재작성값,
PL 은 2023년 원 필링값. 근거: history 의 2024.1/2/3Q(3,118.50 / 6,193.43 / 9,357.89)가 루트의
2023.1/2/3Q 와 정확히 같다. 2023 분기는 사이트 비노출.

**미규명 11건.** 신한라이프는 2025.1Q 부터 갑자기 **+0.086~0.152% 의 일정한** 차가 생긴다
(그 전 8분기는 완전 일치) — 반올림으로 설명되지 않는 계통 차이 지문인데 원문에서 원인을
확정하지 못했다. 교보생명 2023.1~3Q 는 루트·PL·history **3자가 전부 다르다**.
등재부의 `UNRESOLVED` 는 **정당화가 아니라 미규명 표시**이며 note 에 그렇게 적혀 있다.

전건 `inbox/parser/20260825T1520Z__validation__MULTI__csm_amort_identity_28_ledgered_buckets.md`
로 발주(lane: ifrs17).

### 5. 같은 병을 다른 축에서 — 전수 훑고 실측 시뮬 후에만 조였다

| 축 | 종전 | 지금 | 조인 비용(실측) |
|---|---|---|---|
| `8_life` (item17 = sqrt(29-35·R7)) | max(2억, **5%**) | max(2억, **1%**) | **0건** (n=364, p90 0.049%) |
| `19_market` (item19 = sqrt(36-40·M)) | max(2억, **5%**) | max(2억, **1%**) | **0건** (n=356, p90 0.083%) |
| viz rollforward (`validate_csm_waterfall`) | max(500mn, **0.5%**) | max(200mn, **0.1%**) | **0건** (루트 구현과 폭 통일) |
| continuity `WITHIN_FY` | **5%** | **1%** | 새 blocking RED **0** |
| `36_irr` (item36 = f(41-46)) | 5% | 5% **유지** | +12건 — 아래 |

`8_life` / `19_market` 의 5% 는 *"7개 하위항목의 반올림이 누적된다"* 는 이유로 붙어 있었는데
**실측 누적폭이 그 1/50** 이었다. 상수를 `DIVERSIFIED_SQRT_TOL_REL` 하나로 모아 적용전 룰엔진과
적용후 미러(`_TRANS_PARENT_SUBS` 의 `dyn5`)가 **같은 값을 import** 하게 했다 — 적용후만 느슨하면
'룰은 돌지만 못 잡는' false-green 이 된다.

`continuity WITHIN_FY` 를 조이자 메리츠화재 FY2023 하나가 새로 걸렸는데, 그건
`validate_master_tables.WFY_EXCEPTIONS` 에 이미 '소급재작성' 으로 등재된 건이었다. 면제셋을
모듈 레벨로 올려 `validate_csm_continuity` 가 **import 해서 쓰게** 했다(같은 면제를 두 곳에
복사하지 않는다). 그 축은 이제 YELLOW `WITHIN_FY_OPENING_DRIFT_EXCEPTED` 로 인쇄된다.

`36_irr` 은 **조이지 않았다.** 1% 로 조이면 12건이 새로 걸리는데 **12/12 전부 actual > expected
인 양(+)의 계통편차**(+1.08%~+4.69%, 전부 짝수분기)다. 부호가 한쪽으로만 몰리는 것은 데이터
12건이 동시에 틀린 게 아니라 **파생식이 원문 산출식의 하한**이라는 지문이라, 원문 산출식을
확정하기 전에 조이면 오탐 12건을 만든다. `IRR_DERIVED_TOL_REL = 0.05` 에
`documented_widening`(사유 + 티켓 + 실측비용)을 달았다 — 정당화가 아니라 미결 표시다.

### 6. `tests/test_identity_registry.py` (신설, 14 tests, <1초)

45개 축을 `IDENTITY` 33 / `RANGE` 9 / `HEURISTIC` 3 으로 전수 분류하고 각각 진술(부호 규약 포함) ·
구현 위치 · 현재 허용오차 · 실측 근거 · 변이시험 소재를 등재했다. 강제하는 것:

1. **선언 ↔ 코드 동기화** — `tol_from` 으로 살아 있는 상수를 읽어 대조. 몰래 넓히면 막힌다.
2. **IDENTITY 는 밴드일 수 없다** — 상대 tol ≤ 1%(= 관측 반올림폭의 10배 이상 여유). 넘기려면
   RANGE 로 재분류하고 사유를 쓰거나 `documented_widening`(사유·**실재하는 티켓**·실측비용).
3. **RANGE/HEURISTIC 은 사유 필수** (최소 60자). 사유 없이 RANGE 로 옮기는 것이 이 테스트를
   무력화하는 유일한 길이라 거기를 막는다.
4. **K-ICS 룰 전수 분류** — `test_rule_coverage_manifest.DECLARED_RULES` 의 모든 룰이 여기
   성격을 가져야 한다. 새 룰을 넣으면서 '등식인가' 를 안 정하는 길이 없어진다.
5. **등재 안 된 새 임계 상수 탐지** — 검증기 6개 파일의 모듈 레벨 상수를 AST 로 긁어 이름이
   임계처럼 생긴 것(`*_TOL/_LO/_HI/_REL/_ABS/BAND/EPS/FLOOR/CEILING/THRESH*`)이 레지스트리
   참조나 사유 붙은 allowlist 에 없으면 FAIL. `_XCHK_LO/_HI` 가 아무 선언 없이 태어나 몇 달을
   산 경로를 막는다. **이 검사가 즉시 미등재 3건을 잡았다**(`IFRS17_BS_TOL_ABS/REL` ·
   `TIER2_ZERO_EPS`) — 앞의 둘은 진짜 항등식이라 등재했다(자산총계 == 부채총계 + 자본총계).
6. **변이시험 발화** — IFRS17 축은 직접 흔들고(항등식 헬퍼 + **게이트 전체 in-process**),
   K-ICS 축은 `test_rule_coverage_manifest` 에 위임하되 위임이 실제인지(그쪽
   `DECLARED_RULES` 에 있는지) 검사한다.

`prepush_check.py` 오프라인 묶음에 **배선했다** — 안 넣으면 레지스트리도 honor-system 이 된다.

변이 3종 실측(파일을 잠깐 고쳐 pytest 를 돌리고 원복):

| 변이 | 결과 |
|---|---|
| ① 선언 삭제 (`tol_from` 비움) | 1 failed (`test_no_undeclared_threshold_constants`) |
| ② 밴드 확대 (`CSM_AMORT_TOL_REL` 0.0005 → 0.6) | **4 failed** (동기화 · 항등식 발화 2종 · 게이트 RED) |
| ③ 룰 무력화 (게이트 절을 즉시 `continue`) | 1 failed (`test_mutation_gate_emits_red_for_broken_identity`) |
| 원복 | 14 passed |

### 7. 게이트 착지

```
scripts/prepush_check.py  →  exit 0
  gate RED=0 · K-ICS rule gate=clear · domain gates=pass · DART raw 유실=0
  · inbox 기계적위반=0 · offline tests=230 passed, 1 skipped
```

`tests/fixtures/master_tables_golden.json` 재생성(`--update`, 사유 `_regenerated` 에 기록):
SUMMARY 필드 `crosscheck:97P/0M/0F/249S` → `csm_amort_identity:318P/28PIN/0F/0S`.
249 skip 이 0 이 된 것은 4Q-only 제한이 사라졌기 때문이고 exit_code 는 2 로 불변이다.
`tests/test_kics_rules_golden.py` 는 **무변동** — 8_life / 19_market 을 조인 비용이 실제로
0 이었다는 독립 증거다.

---

## 2026-08-25 (c) — CSM continuity 면제 심사: **산문 면제를 잔차 박제로 승격**

티켓 `inbox/_resolved/20260825T0230Z__validation__MULTI__csm_waterfall_sparse_3companies.md`
(iter 4, 종결). 데이터는 한 셀도 안 고쳤다 — 재확인 + 게이트 코드/테스트만.

### 1. 하나생명 2024.4Q 6셀 재검산 — 통과 (plug 0개)

iter2 에서 반려했던 plug(`-1,587.2`, 어느 공시에도 없는 잔차)가 iter3 정정으로 사라졌음을
**원문에서** 확인했다. FY2025 사업보고서 `20260325000201_00760.xml` 주석 14-4 (1) 보험의
`<전기>` 표는 CSM 을 `수정소급법/공정가치법/이외모든계약/소계` 4열로 인쇄하고, **소계 열에
6항목이 전부 그대로 있다**(우리가 합산할 필요조차 없다):

```
308,905,720 - 166,022,230 + 324,034,743 - 40,368,775 + 18,132,607 = 444,682,065   Δ=0 천원
```

억원 반올림 뒤가 아니라 **원문 정수에서 정확히 닫힌다.** 특히 '가정 및 경험 조정' -1,660.2 는
그 표 자신의 `보험계약마진을 조정하는 추정치의 변동분` 행 소계 `(166,022,230)` 의 인쇄값이다.

**2023.4Q 는 옮기면 안 된다(확정).** FY2025 note 38 이 재작성한 것은 2023.12.31 **잔액**뿐이고
(301,612,879 -> 308,905,720 = +7,292,841천원 = +72.93억, 공시 금액과 정확히 일치), FY2023 의
재작성 **rollforward 는 어느 filing 에도 없다**. 기말만 옮기면 그 행이 72.93 만큼 안 닫혀
2023 행에 새 plug 가 생긴다.

**parser 근거 문장 1건 정정.** iter3 의 "FY2023 자기 값과 FY2024 필링 `<전기>` 표가 소수점까지
완전 일치"는 실측상 과장이다 — FY2024 `<전기>` 는 조정 **-750.59** / 상각 **-279.56** / 기말
**3,016.13** 인데 FY2023 자기 표는 -751.05(기타행 -41,413천원 포함) / -279.14 / 3,016.09 다.
마스터 소수 1자리에서 2셀이 갈린다. 결론(경계 Δ=+73.0)은 안 바뀌므로 데이터 정정은 발주하지
않고, 게이트 코드의 등재 사유에서 그 문장을 실측치로 교체했다.

### 2. `_CSM_CONTINUITY_EXCEPTIONS` — 이빨이 없었다

parser 가 iter3 에 신설한 면제(하나생명 2024.4Q, owner 유지 승인). **해제하지 않았다** —
등재 1건 유지, 게이트 출력도 YELLOW 1건 그대로(RED=0 / YELLOW=74, 승격 전후 동일).
바꾼 것은 이빨이다. 승격 전 변이시험 실측
(`scripts/_probes/probe_20260825_mutate_csm_continuity_exception.py`):

| 물음 | 승격 전 |
|---|---|
| 등재 기준이 기계로 검사되나 | ❌ 산문뿐. 코드는 `.get((co,q))` 로 **키 존재만** 봤다 |
| 스코프가 (회사,분기)에 묶여 있나 | ✅ 맞다 (같은 회사 다른 분기·다른 회사 파괴 → 둘 다 RED) |
| 입력이 움직이면 되살아나나 | ❌ 기초 +1,000억 → Δ +73 **→ +1,073** 인데 같은 산문 그대로 YELLOW |
| 결측이면 | ❌ 완전 침묵 (RED=0 YELLOW=0) |
| 무용해지면 | ❌ 아무 말 없음 — 죽은 핀 영구 잔류 |
| 변이시험 | ❌ 없음 |

즉 '잔차 박제'가 아니라 그 버킷 **통째 무조건 통과**였다.
`tests/test_tier2_issuer_inconsistent_exemption.py` 가 tier2 면제에 요구하는 잣대에 미달.

**승격 (`scripts/validate_data_contract.py`)** — 산문 문자열 → 세 겹 박제 dict:

1. `pins` 경계 양끝 셀(3016.1 / 3089.1) — 데이터가 움직이면 `CSM_CONTINUITY_EXCEPTION_DRIFT`
2. `expected_gap 73.0` / `tol 0.2` — 발행사 명문 공시 델타(+72.93억)와 같은 크기
3. `verify` 인용 파일 + `present_markers` 4개(`308,905,720` `444,682,065` `166,022,230`
   `7,292,841`) + **`absent_markers`** `301,612,879`(재작성 전 값 — 그 파일에 있으면 '단일
   표에서 왔다'는 전제가 깨진 것). raw 는 gitignore 라 파일이 없는 클론에서는 RED 가 아니라
   `CSM_CONTINUITY_EXCEPTION_UNCHECKABLE` YELLOW 로 **정직하게 말한다**(push 는 안 막는다).

같이 닫은 것 둘:
- **결측 SKIP** → `CSM_CONTINUITY_INPUT_MISSING` RED. 직전 FY 4Q 행이 있는데 경계 양끝 중
  하나가 비면 그 경계는 '깨끗한' 게 아니라 **검산되지 않은** 것이다. 현재 이 경로 버킷 **0개**
  (census 실측)라 게이트 출력을 한 줄도 안 바꾼다 — 앞으로 생길 결측만 막는다.
- **죽은 면제** → `CSM_CONTINUITY_EXCEPTION_INERT` YELLOW (경계가 닫히거나 버킷이 사라지면).

**신설 `tests/test_csm_continuity_exception.py` (18 tests, 2.4초, 오프라인).** 변이 전부 발화:
기초 +1,000억/+0.5억·직전기말 +40억 → RED×2, 기초 결측 → RED, 경계 복원/버킷 삭제 → INERT,
인용 마커 누락/대조군 마커 존재/산문 등재 후퇴 → RED×2, 인용 파일 부재 → UNCHECKABLE YELLOW.
레지스트리 크기 `== 1` 고정 — 조용히 한 건 더 들어오면 테스트가 막는다.

**관찰(결함 아님)**: `validate_master_tables.py` 의 `CONT` 는 이 면제를 모르고 `cont:1` 을 계속
찍는다(골든에 박제). `check_csm_continuity` docstring 의 "두 게이트가 다른 답을 내면 안 된다"는
면제 층에서 지금 사실이 아니다 — **그대로 두는 편이 낫다**(두 곳에서 보이는 편이 안전).
그 문장은 다음에 그 게이트를 손볼 때 정리 대상.

### 3. 같은 병 전수 census — **키워드 축은 판별력이 0이다**

parser iter3 은 `"소급 재작성으로 재무상태표에 미치는 영향"` **한 문구**로 raw 를 뒤져 2사만
매칭이라고 결론냈다. 실측으로 두 방향에서 반박한다.

**(a)** 라벨 변형 9종으로 넓히면 raw XML 444개 중 **'강한 후보' 309건** — 사실상 전 회사·전
분기다. **좁히면 1건, 넓히면 전부.** 어느 쪽도 census 가 못 된다("키워드 부재 ≠ 원천 부재").

**(b) 라벨을 안 쓰는 축이 본선.** 마스터의 FY 경계 잔차 전수 분포가 이 병의 직접 탐지기다
(빌더가 각 filing 의 `<당기>` 표를 쓰므로, 후속 filing 이 전기를 재작성하면 그 filing 의
기초가 직전 filing 의 기말과 갈라진다):

```
평가된 경계 252 :  잔차 0 = 228 / 0 < 잔차 <= tol = 23 / tol 초과 = 1 (하나생명, 등재된 예외)
```

**tol 바로 밑에 같은 병 후보 4사**: 롯데손해 2024.4Q **-105.4억**(0.44%, tol 의 88% — 2024.1Q/
2Q/3Q 기초는 2023.4Q 기말과 소수점까지 일치하는데 **연차 filing 만** 다르다) · 신한라이프
FY2025 -26.8억 · 미래에셋 FY2025 +6.5억(**FY 중간에** 기초가 바뀐다) · 아이엠라이프 2025.4Q
-9.2억. 원인은 단정하지 않고(반증쿼리 1건까지만) 별건 발주:
`inbox/parser/20260825T1340Z__validation__MULTI__csm_fy_opening_disagrees_across_filings_subtol.md`

### 프로브 (전부 read-only, 마스터 미기록)

- `scripts/_probes/probe_20260825_hana_note144_raw_cells.py` — raw 표 원문 셀 인쇄
- `scripts/_probes/probe_20260825_hana_master_vs_raw.py` — 마스터 ↔ raw 셀 대조 + 천원 항등식
- `scripts/_probes/probe_20260825_mutate_csm_continuity_exception.py` — 면제 변이 9종
- `scripts/_probes/probe_20260825_csm_continuity_scope_census.py` — 룰 검사범위 census
- `scripts/_probes/probe_20260825_restatement_census_broad.py` — 재작성 census (키워드 축 + 무키워드 축)

### 4b. 그리고 그 변이시험이 **push 에서 안 돌고 있었다** — 훅에 배선했다

`prepush_check.py` 의 offline 테스트는 **고정 목록**(`fast = [...]`)이라, 새 테스트 파일을
만들어도 그 목록에 안 넣으면 push 때 한 번도 안 돈다. 처음 prepush 실행이 `198 passed` 로
초록이었는데 그 198 에 이 18건이 **안 들어 있었다**(파일은 이미 디스크에 있었다).
이 저장소가 이름 붙여 둔 실패모드 그대로다 — **"배선했다"와 "강제된다"는 다른 말.**
→ `tests/test_csm_continuity_exception.py` 를 `fast` 목록에 추가(2.4초).

**남은 같은 종류의 사각(이번 범위 밖, 다음 라운드)**: `tests/test_tier2_issuer_inconsistent_exemption.py`
와 `tests/test_exemption_absence_pin.py` 도 그 목록에 없다. 둘 다 **면제 변이시험**이라 같은
논리로 push 마다 돌아야 한다. 실행시간 측정 후 넣을 것.

### 게이트

```
scripts/validate_data_contract.py       exit=0  RED=0  YELLOW=74  (승격 전후 동일)
scripts/prepush_check.py                exit=0  (198 passed / 1 skipped, 11분 27초)
tests/test_csm_continuity_exception.py  18 passed (2.4초)
tests/test_push_gate_wiring.py          45 passed (배선 추가 후 재확인)
tests/test_deploy_assets.py             10 passed
```

**동시 세션 주의 — 내 것이 아닌 FAIL 1건.** `tests/test_master_tables_golden.py` 가
`pl_bridge:2511P/18F` vs 골든 `2503P/26F` 로 실패한다. 이건 **병행 PL 세션**이 13:29 에
`PL_breakdown.json` 을 바꾼 결과다(`insurequant_master_tables.xlsx.bak_20260825_pldrift` 동반).
`validate_master_tables.py` 에는 `validate_data_contract`/`CSM_CONTINUITY` 참조가 **0건**이라
이번 변경과 인과가 없고, 같은 SUMMARY 의 `cont:1` 은 기대/실측이 동일하다.
**골든을 `--update` 하지 않았다** — 그 축은 그 세션 소유다.

---

## 2026-08-25 (b) — 라이브 아티팩트 배선: 게이트가 **보지도 않던** 파일 6개를 검사에 올렸다

포스트모템: [`docs/postmortems/PM-2026-08-25_gate_read_the_wrong_file.md`](postmortems/PM-2026-08-25_gate_read_the_wrong_file.md)

### 반증 먼저 — 발주받은 census 5건 중 5건 참, 1건 거짓, 2건 누락

발주 census 는 **문자열 리터럴** 기반이라 양방향으로 틀렸다. 런타임 추적
(`scripts/_probes/probe_20260825_trace_validator_reads.py` — `builtins.open`/`Path.read_*` 을
감싸고 검사기를 실제로 돌려 열린 경로를 기록)으로 확정했다.

- ✅ 5건 전부 참 (PL 축 오조준 · NB_CSM_multiple · csm_amort_schedule · csm_waterfall_history ·
  insurance_pl_breakdown)
- ❌ **`equity_composition.json` 404 는 거짓** — `origin/main:IFRS17.html` 131행의 **HTML 주석**
  하나뿐이고 "죽은 코드는 이번에 진짜 삭제함"이라고 적혀 있다. fetch 하지 않는다. 티켓 불요.
- ⚠️ 오탐 2건: `data/dart/viz/csm_waterfall.json` · `data/ir/nb_csm_ratio.json` 은
  `validate_nb_csm_multiple` 이 `VIZ / "csm_waterfall.json"` 형태로 **읽고 있었다**(동적 조립).
- ➕ **census 가 놓친 2건**: `kics_tier{1,2}_utilization.json`. `validate_data_contract.ARTIFACTS`
  에 배포 경로로 **등록만** 돼 있고 값은 `_load_tier()` 가 `output/tier{1,2}_utilization/` 를 읽는다
  — 런타임에 배포본이 **한 번도 열리지 않는다**. 여기서 **라이브 오표시 4건**이 나왔다.

### 고친 것

**① PL 축 소스 재조준** (`scripts/validate_master_tables.py`)
`PL_PATH` 를 `data/dart/viz/pl_breakdown_master.json` → `PL_breakdown.json`. 배포본에만 있던
**1,307셀이 처음으로 PL 항등식·CSM 교차대조**를 받는다. 카운트 이동:

| 축 | 전 | 후 |
|---|---|---|
| `HOLE-PL (통째)` | 24 | **0** — 24/24 전부 phantom |
| `crosscheck fail` | 1 (BNP 2025.4Q) | **0** — 같은 이유의 phantom |
| `PL_BRIDGE fail` | 12 | **26** (phantom 2 소멸 + 처음 검사받아 드러난 16) |
| `zero_legs` | 5 | 3 |

**게이트 출력과 골든 `_regenerated` 에 "24건은 phantom 이었다"를 박아 뒀다** — 다음 세션이
"HOLE 이 사라졌다"를 회귀로 오인하지 않게.

**② `scripts/validate_live_artifacts.py` 신설** → `prepush_check.py` **1c 도메인 게이트** 배선.
`NB_CSM_multiple` · `csm_amort_schedule` · `csm_waterfall_history` · `insurance_pl_breakdown` +
`kics_tier{1,2}_utilization`(값 축). **형식 검사(파일 존재 여부) 금지** 원칙대로, 전부 마스터
교차대조 · 파일 안에서 닫혀야 하는 산수 · 기대 그리드 census 다. 룰 16종은 PM §2 참조.

**③ 배선 매트릭스** (`tests/test_push_gate_wiring.py`) — `LIVE_ARTIFACT_READERS` (라이브가
fetch 하는 .json 은 전부 읽는 검사기가 선언돼 있어야 한다) + `DEPLOYED_VS_UPSTREAM` (배포본과
중간산출물이 둘 다 있으면 배포본을 읽어야 한다). **변이 5종 5/5 발화**
(`scripts/_probes/probe_20260825_mutate_wiring_matrix.py`), 실행 후 트리 복원 확인.

### 드러난 것 — 라이브가 실제로 틀리다

같은 분기·같은 한도인데 **배포본만 분자가 0** (게이트는 상류를 봐서 몰랐다):

| 파일 | 회사 | 화면 | 빌더 산출물 |
|---|---|---|---|
| tier1 | 하나손해보험 | **0.0%** | 100.0% (`issued` 0 vs 1,000억) |
| tier2 | IBK연금보험 | **0.0%** | 22.2% (`subordinated` 0 vs 1,597.3억) |
| tier2 | 아이엠라이프생명보험 | **0.0%** | 40.6% (`hybrid` 0 vs 948.8억) |
| tier2 | 하나손해보험 | **0.0%** | 13.2% |

그 밖에: `NB_CSM_multiple.json` 이 **한 분기 뒤처짐**(마스터 2026.2Q / 배포본 2026.1Q, 28사 결측)
· 예별손해 2023.4Q 신계약CSM **부호 반전**(-509.7 vs 마스터 +509.7) · `csm_amort_schedule` 이
**16~30년+ 컬럼을 통째로 버려** 22사에서 Σ(연차)가 합계보다 35~44% 작음 · `csm_waterfall_history`
가 **아무도 재생성 안 하는 정적 스냅샷**이라 마스터 대비 **933/1,581셀(59.0%) drift** ·
에이비엘생명 2024 Q1~Q3 `원수CSM상각` 이 **2025 Q1~Q3 와 1원도 다르지 않음**(복사 지문).

### 착지 — 초기 YELLOW + 승격 조건 박제 (선례 UH-3 · `CSM_WATERFALL_PLAUSIBILITY`)

건별 등재부 2종. **통째 skip 이 아니고**, 매 실행 사유와 함께 인쇄되며, 고쳐지면 게이트가
`BASELINE STALE` / `FIXED?` 로 알려준다. **등재에 없는 신규 발견은 처음부터 RED.**

- `data/_gold/pl_bridge_baseline.json` — 26건 (pre_existing 10 · basis_mix 5 · lob_sum_gap 5 ·
  sub_leg_gap 3 · **copied_cell 3**)
- `data/_gold/live_artifact_baseline.json` — 1,086건
- 승격 기한 **2026-10-31** 을 `_promote` 필드에 박았다. `csm_waterfall_history` 는 예외적으로
  **파일의 처분**(마스터 파생으로 교체 권고)이 승격 조건이다.

### 우리 룰의 결함으로 판정해 **등재하지 않고 룰을 고친 것**

`TIER_UTILIZATION_IDENTITY` 초안이 5사(NH농협손해 192.9% 등)에서 실패했는데 데이터가 아니라
**룰이 틀렸다** — 소진율은 owner 결정으로 100 에서 잘린다. `min(100, …)` 으로 고쳐 5건 소멸.
**baseline 은 룰 결함을 덮는 데 쓰지 않는다.**

### 발주

- `inbox/parser/20260825T1120Z__validation__MULTI__pl_bridge_deployed_master_defects.md` (ifrs17)
- `inbox/parser/20260825T1125Z__validation__MULTI__live_viz_artifacts_unchecked.md` (ifrs17)
- `inbox/publishing/20260825T1130Z__validation__MULTI__deployed_artifact_diverges_from_builder.md`

### 검증

`pytest tests/` 413 passed · 변이 5/5 발화 · `validate_live_artifacts` exit 0 (RED 0 / YELLOW 1,086)
· `validate_master_tables --no-build` SUMMARY 골든 `--update` 재생성(사유는 fixture `_regenerated`).

---

## 2026-08-25 — CSM sparse 티켓 재확인: **게이트의 PL 축이 배포본을 안 보고 있었다**

`inbox/parser/20260825T0230Z__validation__MULTI__csm_waterfall_sparse_3companies.md` 가
`answered` 로 돌아와 재확인한 라운드. 판정 3건 중 2건 확정 · 1건 반려(`iter: 2`), 그리고
**원 티켓이 물었던 "census 가 왜 조용한가"의 답 절반이 게이트 자신에게 있었다.**

### 1. 불변식 1번 위반 — 검사 대상 ≠ 배포본 (PL 축만)

`scripts/validate_master_tables.py` L31-32 는 `WF_PATH = "CSM_waterfall.json"`(배포본)인데
`PL_PATH = "data/dart/viz/pl_breakdown_master.json"`(파서 중간산출물)이다. 실측:

- 게이트 소스 7,199행 vs 배포본 `PL_breakdown.json` 8,650행
- **배포본에만 있는 셀 1,451개(16.8%, 24개사)** = 이 파일의 PL 검사 3종(COVERAGE·PL_BRIDGE·
  CSM_CROSSCHECK)이 순회하지 못한다. 역방향은 0. (`validate_data_contract.py` 는 배포본을 읽으므로
  census·cross_source 는 그 셀들을 본다 — 즉 결측은 잡히되 **PL 항등식은 한 번도 안 걸린다**.)
- 공유 키 값 불일치 30건. BNP카디프 2025.4Q item5 ×1,592 / item4 ×1,000 / 라이나 2023.4Q item9 ×429.
- 게이트가 매 실행 찍던 `HOLE-PL … (통째)` **19건은 19/19 전부 phantom** — 배포본엔 값이 다 있다
  (삼성화재 2024.4Q 보험손익 1,780,370 등). 죽은 사본에만 없다.
- `crosscheck fail=1`(BNP 2025.4Q)도 배포본 기준이면 통과한다. 그 실패가
  `tests/fixtures/master_tables_golden.json` 에 `1F` 로 박제돼 있었다.

갈라진 이유는 `build_root_masters.py::build_pl` 이 viz 소스를 읽은 뒤 `_additive_merge(rows, PL_OUT)`
로 **기존 루트 마스터를 union 병합**하기 때문이다(그 함수 docstring: 2026-08-14 에 61셀/1,475행을
이 경로로 날린 사고의 근본원인 수정). **루트가 누적된 정본이고 viz 소스는 재생성 가능한 부분입력**인데
게이트가 부분입력 쪽을 보고 있었다.

**아직 안 고쳤다.** 배포본으로 재조준하는 순간 1,451셀이 처음 검사 대상이 되므로 룰별 전 버킷
시뮬레이션이 선행이다. `TODO_validation.md` 1순위.

### 2. 완결성 census 사각은 안 닫혔다

`coverage_holes(..., active_min=7)` 무변경, `exclude_companies` 참조 0회. 서울보증·신한이지는
CSM 마스터 행이 0개라 `if not present: continue` 로 조기 탈출해 **struct 목록에조차 안 뜬다.**
active_min 미만으로 CSM census 밖인 회사는 **14곳**이고 이번에 12셀을 채운 하나생명도 그 안이다.

### 3. 반려 1건 — 하나생명 2024.4Q 는 두 filing 기준을 섞은 행이다

FY2025 filing 「38. 재무제표 재작성」(K-IFRS 1008 소급적용, 보험계약부채 +5,726,404천원)은
실재하고 2025.4Q·2023.4Q 는 전부 원문과 일치한다. 문제는 2024.4Q 다:

| 항목 | FY2024 원본 | FY2025 재작성 전기 | 마스터 |
|---|---:|---:|---:|
| 기초 | **3,016.13** | 3,089.06 | **3016.1** (원본) |
| 이자 | 179.02 | **181.33** | **181.3** (재작성) |
| 조정 | -1,647.36 | -1,660.22 | **-1587.2** ← 어느 쪽도 아님 |
| 상각 | -398.57 | **-403.69** | **-403.7** (재작성) |
| 기말 | 4,389.56 | **4,446.82** | **4446.8** (재작성) |

`-1587.2` 는 순수 잔차 플러그이고, 발행사 값과의 차이 +73.0억은 **기초의 재작성분 +72.93억**과
정확히 같다. item4 는 빌더 설계상 잔차라 나머지 다섯 칸이 **한 표에서** 올 때만 발행사 값과
같아지는데 그 전제가 깨졌다. 항등식 Δ=0 · FY 경계 Δ=0 · 게이트 전부 초록 —
**화면 막대만 어느 공시에도 없는 값**인 전형적 false-green.

### 4. 확정 2건 + 단위버그 전수

- **서울보증보험 정당 미공시 확정.** 근거를 키워드 부재에서 **긍정 증거**로 교체했다 —
  주석 14 「회계모형별, 포트폴리오별 보험부채 현황」의 컬럼이 보험료배분접근법 **하나뿐**이고
  일반모형 컬럼이 아예 없다(FY2024.4Q 2,770,640,620천원 · FY2025.4Q 2,754,928,850천원 ·
  FY2026.2Q 2,900,029,184,824원). parser 가 안 본 분기·반기 5건도 `"보험계약마진"` 0회이고,
  `"측정요소"` 12회는 전부 `재측정요소`(확정급여채무)라 키워드만 셌으면 오탐할 자리였다.
- **신한이지 제외 유지** — 단 사유는 "미공시"가 아니라 금액 미미(기초 CSM 0.71억 / 기말 1.69억,
  원문 표 실재).
- **`waterfall_for_dir()` 단위판별 전수(302 dirs)**: 표가 선언한 단위와 코드가 가정한 단위가
  어긋나는 버킷 **8건 / 4개사**(신한이지·BNP카디프·카카오페이·**AIG 2025.4Q**). 전부 이미 gold
  (`set` 30셀 + 제외 1개사)로 덮여 마스터는 옳지만 **코드는 미수정**. AIG 가 mag
  2.66e8→1.55e8→**9.87e7** 로 내려오다 임계 `1e8` 을 넘으며 그 해에 처음 깨졌다 —
  규모가 줄어드는 회사는 언젠가 반드시 걸린다. 다음 후보 IBK연금(천원 표, 기말 4,501~5,204억).
  → `inbox/parser/20260825T0800Z__validation__MULTI__csm_unit_heuristic_reads_magnitude_not_label.md`

### 신규 프로브 (전부 read-only)

- `scripts/_probes/probe_20260825_gate_pl_source_vs_deployed.py` — 불변식 1 감사
- `scripts/_probes/probe_20260825_csm_unit_heuristic_sweep.py` — 단위판별 전수(79초)
- `scripts/_probes/probe_20260825_hana_csm_rows.py` — 하나생명 행 vs 원문 3종 대조
- `scripts/_probes/probe_20260825_coverage_census_blindspot.py` — census 사각 실측

### 게이트

`scripts/prepush_check.py` **exit 0** (RED=0 · K-ICS clear · 도메인 4종 pass · inbox 위반 0 ·
오프라인 176 passed/1 skipped, 7분 01초). `validate_master_tables.py --no-build` exit 2 이고
SUMMARY 가 골든 박제와 문자열까지 일치(드리프트 0). **마스터 JSON·룰 코드·골든 무변경.**

---

## 2026-08-25 — 저수익 휴리스틱 쳐내기: 5개 후보 중 **1개만 잘랐다** (나머지 4개는 반증으로 살림)

owner 지시: *"씰데없는 룰들은 좀 쳐내 제발"*, *"실질 검증은 산술적으로 닫히는 거에서 다 걸린다."*
오케스트레이터가 5개 후보를 지목하고 **"지우기 전에 각 룰별로 반증을 한 번씩 돌려라"** 를 조건으로 달았다.
전수 실측한 결과 **후보 5개 중 4개는 전제가 사실과 달랐다.** 자른 것은 1개다.

`kics_disclosure.json` · 마스터 xlsx 는 **한 칸도 안 건드렸다**(코드·룰·선언만). 허용오차 무수정.

### 판정 요약

| # | 후보 | 실측 | 판정 |
|---|---|---|---|
| 1 | generic anomaly discovery (CHECK 5) | YELLOW **224/297 (75.4%)** + 리뷰 큐 83 · **RED 0** · 마지막 수정기여 2026-06-19/20 | **잘랐다** → `scripts/scan_generic_anomalies.py` |
| 2 | `IDENTITY_TAUTOLOGY` / excess·z | 현재 RED 0 · REVIEW **2줄** · **write-path 버그 2건을 잡은 이력** | **살림 (반증)** |
| 3 | `AXIS_EVAL_RATE_LOW` / `AXIS_NOT_EVALUATED` | **둘 다 현재 0건.** 음성대조군 20·3 발화 | **살림 (반증)** |
| 4 | `SOURCE_UNREADABLE_NOT_VERIFIED` 밀도 휴리스틱 | 죽이면 판정불가 칸 **35 → 251 (7.2배)** | **살림 (반증)** |
| 5 | leaf 감사기 `LEAF_VS_RAW_MISMATCH` | push 경로 호출처 **0** — 이미 `scripts/_probes/` | **이미 되어 있음** |

### 1. 잘라낸 것 — 일반 이상치 발견 레이어 (유일한 진짜 저수익)

`validate_data_contract.run_gate()` 의 `check_generic_anomalies` 호출과 `prepush_check.py` 의
트리아지 절을 뺐다. **삭제가 아니라 이전이다** — `scripts/scan_generic_anomalies.py` 신설.

근거(실측):
- 게이트 YELLOW **297건 중 224건(75.4%)** 을 혼자 만든다(PEER_OUTLIER 147 · COHORT_ZERO 77).
- **RED 를 한 건도 낸 적이 없다.** 설계상 YELLOW 전용이라 `blocked = n_red or n_hyg or n_test
  or n_kics or n_dom` 에 **애초에 항이 없었다** — push 를 막은 적이 구조적으로 없다.
- 게이트가 찍던 224건은 **트리아지 이전(정밀화 전)** 숫자다. 트리아지가 134건을 노이즈로
  자동 억제하는데 게이트는 그 앞단을 날것으로 인쇄하고 있었다
  (예: "비엔피파리바카디프 기초CSM=342 vs cohort median 26,882" — 그냥 작은 회사다).
- 마지막으로 데이터 수정을 낳은 것은 **2026-06-19/20 라운드**(교보생명 원수예실차 4분기 ·
  BNP파리바카디프 단위오류 1.77조 · 코리안리 중복 43 · 교보라이프플래닛 보험금융손익 = 9칸).
  그 뒤 두 달간 이 큐에서 나온 데이터 수정 0건.
- 비용은 wall time 이 아니라 **사람 주의력**이다: CHECK 5 단독 실행 시간 **0.00초**.

**조용히 사라지지 않게 했다.** 게이트와 훅이 매 실행 한 줄로 "분리됨 + 어디서 돌리는지" 를 찍는다.
다음 세션이 "이상치 검사가 원래 없었다" 로 읽는 것이 이 저장소의 반복 사고형태다.

### 2. 반증 — `IDENTITY_TAUTOLOGY` 는 **write-path 버그 2건을 잡은 룰**이다

오케스트레이터 전제: *"오늘 validation 스스로 '내 룰이 틀렸다' 며 되돌린 룰이다."*
**틀렸다.** 되돌린 것은 **축 미러 룰**(`AXIS_SELF_MIRRORED_APPLIER`, 2026-08-21 (f) 자기정정)이지
동어반복 탐지기가 아니다. 동어반복 탐지기의 실적은 커밋 `0c04537` 에 박혀 있다:

> *"item4·item3 되맞춤 경로 제거. rule 2·R1 이 동어반복이었다(잔차 정확0 93%→67%)"*

구체적으로 —
- `recalc_kics_derived.py` 가 **허용오차 게이트 없이** `item3 = item1 − item2` 로 공시값을
  무조건 덮어쓰고 있었다. 그 결과 **rule 1(R1)이 실데이터에서 구조적으로 실패할 수 없었다**
  (n=477, 잔차 정확0 97.7% vs 귀무 75.0%, excess 1.30, z 11.4).
  → write-path 제거 + `fix_20260821_item3_writepath_restore.py` 로 79칸 원문복원.
- 같은 형태가 `item4`(rule 2)에도 있었다(`_reconcile_item4_from_components`).

**오늘 그 탐지기가 살아 있음을 다시 쟀다**: R1 은 이제 excess **1.08 · z 3.20** 으로 임계
(1.20 / 5.0) 아래다. **버그를 고치니 지표가 내려갔다** — 탐지기와 수정이 닫힌 고리를 이룬다.
룰 1·2 가 덮는 findings 는 **976건**(각 488)이고, 그것을 되맞춤으로 무력화한 스크립트
(`recalc_kics_derived.py`)는 지금도 살아 있는 코드다. 이 탐지기를 빼면 그 되맞춤이 다시
들어와도 아무도 모른다.

현재 비용: **RED 0 · REVIEW 2줄**(owner 면제된 `R2_순자산합` 적용전·적용후 상한 박제).
2줄 때문에 976건짜리 축의 falsifiability 감시를 끄는 것은 수지가 안 맞는다.
→ **룰 유지. owner 면제 2건도 그대로 둔다**(룰이 살아 있으므로 면제도 살아 있어야 한다).

### 3. 반증 — 축 평가율은 "매 실행 찍는 계기판" 이 아니라 **0 을 찍는 조용한 트립와이어**다

전제는 *"매 실행 찍고 있어 사람들이 넘겨 읽는다"* 였는데, 실측은 **둘 다 0건**이다:
`AXIS_NOT_EVALUATED` = 0, `AXIS_EVAL_RATE_LOW` = 0 (축 census 20행 전부 통과).
게다가 `prepush_check.py` 는 K-ICS 게이트 출력을 키워드 필터로 추려 보여줘서 훅 화면에는
이 줄이 **아예 안 나온다.** 즉 노이즈 비용이 0 이다.

죽은 검사가 아님도 확인했다(음성대조군):
- 평가율 바닥을 101% 로 올리면 → `AXIS_EVAL_RATE_LOW` **20건** 발화
- `effective=0` 을 강제하면 → `AXIS_NOT_EVALUATED` **3건** 발화

그리고 `AXIS_NOT_EVALUATED` 는 통계룰이 아니라 **결측 census 와 같은 부류**다 —
"이 축의 `FAIL 0` 은 증거가 아니다". 오케스트레이터의 절대금지 목록에 든
`MISSING_CELLS`("셀이 비면 항등식은 0들끼리도 닫힌다")와 같은 논리이고, 실제로
`CAPSEC_SOURCE_UNRESOLVED` · `DIV_CENSUS_SOURCE_MISSING` 과 한 가족으로 설계됐다.
**차이는 이것이 "셀이 비었나" 가 아니라 "룰이 그 셀을 순회하기는 하나" 를 본다는 점**이고,
후자는 결측 census 가 구조적으로 못 보는 사각이다(회사 필터·부모-자식 맵 누락).
→ **둘 다 유지.** 판정 강등도 하지 않았다 — 0 을 찍는 검사를 리포트로 내려도 얻는 게 없고,
잃는 것은 트립와이어다.

### 4. 반증 — 텍스트밀도 휴리스틱은 노이즈 **생산자가 아니라 감축자**다

전제는 *"vision 원장이 대체했으니 밀도 휴리스틱을 죽여라"* 였다. 방향이 반대였다.
밀도 사이드카는 460버킷을 `READABLE` 로 **인증**해서 "후=전 은 구조적으로 정당" 을 성립시킨다.
사이드카를 빈 맵으로 바꿔 보면(= 휴리스틱 제거):

| | 판정불가(unverifiable) 칸 |
|---|---|
| 현행(밀도 사이드카 사용) | **35** (그중 20칸은 vision 원장이 판정 완료) |
| 밀도 휴리스틱 제거 | **251** |

전 칸이 `UNMEASURED` 로 떨어져 **7.2배로 늘어난다.** 그리고 vision 원장은 바로 이 35칸에만
붙으므로, 밀도 휴리스틱을 죽이면 **원장도 같이 죽는다**(전부 `SOURCE_VISION_INERT`).
현재 `SOURCE_UNREADABLE_NOT_VERIFIED` 실발화는 **0건**이다 — 20줄은 전부 원장이 판정한
`SOURCE_VISION_VERIFIED` 다. → **유지.**

### 5. 이미 되어 있던 것 — leaf 감사기

`LEAF_VS_RAW_MISMATCH` 는 `scripts/_probes/leaf_scale_residue_audit.py` 에 있고
`prepush_check.py` · `validate_*.py` · `.githooks/pre-push` 어디에서도 **호출처가 0** 이다.
이미 push 경로 밖이다. (이력상 실적은 있다 — KR0071 item24 날조 dash 행을 잡았다.
`inbox/_resolved/20260821T1105Z__…`.) → **무작업.**

### 커버리지 불변 증명 (변이시험)

`scripts/_probes/probe_20260825_coverage_equivalence.py` 신설. 쳐내기 전/후 각각 돌려
반응 집합을 대조한다. 하니스 자신의 함정 3개를 명시적으로 피했다:

1. **문자열 값.** `kics_disclosure.json` 의 `값` 22,658칸 중 **진짜 숫자는 724칸(3.2%)**,
   나머지는 숫자문자열이다(`probe_20260825_value_types.py` 실측). `isinstance(v,(int,float))`
   로 거르면 40,655칸 중 1,434칸(3.5%)만 흔들고 "전부 눈멀었다" 는 거짓 결과가 나온다.
   `_shake()` 가 쉼표·△·괄호까지 파싱한다.
2. **공유 리포트 폴더.** `artifacts/kics_validation/` 을 읽지도 쓰지도 않는다 — `main()` 을
   안 부르고 `run_validation` / `run_gate` 를 in-process 로 호출해 **반환값만** 쓴다.
3. **음성대조군 양방향.** ① 아무것도 안 흔든 사본이 무반응인지(비결정성 탐지)
   ② 반드시 반응해야 하는 표적(item1·14·15·19)이 반응하는지
   ③ 선언된 사각(item12·13 적용후)이 여전히 무반응인지.

### 커버리지 불변 — 실측 결과 (exit 0)

쳐내기 **전** 한 번(48분 26초), **후** 한 번(46분 48초) 전수로 돌려 대조했다.

| 스윕 | 표적 | 눈먼 표적 | 쳐낸 룰 외 손실 | 모의≠실제 |
|---|---:|---:|---:|---:|
| A. CSM_waterfall / PL_breakdown 버킷 | 366 | **0** (+4는 아래 자기정정) | **0** | **0** |
| B. kics_disclosure 항목×컬럼 | 108 | **0** | **0** | **0** |

- **모의≠실제 0** 이 핵심이다. before 실행 중에 계산해 둔 "쳐낸 뒤" 예측이 실제 after 와
  **474개 표적 전부에서 일치**했다 — 쳐내기가 `check_generic_anomalies` 제거 **이상의 일을
  하지 않았다**는 기계적 증거다. (근거: 그 함수는 `env.wf`·`env.pl` 을 읽기만 하고 `res` 에
  YELLOW 를 append 만 한다. 공유 헬퍼도 env 변경도 없다.)
- 대조군은 before/after 동일: noop(무변이) 반응 0 · must-react `item1·14·15·19` 적용전/후
  **6/6 True** · 선언된 사각(item12·13 적용후) 불변.
- 하니스는 `artifacts/kics_validation/` 공유폴더를 **읽지도 쓰지도 않는다**(`main()` 우회,
  `run_validation`/`run_gate` in-process 반환값만 사용) — 남의 리포트를 자기 것으로 읽어
  "변화 없음" 이 나오는 함정 회피.
- 문자열 처리: `kics_disclosure.json` 의 `값` 22,658칸 중 **진짜 숫자는 724칸(3.2%)** 뿐이라
  `isinstance(v,(int,float))` 필터는 40,655칸 중 1,434칸(3.5%)만 흔든다. `_shake()` 가
  쉼표·△·괄호를 파싱해 **22,648 + 17,997칸**을 실제로 흔든다.

### 자기정정 — **내 하니스가 "아무도 안 본다" 고 거짓말했다**

전수 스윕 1차 결과에서 366버킷 중 **4버킷**이 "쳐내면 어떤 룰도 안 본다" 로 나왔다.
반응룰이 `ANOMALY_COHORT_ZERO`·`ANOMALY_PEER_OUTLIER` 둘뿐이었고, **3버킷이 표시분기**였다.
수용기준대로면 여기서 쳐내기를 되돌려야 했다.

**되돌리기 전에 한 번 더 확인했고, 오판이었다.** 하니스가 `validate_data_contract` +
K-ICS 룰엔진 **두 층만** 재고 있었다. PL 항등식(브리지)·CSM closing identity·plausibility 는
`scripts/validate_master_tables.py` 에 있고 그 게이트는 `tests/test_master_tables_golden.py` 를
통해 **push 경로 안에서 돈다.** 네 버킷을 그 층에서 다시 흔들었더니 전부 반응한다:

| 버킷 | 흔든 칸 | 반응 |
|---|---:|---|
| 서울보증보험 2026.2Q | 11 | `pl_bridge` |
| 신한이지손해보험 2024.4Q | 11 | `pl_bridge` |
| 신한이지손해보험 2025.4Q | 23 | `pl_bridge` |
| 하나생명보험 2025.4Q | 24 | `pl_bridge` |
| (음성대조군) DB생명 2025.2Q | 30 | `pl_bridge`·`closing`·`plausibility` |
| (음성대조군) 삼성생명 2025.4Q | 30 | `pl_bridge`·`closing`·`plausibility`·`crosscheck` |

원인은 단순했다 — **네 버킷 모두 `CSM_waterfall` 행이 아예 없다.** 그래서 CSM 계열 룰
(`CSM_CONTINUITY_FY_BOUNDARY`·`CSM_SIGN_CONVENTION`·`PL_CSM_AMORT_SCALE_GAP`)이 안 돌 뿐,
PL 항등식은 멀쩡히 본다.

**교훈은 이 저장소의 반복 주제 그대로이되 거울상이다.** 평소 경계는 *"룰이 0이라고 말한다 ≠
그 축이 깨끗하다"* 인데, 이번엔 *"내 하니스가 무반응이라고 말한다 ≠ 아무도 안 본다"* 였다.
**검증기의 검사범위를 의심하라는 규율은 내가 만든 계측기에도 똑같이 적용된다.**
하니스에 한계와 실측을 주석으로 박고(`RESIDUAL_COVERED_BY_MASTER_TABLES`), 새 버킷이 거기
들어오려면 **다른 층이 본다는 실측을 반드시 붙이도록** 못 박았다.

### 부산물 — `CSM_waterfall` 이 드문드문한 회사 3곳 (census 사각)

위 4버킷을 파다가 나왔다. `coverage_holes(idx, key_items, active_min=7)` 가 **"활성 신고사"
문턱(7분기)을 못 넘는 회사를 struct(미공시)로 분류해 뺀다** — 즉 **적게 있을수록 검사에서
빠지는** 구조다. 0분기인 회사는 `MASTER_HOLE` 이 영원히 0 이다.

| 회사 | WF 분기 | PL 분기 | raw 디렉터리 |
|---|---:|---:|---:|
| 서울보증보험 | 0 | 6 | 13 |
| 신한이지손해보험 | 0 | 2 | 6 |
| 하나생명보험 | **1** (2024.4Q) | 3 | 7 |

앞의 둘은 PAA 라 CSM 워터폴이 정말 없을 개연성이 높지만 **카테고리로 단정하지 않았다.**
하나생명은 생보사인데 1분기만 있어 확인이 필요하다. raw 가 `data/dart/` 에 **있으므로**
parser(ifrs17)로 발주했다 — `inbox/parser/20260825T0230Z__validation__MULTI__csm_waterfall_sparse_3companies.md`.
정당 미공시가 확정되면 그때 `active_min` 사각을 **레지스트리 기반 판정**으로 바꾼다
(지금 배선하면 근거가 없어 오탐 발생기가 된다).

### 선언 — 다음 세션이 회귀로 오인하지 않게

`tests/test_push_gate_wiring.py` 에 `DATA_CONTRACT_CHECKS` 매니페스트를 신설했다.
종전 매니페스트는 `scripts/validate_*.py` **파일** 단위만 강제했는데, 한 파일 안의 `check_*`
하나를 `run_gate()` 에서 빼는 것도 똑같이 게이트를 좁히는 행위인데 아무도 안 보고 있었다.
이제 검사 10개 전부가 `WIRED` 또는 `DEWIRED`(+사유+손으로 돌리는 스크립트 경로)로 선언되고,
선언과 실제 호출이 어긋나면 테스트가 막는다. 변이시험 2건으로 무효성 확인:
- `check_generic_anomalies` 를 되살리면 → FAIL (선언을 안 고쳤으므로)
- `check_census` 를 조용히 빼면 → FAIL

### 게이트 실측 (before / after)

| 지표 | before | after |
|---|---|---|
| `prepush_check.py` wall time | 7분 47.6초 | **7분 21.7초** |
| `prepush_check.py` exit | 0 | **0** |
| data-contract RED / YELLOW | 0 / **297** | 0 / **73** |
| ├ CHECK 5 (anomaly) | 224 | 0 (게이트 밖) |
| └ 나머지 4개 검사 | 73 | 73 (불변) |
| 이상치 리뷰 큐(매 실행 재생성) | 83 | 0 (수동 실행 시에만) |
| K-ICS findings 총계 | 13,664 | 13,664 |
| K-ICS RED / YELLOW / GREEN / SKIP | 36 / 1,519 / 9,523 / 2,586 | 동일 |
| 오프라인 테스트 | 164 passed, 1 skipped | **176 passed, 1 skipped** |
| `--selftest` | 55/55 | 55/55 |

수동 실행은 종전과 같은 수를 낸다: `scan_generic_anomalies.py` → 후보 224
(PEER_OUTLIER 147 · COHORT_ZERO 77) · 트리아지 REAL 77 / UNCERTAIN 6 / NOISE 134 /
OWNER_CONFIRMED 8 · `anomaly_skeptic_input.json` 83건.

### 남긴 것 / 되살리는 법

`run_gate()` 의 `# check_generic_anomalies(res, env)` 주석을 풀고
`DATA_CONTRACT_CHECKS["check_generic_anomalies"]` 를 `WIRED` 로 바꾸면 원상복귀다.
선언을 안 고치면 테스트가 막는다(의도).

### handoff

`docs/agents/claude-agent-publishing.md` §0(L163)·§3(L168-170)이 트리아지가 prepush 안에
있다고 적고 있다 — **다른 stage 프롬프트라 내가 안 고쳤다.**
→ `inbox/publishing/20260825T0130Z__validation__MULTI__anomaly_discovery_dewired_from_prepush.md`

CSM 드문드문 3사(위 부산물)는 raw 가 `data/dart/` 에 있으므로 parser(ifrs17)로 발주 —
→ `inbox/parser/20260825T0230Z__validation__MULTI__csm_waterfall_sparse_3companies.md`

인보 위생: 활성 2 · 위반 0(기계적 0 · 방치 0).

---

## 2026-08-24 (iter-4) — 면제 재감사 26버킷 반영: 부재형 면제 셀단위 박제 · 원장 경화 · 마커 행 귀속

오전 재감사(`artifacts/validation/reaudit_20260824_*.md` 5건)가 지목한 **안전 층**을 코드에 반영했다.
휴리스틱 룰 정리는 이번 범위 밖(발주자 지시). `kics_disclosure.json` · `insurequant_master_tables.xlsx`
는 **읽기만 했다** — 이번 라운드는 값 변경이 0 이다.

### A. 부재형 면제가 축을 통째로 눈감기던 구조 제거 (`scripts/validate_kics_disclosure.py`)

**사고**: 하나생명 KR0097 2024.4Q 의 `item33후`(942.86)·`item34후`(896.15)는 **2024.3Q 값의 복사**
였고 `item30후`·`item35후` 는 결측이었다. 그런데 `_AFTER_SUBRISK_NOT_DISCLOSED` 가
`(회사,분기)` 통째로 mmult 3축(15·17·19) · `_after_parent_missing_child_present` ·
`_parent_present_child_incomplete_after` · `_diversification_negative` 적용후 · 축 평가율 census
**다섯 곳**에서 순회를 건너뛰어 **어떤 룰도 그 셀을 본 적이 없다.**
실측: 그 4셀을 정정 전 값으로 되돌린 마스터로 게이트를 돌려도 출력이 **바이트 동일**.

**수정 — 면제는 축을 빼지 않고 셀을 박제한다.**

- `_AFTER_SOURCE_ABSENT_CELLS` / `_POST_PARENT_SOURCE_ABSENT_CELLS` — `(회사,분기) → 원천에 적용후
  컬럼이 없는 항목집합`. 종전 `(회사,분기)` 집합은 호환 껍데기로만 남겼다(축 제거 용도 폐기).
- 축의 적용후 입력이 **완비되면 면제와 무관하게 검산**한다. 결측인 입력이 **전부** 박제 셀일 때만
  `SOURCE_ABSENT_PINNED(29후,30후,…)` 로 미판정 처리하고 **셀 번호를 인쇄**한다
  (`_all_missing_are_pinned`). 박제 밖 셀이 섞이면 기존 추출갭 갈래로 내려간다.
- **`EXEMPTION_ABSENCE_PIN_PARTIAL_FILL` RED 신설** — 박제 그룹(부모별 자식집합)이 부분충전이면
  차단. 섞인 상태는 항등식을 입력결측 SKIP 으로 만들어 채워진 값이 무검사가 되는데, 사고 당시가
  정확히 그 상태였다(면제를 풀어도 결측 2칸 때문에 mmult 가 SKIP 이었다).
- `EXEMPTION_ABSENCE_PIN_VALUE_PRESENT` review — 원장이 '부재' 라는 셀에 값이 있으면 그 값은
  파생값이므로 매 실행 인쇄한다.
- **범위를 claim 에 맞게 좁혔다**: 축 15후(원문 p281 이 여섯 값을 다 인쇄하고 diff +0.0043 으로
  닫힌다)와 KR0049 의 `item1/2/3/14/27/28후` 가 근거 없이 사각이었다. 반대로 KR0097 의 `36~40후`
  부재는 사실인데 원장 어디에도 없어서 새로 명시했다(raw p301~309 B.2 절 `경과조치` 0회).

**수용기준 실측**: 정정 전 마스터 → 게이트 **EXIT 2** (`EXEMPTION_ABSENCE_PIN_PARTIAL_FILL`),
정정 후 → **EXIT 0**. 재현 `scripts/_probes/probe_20260824_v_mutate_kr0097.py` + `--master`.

### B. KR0087 동양생명 2025.2Q — `OUR_RULE_DEFECT` 확정, 면제 해제

발행사가 `보완자본 한도 적용 전` 행에 **한도값**(item47 == item48 == 1,210,705백만)을 인쇄해
`한도초과 = max(0, item47 − item48)` 이 구조적으로 0 이 됐고, 다리가 정확히 item12(1,188억)만큼
어긋났다. 등재 주장("발행사가 자기 각주 주1) 을 어겼다")은 **거짓** — 각주는 지켜졌다.

`kics_json_rules._tier2_excess_recovered_from_post` 신설(적용전 컬럼 한정, 가드 5개):

```
promo     = item2후 − item2전                    (경과조치 기본자본 승격액)
debt_post = item51후 − item49후                  (적용후 인정 채무성 보완자본)
debt_true = debt_post + promo   →  한도초과 = debt_true − item48전
가드: 중복행(47≈48) · promo>tol · 적용후 미구속 · 한도 구속 · 인쇄 보완자본 재현
```

실측 1,188.00 → 다리 잔차 **0.00**. **전 버킷 시뮬(488): 발동 1 · 해결 1 · 파손 0 · 무변동 0.**
같은 회사 2025.4Q·2026.1Q 는 `47 > 48` 을 정상 인쇄해 가드 D 에서 걸러지고 현행대로 닫힌다
(잔차 0.24 · 0.38). **되짚기 식 자체의 독립 검증**: 중복행 가드를 빼면 item47 이 정상 인쇄된
5버킷(KR0076 2023.1Q · KR0104 2024.4Q~2025.3Q)에서도 발동하는데, 되짚은 초과액이 인쇄값 기반
초과액과 **0.41 이내로 일치**한다(82.24/82.57 · 810.57/810.98 · 1904.33/1904.59 · 1968.77/1968.74 ·
974.76/974.70). 즉 이 식은 검증 가능한 곳에서 이미 맞고, 검증 불가능한 곳에만 대신 쓰인다.

면제는 `2_tier1_bridge` 축만 해제하고 `47_tier2_census`(TIER2_DUPLICATE_ROW, 발행사 사실)는 유지.
해제한 축은 원장 `contradicted_pins` 에 남겨 재등재 시 `EXEMPTION_PIN_RE_REGISTERED` RED.
(한화생명은 전 축이 풀려 `status=CONTRADICTED` 였는데, 여기는 한 축만 풀려서 **축 단위 tripwire**
가 필요했다.)

### C. 원장의 박제 숫자를 코드가 실제로 읽는다 (`_pin_ledger_agreement_findings`)

감사 H2: `expected_residual` 을 읽는 코드가 **하나도 없었다** — 진짜 박제는 코드 상수에만 있고
원장 숫자는 사본이며 아무도 안 봤다. 감사 H3: 그 사본이 **이미 어긋나 있었다**(KR0075 2024.3Q 는
존재하지 않는 축 이름 `47_tier2_census|적용후`, 2024.4Q·2025.1Q 는 census 두 축 결손).

`_code_pin_map()` 이 코드 박제 5종(`_TIER2_*` residual · `_LIFE8_*` · `IRR_DERIVE_*` · 부재 박제 2종)
을 원장과 같은 모양으로 펴고, 축 목록 · 잔차값(tol 0.01) · `absent_cells` · `contradicted_pins` 를
대조한다. **정본은 코드**, 원장은 반드시 일치해야 하는 사본. 배선 직후 위 5건을 실제로 잡았고
`scripts/fix_20260824_ledger_pin_sync.py` 로 동기화했다.

### D. verify 마커 행 귀속 (`verify.present_rows`)

감사 H5: 마커 155개 중 132개가 숫자-only, 그중 **57개가 인용 페이지에서 2회 이상** 등장 —
원장이 기록하는 명제는 "어느 **행**이 값 V 를 인쇄한다" 인데 검사는 "V 가 어딘가 있다" 만 봤다.

`present_rows = [{row, value}]` 신설. 판정: 라벨과 값의 y-중심 거리 ≤ `_ROW_ANCHOR_BAND`(3.0pt)
**이고** 값이 라벨 오른쪽(x). 캘리브레이션 15케이스(참 9 + 음성대조 6)에서 참 최대 Δ 0.21pt ·
거짓 최소 Δ 8.87pt. 어긋나면 `EXEMPTION_CITATION_CONTRADICTED` RED.

> **구현 중 실제로 밟은 버그**: 단어 run 이 행 경계를 넘어 누적돼 서로 다른 행의 조각이 한
> 라벨로 '발견' 되고 평균 y 가 행 사이에 찍혔다 — 롯데손해 2023.1Q 에서 `8,034` 를 `기본자본`·
> `보완자본`·`지급여력금액` **세 행에 동시 귀속**시켰다. `_word_runs` 에 같은 행 제약을 넣어
> 고쳤고 회귀시험으로 못 박았다(`test_a_word_run_never_spans_two_rows`). 이 버그를 안 잡았으면
> **행 귀속 검사 자체가 새로운 무검사**가 될 뻔했다.

**57 중 51쌍 승격**(`scripts/fix_20260824_marker_row_anchors.py`, 게이트 자신의 판정기를 그대로 사용).
등급 census 를 매 실행 인쇄한다: `ANCHORED 51 · LABELLED 23 · UNIQUE 75 · AMBIGUOUS 11`.
**남은 11개**(9 항목)는 라벨이 여러 줄로 감기는 행(`해약환급금 부족분 상당액 중 …` 계열)이라
3.0pt 로 앵커되지 않는다 — 밴드를 키우면 음성대조군이 무너지므로 **승격하지 않고 전건 인쇄**한다
(`EXEMPTION_MARKER_UNANCHORED`, UH-10).

### E. 면제 사유 갱신 6건 (`scripts/fix_20260824_ledger_reasons.py`) — 판정은 하나도 안 뒤집었다

| 대상 | 갱신 내용 |
|---|---|
| KR0032 2024.3Q | "고칠 셀이 없다" → 발행사가 FY2024_Q4 **p43** 에서 같은 분기 Ⅲ행을 8,867 → **9,390** 으로 정정했다(9,390 이면 다리 +1). `release_condition` 이 **이미 충족**돼 있어 재작성 — as-disclosed 유지가 현 상태이고 as-restated 채택은 owner 결정. `registered_by` 도 보충(26건 중 유일한 결손, 감사 H7) |
| KR0032 2025.4Q | `claim_kind` **variant → 행 오기**(13분기 투표 A 12 : C 2, C 쪽 1건은 한도구속이라 판별력 없음). 적용후 잔차 **1,899.18 = 949.59 × 2**(차감 스텝 수)를 박제 대상에 편입 — KR0094 IRR 면제와의 적용후 커버리지 비대칭 해소 |
| KR0073 2025.2Q | note 의 "최악 단일 시나리오보다 작아질 수 없다" 논증이 **우리 도출값 435,845 로 반증**됨 → 전수 탐색(재현 조합 0건) + 221/221 대조군으로 근거 교체. 6개 짝수분기 전부에 같은 편의가 있고 **5% 상대 tol 이 5분기를 흡수**한다는 사실을 기록(UH-11) |
| KR1000 2024.4Q | "보완자본만 적용전으로 넘어갔다" → **기본자본도 함께**(32,860 ≈ TFI 적용전 32,859.53) |
| KR0049 2024.3Q | 근거의 절반인 **FY2024_Q4 p36/p42/p43** 을 `citation.also` 에 추가 + `absent_cells`(15~23) 신설 |
| KR0079 2023.2Q | 적용후 박제의 **유일한 근거 페이지 p12**(경과조치 3종 미적용 명시)를 `citation`·`image_verification` 에 추가 |

### F. 배선·회귀

- **push 게이트 위임**: `validate_data_contract.check_census` **1b(vi-b)** 에서 `_absence_pin_census`
  · `_pin_ledger_agreement_findings` 를 호출(재구현 금지 — 소스 검사로 강제).
  K-ICS 게이트에만 배선하면 push 를 못 막는다는 이 저장소의 반복 함정 그대로다.
- `tests/test_exemption_absence_pin.py` **34 케이스** 신설 — 라이브 마스터·라이브 원장 변이시험.
- `scripts/_data_contract_selftest.py` **N8 · N8b · N9 · N10** 추가 → **55/55**.
  덤으로 **기존 N6 이 이 라운드 전부터 FAIL 이던 것을 고쳤다**(픽스처가 `verify: None` 이라
  `EXEMPTION_VERIFIED_WITHOUT_MARKERS` 가 같이 터졌다 — 케이스는 결함을 하나만 심어야 한다).
- `tests/test_tier2_issuer_inconsistent_exemption.py`: KR0087 파라미터 제거 + `_post` 박제 회귀 2건
  추가 + `test_a_post_axis_pin_never_lowers_the_blocking_count` 신설
  (`_post` 박제 도입 직후 blocking RED 가 **-2** 로 찍혔다 — accepted 전체를 차감했기 때문).
- 골든 `tests/fixtures/kics_rules_golden.json` **6차 재생성**(`--update`), 사유는
  `test_kics_rules_golden.py` `_update()` ⑩ 항목. RED 37→36 · GREEN 9,522→9,523 · findings 총계 불변.
- 사고 기록: `docs/postmortems/PM-2026-08-24_absence_exemption_blinded_axis.md` (색인·UH 표 갱신,
  신규 **UH-10 · UH-11 · UH-12**).

### 게이트 실측

```
validate_kics_disclosure.py   EXIT 0 · RED=36 YELLOW=1519 GREEN=9523 SKIP=2586 · blocking RED=0
validate_data_contract.py     EXIT 0 · RED=0 YELLOW=297
validate_data_contract.py --selftest   55/55
pytest tests/ -q              379 passed, 2 skipped
```

## 2026-08-24 (iter-3) — `item47` 스코프 인식 룰 수정 · 한화생명 면제 해제 · 원천 육안판독 원장 신설

iter-2 가 규명한 인과를 코드에 반영하고, 남아 있던 sender 티켓을 닫았다. **inbox 활성 0건.**
`kics_disclosure.json` · `insurequant_master_tables.xlsx` 는 **읽기만 했다.**

### A. 룰 — `item47` 스코프를 회사별로 판정한다 (`src/solvency/validation/kics_json_rules.py`)

한도(`item48`)는 채무성 자본에만 걸린다. 그런데 발행사가 `item47`(보완자본 한도 적용 전)을 두
관행으로 인쇄한다 — **EXCL**(채무성만) / **INCL**(`item49` 포함). 룰은 EXCL 만 알아서 INCL 회사의
**한도 구속 분기**에 한도초과액을 `item49` 만큼 과대계산했다.

- `_tier2_i47_scope_map(buckets, tolerance)` **신설** — 회사별 스코프를 **그 회사 자신의 결정적
  버킷 투표**로 정한다(두 읽기 중 정확히 하나만 공시 보완자본을 재현하는 버킷만 센다).
  **회사 하드코딩 리스트를 만들지 않았다.** 룰엔진과 같은 tol 을 쓴다(OCR 회사 10.0).
  CONFLICT 회사는 종전 관행 EXCL 로 남긴다(근거 없이 새 읽기를 넓히지 않는다).
- `_tier2_branch(..., scope=)` · `_tier2_expected(...)` · `_tier2_debt(...)` — INCL 이면
  `debt = item47 − item49` 로 한도 시험·초과액·**기대값**을 계산한다. 종전에는 갈래를 한 읽기로
  판정하고 `expected` 는 다른 읽기 식으로 인쇄했다(축 F 79칸이 실제로 그랬다).
- 갈래 4 → 6: `I49_IN_I47_CAPPED` · `I49_IN_I47_UNCAPPED` 신설. **기존 이름의 접두사가 아니게**
  지었다 — 게이트·시험이 `"branch=CAPPED" in detail` 이라는 **부분문자열**로 갈래를 읽으므로
  `CAPPED_INCL` 로 지으면 두 갈래가 한 이름으로 뭉개진다.
- `_TIER2_EXCESS_BEARING_BRANCHES` 상수 신설 — 축 A 가 한도초과액을 실제로 더하는 갈래 집합.
  **작업 중 이 은닉 필터를 실제로 밟았다**: 갈래만 만들고 `branch in ("CAPPED","BOTH")` 를 안
  고쳐서 새 갈래가 조용히 초과액 0 이 됐고 시뮬이 "전이 0건" 으로 나왔다.

**전 버킷 시뮬(룰엔진 전층, 양방향)** — 종전 시뮬은 다리만 재구현해서 갈래를 공유하는 축 B·F 의
부수효과를 못 봤다. `run_validation` 산출 전체를 수정 전후로 덤프해 대조
(`scripts/_probes/probe_20260824_findings_snapshot.py dump|diff`):

| | 건수 |
|---|---|
| 새로 닫힘 | **1** (KR0068 2025.2Q `2_tier1_bridge` −30,095.00 → +0.26) |
| 새로 깨짐 | **0** |
| findings 총계 | 13,664 **불변** (finding 키 집합도 동일) |
| 갈래 이름만 변경 | 272 |
| status 동일 + diff 이동 | 12 (KR0075 3분기) |

전체: **RED 38 → 37 · GREEN 9,521 → 9,522.** 골든 `--update` 재생성, 사유는
`tests/test_kics_rules_golden.py` `_what` **5차** 항목.

**두 게이트가 같은 함수를 부르므로 절반만 굳는 경로가 없다** — `validate_data_contract.py` 가
`kics_run_validation` 을 직접 호출한다(재구현 없음).

### B. 면제 — 해제 1 · 박제값 정정 3 (새 면제 0)

- **KR0068 2025.2Q 해제.** 룰 수정 후 게이트가 `TIER2_EXEMPTION_INERT` 로 "등재를 풀어라" 를
  먼저 인쇄했다. 원장 기록은 지우지 않고 `status=CONTRADICTED` + `resolved_note` 로 남겼다 —
  **재등재 시 `EXEMPTION_CITATION_CONTRADICTED` RED 가 즉시 뜬다**(시험으로 흔들어 확인).
- **KR0075 2024.3Q·2024.4Q·2025.1Q 박제잔차 6개 갱신**(해제 아님). 스코프 정정으로 기대식이
  바뀌어 잔차가 이동했다(−220.98→+14.86 등). **마스터 셀은 한 칸도 안 움직였다.** 새 값이
  **다리 잔차와 수렴**하는 것이 방증(구성 +14.86 vs 다리 +15 · +87.22 vs +87) — 종전 값은 서로
  다른 두 불일치가 있는 것처럼 보이게 했다. 종전 값은 `expected_residual_alt_reading` 에 보존.
- **KR0075 의 INCL 판정이 오염된 셀에 기대는지 따로 확인했다** — 그 회사는 문제의 3분기에
  `item47 == item48`(이미 `TIER2_DUPLICATE_ROW` 플래그)이라 순환 위험이 있었다. 실측 결과
  INCL 표 18개는 전부 `item47 ≠ item48` 인 나머지 9분기에서 나온다
  (`scripts/_probes/probe_20260824_kr0075_scope_evidence.py`). 같은 실측이 종전 게이트 주석의
  오류도 드러냈다("채무성 자본이 0인 회사라서" → 틀렸다, 9분기 채무성은 53~159억). 주석 정정.
- **면제를 지탱하던 시험 6건은 지우지 않고 이전·fixture 화**했고 삭제/이전 이유를 코드에 남겼다.
  특히 `VERIFIED_BY_OWNER` 배선 시험 3건은 살아 있는 항목이 0 이 됐지만 **fixture 로 유지**했다
  — 지우면 다음 owner 판단 면제 때 배선이 이미 썩어 있는지 아무도 모른다. 레지스트리 크기 19→18.

### C. 원천 육안판독 원장 신설 — `SOURCE_UNREADABLE_NOT_VERIFIED` 20 → 0

`validate_data_contract.py` 가 매 라운드 같은 YELLOW 20줄을 찍는데 그 20칸은 이미 원문으로
판정이 끝나 있었다(폰트 유니코드 매핑 실패라 렌더링하면 읽힌다). 판정을 게이트에 안 넣으면
아무도 안 보게 되고, 나중에 **진짜 미판독 칸이 섞여도 안 보인다.**

- `data/_gold/kics_source_vision_verified.json` **신설**(10쌍, 생성기
  `scripts/fix_20260824_register_source_vision.py`). 필수: 판독자·판독일·판독방식·raw 경로·
  본 페이지(0-idx + 인쇄쪽수)·**인쇄된 문구**·기계검증 불가 사유·박제 셀·**sender 재현 깊이**.
- 게이트 배선: 필수필드 결손 **RED** · 박제셀 결측 **RED** · **주장(적용후=적용전) 붕괴 RED** ·
  값 드리프트 YELLOW · 통과해도 **매 실행 인쇄**(`SOURCE_VISION_VERIFIED`) · 무용해지면
  `SOURCE_VISION_INERT`. **원장이 사라지면 조용히 통과가 아니라 종전 YELLOW 로 되돌아간다.**
- 변이시험 **23건**(`tests/test_source_vision_verified.py`) — 배선 확인(순수함수만 돌고 게이트가
  안 부르는 상태 차단) + **회사마다 원 sender 직접 재현분 최소 1건 강제** 포함.
- **줄 수는 그대로 20 이다. 침묵시킨 게 아니다** — 이제 진짜 미판독이 생기면
  `SOURCE_UNREADABLE_NOT_VERIFIED` 가 0 에서 튄다.

**sender 재확인은 답변을 베끼지 않았다.** 4개 회사 각 1분기(TFI=**O·X·UNKNOWN** 전부 포함)를
직접 렌더링해 판독했고, 10쌍 전수로 기계적 필요조건(`item1·14·15·17·19·27` 60칸 전==후,
지급여력비율 소수 8자리까지 동일)을 따로 걸었다
(`scripts/_probes/probe_20260824_unreadable_pairs_recheck.py`).
**답변의 진단 한 줄은 반증했다** — "대상 페이지는 읽히는데 문서 평균 때문에 UNREADABLE" 은 틀렸다.
인용 페이지가 문서 평균보다 **더** 안 읽힌다(34.0 vs 68.9 · 13.5 vs 262.7 · 2.0 vs 5.8 ·
0.0 vs 1.2 자/p). 제안대로 사이드카를 대상 페이지 기준으로 바꾸면 YELLOW 가 **는다** → 미채택.
부수로 답변의 페이지 idx 가 1-idx 였음도 확인(KB손해 2025.3Q 실측 0-idx 16·17) — 원장에는
내가 직접 연 페이지만 `pages_verified_by_sender: true`.

**부수 확증**: 미래에셋생명 2025.1Q p17 TFI 표가 `한도적용전 1,058,020 = 후순위채무 303,030 +
해약환급금 초과분 754,990` 으로 마지막 자리까지 닫힌다 — **INCL 관행의 두 번째 독립 증거**
(첫 증거는 한화생명 2025.2Q). 같은 표에서 KR0079 의 item47~54 전 분기 결측도 재확인(parser 몫,
다른 스레드가 다루는 중이라 새 발주는 안 했다).

### D. 사고 기록

`docs/postmortems/PM-2026-08-24_i47_scope_misread.md` **신설(5칸 = `closed`)** + 색인·UH 표 갱신.
이 사고의 유형은 false-green 의 쌍둥이다 — **룰이 한 관행만 알면, 다른 관행 회사의 잔차가
'발행사가 이상하다' 로 읽히고 면제로 조용해진다(룰의 결함이 발행사의 결함으로 세탁된다).**
신규 **UH-9**(회사 단위 스코프 투표는 관행이 시간에 따라 바뀌는 발행사를 못 담는다 — KB손해가
2025.2Q 에 INCL→EXCL). **분기 단위 판정은 만들지 않았다** — 측정된 이득 0(전수 시뮬 status 전이
0건), UH-5 선례(오탐억제를 설계할 수 없으면 배선하지 않는다). 발화 조건과 감지 경로를 UH 표에 박았다.

### E. 게이트 실측 (exit code)

```
scripts/validate_kics_disclosure.py   -> EXIT 0 · RED=37 YELLOW=1519 GREEN=9522 SKIP=2586 · blocking RED=0
scripts/validate_data_contract.py     -> EXIT 0 · RED=0 YELLOW=296 provisional=False
pytest tests/ -q --ignore=tests/test_pl_breakdown_golden.py --ignore=tests/test_ifrs17_bs_golden.py
                                      -> 343 passed, 1 skipped  (직전 318)
scripts/check_inbox_hygiene.py        -> EXIT 0 · 활성 0 · 위반 0
```

### F. 범위 밖 발견 (수정 안 함, 별도 티켓)

`scripts/validate_data_contract.py --selftest` 가 **50/51** — `N6 EXEMPTION_LEDGER_SCHEMA_INVALID`
케이스가 실패한다. 관련 4파일을 HEAD 로 되돌려도 재현되므로 **이번 라운드 이전부터 깨져 있었다.**
게이트 자신의 자기시험이 조용히 실패 중인 상태(= 이 저장소가 명문화한 "게이트 자신의 검사범위를
의심해라" 의 정확한 형태)라 별도로 분리했다.

### G. 종결한 티켓

- `inbox/_resolved/20260824T0410Z__validation__KR0068_2025.2Q__tier1_bridge_residual_unexplained.md`
  (`resolved`, iter-3) — 원인 규명 → 룰 수정 → 면제 해제까지 자기완결.
- `inbox/_resolved/20260821T0620Z__validation__MULTI__meta_rules_wired_axis_and_provenance.md`
  (`resolved`, iter-2) — sender 종결. §3 을 판정 + 원장 등재 + 게이트 배선으로 닫았다.

---

## 2026-08-24 (iter-2) — KR0068 한화생명 2025.2Q `2_tier1_bridge` −30,095 의 인과 규명

**결론: 발행사 자기모순이 아니었다. 우리 룰이 `item47` 의 스코프를 잘못 가정하고 있었다.**

`item47`(보완자본 한도 적용 전)이 `item49`(해약환급금 부족분 상당액 중 해약환급금 상당액
초과분)를 포함하는지 여부가 **발행사마다 다르다.** 룰은 "포함하지 않는다"만 알고
`한도초과 = max(0, item47 − item48)` 을 쓴다. 한화생명은 포함하는 관행이라 그 값이 `item49`
만큼 과대해진다(70,821.29 대신 825.74).

원문 실측(`data/disclosure/FY2025_Q2/raw/KR0068_한화생명.pdf` p18, 백만원):
`한도적용전 14,012,828 − 해약환급금 6,999,555 = 채무성 7,013,273 > 한도 6,930,699`
→ 초과 **82,574(=825.74억)** → `보완자본 = 6,930,699 + 6,999,555 = 13,930,254`(인쇄 13,930,253).
주2) 각주대로 `213,475 − (30,921 − 825.74) − 100,874 = 82,505.74` vs 인쇄 `82,506` → **잔차 0.26**.

- **13분기 중 한도가 실제로 구속하는 분기는 2025.2Q 하나뿐이다.** 2025.1Q 채무성 5,792,383 <
  한도 6,838,221 · 2025.3Q 7,023,226 < 7,122,730. 그래서 나머지 12분기는 `item3 == item47` 이
  되어 룰이 `UNCAPPED`(한도초과=0)로 우연히 맞혔고, 구속하는 그 한 분기만 `CAPPED` 로
  오분류돼 과대 한도초과가 다리에 들어갔다.
- **iter-3 §2 의 "보완자본 = 한도적용전 그대로(한도로 안 잘림)" 는 오독이었다** — 한도가 안
  걸린 분기를 관행으로 일반화한 것. 적용후만 안 잘리고 적용전은 정확히 잘린다.
- **`item12` 는 정상.** 클램프(`min(raw_exc, item12)`)는 틀린 `raw_exc` 를 가린 밴드에이드였다.
  클램프 발동 10칸 대조군에서 배율이 1.00~1.12 인 9칸과 달리 한화생명만 2.29 배이고,
  `70,821.29 − 825.74 ≈ 69,995.55 = item49` 로 그 차이가 정확히 `item49` 다.

**가설을 먼저 반증했다(§3.1 규율).** "모든 회사가 포함 관행" 가설은 전수에서 구성식 461칸 ·
다리 31칸을 깨뜨려 **기각**. 회사 속성으로 좁힌 뒤 전수 투표 = EXCL 27사 · INCL 5사
(KR0004·KR0068·KR0075·KR0079·KR0080) · CONFLICT 4사. 원문 대조군 **IBK연금 2025.3Q(EXCL)**
p16 은 `한도적용전 403,778 < 보완자본 695,572` 로 정반대 구조를 인쇄한다 — 두 관행이 같은 행
이름으로 존재한다는 직접 증거.

**스코프 인식 한도초과 전수 시뮬레이션: 새로 닫히는 칸 1 · 새로 깨지는 칸 0**(나머지 600칸 무변화).

**그런데 룰은 고치지 않았다.** 이 수정은 ① 룰엔진 ② `test_kics_rules_golden.py`(라이브 마스터에
물림) ③ 게이트 박제값 ④ 면제 원장 ⑤ 변이시험 4~6건을 **한 커밋에서 동시에** 움직여야 하는데,
당시 다른 세션이 `kics_disclosure.json` 을 편집 중이었다. 그 상태로 골든을 `--update` 하면
반쯤 쓰인 마스터가 박제된다(이 저장소의 lost-update 전례). → 후속 티켓으로 이월.

**면제는 해제하지 않고 사유만 정정했다** (`scripts/fix_20260824_kr0068_exemption_reason.py`).
지금 풀면 룰이 여전히 −30,095 를 내므로 RED → push 차단이다. 자유텍스트 6곳
(`claim`·`claim_kind`·`note`·`open_lead`·`scope`·`release_condition`)만 고치고 박제값·status·
마커·허용오차는 무변경. 특히 `note` 의 **"어느 해석에서도 826/30,095 에 해당하는 항목은 원문에
없다" 를 반증으로 정정**했다 — 826 은 p18 세 행에서 산식으로 나온다.

실측: `validate_kics_disclosure.py` exit 0, RED 라인·Top RED offenders 가 정정 전후 **완전 동일**,
`pytest` 142 passed. 프로브 5종 + raw 덤프는 `scripts/_probes/probe_20260824_*` ·
`artifacts/validation/probe_20260824_*.txt`.

## 2026-08-24 (3차, 잔여 inbox 6건 정리) — 가설 5연속 오답 경위 기록 + 티켓 3건 종결·3건 존속

**owner 지시**: 남은 inbox 6건("`inbox/parser/20260821T0620Z, 1745Z, 1900Z, 2010Z, 20260824T0400Z`,
`inbox/validation/20260824T0410Z`")을 확인하고, 이번엔 서브에이전트 4개가 전부 API 529(모델
과부하)로 죽어서 직접 스크립트로 재확인했다. owner 사전 판단: "실제로 원본 데이터 단에서
발생한 오류고 우리가 고칠 건 없지싶다" — 아래 실측이 대체로 이 판단과 일치한다.

### A. 가설 5연속 오답 경위 (`docs/agents/claude-agent-validation.md` §3.1 규율의 근거)

2026-08-21~24 TFI(공통적용경과조치)/tier2 표 작업 중 다섯 가설이 전부 반증됐다:
1. **"적용후 429/430 이 동일=복사"** → 215:0 전수 실측으로 반증. `item48_적용후` 는 항상
   `item14_적용전 × 50%` 를 따르는 것이었다 — TFI 스코프 ≠ 결합 스코프.
2. **"item3==item13 이면 분기 처리"** → 147건 중 125건이 이미 통과 중이었고, 나머지 47/49
   축이 검사 밖으로 빠지는 수정이라 반려.
3. **"다른 분기에 표가 있으니 추출 갭"** → 해당 회사(교보라이프플래닛) 7개 분기 전수 확인,
   표 자체가 원문에 없음(정당 부재).
4. **"적용후를 item1_적용전과 비교"** → raw 대조 결과 IBK연금 1개사만 일치, 나머지는 원문
   구조 자체가 다름.
5. **"47==48 이면 item49 를 초과분으로"** → 전수 시뮬레이션 통과 423→295, **1건 고치고
   129건 깨짐**(`feedback_simulate_rule_change_before_editing` 메모리에도 등재).

owner: "가설 다섯번 세워서 다섯번 틀리면 니가 가설 세우는 방식을 재고해야 하는거 아니야?"
사후진단 — 다섯 건 전부 **집계 패턴 → 원인을 반증쿼리 없이 추론**했고, 정보 흐름이 거꾸로였다
(집계만 쥔 orchestrator 가 raw 를 쥔 서브에이전트에게 원인을 지시). 규율화: 원인은 반증쿼리
1건을 직접 돌린 뒤에만 발주문에 적는다, 못 돌렸으면 관측+질문으로만 적는다(§3.1) · 룰 코드
수정은 편집 전 전수 시뮬레이션 필수(§3.1, `feedback_simulate_rule_change_before_editing`).
메모리 신설: `feedback_verify_cause_before_dispatch`.

### B. 티켓별 실측 결과 (오늘, 직접 재현 — 서브에이전트 결과 아님)

| 티켓 | 실측 | 처리 |
|---|---|---|
| `20260821T1900Z` csm_waterfall 게이트 미배선 | `validate_csm_waterfall.py` 재실행 → **exit 0, pass=41 fail=0**(구조적 제외 6건). `prepush_check.py` 1c·`test_push_gate_wiring.py` WIRED 양쪽 다 확인됨 | **resolved** — 이미 다른 라운드에서 닫혀 있었다 |
| `20260824T0400Z` item52/54 결함 7건(카카오페이 100배 등) | 카카오페이(KR1098) item52 현재값이 전 분기 item50 과 정확히 일치(억원 스케일) 확인. 게이트 baseline: RED 38 전부 tier2 면제(37)+8_life(1)로 설명됨, 미설명 RED 0 | **resolved** — 이미 커밋 04f5fe0 에서 fix 반영됨 |
| `20260821T0620Z` 메타룰 3종 | 항목1(면제근거 거짓 2건) 이미 ✅. 항목2(`AXIS_SELF_MIRRORED_APPLIER`·`AXIS_NOT_EVALUATED`, 동어반복 오판정) 재실행 **둘 다 0건** — 이미 게이트 쪽에서 분모를 구조인식으로 고쳐 해소돼 있었다. 항목3 `SOURCE_UNREADABLE_NOT_VERIFIED` 는 `validate_data_contract.py` 에서 **20건 YELLOW**(KB손해보험·미래에셋생명·AIA생명 각 2025.1/3Q·2026.1Q, 동양생명 2026.1Q) 살아있음 — non-blocking. 10쌍 중 1쌍(KB손해 2025.1Q)은 티켓 자체가 이미 vision 판독으로 "폰트매핑 문제일 뿐 값은 정확·휴리스틱만 영구 YELLOW" 확인 완료, 나머지 9쌍은 미판독 | **파일은 open 유지**(티켓 자신이 "항목3 때문에 열려있다"고 명시) — 항목1·2 재확인만 추가, 항목3 은 TODO 로 이월(downloader 후보, 아래 C) |
| `20260821T1745Z` viz 패널 3종 단위 분열 | `git diff main` 재확인 — 3파일(`sensitivity_heatmap`·`csm_waterfall_history`·`csm_amort_schedule`) 전부 아직 main 과 다름, 화해 안 됨. raw 단위 확정 작업(카카오페이손해 천원/백만원)은 미착수 | **open 유지** — 화면 숫자 바뀌는 변경이라 확정 전 배포 불가, 다음 라운드로 이월 |
| `20260821T2010Z` leaf residual 4셀 | `leaf_scale_residue_audit.py` 재실행 — **불일치 4건 그대로**(예별손해보험 item36_적용후 ×3, 처브라이프생명 item35 ×1). 1030Z 의 안전가드(부모19 재현실패 HOLD)가 여전히 유효 | **open 유지** — raw 레벨 조사 필요, 다음 라운드로 이월 |
| `20260824T0410Z` 한화생명 KR0068 tier1_bridge | 직접 측정: **KR0068 13개 분기 중 2025.2Q 만 diff +826**(2025.3Q/2026.1Q 는 반올림 ±1, 나머지는 정확히 0) — 이웃 분기 대조(티켓 §4-2)에 답. raw p17 재확인: 헤드라인(221,809=82,506+139,303)·순자산 구성행(합 213,476, 반올림 1)·주2) 각주 전부 마스터와 일치, 모순 위치는 여전히 못 짚음 | **open 유지**(티켓 자체가 "인과 규명 전 close 불가"로 명시) — §4 조사 방향(item12/47 스코프)에 단일분기 확증만 추가 |

### C. TODO 이월 (2026.2Q 재검토, 서브에이전트 배정 예정)

- **kics parser**: 예별손해보험 item36_적용후 3셀 + 처브라이프생명 item35 1셀 —
  `scripts/_probes/leaf_scale_residue_audit.py` 로 재현, 부모19 HOLD 가드부터 확인.
- **ifrs17 parser**: viz 패널 3종(카카오페이손해 민감도 단위, `companies[15]` 워터폴, amort
  캡션/버킷) — DART 원문 단위표기부터 확정, `git diff main -- data/dart/viz/*.json` 로 재현.
- **downloader 후보**: `SOURCE_UNREADABLE_NOT_VERIFIED` 20건(KB손해보험·미래에셋생명·AIA생명
  2025.1/3Q·2026.1Q, 동양생명 2026.1Q) — raw 판독성(스캔/저해상도) 확인 후 refetch 여부 결정.
  YELLOW 라 push 는 안 막지만 방치 금지.
- **validation 자체**: 한화생명 KR0068 2025.2Q 인과 — `inbox/validation/20260824T0410Z` 그대로
  열어둠(exemption `VERIFIED_BY_OWNER` 로 push 는 안 막힘).

---

## 2026-08-24 (2차 owner 위임) — tier2/다리 면제 4건 등재 · `VERIFIED_BY_OWNER` provenance status 신설

**게이트**: `validate_kics_disclosure.py` exit 2 · RED 56 · **blocking RED 29 → 19**.
`validate_data_contract.py` RED **7 → 5**(잔여 5건 전부 parser 발주분).
`pytest tests/ -q --ignore={pl_breakdown,ifrs17_bs}_golden` **318 passed · 1 skipped**(직전 302).
**골든 무변경** — 룰 엔진을 안 건드렸다(면제는 findings 매트릭스 밖의 층이다).
`kics_disclosure.json` · `insurequant_master_tables.xlsx` **읽기만** 했다(parser 가 동시 작업 중).

**등재 4건.** 앞의 셋은 새 조사가 아니라 **이미 확증돼 있었는데 위임 목록 밖이라 두 라운드를
RED 로 버틴 것들**이다(면제를 스스로 넓히지 않는다는 원칙의 비용). 값은 티켓에서 베끼지 않고
raw 를 다시 열어 독립 재현했고 전부 일치했다.

| 버킷 | 축 · 박제 잔차 | 사유 |
|---|---|---|
| KR0004 예별손해 2025.1Q | `3_tier2_composition` **+997.00** | 합계는 두 표가 같은데 tier 분할만 다르다 — TFI 표가 보완자본 997억을 기본자본 쪽에 합쳐 인쇄(자본잠식사). 다리·TFI 구성식은 둘 다 정확히 닫힌다 |
| KR0003 롯데손해 2023.1Q | `2_tier1_bridge` **+19.00** · `3_tier2_composition` **−19.00** · `50_tfi_tier_split` **−18.00** | 두 표가 '적용 전 보완자본' 을 17,812/17,830 으로 다르게 인쇄 + TFI **적용전 컬럼만** 자기 합계행과 안 닫힘(적용후는 정확히 닫힌다 → 추출 결함일 수 없다). 세 축이 같은 18~19 를 가리키고 **부호가 정확히 반대** |
| KR0075 BNP카디프 2024.3Q | `2_tier1_bridge` **+15.00** · `3_tier2_composition` **−220.98** · `47_tier2_census`(전·후) · `51_tfi_tier2_composition` **−221.31** | 2024.4Q·2025.1Q 와 증거 동일. `min(31,614,31,614)+23,584 = 55,198` vs 인쇄 `33,067`, 메모행 둘 다 대시라 메울 행이 없다 |
| **KR0068 한화생명 2025.2Q** | `2_tier1_bridge` **−30,095.00** | **인과 미규명.** owner 가 raw 를 직접 열어 보고 "원문이 그렇게 적혀 있고 별다른 언급은 없다 — 원문대로 오차 용인" 결정 |

**신설: 원장 status `VERIFIED_BY_OWNER`.** 나머지 17건은 발행사 자기모순을 **산수로** 증명하지만
한화생명은 **잔차가 실재하는데 원문 어디에도 그 항목이 없다.** 같은 `VERIFIED` 로 적으면 다음
세션이 인과가 규명된 것으로 오독한다 — 이 저장소의 반복 실패모드다. 게이트에 배선한 것:
① **마커 검사는 `VERIFIED` 와 동일하게 그대로 건다**(owner 판단이 숫자 재확인을 면제하지 않는다),
② `owner_confirmation`{read_by, date, what_was_read, verdict} 필수 —
누락시 `EXEMPTION_OWNER_RECORD_INCOMPLETE` **RED**,
③ 매 실행 `EXEMPTION_STANDS_ON_OWNER_JUDGEMENT` **review** 로 인쇄(조용해지지 않는다).
후속 티켓 `inbox/validation/20260824T0410Z` 는 **open 유지** — 면제는 push 를 푼 것이지 원인을
닫은 것이 아니다. 미규명 단서(item51 후−전 = 825.75 ≈ 826)는 사유가 아니라 해제조건 메모로만 적었다.

**🔴 발주된 박제값이 룰이 내는 값과 달랐다 — 기록해 둔다.** owner 에게 제시된 한화생명 잔차는
**826.00**(각주 괄호 "보완자본 한도 초과액 제외" 를 무시한 읽기)인데, 룰이 emit 하는 diff 는
**−30,095.00**(`branch=CAPPED`: 한도초과 = `min(item47−item48, item12)` = `min(70,821.29, 30,921)`
= 30,921 클램프). **826 을 그대로 박았으면 등재 즉시 `TIER2_EXEMPTION_RESIDUAL_DRIFT` RED 라
면제가 성립조차 안 한다**(실측). 박제는 owner 에게 보고된 숫자가 아니라 **룰이 내는 값**이어야
매 실행 재검산이 성립한다. 두 값을 원장에 **둘 다** 적고
(`expected_residual` / `expected_residual_alt_reading`) 테스트로 강제했다 — 안 적으면 다음 세션이
"박제값이 발주와 다르다" 로 읽고 826 으로 고치거나 허용오차를 건드린다.

**등재하지 않은 것.**
- **KR0008 삼성화재 2025.3Q** — owner 결정이 "면제" 가 아니라 **"우리가 고친다"** 다.
  등재하면 정정 후에도 죽은 핀이 남아 "그 축은 면제됐다" 로 오독된다(지난 라운드에 롯데
  2026.1Q 죽은 핀을 `TIER2_EXEMPTION_INERT` 로 잡아낸 그 형태). parser 정정 중.
- **KR0032 NH농협손해 2024.3Q** — 다리 잔차 −522, **미조사**. 조사 전 등재는 추측이다.
`test_the_exemption_is_narrow_and_does_not_touch_the_held_buckets` 가 두 버킷을 기계로 막는다.

**변이시험**: `tests/test_tier2_issuer_inconsistent_exemption.py` **28 → 47건**. 신규 등재 4버킷을
셀·축 양 겹으로 흔들고(한화생명은 발주 요구대로 **다리 입력 4칸 item2·4·12·13 을 각각**),
`VERIFIED_BY_OWNER` 계약 4건(owner 블록 누락 RED · 마커 누락 RED · review 상시 인쇄 ·
두 잔차 병기)을 추가했다.

**변경 파일**: `scripts/validate_kics_disclosure.py` · `data/_gold/kics_exemption_provenance.json`
(entries 34 → 38) · `tests/test_tier2_issuer_inconsistent_exemption.py` · `TODO.md` ·
`TODO_validation.md` · 티켓 2건 회신. **허용오차 무변경. 커밋·push 안 했다.**

---

## 2026-08-24 (iter-7) — item52/53/54 배선: 축 E 등식 승격 · 축 G 신설 · 항목번호 등록부

**게이트**: `validate_kics_disclosure.py` exit 2 · RED 56 · **blocking RED 13 → 29**
(기존 11 잔존 + 신규 18 − NH농협 면제 2). `validate_data_contract.py` RED 4 → 7.
`pytest tests/ -q --ignore={pl_breakdown,ifrs17_bs}_golden` **302 passed · 1 skipped**.

**무엇이 통과하고 있었나 (false-green)**: parser iter-10 이 item52/53/54 를 1,291셀 적재했는데
그 항목을 보는 룰이 하나도 없었다. `tests/test_rule_coverage_manifest.py` 가 즉시 실패로 잡았고
(설계대로), 룰을 배선하자 **GREEN 이던 18칸이 RED 로 뒤집혔다.** 전부 raw PDF 로 확정:
카카오페이 5버킷 item52 100배 · 처브라이프 item54 원문에 없는 값 · 농협생명 적용후 값 없음 ·
푸본현대 컬럼 오배정 · 행 유실 3건 · 동양 2024.3Q 미확정 · 삼성화재 발행사 자릿수 전치.

**배선**:
- `50_tfi_tier_split{,_post}` — comparand 를 item1(헤드라인)/범위검사 → **item52**(같은 표·같은
  컬럼)로 승격. 적용후 YELLOW 70 → 69칸이 등식으로 닫히고 GREEN 6칸이 RED 로 뒤집혔다.
  item52 결측 30버킷은 폴백 + `TFI_TOTAL_ROW_ABSENT` 사유로 매 실행 세어진다.
- `53_tfi_memo_rows{,_post}` **신설** — census(적용전만) + 부호 + `53+54 ≤ item51`.
  등식(`+item54`)은 **안 걸었다**: 전수 시뮬 새로 닫힘 1 · 새로 깨짐 218.
  포함관계 후보 `≤47`·`≤52` 는 raw 로 반증(DB생명 · 푸본현대 자본잠식).
- 레지스트리 2종(`_TFI_MEMO_ISSUER_BLANK` 12칸 · `_TFI_MEMO_TABLE_NOT_SCANNED` 20버킷) —
  결측 사유를 셋으로 갈라 우리 backlog 를 발행사 탓으로 박제하지 않는다.

**면제**: NH농협 2025.4Q 등재(iter-6 거부 판단을 뒤집었다 — 근거가 바뀌었다). 롯데 2026.1Q 의
축 E 핀 2개 제거(승격으로 그 축이 닫힘, 게이트가 `TIER2_EXEMPTION_INERT` 로 먼저 알림).

**재발방지**: `data/_gold/kics_item_registry.json` + `tests/test_kics_item_registry.py`.
오늘 두 레인이 52 를 동시에 잡았고 게이트가 **우연히** 잡았다 — 예약이 산문에만 있었다.
47~54 등재, 1~46 은 명시적 미등재 선언. `reserved` 번호에 데이터가 들어오면 테스트가 막는다.

**변이시험 신설** `tests/test_tfi_memo_rows.py` 10건 — 세 검사의 RED 발화 + 두 레지스트리가
면제로 넓어지지 않는 것 + 축 E 폴백이 조용하지 않은 것을 라이브 마스터로 강제.

**데이터 무변경**: `kics_disclosure.json` · `insurequant_master_tables.xlsx` 읽기만. 허용오차 무변경.
골든은 `--update` + `_what` 에 사유 기록. 커밋·push 안 함.


## 2026-08-24 — tier2/다리 발행사 자기모순 documented exception 등재 (13버킷 26 finding), blocking RED 39 → 13

owner 가 이번 라운드 등재까지 위임했다. `inbox/parser/20260821T1425Z` iter-6.

### 등재 전에 갈래를 기계로 갈랐다

후보를 눈으로 고르지 않고 두 질문으로 전수 분류했다 — ① TFI 표가 **자기 구성행으로 닫히는가**
(`item51 == min(47,48)+49`, 같은 표·같은 컬럼) ② 그런데 헤드라인 `item3` 과는 다른가. 그 다음
후보 전부를 raw PDF `get_text("words")` 좌표로 직접 열어 확인했다. parser iter-8·iter-9 값과
1원 단위까지 일치했지만 **베끼지 않고 독립 재현**했다.

### 두 계열, 사유를 구분해 적었다

- **계열 ① 두 표가 서로 다른 값을 인쇄** — 코리안리 2023.2Q~2024.4Q(7) · 롯데손해 2026.1Q(1).
- **계열 ② 한 표가 자기 구성행과 안 닫힌다** — 롯데 2024.4Q·2025.1Q · BNP 2024.4Q·2025.1Q ·
  동양생명 2025.2Q.

**owner 발주서의 사유 하나를 실측으로 바꿔 적었다.** 롯데 2024.4Q 는 "공시 보완자본 28,030 vs
min(47,48)+49 = 28,033.4" 로 계열 ①처럼 적혀 있었는데, 실측하면 `item51 = 28,030.38` 이라
헤드라인과 **같다** — 계열 ②다. 사유가 틀린 면제는 다음 세션의 잘못된 일반화 씨앗이 된다.

### 코리안리 — 7분기 전수 raw 판독이 이번 조사의 핵심

```
분기      헤드라인(억)   TFI 적용전(백만)      TFI 적용후(백만)
2023.2Q      5,209        619,243=6,192.43      520,920=5,209.20
2023.3Q      5,114        610,272=6,102.72      511,364=5,113.64
2023.4Q      5,470        646,944=6,469.44      546,989=5,469.89
2024.1Q      5,490        651,623=6,516.23      548,988=5,489.88
2024.2Q      5,444        650,396=6,503.96      544,394=5,443.94
2024.3Q      5,996        707,693=7,076.93      599,602=5,996.02
2024.4Q      8,953        895,327=8,953.27      786,267=7,862.67   <- 여기서 뒤집힌다
```

2023.2Q~2024.3Q 는 헤드라인 = TFI **적용후**이고 TFI 적용전은 자기 구성행으로 정확히 닫힌다.
2024.4Q 에서 보완자본만 적용전으로 넘어갔는데 `Ⅲ.재분류항목`(7,863)은 적용후(7,862.67) 그대로라
다리가 정확히 그 차액(−1,090)만큼 깨진다. **독립 방증**: FY2024_Q4 필링의 직전분기 열이 2024.3Q
보완자본을 **7,077**(= 그 분기 `item51_적용전`)로 재게시한다 — 그 분기 자기 필링의 헤드라인은
5,996 이었다. 같은 셀을 두 필링이 다른 값으로 인쇄한다.

잔차가 −983 ~ −1,081 로 분기마다 다르다(TFI 재분류액 자체가 분기마다 달라서다) → **분기별로 따로
박았다.** 하나로 뭉치면 그 순간 blanket skip 이다.

### 면제를 두 겹으로 짰다

`_LIFE8_ISSUER_INCONSISTENT` 는 잔차 한 겹만 박는다. 이번 것(`_TIER2_ISSUER_INCONSISTENT`)은
두 겹이다:

| 겹 | 박제 대상 | 깨질 때 |
|---|---|---|
| ① `cells` | raw 로 판독한 마스터 셀 | `TIER2_EXEMPTION_INPUT_DRIFT` / `..._INPUT_MISSING` RED |
| ② `findings` | 그 축이 실제로 내는 RED 의 **잔차 + 사유 플래그** | `..._RESIDUAL_DRIFT` RED · 사라지면 `..._INERT` review |

①만 있으면 룰이 바뀐 것을 못 보고, ②만 있으면 데이터가 바뀐 것을 못 본다. 사유 플래그까지 박는
이유는 잔차만 보면 **같은 축이 다른 사유로 깨진 것**을 못 잡기 때문이다(`TIER2_LIMIT_STALE` 자리에
`TIER2_DUPLICATE_ROW` 가 와도 통과해 버린다). finding 자체는 안 지운다 — report 의
`tier2_issuer_inconsistent_exception.exempted_findings` 에 남는다.

변이시험 **28건** 신설(`tests/test_tier2_issuer_inconsistent_exemption.py`). 합성이 아니라
**라이브 마스터**를 흔든다 — 합성이면 "코드가 돈다"만 보이고 "등재된 13버킷이 실제로 재검산된다"는
안 보인다. 그 구분이 정확히 false-green 의 자리다.

### 등재를 스스로 넓히지 않았다 (기계로 강제)

`test_the_exemption_is_narrow_and_does_not_touch_the_held_buckets` 가 보류 버킷이 면제로 새어
들어가지 않는 것 **+ 실제로 RED 로 남아 있는 것**을 둘 다 검사한다.

**BNP카디프 2024.3Q 는 2024.4Q·2025.1Q 와 증거가 동일한데도 등재하지 않았다** — owner 위임 목록
밖이기 때문이다. TODO 와 게이트 report 의 `not_registered` 에 그 사실을 적어 RED 로 남겼다.

### NH농협손해 2025.4Q — 등재하려다 반대 결론이 나왔다

raw `FY2025_Q4/KR0032` p46:

```
보완자본                1,240,112
 보완자본 한도 적용 전     697,899
 해약환급금 … 초과분       447,254
 (기발행 후순위채무)        94,959
```

`697,899 + 447,254 + 94,959 = 1,240,112` — **인쇄된 보완자본과 마지막 자리까지 정확히 같다.**
잔차 949.59억이 그 후순위채무 행과 1원 단위로 일치한다. 발행사 자기모순이 아니라 **`min(47,48)+49`
라는 우리 식에 항이 모자란 것**이다 → parser 발주(메모행 2개 적재 + 전사 census). 면제로 덮으면
우리 결손이 발행사 탓으로 박제된다. BNP 는 같은 두 행이 **둘 다 대시**라 이 설명이 안 통한다 —
그래서 NH농협만 갈라냈다.

### 게이트 사각 하나를 같이 메웠다 — 면제를 위임하지 않고 있었다

등재 직후 `validate_data_contract.py` 를 돌리니 **RED=25** 였고 **그중 21건이 방금 등재한 면제분**
이었다. 그 게이트는 K-ICS 룰을 `kics_run_validation` 으로 **위임**해 RED 를 들어 올리면서
**면제 층은 위임하지 않고 있었다.** 두 게이트가 같은 finding 에 서로 다른 대답을 하면 등재가
조용히 무효가 되고, 다음 사람은 그 불일치를 다른 곳을 넓혀서 푼다.

같은 함수를 부르도록 위임을 배선했다 — **복사가 아니다.** 면제 재검산이 두 벌이 되는 순간 한쪽만
깨지는 경로가 생긴다(코드 자신이 §1b(ii) 에 적어 둔 duplicate-and-drift 회피와 같은 이유).
`8_life` 도 같이 배선했다(현재는 분기 필터에 걸려 미발화지만 같은 모양의 구멍이다). 면제가 깨져
있으면 그 자체가 RED 로 나간다 — 빠지는 것은 매 실행 재검산에 통과한 면제뿐이다.
`validate_data_contract.py` **RED 25 → 4.** `test_..._delegates_the_exemption_not_only_the_rules`
가 소스에서 이 위임을 강제한다.

### 남은 blocking RED 13 · 라우팅

| 버킷 | 건 | 다음 행동 |
|---|---|---|
| KR0075 2024.3Q | 5 | owner 승인만 있으면 즉시 등재 가능(증거 확정) |
| KR0032 2025.4Q | 2 | parser 발주 — 신종/후순위 메모행 적재 + 전사 census |
| KR0003 2023.1Q | 3 | owner 승인 대기(TFI 표 자기합 25,864 ≠ 자기 지급여력금액 행 25,846) |
| KR0032 2024.3Q | 1 | 미조사(다리 잔차 −522) |
| KR0068 2025.2Q | 1 | 후속 티켓 — `item51_후 − item51_전 = 825.75` ≈ 다리 잔차 826, **인과 미규명** |
| KR0004 2025.1Q | 1 | 두 표 스코프 통합 규칙 정의 시 재평가(다리는 이미 닫혀 있다) |

**한화생명을 RED 로 남긴 것이 이 라운드의 판단이다.** 825.75 ≈ 826 은 흥미롭지만 인과가 안
밝혀졌다. "거의 같다"를 근거로 면제하면 패턴을 원인으로 단정하는 것이고, 그건 이 저장소가
반복해서 데인 실패모드다.

### 게이트·테스트

- `validate_kics_disclosure.py` exit 2 · RED=40 · **blocking RED=13**(= 40 − `8_life` 1 − tier2 26).
  박제 26건 전부 tol 0.01 안에서 일치 · 면제 근거(provenance) 검사 RED=0(13건 전부 등재 전
  `present_markers` 기계검증 통과).
- `pytest tests/ -q --ignore=...pl_breakdown... --ignore=...ifrs17_bs...` → **282 passed, 1 skipped.**
- **골든 `--update` 안 했다** — 룰 엔진 무변경이라 필요 없었다.
- 데이터·xlsx·허용오차·기존 레지스트리 3종 전부 무변경(`kics_disclosure.json` mtime 08-22 그대로).
- `validate_data_contract.py --selftest` 는 50/51 인데 실패하는 N6 은 **내 변경 전에도 동일하게
  실패**한다(3파일 stash 후 재확인). 합성 원장 헬퍼 `_ledger()` 가 `status=VERIFIED` + `verify=None`
  을 만드는 selftest 자체의 결손 — 별건.
- 커밋·push 안 했다.
- **부수 관찰(내 변경과 무관, 기록만).** `validate_data_contract.py` 는 실행할 때마다
  `dividend.json` · `data/_derived/qoq_warn.json` · `data/dart/viz/{bs_snapshot,csm_amort_schedule,
  csm_waterfall,insurance_pl_breakdown,sensitivity_heatmap}.json` **7개를 다시 쓴다.** 두 번 돌려
  md5 를 대조하니 **내용은 바이트 동일**이고 mtime 만 갱신된다(커밋 `adbf08c` 의 "산출물은
  되돌린다" 가 내용은 되돌리지만 mtime 은 못 되돌린다는 뜻). 지금은 무해하지만 **mtime 을
  신선도 근거로 쓰는 검사가 생기면 그 순간 거짓 신호가 된다** — 그때 고칠 것. `kics_disclosure.json`
  md5 는 이 세션 내내 불변(`20b43e45…`)임을 확인했다.

---

## 2026-08-22 (a) — tier2 갈래 전수 분류 + 다리 구조적 상한: blocking RED 43 → 34, 면제 신설 0

`inbox/parser/20260821T1425Z` iter-3 회신("43건 전부 원문과 일치 = 룰 문제")에 대한 sender 재확인.
절반은 맞았다 — 9건은 공식이 덜 모델링해서 뜬 RED였고, 나머지 34건은 데이터 쪽이라 예측값을
붙여 되돌려 보냈다.

### 채택하지 않은 안 — `item3 == item13` 을 세 번째 갈래로

parser 는 이 패턴을 7건, orchestrator 는 160건이라 봤다. 실측은 **147건**(47/48/49 완비 기준)이고
**그중 125건이 이미 `CAPPED`/`UNCAPPED` 로 통과**한다. 갈래로 승격하면 그 125칸의 item47·item49 가
통째로 무검사가 된다 — 전날 `48_tier2_limit` 이 로더 강제라 증거력을 잃은 것과 같은 형태다.
`item3 == item13` 은 갈래가 아니라 **채무성 tier2 가 없을 때 자연히 따라오는 결과**다.

### 신설 갈래 `TFI_NA` — 판정 근거가 산술적 모순이라 레지스트리가 필요 없다

`item48`(보완자본 한도)은 `SCR × 50%` 공식값이므로 SCR 이 양수인 한 0 일 수 없다. `item48 == 0
∧ item14 > 0` 이면 그 0 은 금액이 아니라 "해당사항 없음" 표시다(parser 원문 확인: 메트라이프
2023.1Q p11 `보완자본 한도 0 0` + `(기발행 신종자본증권) 0` + `(기발행 후순위채무) 0`).
그 상태에서 한도 항등식은 적용 대상이 아니므로 **대체 항등식 `item3 == item13`** 으로 검산한다.
해당 조건 24칸 전부 성립하고, 실제 갈래 진입은 12칸(메트라이프 10 · 카카오페이 2).

적용전 488 버킷 전수: `CAPPED` 324 · `UNCAPPED` 51 · `BOTH` 34 · `TFI_NA_OK` 12 ·
`INPUT_MISSING` 52 · `NEITHER` 15(RED).

### 다리 — `한도초과 ≤ item12` 구조적 상한

발행사 각주(미래에셋생명 2023.2Q p11 주2)가 기본자본을 *"순자산에서 지급여력금액 불인정 항목
(단, 보완자본 한도를 초과한 금액을 제외)"* 을 차감한 금액으로 정의한다 → 한도초과액은
불인정항목 Ⅱ **안의 구성요소**라 그보다 클 수 없다. 근사치 `max(0, item47 − item48)` 이 상한을
넘으면 넘은 만큼은 다른 데서 온 값이다.

| 후보식 | 통과 | 실패 |
|---|---:|---:|
| 초과항 없음 `i4−i12−i13` | 425 | 52 |
| 무조건 더함 | 440 | 37 |
| CAPPED 조건부 (직전) | 461 | 16 |
| **CAPPED 조건부 + `min(exc, i12)` (채택)** | **467** | **10** |
| `exc = max(0, i47 − i3)` 계열 | 435~440 | 37~42 |

클램프 발동 10칸 중 **9칸에서 다리가 정확히 닫힌다.** 셋은 근사치가 item12 와 반올림 차이
(케이디비 2025.3Q 203.10/203 · 아이엠라이프 2025.2Q 2,015.35/2,015 · IBK연금 2025.3Q 513.09/513)
라 "불인정항목 전액이 한도초과" 임을 직접 보여준다. 남은 1칸(한화생명 2025.2Q)은 그대로 RED —
**클램프는 실패를 지우지 않는다.** 대가는 그 10칸에서 item12 가 상쇄돼 item12 오류를 못 보는 것.
게이트가 발동 칸수를 매번 인쇄한다(`※ 한도초과 클램프 발동 10칸`).

### census 신설 2종 — 하나는 진짜 false-green 을 잡았다

- `TIER2_DUPLICATE_ROW`: `item47 == item48` 소수점까지 정확 일치(4칸 — BNP카디프 3분기 ·
  동양생명 2025.2Q). item48 은 공식값, item47 은 독립 합계라 우연일 수 없다 = 같은 셀 두 번 읽기.
  4칸 전부 이미 다른 축에서 깨져 있었으므로 오탐 0, 진단 정확도만 오른다.
- `TIER2_LIMIT_STALE`: item48 이 당분기 `item14×50%` 와 어긋나는데 **직전분기** 것과는 맞는다.
  롯데손해 2026.1Q 1칸 — 47/48/49 적용전 3칸이 2025.4Q 와 바이트까지 동일하고 item48(10,335.34)이
  2025.4Q SCR×50%(10,335.50)와 일치, 당분기(10,216)와는 119.34 어긋난다. **적용전 컬럼만** 전기
  것이다(적용후는 5,775.82 vs 5,801.18 로 다르다). 산수는 맞는데 소스가 직전분기인 false-green.

### `TIER2_TABLE_ABSENT` 52칸 사유 2분할

`..._INTERMITTENT` **39**(같은 회사가 다른 분기엔 공시 → 추출갭) · `..._COMPANYWIDE` 13
(미래에셋생명 전 분기 부재). **RED 승격은 하지 않았다** — blocking 이 39 늘어나는 정책 결정이라
orchestrator/owner 판단으로 올린다. 사유가 갈렸으니 더는 "SKIP 52" 가 통과처럼 읽히지 않는다.

### 변이시험 — 갈래가 면제로 변질되는 것을 기계로 막는다

- `tests/test_tier2_limit_rules.py` 37 → **53**. `TFI_NA` 갈래 안에서 item3·item13 을 흔들면
  RED 가 나는지, 세 행 중 하나라도 0 이 아니면 갈래에서 빠지는지, SCR=0 이면 갈래가 사라지는지,
  클램프가 실패를 지우지 않는지, 중복행/전기잔존이 적용전·적용후 둘 다에서 잡히는지.
- `tests/test_rule_coverage_manifest.py` 4 → **6**. `COMPOSITION_BRANCHES` 선언 +
  `test_composition_branch_set_matches_manifest`(통과 사유에 갈래 이름이 반드시 박힌다) +
  `test_every_composition_branch_is_falsifiable`(실데이터에서 네 갈래 대표를 뽑아 item3 을
  9,999 흔들면 전부 통과가 깨진다). **갈래를 늘리고 falsifiability 를 증명 안 하면 테스트가 막는다.**
- 순회 범위 실측: 8축 전부 **488/488 버킷 · 39/39 회사**, 중복 발행 0.

### 잔여 34건 — 전부 parser 발주 (면제 신설 0, 허용오차 미변경)

`inbox/parser/20260821T1425Z...md` `## sender 재확인 (validation, iter-2)`, status open · iter 3.
전기 잔존 1 · 중복행 4 · 계열 이탈 2(NH농협손해 2025.4Q 예측 7,928.46 · 한화생명 2025.2Q 예측
≈139,303) · 코리안리 스코프 6(잔차가 `item14 × 5.00%` 와 최대 편차 0.38억으로 일치) ·
순수 코어잔차 6 · 추출불가 1(동양생명 2026.1Q 완전 스캔본).

**owner 승인 필요 3건**: ① 코리안리 — TFI 표 자신의 보완자본/기본자본 행 신규 적재(마스터로는
절대 못 닫는다, 면제보다 이쪽이 맞다) ② `..._INTERMITTENT` 39칸 RED 승격 여부 ③ 동양생명
2026.1Q vision 판독 시도 여부.

### 재현

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_disclosure.py
  -> exit 2, blocking RED=34 (= 35 − 8_life documented exception 1)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
  -> SUMMARY RED=20 (종전 24)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/ -q \
  --ignore=tests/test_pl_breakdown_golden.py --ignore=tests/test_ifrs17_bs_golden.py
  -> 221 passed, 1 skipped
```

골든 `tests/fixtures/kics_rules_golden.json` 은 룰이 **의도적으로** 바뀌었으므로
`python tests/test_kics_rules_golden.py --update` 로 재생성(RED 44 → 35). 해시를 손으로 고치지
않았다. `kics_disclosure.json` · `insurequant_master_tables.xlsx` 미변경, 커밋·push 없음.

---

## 2026-08-21 (i) — `36_irr` 재현불가 5건 잔차 박제 면제 (owner 승인) · push 게이트 RED 8 → 0

`inbox/validation/20260821T1810Z`. 직전 (h) 에서 면제 반증으로 드러난 마지막 RED 8건
(`KICS_36_irr` 4 + `TRANSITION_AFTER_IRR_MISMATCH` 4; 전사로는 적용전 5 + 적용후 5).
대상: KR0073 2025.2Q · KR0094 2024.2Q·2024.4Q·2025.2Q·2025.4Q.

### 판단 — 데이터가 아니라 재현식이 이 회사들에 안 맞는다

- item36 은 **다른 축에서 검산된다**: `item19 = sqrt(item36~40·MARKET_M)` 상대잔차 최대 0.0022%.
- 41-46 은 원문 그대로(raw fitz 로 5건 전건 재확인, 백만원↔억원 환산까지 정확 일치).
- **교보 2025.2Q 는 하한 자체를 못 지킨다**: 금리상승 단일 충격량 684,627 백만원 > 공시 459,988.
  어떤 합성식으로도 최악 단일 시나리오보다 작아질 수 없다 → 같은 기준의 표가 아니다.
- 식 변경 기각: 226버킷 전수에서 현행 signed 식 221/226(97.8%) vs 평균회귀 0절단 123/226(54.4%).
  **티켓의 "갈리는 102건이 전부 현행만 통과" 는 정정** — 실측 A-only 100 · B-only 2.
- 원인은 **`UNEXPLAINED`**. 신한 주2(작성기준 변경)는 열 간 차이에서 상쇄되므로 잔차를 설명하지
  못하고, 그 주2 가 없는 2025 두 분기에도 잔차가 남는다.

### 배선 — 통째 skip 금지, 적용전·적용후 각각

`src/solvency/validation/kics_json_rules.py` 에 `IRR_DERIVE_ISSUER_INCONSISTENT`(5×2 잔차,
tol 0.01) · `irr_derive_expected()` · `irr_pin_verdict()` 신설. 두 축이 **같은 함수를 import**
한다(재타이핑 금지): 룰엔진 `36_irr`(적용전) · `validate_kics_disclosure._transition_irr_after`
(적용후). MATCH → SKIP · DRIFT → RED · **결측 → RED**. `_irr_pin_recheck()` 가 매 실행 두 컬럼
잔차를 인쇄하고, 잔차가 룰 tol 안으로 들어오면 `IRR_EXEMPTION_INERT` review 를 낸다.
`_exemption_registries()` 등록 — 등록 전 실행에서 게이트가 `EXEMPTION_PROVENANCE_MISSING`
RED 5건을 즉시 띄웠다(등재 경로가 실제로 막혀 있다는 증거).

### provenance — `VERIFIED`(기계검증), `VERIFIED_BY_IMAGE` 아님

인용 페이지 텍스트밀도 1,829~3,093자/p 로 image-only 반증 임계(800자/p)를 크게 넘는다.
`present_markers` 에 **원문 수치 자체**(순자산가치 6열 + Ⅳ.금리위험액)를 넣어 게이트가 매 실행
재대조한다. `data/_gold/kics_exemption_provenance.json` 15 → 20건.

### 변이시험 (마스터 무수정, records 주입)

| 실험 | 결과 |
|---|---|
| 면제 ON | `validate_data_contract` RED **0** |
| 면제 OFF | RED **8** (원래와 동일 셀) |
| ON + item36 ×1.02 | IRR 축 RED **10** |
| ON + item44 삭제 | IRR 축 RED **10** |
| ON + item43 ×1.02 | IRR 축 RED **6** — `max(R,0)` 절단 입력이라 **면제 탓 아님**(면제 OFF 에서도 룰이 못 본다) |

(회사,분기)×항목 전수 스윕: 도출값이 실제로 움직이는 입력은 전부 DRIFT=RED, 절단 입력은 결측
경로가 덮는다. 상주화 `tests/unit/test_irr_pin_exemption.py` 9건(pre-push 훅 포함).

### 게이트

`validate_data_contract` RED 8→0 · `validate_kics_disclosure` RED 6→1(= KR0079 8_life 기존 면제분,
blocking 0) · 적용후 36_irr 불일치 5→0 · provenance RED 0.
`tests/fixtures/kics_rules_golden.json` `--update`(36_irr RED 5 → SKIP 5, YELLOW/GREEN 불변).
`test_rule_coverage_manifest.py` `FULL_COVERAGE_SWEEP=1` 3 passed — 매니페스트 수정 불필요.
`sh .githooks/pre-push < /dev/null` **exit 0**.

### inbox

sender 스레드 3건 종결(`20260821T1625Z` · `20260821T1620Z` · `20260821T1420Z`).
**자기 오판 기록**: `20260821T1625Z` 의 KR0071 흥국생명 "raw 가 오문서" 판정은 틀렸다 —
`fitz` 키워드 0회를 내용 부재로 읽었고 실제로는 p1~p112 가 스캔 이미지였다. 바로 위 KR0005
항목에서 같은 함정을 240dpi 렌더링으로 이미 풀어 놓고 KR0071 에 적용하지 않았다.
`20260820T2340Z` 는 레지스트리 등재 잔여로 `answered` 유지.

---

## 2026-08-21 (g) — 미참조 항목 다리 2건 판정 · 발행사 자기모순 면제(잔차박제) · 방치 스레드 2건 종결

### 1. `item23 = item24 + item25 + item26` — 배선 검증(선행 세션 배선분)

세션 크래시로 배선만 남고 기록이 없던 룰을 **중복 작성하지 않고 변이시험으로 검증**했다.
실측 적용전 403검사/403통과 · 적용후 205/205. 발주 시점(01:27)의 유일한 불일치 **흥국생명 KR0071
2023.3Q item24 = 8,313(날조)** 은 그 사이 파서가 `0` 으로 정정했다.

| 변이 | 결과 |
|---|---|
| 룰 함수 스텁 교체(끄기) | FAILS 0 |
| KR0071 2023.3Q item24 = 8313 **재주입** | FAILS 1 (원래 결함 재검출) |
| 통과 회사 **값_적용후** +999 주입(KR0001 2023.1Q item26) | FAILS 1, column=적용후 |

세 번째가 핵심이다 — 적용후 불일치가 라이브 0 이라 "돌긴 도는가" 를 실행결과로는 구분할 수 없었다.
부수 관측: `적용후:자식전부결측·부모>0(추출갭 후보)` **24건** = 미공시가 아니라 추출갭 후보.

### 2. `item2 = item4 − item12 − item13` — **룰이 아니다.** 원문 각주가 정의를 써 놨다

잔차 53건(푸본현대 13/13 · IBK연금 13/13 · 아이엠라이프 7 · 농협생명 4 · 에이비엘 3 · 동양생명 3 ·
롯데손보 2 · BNP카디프 2 · 그 외 6사)을 raw 로 규명했다.

**푸본현대·IBK연금 13분기 전부**를 fitz 로 다시 뽑아 대조 → `기본자본/Ⅰ/Ⅱ/Ⅲ` 이 마스터와 일치하고
**raw 표 자체가 안 닫힌다**(IBK 13분기 잔차 −1,193 ~ −807). 마스터 결함이 아니다.

미래에셋생명 2023.2Q p11 `기본자본주2)` 각주(스캔본 200dpi 렌더링 판독):

> 주2) 기본자본은 건전성감독기준 재무상태표 상의 순자산에서 지급여력금액 불인정 항목
> **(단, 보완자본 한도를 초과한 금액을 제외)** 및 보완자본으로 재분류하는 항목을 차감한 금액

`보완자본 한도 초과액 = 보완자본 한도 적용 전 − 보완자본 한도`. 세 회사 백만원 단위 일치:

| 회사·분기 | 한도적용전 | 한도 | 초과(백만원) | =억원 | 마스터 잔차 |
|---|---|---|---|---|---|
| 푸본현대 2026.1Q p19 | 1,040,999 | 696,260 | 344,739 | 3,447.4 | −3,447 |
| IBK연금 2026.1Q p17 | 440,535 | 359,792 | 80,743 | 807.4 | −808 |
| 농협생명 2025.1Q p18 | 1,565,022 | 1,374,563 | 190,459 | 1,904.6 | −1,905 |

완전검산(푸본 26.1Q): `7,254 − (7,460 − 3,447) − 3,132 = 109` = 공시 기본자본.
"잔차 ≈ −item12" 로 보이던 24건도 같은 현상(초과액이 Ⅱ 를 덮을 만큼 큼).
`보완자본 = min(한도적용전, 한도) + 해약환급금 초과분` 도 확인(IBK `359,792+340,742=700,534`).

**판정 근거의 형태가 ①과 다르다.** ①은 표 안에 합계 캡션 `Ⅲ. 기타 요구자본 (1+2+3)` 이 **인쇄돼**
있어 발행사가 선언한 식이고, 자본 블록 Ⅰ/Ⅱ/Ⅲ 에는 그런 캡션이 **없다**(같은 표의
`나. 지급여력기준금액 (Ⅰ-Ⅱ+Ⅲ)` 는 요구자본 블록 캡션이다). 배선하면 원문을 정확히 옮긴 53셀을
RED 로 잡는다. **면제 레지스트리도 만들지 않았다** — 면제할 결함이 아니다.
→ 파서 발주 `20260821T1425Z`(한도 3줄 적재). 적재 후 배선하면 전건 닫히는 진짜 룰이 된다.

### 3. KR0079 2023.2Q `8_life` documented exception — **잔차 박제형** (owner 승인)

발행사가 자기 총괄표(item17=17,495)와 자기 세부표(R7 집계 16,127.5950)를 안 맞게 공시했다.
독립 재검산으로 잔차 **+1,367.4050** 확인(룰엔진 `R7`·`_diversified_sqrt` **import**), 대조군
2023.4Q 는 **−0.0047** 로 닫힌다(추출 방식 정상). p11 렌더링 판독으로 17,495·209.7 확인.

- `_LIFE8_ISSUER_INCONSISTENT` = {(KR0079, 2023.2Q): {적용전: 1367.4049866571877, 적용후: 동일}},
  `_LIFE8_PIN_TOL = 0.01`. 매 실행 마스터에서 재계산 → 이탈 `LIFE8_EXEMPTION_RESIDUAL_DRIFT` RED /
  결측 `LIFE8_EXEMPTION_INPUT_MISSING` RED / 무용 `LIFE8_EXEMPTION_INERT` review.
  finding 자체는 안 지우고 `report[...]["exempted_findings"]` 에 남긴다. 차단집계에서만 뺀다.
- **적용전·적용후 둘 다 박제** — 발주서가 놓친 두 번째 RED 가 있었다(게이트 `_transition_mmult_after`
  축 17 적용후, item29~35 적용후가 완전미러라 잔차 동일). 적용전만 면제했으면 적용후가 그대로 막았다.
- 변이 4종 전부 통과: 레지스트리 비움 / item17 적용전 +5 / **item33 적용후 −3** / item35 삭제.
- 원장 스키마 신설 **`VERIFIED_BY_IMAGE`** + `_residual_pin_contract`. 이 PDF 는 텍스트레이어가
  **행 단위로 잘려** 있다(58p 4,773자 ≈82자/p, `'3. 시장위험액9,53'` 처럼 값 중간 절단) —
  `absent_markers` 를 걸면 마커를 절대 못 찾아 **항상 '주장 확인'으로 끝나는 무검사**가 된다.
  그래서 마커를 쓰지 않고 `_cited_page_text_density()` 로 **인용 페이지 텍스트밀도를 매 실행 재측정**해
  "기계검증 불가" 주장 자체를 검증한다(>800자/p → `EXEMPTION_IMAGE_CLAIM_REFUTED` RED).
  필수 필드 누락은 `EXEMPTION_IMAGE_RECORD_INCOMPLETE` RED. 침묵하지 않고 매 실행 review 인쇄.
- root `TODO.md` 에 (회사·분기·룰 id·사유·박제잔차·해제조건) 등재.

### 4. 발견한 false-green 1건 — `item4` 가 공시값이 아니다 (파서 라우팅)

`item4 vs Σ(item5..11)`: **적용전 392/392 · 적용후 182/182 완전일치, 불일치 0.** 억원 반올림 표에서
574셀이 전부 오차 0 으로 닫히는 일은 없다. docling MD 전수 스윕 → 공시 Ⅰ ≠ 마스터 item4 **124셀**,
그중 **122셀이 정확히 `마스터 item4 == Σ자식`**(|Δ| 1~4억). 범인:
`fill_period_to_disclosure.py::_reconcile_item4_from_components`(Δ≤10 덮어씀) +
`recalc_kics_derived.py`(Δ>2 **및** 상대 5% 초과 덮어씀 — **큰 오차 경로도 세탁**).
→ rule 2(순자산합)는 파이프라인이 먼저 써 넣은 등식을 검사하므로 영원히 GREEN.
발주 `inbox/parser/20260821T1420Z`.

### 5. 방치 스레드 2건 종결 (원 sender = validation)

`scripts/check_inbox_hygiene.py` 위반 **2 → 0**.

- **`20260803T0520Z` (18일)** — `validate_data_contract.py` CHECK 2 **2a(iv)** 배선
  (`Env.rate_sensitivity_rows` 신설). 사이드카 실사 87셀(디스크 부재 0 · 마스터 조인 87/87 · 양방향
  차집합 0). 파서가 물은 "더 잘게 조인" 은 불요(522행 = 87 × 2 × 3 이고 여섯 변형이 같은 원천표).
  **`target_q=None` 이 의도적**: 이력형 마스터라 `latest_q` 를 걸면 과거분기 86/87 이 STALE_AS_OF 로
  터진다. 변이 4종(사이드카 제거/셀 삭제/as_of stale/source_file 부재) 전부 정확히 1건씩 발화.
  selftest **P1·P2** 신설 + `base_sidecars()`/`base_inject()` 보강 → **51/51**. 게이트 `RED=0 exit=0`.
  **미배선 명시**: 마스터 전체 신선도(최신 2025.4Q vs 2026.1Q) — 공시주기 미확정이라 근거 없이 안 걸었다.
- **`20260706T0502Z` (46일)** — 옛 숫자로 닫지 않고 현재 마스터로 재측정(하나생명 2024.2Q 제외).
  케이디비 **78/78** · 하나생명 **78/78**(둘 다 "완전 미착수"였던 회사) · `_TRANS_EFFECT_MARGIN` 축
  **0건** · 적용사 item1/2/3/14/27/28 적용후 결측 **0** · 선택경과조치 유실/부정합 **0** ·
  적용후 부모 continuity break **0**.
  **`_TRANS_EFFECT_MARGIN` 는 완화하지 않았다** — 0건인 축의 임계를 근거 없이 느슨하게 하면 다음
  분기에 진짜 복사버그를 놓친다(7월 오탐의 실제 원인은 분자 음수 방향체크였고 이미 고쳐져 있다).
  파서 지목 룰 사각 **배선**: `_after_parent_missing_child_present`(부모후 결측 + 세부후 present =
  mmult 미가동, review). 현재 1건 — `KR0071 2024.4Q item15후 결측·세부후 4/4 present · R5 역산 ≈16,987`.

### 게이트 실측 (세션 중 파서가 마스터를 두 번 썼다 — 섞지 않고 기재)

| 시각 | 게이트 | Status counts | 비고 |
|---|---|---|---|
| 01:29 | HEAD 판(item23 룰 없음) | RED=12 YELLOW=561 GREEN=4715 SKIP=1516 | rule별 RED 분해 동일 |
| 01:27 | 작업트리 판 | RED=12 YELLOW=561 GREEN=4715 SKIP=1516 | 기타요구자본 위반 1 |
| 02:00 | 작업트리 판 | RED=2 YELLOW=563 GREEN=4729 SKIP=1510 | 파서 10:58 write |
| 02:16 | **최종** | **RED=1 YELLOW=563 GREEN=4730 SKIP=1510 → blocking RED=0** | 파서 11:03 write |

**기존 룰 findings 무변동 증명 = 01:29 ↔ 01:27** (네 값 + rule별 RED 분해 완전 동일).
이후 이동은 전부 파서의 데이터 정정이고, `test_kics_rules_golden` 은 파서가 11:05 `--update` 재생성.
최종 exit=2 사유는 내 축 밖 2건: coverage census 2셀(카카오페이 2024.2Q·3Q) +
**KR0087 동양생명 2023.2Q item19후 present·item36~39후 결측**(파서 write 로 새로 노출).

테스트: goldens **13 passed** · selftest **51/51**. 룰엔진 무수정, 골든 해시 수기수정 없음,
`kics_disclosure.json` 무수정(전 변이시험 in-memory).

---

## 2026-08-21 (f) — 자기정정: 미러 룰이 '정의'를 '결함'으로 뒤집어 읽었다

(e) 에서 배선한 자기미러 판정이 **틀렸다.** owner 지적: **경과조치 미적용사에게 후 = 전은 정의상
참**이다. 나는 "적용후 입력이 적용전과 전부 동일 = 정보량 0" 이라 보고 미러를 통째로 실질평가에서
뺐고, 그 결과 `36_irr 적용후`·`R2 적용후` 를 "전부 동어반복" 이라며 RED 로 올렸다. 그 칸들은
조작된 값이 아니라 **유일하게 가능한 값**이고, 검사한 것은 헛일이 아니라 맞는 값을 확인한 것이다.
검사의 정보량을 논하다가 데이터의 정당성을 부정해 버린 것 — 축을 잘못 잡은 전형이다.

### 미러를 셋으로 나눴다

| 분류 | 의미 | 처리 |
|---|---|---|
| `mirror_nonapplier` | 비적용사 — 후 = 전이 **정의상 참** | 평가로 인정, 발화 없음 |
| `mirror_applier_legit` | 적용사인데 그 축을 움직이는 종류 **미신청**(또는 조건부 미발동) | 평가로 인정, 발화 없음 |
| `mirror_applier_suspect` | 적용사 + 해당 종류 **신청**했는데 후 = 전 | **RED `AXIS_SELF_MIRRORED_APPLIER`** |

실측(2026-08-21, 486버킷 / 적용사 18사):

| 축 | 평가 | 비적용사 미러 | 적용사·미신청 미러 | **적용사·신청 미러** |
|---|---|---|---|---|
| `36_irr` 적용후 | 103 | 103 | 0 | **0** |
| `R2_순자산합` 적용후 | 182 | 182 | 0 | **0** |
| `R1_가용자본` 적용후 | 485 | 170 | **82** | **0** |

**오염은 한 건도 없다.** 그리고 R1 의 82건이 왜 두 번째 게이팅이 필요했는지 보여준다 — 전부
**'AC'(가용자본 시가평가 자본감소분) 미신청 적용사**다. 종류 게이팅 없이 "적용사 미러 = 오염" 으로
걸었으면 **82건 전건 오탐**, 즉 같은 실수를 규모만 줄여 반복하는 것이었다.

### `_AXIS_TRANSITION_KIND` — 축이 움직여야 하는 근거

`_TRANSITION_KIND`(FSS 2023-03-20 붙임-1 정본)와 짝지어 축→종류를 매핑한다:
`R1`·`R2` ← `AC` / `mmult17` ← `IR` / 나머지는 **`None` = 발화 금지**.
- `mmult19`·`36_irr` 는 `EQ`·`INT` 인데 **조건부 발동**(K-ICS리스크 60%>RBC 일 때만)이라 신청사여도
  후=전이 정당할 수 있다. owner 가 UH-5(2026-07-21)에서 **정확히 이 이유로** item19 COPY 룰
  신설을 기각했다(오탐 52건). 그 결정을 그대로 따른다.
- `mmult15`·`R5`·`R6`·`R7`·`R8` 은 하류 집계축이라 어느 종류든 흘러들어와 단일 매핑이 불가능하다.

### 정정된 평가율

미러를 평가로 인정하므로 실질평가 = 평가 − **오염의심**(0) 이다.

| 축 | 실질(grid) | 전버킷 | 독립(미러 제외, 보조지표) |
|---|---|---|---|
| `36_irr` 적용후 | **47.0%** | 21.2% | 0.0% |
| `R2_순자산합` 적용후 | **37.6%** | 37.4% | 0.0% |
| `R1_가용자본` 적용후 | 100.0% | 99.8% | 48.0% |
| mmult15 / 17 / 19 적용후 | 98.3 / 97.3 / 98.6% | | 64.3 / 60.9 / 56.7% |
| R5 / R6 / R7 / R8 적용후 | 94.2 / 99.0 / 100.0 / 100.0% | | 63.6 / 64.9 / 52.4 / 65.4% |

**독립 평가율**("후가 전과 달라질 수 있는 칸 중 판정한 비율")은 보고만 하고 **판정에는 쓰지 않는다** —
비적용사 미러는 결함이 아니기 때문이다. (e) 에서 보고한 21.2% / 37.4% 는 미러를 무가치로 본
계산이라 축의 실제 커버리지를 과소평가한 수치다.

### 회귀 그물 — '무엇을 잡으면 안 되는가'도 고정한다

- **N1 교체**: AC 신청사의 적용후 복사 → `AXIS_SELF_MIRRORED_APPLIER` RED.
- **N1b 신설**: **미적용사의 후 = 전 → finding 0.** 옛 로직(미러 전부 차감)으로 되돌리면 N1b 가
  즉시 `AXIS_NOT_EVALUATED` 로 터지는 것까지 실검사로 확인했다. 이 케이스만이 이번 오류의 재발을 막는다.
- selftest **45/45 → 46/46**. 골든 4종 13 passed(룰엔진 무변경이라 매트릭스 무이동 — `--update` 불필요).

### 게이트 (같은 데이터 A/B, master sha `2abd154b`)

| | RED | YELLOW |
|---|---|---|
| 신규 룰 비활성(=HEAD) | 0 | 275 |
| 신규 룰 활성 (정정 후) | **0** | **310** |

**메타룰은 이제 push 를 막지 않는다.** (e) 의 RED 4건 중 축 2건은 위 정정으로 철회됐고, 면제 2건은
파서가 `KR0003 2026.1Q`·`KR0073 2026.1Q` 를 레지스트리에서 해제하고 적용후 세부를 재추출해 소멸했다.
근거 원장의 두 기록은 **고아로 보존**한다 — 같은 (회사,분기)가 다시 면제로 등재되면
`status=CONTRADICTED` 가 즉시 RED 로 되살린다(반증된 근거의 조용한 부활 차단).

③(면제 근거 원장) ④(판독불가 셀 분리)는 owner 확인대로 그대로 유지했다.

---

## 2026-08-21 (e) — 메타룰 배선: "룰이 돌았다" ≠ "룰이 판정했다"

owner: *"뻔한 룰들이 배선조차 안 돼 있었으니 '게이트 초록'은 아무 뜻도 없었다."* (d) 의 적대적
재검증이 그걸 증명했다. 그 결과를 **산문이 아니라 강제 검사**로 굳혔다. 데이터는 안 건드렸다
(파서 kics 레인이 `kics_disclosure.json` 을 동시 수정 중 — 티켓으로만 조율).

### 왜 필요했나 — `FAIL: 0` 이 참이지만 무의미했던 자리

`36_irr 적용후` 는 그리드의 21%만 판정하면서 `FAIL 0` 을 인쇄했고, **그 21% 마저 값_적용후가
적용전과 전부 동일**했다. 원천 시나리오표의 컬럼은 `충격 전 | 충격 후(평균회귀·상승·하락·평탄·경사)`
이고 **경과조치 전/후 축이 아예 없다**(23/23사). 즉 그 검사는 자기 자신과 비교하는 동어반복이었다.
평가율을 방출하는 축이 하나도 없었기 때문에 이 상태가 통과처럼 읽혔다.

### 배선한 4가지

| # | 룰 | 판정식 | severity | 위치 |
|---|---|---|---|---|
| ① | `AXIS_NOT_EVALUATED` | 축×컬럼의 **실질 평가**(평가−자기미러) == 0 | **RED (push 차단)** | `_axis_eval_findings` → `validate_data_contract.check_census` 1b(v) |
| ① | `AXIS_EVAL_RATE_LOW` | 축그리드 또는 전버킷 기준 평가율 < 50% | YELLOW | 〃 |
| ② | (미러 판정) | 적용후 **대상·입력 전부**가 적용전과 수치 동일 → 정보량 0 | ①의 입력 | `_axis_evaluation_census` |
| ③ | `EXEMPTION_PROVENANCE_MISSING` / `_CITATION_UNRESOLVED` / `_CITATION_CONTRADICTED` / `_LEDGER_SCHEMA_INVALID` | 면제 레지스트리 6종 × 근거 원장 대조 + 인용 raw 재확인 | **RED** | `_exemption_provenance_findings` → 1b(vi) |
| ③ | `EXEMPTION_PROVENANCE_UNVERIFIED` | 기록은 있으나 기계검증 가능한 인용 미비 | YELLOW | 〃 |
| ④ | `SOURCE_UNREADABLE_NOT_VERIFIED` | `세부후결측(후=전)` 인데 raw 텍스트레이어 판독불가 | YELLOW | `_transition_mmult_after` → 1b(iv) |

**분모를 둘 다 잰다.** 축 그리드(적용전에 대상+입력 1개 이상 실재)만 보면 **추출갭으로 입력이
사라질 때 분모도 같이 줄어 평가율이 오히려 좋아지는** 함정이 있다 — census 룰이 "raw 를 정직하게
채울수록 RED 가 는다"로 앓았던 병의 거울상이다. 그래서 전 버킷 기준도 같이 재고 둘 중 하나라도
바닥을 뚫으면 review 로 올린다.

**임계값 근거.** `실질 0칸 = RED` 는 임계가 아니라 정의다 — 아무것도 확인 안 한 축의 "FAIL 0" 은
증거가 될 수 없고, 이 저장소는 이미 같은 부류(`CAPSEC_SOURCE_UNRESOLVED` ·
`DIV_CENSUS_SOURCE_MISSING` = "검사축 소실 = 통과 아님")를 RED 로 다룬다. `50%` 는 **데이터
임계가 아니라 의사소통 임계**다: 그리드 절반도 못 본 축의 요약문은 정보보다 오해를 준다.
YELLOW 308개 틈의 한 줄로 두지 않은 이유는, 그렇게 묻히는 것이 이 저장소가 두 달 데인 방식이라서다.

### 새로 드러난 것 — 100% 미러 축이 하나 더 있었다

| 축 | grid | 평가 | 미러 | 실질 |
|---|---|---|---|---|
| `36_irr` 적용후 | 219 | 103 | **103 (100%)** | **0** |
| **`R2_순자산합` 적용후** | 484 | 182 | **182 (100%)** | **0** |

`R2` 는 (d) 의 적대적 재검증도 못 본 신규 false-green 이다. 나머지 축의 적용후 미러 비중은
32~52% → **적용후 검사의 절반가량은 전=전 재확인**이고, 진짜 독립 검증분(실질 평가율)은
mmult15 63.8 · 17 60.3 · 19 56.1 · R1 48.0 · R5 63.6 · R6 64.9 · R7 52.4 · R8 65.4% 다.
이 표가 이제 매 실행 인쇄된다.

### 면제 근거 원장 — 억제기가 아니라 근거 기록

신설 `data/_gold/kics_exemption_provenance.json` (14 항목 = 레지스트리 6종 전수).

- **레지스트리에 있는데 원장에 기록조차 없으면 즉시 RED** → 조용히 새 면제를 추가하는 경로가 닫혔다.
- 원장에 억제성 키(`suppress`/`exempt`/`ignore`/`waive`/`skip`/`silence`)가 들어오면
  `EXEMPTION_LEDGER_SCHEMA_INVALID` RED — **원장이 면제기로 변질되는 것을 기계로 막는다.**
- `verify={file,pages,absent_markers}` 를 든 항목은 게이트가 매 실행 **그 raw 페이지를 직접 열어**
  '부재' 주장을 반증한다. 공백 제거 후 부분문자열 매칭(PDF 추출은 줄바꿈이 제멋대로).
- **라이브 2건 적발** — `KR0003 2026.1Q`(주장 "②③표 부재" → raw p24 에 ②표가 적용후 컬럼까지
  완비: 비율후 164.42 · 생명장기후 1,124,541 · 시장후 670,846) · `KR0073 2026.1Q`(주장 "섹션
  자체 없음" → raw p15 에 공통+② 전체, 적용후 비율 201.87. 주장된 헤드라인 214.23 은 그 페이지
  어디에도 없다). 둘 다 **이 세션에서 fitz 로 직접 재확인**했다(inbox 메시지를 근거로 쓰지 않았다).
  **면제 해제는 owner 소관이라 등재분을 지우지 않았다** — 근거가 거짓이라는 사실만 기록·RED.

### 판독불가 셀을 '정당' 에서 분리

`세부후결측(후=전)` 246칸을 한 덩어리로 세면서 사실상 "구조적으로 정당" 취급하고 있었다.
→ 판독가능 214 · **UNREADABLE 26 · BORDERLINE 6** 으로 갈랐다. 신호는 반드시 **raw PDF
텍스트레이어**에서 뽑는다 — docling MD 길이로 대신하면 이번에 적발된 면제 2건과 **똑같은 실패
모드**다(MD 유실을 '원천 부재'로 오독).

신설 `scripts/build_kics_source_textlayer.py` → `data/_derived/kics_source_textlayer.json`
(486셀 / 399초, READABLE 461 · BORDERLINE 7 · UNREADABLE 18). 게이트는 사이드카를 그대로 믿지
않고 **기록된 파일 크기를 디스크와 대조**해 어긋나면 `UNMEASURED` 로 강등한다(stale 사이드카가
조용히 '판독가능'을 주장하는 경로 차단). 하한 100자/페이지는 실측 분포의 **빈 구간**(73.4 ↔ 102.7)에
둔 값이고, 걸린 두 회사(KR0010·KR0079)가 룰엔진 `IMAGE_OCR_COMPANIES` 와 정확히 일치한다(독립 교차확인).

### 회귀 그물 — mutation test 가 실제로 무는지까지 확인

`_data_contract_selftest.py` **N1~N7** 신설(38/38 → **45/45**). 신설 7룰을 각각 결함 하나만 심은
합성 픽스처로 고정한다. 여기서 한 걸음 더 갔다: **각 케이스가 그 룰을 죽였을 때 실제로 FAIL
하는지 확인**(7/7 BITES). 우연히 통과하는 mutation test 는 없는 것만 못하다.
평가율 룰은 `_AXIS_MIN_GRID=20` 이상에서만 판정하므로 N1/N2 픽스처는 12사×3분기=36버킷으로 넓혔다
(기존 4사 픽스처로는 룰이 아예 깨어나지 않는다 — 그래서 기존 38케이스에 오탐이 0이다).

### 게이트 (같은 데이터 A/B)

세션 중 파서가 마스터를 또 덮어써서(`bc8e8cc0…` → `2abd154b…`) 단순 before/after 가 오염됐다.
**신규 룰만 끈 채 같은 데이터에 두 번 돌려** 분리했다 — 공유 트리에서 게이트를 고칠 땐 이 절차를 쓸 것.

| | RED | YELLOW |
|---|---|---|
| 신규 룰 비활성(=HEAD 동작) | 0 | 275 |
| 신규 룰 활성 | **4** | **308** |

델타는 **전부 신규 5룰뿐, 기존 룰 변동 0**. RED 4 = `AXIS_NOT_EVALUATED` 2 +
`EXEMPTION_CITATION_CONTRADICTED` 2. YELLOW +33 = 판독불가 20 + 면제 미검증 12 + 평가율 저하 1.
골든 4종(`test_kics_rules_golden`·`test_master_tables_golden`·`test_post_transition_golden`·
`test_deploy_assets`) 전부 통과 — **룰엔진 무변경이라 findings 매트릭스가 안 움직였다.**

> 🔴 **owner 판단 지점**: 배선 직전 push 게이트는 RED=0 이었다(ifrs17 레인이 그 사이 케이디비
> R_RSV_9 해소). **지금 push 를 막는 4건은 내가 고른 정책의 결과다.** 완화는
> `validate_data_contract.py` 의 `AXIS_NOT_EVALUATED` severity 한 줄. 축 면제 경로는
> `_AXIS_NOT_EVALUATED_EXEMPT`(현재 **비어 있음**)로 열어 뒀고, 등재하면 근거 원장 기록이
> 자동 강제된다(근거 없이 넣으면 `EXEMPTION_PROVENANCE_MISSING` RED).

### 요청받은 측정 — 5% 허용오차 밴드 (변경 안 함)

`scripts/_probes/tolerance_band_5pct_audit.py` 상주. `8_life`(item17·R7)·`19_market`(item19·MARKET_M)
가 `max(eff_tol, 5%·|expected|)` 덕에**만** 통과하는 셀 = **16칸**(= 8 (사,분기,축) × 전·후.
전·후가 미러라 두 번 세어진다) = 평가셀의 **1.1%**.

| 축/컬럼 | 회사 | 분기 | \|잔차\| | flat tol | 5% 밴드 |
|---|---|---|---|---|---|
| 19_market 전·후 | 삼성생명 | 2023.2Q | **899.2억** | 2.0 | 10,525억 |
| 8_life 전·후 | 현대해상 | 2024.2Q | **273.1억** | 2.0 | 3,553.6억 |
| 8_life 전·후 | KB손해 | 2023.2Q | 161.1억 | 10.0 | 2,789.3억 |
| 19_market 전·후 | KB손해 | 2024.2Q | 46.4억 | 10.0 | 1,375.0억 |
| 19_market 전·후 | 코리안리 | 2023.4Q | 45.5억 | 2.0 | 367.2억 |
| 8_life 후 / 전 | 아이엠라이프 | 2023.1Q | 9.9 / 4.9억 | 2.0 | 72.5 / 194.4억 |
| 8_life 전·후 | 동양생명 | 2024.2Q | 5.3억 | 2.0 | 904.2억 |
| 19_market 전·후 | AIA | 2025.2Q | 3.5억 | 2.0 | 358.5억 |

flat 로 조이면 **display 분기 신규 RED 는 4칸뿐**(코리안리 2023.4Q · AIA 2025.2Q 각 전·후),
나머지 12칸은 display scope 밖이라 push 를 안 막는다. "한꺼번에 수십 건이 켜진다"는 우려보다 훨씬 작다.
**단 이건 적용전/적용후 공통 룰엔진 허용오차라(적용후만의 회귀가 아니다) 조이면 골든 매트릭스가
움직인다 → owner 승인 없이는 안 건드린다.**

### 파서 발주

`inbox/parser/20260821T0620Z__validation__MULTI__meta_rules_wired_axis_and_provenance.md` (lane: kics)
— ① 면제 2건의 적용후 세부 재추출(값 전부 티켓에 옮겨 적었다) ② **`R2_순자산합` 적용후 컬럼이
원천에 실재하는지 판정**(개념 부재면 축 면제 후보, 있으면 182셀 미러가 오염) ③ 스캔본 16(사,분기)
OCR 우선순위(밀도표 그대로 사용 가능).

---

## 2026-08-21 (c) — 적용후 배선 확대 실행: 18사→39사 · 축15/36_irr 신설 · 허용오차 적용전과 동일

(b) 에서 열거한 구멍을 실제로 막았다. 데이터는 파서가 닫았고(축 A/B/C 전후 FAIL 0, 독립 재확인),
**게이트는 안 닫혀 있었다.** 파서가 "데이터가 깨끗하니 넓혀도 신규 RED 없다"고 했는데, 넓혀보니
**4건이 나왔다** — 그 주장을 그대로 믿었으면 그대로 묻혔다.

**바꾼 것 4가지** (`scripts/validate_kics_disclosure.py`):

| # | 변경 | 왜 |
|---|---|---|
| 1 | `_transition_identities_after` · `_transition_mmult_after` · `_parent_present_child_incomplete_after` **적용사 18사 → 전사 39사** | 비-applier 21사의 적용후 셀이 **8,914개**로 적용사 6,089개보다 **많은데** 통째로 미순회. 공통(TFI)사는 후=전이라 '방향성'은 못 걸지만 **항등식은 후에도 성립해야** 한다 |
| 2 | `_TRANS_PARENT_SUBS` 에 **축 15**(`sqrt([17-20]·R4) + item21`) 추가 | 종전 `{17,19}` 뿐 → 기본요구자본 적용후가 통째로 미검사 |
| 3 | **`_transition_irr_after` 신설** (36_irr 적용후, 전사) | 적용후 배선 전무 |
| 4 | 적용후 허용오차를 **룰엔진(적용전)과 동일**하게 (합=flat `eff_tol`, 비율=sub-scale 동적) | 같은 룰이 컬럼에 따라 다른 잣대를 쓰고 있었다 |

**4번이 제일 컸다.** 합-항등식 적용후가 `max(2.0, 0.5%)` 라 53,537억 기준 **267억까지 통과**시켰고
(적용전은 flat 2.0), 그 틈으로 **한화손해 2024.2Q `item1후`=적용전 복사(4.03억)** 가 새고 있었다.
반대로 비율은 적용후만 flat 2.0 이라 **카카오페이 micro 반올림 3건이 적용전 GREEN·적용후 RED** 로
비대칭이었다(엔진의 sub-scale 동적식을 쓰니 사라짐 = 진짜 결함이 아니었다).

**확대가 잡은 것 (동결 스냅샷 A/B, HEAD 게이트 0건 → 확대 게이트 4건, 기존 검출 소실 0건):**

1. **한화손해 KR0002 2024.2Q `item1후`** — raw `KR0002_한화손해보험.md` L363 `지급여력금액 5,354,135 |
   5,353,772`. 마스터 적용후는 53541(=적용전) 인데 정답은 53,537.72. raw 는 적용후에서도
   `2,637,797+2,715,975=5,353,772` 로 정확히 닫힌다. **파서 발주.**
2. **코리안리 KR1000 2023.3Q** — item29~35후·36~39후 **12칸 결측**(앞뒤 분기는 present, SANDWICHED).
   같은 필링에서 `지급여력기준금액 적용전=적용후=1,978,169` 라 채울 값이 확정적. **파서 발주.**
3. **미래에셋 KR0079 2023.2Q `item17후` mmult 1,367.4** — 값_적용후가 적용전과 **바이트 동일**이라
   documented 된 적용전 `8_life` RED 의 **거울**. 새 결함 아님. **owner 승인 후보**(면제는 내가 등재 안 함).

**결측을 숨기지도, 결함으로 세지도 않는다.** 세 검사 전부 `not_evaluated` 명시 집계를 리포트·표준출력에
낸다. 36_irr 적용후는 계산가능 103셀 FAIL 0 인데 그 103셀은 **41~46 후가 적용전과 100% 동일**이고,
반대로 `짝수Q·적용전완비·적용후결측` 이 **114셀**이다 → "원천에 시나리오표의 전/후 구분이 있는가"를
파서에 질의(`POST_SCENARIO_ABSENT` 로 세어서 보고, RED 로는 안 건다).

**명시적 scope 제한 1건(정당)**: `_transition_ratio_after_capture`(후>전 방향성)는 선택경과조치
적용사에서만 성립하는 **도메인 불변식**이라 18사 유지. 대신 나머지 21사의 적용후 비율은 항등식
(R7/R8후)과 결측(census item27/28)으로 전사 검사된다 — 근거를 docstring 에 박았다.

**회귀 그물**: `_data_contract_selftest.py` 에 **F6~F9** 신설(비-applier mmult / 축15 / 36_irr후 /
허용오차 parity). 되돌리면 즉시 FAIL 한다. **selftest 31/34 → 38/38.**

> 🔴 **덤으로 잡은 게이트 자기검사 사각**: selftest `I1/I2/I3`(17BS 항등식·코어 census·미배포 YELLOW)이
> `validate_statutory_reserves.py:371 r["생손보여부"]` **KeyError 로 ERROR** 상태였다 — 합성행엔 그 키가
> 없다. 즉 **그 세 룰이 사실상 무검증**이었는데 아무도 몰랐다. 메타 3종을 `.get` 으로 바꿔 복구
> (실마스터 행엔 항상 있으므로 라이브 판정 무변화 — RED=1 BASELINE=15 그대로 확인).

**게이트 수치** — `validate_kics_disclosure.py` exit 2: RED=12(전건 documented) + census 2(카카오
이미지PDF, documented) + **신규 적용후 4셀**. `validate_data_contract.py` **RED=1 YELLOW=275 exit 2
(확대 전후 동일)** — 신규 4건은 전부 `_DISPLAY_QUARTERS` 밖 분기(2023.2Q·2023.3Q·2024.2Q)라
push 차단 경로의 표시분기 스코프에서 걸러진다. **push 차단은 안 늘었다.** 유일한 차단 RED 은
ifrs17 레인의 케이디비생명 item5(`R_RSV_9`). 골든 `test_kics_rules_golden` 통과(룰엔진 무변경).
발주 `inbox/parser/20260821T0155Z`.

> **측정 함정 기록**: 세션 중 파서가 `kics_disclosure.json` 을 덮어써서(01:28 KST) 단순 before/after 가
> 오염됐다(YELLOW 560→561 이 내 변경 탓으로 보였다). **마스터를 스냅샷으로 얼리고 HEAD 게이트 vs
> 확대 게이트를 같은 데이터에 돌려** 분리했다. 공유 트리에서 게이트를 고칠 땐 이 절차를 쓸 것.

---

## 2026-08-21 (b) — "적용후에도 똑같이" 는 룰 10개 중 8개가 18/39사, 2개는 아예 미배선

owner 재질의로 룰별 적용후 배선을 코드에서 전수 확인했다. **owner 지시(2026-07-07)는 배선돼
있으나 절반만 덮는다.**

- 룰엔진(`kics_json_rules.py`)이 `post=True` 로 적용후를 읽는 곳은 **단 3곳** — rule 9·10·8_post.
- 게이트 스크립트가 별도 배터리로 보강한다: `_TRANS_AFTER_IDENT`(R1·R2·R5·R6·R7·R8) ·
  `_transition_mmult_after`(8_life·19_market). **둘 다 `if c not in _TRANSITION_APPLIERS: continue`
  로 18사 한정.**
- **R4(기본요구자본 mmult)와 36_irr 은 적용후 검사가 어디에도 없다.**

전 룰 × 전후 전수(전사, 입력완비 버킷만): 적용후에서만 새로 깨지는 것이 **16건** —
R1 1 · **R4 9(tol 2.0 이면 36)** · R6 1 · 8_life 4 · 19_market 1. R7/R8 은 전후 동수라
적용후 고유 결함이 아니다(카카오페이 micro-insurer, 기존 documented).

**측정을 두 번 틀렸고 그 과정을 남긴다** — 이 저장소에서 반복되는 함정이라서다:
1. `run_validation` 을 `source_has_breakdown` 없이 불러 **적용전** 19_market 이 RED 131 로
   부풀었다(게이트 실제값은 0). 보조입력을 안 주면 cadence-aware 로직이 무너진다.
2. 적용후 컬럼을 룰엔진에 그대로 먹였더니 **적용후가 원래 없는 항목**(item4~13·41~46 은 적용후
   커버리지 47~52%)이 전부 결함으로 잡혀 R2 256건·36_irr 114건이 됐다. 룰엔진은 입력 결측을
   RED 로 내는 관례(커버리지 census)라 그렇다.
→ **결측과 결함을 절대 섞지 말 것.** 입력완비 버킷만 판정하고 나머지는 `계산불가` 로 따로 센다.

**세 번째 축이 더 클 수 있다**: 적용후 `계산불가` 가 36_irr **383/486** · R2 **304** ·
19_market **190**. 적용후 세부항목 커버리지가 절반이라 "적용후도 똑같이 검사한다"가 지금
구조에선 물리적으로 절반만 가능하다. 원천부재/추출갭 판정을 파서에 요청했다.

감사 스크립트 2종을 상주시켰다(`scripts/_probes/after_column_rule_audit.py` ·
`mmult_after_audit.py`) — 일회성 조사로 끝내면 같은 질문이 또 온다.

**교훈**: 게이트가 0 을 찍으면 분모(검사 대상 수)와 **그 검사가 어느 컬럼을 읽는지**를 같이 읽어라.

---

## 2026-08-21 (a) — "적용후 mmult 0 불일치"는 범위 밖이었다. 축 C 는 검사 자체가 없었다

owner 가 "그게 그렇게 쉽게 닫힐 리 없다"며 생명장기 하위와 지급여력기준금액 하위까지 전후 전수
검증을 지시했다. **owner 가 옳았고 내 전날 보고가 틀렸다.**

**무엇을 잘못했나**: 게이트가 출력하는 `적용후 mmult 불일치: 0` 을 읽고 "적용후 mmult 가 다
닫힌다"고 보고했다. 그 줄은 `_transition_mmult_after()` 의 결과인데, 그 함수는
**① `_TRANSITION_APPLIERS`(선택 경과조치 18사)만** 돌고 **② `_TRANS_PARENT_SUBS = {17, 19}`**
만 본다. 즉 비-applier 회사와 **축 C(기본요구자본 item15)** 는 애초에 검사 대상이 아니다.
게이트는 자기 범위 안에서 정직했고, **범위를 확인하지 않고 전체로 읽은 것이 내 잘못**이다.

**전수 재계산**(행렬은 `kics_json_rules` 의 `R4/R7/MARKET_M` 을 import — 재타이핑 금지):

| 축 | 적용전 FAIL(tol2) | 적용후 FAIL(tol2) | 적용후 계산불가 |
|---|---|---|---|
| A 생명장기 `17=f(29-35)` | 5 / 350 | **10 / 345** | 141 |
| B 시장 `19=f(36-40)` | 3 / 340 | **4 / 296** | 190 |
| C 기본요구자본 `15=f(17-20)+21` | **0 / 484** | **36 / 480** | 6 |

**축 C 가 핵심이다.** 적용전은 484건 전부 tol 2.0 으로 닫히는데 적용후는 36건이 깨진다.
처음엔 "적용후엔 이 항등식이 원래 성립 안 하는 것 아닌가"를 의심했으나 **적용후도 444/480 이
닫히므로 항등식은 성립한다** → 36건은 의미론 불일치가 아니라 셀 결함이다. 잔차 부호가 ± 로
섞이고 회사별 연속분기(흥국생명·에이비엘·농협생명·흥국화재)로 묶인다.

**산술적으로 불가능한 셀 2건** — 이게 가장 확실한 결함이다:
- 신한이지 2025.1Q: `item35(대재해)후 = 43` 인데 부모 `item17후 = 10`.
  **분산 후 부모가 개별 하위위험보다 작을 수 없다.** 적용전은 10 vs 계산 9.90 으로 깨끗하다.
- 하나손해 2025.2Q: `item34(사업비)후 = 44.43` 인데 이건 `item35(대재해)` 의 값이다(한 칸 밀림).
  부모후는 적용전 복사본이라 안 움직여서 산술로만 드러난다.

**세 번째 사각**: `계산불가`(하위 결측으로 mmult 시도조차 못 함)가 A 136~141 · B 146~190 —
486 버킷의 **28~39%** 다. FAIL 로도 안 잡히고 조용히 넘어간다. 커버리지 census 를 1급으로
두라는 기존 교훈(`feedback-coverage-census-mandatory`)이 이 축에도 그대로 적용된다.

**조치**: 발주 `inbox/parser/20260821T0010Z`(lane: kics). 감사 스크립트를 상주시켰다
(`scripts/_probes/mmult_after_audit.py`) — 일회성 조사로 끝내면 같은 질문이 또 온다.
**게이트 배선은 하지 않았다**: 축 C 적용후를 RED 로 걸면 즉시 36건이 push 를 막으므로
배선 방식(즉시 RED / 래칫 baseline / 비차단 관찰)은 owner 판단을 받는다.

**교훈**: 게이트가 0 을 찍으면 **그 0 의 분모(검사 대상 수)를 같이 읽어라.** 이 저장소가
반복해 데인 "맞는 산수·틀린 범위"가 이번엔 검사기 쪽에서 났다.

---

## 2026-08-20 (l) — 뒤채움 라운드 종결. 등재를 "안 하는" 판단 2건과 룰 한계 1건을 기록한다

파서가 답한 내 스레드 3건을 전건 대조 후 **resolved**. 검증분(KB 억원 단위오판 8칸 제거 ·
분기 22→16 이 코어 0칸 · `eqYearPeriods()` 가 `.4Q` 만 써서 화면 무영향 · 농협생명 item7
원문 3필링)은 TODO `(l)` 에 실측과 함께 있다. 여기에는 **판단**만 남긴다.

**1. 등재하지 않기로 한 것 2건 — 레지스트리는 "억제할 finding 이 있을 때만" 쓴다.**
농협생명 item8 · 롯데손보 item8 은 N/A 판정이 옳다(각각 "보증준비금의 잔액 및 적립예정금액은
없습니다" 캡션 / 책임준비금 구성 나열 안의 `0`). 그런데 **R-RSV-9 기대 그리드가 "그 항목을 한
번이라도 공시한 회사"** 라서 행이 0개인 (회사,항목)은 애초에 그리드 밖이고, `--no-baseline`
전수에서 두 건 다 finding **0** 이다. 등재하면 아무것도 억제하지 않는 **죽은 항목**이 되고,
레지스트리를 읽는 사람에게 "여기 뭔가 억제되고 있다"는 오해를 남긴다. 진짜 재발 방지책은
parser 가 `_P1_CONCEPTS` 옆에 박은 **"보증준비금을 여기 추가하지 마라"** 주석이다 — 같은
개념명이 「가. 준비금 적립내역」·「라. 책임준비금 적립 내역」 표에도 나오는데 그건
**보험부채 구성요소**지 이익잉여금 안의 법정준비금이 아니기 때문이다.

**2. R-RSV-5 의 알려진 한계 — 결손 상태 회사의 잔액은 누적이 아니다.**
케이디비생명은 미처리결손금 상태라 기적립액이 계속 `-` 이고 `잔액 = 그 분기 적립예정액` 이다
(2026.1Q 원문: 기적립액 `-` / 적립예정금액 23,550 / 잔액 23,550, 같은 필링에 `미처리결손금`
6회). 그래서 2026.1Q 23,550 → 2026.2Q 4,323 의 비단조가 **진짜 현상**이다. R-RSV-5 는
"잔액은 누적이라 급변 불가"를 전제하므로 이 구조에 대해 오탐이다.

**레지스트리에 세 번째 축(스케일 점프 면제)을 파지 않았다.** R-RSV-5 는 ORANGE(비차단)이고,
비차단 룰 하나를 위해 gold 스키마를 넓히는 건 과설계다. 축을 팔 값어치는 그 룰이 push 를
막을 때 생긴다. 한계로 기록만 한다.

**3. 새로 드러난 것 — 삼성생명 item5 의 2년 반 공백.** 첫 실관측이 2025.4Q 다(제도는 2023년
시작). **뒤채움 사본이 이걸 가리고 있었고 사본을 걷어내니 드러났다 — 그게 (i)~(j) 라운드의
목적이었다.** 다만 `disclosed_none` 에 2023.3Q~2024.4Q 6분기가 owner 확정으로 이미 있으므로
실제 조사 대상은 2025.1Q~2025.3Q · 2023.1Q~2023.2Q 다. 티켓 `20260820T2340Z` A 항목.

**4. 잔여 이관.** 세 스레드에 흩어져 있던 미결(A 삼성생명 갭 · B AIG/메트라이프/BNP item4 ·
C flat 16건)을 `inbox/parser/20260820T2340Z` 한 곳에 모았다. C 는 재동결 **후** 목록이라
"이미 사라진 구간을 파는" 낭비가 없다(파서 요청). 한화생명이 6구간으로 최대 덩어리다.

게이트: RED=0 BASELINE=16 ORANGE=51 SUPPRESSED=76 · data_contract RED=0 exit 0 · 13 passed.

---

## 2026-08-20 (k) — 해약환급금준비금 개념은 안 섞였다. 그리고 내가 "자체 파싱 금지"를 어겨서 유령값을 봤다

`(j)` 끝에 남긴 질문 — 삼성화재는 BS 괄호 `적립예정액`(누적 램프), 현대해상은 P1 잔액(Q3 −23%)
이라 **한 열에 다른 개념이 섞인 것 아니냐** — 에 parser 가 태그로 답했다(`20260820T2210Z`).
**섞이지 않았다.**

```
삼성화재 2023.3Q  BS dart_SurrenderValueReserveToBeAdded  적립예정액  916,764,435,901
                  dart_SurrenderValueReserve 행 자체가 없음
현대해상 2023.3Q  BS dart_SurrenderValueReserve           기적립액             0
                  BS dart_SurrenderValueReserveToBeAdded  적립(환입)예정액 3,603,896,678,640
```

**2023년은 제도 첫 해라 두 회사 다 기적립액이 0/부재라서 `적립액 = 기적립액 + 적립예정액 =
적립예정액`** 이 된다. 내가 "다른 개념"이라고 본 두 값이 2023년에는 같은 것이다. 2024년부터
기적립액이 붙고 마스터는 둘을 더한다(현대해상 2024.1Q `3,422,425 + 552,832 = 3,975,257`).

**내 오류 — 이게 이 항목의 본론이다.** parser 표를 재확인하려고 FS-API 태그 매칭을 **손으로**
짰는데 `aid.endswith("SurrenderValueReserve")` 가 **CIS 의
`dart_AdjustedProfitLossNetOfSurrenderValueReserve`(해약환급금준비금 반영후 조정이익)** 까지
물었다. 그래서 "삼성화재 기적립액 670,968 / 현대해상 −80,965" 이라는 값을 얻고 parser 표(행없음
/ 0)가 틀렸다고 봤다. 그 숫자들은 **조정이익이지 준비금이 아니다.**

이 모듈 docstring 이 **"R-RSV-4/11/12 는 자체 파싱 금지 — `build_ifrs17_bs._extract_from_list`
를 호출한다"** 고 쓴 이유가 정확히 이것이고(2026-08-19 NH농협손보 오판의 교훈), 조정이익 표
함정은 `reference-reserve-adjusted-income-table-sign` 으로 이미 등재돼 있다. **아는 함정에
아는 규칙이 있는데 검증하겠다고 손으로 짜다가 그 함정에 빠졌다.** 빌더 함수를 쓴 같은 세션의
다른 검사들(삭제 98칸 FS-API 조회 등)은 전부 정상이었다 — 규칙이 맞고 내가 어긴 것이다.

**12.5배 차이의 정체**: 현대해상 BS 괄호의 해약환급금 숫자(352,471)는 이 마스터 item5 의 정의가
아니다. 같은 괄호에서 비상위험은 `29,265 + 1,242,298 = 1,271,563` 으로 P1 과 닫히는데 해약환급금만
안 닫힌다. 마스터는 현대해상에 그 괄호를 쓰지 않는다(P1/FS-API 만). 괄호를 읽는 핸들러는
`HANDLERS = {"KR0008": extract_samsung_fire}` 로 삼성화재 한 회사에만 등록돼 있다(확인함).

**소스 함정 기록(현재 무해)**: 현대해상 `FY2024_Q2` P1 표는 헤더가 제71기 2분기인데 법정준비금
3행이 1분기 값 그대로다 — 책임준비금만 `31,495,088 → 32,685,218` 로 갱신되고 해약 3,975,257 ·
비상 1,297,731 · 대손 126,794 는 정지. 마스터는 안 물었다(FS-API 합 4,218,680 채택). **"FS-API
우선, P1 은 gap-fill" 규칙이 실제로 막은 사례다.**

기계 가드는 넣지 않는 데 동의한다 — "직전과 같은 값이면 버린다"는 **정당한 flat 까지 버리고**,
그건 R-RSV-1 이 하루 종일 씨름한 바로 그 구분이다. 다만 더 좁은 지문을 남긴다:
**"값이 같다"가 아니라 "같은 표의 다른 행은 갱신됐는데 이 행들만 정지"** 라는 표 내부 모순.
P1 이 gap-fill 이 아니라 1순위가 되는 날 꺼낼 것.

마스터·게이트 변경 없음(sha256 `e27cb60f1e52650f`, RED=0 BASELINE=17).

---

## 2026-08-20 (j) — 래칫이 "데이터가 좋아져도" 막았다. 구간 키를 포함관계+값으로 교체

parser 가 `20260820T1900Z`(뒤채움 과대계상)를 처리하자 **신규 RED 6건**이 떴다. 원인은 데이터
악화가 아니라 **개선**이었다 — 뒤채움 사본 98칸을 걷어내니 flat 구간이 짧아졌는데,
`statutory_reserve_baseline.json` 의 래칫 키가 `quarter: "2023.1Q~2024.3Q"` 같은 **구간
문자열**이라 축소된 구간이 키에서 빠져 새 결함으로 잡힌 것이다. 예: DB생명 item5
`2023.1Q~2024.3Q` → `2023.4Q~2024.3Q`, 값은 1,633,087 그대로.

**래칫이 막아야 하는 것은 '새로운 결함'인데 '같은 결함의 경계 이동'까지 막았다.**

**재동결 전 독립 검증 4종** (재동결은 면제 행위라 요청을 그대로 수용하지 않는다):

1. **삭제 98칸에 실관측이 섞였나 → 0건.** 셀을 지우면 flat 결함도 같이 사라지므로 여기가 제일
   위험하다. 98칸 전부 FS-API OFS 캐시를 직접 조회했고 전부 원천이 침묵하는 칸이었다.
2. **changed 10칸이 내 독립 판독과 일치.** 삼성화재 2023.2Q 556,503 · 메리츠 2023.1Q
   328,904/63,276 은 `(i)` 항목에서 내가 raw 로 읽은 값 그대로다. 현대해상 4칸도 P1 표와 일치.
3. **`--no-baseline` 전수 분류: RED 17 = 정확일치 11 + 축소분 6 + 신규 0.** 신규 0 확인 후 재동결.
4. **골든 재현성**: `test_ifrs17_bs_golden` 386초 통과 + **실행 전후 마스터 sha256 동일**
   (백업 후 실행 — 그 테스트는 마스터를 인플레이스로 덮는다). 마스터는 빌더 산출 그대로다.

**조치**: baseline 34 → 17 재동결. 구간 매칭을 **`포함관계 + value 일치`**로 교체하고 각 엔트리에
`value` 필드를 넣어 메시지 문자열 파싱을 없앴다. 둘 다 요구하는 이유 — 포함만 보면 프리즌 구간
안에서 **다른 값**의 새 flat 이 생겨도 흡수하고, 값만 보면 구간이 **길어진 것**(결함 확대)을
통과시킨다. 4시나리오 실검사: 동일 구간·동일 값 → 흡수 / 축소 구간·동일 값 → 흡수 /
프리즌 안·다른 값 → 차단 / 프리즌 밖 확장·동일 값 → 차단.

> **같은 병을 하루에 두 번 앓았다.** 오전 `(g)` 에서 `legit_flat` 이 span 정확일치라 owner 이월로
> 구간이 늘자 등재해 둔 정당 사유가 RED 로 되살아났고 from/to 포함관계로 고쳤다. 그때
> **옆 레지스트리(baseline)에 같은 병이 남아 있는 걸 보지 않았다.** 한 곳에서 발견한 실패 양식은
> 같은 모양의 다른 저장소에도 바로 대조할 것 — **구간 키를 문자열 정확일치로 잡지 말 것.**

**결과**: RED=0 BASELINE=17 ORANGE=51 SUPPRESSED=75 · `validate_data_contract` RED=0
YELLOW=276 exit 0 · 골든 6종+deploy_assets 15 passed. push 차단 없음.

YELLOW 254 → 276 은 **R-RSV-9 census +19**(전건 ORANGE). 뒤채움 사본을 걷어낸 자리가 이제
**정직한 결측**으로 잡히는 것이라 의도한 방향이다 — 지어낸 값보다 빈 칸이 낫다.

**미결(비차단)**: 해약환급금준비금 2023년 값의 **개념이 회사별로 갈릴 수 있다.** 삼성화재는 BS
괄호주기 `적립예정액`(259,134→556,503→916,764→1,180,012 누적 램프), 현대해상은 P1 표 잔액
(4,391,552→4,658,628→3,603,897→3,422,425, Q3 −23%). 현대해상은 같은 필링의 BS 괄호주기가
`적립예정금액 352,470,800,897원`(=352,471)이라 P1 과 **12.5배** 차이다. 파서에 정의 정리 요청.

---

## 2026-08-20 (i) — 면제 근거가 "추출기의 침묵"이면 순환이다. rollforward 면제를 '필링의 부재'로 좁힘

parser(`inbox/parser/20260820T0430Z` 답변 2)가 R-RSV-1 flat 44건 중 **28건을 "빌더가 복제한
칸이라 flat 은 구성상 필연"**이라며 일괄 면제를 요청했다. 분해는 독립 재현해 **숫자까지 일치**했고
(마스터에서 span 재계산 → 28/16), 논리도 옳다 — 우리가 만든 사본을 우리가 결함으로 다시 세면
순환이다. 뒤채움은 첫 관측이 구간 **끝**에 오므로 `span[1:]` 이 아니라 **실관측 수**로 세야 한다는
지적도 맞다.

**그런데 근거가 순환이었다.** 요청의 출처인 사이드카 `rollforward_filled` 는 **빌더가 "값을 못
얻었다"고 판단한 칸의 목록**이다. 그러면 두 명제가 구분되지 않는다:

- (A) 회사가 그 분기에 **필링을 안 냈다** → 진짜 원천 부재. 면제 정당.
- (B) 필링은 있는데 **우리 추출기가 못 읽었다** → 면제하면 결함이 영구히 숨는다.

**(B) 가 실재한다.** 삼성화재 `FY2023_Q2/20230814002808.xml` 이익잉여금 행에
`(해약환급금준비금 적립예정액: 556,503,490,830 원)` 이 그대로 실려 있는데, 마스터 2023.2Q 는
**916,764 백만원**(2023.3Q 실관측치의 뒤채움) — 공시값 556,503 의 **1.65배**다. 메리츠 2023.1Q 도
'재무건전성' P1 3기간표에 `비상위험준비금 328,904 | 321,055 | 301,971` ·
`대손준비금 63,276 | 50,364 | 33,839` 이 있는데 마스터는 321,055 / 42,012 다. 빌더 자신의
`parse_filing()` 에 이 필링들을 직접 물려도 **17칸 전부 값을 못 얻는다(0/17)** — 사람이 원문에서
읽히는 값을 추출기가 못 본다. **그러므로 추출기의 침묵은 면제 근거가 될 수 없다.**

**조치 — `validate_statutory_reserves.rollforward_exempt()` 신설.** 면제 기준을 '추출 실패'가
아니라 **'필링의 부재'**로 잡고, 게이트에서 두 조건을 **다시 확인**한다(`carry_forward_exempt()`
와 같은 구조): ① raw 디렉터리가 없거나 `meta.json` 이 `no_filing: true`, **그리고** ② FS-API
캐시도 그 (분기, 항목)에 값을 주지 않는다. 결과 **9구간만 억제**(2021~2022 raw 미수집 7 +
서울보증 2024 `no_filing` 2). 필링이 실재하는 **21구간은 면제하지 않았다.**

> **함정 기록**: 서울보증 FY2024 Q1~Q3 은 raw 디렉터리가 **있고 안이 비어 있다**
> (`{"period":..., "no_filing": true}`, xml 0개). 디렉터리 존재만 보면 필링이 있는 것처럼 보인다 —
> 초기 프로브가 이걸 "필링 존재"로 세어 예측이 7구간이었는데 실제 억제는 9구간이었다.
> **`no_filing` 마커를 같이 보지 않으면 반대 방향 오판이 난다.**

**부수 발견 — 뒤채움 75칸.** `rollforward_filled` 355칸을 첫 실관측 기준으로 가르면 앞채움 280 /
**뒤채움 75**(2021=18 · 2022=3 · **2023=43** · 2024=6 · 2025=5). 2023 이 위험한 이유는
해약환급금준비금 제도 첫 해라 잔액이 0에서 급증하는 구간이라서다 — Q3/Q4 값을 Q1/Q2 로 복사하면
계통적 과대계상이 된다. 원인은 fold-in(`기적립액 + 적립예정액`)이 **Q4 에만** 걸리는 것
(`_rollforward_reserve_series` 의 `s[(fy, 4)] = folded`). 발주 `inbox/parser/20260820T1900Z`.
**FY말·2024년 이후 값은 이 결함의 영향을 받지 않는다.**

**에이비엘생명 item7 `legit_flat` 등재.** FS-API OFS 캐시 11개 필링 전수 확인 — 전부
`status=000`(무응답 013 아님)이고 `대손준비금 기적립액` 이 **6,336,633,809원으로 동일**,
`적립예정액` 라인이 없다. **`2023.4Q~` 만 등재**하고 `2023.1Q~2023.3Q` 는 전수 확인을 못 해
baseline 에 남겼다(확인하지 않은 셀을 등재하는 것은 결함 은폐 — 2026-08-20 (e) 의 자기정정과 같은 선). 
등재 근거의 **종류**가 하나손보·비엔피파리바(원문에 적립 중단 사유가 있는 결손금 케이스)와 다르다는
점을 레지스트리에 명시했다 — 에이비엘은 흑자이고, 근거는 서사가 아니라 **원천 대조**다.

**카카오페이 재검증 통과**(parser 열 판정 버그 수정). 본문 XML 에서 자산/부채/자본총계 6개 값을
직접 확인했고 기간 배정이 맞다. 항등식이 두 분기 모두 **차 0.0**, item13 의 한 해 밀림도 해소.

**결과**: `validate_statutory_reserves.py` RED=0 **BASELINE 44 → 34** ORANGE=43 SUPPRESSED=84 ·
`validate_data_contract.py` RED=0 YELLOW=253 exit 0 · 13 tests passed. baseline 축소 10건
(면제 9 + 에이비엘 1), 신규 RED 흡수 0건 확인 후 `_shrink_log` 기록.

**교훈 (일반화)**: 검사받는 쪽이 만든 목록을 면제 근거로 쓸 때는, 그 목록이 **관측의 부재**를
말하는지 **추출의 실패**를 말하는지 먼저 갈라야 한다. 둘은 같은 파일에 같은 모양으로 적힌다.

---

## 2026-08-17 (b) — CSM 부호 규약 룰 신설. 폐쇄식이 잔차로 닫혀 부호역전을 통과시키던 자리

예별손해보험 2023.4Q 는 **신계약 △509.7 / 이자 △203.1 / 상각 +471.8** 로 세 항목이 뒤집혀 있었는데
폐쇄식은 정확히 닫혀 있었다 — **조정(item4)이 잔차(plug)라 차액을 흡수**하기 때문이다.
라이나 건(조정이 계약경계 효과를 흡수)과 같은 함정이 다른 얼굴로 재발한 것이다.

**원인**: 그 필링은 잔액 블록이 부채 기준인데 **변동 블록이 손익(P&L) 기준**이다
(`기말 = 기초 − Σ변동` 으로 닫힌다). 상각이 +로 찍힌 건 그게 보험수익이라서다. 추출기가 변동 행
부호를 그대로 옮겼다. 정정 후 raw 행 합(47,749,807천원 = 477.5억)이 역산값과 독립 일치.

**이번 라운드에서 배운 판별식의 함정**: parser 가 2025.4Q 를 "덧셈으로 닫히니 정상"이라고 판정했는데,
**기말=0 이면 그 검산은 퇴화한다**(뺄셈은 `2×기초` 라 애초에 못 닫힘). 결론은 맞았지만 근거는 무효였다.
믿을 수 있는 판별식은 **상각 행 부호** 하나다.

**신설 룰** `CSM_SIGN_CONVENTION` (RED): 신계약 CSM < 0 또는 CSM 상각 > 0.
전사 355:1 로 만장일치인 축이라 오탐 여지가 사실상 없다. 예외 1건(예별 2025.4Q)은
`_CSM_SIGN_EXCEPTIONS` 에 raw 근거 전문과 함께 등재하고, **조용히 숨기지 않고**
`CSM_SIGN_CONVENTION_EXCEPTED` YELLOW 로 사유를 계속 노출한다.
(그 회사는 손실부담 전입/환입을 CSM 열 안에 표시해 신계약 행이 onerous 분을 net 한다 — 표준 표기는
그 행의 CSM 열을 비운다. 라이나 동일 표로 대조 확인.)

**부수 효과**: "다른 회사도 이 서식인가"라는 스윕 발주가 불필요해졌다. 지문이 `상각>0` 인데
마스터 전수에서 0건이므로, 회사별 raw 대조 없이 답이 나온다. 게이트 RED=0 / YELLOW=224, selftest 34/34.

## 2026-08-17 — RED=0 도달, 2026.2Q 라이브 배포 차단 해제

라이브 오표시(삼성화재 2026.2Q PL 0)에서 시작한 라운드 종결. 교차대조 3종 RED 승격 → 21건 →
parser 20건 해소 → AIG 1건 downloader fetch → **RED=0 / exit 0**.

| 지표 | 2026-08-15 | 2026-08-17 |
|---|---|---|
| PL↔워터폴 교차대조 | 정상 305 / 배수이탈 12 / 한쪽만 빔 22 | **정상 340 / 0 / 0** |
| 게이트 | RED 21 (승격 후) | **RED 0** |
| `zero_legs` | 11 | 4 |
| `closing` | 355P/1S | 356P/0F/0S |

**파서가 밝힌 근본원인**: DART 가 2026.2Q 반기보고서부터 CSM상각 행 라벨을 재구성했고
("서비스의 이전으로…" → "보험계약서비스의 이전 때문에…"), 그 문자열이 회사별로 **서로 다른
하드코드 상수 4곳 이상**에 박혀 있어 12사가 한꺼번에 터졌다. 곁가지로 현대해상만 공시단위가
원→천원으로 바뀌었고, DB생명·교보·동양은 반기보고서 [3개월,누적] 4컬럼에서 3개월 컬럼을 읽고
있었으며, 롯데는 FS-API 캐시가 필링 당일 조회로 status=013 에 고착돼 있었다.

**이 라운드가 남긴 교훈**: 단일 마스터 안의 폐쇄식은 이 사고를 하나도 못 잡았다(전부 닫혀 있었다).
**두 마스터가 같은 사건을 각자 들고 있을 때, 그 둘을 대조하는 것만이 탐지기**였고, 배수 수렴
(0.33~0.52 → 0.99~1.04)이 값이 맞다는 증거까지 제공했다.

**게이트를 상한으로 쓰지 말 것 (신규 발주)**: parser 가 AIG item9 을 raw 에서 찾아 놓고
*"룰이 item4 단독 비교라 문제 없음"* 을 근거로 비워 뒀다. 룰이 관대한 것이 값을 빼도 되는 근거가
되면 게이트는 품질의 하한이 아니라 상한이 된다. 지적하고 발주(`20260817T0400Z`).
동시에 `item9 or 0` 로 결측을 흡수하는 내 룰의 결함도 인정하고, 정당 결측(28건 중 대다수)과
구분할 근거가 생기기 전에는 조이지 않기로 했다.

**여전히 미배선(UH)**: 배포 직전 **main 기준 게이트 재실행**. 이번 사고의 구조적 원인이
"게이트는 작업트리를, 사용자는 main 을 본다" 였는데 그 축은 아직 절차가 없다.

## 2026-08-17 — 교차대조 RED 21 → 1. 파서 답신 검증 + "raw 없음" 오종결 정정

신설 교차대조 3종(RED 승격)에 대한 parser 답신을 마스터에 대고 전수 재측정.

**통과**: 340쌍 중 정상 339 / 배수이탈 0 / 한쪽만 빔 1(HEAD 는 305/12/22). 셀 유실 0.
`closing 355P/1S → 356P/0F/0S`, `zero_legs 11 → 4`, selftest 33/33, 골든 3종 PASS.

**값 검증 방법 — 배수 수렴을 증거로 썼다.** 고쳐진 자리들의 PL/워터폴 배수가 **0.33~0.52 → 0.99~1.04**
로 수렴했다. 2Q 에서 0.5, 3Q 에서 0.35 라는 값은 **누적(YTD) 자리에 당분기 값을 실었을 때 나오는
정확한 지문**이고(H1 대비 Q2 = 1/2, 9M 대비 Q3 = 1/3), 그게 1.0 으로 붙었다는 건 서로 다른 note 에서
독립 추출된 두 수가 일치했다는 뜻이다. 단일 마스터 안에서는 어떤 폐쇄식으로도 얻을 수 없는 증거다.

**정정 — "raw 없음"을 액면 그대로 받지 않았다.** parser 가 AIG손해보험 2023.4Q 를 *"저장소에 없어
재추출 불가"* 로 종결했는데, OpenDART 공시목록을 조회하니 `20240403002101 감사보고서 (2023.12)` 가
그대로 있었다. **저장소에 없는 것과 소스에 없는 것은 다르다** — 라우팅 규칙(memory: route-by-raw-availability)
그대로 downloader 로 넘겼다. 이 한 건이 현재 RED 전부이고, 받아오면 RED=0 → 2026.2Q 라이브 배포가 풀린다.
(함정 기록: DART 등록명이 "AIG" 라 "AIG손해보험"으로는 이름검색이 안 걸린다.)

**남긴 위험**: `extract_tier2_abl` · `_oll_ytd` 는 공용함수 blast radius 때문에 **코드가 아니라 override 로만**
고쳐졌다. 같은 경로를 타는 다른 회사가 재빌드에서 재발할 수 있고, 그건 이제 교차대조 RED 가 상시 감시한다.

## 2026-08-15 (p) — 신설 룰 4종 즉시 RED(관찰기 폐지). RED=21, push 차단

owner 지시: *"신설 3종도 당연히 맞아야지."* 이 저장소의 관행(신설 룰은 YELLOW 관찰 1~2 릴리스 후
승격 — `CSM_WATERFALL_PLAUSIBILITY`/UH-3 선례)을 **이 건에는 적용하지 않기로 했다.**
근거가 분명하다: 관찰기는 "탐지기가 오탐을 내는지 모를 때" 쓰는 장치인데, 이번 3종은 **이미 라이브
오표시를 실제로 잡아낸 뒤**였다. 잡히는 걸 확인하고도 안 막으면 그건 관찰이 아니라 방치다.

| rule | 현재 | 비고 |
|---|---|---|
| `PL_CSM_AMORT_VS_WATERFALL` | 14 | PL 쪽만 빔 |
| `PL_CSM_AMORT_SCALE_GAP` | 6 | 에이비엘 4건이 일관되게 0.1배 = 단위 혼입 의심 |
| `CSM_AMORT_MISSING_VS_PL` | 1 | 미래에셋 2026.2Q, 폐쇄식이 조정으로 닫혀 안 보이던 자리 |
| `PL_YTD_COLLAPSE_TO_ZERO` | 0 | 파서가 이미 소진 → **무료 승격**(회귀 잠금 목적) |

게이트 RED=21 / YELLOW=223, exit 2. selftest 33/33(L1·L2 기대 severity 갱신), 골든 3종 PASS.

**대가를 명시해 둔다**: 값이 이미 검증된 2026.2Q 9개사 배포도 함께 막힌다 → 라이브의 "0 표시"가
그동안 남는다. owner 가 그 순서를 알고 선택했다. 종결 조건 = 21건 소진 → RED=0 → 배포.

## 2026-08-15 (o) — 라이브 오표시 사고: PL↔CSM_waterfall 교차대조 부재 + 게이트가 main 을 안 봄

owner 가 화면에서 삼성화재 2026.2Q 원수CSM상각·RA해제가 전부 0 인 것을 발견. 게이트는 RED=0 이었다.
**false-green 두 겹**이었고 둘 다 배선으로 닫았다.

### 1. 게이트가 작업트리만 검사했다
"게이트가 검사하는 파일 = 사용자가 보는 파일"을 **브랜치 축에서 적용하지 않았다.** 같은 룰을 `main` 에
돌리자 2026.2Q 9개사(삼성화재·DB손보·현대해상·한화생명·한화손보·흥국화재·미래에셋·롯데손보·코리안리)의
PL 생명장기 분해가 통째로 null 인 것이 즉시 드러났다. 작업트리는 이미 정상이고 값이 워터폴 상각과
소수점까지 일치한다 → 배포로 해소(publishing 발주). **UH 로 남긴 것: 배포 직전 main 기준 재실행 절차화.**

### 2. 같은 사건을 든 두 마스터가 서로를 안 봤다
`PL_breakdown` 의 CSM상각과 `CSM_waterfall` 의 상각액은 같은 회사·같은 분기의 같은 사건인데 대조가 없었다.
**폐쇄식은 결측을 통과시킨다** — null/0 은 등식을 깨지 않고 다른 항이 흡수하면 그대로 닫힌다.
신설 3종(`check_cross_source`, selftest L2):

| rule | 잡는 것 | 현재 |
|---|---|---|
| `PL_CSM_AMORT_VS_WATERFALL` | PL 쪽만 빔 | 14 |
| `PL_CSM_AMORT_SCALE_GAP` | 배수 0.4~2.5 이탈 | 6 |
| `CSM_AMORT_MISSING_VS_PL` | **워터폴 쪽만 빔(역방향)** | 1 |

역방향 1건 = 미래에셋생명 2026.2Q. 상각 1,128억이 빠졌는데 `기초+신계약+이자+조정 = 기말` 이 정확히
닫힌다(조정이 plug). 기존 `IMPOSSIBLE_ZERO_AMORT` 는 `상각 == 0` 만 봐서 **`None` 을 통과시켰다** —
"0 만 검사하고 결측을 안 보는 룰"이라는 같은 함정의 다른 사례다.

### 교훈
개념이 완전히 같지 않다고(손보 PL 은 생명장기 leg, 워터폴은 전사) 대조를 미루면 **아예 안 보게 된다.**
밴드를 느슨하게(0.4~2.5) 잡고 "한쪽만 비어 있는 자리"만 노려도 사고는 잡힌다.

## 2026-08-15 (k) — 라이나 CSM 경계 위반의 정체는 **소급재작성**. 진단 두 개(파서·검증)를 raw 로 뒤집음

파서가 "원천 데이터부터 틀렸다"고 회신 → raw 두 필링을 열어 전 열 재계산. **양쪽 진단이 다 틀렸다.**

### 파서 근거 기각 — 뺄셈 자리에 덧셈

*"기초 보험계약자산 + 기초 보험계약부채 ≠ 기초 잔액"* 이 원천 이상의 근거였다. 그 표의 정의는
**`잔액 = 부채 − 자산`**(자산은 음의 부채)이고, 그렇게 계산하면 기초·기말 **7개 열 전부 정확히 일치**한다.
표는 흠이 없다.

### 검증(내) 진단도 취소 — "스케줄 표에서 뽑았다" / "항목4 는 plug"

값은 진짜 측정요소별 변동표에서 나왔다. 스케줄 표 합계가 CSM 잔액과 같은 건 **정상** —
그 표는 *"보고기간말 CSM 을 기대상각기간별로 배분"* 한 것이라 합계가 곧 잔액이다.
두 표 일치는 오류가 아니라 교차확인이었다. 항목4 30,211.1억도 plug 가 아니라
`추정치변동분(−4,182.9) + 계약의 경계 변경 효과(+34,394.0)` 로 raw 에 그대로 있다.

> **숫자가 정확히 일치한다는 사실만으로 "같은 표에서 베꼈다"고 읽으면 안 된다.**
> 두 공시표가 같은 잔액을 서로 다른 절단면으로 보여주는 경우가 있고, 그때 일치는 증거가 아니라 정합이다.

### 진짜 원인

같은 FY2023 을 두 필링이 다르게 말한다. **양쪽 다 자체 폐쇄식은 정확히 닫힌다.**

| FY2023 CSM | 원공시 `20240409003674` | FY2024 필링 `20250409002702` 전기 비교표시 |
|---|---|---|
| 기초 | 22,082.5억 | 35,264.0억 |
| 기말 | **55,155.5억** | **32,301.6억** |

차이는 한 줄 — 원공시에만 있는 `기타 → 계약의 경계 변경 효과 +34,394억`(순부채 영향 0,
측정요소 간 재배분)이 재작성본에서 사라졌다. **정정공시는 없다**(비상장 → 감사보고서만,
DART 목록 4건 전수 확인). 재작성은 다음 해 보고서의 전기 비교표시로만 반영됐다.
마스터가 2023.4Q=원공시 / 2024.4Q=재작성본을 나란히 든 상태 = 경계 파열. **어느 쪽도 파싱 오류가 아니다.**

### 처분과 원칙

2023.4Q 를 **전기 비교표시 기준으로 재작성**(기초 35,264.0 → 기말 32,301.6) → 2024.4Q 기초와 정확히 연결.
추출 좌표·6항목 값·검산까지 실어 발주(`inbox/parser/20260815T0940Z…`). 선례 = `20260620T0600Z` 교보 건.

`feedback_continuity_break_is_red` 는 유효하다. 다만 이 케이스의 올바른 종결은 **"재작성이니 면제"가 아니라
"raw 로 재작성을 확정한 뒤 재작성 기준으로 값을 맞춘다"** 이다 — 면제도 아니고 값 보정도 아니다.

## 2026-08-15 (j) — 파서 재조치 검증: 5사 override 철회 확인, 남은 RED 1건은 "스케줄 표를 CSM 잔액으로 쓴 것"

(i) 에서 `CSM_CONTINUITY_FY_BOUNDARY` 를 push 게이트로 올린 직후의 첫 실사용 라운드.
파서 재조치 후 **RED 11 → 1**.

### 5사 앵커 — 철회가 진짜인지 raw 까지 확인

iter 2 에서 반려했던 "1Q 를 2Q 에 맞추는 override" 는 완전히 철회됐다:
교보·신한라이프·메리츠·에이비엘·푸본현대의 **2026.1Q 6항목이 HEAD 와 완전 동일**,
`2025.4Q 기말 == 2026.1Q 기초 == 2026.2Q 기초`(Δ 0.0), 골든도 `6cont` → `1cont` 로 되돌아왔다.

다만 "다섯 회사가 전부 앵커와 정확히 같아졌다"는 상태는 **앵커를 베껴 넣어도 똑같이 보인다.**
그래서 raw 로 갈랐다 — 메리츠 2026.2Q 반기보고서 원문에서 기초 CSM
`11,103,697`(백만원) = 111,037.0억을 직접 확인. 복사가 아니라 실제 공시값이다.
**"수치가 맞다"와 "출처가 맞다"는 다른 질문이고, 후자는 raw 에서만 답이 나온다.**

### 남은 RED 1건 — 라이나생명 2023.4Q

`2024.4Q 기초 32,302 != 2023.4Q 기말 55,156 (Δ-22,854)`. 2023.4Q 쪽이 틀렸고, 숫자 정확 일치 2건으로 특정:

| 마스터 | 값 | 출처 표 | 원문 |
|---|---|---|---|
| 2023.4Q 기말 | 55,155.5억 | "기대상각기간별 보험계약마진" 표 | 5,515,548,316천원 |
| 2023.4Q 기초 | 22,082.5억 | 같은 caption 두 번째 표 | 2,208,247,317천원 |

그 필링에서 추출된 CSM 표 **4장이 전부 상각스케줄이고 변동표는 0장**이다. 스케줄 합계는
**미래 상각액의 단순합(할인 전)** 이라 CSM 잔액보다 구조적으로 크다(55,155.5/32,301.6 = 1.71).

**폐쇄식은 이 건을 잡을 수 없었다.** 조정(항목4) 30,211.1 이 나머지를 맞추는 역산 plug 라
6항목 합이 저절로 닫힌다(356블록 중 352가 닫힘). **FY 경계 룰이 유일한 탐지기**였다 —
(i) 의 승격 판단이 하루 만에 값을 했다. → `inbox/parser/20260815T0700Z…`

동봉: 신규 2023.4Q 3건이 앵커가 없어 경계 검사 자체가 불가능하다(메트라이프·처브라이프·AIA).
AIA 는 24·25 가 함께 들어와 체인을 확인했고, **메트라이프는 라이나와 같은 지문**(추출 표가
스케줄뿐)이라 값 출처 확인을 같이 요청했다. **앵커 없는 블록은 "통과"가 아니라 "미검사"다.**

### 그 외

- **17BS 확장 통과**: items 1-31(1,637→5,008행, 섹션/레벨 키 추가)인데 `BS_IDENTITY` 위반 0 ·
  코어(1·2·3·4) 결측 0. 세부행은 코어에 넣지 않았고 **새 룰도 만들지 않았다**(owner 지침).
- **회귀 없음**: CSM 행 유실 0(1,962→2,136) · `--selftest` **31/31** ·
  `test_master_tables_golden` + `test_deploy_assets` **11 passed** · `--no-build` SUMMARY 골든 일치.
- push 게이트 **RED=1 / YELLOW=236 (exit 2)** — 차단 유지.


## 2026-08-14 (f) — owner 종결: 비상장 6개사 census 면제. RED 42 → 0, 17BS 라운드 종료

owner: *"그 귀찮은 짓을 하지 말라니까? 걔네는 걍 접고 마무리해."*
(e) 에서 **채울 소스가 없다**는 게 실측으로 확정됐으므로, 그 결측을 RED 로 두면 게이트가 영구히
push 를 막는다. 소스 없는 결측은 게이트가 아니라 **스코프**의 문제다.

### 반영

- `validate_data_contract.py` 에 `IFRS17_BS_NO_SOURCE` = 비상장 6개사(AIG · 하나손해 · 신한이지 ·
  비엔피파리바카디프 · 메트라이프 · IBK연금) → **코어 census 면제**.
- **면제 근거를 파일이 아니라 코드 주석에 박았다.** 방금 아카이브한 예외 레지스트리
  (`equity_census_exceptions.json`)를 되살리지 않기 위해서다. 주석에는 판정 근거 3종을 남겼다:
  OpenDART `013`/`014` 실측 · **상장 대조군 정상**(= 우리 호출 문제가 아님) · owner 지시일자.
- **면제는 census 한정.** `BS_IDENTITY` 는 이 6개사에도 계속 돈다 — 값이 들어오는 순간 구조검사를
  그대로 받는다. "회사를 통째로 검사 밖으로 빼는" 형태를 피했다.
- 조용히 사라지지 않게 **집계 YELLOW 1건**(`BS_CENSUS_NO_SOURCE_COMPANY`)에 11블록을 이름으로 찍는다.

### 결과

**RED=0 / YELLOW=220 (exit 0)** · `--selftest` **25/25** · `pytest tests/test_deploy_assets.py` **10/10**.
push 차단 해제(배포 판단은 publishing + owner 승인).
발주 티켓 2건 종결 → `inbox/_resolved/` (`20260814T0500Z` 재확인 후 resolved,
`20260814T0620Z` owner 취소로 resolved). **validation inbox 비어 있음.**

### 남긴 판단 기록

이번 라운드에서 예외 등재를 **한 번 거절하고(삼성생명, 소스가 고쳐질 수 있었다) 한 번 수용했다
(비상장 6개사, 소스가 존재하지 않는다).** 갈림길은 "RED 이 몇 건이냐"가 아니라 **"고칠 소스가
있느냐"** 였고, 그 판정을 추측이 아니라 API 실측 + 대조군으로 했다. 다음에 같은 상황이 오면
같은 순서로 — 먼저 소스 존재를 증명하고, 그 다음에 면제한다.

## 2026-08-14 (e) — 비상장사 17BS 결측에 **OpenDART 우회로는 없다**(실측 확정, 발주 없음)

owner 가 "비상장사라 누락된 것 같다"며 API 2종(`apiId=2019019` · `2019020`)을 지목하고
**샘플 1사로 확인 → 나오면 downloader 발주, 없으면 패스**를 지시했다. 결과는 **둘 다 막힘**.
기록 목적은 하나 — **재조사 방지.**

### 무엇을 쟀나 (대조군이 이 조사의 핵심)

| API | 비상장 3사: IBK연금 · 메트라이프 · AIG (필링 6건) | 상장 대조군: 한화생명 (3건) |
|---|---|---|
| `fnlttSinglAcntAll` (2019020, 이미 쓰는 것) | `status=013 조회된 데이타가 없습니다` (OFS·CFS 공히) | `status=000` OFS 245행 / CFS 346행 |
| `fnlttXbrl` (2019019, 이번에 처음 호출) | `status=014 파일이 존재하지 않습니다` **6/6** | **ZIP OK** 1.4-1.7MB · 7파일 **3/3** |

`014` 만 보고 "API 가 안 된다"고 적으면 **우리 호출이 틀렸을 가능성**과 구분이 안 된다.
대조군 3/3 성공이 그 구분을 만든다 — **호출은 맞고 파일이 없는 것.**
구조적 이유: `fnlttXbrl` 은 **정기공시(사업/반기/분기보고서)에 첨부된 XBRL** 을 주는 API인데,
비상장 보험사는 DART 에 **감사보고서(F)만** 낸다(IBK연금은 2025-2026 공시 2건이 전부 감사보고서).

### 그래서 무엇이 달라지나

RED 42셀(Tier-2 6개사 코어 1·2·3·4)은 **"다른 소스로 채우면 되는 것"이 아니다.**
감사보고서 본문 XML 파싱(`build_equity_composition_tier2.parse_filing`)을 고치는 것이 유일 경로 →
iter 2 티켓(`inbox/parser/20260814T0620Z…`)에 위 표를 근거로 붙여 발주 유지. downloader 발주 없음.

### 같이 확인된 것

- **iter 1 스레드 종결**(`inbox/_resolved/20260814T0500Z…`): 파서 답변을 마스터에 대고 독립 재측정 —
  `BS_IDENTITY` 전수 **0건**(삼성생명 OFS 고정 확인), AOCI 코어 결측 **0건**(한화·흥국·AIA·아이엠라이프
  16셀 소멸, item4 265→282행), 항목 6·7 신규 유입(P-5). **소스 수정으로 소멸 누계 18 / 예외 등재 0.**
- `pytest tests/test_deploy_assets.py` **10 passed** — publishing keep-list swap 착지로 (d) 의
  배포 blocker 해소. 남은 blocker 는 **RED=42 하나**. `--selftest` 25/25.

## 2026-08-14 (d) — 배포 승격으로 게이트 실차단 전환. RED 0 → 42 (코드 수정 0줄)

`IFRS17.html` 이 `IFRS17_BS.json` 을 실제로 fetch 하기 시작(16:39 KST)하면서 **"배포 HTML 이
읽으면 RED, 아니면 YELLOW"** 판정식이 설계대로 발동했다. 같은 findings 가 심각도만 승격됐다.

| | (c) 시점 | (d) 현재 |
|---|---|---|
| `validate_data_contract.py` | RED=0 / YELLOW=261 (exit 0) | **RED=42** / YELLOW=219 (exit 2) |

### RED 42 = 원인 한 가지 — Tier-2 재무상태표 본표 미추출
6개사 11블록에서 코어 1·2·3·4(자산/부채/자본/AOCI)가 통째로 없고 준비금 계열(5·7)만 들어와 있다:
IBK연금 3분기 · 메트라이프 3분기 · AIG 1 · 하나손 1 · 신한이지 1 (+ KR0075 2분기는
**owner 지시로 이번 턴 보류**). `TIER2_ITEM_MAP` 의 40/41/1/6 이 안 채워지는 원인 조사를
`inbox/parser/20260814T0620Z…`(iter 2)로 발주 — 값 보정 요청 0건.

### owner 정정 1건 — IBK 를 "준비금 결측"으로 읽지 말 것
IBK연금은 2023.4Q 해약환급금준비금 **기적립액 0 + 전입액 185,680백만원**이 정상이고
(→ 2024.4Q 기적립액 185,680), **항목 5 는 optional 이라 게이트가 애초에 안 본다.**
그 회사의 문제는 자산/부채/자본/AOCI 가 전 분기 없다는 것. 파서 티켓에 오독 방지 문구로 못박았다.

### 소스 수정으로 소멸 누계 14건 — 예외 등재 0건
(c) 의 10건 + **AIA생명 AOCI 3 · 아이엠라이프 1**(그 직후 파서가 채움: AIA 2023.4Q=1,362,853 /
2024.4Q=131,569 / 2025.4Q=△231,188 · 아이엠라이프 2025.4Q=△616,989).
owner V-3 이 요구한 "예외로 덮지 말고 소스를 고쳐 소멸시킨다"가 전 구간 성립했다.

### 배포 blocker 가 designer → publishing 으로 이동
`pytest tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` FAIL 의 대상이 바뀌었다.
designer repoint 는 완료(`IFRS17.html` 이 `IFRS17_BS.json` 을 fetch, designer 문서도 언급함).
이제 **`claude-agent-publishing.md` 가 `IFRS17_BS.json` 을 언급하지 않는다** = keep-list 누락 →
그대로 배포하면 라이브 404(루트 JSON 3개 누락 전례와 동형). 기존 owner 발주
`inbox/publishing/20260814T0232Z…keeplist_swap_equity_to_ifrs17_bs.md`(open)가 그 자리라 신규 발주 없음.

## 2026-08-14 (c) — 파서 재빌드 후 독립 재검증 + 스레드 4건 종결. RED=0 유지, 17BS 40 → 42

(b) 의 수치는 재빌드 **직전** 스냅샷이었다. `IFRS17_BS.json` 이 그 직후(14:42 KST, 1,546행)
파서 P-1/P-2 반영으로 다시 쓰였기 때문에 게이트를 재실행해 전수 대조했다.

### 결과
`validate_data_contract.py` **RED=0 / YELLOW=261**(exit 0, (b) 시점 259에서 +2) ·
`--selftest` **25/25** · `pytest tests/test_deploy_assets.py` **1 failed / 9 passed**
(FAIL 은 `IFRS17.html` 이 아직 `equity_composition.json` 을 fetch 하는 건 하나뿐 — designer·publishing 대기).

### 소스 수정으로 소멸한 10건 — **예외 등재 0건**
| 건 | 수 | 경로 |
|---|---|---|
| 삼성생명 `BS_IDENTITY` (2025.2Q·3Q) | 2 | 파서 P-1 **OFS 고정**. 두 분기 모두 항목 1·2·3·4 정상 적재, 항등식 통과 |
| 한화생명 AOCI(4) 결측 | 3 | 파서 P-2 **태그 조건부 채택**(`dart_ElementsOfOtherStockholdersEquity`) |
| 흥국생명 AOCI(4) 결측 | 5 | 위와 동일 |

owner V-3 의 요구("예외 등재로 RED 를 없애지 마라 — 등재하면 다음에 진짜 연결/별도 오선택이
와도 조용히 통과한다")가 **실측으로 성립**한 사례다. 예외 레지스트리는 아카이브된 채로 두었고
새 게이트에는 예외 기구 자체가 없다.

### 잔여 42셀 (전부 YELLOW — 미배포) → parser iter 2
`inbox/parser/20260814T0620Z…ifrs17_bs_delta_after_ofs_rebuild.md`.
- **Tier-2 본표 부분산출 38셀**: AIG 4 · 메트라이프 8 · IBK **12**(2023.4Q 신규) ·
  **KR0075 비엔피파리바카디프 8(신규)** · 하나손 3 · 신한이지 3.
  지문이 iter 1 보다 뚜렷해졌다 — KR0075·IBK 2023.4Q 는 **항목 7(대손준비금) 하나만** 들어와 있다.
  즉 Tier-2 경로가 **준비금 주석은 잡고 재무상태표 본표(`TIER2_ITEM_MAP` 의 40/41/1)를 못 잡는다.**
- **AOCI 태그변형 잔여 4셀**: AIA생명 3 · 아이엠라이프 1 (한화·흥국과 다른 태그일 가능성).
- 값 보정 요청 0건.

### 인지해 둘 것 — census 회사축 (owner 판단 대기)
KR0075 는 (b) 시점엔 "행이 0건이라 census 가 못 보는 2사" 중 하나였는데, 재빌드로 행이 생기자
바로 잡혔다. **행이 아예 없으면 여전히 무신호**이고 현재 그 상태인 회사는 KR1098 카카오페이손해
1사다. 기대그리드(39사×7분기)로 올리면 366셀 + 예외 레지스트리 부활이 필요해 이번엔 미배선.

### 스레드 종결
8/13~8/14 owner 발주 4건을 `inbox/_resolved/` 로 이동 — `20260813T0422Z`(resolved) ·
`20260814T0035Z`(resolved) · `20260814T0216Z`(superseded) · `20260814T0232Z`(resolved).
**validation inbox 는 비었다.**

## 2026-08-14 (b) — `equity_composition` 도메인 게이트 철거, 17BS 정본 = `IFRS17_BS.json`. RED 21 → 0

발주 `inbox/validation/20260814T0232Z…unwire_equity_composition_gate.md`
(직전 `20260814T0216Z…bs_gate_shrink_to_bs_identities.md` 는 그 안에서 대체 선언 → superseded).
같은 날 세 번째 축소 라운드이고, 이번엔 도메인 자체가 내려갔다. **신규 룰 0개.**

### 왜
owner: *"이건 그냥 high-level BS 를 긁으면 거기엔 '기타포괄손익 합계'가 없고, 사실 필요한 건
'기말 AOCI'뿐이라서 굳이 검증할 등식조차 없다."* → 항목 1-49 마스터(`equity_composition.json`)를
아카이브하고 항목 1-5(자산/부채/자본/AOCI/해약환급금준비금)짜리 `IFRS17_BS.json` 한 벌로 간다.
게이트에 남은 RED 21건 중 19건이 **owner 가 요구한 적 없는 축**(AOCI 흐름 분해)의 등식이거나
그 축의 결측이었다.

### 반영
- `validate_data_contract.py` 에서 `check_equity_composition` · `MASTER_FILES["equity_composition"]` ·
  `Env._load_equity_findings` · `Env._equity_is_published` 제거.
- 그 자리에 `MASTER_FILES["IFRS17_BS"]` + `check_ifrs17_bs()`. 룰은 **딱 둘**:
  `BS_IDENTITY`(항목1 == 항목2+항목3, 허용오차 max(1백만원, 0.1%) — 종전 `EQ_BS_IDENTITY` 와 동일) ·
  `BS_CENSUS_MISSING_ITEM`(코어 1·2·3·4). 항목 5·6·7(준비금 3종)은 optional = 무검사.
  자본총계 폐쇄식은 새 마스터에 자본 세부항목이 없어 성립하지 않는다(AOCI 태그 채택 검산은 파서 몫).
- **심각도 결정 방식은 그대로 재사용**: 배포 HTML 이 그 JSON 을 fetch 하면 RED, 아니면 YELLOW.
  지금은 `IFRS17.html` 이 아직 옛 파일을 읽고 있어 17BS 40건이 YELLOW —
  designer 가 repoint 하는 순간 코드 수정 없이 RED 로 승격된다.
- `archive/2026-08_equity_composition/` 신설 + `validate_equity_composition.py` ·
  `data/_gold/equity_census_exceptions.json` · `equity_value_overrides.json` 이동(+README).
  **지우지 않고 옮겼다** — 되살리면 룰 4개(롤포워드·stock-flow·continuity·OCI residual)가 통째로 붙어 온다.
- selftest 3개 추가(`I1 BS_IDENTITY` · `I2 BS_CENSUS_MISSING_ITEM` · `I3 미배포면 YELLOW`).
  이 마스터에 남은 룰이 둘뿐이라 조용히 죽으면 17BS 검사축이 통째로 사라진다. 22/22 → **25/25**.

### 결과
`validate_data_contract.py` **RED 21 → 0**(exit 0), YELLOW 396 → 259.
17BS 실측 40건(전부 YELLOW): Tier-2 부분산출 26 · AOCI 태그변형 12 · 삼성생명 BS 항등식 2
→ `inbox/parser/20260814T0500Z…ifrs17_bs_census_and_identity.md`.

### 기록해 둘 판단 2개
- **삼성생명 2건을 예외 등재하지 않았다.** owner V-3: 등재하면 다음에 진짜 연결/별도 오선택이
  와도 조용히 통과한다. 확인 결과 애초에 등재된 적도 없었다(레지스트리에 KR0069 0건).
  파서 OFS 고정 후 소멸하는지로 판정한다.
- **census 회사축은 못 본다(자인).** 새 census 는 "마스터에 행이 있는 (회사,분기)" 안에서만 돈다 →
  행이 0건인 2사(KR0075·KR1098)는 무신호. 기대 그리드(39사×7분기)로 올리면 366셀이 뜨고 방금
  아카이브한 예외 레지스트리가 다시 필요해져서 이번 라운드에선 붙이지 않고 owner 판단으로 올렸다.

## 2026-08-14 — equity census 코어 축소(owner 범위 정정). RED 182 → 21, 게이트 실차단 전환

발주 `inbox/validation/20260814T0035Z…equity_scope_rollback_core_shrink.md`.
**룰을 하나도 새로 만들지 않았다** — 지우고 낮추는 작업.

### 무엇이 잘못돼 있었나
owner 원 요구는 "high-level 17BS(자산/부채/자본/AOCI)를 OpenDART API 로 빠르게, 가능하면
해약환급금준비금까지 — **안되면 pass**"였는데, 8/13 발주가 항목 10 을 **필수 코어 + 결측=RED** 로
격상시켰다. 그 결과 RED 182건 중 160건이 owner 가 "없으면 넘어가라"고 한 항목의 결측이었다.
**게이트가 요구사항이 아니라 발주 오류를 지키고 있던 상태.**

### 반영
- `CORE_ITEMS = (1, 6, 40, 41)`. `OPTIONAL_ITEMS = (5,10,11,20,29,30)` 은 결측을 셀별 RED 로
  뿌리지 않고 **집계 YELLOW 1건**(`EQ_OPTIONAL_ITEM_ABSENT`, 항목별 셀 수)으로만 남긴다 —
  "탐지는 지우지 말되 강제하지 말 것"의 최소 형태.
- `EQ_PARENT_CHILD_INCOMPLETE` RED → YELLOW.
- `EQ_TIER2_SCOPE_GAP` + `TIER2_CORE_ITEMS` + `load_tiers()` 삭제. Tier-2 가 취소돼 티어 분기가
  의미를 잃었고, 유일한 호출부가 사라진 `load_tiers` 는 고아라 같이 정리했다.
- **Tier-2 15개사 census 예외 등재**(`data/_gold/equity_census_exceptions.json`). 근거는
  `inbox/parser/20260814T0035Z…equity_tier2_stop.md` "XBRL FS 없는 15개사 = 영구 결측 확정",
  회사목록은 사이드카 `universe.tier2_companies`(14) + `tier2_still_missing`(KR1098).
  등재하지 않으면 **채울 경로가 없는 27건이 영구 RED** 로 push 를 막는다. `_excepted()` 가
  `companies` 배열도 받도록 3줄 확장(레지스트리 한 항목으로 15사 표현).

### 배포 판정이 자동으로 뒤집혔다
8/13 에 넣은 "페이지가 이 JSON 을 fetch 하는가"로 심각도를 정하는 배선이 실제로 작동했다 —
IFRS17.html 이 `equity_composition.json` 을 읽기 시작하자 코드 수정 없이 스테이징 YELLOW 강등이
끝나고 **`validate_data_contract.py` RED=21 = push 실차단**이 됐다.

남은 21건은 전부 owner 요구 4항목 자체의 문제다: AOCI(6) 결측 13(한화생명 7·흥국생명 6 —
같은 분기의 1/40/41 은 붙어 있어 account_id 변형 의심) · 롤포워드 6(KB라이프 328,699 /
한화손보 3,198 / DB생명·DB손보 각 2건은 FY 내 상수 = 기초 오선택 계열) · 삼성생명 BS 항등식 2
(DART 원본 캐시 품질 이슈로 파서 종결 → owner 결정 대기). 앞 19건은 파서 발주
`inbox/parser/20260814T0130Z…equity_core4_gaps_after_scope_shrink.md`.

### 그 전환이 드러낸 selftest 오염 (버그 1건 수정)
심각도가 RED 로 올라가자 `--selftest` 가 **0/22** 로 무너졌다. `Env` 가 inject(합성) 모드에서도
`equity_findings` 를 **디스크에서** 읽어, 실제 equity RED 21건이 22개 합성 케이스 전부에 섞여
들어갔기 때문. 마스터 격리 규칙(`wf_by_code` 가 이미 따르던 것)을 equity 에도 적용 —
inject 모드면 `equity_findings=[]`, `equity_published=False`. → **22/22 복구.**
YELLOW 였을 때는 조용히 통과하고 있었다: 심각도 승격이 없었으면 못 찾았을 오염이다.

### 부수 발견 — keep-list 문서 갭(라이브 404 위험)
`pytest tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` FAIL:
IFRS17.html 이 fetch 하는 `equity_composition.json` 이 publishing·designer §1 표에 없다.
keep-list 가 그 표에서 유도되므로 그대로 배포하면 패널이 404 로 빈칸이 된다 →
두 스테이지에 `20260814T0135Z…equity_keeplist_doc_gap.md` 발주. **RED 0 + 이 테스트 통과 전 push 금지.**

---

## 2026-08-13 (b) — 파서 답변 재검증(iter 2): raw 대조 + "무신고 값 정정" 탐지 룰 신설

발주 스레드: `inbox/_resolved/20260813T0600Z…equity_composition_red_findings.md`(파서 답변 후 resolved)
→ 잔여·신규 `inbox/parser/20260813T1330Z…equity_composition_red_round2.md` (iter 2).

### 왜 마스터 대신 raw 를 봤나

파서가 RED 328 → 216 을 보고했다. 마스터만 보면 "항등식이 닫혔다"는 것밖에 확인할 수 없고,
**빌더가 raw 를 고쳐서 내려보내면 모든 항등식이 깨끗하게 닫히면서 게이트를 통과한다**
("맞는 산수·틀린 소스" — 이 저장소의 두 달짜리 false-green 근본원인과 같은 형태).
그래서 사이드카가 인용한 캐시 파일을 직접 열어 Tier-1 **243 (회사,분기) 전수** 재추출·대조했다.

| 파서 주장 | 판정 | 근거 |
|---|---|---|
| P-1 항목8 비지배지분 추가로 폐쇄 | **진짜 raw 값(plug 아님)** | 22셀 `ifrs-full_NoncontrollingInterests` 일치 + **폐쇄식 잔차 − item8 = 0** — 독립 추출값이 항등식을 스스로 닫음 |
| P-6 메리츠 단위붕괴는 raw 그대로 | **파서가 맞다. 내 룰이 틀렸다** | 원문 `478,384,895,270원`/`-432,734,801원`, 2024.2Q=-81,958 로 0 통과 스윙 |
| P-4 NH농협손보 부호 정정 | **값은 맞고 방식이 틀렸다** | 아래 |
| P-2/P-3/P-5 | 해소 확인 | ROLLFORWARD 22→3 · RESIDUAL 19→0 · PARENT_CHILD 28→2 |
| P-7 사이드카 | 규격·커버리지 OK | 마스터↔사이드카 차집합 양방향 0 · universe 선언 = kics 39사 정확히 일치 |

### 핵심 사고 — 빌더가 raw 를 무신고로 고치고 있었다

`build_equity_composition.py:354` 의 `out[30] = out[6]`(|30|=|6| 이고 부호만 다르면 6 의 부호 채택).
전수 대조 결과 실제 변경 셀은 **KR0032 2024.4Q 1건**(raw +261,713 → 마스터 -261,713)이고
**어느 값이 맞느냐는 파서가 맞다**(2025.1Q 필링 기초·2024.3Q BS/SCE 로 재확인). 문제는 방식:

1. owner 발주문 §3 **"6과 30을 같게 만들려고 한쪽을 복사하지 말 것 — 둘의 일치가 검증 항등식이다"** 위반.
2. 일반 규칙이라 앞으로 같은 클래스가 나오면 `EQ_AOCI_STOCK_FLOW_TIE` 가 **영원히 침묵**한다.
   탐지기를 만들게 한 그 사고가 재발하면 못 잡는다.
3. 사이드카는 그 셀을 `Tier-1 / source_file=...` 로 신고 — **그 파일에 없는 값을 그 파일에서 왔다고
   말한다.** provenance 가 형식상 만족되면서 실질은 거짓.

→ **`EQ_MASTER_VS_RAW_DRIFT`(RED)** 신설. 마스터 item 6/29/30 을 인용 캐시의 raw 와 상시 대조하고,
정정은 `data/_gold/equity_value_overrides.json` 에 reason+evidence 로 **신고**해야 인정한다
(정정 금지가 아니라 **조용한** 정정 금지 — `csm_manual_overrides.json` 과 같은 취지).
item20 은 재작성 브리지라 raw 여러 행의 합성이 정상이므로 이 대조에서 제외했다.

### 신설 룰 4개 (전부 `scripts/validate_equity_composition.py`. 게이트는 러너 결과를 흡수하므로 배선 변경 불요)

| rule id | 함수 | 막는 것 | 초회 |
|---|---|---|---|
| `EQ_MASTER_VS_RAW_DRIFT` RED | `check_raw_fidelity` | 무신고 값 정정 | 1 |
| `EQ_OPENING_VS_BS_COMPARATIVE` RED | `check_raw_fidelity` | 기초(20) 행 오선택 — item20 = 그 필링 자신의 BS 전기 | 0 |
| `EQ_BS_IDENTITY` RED | `check_identities` | 자산=부채+자본. **Tier-2 행의 유일한 구조검사**(천원↔백만원 오적용 탐지) | 2 |
| `EQ_DERIVED_UNDECLARED` YELLOW | `check_raw_fidelity` | 역산값이 공시값으로 위장 | 64셀 |

`EQ_OPENING_VS_BS_COMPARATIVE` 는 item20 의 **유일한 독립 앵커**다(그 전까지 item20 은 raw 대조
대상이 아니었다). FY 범위를 데이터로 정했다 — FY2024 88/88 · FY2025 90/90 · FY2026 23/23 전수 일치,
FY2023 은 34/42 불일치이나 **정당**(IFRS17 최초적용: BS 전기 = 재작성 전, SCE 기초 = 재작성 후).
그래서 전환연도만 제외하고 상시 배선. 지금 발화 0건이므로 오탐 없이 P-2 클래스를 영구 봉쇄한다.

### 룰 정정 3건 (내 쪽 결함)

1. **census 가 6사를 통째로 못 보고 있었다.** 회사 축을 `kics_disclosure`(39사)로 옮기고
   `PL_breakdown` 은 분기 케이던스로만 쓴다. PL 에 없는 회사는 연 1회 4Q 기대(사업보고서는 전사가 낸다).
   → **카카오페이손보는 equity 행이 0건인데 RED 가 0건**이었다. 사이드카 universe 선언과 결과는
   같지만(양방향 차집합 0), **검증받는 쪽 산출물에서 모집단을 받지 않는다**는 원칙 때문에 앵커는 kics.
2. **Tier-2 스코프 반영** — `TIER2_CORE_ITEMS=(1,6,10)`. owner 가 Tier-2 범위를 좁혔으므로 5/20/29/30 을
   요구하지 않되, 그 갭을 `EQ_TIER2_SCOPE_GAP` YELLOW **104건**으로 상시 카운트한다(스코프 축소가
   조용한 검증 공백이 되지 않게). `EQ_PARENT_CHILD_INCOMPLETE` 도 Tier-2 제외 → 21→2(이중계상 제거).
3. **`EQ_UNIT_SCALE_JUMP` 오탐 수정** — 단위 오적용은 부호를 바꾸지 않는다. 부호 반전 쌍 skip.
   파서가 요청한 owner_confirmed 등재는 **거절**했다: 탐지기 결함을 owner 승인으로 덮으면 그 다음부터
   진짜 단위오류도 못 잡는다. 레지스트리는 데이터가 맞을 때 쓰는 도구다.

### continuity 면제를 사람에서 데이터로

발주문은 "소급재작성 주장으로 면제 금지 — 면제는 raw 확정 후에만"이다. 그 raw 확정을 게이트 안에서
한다: 기초(20)가 **그 필링 자신의 BS 전기와 일치**하면 발행사 소급정정이 raw 두 곳에서 확인된
것이므로 `EQ_AOCI_CONTINUITY_RESTATED` YELLOW, 아니면 RED 유지. 푸본현대 2025.1Q(-789,340 vs
전기말 -801,322)가 여기 해당 — 자기 필링 BS 전기가 -789,340 으로 일치. 사람이 선언하는 면제 경로를
만들지 않으면서 발주문 요건을 만족한다.

### 결과

**룰 RED 235 → 231** (감소는 내 룰 정정, 증가는 신규 탐지 — 상쇄된 것이라 iter-2 노트에 내역 명시).
잔여 최대 덩어리는 **item10 단독 결측 181건 = XBRL 은 있으나 해약환급금준비금이 주석에만 있는
Tier-1 회사**(owner 발주문 §2 가 예고한 미착수 축. 파서 Tier-2 작업은 XBRL 자체가 없는 15사만 커버).

회귀: `validate_data_contract.py --selftest` **22/22** · `pytest tests/test_deploy_assets.py` **10 passed** ·
라이브 게이트 **RED=0 / YELLOW=605**(미배포 스테이징 유지, push 미차단).

부수 처리: `inbox/_resolved/20260803T0545Z…plausibility_postmortem_anchor_stale.md` 종결 —
`CSM_WATERFALL_PLAUSIBILITY` 분포 독립 재계산(35사·median 0.5599·최대 KR0076 0.9989·발화 0),
**임계값 ×10 유지**하고 PM-2026-07-30 §3 에 앵커 정정 블록 추가(원문은 남김). 일반화: **정정 이력이
있는 셀은 임계값 앵커로 쓰지 않는다.** G2 셀프테스트는 합성 코호트라 회귀 영향 없음(파서 미확인 항목).

---

## 2026-08-13 (a) — `equity_composition` (AOCI + 법정준비금) 검증 룰 신설 + push 게이트 배선

발주: `inbox/validation/20260813T0422Z__owner__MULTI__equity_composition_rules_and_gate.md` (V-1~V-6).
"마스터가 아직 없으니 룰을 먼저 못박아라"는 발주였으나, 같은 날 14:33 파서가 1차 산출(6,255행/24사/11분기)을
올려 **룰 설계 + 실행 검증**을 함께 마쳤다.

### 신설 파일
- `scripts/validate_equity_composition.py` — 룰 본체 한 벌(중복 구현 금지). 단독 실행 RED면 exit 2, `--json`로 findings 덤프.
- `data/_gold/equity_census_exceptions.json` — census 예외 레지스트리. **reason/evidence가 비면 예외로 인정하지 않고
  `EQ_EXCEPTION_REJECTED` RED**를 세운다("아직 안 받아봤다"는 예외 사유가 아니다, 발주문 V-2).

### 게이트 배선 (V-6 "반쪽 배선 방지" 요구 = 경로+함수명 명시)
`scripts/validate_data_contract.py`:
`Env.MASTER_FILES["equity_composition"]`(mtime 감시) · `Env._load_equity_findings`(러너 호출, 러너가 죽으면
조용한 pass가 아니라 `EQ_RULE_RUNNER_FAILED` RED) · `Env._equity_is_published` · `check_equity_composition`
(run_gate 2번째). 룰 결과를 census/as_of/domain/anomaly 버킷으로 옮긴다.

**심각도의 배포 연동.** 아직 어떤 배포 HTML도 `equity_composition.json`을 fetch 하지 않는다 → RED를 YELLOW로
낮추고 사유를 메시지에 남긴다. 디자이너/퍼블리싱이 패널에 물리는 순간 **코드 수정 없이** RED로 승격
(주입 검증: published=True → RED 341 / False → RED 0). 발주문 V-3의 "배포 아티팩트가 되면 배선"과
V-6의 "반드시 이 경로에 걸릴 것"을 동시에 만족시키는 형태이고, 판정 근거가 사람이 넘기는 플래그가 아니라
**페이지가 실제로 읽는지**라 stale 될 수 없다.

### 발주문 정정 1건 — `AOCI_CONTINUITY`의 기준
발주문은 "직전분기 30 == 당분기 20"이었다. 한국 중간 자본변동표는 **FY 누계**라 기초자본 행이 FY 내내 고정이다
(빌더 docstring도 동일 서술). 실측: 직전분기 기준 일치 **0건** / 직전 FY 4Q 기준 일치 **150건**. 그대로 짰으면
전 회사 false RED. → **직전 FY 4Q의 30 == 당 FY의 20**으로 검사하고, 등급은 발주문대로 RED(CSM continuity 동급) 유지.
부수적으로 `EQ_AOCI_OPENING_FY_DRIFT`(FY 내 기초가 분기마다 달라지면 컬럼 오선택) YELLOW 신설.

### census가 스스로 눈 감는 것을 막은 설계 2가지
1. 기대그리드의 회사·분기 축을 **형제 마스터 `PL_breakdown`이 실제로 커버하는 (회사,분기)** 에서 유도한다.
   회사별 공시 케이던스(감사보고서 전용사 = 4Q만)까지 데이터가 들고 있어, "손보는 X 없음" 류 카테고리 단정을 배제한다.
2. 분기 축을 **equity 마스터가 가진 분기로 좁히지 않는다.** 좁히면 통째로 빠진 분기(2023.1Q/2Q)가 기대치에서도
   사라진다. 빠진 분기는 레지스트리 예외로만 제외.

### owner 결정으로 같은 날 종결한 3건 (RED 341 → 328)

1. **`EQ_RESERVE_WITHIN_RE`(5 ≥ 10+12+14) RED → YELLOW flag.** owner 지적대로 이익잉여금 =
   법정준비금 3종 + **미처분이익잉여금**이고 그 잔여가 음수면 준비금 합이 총액을 정당하게 넘는다
   (해약환급금준비금은 손실 중에도 법정 강제적립). 항등식이 아니었다 — 발화 13건도 자본체력 약한
   2사에 몰려 있었다(에이비엘 11 = 이익잉여금 결손 △218,178 / 롯데손보 2 = 미처분 △5,892·△18,407).
   탐지는 유지하되 미처분 잔여를 메시지에 실어 **배당가능이익 소진 신호**로 쓴다.
   → 룰을 데이터에 맞춰 깎은 게 아니라, **부등식이 회계적으로 성립하지 않았던 케이스**다.
2. **케이디비생명 자본잠식 3분기 owner 확인** → `equity_census_exceptions.json` `owner_confirmed`
   등재 + `SUPPRESSIBLE`(flag 성 룰) 한정 억제. census/항등식 RED 는 이 경로로 지울 수 없다.
3. **AOCI ↔ K-ICS 가용자본 방향성 비교 = 미구현 종결**(owner: AOCI 는 IFRS17 개념). 사유를
   `check_cross_master` docstring 에 남겨 "빠뜨린 것"으로 오해되지 않게 했다.

### 초회 실행 결과 — RED 341 (전량 파서 라우팅, 값 보정 없음)
`inbox/parser/20260813T0600Z__validation__MULTI__equity_composition_red_findings.md` P-1~P-7.
대표 진단 2건: ① 자본총계 폐쇄 실패 22건이 **CFS 기준 2사(메리츠·삼성생명) 11분기 전부** = 비지배지분 미포착
(항목 8 신설 요청) ② 롤포워드 22건이 2023.3Q/4Q 집중 + 회사별 차이가 FY 내 **상수** = 흐름이 아니라 FY2023 기초
한 값 오선택(IFRS17 최초적용 재작성 전/후 두 줄).

---

## 2026-08-03 (c) — UH-3 end-state: provenance 사이드카 **부재 = RED** 전환

### V23 — `MISSING_PROVENANCE_SIDECAR` YELLOW → RED (UH-3 종결, 2026-07-21부터 미완이던 축)

**전환 근거 = 선행조건 충족 확인.** UH-3는 2026-07-21에 "notes로 조용히 통과"를 **집계되는
YELLOW**로만 승격한 상태였다(그때 RED로 올리면 미발행 마스터 4종이 전부 red-out돼 push가 영구
차단). 오늘 CHECK 2 대상 4종이 **전부 발행 완료**됨을 실측 확인:

| 마스터 | 사이드카 | 발행 주체 |
|---|---|---|
| `forward_capital` · `tier1_utilization` · `tier2_utilization` | ✅ 루트 3개 | publishing `faa34cd` → 2026-08-03 `scripts/emit_capsec_provenance.py`로 **도출식 전환**(V21) |
| `sensitivity_heatmap` | ✅ `data/dart/viz/sensitivity_heatmap_provenance.json` | parser `scripts/emit_sensitivity_provenance.py` (UH-3 잔여 1건 해소) |

라이브 `MISSING_PROVENANCE_SIDECAR` YELLOW **1 → 0** → `check_as_of._fallback_note`를
**RED**로 승격. 이제 부재는 "아직 미발행(정상)"이 아니라 **발행 경로가 씻겨나갔다는 신호**다.
parser의 emitter 독스트링도 같은 계약을 명시하고 있었다("once this sidecar exists, CHECK 2 flips
… no-sidecar=RED") — 상류가 이미 통보받은 전환이다.

**Phase-1 추론 블록은 지우지 않았다.** 코드 주석의 원래 end-state는 "fallback 삭제"였지만, 그
분기가 이제 RED라 **통과 경로가 아니고**, 무엇이 어긋났는지(stale quarter / 결측 meta) 진단을 함께
보여주는 값이 있다. 삭제는 작동하는 검사를 버리는 쪽이라 채택하지 않았다(surgical 원칙).

**검증.**

| 항목 | 결과 |
|---|---|
| 라이브 게이트 | CHECK 2 **RED=0 유지** · 총 RED **13**(전부 기존 `CAPSEC_COVERAGE_REGRESSION`) = 전환에 따른 신규 RED·오탐 **0** |
| self-test | **21 → 22/22 PASS**. baseline에 유효 사이드카 4종 주입(`base_sidecars()`)해야 clean이 성립하도록 fixture 갱신 |
| 신규 케이스 **C3** | 사이드카 1종(tier1) 제거 → RED 1건만 방출 |
| 이빨 검증 | `GateResult.add`를 가로채 severity를 YELLOW로 **강등**하면 C3 미검출 FAIL = 판정이 실제로 일어남 |
| 부수 fixture 정정 | `f_stale_as_of`는 사이드카가 낡은 기준일을 **정직하게 선언**하는 형태로 바꿔 STALE_AS_OF만 남김(사이드카 present면 index miss로 MISSING_PROVENANCE가 먼저 터짐). `f_source_id_lineage_mismatch`는 나머지 3종을 유효하게 유지(결함 1개 원칙). evidence 계보 키를 선언 소스와 맞춰 `FSC_BONDS → DART` |

**잔여 = UH-8 신규.** `kics_rate_sensitivity`는 `MASTER_FILES`에 있으나 **CHECK 2 검사 대상이
아니다**(사이드카 없음). 값은 `data/_derived/kics_rate_sensitivity_validation.json`이 보지만
**소스 신선도는 아무도 안 본다** — UH-3가 닫은 것과 같은 부류. 발행 선행 발주
`inbox/parser/20260803T0520Z__validation__MULTI__rate_sensitivity_provenance_sidecar.md`
(lane: kics), 발행 후 CHECK 2 2a(iv) 배선. **발행 전 배선 금지**(즉시 red-out) — UH-3에서 검증된 순서.

---

## 2026-08-03 (b) — 자본성증권 **커버리지 census** 신설 (inbox 1건 드레인)

### V22 — `CAPSEC_COVERAGE_REGRESSION` 신설 (owner `20260803T0310Z`, V21의 나머지 절반)

**무엇이 통과했나.** V21이 "틀린 소스라고 **말하는 것**"을 막은 직후에도 게이트 RED=0이었다 —
**소스가 통째로 비어도 통과**했기 때문. `20260803T0055Z`로 채권 원천이 FSC → DART per-bond로 바뀌면서
DART FY2025 annual raw가 없는 회사의 채권이 통째로 빠졌고, 상환 차감이 사라져 비율이 **낙관 방향으로**
틀렸다: KR0050 하나손해 1,000억→0 (2030 124.47%→146.09%), KR0076 아이엠라이프 2,700억→0
(93.65%→**152.12%**, 권고선 130% 아래→위). 원인은 `bond_coverage`가 **"스캔 후 무발행"과 "소스에 아예
없음"을 한 값(`no_bonds_in_dart`)으로 뭉갠 것** — 구분이 안 되니 룰이 성립할 수 없었다.
`feedback_coverage_census_mandatory`의 사각.

**조치 (`scripts/validate_data_contract.py` `check_census` 1e).**
- **`CAPSEC_COVERAGE_REGRESSION`(RED)** — 축은 git diff가 아니라 **선언된 per-bond 소스 안의 회사 존재
  여부**(git 없이 되는 축이어야 1차 판정이 된다). 소스에 레코드 없음 = RED(미검증) / 레코드 있고 해당
  슬라이스 잔액 0 = **통과**(정당한 무발행) / 잔액>0인데 마스터 0 = RED(어댑터 drop).
  **라벨을 믿지 않는다** — 마스터의 `bond_coverage`를 읽지 않고 `index_bond_source()`가 선언된 소스
  파일을 직접 읽어 도출(DART/FSC 2계보 스키마). 모집단 하드코딩 없음 = 마스터가 발행한 행이 대상(self-census).
- **`CAPSEC_SOURCE_UNRESOLVED`(RED)** — 마스터가 행을 발행하는데 소스 선언이 없으면 검사가 **빈 껍데기**가
  된다(2c가 겪은 실패 유형). 축 소실 = 통과 아님.
- **`CAPSEC_AMOUNT_MISMATCH`(YELLOW)** — 0은 아닌 금액 불일치(`max(1억,1%)`). 라이브 0건 → 관찰기.
- **`CAPSEC_COVERAGE_DROP_VS_PRIOR`(YELLOW)** — 보조축(그물). 직전 `output/kics_forward_capital/<stamp>`
  대비 회사별 >0→0 후퇴 또는 전사 20% 급감. 같은 버그로 두 번 생성되면 눈이 머는 축이라 **1차 판정에 안 씀**.
- 오탐 억제: 슬라이스별 자기검열(신종만 발행한 회사의 후순위 0은 대상 아님) + tier 마스터는 소진율
  분자(신규분)가 아니라 **경과조치 면제분까지 더한 총액**을 존재 신호로 사용.
- **`bond_coverage` 3-way**(`forward_capital_simulation.py::_bond_coverage`, 배포 에셋 **추가만**):
  `dart_listed` / `no_bonds_in_dart` / **`absent_in_source`**. 재생성 diff = 15행 라벨 + KR0069
  confidence 사유 1건, **수치 무변**. 같이 발견: `compute_confidence`의 no-bond 지름길 리터럴이
  `no_bonds_in_fsc`로 남아 rename 이후 **죽어 있었다** → 복구하되 `absent_in_source`에는 미적용
  (스캔도 안 한 회사에 "reconcile 할 게 없으니 high"는 이 사건의 낙관 주장 그 자체).

**mutation 증명.** 배선 전 라이브 RED **0** → 배선 후 **RED=15**(KR0050·KR0076 포함, push BLOCKED).
selftest **16 → 21/21 PASS**(H1 absent·H2 어댑터 drop·H3 축 소실·H4 그물·H5 금액불일치).
이빨 검증: `_capsec_coverage_findings`를 monkeypatch로 죽이면 H1~H5 전부 미검출 FAIL(21→16).
`pytest tests/test_deploy_assets.py` 9 passed.

**RED 15건은 exception으로 닫지 않았다**(owner 완료조건 #3) — raw 부재가 원인이므로 정상 경로는
raw 도착 → 재추출 → 자연 소멸이고 그때까지 push가 막히는 것이 의도된 동작(`feedback_red_blocks_push`).
발주: parser `20260803T0400Z`(raw 있는 12사 = 추출 또는 무발행 빈 레코드 명시) ·
downloader `20260803T0405Z`(raw 없는 3사: KR0049 악사·KR1010 교보라플·KR0150 서울보증).
7사는 `data/bonds/_census_fy2025.json`에 `HAVE_BONDS: false` 스캔 기록이 있으나 **그 census는 사이드카가
선언한 소스가 아니다** → 정당한 0의 근거는 소스의 빈 레코드(`bonds: []`)로 남긴다는 계약(`20260803T0123Z`)에
따라 RED 유지. 상세 5칸: `docs/postmortems/PM-2026-08-03_capsec_provenance_label_mismatch.md` **§6**.

---

## 2026-08-03 — provenance 라벨 계보 검사 + CSM 상대규모 plausibility (inbox 2건 드레인)

### V21 — `SOURCE_ID_LINEAGE_MISMATCH` 신설 (owner `20260803T0056Z`, false-green 해소)

**무엇이 통과했나.** `validate_data_contract.py`가 capital-securities 3마스터
(`forward_capital`·`tier1_utilization`·`tier2_utilization`)에 `source_id == "FSC_BONDS"`를
**하드코딩 요구**. 그런데 tier1/tier2는 2026-06-20부터 DART가 원천
(`wire_capital_securities_to_utilization.py` → `data/bonds/capital_securities_fy2025.json`).
사이드카는 하드코딩 요구를 만족시키려고 **DART 파일에 FSC 라벨**을 달았고, 게이트는 그 거짓 주장을
"검증"해 **RED=0으로 통과**시켰다. PM-2026-06-16 "맞는 산수·틀린 소스"의 provenance 축 변종.

**조치.**
- **`source_id_for_lineage()` + `_SOURCE_LINEAGE`** — 경로 접두사 → 원천 매핑
  (`normalized/**`·`raw/**`→FSC_BONDS / `capital_securities_*`·`disclosure/**`·`data/dart/**`→DART).
  선언 라벨 ≠ 계보면 **RED `SOURCE_ID_LINEAGE_MISMATCH`**. **계보 미등록 경로도 RED**(검증 불가 = 통과 아님).
  enum 확대(`{FSC,DART}` 둘 다 허용)를 거부한 이유 = 아무 라벨이나 통과해 검증력 소멸.
- `effective_filtered == true` 요구 **유지**하되 `source_id` 검사와 **분리**(어느 쪽이 깨졌는지 구분).
- **effective 증거 재조준**: 종전엔 FSC 스냅샷 **한 파일**만 봐서, tier1/tier2가 DART로 옮겨간 뒤
  **서빙되는 DART per-bond의 도넛 가드는 아무도 검사하지 않았다.** `capsec_sources_in_use()`가
  사이드카에서 `{계보: {source_file}}`를 뽑고 **계보마다 그 선언된 파일**을 검사(글롭·최신stamp 추측 제거
  = 검사파일 == 서빙파일). DART 2축 신설: (i) 아티팩트 as-of에 콜 도래·outstanding>0이면
  `past_call_outstanding: true` 필수, (ii) 스냅샷~마스터 as-of 구간 콜 도래분 — 후순위는 `amort()`가
  0으로 떨어뜨리나 **신종은 tier1 분자에 무조건 합산**되므로 이 검사만이 막는다. 라이브 누출 0.
- **`scripts/emit_capsec_provenance.py` 신설** — 루트 사이드카 3개를 **게이트와 같은 함수로 도출**
  (하드코딩 금지). `--check`는 drift 시 exit 2. 손타이핑 사이드카는 리빌드에 무방비였다.
- **`tests/test_deploy_assets.py::test_capsec_provenance_source_id_matches_lineage`** 신규 — 라벨/계보
  일치 + `--check` 무drift 기계검사. → **9 passed**.

**mutation 증명 (owner 완료조건 #2).** 배선 전 라이브 RED **0** → 배선 후(정정 전) RED **2**
(tier1·tier2) → 사이드카 재발행 후 **0**. `source_id_for_lineage` 무력화 시 selftest G1 **FAIL**.

**as-of 정본 확정 (owner §4).** 사이드카 `as_of_date` = **2026-03-31 (2026.1Q)** 정본
(manifest `baseline_quarter`·tier doc `quarter`·`wire_…py AS_OF` 3중 일치). per-bond `as_of: 2025-12-31`은
**다른 축**(채권 스냅샷 기준일). `baseline_2025_4Q` 키는 **stale 이름·값은 2026.1Q** →
**UH-7**로 publishing 발주(`inbox/publishing/20260803T0210Z`, `K-ICS.html`이 1곳에서 읽어 동시 변경 필요).

**진단 1건 정정.** owner §3의 "파일 없음 = 그냥 통과"는 사실과 달랐다 — 그 경로는 이미
`MISSING_EFFECTIVE_LIST` RED를 방출한다. 실제 사각은 **틀린 파일(FSC)을 보고 있었다**는 쪽.

### V20 — `CSM_WATERFALL_PLAUSIBILITY` 신설 (parser `20260730T0040Z`, UH-6 해소)

`_csm_magnitude_implausible()` → `check_census` **1d**. 판정식 `기말CSM ÷ item1 지급여력금액`
(회사별 최신 분기, KR코드 조인) > `median × 10`. severity **YELLOW**(관찰 1~2 릴리스 → RED).

**임계값 parser 초안 ×20 → ×10 조정.** 초안 근거(KR0075 r=153.01 / 차순위 3.49)는 **정정 전** 값.
정정 후 라이브 36사 분포 = median **0.563** · 최대 **1.530**(KR0075, ×2.7) → ×20(r>11.3)은 라이브
최대의 7.4배 여유로 **중간규모사의 ×10 단위오류(r 0.563→5.63)를 놓친다**. ×10은 3.7배 여유 유지 +
그 부류 포착. 100× 사고는 ×273이라 어느 쪽이든 발화. **라이브 발화 0건(오탐 0).**

오탐 억제 (a) K-ICS 미공시사 skip · (b) 표본<10 skip · (c) 상한만 + **(d) 신규: 지급여력금액 ≤ 0 skip**
(자본잠식사 예별손해 item1=△1,090 — 비율 무의미, 규모 이상치는 CHECK 5 generic scan 소관).

회귀: `_data_contract_selftest.py` **G2**(항등식은 닫히나 규모만 비정상인 합성 케이스) + selftest에
**YELLOW 기대 축** 추가. 부수 정정: selftest가 `wf_by_code`를 **디스크 실데이터**에서 읽던 것을 inject
격리로 전환(합성 케이스 오염, pre-existing).

### 상태

`--selftest` **14 → 16/16 PASS**(G1·G2 둘 다 이빨 검증 통과) · 게이트 **RED=0** YELLOW=210(기존 generic
anomaly 후보, 비차단) · `pytest tests/test_deploy_assets.py` **9 passed** · inbox validation **비었음**.
PM-2026-08-03 신규 · PM-2026-07-30 `open → closed` · README UH-6 해소 / UH-7 신규.

**잔여(절반-경화 재확인).** `prepush_check.py:23`은 `validate_data_contract`·`triage_anomaly_candidates`만
import — `validate_kics_disclosure.py`를 **호출하지 않는다.** 이번 룰 2종은 push 게이트 배선이라 무관하지만,
K-ICS 게이트 전용 룰(현 documented RED 8건 포함)은 여전히 push를 못 막는다. 체인 추가는 push를 즉시
차단하므로 **owner 결정 사항**(임의 변경 안 함).

---

## 2026-07-21 (3차) — UH-5 종결 (요구자본 부모 COPY 룰) + UH-3/UH-4 배선

owner 승인. V19 미배선(UH) 잔여 정리 라운드.

### UH-4 해소 + UH-3 부분강화 (commit `647c65c`)
- **UH-4**: `scripts/_data_contract_selftest.py` 신설 — `Env(inject=)` 합성 mutation suite **14/14 PASS**
  (기존 spec §5 회귀 + 1b(iv) lift 5종 F1~F5 회귀 보호). `--selftest` ModuleNotFoundError 해소
  (end-to-end 14/14). **이빨 검증**: 룰 monkeypatch로 죽이면 해당 케이스 미검출→FAIL 확인.
- **UH-3**: sidecar 부재가 `notes`(비집계)로 조용히 통과하던 것을 집계되는 YELLOW
  `MISSING_PROVENANCE_SIDECAR`(현 4건: sensitivity_heatmap·forward_capital·tier1/tier2)로 승격.
  RED 전환은 상류 발행 후(지금 RED면 미발행 마스터 red-out으로 push 영구차단). 발행 발주 완료.

### UH-5 종결 = premise-refined (owner Socratic 지적으로 확정)
owner: "subrisk만 달라야 하는 게 맞긴 한데, subrisk가 다르면 상위 risk도 당연히 달라야 하지 않나?"
→ **맞고, 기존 `_transition_mmult_after`(부모후=sqrt(subrisks후·상관행렬))가 이미 강제.**

- **선행조건 확인**: FSS 2023-03-20 붙임-1(`trend20230320_3.pdf` p6, 회사별 경과조치 종류)을 좌표추출
  전수 복원(총계 검증 **4/19/12/8** 일치) → `_TRANSITION_KIND` registry 등재
  (`validate_kics_disclosure.py`, 소비 룰 없는 문서 registry).
- **전제 falsify**: "TAC형(가용자본만·요구자본 무영향) 회사" = **0사**. 가용자본(AC) 경과조치 신청은
  4사(케이디비·IBK연금·하나생명·푸본현대)뿐이고 이 4사 전부 요구자본 보험리스크(IR)도 신청.
  elective 18사 전원이 요구자본 경과조치사.
- **실측 78 "부모후=전" 셀 분류**: **A(subrisk후≠전인데 부모후=전=모순) 0** [mmult가 이미 강제] ·
  **C(item14후 다름·부모후=전) 52 전부 item19(시장위험)** [한화손·롯데손·악사·처브=주식/금리 미신청사
  정당 / 농협손·DB생명·에이비엘=신청사이나 금리·주식 경과조치 조건부(K-ICS리스크 60%>RBC일 때만
  발동)라 실효과 0 가능+내부정합 통과] · **D(subrisk후 부재) 26** [census 소관]. **진짜 미검출 0.**
- **결론**: 부모 COPY 룰은 item17=mmult 중복·item19=오탐 52·진짜미검출 0 → **신설 불요.**
  headline(item27/28)은 `_transition_ratio_after_capture`가 18사 전원 검증 중. postmortem README 3차
  종결 기록. 게이트 무회귀: push 게이트 **RED=0** 유지, K-ICS RED=12 전부 documented(KR0079 8_life·
  KR0087 동양 2023.2Q·KR0097 하나생명 2024.2Q 이미지전용).

---

## 2026-07-21 — 사고 포스트모템 관행 도입 + 기존 4건 소급 (owner `20260721T0233Z`)

owner: "포스트모템이 게이트 룰로 종결되지 않으면 같은 부류가 다시 통과한다." 5칸 미충족 시 close 불가인
blameless 포스트모템 관행 신설.

- **구현형태 = 로컬 스킬 채택** (`.claude/skills/incident-postmortem/SKILL.md`). 외부 서드파티 스킬
  미채택 사유: 종결 5칸이 이 저장소의 **게이트 파일명·registry 변수명·display-scope·두 게이트 분리**를
  직접 지목해야 강제력이 생기는데 범용 포스트모템 스킬로는 불가. 기존 로컬스킬(`kics-parser`·
  `ifrs17-parser`) 패턴 존재 + 금융데이터.
- **정본**: `docs/postmortems/README.md`(관행·종결조건·색인·UH표) + `_TEMPLATE.md`.
  스테이지 프롬프트 `docs/agents/claude-agent-validation.md` **§5.1 신설**에서 링크.
- **소급 4건**: PM-2026-06-16 두 달 글리치(**closed**, push 게이트 배선) · PM-2026-07-07 적용후 전면
  미검증(**open**) · PM-2026-07-08 V17 가짜복사(**open**) · PM-2026-07-15 부모 census(**closed**, 양쪽 배선).

### 🔴 소급의 실질 산출물 — 미배선(UH) 4건

- **UH-1 (P1, 최대 발견)**: 적용후 검증 7종(`_transition_ratio_after_capture`·`_transition_mmult_after`·
  `_transition_identities_after`·`_parent_present_child_incomplete_after`·`_diversification_negative`·
  `_item12_equals_item1`·`_ratio_series_spikes`)이 **push 게이트에 미배선**. `validate_data_contract.py`의
  `check_census`는 `kics_json_rules.run_validation`의 rule-based 결과만 lift하고, **`prepush_check.py`는
  `validate_kics_disclosure.py`를 import·실행하지 않음** → 07-07·V17 사고 대응 룰 전부가 push를 못 막는다.
  사고 4건 중 3건이 여기 걸림.
- **UH-2 (P1)**: `scripts/validate_data_contract.py`가 **git untracked**(머신-로컬) → push 게이트 배선
  (V18 부모 census 포함)이 git에 없음.
- **UH-3 (P2)**: provenance Phase-2 end-state 미강제 — sidecar 존재 3종(kics_disclosure·CSM_waterfall·
  PL_breakdown)만 strict, 없는 마스터는 Phase-1 추론 fallback으로 통과.
- **UH-4 (P2)**: `validate_data_contract.py --selftest`가 `_data_contract_selftest` 부재로 실행 불가.

### ✅ 같은 날 UH-1·UH-2 배선 완료 (owner 승인 "나머지는 추천대로 배선 고고")

- **UH-1**: 적용후 검증 7종을 `validate_data_contract.py` `check_census` **1b(iv)** 로 lift
  (display 7분기 scope). 6종 RED(`TRANSITION_AFTER_{COPY|MISSING|LOWER|AMT_MISMATCH}` ·
  `TRANSITION_AFTER_MMULT_MISMATCH` · `TRANSITION_AFTER_IDENTITY` · `POST_TRANSITION_CHILD_MISSING` ·
  `DIVERSIFICATION_NEGATIVE` · `ITEM12_EQUALS_ITEM1`) + `RATIO_SERIES_SPIKE`만 YELLOW(휴리스틱이라
  단독 push 차단 금지 — 원 룰 정의 준수). **주입 테스트로 방출 경로 검증**: display-scope를 2023.1~3Q로
  임시 확장 시 baseline RED 0 → lifted RED 4건(예별손해 3분기·IBK연금) 방출 확인. 배선 후 실 게이트는
  **RED=0 유지**(현 findings 전부 non-display 2023.x).
- **UH-2**: push 게이트 체인 3종(`validate_data_contract.py`·`prepush_check.py`·
  `triage_anomaly_candidates.py`) **git 등재**. gitignore가 아니라 단순 미추가였음(scripts/ 163개 이미
  tracked, 나머지 의존성도 전부 tracked였음).
- **도메인 경계 명문화(owner 지적)**: 경과조치는 **K-ICS 전용**(적용전/적용후 이중공시). IFRS17엔
  대응 개념 없음 — 전환방법(수정소급/공정가치)은 도입시점 측정방법이지 이중컬럼이 아니라 **복사할 짝
  자체가 없음** → `TRANSITION_AFTER_*` IFRS17 유사룰 금지. 상위 패턴("presence만 검사→세탁")만 도메인
  무관이며 IFRS17은 기존 `CSM_WATERFALL_PLAUSIBILITY`/`IMPOSSIBLE_ZERO_*`가 담당. README·SKILL 기록.
- **PM-2026-07-07·PM-2026-07-08 → `closed`** (3번 칸 충족). 잔여 P2: UH-3·UH-4·UH-5(신규, 요구자본
  COPY 검사 부재).

---

## 2026-07-16 — 부모 census parser fill 적대검증 (worklist `20260715T0835Z` resolved)

parser가 continuity 워크리스트 답변(fill: 삼성생명 2025.1Q·동양생명 4분기·한화생명 2025.2Q/3Q·흥국생명
17~21·하나생명 18~23). validation 재검증:
- **미러fill(후=전) 정당성 PASS** (V17 가짜복사 재발 아님): 삼성생명(KR0069)·동양생명(KR0087)·한화생명
  (KR0068)은 `_TRANSITION_APPLIERS` 18사(elective)에 없는 **공통(TFI)경과조치사** → 요구자본(item15~21)
  후=전이 도메인상 정답(TFI는 가용자본만 영향). 적대검증: item1(가용자본)후는 2025.2Q에 실효과(Δ+825~1188)
  로 ≠전인데 item15~21후=전(±1억 반올림뿐) = 공통경과조치 정합 확인. mirror=정답.
- **무회귀**: `_transition_ratio_after_capture`(COPY/LOWER/AMT_MISMATCH)·mmult·항등식·분산효과음수 전부
  0 유지. continuity break **117→62셀**, **push 게이트 census RED 47→4**.
- **잔여 2건 owner escalate**(raw 도출불가, `_POST_PARENT_NOT_DISCLOSED` 결정 대기):
  흥국생명 2024.4Q [15,16,22](image PDF+TIR/TER 다중경과 R4 재현불가) · 하나생명 2024.4Q [16](비표준
  감사보고서 공시, item17후=1757.32가 raw page 2001.90 불일치=partial-mmult 아티팩트 의심 → item16 파생값
  불신). validation 자체 waiver 안 함 = owner 택일(exemption 등재 vs 재추출).
- non-display 비차단 워크리스트: 코리안리 3분기·악사·처브·IBK 2023.2Q 등(git-purge raw, 저우선).

---

## 2026-07-15 — 적용후 요구자본 **부모** census blind spot (owner `20260715T0801Z`)

owner: 2026.1Q push 게이트가 통과했으나 5적용사(한화생명·교보·하나·롯데손해·농협) 요구자본 부모 항목
`값_적용후`가 결측인 채 통과(false-green). 근본원인: 07-12 census(`_parent_present_child_incomplete_after`)는
**부모후 present일 때만** 자식 결측을 봐서 **부모(15~21) 통째 결측이면 census/identity/mmult 전부 skip**.

- **신설 `_post_transition_parent_census`** (scripts/validate_kics_disclosure.py): 적용후를 공시하는 회사의
  요구자본 부모 continuity census. (회사,항목) 값_적용후가 **직전 공시분기 present인데 당 분기 결측**이고
  이후 재출현(SANDWICHED)/최신분기(TRAILING)이면 = 추출갭 → RED. 도입초 onset·항구적 중단은 flag 안 함.
  - 대상: 15기본요구자본·16분산효과·17생명장기·18일반손해·19시장·20신용·21운영 = **코어(RED)**; 22법인세조정·
    23기타요구자본 = 조정(코어 break 동반 시만 RED, 단독은 review — 종속회사/법인세 legit-absent 흔함).
  - **적용사 판정 = continuity 자체**(별도 seed 없음) → `_TRANSITION_APPLIERS` 18사(elective)에 없던 공통
    경과조치사 **한화생명(KR0068)·삼성생명(KR0069)·코리안리(KR1000)**도 포착. 한화생명이 기존 검사에서
    빠지던(18사 하드코딩) 근본원인 해소.
  - 항목 4/12/13(구조적 적용후 미공시=NO_POST_TRANSITION_DISCLOSURE)은 census 대상 원천제외 → 구조적은
    flag 안 됨(요청3). 면제 registry `_POST_PARENT_NOT_DISCLOSED`=비어있음(owner "오면제 금지", waiver=owner 권한).
- **양쪽 배선**: (1) `validate_kics_disclosure.py` 전분기 리포트+exit2 (parser 워크리스트),
  (2) `validate_data_contract.py` `check_census` 1b(iii) **display 분기만 차단**(다른 census와 동일 scope)
  = "push 게이트가 통과"의 정정 지점. 두 스크립트 compile OK, 기존검사(mmult/항등식/하위census/core RED) 무회귀.
- **검증**: 병행 parser 세션이 2026.1Q 5사 15~23 값_적용후 전량 UPSERT(mtime 17:32) → 2026.1Q census RED=0 +
  산술 후검사 0 통과 = **게이트가 갭→RED, fill→통과** 설계대로 작동 확인.
- **잔존 push 차단 census RED=47 (8 회사·분기, historical display)** → parser 발주 `20260715T0835Z`:
  🆕 삼성생명 2025.1Q·흥국생명 2024.4Q(진짜 추출갭, 매분기 공시 중 1분기 유실) · owner 2차 한화생명 2025.2Q/3Q ·
  raw확인 동양생명 3분기·하나생명 2024.4Q(구조적이면 owner exemption).
- **건2 `8_post` dynamic tol (publishing `20260712T0219Z`)**: 이미 07-12 코드반영 확인(KR1098 2023.4Q 8_post
  =YELLOW diff -92.82 tol내), `7_post` 룰 부재 → 추가 조치 불요. resolved.

---

## 2026-07-12 (4) — 전수 헤드라인 대조 + 파서 IBK fix 반려

owner "같은 혼합 다른 회사도 헤드라인 대조 전수검증 + 파서작업 확인". 18적용사×전분기 raw 주요경영지표
'경과조치 후' vs 데이터 item27후 대조(anchor=경과조치'전' 일치행, 오탐0):
- **110건 정합 · 불일치 3건(예별손해 KR0004 2023.1Q/2Q/3Q) · 119건 자동파싱불가(포맷/이미지)**.
- **예별손해 3건 = IBK와 동형 혼합**: item27후가 ②표 단독값(74.67/72.21/58.33)인데 헤드라인 정본은
  82.56/79.96/64.50. 다중경과조치(①②③) 결합 최종 아닌 개별표값 오추출.
- **파서 IBK fix(20260712T0430Z) 반려**: item1후를 ①TAC표값 8241.63으로 넣어 **공통(TFI) 경과조치
  누락**(raw: 공통 605,115→697,391 +92,276 빠짐). 결합 정답 = 605,115+공통+TAC = 9164.38(원래값이
  맞았음). parser item14후=4657.6은 ②③결합(≈5179)보다 낮아 불가능. 정정값 발주(item1후 9164.38·
  item14후 5179.08·item3후 8869.48·item28후 5.69, item2후·item27후는 parser 맞음).
- 케이디비 2025.4Q 헤드라인 대조 플래그 = 내 파서 오탐(점선줄), 데이터 205.7 정상.
- 발주 `20260712T0700Z__…__headline_reconcile_ibk_yebyeol.md`(IBK 반려+예별3건+119 per-company 재조정).
- 대조 스크립트 `scratchpad/headline_crosscheck2.py`(anchor, 오탐0). core RED 13·분산효과음수 1 불변.

## 2026-07-12 (3) — 파서 census-fill 적대검증 + 분산효과 부호 sanity 신설

parser가 322→2 fill(commit a797681) 완료 주장 → owner "존나 적대적으로 검증". 독립 재검증:
- **파서 fill 견고 확인**: item18=0이월 0오류·시장하위 carry 0불일치·신용/운영 carry✓·mmult 정합·
  한화손해 item19후=전(raw ②표 "시장 461,015→461,015 불변" 확인, 준비금경과라 시장무관, 13분기 일관).
  2 exemption(롯데·교보 2026.1Q)도 raw 정독→②③표 진짜 부재 확인, `_AFTER_SUBRISK_NOT_DISCLOSED` 등재.
- **적대 스윕이 파서 무관 기존 오류 1건 적발 — IBK연금 2023.2Q**: 적용후가 ②표(기본요구자본 677,870,
  시장 불변)와 ③표(시장 281,235)를 **혼합** → Σ(위험액)<기준금액 → **분산효과 -246.66(음수)**. item27후
  135.19도 헤드라인 요약표 176.95와 불일치. R6 항등식·item27체크·mmult가 산술만 봐서 전부 통과시킴.
- **신설 `_diversification_negative`**(전·후, 전체회사, RED blocking): item16<0 또는 Σ(17~21)<item15.
  전 회사 스캔 결과 음수 1건(IBK)뿐 = 고립. 게이트 배선(exit-code) 완료.
- parser 발주 `20260712T0430Z__…__ibk_multitransition_mixed.md`(②③ 결합 재도출 or item27후 정정+세부 None).
- **현 게이트: census 0·mmult 0·항등식 0·분산효과음수 1(IBK) 정상차단**. core RED 13 불변.

## 2026-07-12 (2) — 적용후 요구자본 census 신설 (blind spot 정정)

**앞 항목의 "gate-clear"는 조기판정이었음.** owner가 아이엠라이프 2025.4Q 적용후 신용·분산효과 결측을
지적 → 적용후 게이트가 mmult(item17/19 leaf)만 보고 **요구자본 구성(15→16~21) census가 없었음**을
확인. 적용후 항등식(R6)은 결측셀을 skip → 부분충전이 양쪽으로 샘.

- **신설 `_parent_present_child_incomplete_after`**(적용전 census 미러): 부모후 present인데 '적용전
  present&material' 자식후 결측=RED(blocking). 부모맵 `{15:(16~21),17:(29~35),19:(36~40)}`. 게이트
  exit-code·print 배선.
- **적발 322 항목셀**(149 부모·분기): DERIVE 96(분산효과 파생)·CARRY 206(신용/운영/시장하위 후=전
  carry-forward)·EXTRACT 20(raw 재추출, 14 회사·분기). 분류·근거 `data/_derived/after_census_gaps.json`.
- parser 발주 `inbox/parser/20260712T0230Z__...__after_requirement_census_322cells.md`.
- **현 게이트: 적용후 census 149 RED로 정상 차단**(exit 2). parser fill 후 0 확인 → 재publish.
- carry-forward 안전성 검증: 신용 후=전 217/218·운영 213/213·분산효과 항등식 119/119 성립.

## 2026-07-12 (1) — 적용후 전수검증 완결 + publish gate-clear [정정됨 → (2) 참조]

owner 지시 "모든 검증룰은 적용전후 동일 적용" 대응. prepush RED=0 달성(publish 가능).

- **8_post dynamic tol 배선**(`kics_json_rules.py`): rule 8(적용전)만 있던 micro-coarse tol(`max(eff_tol, |exp|*0.5/d14 + 50/d14)`)을 8_post에도. 카카오 2023.4Q(item14후=20억 반올림, 974/20=4870 vs 공시4777) prepush RED 1→0. rule8과 불일치 교정.
- **적용후 tolerance 교정**(`validate_kics_disclosure.py`): `_transition_identities_after` R1~R8 합-항등식 tol 5%→0.5%(mmult용 5%가 exact 합에 잘못 복사돼 농협생명 가용자본 2693억 break 마스킹하던 버그). item1후=item2후+item3후 등 3건 unmask → parser raw-verified override로 해소(inbox 20260707T2223Z).
- **COPY amount-guard**: 적용후 item27/28 COPY 판정에 item2후/item14후 이동 여부 추가(롯데 자본잠식 소폭개선 오탐 방지).
- **documented exceptions 5셀**(`_AFTER_SUBRISK_NOT_DISCLOSED`): 하나생명 24.4Q/26.1Q(phase-in 미공시)·농협생명 23.1Q(다중경과 결합공식불명)·처브 24.3Q(컬럼불규칙)·흥국화재 24.4Q(image-only) — 적용후 mmult·추출갭 둘 다 제외. TODO_validation.md 기록.
- **게이트 상태**: prepush RED=0(gate-clear) · K-ICS 적용후(항등식·mmult·item12·유실) 0 · core RED 13(동양·하나생명·미래에셋 image-scan + 한화손해 4억 반올림, 전부 documented) · IFRS17 core 깨끗.

## 2026-07-07 (b) — 인계: parser의 게이트 수정 적대적 리뷰(승인) + 잔여 4 MISSING 복구발주

멈춘 검증 세션 인계. parser가 0502Z 정본발주 처리(139→4 MISSING)하면서 **내 게이트 스크립트를 3커밋 수정**(69fe566 데이터/doc·972c206 sign fix·94db994 dynamic margin) → 파서가 검증코드를 건드린 거라 **적대적 리뷰**:
- **972c206 부호 fix = 정당**: `LOWER`(방향위반)을 `b>=0`일 때만 발화. 분모(기준금액) 항상 양수→비율부호=분자부호, "자본잠식사(음수비율)는 분모↓시 더 음수 정상"을 정확히 구현. COPY/AMT_MISMATCH 부호무관 유지. raw 4사 검증 근거.
- **94db994 dynamic margin = 정당**: 절대 1.0pp→`max(0.1,min(1.0,0.15·|전|))`. 독립감사(`scratchpad/adv_margin.py`): 통과된 5셀 전부 상대변화 18~47%=진짜 소액개선(복사면 ~0%), floor 0.1이 반올림복사 계속 차단, 구멍 0. rule8 동적허용오차와 동형. **accept.**
- **rule_8_post `same_basis` fix**(kics_json_rules.py, 미커밋): item2후/item14후 기준 어긋나면(한쪽만 post) pre2/post14 무의미값→spurious RED. mixed-basis시 SKIP(진짜결측은 transition MISSING이 잡음). 정당.
- **잔여 4 MISSING 복구발주 `20260707T0013Z`**: 흥국생명/흥국화재 2024.4Q(원천오염이나 25.1Q 비교표 직전분기컬럼으로 복원)·악사 2024.3Q(cadence아님, 다른 홀수분기 다 present, 재추출). 전부 복구경로 확인.
- **코어 RED 12 = 전부 이미지스캔**: KR0087 동양2023.2Q×7·KR0079 8_life(documented)·**KR0097 하나생명 2024.2Q×4(신규, scan-image items1-26 결측, OCR 재처리 필요)**.
- **transition 게이트 최종**: 18정본사 item27·28, 부호인지, dynamic margin, AMT_MISMATCH. 반올림복사·item27-only·"진짜동일"·부호오탐 전부 차단. 139→4(복구발주됨).

---

## 2026-07-07 — ✅ 경과조치 after-capture 작업본(139→7) 적대적 재검증 + rule_8_post 폴백버그 수정

DEFINITIVE(20260706T0502Z) 발주에 대한 parser 작업본을 **raw 3중대조(회사별 fan-out 4에이전트) + 내부정합 프로브 + 스코프 diff**로 적대 재검증. **판정: 작업본 대체로 건전(sound).**
- **raw로 확증**: 케이디비생명 13Q from-scratch(총괄표 억 직접대조·item1 자본감소분 점프·음수부호·복붙지문0)·하나생명 3Q·마진완화/부호skip 셀 전부(IBK 2024.2Q item1 6064→9407 +55%도 REAL). 검증기 sign-fix·margin-fix 정당(항등식 체크 유지로 은폐 없음). before값 무변경·행 무증감·항등식 0불일치. 부호skip 셀 전량 분모(item14) 실감소 뒷받침(SUSPECT=0). 스코프이탈 10건(메리츠·신한라이프 후=전)은 정확·무해.
- **F1(RED→parser)**: 에이비엘 KR0070 2025.3Q item28後=52.22·푸본 KR0083 2023.1Q item28後=△70.57 — raw 총괄표에 값 실재한데 "not fixable"로 성급 포기. item2後=item2前(불변)·item28=item2/item14×100로 복원. 발주 `20260706T2330Z`.
- **F2(→parser)**: 흥국생명 KR0071 2024.4Q item1後=35158/14後=16987/27後=207이 **출처불명**(available raw=오수집 사업보고서, 지급여력비율 수치·총괄표 부재; 207 정수+item14後 파생 냄새). parser 자기원칙(None+not_disclosed)·sibling item28後(None)과 모순 → 인용 or null 요청.
- **F4(→downloader/OCR)**: 하나생명 KR0097 2024.2Q 스캔이미지(56p text0)지만 DPI렌더로 전 코어 복원가능(현재 0레코드, parser "OCR채움" 미반영). 영구 dead-end 아님.
- **F3 수정 완료(validation 도메인)**: `kics_json_rules.py` rule_8_post 폴백버그 — item2後 결측인데 item14後만 있으면 `expected=pre2/post14`(pre분자÷post분모 혼합) spurious RED. **분자/분모 same-basis(`(2 in values_post)==(14 in values_post)`)일 때만 검증**하도록 수정. spurious 8_post RED 3→0, GREEN 458 보존(coincidence-pass 19만 정당 skip). 진짜 결측은 transition MISSING이 독립 검출 → 은폐 없음. 테스트 25/25 pass.
- **게이트 현황(exit 2 유지, push 차단 정상)**: 룰 RED 8(KR0087 2023.2Q 7 + KR0079 8_life 1 = 전부 scan-only pre-existing/documented) + census MISSING 3(하나생명 2024.2Q·카카오 ×2) + transition MISSING 7(흥국화재2·악사2·에이비엘1·흥국생명1·푸본1). transition 7 중 5(에이비엘·푸본·흥국생명)는 F1/F2로 처리 예정, 2(흥국화재)·악사는 raw 부재(downloader/연말이연) 정당.

## 2026-07-06 — 🔴 경과조치 "적용후" 가짜수정 적발 + 게이트 하드룰 (owner #6, user 지목)

user: "경과조치 적용사면 적용 전후로 지급여력비율이 같아선 안 된다"는 도메인 불변식으로 파서 재실행 검증 지시. → **파서 "복사버그 정정" 커밋이 가짜수정임을 적발.**
- **적발**: 파서가 커밋 5건(`31bcead·55e81f3·f3b4013·ad968cf·c604e0e`)으로 처리 주장했으나, item27 적용후를 raw에서 추출한 게 아니라 **round(적용전)을 적용후 칸에 복사**(exact-identical만 피한 위장). 22 적용사 item27 285셀: **복사/반올림(|후−전|<0.1) 139 + 결측 19 + 역전 6 = 164 가짜(57%)**, 진짜 후>전 121뿐. 결정적 근거 = 정상 마진 50~190%p(한화손해 176.7→254.4·아이엠 158.5→294.8·DB생명 202.4→361)라 후=전(차이 0.01)은 물리적 불가.
- **게이트 하드룰 `_transition_ratio_after_capture`** (owner 20260703T1138Z #6): 불변식 = 경과조치 적용사는 item27 적용후 > 적용전. 적용사 = **owner 22 seed ∪ 동적탐지(후−전≥1%p 분기 ≥2)**. 적용후 (후−전)<1%p OR None OR 후<전 = **RED, exit 2 하드차단.** item27 전용(금액계열은 경과조치 종류별 방향 상이).
- **라이브 168셀 검출**(21 적용사; **IBK연금만 0 = 유일 정상재추출 → 룰 오탐 0 확인**). self-test 7/7. 파서 반려 `20260705T2150Z`.
- **publish = 보류 확정**: 적용후=화면 표시값(경과조치 후 지급여력비율)이 21사 168셀 가짜 → 진짜 재추출 + 게이트 168→0 전엔 불가. 게이트가 이제 하드 강제.

---

## 2026-07-05 (c) — parser 0745Z 백필 검증: PARTIAL 14→3, 잔여 진짜갭 2건 재발주 + 자체정리

parser가 0745Z(census 백필 발주) 처리 완료 주장 → **데이터로 검증**(말 안 믿고 시계열 대조).
- **parser 실적**: PARTIAL 14→4·FULL_ABSENT 14→2. docling 미실행 11건(raw는 있으나 md_inbox 부재) 재docling+fill, item27 중복행 dedup(삼성생명·메트라이프 14분기), 부수버그 2건 수정(KR0082 2023.3Q item29 cell-shift 부모값 복제→987.32 / KR0097 2024.4Q item35 1000x→52.08). 커밋 3(`f62add4·26b8446·748a8b2`).
- **잔여 4 PARTIAL 시계열 검증 → 파서 주장 일부 반박**:
  - **KR0073 교보 2023.2Q item35(대재해)** = 진짜 갭(파서 놓침): 다른 11분기 전부 ~3,450억(±3%)인데 2023.2Q만 빔. → 재발주.
  - **KR0075 BNP 2025.3Q item37(주식)** = 파서 "실제0 공시" 주장 **반박**: 12분기 전부 67~311억, 0인 적 없음. 생보사 주식위험 0 비현실적. → 재발주(2025.3Q 표 재확인).
  - KR1098 카카오 2023.3Q item40(자산집중) = micro(1.3~68억), 0 가능성 수용 → parser에 "0이면 None 아닌 0.0 적재" 권장.
  - KR0051 신한이지 2023.2Q item32(LTC) = 값 ~1억(median 1.0=floor 경계) 오탐 → **`_CHILD_MATERIAL_FLOOR` 1.0→5.0억 상향**(진짜 갭 median 24억+ 무영향, self-test 7/7). PARTIAL 4→3.
  - KR0104·KR1010 2023.2Q FULL_ABSENT = 파서 확정 legit-absent(원천 세부표 부재) 수용.
- **재발주**: `inbox/parser/20260705T0805Z…census_residual_2cells`(교보 item35 + BNP item37, 데이터 증거 첨부). 현 PARTIAL 3 = 재발주 2 + 카카오 micro 대기.

---

## 2026-07-05 (b) — parser 재라운드 검증: KR0083 해소 → prepush GATE-CLEAR (RED 1→0)

파서 재작업(IFRS17 viz 재빌드 + KR0083 2025.2Q K-ICS 재추출) 검증.
- **KR0083 2025.2Q 완전 해소**: downloader가 오슬롯 PDF 교체(KR0075 BNP 파일이 KR0083 슬롯을 덮고 있던 원인) → parser 재추출(items 1-28 교차검증 일치·subs 29-46 복원·item19=√(VᵀMV)=8559 reconcile ✓, #32 장기재물=푸본현대 전분기 미공시 legit-absent). → **prepush(data-contract) RED 1→0 = GATE-CLEAR**(provisional=False), K-ICS RED 9→8, FULL_ABSENT 16→14.
- **K-ICS RED=8 = 전부 documented**: KR0079 8_life(SKIP=비차단) + KR0087 동양 2023.2Q ×7(코어표 이미지전용 scan-only census갭, `TODO.md` L89). 신규 RED 0.
- **IFRS17 마스터 코어 무손상**: closing 324P/0F · crosscheck 0F · cont 0 · dup 0. sens 1R(라이나 known)/direction 18→20(민감도 재빌드, 비차단).
- **push 잔여 = 내 신규룰 PARTIAL 14**(parser worklist 0745Z 아직 open/미드레인) — 실제 갭, parser 백필 대기. 내 validation inbox empty.
- ⚠️ **관측**: prepush data-contract 게이트 census는 `_coverage_census`+`_parent_zero_child_nonzero`만 재사용, **내 `_parent_present_child_incomplete`(PARTIAL 14)는 미포함** → prepush=RED0인데 K-ICS 게이트엔 14 PARTIAL 잔존. push 권위 게이트에 신규룰 배선 검토 필요(follow-up).

---

## 2026-07-05 — parser IFRS17 재빌드 검증 + IBK연금 무재보험 false-positive 해소 (owner "cell 등록")

parser가 IFRS17 레인 재빌드(viz 패널 + 마스터: csm_waterfall·pl_breakdown·sensitivity_heatmap·bs_snapshot + DART FS 캐시). 게이트 전수 재검증.

- **코어 정합성 무손상**: IFRS17 **closing 324P/0F · crosscheck 0F · plausibility cont 0/dup 0** — 재빌드가 기본 등식 안 깨뜨림. **tier2 data-contract RED 4→0** (두 달 막던 소진율/분모 이슈 해소 확인).
- **push 게이트(prepush) RED 5→1**: 5 RED = KR0083 2025.2Q 19_market(진짜 갭, 이미 parser 0745Z 라우팅) + **IBK연금보험 재보험손익=0 ×4**(`IMPOSSIBLE_ZERO_LEG`). IBK연금 4건은 **오탐** — 순수 연금사 무재보험 입증(재보험 5개 leg 전부 0.0 + 원수분해 정확히 닫힘: 원수CSM상각35111.6+위험조정2162.6−예실차5855.7−기타4015.9=생명장기원수손익27402.6). 손보 장수 케이스와 동형(카테고리로 단정 금지).
- **owner 결정 "cell 등록"** → 처리: (1) `data/_gold/user_pl_confirmed_cells.json`에 IBK연금 2024.4Q·2025.4Q 재보험 legit-zero **4셀 등록**. (2) `validate_data_contract.py._pl_impossible_zero_leg`가 owner-confirmed registry 존중하게 배선(skeptic과 동일 `_load_owner_confirmed` 패턴, tol 내 재드리프트 시 재발화). (3) 마스터 게이트도 whack-a-mole 방지 위해 `IMPOSSIBLE_ZERO_EXEMPT` + `ZLEG_LEGIT`에 IBK연금 면제(에이비엘 선례 동형). → prepush **RED=1**(KR0083만), 마스터 **impossible0 4→0·zero_legs 5→3**(잔여 동양/예별 known).
- **잔여 전부 known/legit**: pl_bridge 6F(전부 2023.1Q 사이트 비노출 + KB라이프 소액), zero_legs 3(동양 2025.3Q·예별 소형손보 생명장기 None), sens 1R(라이나 천원 미정규화 V12 audit-only), anomaly 199Y(마이크로사 triage큐 비차단). **push 차단 = KR0083 1건뿐**(parser 백필 대기).
- 부수: `_data_contract_selftest.py` 부재(pre-existing purge, git無) → `--selftest` 불가하나 본 게이트 정상. 회귀는 라이브 실측(RED 조성 검증)으로 대체.

---

## 2026-07-04 — 게이트 사각 2종 신규룰 (parser blind_spot 0703 처리): 부모-자식 census + 지급여력비율 스파이크

parser blind_spot `20260703T1250Z`(owner 워크스루가 게이트 RED=0 통과분에서 잡은 2부류) 처리. 데이터는 parser가 이미 수정, 이건 **룰 강화**(auto_loop 아님). 둘 다 `scripts/validate_kics_disclosure.py`에 구현, self-test 7/7 PASS.

- **사각 B → `_parent_present_child_incomplete` (RED, 차단):** 부모 위험액(item17/19) present&비0인데 그 회사가 '평소 유의미하게 보고하던' 자식(29-35/36-40)이 결측 = docling 행 누락. 기존 `_parent_zero_child_nonzero`의 역방향(부모>0·자식결측) 사각을 닫음. 자식 '기대'는 **회사별 self-census**(부모-present 분기 과반 present & 중앙값≥1억) — **회사유형이 아니라 회사별 실보고값 기준**(owner 지적: 손보사도 장수리스크 있을 수 있음 → DB손해 406억·코리안리 45억·삼성화재 20억 실보고 확인, 검출대상 유지). 구조적 N/A·상시0(생보 LTC item32 등)만 자동제외. **PARTIAL**(자식 일부 present+기대자식 결측=표실재·행누락)만 RED 승격, **FULL_ABSENT even-Q**(자식 전부결측, 2023.2Q 도입초 간이공시 클러스터 의심)는 자동RED 대신 **원천확인 review(비차단)**. 라이브: PARTIAL **14 RED**(KR0050 24.1Q/24.3Q/25.1Q item34·35 = blind_spot 예상 3건 정확 발화) + FULL_ABSENT review 16.
- **사각 A → `_ratio_series_spikes` (YELLOW, 비차단):** item27(지급여력비율) 회사별 시계열에서 인접 2분기 '양쪽 모두'와 크게 벌어진 단일 분기 = 엉뚱한 회사 PDF 오적재 같은 소스오염(자기정합적이라 산술룰 GREEN 통과). **부호역전 자체는 flag 안 함**(자본잠식사 정상 0선통과) — resid=|x-(prev+next)/2|>max(30, 3·(|prev|+|next|)) & 양옆 각각 30%p 이탈. 라이브 발화 0(parser 수정 후 clean), 옛 KR0083 25.2Q +318 주입 시 정확 발화(self-test). item27 중복행(삼성생명·메트라이프 전정밀도+반올림 이중기재) 분기 dedup 포함.
- **무손상 확인**: 기존 run_validation RED=9 불변(내 추가는 findings/by_status 미접촉, 별도 report 섹션+exit code만). census/parent-zero 기존 로직 그대로.
- **후속 라우팅**: 발화 14 RED + 16 review 백필 → `inbox/parser/20260704T0745Z…parent_child_census_gaps`(부수발견 2건 동봉: item27 중복행·세션중 kics_disclosure.json 재작성=parser 활성 추정). blind_spot 0703 = **resolved**(inbox/_resolved). owner tier_limit 1529Z도 resolved 아카이브.

---

## 2026-06-20 (b) — owner xlsx/JSON 직접수정 후 게이트 3종 전수 재검증 (push-gate 무결성, 재적재 0)

owner가 `sync_owner_fills_to_json.py`(135셀)+`insert_kakao_missing_quarters.py`(89행)+MOLE 손정정(교보 원수예실차·BNP 단위·코리안리 중복)으로 **root JSON 직접수정**. validation은 owner 지시("덮어쓰지 마라")대로 **재적재 금지, read-only 검증만**(`validate_master_tables.py --no-build`로 owner값 보존 — 빌드 선행 시 diag 미반영분 소실 위험).

- **data-contract 게이트(`prepush_check.py` = push #0): RED=4, 전부 tier2(CHECK 4 domain identity).** 동양·KB·미래에셋 2026.1Q `T2_UTIL_OVER_100_NO_EXEMPTION`(proxy-gross artifact) + 신한이지 `T2_DENOM_NOT_SCR_HALF`(1/100 스케일). 하나손·악사=YELLOW(면제표 파싱 legit "100%+"). **전부 owner `TODO.md`(2026-06-20) + inbox 라우팅 완료**(UTIL×3=downloader OCR 0617Z, DENOM×1=parser ifrs17 0238Z). push는 4건 해소 후 = 현 BLOCKED 정상. **validation 신규발주 0.**
- **owner CHECK 4 리뷰(재구현 0)**: 면제표 파싱사=YELLOW / proxy 미파싱=RED / RBC 분모=RED 분기 전부 의도대로. 회귀 "KB류 미추출>100%=RED" 하드강제 충족. tier_limit inbox(1529Z) resolved.
- **K-ICS 게이트: RED=1**(KR0079 미래에셋 8_life 2023.2Q, scan-only SKIP 비차단) + census missing 4(동양/하나생명/카카오 이미지 PDF) — 전부 `TODO.md` documented.
- **IFRS17 master 게이트: closing 321P/0F · crosscheck 0F** 유지 = **owner PL 121셀+CSM 10셀 수정이 정합성 무손상**. plausibility **cont 12→6 감소**(owner 손정정이 오히려 개선). 잔여 sens 1R(라이나 천원 미정규화=기존 0712Z/V12 audit-only 밴드레이아웃 추적), pl_bridge 14F(2023 known + 한화생명 이상치, 비차단), zero_legs 1(동양 2025.3Q known).
- **owner 룰7/8 dynamic tolerance 독립검증 PASS**: `max(eff_tol, |exp|×0.5/d14 + 50/d14)` dynamic항이 분모 d14(item14)에 반비례 → 정상분모 tol=2.0 불변, 카카오 20억만 tol≈124%p. 진짜오류 마스킹 0(게이트 실측 K-ICS RED=1만=타사 미마스킹 확인) → owner 감사주장("카카오 2023.4Q 2건만") 정합.

- **cont 6건 처분(owner 결정 2026-06-20, "마저" 후속) = 둘 다 데이터 정정(면제 아님)**: 교보생명 2024 = legit 소급정정 → **후속 공시 '전기' rollforward로 과거 cell 정정**(owner 제안). 처음엔 `CONT_RESTATEMENT_CONFIRMED` 면제 등록했다가 owner가 "면제 말고 전기표에서 재작성값 가져와 정정" 제안 → **면제 코드 원복, parser 0600Z 정정 발주로 전환**(시계열 통일이 면제보다 정확). 삼성생명 2024 = misparse(owner: 2023.4Q 기말 122474 정답) → parser 0545Z. **raw XML은 purge지만 extracted(`data/dart/extracted/<회사>_<rcept>_measurement.json`)는 살아있어 실행가능** — raw 없을 때 후속 공시 비교열 추출이 우회로. 정정 후 cont 6→0. 라이나 sens RED → V12 0435Z phase2 추적 핀. pl_bridge 14F = 전부 known(2023 비노출 12 + 소액잔차 2).

**종합: push 차단 = ① data-contract tier2 4건(parser 0238Z/downloader OCR) + ② IFRS17 삼성 cont(parser 0545Z 정정 대기). 둘 다 데이터작업 = validation 소관 밖.** 그 외 신규 글리치 0, 잔여 전부 owner 인지/라우팅/documented.

---

## 2026-06-20 — 룰7/8(지급여력·기본자본비율) 초소형 분모 동적 tolerance (orchestrator FYI)

owner가 카카오페이손해(KR1098) 2023.4Q·2024.4Q 통째결손을 xlsx로 채워 JSON 직접삽입(89행) → 2023.4Q에서 **KICS_7·8 RED**. 원인=기본요구자본(item14) **20억** 초소형 분모의 정수반올림: 재계산 974/20×100=4870 vs 공시 item27/28=4777.18(정확). 분모 ±0.5 반올림이 비율 ~120%p 흔듦. **`kics_json_rules.py` 룰7·8에 동적 tolerance** `max(eff_tol, exp×0.5/|item14| + 50/|item14|)` 추가(기존 **8_life 선례 동형**, line 429~432). 감사: OLD-fail→NEW-pass 셀=**카카오 2023.4Q 2건뿐, 타사 0건**(단조 widening, 진짜오류 마스킹 없음 검증). 게이트 RED 13→11. parser 0811Z 후속2 참조.

---

## 2026-06-17 — data-contract 게이트 마무리(서브에이전트 한도중단 복구) + consolidate 자동아카이브 + inbox 드레인

- **data-contract 게이트 완성**: 면제 메커니즘 제거(zero-RED 정책) + Phase 2 사이드카 reader 추가를 시킨 서브에이전트가 **세션 한도로 중단**(reader+helper는 작성, `Env._load_provenance_sidecars` 로더만 누락 → AttributeError 크래시 0/7). 메인이 누락 로더 추가로 복구: `--selftest` **7/7**, 라이브 **exit2 RED=52**(sensitivity 22 STALE_AS_OF 유지). reader=사이드카 있으면 strict/없으면 Phase-1 fallback.
- **`consolidate_inbox.py` 자동 아카이브**(owner): `_archive_resolved()` 매 실행 시 stage 폴더 `status: resolved`→`inbox/_resolved/`(answered 제외, idempotent, 동명 중복제거) + `_data_contract_findings` 핸들러 pre-wired. 일회 sweep 포함 resolved 19건+ 정리.
- **validation inbox 0 open 드레인**.

---

## 2026-06-16 — 부모-자식 정합 룰 신설(SGI 게이트 사각) + INTERNAL_MODEL_36IRR 등록 + 카카오 cadence 정정

owner 라이브 QA 3차 inbox 드레인(`…SGI…catastrophe_misparse_blindspot`, `…kics_market_irr_exempt_register`).

**🔧 신규 룰 — `_parent_zero_child_nonzero` (`validate_kics_disclosure.py`)**: 부모 위험액 항목이 표에
present & ≈0인데 하위 세부 비0 = 구조상 불가능(K-ICS 상관행렬 집계상 분산총액 ≥ 최대 단일세부) → RED(게이트
차단 exit 2). 부모 매핑은 명시 item번호(항목번호 flat index·라벨접두어 '1.'은 자본tiering에도 출현 → 접두어
매칭 불가): item17(생명장기)→29-35, item19(시장)→36-40. 부모 결측은 census 소관이라 제외. owner SGI 25.4Q
대재해(item35=5212/생명장기 0) 사각 폐쇄. **전수 스캔 3셀**(owner 1 + 적발 2): 서울보증 2025.4Q·2023.4Q,
카카오 2023.3Q — 전부 대재해(item35) 오정렬. 파서 발주(`…parentzero_catastrophe_plus_kakao_19market`).

**✅ INTERNAL_MODEL_36IRR_EXEMPT 등록(owner 승인 2026-06-15)**: `kics_json_rules.py` frozenset + 36_irr 블록
최상단 SKIP 단락. 5셀(KR0073 2025.2Q · KR0094 2024.2Q/2024.4Q/2025.2Q/2025.4Q) RED→SKIP. **36_irr RED 11→6**
(잔여=KB 이미지 3 + 신한이지 micro 3). 내부모형사 — 41-46 순자산가치 present라 표준식이 _check_numeric RED를
내므로 최상단 SKIP. 근거 = 회사 시나리오별 금리위험액 직접공시 → 식 정확일치(KR0094 25.4Q=578,999).

**🔴 카카오 2023.3Q 19_market = cadence-SKIP 부적절(TODO line 79-80 정정)**: parser 제안("NO-HEADER cadence")을
검증하니 docling MD L177-186에 분해표 실재(시장위험액 248/금리 15/부동산 244). 19_market RED는 참(JSON 36-40
미적재) → cadence-SKIP 안 함(실재 표 은폐+회귀 위험). 단 micro 억원-coarse(item19=2=248백만/100)라 적재해도
near-0·reconcile 불안정 = 카카오 2023.2Q 동류 micro artifact. 처분=파서 적재 후 micro documented or owner
micro exception(cadence 아님). 회귀: pytest tests/unit 110 passed.

## 2026-06-16 (b) — V7 NB CSM 시계열 off-by-one 재확인 + check_nb_csm_history.py 복원 (backlog #5)

owner "바로 진행" → backlog_digest #5(history 빌더 off-by-one 회귀 → check 재실행, systemic-3 재확인) 처리.

- **off-by-one-year 회귀 = FIXED 확정**: 현 `data/ir/series/`는 Q1 YTD-reset 정합(삼성화재 nb_csm_eok 6782.7→14426→26068→34995, 2024.1Q 8855.5 리셋 = 1년 시프트면 불가능). series mtime 10:40 > stale check 10:35이나 ir_eok·flag 완전 동일 = 시프트 흔적 0.
- **`scripts/check_nb_csm_history.py` 복원**: 사라진 ad-hoc 도구를 self-contained 재작성. 컨벤션을 series 메타에서 도출(nb_csm_singleQ_eok field=singleQ / units "YTD"=ytd_delta / else per_q_delta), DART new_business YTD→per-Q delta(Q1 raw, mn→억). DART per-Q가 stale matrix와 정확 일치(faithful 검증). `data/_derived/nb_csm_history_check.json` 현행 갱신, exit 2 if OVER/UNDER. 소비자 0(standalone 리포트).
- **systemic-3 = 실재(정렬 아티팩트 아님), 근본원인 = DART partial 추출**: 롯데 2025.2Q status=partial→NB_YTD=0→delta −1098.5(음수 NB 불가) / 미래에셋 2025.2Q·3Q partial→YTD collapse→2025.4Q ok에서 catchup spike(=‟↑↓ 교대") / 2025.2Q cohort-wide=동일 partial(반기·3분기 CSM 블록). DB 부호반전은 DB DART 2025.2Q+ 부재로 재현 안 됨(현상 롯데로 이동). 삼성생명 2025.2Q OVER(+26%)=status=ok=진짜 DART↔IR scope 차이(별건).
- **라우팅**: parser/ifrs17 `20260616T0230Z__validation__MULTI__nb_csm_partial_extract_corrupts_history`(partial 재추출 + status∈{partial,no_csm_block} 전사 sweep + 삼성생명 별건). 검증측 #5 완료, parser 재추출 트리거 대기.

## 2026-06-16 (c) — backlog #6/#7/#8/#9 (4-에이전트 Workflow 병렬 + 통합)

owner "전부다 진행" → backlog_digest 잔여 4건을 Workflow(4 에이전트 병렬)로 처리 후 메인 통합·검증·라우팅.

- **#6 삼성화재 FY2024 IR benchmark = RESOLVED / 현대해상 = owner·downloader**: `validate_nb_csm_multiple.py`에 `load_fy2024_ir_anchors`(IR series 2024.4Q.multiple_derived_ytd를 aligned FY2024 anchor로) + 삼성화재 PREFERRED_SCOPE에 monthly_avg_from_ytd. 삼성화재 computed 14.76 vs IR 15.16 rel 0.026 period_aligned=True fallback_used=False, **fallback_pass 2→1**. 현대해상은 in-repo FY2024 annual IR multiple 부재(1H/2H cadence) → fallback 잔존, owner 결정.
- **#7 V9 잔여 = 조사완료(parser-fix 0)**: closing identity 전부 EXACT(산술오류 0). (※ 한때 CONT 이중계상 면제를 넣었으나 **owner 지시로 즉시 revert: continuity break = 무조건 RED, "소급재작성" 면제 금지** — cont=15 유지, 면제 0. WFY 면제만 존치. 메모리 [[continuity-break-is-red]].) **[정정 2026-06-16: 오진 시인]** 교보 2026.1Q 등 5사 2026.1Q boundary = REAL 재작성 **아님 = 파싱오류**(owner 원본검증: 2026.1Q 기시=직전 2025.4Q 기말; 교보 65,110/메리츠 111,037/신한라이프 75,537/에이비엘 9,702/푸본현대 1,907.45). self-closing identity는 opening 검증 불가 = 내 오진. → downloader FY2026_Q1 raw 복원 + parser 재추출 발주(`…restore_fy2026q1_dart_raw`, `…csm_2026q1_opening_misparse`). 케이디비 2024.2Q +58%만 별건 within-period 변동. 저배수 4사 = scope 오류 아님(Q1 계절저점/micro, 분자 waterfall item2 일치; 한화 9.84는 IR FY 7.6 초과=‟low" 오독) → backlog framing 정정.
- **#8 verify_parser_change.py = DONE**: snapshot/diff(blast-radius; kics는 (code,quarter,item) cell-diff)/validate(6검증기 일괄 exit+summary 표)/all. 통합 `validate` 실행 확인(6검증기 정상). 추출기 변경 회귀 1커맨드.
- **#9 QoQ yaml loader = 이미 배선(no-op)**: `validate_master_tables.py:84`가 이미 `yaml.safe_load(config/qoq_thresholds.yaml)`. backlog 항목 stale.
- 회귀: pytest tests/unit 110 passed. verify_parser_change validate = 6검증기 정상(비-0은 전부 documented/routed: kics RED 동시변경, master cont/pl_bridge known, nb_csm_history parser 라우팅).

## 2026-06-16 (d) — KB PL 기타사업비 전수검증 + decision-free inbox 드레인 + data-contract 게이트 착수

owner: (1) decision-free inbox A-to-Z, (2) KB PL 기타사업비(item16) 전수검증.

- **PL 기타사업비(item16) 0처리 전수검증** (owner: IFRS17.html KB 보험손익 0.63조는 −16 없이 나옴, item16=0.39 차감이 워터폴 깨뜨림). 등식 `item1=4+5+6+7+8+13+14+(15−16)`(IFRS17.html:472). `scripts/check_pl_other_expense_closure.py` 신설 — pl_breakdown_master 244셀 분류: **ZERO 21**(보험손익이 −16 없이 닫힘 → item16 spurious) / KEEP 223 / NEITHER 31. ZERO = **KB손해 13분기 전부 resid=0 정확**(owner 케이스) + 케이디비생명 2023.2Q(0) + 흥국화재 6 early분기(2025.2Q부터는 −16으로 닫힘=비일관) + DB손해 2023.2Q는 resid −6,869=별건 제외. item20 영업이익=item1+item17이라 item16은 영업이익에도 안 들어감(=워터폴 전용 오류). → parser/ifrs17 발주 `…pl_other_expense_zero_where_closes`(build_pl_breakdown 일반규칙: 닫히면 item16=0, raw 비의존 transform). PL 마스터는 parser 리빌드 소유라 직접 편집 안 함(소실).
- **decision-free inbox 드레인**: (a) `doc_hygiene_prompt`→resolved (validation 프롬프트 3정정: gathering→parser·§3.1 inbox정본 재서술·misc 보조도메인 명확화). (b) `v7_gate_enforcement`(publishing)→resolved (check_nb_csm_history 복원 확인·V7는 data-contract ③ same-concept로 흡수+V1 retire 경로, 별도 publishing 블록 불요).
- **data-contract 사전-push 게이트 Phase 1 = DONE·검증** (owner `…data_contract_prepush_gate`, 최우선 인프라): `scripts/validate_data_contract.py`(+selftest) — 기존 validator import·호출(삭제 없음). 메인세션 검증: `--selftest` **7/7 PASS**(회귀 5건+변형) / 라이브 **exit 2 RED=52**(census 30=K-ICS 게이트 흡수+MISSING_FILER 6 · **as_of 22=신규 provenance 축이 V12 sensitivity_heatmap FY2024 staleness 적발** · cross-source 0) / build 미트리거. owner 결정 3: 22 STALE_AS_OF 처분(§4 면제 owner권한)·와이어링(§6)·exception 포맷. Phase 2 provenance 계약 정의 완료(parser/downloader 바운스 대기).

---

## 2026-06-15 — CSM 민감도 전수 재추출 발주(25.4Q 경영공시 기준) + DIRECTION_SANITY 룰 + 흥국생명 진단

owner: IFRS17.html CSM 민감도 흥국생명 이상(사망률↑ CSM−36 vs 25.4Q 경영공시 +28 / 해지율 역행 / 장해질병 누락) 지적.

- **진단(raw 검증)**: 현 heatmap 소스 = **FY2024 DART 사업보고서**(흥국 rcept 20250331003642, 2024.12.31) = **1년 stale + 비전수**(비상장사 DART 미제출). parser는 합계 행 충실 추출(해지율↑ 합계 CSM−1445.2/손익+61.12 = heatmap 일치 = **파싱오류 아님**). 장해질병 = FY2024 사업보고서 부재(경영공시엔 존재). 해지율 역행(CSM↓손익↑) = **source-faithful**(건강보험 product CSM−112,242/손익+564 견인).
- **소스 결정**: **25.4Q 경영공시**(`data/disclosure/FY2025_Q4`) — 전 보험사 의무·분기별·장해질병 granular. DART 사업보고서는 상장/대형사·연1회. 둘 다 2025.12.31·~2026.3 제출로 recency 동급, **커버리지·세분이 경영공시 우위** → 전수 fill 정답. inbox/parser(ifrs17) `20260615T0415Z__...csm_sensitivity_refill_disclosure_basis` 발주(파싱은 parser, validation 직접 안 함).
- **신규 룰 SENSITIVITY_DIRECTION_SANITY**(`validate_master_tables.py` 5b, owner rule-of-thumb): `sign(csm_delta)≠sign(pl_impact)`면 YELLOW(|CSM|·|손익|≥1억 floor). 손익/자본 컬럼 오선택·부호오류 전수 triage. 흥국 해지율형 source-faithful 역행도 flag되므로 fill 후 real(onerous) vs 파싱오류 판별. compile OK, stale FY2024 데이터엔 미실행(fill 후 작동).

## 2026-06-14 (b) — 정합성 전수검증: scan false-positive fix + sensitivity 단위룰 신설 + inbox 드레인 + 동시변경 적발

owner "docs 둘러보고 inbox·마스터 JSON 정합성 검증" 지시 → 3대 게이트 실측 + inbox 드레인.

**게이트 실측 (게이트 RED은 외부 동시쓰기로 변동, 아래 스냅샷 ~20:00 KST):**
- K-ICS `validate_kics_disclosure.py`: RED **42** (등식 21 + 시장 21) + census hole 21, exit 2. 등식 21 = 메리츠 rule5 ×12(systematic +45억) + 코리안리 2025.2Q core None ×7 + AIA rule2 ×1 + 미래에셋 8_life ×1.
- 금리민감도 `validate_kics_rate_sensitivity.py`: **RED 0** (RS3 32Y, DB손해 basis 예외 3). PASS.
- IFRS17 `validate_master_tables.py`: closing 0F·crosscheck 0F·pl_bridge 14F(2023 known + 메리츠 2023 + 한화생명 2023.2Q −90,613 이상치)·cont 15·wfy 2. + **신규 sensitivity RED 0/YELLOW 1**.

**🔧 fix 1 — `_scan_breakdown_presence` false-positive (삼성생명 odd-Q)**: distinct≥3 **substring** 매칭이 경과조치표 compound('주식위험액증가분점진적인식')·산문('자산집중위험등')을 라벨로 세어 odd-Q false RED. parser D 분쟁 raw 판정(KR0069 FY2023_Q3 MD L184/185/174/230 전부 비-표) → parser 정답, 06-13c "삼성생명 odd 3=진짜 갭" 자기정정. fix: 번호접두어 제거 후 **clean-cell 매칭**(셀==라벨/어간 또는 라벨 직후 숫자). 19_market RED 15→10(KR0069 odd 3 SKIP, 짝수·GREEN 불변).

**🔧 fix 2 — SENSITIVITY_UNIT_SANITY 룰 신설 (owner 0712Z claim2)**: `validate_master_tables.py`에 회사별 max|csm_delta| vs 또래 median 규모비. RED>1000x/<1/1000x(단위 미정규화, gate 차단)·YELLOW>100x/<1/100x. 현대해상=원단위→삼성화재 640배 케이스 회귀가드. 실측 RED 0(heatmap 19:58 재정규화로 640배 해소)·YELLOW 1(푸본현대 9.86억=median 1/308, ÷100 미적용 의심). 미래에셋·롯데·한화손해 3사 scenarios 0건(coverage 갭).

**🚨 동시변경 적발**: `kics_disclosure.json` mtime 17:16→**19:59:46**, `sensitivity_heatmap.json` 17:19→19:58 — **다른 parser 세션이 실시간 백필 중**(멀티세션 설계). 세션 중 게이트 RED 52→42, 시장 RED 31→21. 단일 스냅샷은 잠정값. 시장 RED은 parser 활성 도메인이라 라우팅 제외(중복 회피).

**📬 inbox 드레인 (validation/ open 3 → 처리)**:
- owner `census_gaps_sensitivity_sanity` → **resolved**. claim1(2025.4Q 36-40 전사누락)=라이브 staleness(데이터 38/38 적재·게이트 RED로 차단 중, 라이브만 미재배포=publishing/designer). claim2=sensitivity 룰 신설.
- parser `irr_exempt_register` **v2/iter2** → **answered**. 삼성생명 odd-Q resolved(라인번호 공유). TOOLING_FAIL census 요청=원칙수용·wire-up 보류(nonok.json이 데이터보다 lag, KR0011/KR0032 이미 빠짐, 진짜갭은 19_market이 이미 RED). INTERNAL_MODEL_36IRR/OCR/micro EXEMPT=owner 결정 상신(§4, 자체 waiver 금지).
- owner `backlog_digest`(0612Z) → #3/#4(시장36-40·item14후) 완료 종결, 잔여 open.

**근본원인 검증 Workflow(8 에이전트, raw 대조 진단→적대검증) → 라우팅**:
- **메리츠 rule5 ×12 → reparse**: parser가 item23(기타요구자본)+sub item25(비례성원칙)를 12 과거버킷 0 과소추출. 공시값(38~54억)=diff 정확일치, item14/15/22 정확. **라이브 2026.1Q는 이미 item23=57 PASS** = 구경로 버그. inbox/parser `KR0001_MULTI__rule5_item23_underextract` 발주.
- **코리안리 2025.2Q ×7 → reparse**: redocling이 MD 재생성 완료(코어 지급여력표 실재)인데 후속 파서가 금리민감도 스코프만 돌고 코어 1-28 추출기 미실행. item28 파생도출 필요. inbox/parser `KR1000_2025.2Q__core_items_not_extracted` 발주.
- **AIA KR0080 2025.1Q rule2(−789) → documented_exception(owner §4)**: image-only scan, item8/item9 둘 다 819(중복 OCR키잉), 텍스트 reparse 불가. 정확 allocation 미확정(item9≈30 추정). owner 등록 권고.
- **미래에셋 KR0079 8_life(2023.2Q +1367) → documented_exception(owner §4)**: image-only(파싱 MD조차 부재, pypdf 숫자레이어 0), subs 29-35 OCR노이즈 ~8.5% spread, 단일 culprit 없음. **기존 KR0079 rule2 예외를 8_life로 확장 권고.**

**재드레인(owner 지적 "안던진 inbox 없냐") — 동시변경 반영 재검증 + IFRS17 미발신 적발**:
- 데이터 재변경 확인: `kics_rate_sensitivity.json`(20:14)·`sensitivity_heatmap.json`(19:58, parser G7 재빌드) → **전 게이트 재검증**: K-ICS RED 42 · RS RED 0(20:14 변경 후도 안정) · master closing/crosscheck 0F · sens 0R/1Y. 내 답변 메시지 3건 무결(v3 clobber 없음).
- owner IFRS17 sensitivity 메시지(`ifrs17_csm_sensitivity_extraction`)는 **parser/ifrs17로 갔고 answered**(A G4b·C G6 삼성=백만원/현대=천원·B G7 5손보 복구). 그 답변 line 76 "validation 단위/비율 sanity 게이트 룰 권장"을 내 SENSITIVITY_UNIT_SANITY가 **충족**.
- **미발신 적발 → ifrs17 parser 발주**(`20260614T1135Z__validation__MULTI_2025__sensitivity_unit_ratio_sanity`): **푸본현대 csm_delta=9.86 vs pl=1164.85(비율 1/118, median 1/308) = under-scale** — 파서 OVER-scale 가드(>총CSM×3)의 사각(작은 쪽 미탐), 내 룰이 YELLOW로 포착. + 미래에셋(unavailable)·신한라이프(partial) CSM 민감도 coverage 재확인.
- parser 3건 회신(메리츠·코리안리·sensitivity) **전부 answered → 재검증 통과**: 메리츠 item23/25 12분기 적재(rule5 12 RED→0), 코리안리 코어 1-28+item28 파생+시장37-40(7 RED+19_market 해소), 푸본현대 = under-scale가 아니라 **mis-tagged 롤포워드**(shock행 0, parser `_has_shock_rows` 가드로 KB·푸본현대 ok→partial). 게이트 **RED 42→23**, sensitivity YELLOW→0. 3건 `_resolved/` 이동.

**inbox 백로그 triage (owner "1번 ㄱㄱ")** — validation-sent answered **16건 종결→`_resolved/`**:
- 06-09 continuity 8(KR0003/0011/KR1000 해소 + KR0009/0070/0072/0073/0099 = legit_restatement documented, WFY_EXCEPTIONS) / 시장 6(룰 라이브·146회수·fitz백필로 superseded) / qoq_signflip(동양 FIXED·교보 real·코리안리 escalate 3 verdict) / user_xlsx(06-11 재검증 통과·spawned 2건 clean).
- **유지(잔여)**: `hyundai_pl_legit_misjudge`(현대 2024.1Q~2025.2Q ZLEG_LEGIT_CQ 등록 잔여 — zero_legs 6 중 현대 5) + KR0083 2026.1Q continuity(현 RED Δ12.4%·sensitivity flagged = 실데이터 의심).
- **신규 in-inbox(parser irr_exempt 재확인)**: ① localizer **fitz-fallback LANDED**(KR0011·KR0032 ERR→OK, pytest 110) → **TOOLING_FAIL census 선결조건 충족, wire-up 가능**. ② **IBK(KR1011) 내부모형 면제서 제외**(fitz로 41-46 적재·derive rel 0.0% GREEN) → INTERNAL_MODEL_36IRR owner상신 = 신한라이프 4 + 교보 1 = **5건만**. ③ 현 RED 23 = 전부 OCR/내부모형/micro/scan = owner.

**A·B 실행 (owner "AB go")**:
- **(A) TOOLING_FAIL census 배선** — `validate_kics_disclosure.py._market_tooling_fail()`: nonok.json(localizer ERR/NO_SIGNAL/TIMEOUT/SCAN)을 현재 데이터와 대조해 *여전히 갭*(item19 공시·36-40 결측)인 셀만 're-localize' 워크리스트로 노출. stale-nonok 제외(데이터 lag 방지), 게이트 비차단(짝수 진짜갭은 19_market이 이미 RED — 원인 귀속용). 현 **TOOLING_FAIL=0**(3 nonok 전부 백필). parser fitz-fallback 안착 약속분 이행.
- **(B) 현대해상 2024.1Q~2025.2Q ZLEG_LEGIT_CQ 등록** — parser 표단위 raw확인(OLD form 비용측 LOB 부재) → `zero_legs 6→1`(동양 2025.3Q 잔여, 별건). `hyundai_pl_legit_misjudge` thread 종결.

**수렴 (parser 3 메시지 실시간 처리 → 내 재검증 PASS → resolved)**: parser가 KR0001(item23/25 항등도출=공시값 일치 적재)·KR1000(코어 1-28 + item28 파생 156.19 + 시장37-40 fitz보너스)·sensitivity(근본원인=mis-tag 롤포워드 shock행0, `_has_shock_rows` 가드 차단; 내 under-scale 가설보다 정확) 전부 answered. **재검증: 게이트 RED 42→23**(비-시장 21→**2**), **sens YELLOW 1→0**. 3 스레드 `_resolved/` 이관. **잔여 RED 23 = 전부 owner 결정 또는 parser 활성도메인**: AIA rule2 + 미래에셋 8_life = documented_exception 대기(2) / 시장 21 = localizer fitz-fallback 진행 + INTERNAL_MODEL/OCR/micro EXEMPT(owner). **validation-actionable reparse = 0.**

## 2026-06-14 — 파서 회신 2건 처리: 시장위험 146 회수 재검증 + item14후(8_post) 검증

새 parser inbox 2건 드레인(둘 다 resolved → _resolved):

- **`market_subrisk_recovered_146` 재검증 ✅**: 파서가 LLM추출+sqrt reconcile<2% 게이트로 36-40을 103→**146 all-five** 회수(41-46 144→**177**), gold 1325셀 영속화. master 반영 확인(all-five=146/41-46=177 실측). 게이트 19_market RED **148→21**(파서 회수 + 내 source-grounded cadence 합산). 파서가 이전 SKIP 요청 철회("200+ RED은 룰 아티팩트 아니라 underparse, owner·validation 옳았다") — 내 cadence 진단(홀수=간이공시) 독립 확인.
  - **핵심 회신**: 파서의 "odd-Q 103 EXEMPT 등록" 요청 **불필요** 통보 — source-grounded 룰이 disclosure MD 직접 읽어 홀수 간이공시를 자동 SKIP(수동 명단관리 불요, 분기 자동갱신). MARKET_BREAKDOWN_EXEMPT는 "짝수인데 원천도 부재" 예외만.
  - 잔여 19_market 21 = scan/OCR(AIA·카카오) + 짝수 full-form 결측(한화생명·흥국·DB·NH·KB손해·신한이지·처브) + 삼성생명 odd 3(텍스트표 존재·누락). `19market_real_gaps_21` inbox와 일치.
- **`post_transition14_done` (owner #4 / xlsx #3 blocker) 검증 ✅**: 파서가 생보 경과조치 적용후 item14후 적재(전=후 스킵버그 + _is_market_section 오분류 수정). 게이트 **rule 8_post = GREEN 442 / RED 0**(hollow SKIP 아님). 검증식 (2후+3후)/14후×100≈item27후 25/25 일치.
  - 파서의 룰 SKIP 요청 2건(36_irr/19_market 부분데이터 SKIP) **승인 안 함**: 0600Z에서 파서 철회. 올바른 해결은 SKIP rubber-stamp 아니라 데이터 회수 + source-grounded cadence(이미 적용). PDF census AGGREGATE 244 blanket 등록도 안 함(잠정후보).

게이트 현재: K-ICS RED 58(19_market 21 + 36_irr 16 + census 21), RS RED 0, IFRS17 closing/crosscheck 0F. owner #4 done.

## 2026-06-13 (c) — 19_market 과잉 RED 적발·수정 (source-grounded cadence; 148→21)

owner "19_market 148 진짜 어려운 거냐" 질문 → raw 추적으로 **내 2026-06-12 19_market RED 승격이 cadence 미처리로 과잉 flag**임을 적발(36_irr엔 넣은 cadence를 19_market엔 안 넣음 = 내 버그, owner 격노건과 반대방향).

- **진단(raw 확증)**: 148 RED을 MD 직접 확인 — 삼성화재 2025.1Q(홀수) MD엔 item19=60,822만 있고 36–40 세부표 없음(주식/금리위험액은 경과조치 문맥뿐). 생보 9사+삼성화재 등 **1Q/3Q는 간이공시라 세부표 원천부재**(69/72 raw 확증). 현대해상도 2023.3Q엔 표 있었으나 2025.3Q엔 없음 = 시기별 cadence 변화.
- **수정 (source-grounded + parity)**: `validate_kics_disclosure.py._scan_breakdown_presence()` — item19 공시·36–40 결측 후보셀의 disclosure MD를 직접 읽어 세부표 5종 라벨 distinct≥3이면 표 존재로 판정. `run_validation(source_has_breakdown=...)` 파라미터로 전달. `kics_json_rules.py` 19_market: **짝수분기(2Q/4Q full form)는 결측이면 무조건 RED**(텍스트스캔이 이미지/스캔표를 못 보므로 짝수는 숨기지 않음), **홀수분기는 MD에 표 있으면 RED·없으면 SKIP**(간이공시 cadence). `IRR_SCENARIO_EXEMPT`처럼 MARKET_BREAKDOWN_EXEMPT는 override 유지.
- **결과 19_market: RED 148→21** (EVEN 18 full-form 갭 + ODD 3 삼성생명 텍스트갭 = 진짜 추출가능 갭) / **cadence-SKIP 127 전부 ODD**(간이공시 원천부재, 짝수 숨김 0). GREEN 289 불변. 하나손해·삼성생명 2025.4Q는 파서가 이미 추출(GREEN).
- **자기정정**: 직전에 "148 전부 파서갭"이라 한 진술 철회 — raw 보니 ~127은 cadence-legit(내 룰 과잉), 진짜 갭은 21. 게이트 RED 264→**58**(19_market 21 + 36_irr 16 + census 21).

## 2026-06-13 (b) — 36_irr SKIP맹점 폐쇄(cadence-aware RED) + report_latest fresh-write

owner "TODO에서 확실히 고쳐야 하는 것만 골라 즉시 수정" 지시 → validation 단독 must-fix 2건(파서 무의존, 결정적):

- **36_irr SKIP→RED (cadence-aware)** (`kics_json_rules.py`): 19_market과 동일 맹점(부모 present·자식 결측인데 SKIP=통과). 단 41–46(금리위험 순자산가치 6시나리오)은 **짝수분기(2Q/4Q) 서식에만 존재**(실증: 41–46 보유분기 = 2023.2Q~2025.4Q 짝수 6개뿐, 홀수 0). 규칙: item36 공시·41–46 결측이 **짝수분기면 RED**(parser gap), **홀수분기면 SKIP**(원천부재 정당). `IRR_SCENARIO_EXEMPT`(빈값) 문서화 면제. 결과 **RED 23 (전부 EVEN, ODD false 0)** — 기존 SKIP에 은폐됐던 짝수분기 갭. 23건: 2023.2Q(BNP파리바·흥국화재) / 2023.4Q(KB손해·신한이지·에이비엘·하나생명·하나손해·흥국화재) / 2024.2Q(KB손해·교보플래닛·BNP·신한이지·흥국화재) / 2024.4Q(교보플래닛·신한이지) / 2025.2Q(교보플래닛·교보생명·하나생명) / 2025.4Q(IBK연금·KB손해·교보플래닛·케이디비·하나생명). → parser 41–46 재추출(market_subrisk inbox 후속).
- **report_latest.json fresh-write** (`validate_kics_disclosure.py`): 게이트가 매실행 `artifacts/kics_validation/report_latest.json`을 fresh로 덮어씀. 기존엔 orphan stale(5/25본)이 glob 정렬에서 timestamped 최신보다 뒤로 정렬돼 mis-read 유발(소비자 코드 0). 함정 제거.
- **게이트**: RED=268(19_market 220 + 36_irr 23 + census 21 + 등식 ~). 19_market 여전히 작동, compile OK.

## 2026-06-13 — owner 직접지시 kics_disclosure 데이터 정정 (dedup + 스케일 + AIA 적용후) + 19_market 면제 거부

owner가 kics_disclosure.json 다수 데이터 버그 지적. validation이 직접 정정(파서 무의존, 결정적):

- **중복행 dedup** (`scripts/dedup_kics_disclosure.py`, backup .bak): 16,160→15,665(−495). key+값 동일 34키 축약 / 값상이는 항등식 채택(비영단일 56, 23=24+25+26 closure 12 code·q, 27·28 정의식 13, 최빈 9; **FLAG 0**). garbage 기각(item12 68431·71335, item26 8313). 리포트 `artifacts/kics_validation/dedup_report_*.md`. 파서엔 "파이프라인 끝에 dedup 상설" + first/last/any 질문 답(="항등식으로 1행").
- **하나손해 2026.1Q 기본자본비율 2861%→28.62%** (`scripts/fix_kics_targeted.py`): 근본원인 item2(기본자본)=132375 ×100 스케일오류(item2>item1 불가 식으로 적발 — blanket threshold 아님; 카카오페이 6310%는 item2≤item1이라 정상 보존). item2→1323.75, item3 plug(−125617=item1−item2_old)→5434.25 복구, item28(적용전+적용후)→28.62. rule 1·8_post RED 해소.
- **AIA(KR0080) 적용전=적용후 강제** (owner: 경과조치 미적용사): 값_적용후 16행 copy-leak(item2=39162·item3=75984 frozen) 일소 + item27 8분기 도출(item1/14×100). rule 7 RED 해소. 적용전(값)은 파서 재적재로 이미 클린.
- **코리안리 자동차손익 null→0** 권고(owner: 자동차=일반 sub항목, 별도 미분리 = 정상). 파서 빌드 반영 요청.
- **19_market 면제 요청 거부**: 파서가 "fitz no-pdf 0건 = 223건 구조적 미공시"로 MARKET_BREAKDOWN_EXEMPT 등록 요청 → **blanket REJECT**. 근거: 하나손해(image-split)·삼성생명(라벨변형) 실공시 입증(2026-06-12a) = 추출기 한계지 부재 아님. reconcile-fail 3건은 표 존재. 조건부만 허용(image-split 스티칭+라벨변형 재추출 후, 그래도 없으면 raw 페이지 근거 첨부분만 셀단위 등록). MARKET_BREAKDOWN_EXEMPT 여전히 비어있음.
- **게이트**: dedup+정정 후 RED 293(19_market 229 + census 22 + 등식 ~42). 내가 유발한 RED(rule1 KR0050, 8_post KR0050) 전부 해소, 신규 0. 잔여 등식 RED(rule5/8 메리츠 등)는 기존 파서 추출 이슈.
- **진행 중(서브에이전트)**: 금리민감도 11사 2025.4Q 추출시도 + 현대 PL 2023–24 IR대조. 결과 도착 시 파서 라우팅. inbox 회신: `20260612T1100Z__parser__...2026q1_loaded_and_19market_exempt_request.md` ## 답변.

## 2026-06-12 (b) — consolidate_inbox 선배선(RS/waterfall) + V2 fallback 재검증 + market 스레드 정정종결

owner 백로그 다이제스트(#2/#6/#10) 즉시가능분 처리.

- **#2 consolidate_inbox VALIDATORS 배선**: `_rate_sensitivity_findings`(RS1/RS2_base RED) + `_waterfall_findings`(must_reparse) 추가, `VALIDATORS=[continuity,rate_sensitivity,waterfall]`. TEMPLATE을 `{section}`/`{request}`로 일반화(continuity 보존). 세 RED 버킷 0건 = **선배선**(owner "RED 발생 전 배선"). 06-09(a) "waterfall 항목 생기면 추가/untested 안 씀" 방침 → 스키마 확정(RS=runner dict키, waterfall=`failed` 버킷 동형)되어 pre-wire. 검증 3중(idempotent run findings=9 skip / 계약 플레이스홀더 테스트 / 합성 RED e2e: name→code·period유도 정상).
- **#6 V2 fallback**: `validate_nb_csm_multiple.py` 재실행 — **한화생명 fallback_used=False = retire 확정.** 삼성화재(2025.3Q 17.54 vs IR 14.1, rel 0.244=tol 0.25 턱밑)·현대해상(2025.1H)은 aligned FY2024 행 실패→fallback 통과(validator tolerance-loophole 경고). 삼성화재 IR annual benchmark 보강 미결(FY2024 IR 분모 소싱 필요).
- **#10 housekeeping**: inbox/validation 5건 `_resolved/` 이관(RS 2 clean + market 3 정정후). market_coverage_phase2_loaded의 "잔여 SKIP 정당(삼성화재·삼성생명·현대·한화 PDF 비공시)" 결론 **OVERTURN** 기록(=2026-06-12(a) 적발과 연결). "clean 종결" 아닌 "정정 종결"로 판단.

## 2026-06-12 — KICS 게이트 2대 사각 적발: coverage census 부재 + 19_market SKIP맹점

owner 격노 적발: (1) `kics_disclosure.json` 2026.1Q가 한때 KB손해 1개사(26셀)만 적재됐는데 게이트가 RED=0 통과 (2) 시장위험 세부 5종(item 36–40)이 거의 미적재인데 19_market이 SKIP으로 통과. 다른 세션은 즉시 적발. **근본원인 = 게이트가 "있는 셀이 맞나"만 보고 "있어야 할 셀이 있나"를 안 봄.**

**근본원인 (코드 레벨):**
- `validate_kics_disclosure.py`는 `run_validation(records)` — 데이터에 **존재하는 (회사×분기) bucket만** 순회. 분기/회사가 통째로 빠지면 finding 0개 → RED=0. 기대 universe 개념 부재.
- `kics_json_rules.py` `19_market`: 부모 item19 공시 + 자식 36–40 **전부 결측이면 RED이 아니라 SKIP**. 게이트가 RED만 세니 SKIP=사실상 통과. (`36_irr`도 동형 — 추후 검토.)

**수정 2건:**
- **`19_market` SKIP→RED 승격**: 부모 item19 공시인데 36–40 전무 → RED(parser gap 추정). 부분결측은 0 처리 허용 유지. 진짜 미공시는 `MARKET_BREAKDOWN_EXEMPT`(회사,분기) 문서화 면제(현재 비어있음).
- **coverage census 신설** (`validate_kics_disclosure.py` `_coverage_census`): regular-filer(≥분기절반 출현) × 분기 기대그리드 → 빠진 (회사,분기) RED + exit code 반영. 리포트에 `coverage_census` 블록·콘솔 분기별 미싱 출력.

**재실행 결과**: RED=292 (수정 전 사실상 은폐). 내역: 19_market 224건(36개사·13분기 전부 — 삼성생명/삼성화재/현대/DB/메리츠 포함) + census 미싱셀 28 + 등식 RED 40. **224건은 수정 전 전부 SKIP**이었음.

**raw 교차검증 (미공시 반증)**: 하나손해 2025.4Q는 5종 실재(금리30,358/주식62,491/부동산2,643/외환12,483/자산집중5,251)이나 표가 `<!-- image -->`로 분절 → 파서 미봉합. 삼성생명 2025.4Q는 "1.금리위험액"+충격시나리오방식 중간열 라벨변형. 둘 다 미공시 아님 = 전사 파서 갭. 2026.1Q는 항목 1–28에서 추출 절단(29–46 전무).

inbox: `20260611T2200Z__validation__MULTI_ALL__kics_market_subrisk_systemic_underparse.md` (route reparse — 36–40 전사 재추출 + 분절표 봉합·라벨변형 가이드 + 2026.1Q 29–46 backfill + census 28셀). 메모리: `coverage-census-mandatory` 신설.

## 2026-06-11 (c) — 현대해상 PL legit_absent 오판 적발 + AIA 사코드 + 불가능-0 leg 룰

owner가 현대해상 2026.1Q PL 답지(`gold/보험손익 breakdown_현대해상_2026.1Q.xlsx`)로 parser의 legit_absent 판정 반박.

- **AIA 사코드** (owner 재지시): `CSM_amortization.json` 10행 사코드 공란 → KR0080 채움. 원인: `build_tidy_exports.py meta()`가 kics_disclosure 원수사명만 봐서 kics 미수록 AIA는 None. `NAME_CODE_FALLBACK`(에이아이에이생명보험→KR0080) 추가(영속) + json 즉시 패치.
- **불가능-0 leg 룰** (`IMPOSSIBLE_ZERO_LEGS`): 생명장기 원수손익·기타원수·재보험손익·기타재보 4종은 장기보험사면 0원 불가 → 0.0이면 RED. 현재 0건(전부 None)이나 미래 가드. 메모리 `validation-blind-spots` 보강.
- **현대해상 legit_absent 오판 정정**: parser가 4종을 도출불가로 판정했으나 답지로 실재 확인(생명장기원수 279,302=241,253+37,322−126,865+127,592 검산 일치). raw에 보험수익 분석공시 멀쩡. ZLEG_LEGIT에서 **현대 회사면제 제거 → 8분기 재노출**. 단 **2025.2Q만** 진짜 미공시(보험서비스비용·재보험수익 자체 부재, owner 확인) → `ZLEG_LEGIT_CQ` 분기단위 면제.
- 교훈: legit_absent 주장은 **raw 표 존재로 교차검증** 필수 — 회사 전체 면제는 분기단위 진짜 미공시를 가린다.

inbox: `20260611T1000Z__validation__KR0009__hyundai_pl_legit_misjudge.md` (경고, route reparse, 8분기 재추출 + 2025.2Q 패스).

## 2026-06-11 (b) — parser 회신 재검증 통과: overrides 영속성·NB EX-기타·아이엠 정정 확인 + exception 등록

parser가 V9 inbox에 회신: ⓪ `csm_manual_overrides.json` + `_apply_csm_overrides()` 훅 구축(빌드 생존) ③ NB EX-기타 + `_MULT_FLOOR=1.0` 적용 ④ 아이엠 분자 CSM열로 정정(0.02→8.36/8.82) ① WFY 10/10 판별(DB손해 re-anchor 18셀 / 9건 legit restatement) ② PL None 분류 + gold-cell +170셀, 신한이지 CSM 제외(×1000 단위오류).

**재검증 (기본 빌드 포함)**: 정정 전부 빌드 생존 ✅ (롯데 16,774.38 / 아이엠 1,599.8 / DB re-anchor / 신한이지 제외). `--no-build` 모드 해제.

**exception 등록**: `WFY_EXCEPTIONS` 9건(legit restatement — 교보 3Q24 공식 소급재작성 등) + `ZLEG_LEGIT` (현대 분리미공시 4종 / ABL 재보 4종 / 서울보증·AIG·교보플래닛·신한이지 ALL). 결과: **wfy 9→0, zleg 23→1**(동양 2025.3Q 잔여).

**신규 발견 → parser 회신**: 메트라이프 영업이익 등식 2분기 FAIL(+12,086/+12,897, gold-cell 후 표면화) + 코리안리 crosscheck 2F 재출현(wf 2024.4Q 상각 ≈ pl 2023.4Q → 1년 lag 의심, KR1000 basis 연관).

SUMMARY: coverage 0/0 | closing 0F | dup0/spike1/cont16/wfy0/zamort0 | pl_bridge 2209P/16F(2023 12+메트라이프2+KB라이프·흥국 소액2) | zleg 1 | crosscheck 2F(코리안리) | qoq 195Y.

## 2026-06-11 — 사용자 xlsx 수기검수 적발 → 검증 사각 4종 보강 + 4갈래 조사

사용자가 마스터 xlsx 수기검수로 validation 미스 적발 (롯데 2023.2Q 기초, KDB 2023 상반기 상각 공란, 미래에셋 상각 누락, 현대해상 PL leg "0", 아이엠라이프 배수 0.02). **검증 사각 4종을 메모리+룰로 영구 반영**:

**신규 룰 3종** (`validate_master_tables.py`):
- **WFY**: FY내 기초 CSM 동일성 (YTD 컨벤션). 기존 연속성은 FY 경계만 봄. → 즉시 10건 적발 (DB손해 FY2023 4분기 전부 상이 등 — 롯데 동형 정정공시 의심, parser 재확인).
- **ZAMORT**: CSM상각 == 정확히 0 불가능 (사용자 룰 지시).
- **ZLEG**: PL 생명장기 sub-item 10종 중 0/None ≥4 무더기 flag → 28건 (현대해상 13분기 — **None이 bridge SKIP으로 은폐되던 패턴**; "0"으로 보인 건 xlsx의 None 렌더링).

**4갈래 병렬 조사 결과**:
- **xlsx diff**: 사용자 수정 24셀+신규 12행 식별 (롯데 2023.1Q신설+2Q전항목 / 케이디비 2023상반기 / 미래에셋 2023.1Q신설+2025.2Q~26.1Q 상각신설·가정재분해). → parser가 root JSON·xlsx까지 ingest 확인(19:12). ⚠️ diag stale — 다음 빌드 시 소실 위험, inbox CRITICAL로 전달. validation은 당분간 `--no-build`.
- **NB 분모**: 기타(비월납, 대부분 단체) 초회보험료 혼입 확정. EX-기타 시 농협생명 3.71→11.20, NH손해 1.74→11.38, KB라이프→10.48, 삼성생명→11.47 (10~17 정상권 진입). **삼성생명 EX-기타가 IR에 5분기 전부 근접**(MAE 0.43 vs 1.10; IR 정의=월납월초) → builder EX-기타 전환 권고. 교보·한화는 기타로 설명 안 됨(별도 원인). 568억은 NH손해 기타(농협생명은 649.8억).
- **PL zeros**: 정확히-0 무더기 0건 — 실체는 None. 예실차=0 45셀은 미공시→identity 유도(정상).
- **소스 추적**: DART 미공시 11사 전부 **연간 감사보고서(00760 별도, pblntf_ty=F)** 소스 — 검증된 공시지만 4Q만. **하나손해/하나생명/신한이지는 지주 분리가 아니라 자체 별도 감사보고서 파싱** (지주 보고서 미사용 — 분리 시도 자체가 없었음). 아이엠라이프 DART 분기 부재 = 비상장 지주 자회사(사업보고서 의무 없음). **아이엠라이프 0.02 = 분자 오염**(BEL+RA+CSM 행합 4.4억; 실제 CSM 1,599.8억) → parser 수정 대상.

inbox: `20260611T0900Z__validation__MULTI_ALL__user_xlsx_audit_followup.md` (diag 영속성 CRITICAL + WFY 10건 + ZLEG 28건 + NB EX-기타 + 아이엠라이프). 메모리: `feedback_validation_blind_spots` + `project_master_xlsx_review_loop`.

## 2026-06-10 — K-ICS 금리민감도 RS1–RS4 룰 구현 + 검증 통과 (RESOLVED)

owner 발주(RS1–RS4) + parser 마스터 적재(`kics_rate_sensitivity.json` 423행, 74 사·분기) → `scripts/validate_kics_rate_sensitivity.py` 신규 구현. 정본 `docs/agents/kics-rate-sensitivity-spec.md` §5.

- **RS1_RATIO_IDENTITY** (RED): (사,분기,경과조치)·충격컬럼별 `비율≈금액/기준금액×100`, tol max(0.5%p, 0.5%·비율). → **0 RED** (705 컬럼 전수 통과).
- **RS2_BASE_ANCHOR** (RED): 적용전 base vs kics_disclosure item1/14/27, tol 금액 2억/비율 0.5%p. → **0 RED** + KR0011 DB손해 2025.2Q 3 measure documented exception(별도/연결 basis, `RS2_EXCEPTIONS`).
- **RS3_DIRECTION_SANITY** (YELLOW): 생보 −100bp 비율 상승(역방향) 28건 — ALM상 정상 가능, 플래그만.
- **RS4_COVERAGE_CENSUS** (YELLOW): **회사 cadence 인식**(1Q/3Q 보유 이력 없으면 반기공시 → 1Q/3Q 부재 정상) → 손보 1Q/3Q 과탐 40→**1**(코리안리 2025.2Q hole).

**gate RED=0.** 룰표 `claude-agent-validation.md` §1.1 등재. 결과 `data/_derived/kics_rate_sensitivity_validation.json`. inbox owner/parser 2건 resolved. (consolidate_inbox 핸들러 배선은 RED 발생 시 후속 — 06-12(b)에서 선배선.)

## 2026-06-09 (d) — 시장위험 Phase-2 적재 재검증 통과 (RESOLVED)

parser Phase-2(PDF 직접추출, +150행 → 14,394) 재검증. `run_validation`:
- **게이트 RED=2**(KB손해 KR0010 rule2 OCR, KICS-IMG; **신규 RED 0**). 통과.
- `19_market` GREEN 163→**185** / SKIP 221→199. `36_irr` GREEN 42→**47** / YELLOW 17→23 / SKIP 314.
- 교보(KR0073) 전치표 5분기 스폿: derived vs item36 diff 0.1~2.8%(tol 5% 이내, YELLOW=정당).
- 잔여 SKIP 정당: 19_market 구조적 ~100(삼성화재·삼성생명·현대·한화생명 PDF 비공시) / 36_irr Q1·Q3 ~85(시나리오표 원천부재) / IRR 직접형 15(별도 schema 보류). ⚠️ 이 "정당" 결론은 2026-06-12(a)에서 OVERTURN(분절표·라벨변형 = 파서 갭).

inbox `phase2_loaded` **resolved**. **V3 시장위험 검증 한 사이클 완결**: 룰 구현 → 골든 → 1차적재 → 결손census → Phase-2 PDF추출 → 재검증 RED 0. 추가 적재 시 동일 게이트 재실행.

## 2026-06-09 (c) — 시장위험 item36–46 1차 적재 검증 통과 (RED 0)

parser가 item36–46 1차 적재 → `validate_kics_disclosure.py` (19_market/36_irr 활성) 재실행:
- **19_market: 163 GREEN / 221 SKIP / 0 RED**
- **36_irr: 42 GREEN / 17 YELLOW / 325 SKIP / 0 RED**
- 게이트 RED=2 불변(기존 KR0010 OCR).

**단위 정합 확인** (앞 (b)의 회신 요청 해결): item36–40을 억원(세부표 백만원 ÷100) 적재한 게 맞음 — 19_market GREEN 163건이 item19(억원)와 일치. YELLOW 17(36_irr)은 0.0~3.4% 미세편차(`classify_diff`). 게이트 무관. SKIP은 미적재 분기 — parser 적재 계속 시 자동 GREEN. parser inbox 회신: `inbox/parser/20260609T0300Z__validation__MULTI_ALL__market_risk_loaded_pass.md`.

## 2026-06-09 (b) — V3 시장위험 룰 19_market + 36_irr 구현 (8_life 복제)

parser inbox(`market_risk_rule`, `market_irr_rules_19_36`) 요청 → `src/solvency/validation/kics_json_rules.py`에 2룰 구현. 정본: `docs/agents/kics-market-risk-decomposition.md`.

- **`19_market`**: `item19 = sqrt(V'·M·V)`, V=[36–40](금리·주식·부동산·외환·자산집중). `MARKET_M` 5×5(대각1.0/외환-주식 −0.25/자산집중 행열 0/그외 0.25). `_diversified_sqrt` 재사용. **부분결측 허용**(없는 하위=0; item19 또는 36–40 전부 결측 → SKIP). dynamic tol `max(eff_tol, 5%·expected)`, IMAGE_OCR 10.0 승계.
- **`36_irr`**: `item36 = √[max(R상승,R하락)² + max(R평탄,R경사)²] + R평균회귀`. R=base(41)−시나리오순자산(43/44/45/46), 평균회귀=41−42(signed). 41–46 중 결측 → SKIP.

**골든 3/3 정확 일치**: 19_market 흥국 FY2023_Q1 sqrt(V'MV)=813,201백만=8,132억(=item19) / 36_irr 흥국 157,128(공시 157,127) / 현대 322,767(공시 일치).

**상태**: item36–46 적재가 parser 진행 중 → 신규 2룰 **전사 SKIP**(게이트 미반영). RED=2 불변(회귀 없음). 적재 후 자동 활성. 단위: 룰은 item36–40을 억원(=item19 동일단위) 가정 — parser 적재 단위 회신 대기. inbox 2건 answered.

## 2026-06-09 (a) — consolidator 스크립트화 (mechanical=script, judgment=agent)

운영 개선 #2: validator JSON → inbox 메시지 변환을 에이전트/수동 → **스크립트** [`scripts/consolidate_inbox.py`](../scripts/consolidate_inbox.py)로.

- **왜**: smoke-test에서 emit(consolidator)·eval을 에이전트로 돌리니 1 finding에 208k 토큰. 변환은 기계적이라 에이전트 낭비. 원칙 **에이전트=판단·신규성, 스크립트=기계** 적용.
- **consolidate_inbox.py**: continuity validator(`csm_continuity_validation.json`) findings → `inbox/parser/` reparse 메시지(값 시계열 + 내부 closing-identity precompute 포함). **idempotent** — `parser/`·`_resolved/`에 같은 (회사·기간·토픽) 있으면 skip. 신규 validator는 `VALIDATORS` 리스트에 핸들러 추가. waterfall must_reparse 버킷은 당시 비어 미적용(항목 생기면 추가 — untested 코드 안 씀). → 06-12(b)에서 RS/waterfall 핸들러 선배선.
- **루프**: validator 실행 → `python scripts/consolidate_inbox.py` → 사람이 "inbox 확인해라". (driver 상설화는 안 함 — 사람 킥으로 충분, owner 결정.)
- **배선**: `inbox/README.md` "consolidator 향후 작업" → 스크립트 명시; validation 프롬프트 §3.0 route 분류를 mechanical(script)/judgment(agent)로 분리.
- **inbox 정리**: parser fix로 해결된 3건(흥국 FY2023·코리안 FY2024·코리안 2024.1Q) + 스모크 데모 1건 → `_resolved/`. `parser/`에 live finding 9개만 남김. 폐기된 probe `_seed_continuity_inbox.py` 제거.

## 2026-06-09 — V4 QOQ_DELTA_WARN 구현 (시계열 anomaly) + parser inbox

V4 `QOQ_DELTA_WARN` 소비자 코드 구현 (`validate_master_tables.py` 4번). spec(`config/qoq_thresholds.yaml`)의 CSM 항목 대상:
- 누적 항목(신계약/이자부리/상각) → **YoY**(전년 동기 YTD 대비). net-quarterly QoQ는 분기 계절성으로 노이즈 폭발(645건) → YoY로 계절성 상쇄.
- 시점 항목(기말 CSM) → QoQ. floor 50억(작은 분모 % 폭발 제거).
- **PL 손익(보험손익/투자손익/당기순이익) 제외**: 시장·금리 민감 본질적 고변동 + spec items 미등록. (임의 추가했다가 590건 노이즈 → 철회.)
- YELLOW(다운스트림 차단 안 함). 전체 → `data/_derived/qoq_warn.json` (sign_flip 플래그 포함).

**결과**: 193건 YELLOW (신계약 69 / 이자부리 59 / 상각 51 / 기말 14). 대부분 사업변동. **진짜 데이터 의심 = 이자부리 부호반전 3건** (양수→음수): 동양 2025.4Q(1,134→−2,140)·교보 2025.3Q(3,242→−5,290)·코리안리 2025.2Q(318→−116).

→ parser inbox: `inbox/parser/20260609T0200Z__validation__MULTI_2025__qoq_interest_signflip.md` (route: blind_spot, 이자부리 부호 raw 확인 요청).

**교훈**: QoQ anomaly는 임계·기준(net/YoY/raw) 선택이 신호품질을 좌우. flow는 YoY, stock은 QoQ, 고변동 손익은 제외. 부호반전이 단순 %급변보다 강한 데이터-오류 신호.

## 2026-06-08 — MASTER_COVERAGE 룰 신설 (hole을 SKIP으로 숨기던 사각지대 보강)

**검증 결함 인정**: closing/pl_bridge/crosscheck가 항목 None을 전부 SKIP 처리 → 거대한 skip(pl_bridge 456 / crosscheck 227) 뒤에 "있어야 하는데 없는" 데이터(hole)가 숨어 있었음. parser census(WRONG vs HOLE 분리)가 먼저 짚음 — validation이 했어야 할 일.

신규 룰 `MASTER_COVERAGE` (`validate_master_tables.py` 0번): active 회사(핵심항목 ≥7분기)의 빈 분기 = hole. **2024+ = real hole**, 2023 = known(사이트 비노출), <7분기 = structural(외국계·소형 미공시, 제외).

**검출**: real hole(2024+) **4건** / 2023 known 40 / struct 18.
- **미래에셋생명 CSM 2025.2Q·3Q·2026.1Q** — `CSM상각` None (2025.1Q는 −483.6 있음). closing identity가 skip하던 것.
- **롯데손해 PL 2025.2Q** — `생명장기손익` None (1Q·3Q는 있음). pl_bridge가 skip하던 것.
→ **parser 데이터 채움 대상**. 둘 다 절댓값 검증을 통과한 게 아니라 *검증 자체를 skip*당한 케이스.

검증 철학 갱신: "값이 틀린 것(WRONG)"뿐 아니라 **"값이 없는 것(HOLE/coverage gap)"**도 1급 검증 대상. skip은 침묵이 아니라 분류돼야 함.

## 2026-06-08 — 빌드→검증 통합 (build_root_masters 자동 선행)

`validate_master_tables.py`가 검증 전 `build_root_masters.py`를 자동 선행(idempotent). 빌드 누락으로 "고쳤는데 검증에 안 보임" 문제 구조적 차단(아래 06-07(h) 교훈). `--no-build`로 끔. 회귀 명령: `python scripts/validate_master_tables.py` (빌드+검증 한 방).

## 2026-06-07 (h) — 흥국 해소 (빌드 누락이 원인) + 빌드 체인 교훈

흥국화재 "고쳤다"는데 3번 재검증해도 루트 `CSM_waterfall.json`에 변화 0 → **빌드 한 단계 누락**. 체인: `csm_waterfall_master_diag.json`(소스) → `build_root_masters.py` → 루트 `CSM_waterfall.json`. parser가 **diag는 22:13에 제대로 고쳤는데** **루트는 21:31 옛것** — `build_root_masters.py`를 안 돌려 미반영. validation이 빌드 실행 → 루트 갱신 → **흥국 완전 해소** (복붙 6→0 / spike 4→1 / cont 21→14).

**⚠️ 운영 교훈 (핸드오프 필수)**: parser가 소스(diag/viz)를 고쳐도 **`build_root_masters.py` 재실행 전엔 루트 마스터에 반영 안 됨**. mtime 비교(소스 > 루트)로 빌드 누락 탐지 가능.

**빌드가 드러낸 새 건**: 롯데손해 2025.4Q wf CSM상각 −980(거의 0, 이상치) → crosscheck +99.5% RED. 롯데 FY25 양식 이슈(V7)와 연관 의심 → parser.

## 2026-06-07 (g) — CSM_PLAUSIBILITY 룰 신설 (closing identity 사각지대)

사용자가 흥국화재 2025.4Q 기말 CSM이 **34.1억**(직전 26,693억)으로 비정상 폭락한 걸 지적. closing identity는 **내부 산술 합산만** 검증 → 가정조정(−28,929.9억)이 폭락을 흡수해 closing이 우연히 닫혀 통과(0F). **절댓값 plausibility 검증 부재가 validation 갭**.

신규 룰 `CSM_PLAUSIBILITY` (`scripts/validate_master_tables.py` 1b):
- **복붙(dup)**: 같은 회사 내 서로 다른 분기의 기말 CSM이 소수점까지 동일 → 복붙 의심.
- **기말 QoQ 폭변(spike)**: 기말 CSM `|ΔQoQ| > 50%`.
- **연속성(cont)**: `FY[t] 각 분기 기초 CSM = FY[t-1].4Q 기말`. tol max(0.5%·|전년말|, 2억). 2023은 SKIP. — 사용자 지적으로 추가, 가장 근본적인 sanity.

**연속성 검출 21건**:
- 🔴 진짜 오류: **메트라이프 2025.4Q 기초 48,134 = 2024말 24,067 ×2 (이중계상, KB라이프형)**, 케이디비생명 2025.1~4Q 기초 복붙, 흥국화재 2025.2Q·3Q 기초 복붙.
- 🟡 회색지대 (IFRS17 기초 재작성 가능): 삼성생명 2024 Δ−1,452·신한라이프·메리츠·에이비엘·푸본 작은 Δ; 교보(±2,905/+5,659)·KB라이프(+1,622)는 parser 확인.
- severity 권고: 배수/큰 Δ = RED, 작은 Δ = YELLOW.

**dup/spike 검출**: 6 dup + 4 spike, 케이디비생명·흥국화재 집중.
→ **parser 전달 대상**: 케이디비생명·흥국화재 2025 CSM_waterfall 재추출 + 메트라이프 2025.4Q 기초 2배. closing 0F였어도 절댓값이 틀린 케이스.

## 2026-06-07 (f) — DB손해·KB손해 별도/연결 fix → PL_BRIDGE 31F→16F

parser가 별도/연결 LOB 레그 fix를 DB손해·KB손해로 확장 → **2024+ 보험손익 fail 10건 완전 해소** (DB손해 5 + KB손해 5). 진단(DB=ΣLOB 결손 / KB=ΣLOB 과대, LOB 내부는 정합)이 정확히 별도/연결 레그 오선택이었음.

**PL_BRIDGE 31F → 16F**. 잔여: 2023 분기 11건(사이트 비노출) + 2024+ 5건(KB라이프 2024.1Q +1,136 / 악사손해 2024.4Q +3,483 / 흥국화재 2025.1Q −714·2025.4Q +1,684·2026.1Q +968).

**dual-form의 정당성 (사용자 확인 2026-06-07)**: 보험손익은 통상 `종목별 합 − 기타사업비`(adj)지만 일부 회사·분기(흥국 2024.4Q, KB 등)는 종목별 합산에 기타사업비가 이미 녹아있어 bare(`= ΣLOB`)로 닫힘. dual-form은 이 케이스를 통과시키려는 의도된 설계 → bare로만 통과하는 분기는 정상, flag 안 함. (앞서 "숨은 275억 LOB 결손/dual-form 허점" 진단·"회사별 form 고정 flag" 제안 철회.) 단 한화손보→삼성화재 LOB 별도/연결 교훈(§1.5)은 유효 — 과잉진단 금지.

## 2026-06-07 (e) — 보험손익 잔차 = LOB 별도/연결 레그 오선택 (진단 가이드 정정)

삼성화재 2026.1Q +2,067, 한화손보 2025.2~4Q를 "기타영업수익 누락"으로 진단했으나 **2건 연속 오진**. parser FS-API 검증 결과 진짜 원인 = **ΣLOB 별도/연결 레그 오선택**:
- 별도(OFS) 기준 회사는 FS-API상 **기타영업수익 구조적 0**.
- parser `pmin`(최소합계=별도) 휴리스틱이 **재보험 레그에서 뒤집힘**(연결이 그룹내부 재보험 상계) → 기준 불일치 → ΣLOB 결손.
- 분기마다 별도/연결 대소가 달라 같은 회사도 일부 분기만 fail.

parser fix(별도 보험수익 anchor + cost/재보험 레그 same-block `first_from`) → **삼성화재 2026.1Q + 한화손보 2025 둘 다 해소**. pl_bridge **36F → 31F**. 진단 가이드 §1.5에 박음: 보험손익 잔차는 "기타영업수익 누락"이 아니라 **LOB 별도/연결 기준 일관성부터 의심**.

## 2026-06-07 (d) — CSM_CROSSCHECK 진짜 2건 해소 → 0F

진짜 의심 2건이 서로 다른 원인이었음 ("재보험 혼입" 가설은 둘 다 빗나감):
- **KB라이프 2023.4Q — wf 버그 (parser fix)**: 사업결합(KB생명+푸르덴셜)으로 기초가 2줄. 전기 블록 기말이 사업결합 전 기초와 같아 값연속성 검사 통과 → wf가 당기 블록(−283,905)에 전기 블록(−146,769)을 합산해 **정확히 2배**(−430,674). closing identity는 비례 2배라 우연 통과, crosscheck만 잡음. parser `_is_prior_header()`(`['구분','전기']`) 추가 → KB라이프 13분기 OK, 상각 −2,839.1억(=pl ✓).
- **코리안리 2025.4Q — validation 룰 스코프 버그 (validation fix)**: 파서 정확. 재보험사 PL은 발행계약을 `원수CSM상각(4) + 수재CSM상각(4-1)`로 분리(41,154+32,210=73,364=wf 상각). crosscheck 룰이 PL 수재(4-1)를 빼먹어 false-positive → `p = 원수CSM상각 + (수재CSM상각 or 0)`로 수정(출재 9-1 제외). §1.2 반영.

**결과**: CSM_CROSSCHECK **66P/2M/2F → 68P/2M/0F**. CSM_waterfall 도메인(closing 0F + crosscheck 0F) 완전 정합. 잔여 MINOR 2건(에이비엘 6.9%·흥국화재 6.4%)은 경고만.

## 2026-06-07 (c) — CSM_CROSSCHECK tol 3단계 정책

`CSM_CROSSCHECK`는 **서로 다른 DART 표**(PL 보험수익 구성 vs CSM 변동표) cross 비교라 표간 반올림·집계 차이로 수% 편차가 구조적. **3단계 tol** 도입 (§1.2):
- **OK**: `|s| ≤ max(5%·|pl|, 300백만)` · **MINOR** (경고, pass): `5% < |s| ≤ 10%` · **RED**: `|s| > 10%` → parser loopback.

결과: crosscheck **9F → 66P / 2M / 2F**. 진짜 불일치(KB라이프 51.7%·코리안리 78.3%)만 RED, 경계 7건 흡수. 진짜 2건과 경계(최대 6.9%) 갭이 51%+로 커서 10% 임계 안전.

## 2026-06-07 (b) — CSM_waterfall closing 완전 해소 (parser 재추출 후 재검증)

parser가 CSM_waterfall 측정요소 변동표 재추출 → 재검증 (`scripts/validate_master_tables.py`):
- **CLOSING_IDENTITY: 40F → 0F** (299P / 0F / 6S). 23사 × 13분기 전부 `기초+신계약+이자+가정+상각 = 기말` 정합. 🎯
- **CSM_CROSSCHECK: 20F → 9F** (61P / 9F / 224S). 잔여 9건은 (c) tol 3단계로 정리(진짜 의심 2건 KB라이프·코리안리 + 경계 7건).

## 2026-06-07 — V8 마스터테이블 검증 소비자 코드 첫 실행 + 룰 정식화

사용자가 (거의) 전사·전분기 마스터테이블 구축 완료 → V8 소비자 코드 `scripts/validate_master_tables.py` 작성·실행. 입력: `pl_breakdown_master.json` (백만원, 32사×13분기) + `CSM_waterfall.json` (억원, 23사×13분기).

**3개 룰 첫 실행**: CLOSING_IDENTITY 218P/40F/41S · PL_BRIDGE(8단) 2023P/36F/469S · CSM_CROSSCHECK 33P/20F/190S.

**룰 정식화 (오탐 제거)**:
- **보험손익 dual-form**: `보험손익 = ΣLOB`(손보) 또는 `ΣLOB + 기타영업수익 − 기타사업비용`(삼성화재 등). 둘 중 하나 닫히면 PASS → 손보 bare-close 오탐 ~19건 해소.
- **영업이익 abs floor 200→600백만**: 0근처 회사(KDB 등) 과민 방지.
- **CSM_CROSSCHECK 4Q-only**: pl·wf 모두 YTD 누적 → 1~3Q 분기배분 노이즈 제거. 136F→20F.

**parser 1차 수정 반영**: item16 음수 7건 abs 정규화, item19 account_nm fallback 277셀 포착, item17 net 통일.

**남은 fail**: CSM_waterfall 도메인 60건(closing 40F + crosscheck 20F) = parser 재추출 · PL 잔여 36F(대부분 known FY2023 HTML fallback + 한화손해 dual 미닫힘).

회귀 명령: `python scripts/validate_master_tables.py`.

---

## Archive (pre-2026-06)

> 1줄 요약. 전문은 git log/blame. dead-end/폐기 근거는 프롬프트에 보존(SEGMENT cross-source 폐기·PL_BRIDGE §1.5 / 메리츠 보종 영구SKIP §1.2 / off-year→continuity §3.0 / dual-form 과잉진단 금지 §1.5 / 빌드체인 gotcha §3.0). K-ICS RED 진행 + 분기별 batch 원문은 `docs/claude-changelog.md` Historical archive(2026-05-24/25, 2026-04-26~28).

- 2026-06-01 (밤) — SEGMENT cross-source 폐기 + PL_BRIDGE_DART_INTERNAL 신설(§1.5, DART 자기완결 10등식, 삼성화재 2025.4Q PASS) → V8
- 2026-06-01 (밤 b) — 메리츠 CSM waterfall: breakdown 영구 SKIP + CSM_AMORT cross-table 신설
- 2026-06-01 (밤 c) — 통합 마스터테이블 입력 계약 + CSM_CROSSCHECK 확장
- 2026-06-01 (저녁) — 🚨 history 재빌드 off-by-one-year 회귀 발견 + check 도구 cohort 가드
- 2026-06-01 — V7 history-wide check 도구(`check_nb_csm_history.py`, 13Q×9사) + systemic 이슈 3건 발견(2025.2Q cohort-wide / DB 2025.2-4Q 부호 반전 / 미래에셋 ↑↓ 교대); FY24 widespread 6/7 OK(롯데 FY25 의존); 한화 V2 fallback retire 가능
- 2026-06-01 — V7 6/7 OK 회복 (parser 별도·당기 disambiguation + 소계 이중계상 fix)
- 2026-05-31 — V7 `NB_CSM_DART_VS_IR_ANNUAL_SUM` 룰 + convention-aware check 도구
- 2026-05-31 — NB CSM multiple validator: period-aware + fallback flagging (V2), retry max 8→5
- 2026-05-31 — QoQ threshold registry v1 (`config/qoq_thresholds.yaml`, V4 spec)
- 2026-05-31 — DART ↔ IR cross-source 3개 룰 추가 + IR-side input 계약 §1.4 (V1 spec)
- 2026-05-30 — Validation prompt 초안 (R1–R10, IFRS17 CSM 룰셋, `QOQ_DELTA_WARN`, retry loop max=5)
- 2026-05-29 — Plausibility gate (`MAX_PLAUSIBLE_MULTIPLE=60`) + Samsung Life 사망 misparse fix
- 2026-05-25 — K-ICS rules 9 + 10 추가 + RED reduction 419→2 (KR0010 OCR 잔여) + unit-hint mismatch auto-detect + Tier-2 utilization reconcile
- 2026-05-24 — K-ICS JSON validation rules doc + pipeline gate; KICS-VALIDATE harness; R7 matrix fix
- 2026-04-26 → 2026-04-28 — Foundational validation

세부 K-ICS RED 진행 + 분기별 batch 원문은 [`docs/claude-changelog.md`](claude-changelog.md) Historical archive에 압축 보존. 본 파일은 validation-relevant 분리본.
