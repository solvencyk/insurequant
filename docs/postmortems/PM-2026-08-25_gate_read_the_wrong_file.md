# PM-2026-08-25 — 게이트가 배포본이 아닌 파일을 검사했다 (불변식 1번 위반)

> 상태: `closed` (잔여 UH-13 · UH-14)
> 규격: `.claude/skills/incident-postmortem/SKILL.md` · 색인: [`README.md`](README.md)
> 재현 스크립트: `scripts/_probes/probe_20260825_*.py` (7종)

## 0. 한 줄

`CLAUDE.md` 불변식 1번("게이트가 검사하는 파일 = 사용자가 보는 파일")이 **명문화된 채로
깨져 있었다.** 라이브 배포 HTML 4종이 fetch 하는 `.json` **16개 중 6개를 어떤 검사기도 읽지
않았고**, 그 위에 "읽기는 하는데 배포본이 아니라 파서 중간산출물을 읽는" 축이 셋 더 있었다.

---

## 1. 무엇이 통과했나

**게이트는 전부 초록이었다.** 막는 룰이 없어서가 아니라 **보는 범위**가 잘못돼 있어서다 —
false-green 중에서도 가장 조용한 형태다.

### 1a. `validate_master_tables.py` 의 PL 축이 죽은 사본을 검사했다

```python
PL_PATH = "data/dart/viz/pl_breakdown_master.json"   # 파서 중간산출물
WF_PATH = "CSM_waterfall.json"                       # 배포본
```

CSM 축은 배포본을 보는데 **PL 축(COVERAGE · PL_BRIDGE · CSM_CROSSCHECK)만 상류를 봤다.**
실측(`probe_20260825_simulate_pl_source_reaim.py`):

| 지표 | 실측 |
|---|---|
| 게이트가 읽던 `pl_breakdown_master.json` | 7,391셀 / 302 (회사,분기) |
| 배포본 `PL_breakdown.json` | 8,698셀 / 356 (회사,분기) |
| **배포본에만 있어 PL 검사 3종이 못 보던 셀** | **1,307 (15.0%)** |
| 게이트가 찍던 `HOLE-PL (통째)` | **24건 → 24/24 전부 phantom** |
| 게이트가 찍던 `crosscheck fail` | **1건(BNP 2025.4Q) → phantom** |
| 재조준 후 새로 드러난 `PL_BRIDGE` 실패 | **16건** |

즉 게이트가 **아무도 안 보는 파일**을 상대로 hole 과 fail 을 찍고 있었고, 진짜 배포본의
1,307셀은 PL 항등식·CSM 교차대조를 **한 번도 안 거쳤다.** 그리고
`tests/test_master_tables_golden.py` 가 그 상태(`24PL`, `1F`)를 골든에 박아 굳혀 놨다.

### 1b. 라이브가 쓰는데 아무도 안 읽던 파일 6개

런타임 추적(`probe_20260825_trace_validator_reads.py` — `builtins.open` / `Path.read_*` 을
감싸고 검사기를 실제로 돌려 열린 경로를 기록)으로 확정했다:

| 파일 | 쓰는 화면 | 읽는 검사기 |
|---|---|---|
| `NB_CSM_multiple.json` | index.html · IFRS17.html (CSM 버블맵) | **없음** |
| `data/dart/viz/csm_amort_schedule.json` | IFRS17.html | **없음** |
| `data/dart/viz/csm_waterfall_history.json` | IFRS17.html | **없음** |
| `data/dart/viz/insurance_pl_breakdown.json` | IFRS17.html | **없음** |
| `kics_tier1_utilization.json` | K-ICS.html | **없음**(값 축) |
| `kics_tier2_utilization.json` | K-ICS.html | **없음**(값 축) |

tier1/tier2 가 특히 교활하다. `validate_data_contract.ARTIFACTS` 는 **배포 경로를 등록해
두었고 그 주석은 "게이트가 검사하는 대상 = 사용자가 보는 파일, 이 규칙을 여기서 강제한다"
라고 적혀 있다.** 그런데 값을 로드하는 `_load_tier()` 는
`output/tier{1,2}_utilization/*.json` 을 읽는다 — mtime·provenance 는 배포본을 보고
**숫자는 상류를 본다.** 등록만으로 검사가 되는 것이 아니다.

그 결과 **실제로 화면이 틀렸다**(같은 분기, 같은 한도, 분자만 0):

| 파일 | 회사 | 배포본(화면) | 빌더 산출물(게이트가 검사) |
|---|---|---|---|
| tier1 | 하나손해보험 | **0.0%** | 100.0% (`issued` 0 vs 1,000억) |
| tier2 | IBK연금보험 | **0.0%** | 22.2% (`subordinated` 0 vs 1,597.3억) |
| tier2 | 아이엠라이프생명보험 | **0.0%** | 40.6% (`hybrid` 0 vs 948.8억) |
| tier2 | 하나손해보험 | **0.0%** | 13.2% |

### 1c. 왜 아무도 몰랐나

세 층의 매니페스트가 이미 있었는데 **전부 이 질문을 안 물었다**:

- `test_push_gate_wiring.py::WIRED` — "어떤 **게이트**가 도는가" (파일 단위)
- `test_push_gate_wiring.py::DATA_CONTRACT_CHECKS` — "게이트 안 어떤 **검사**가 도는가"
- `test_rule_coverage_manifest.py` — "어떤 **항목**이 어떤 룰에 검사받는가" (K-ICS 한정)

**"그 검사가 어떤 파일을 읽는가"를 강제하는 층이 없었다.** 게이트를 아무리 촘촘히 배선해도
입력이 엉뚱하면 전부 헛돈다.

---

## 2. 어떤 룰이었으면 잡았나

### R-1 `LIVE_ARTIFACT_READERS` 매트릭스 (테스트 층)

- **입력**: `origin/main` 의 배포 HTML 4종에서 정규식으로 뽑은 `.json` fetch 목록
- **판정**: `fetched - declared ≠ ∅` → FAIL / `declared - fetched ≠ ∅` → FAIL(죽은 사본 검사)
- **보강**: 선언한 검사기의 소스에 그 경로 리터럴이 실제로 있어야 한다(선언만 하고 안 읽는 것 차단)
- **severity**: 테스트 FAIL = push 차단 (훅의 오프라인 묶음)

### R-2 `DEPLOYED_VS_UPSTREAM` 짝 규칙 (테스트 층)

- **입력**: (배포본, 중간산출물, 배포본을 읽어야 하는 검사기) 삼중항
- **판정**: 해당 검사기 소스에 배포본 경로가 없으면 FAIL. 추가로 상류 경로가
  `load_long|json.load|read_text|open` 과 같은 줄에 있으면 FAIL(주석은 허용, 로드는 금지)
- **severity**: FAIL = push 차단

### R-3 라이브 아티팩트 값 룰 (게이트 층)

| 룰 | 판정식 |
|---|---|
| `NB_RATIO_IDENTITY_{연누계,당분기}` | `배수 == 신계약CSM / 월납월초보험료` (**두 축 모두**) |
| `NB_YTD_QUARTERLY_{신계약CSM,월납월초보험료}` | `당분기 == YTD(Q) - YTD(Q-1)` (1Q 는 `== YTD`) |
| `NB_VS_WATERFALL` | `NB.신계약CSM_연누계 == CSM_waterfall 항목2` (tol 1%) |
| `NB_CENSUS_MISSING` | 마스터에 신계약CSM 이 있는 (회사,분기)가 NB 배포본에 없음 |
| `AMORT_{YEARLY,BUCKETS}_SUM_NE_TOTAL` | `Σ(연차 버킷) == total` (tol 0.5%) |
| `AMORT_TOTAL_VS_CLOSING_CSM_{SCALE,BAND}` | `\|total / 기말CSM\|` ∉ [0.05, 20] = SCALE / ∉ [0.6, 1.4] = BAND |
| `AMORT_STATUS_NOT_OK` · `AMORT_CENSUS_MISSING` | status ≠ ok / 마스터 대비 결측 |
| `HIST_STAGE_IDENTITY` | `opening+nb+interest+assumption+amortization == closing` (tol 0.1%) |
| `HIST_MASTER_DRIFT` | `snapshot/100 == master` 셀 단위 (tol max(2억, 1%)) |
| `HIST_CENSUS_MISSING` · `HIST_NOT_IN_MASTER` | 양방향 census |
| `INSPL_CSM_AMORT_{SCALE,BAND}` | 표 `보험계약마진상각` 합계 vs PL 마스터 `원수CSM상각` |
| `INSPL_CENSUS_MISSING` · `INSPL_STATUS_NOT_OK` | census / status |
| `TIER_DEPLOYED_VALUE_DIFFERS` | 같은 분기에서 배포본 `utilization_pct` == 빌더 산출물 값 |
| `TIER_DEPLOYED_QUARTER_STALE` | 배포본 `quarter` == 빌더 최신 산출물 `quarter` |
| `TIER_UTILIZATION_IDENTITY` | `utilization_pct == min(100, 분자/한도×100)` — **캡은 owner 결정** |
| `TIER_DEPLOYED_MISSING_COMPANY` · `TIER_ARTIFACT_UNREADABLE` | census / 파싱 |

- **severity**: `data/_gold/live_artifact_baseline.json` 에 **건별 등재된 것 = YELLOW**(매 실행
  사유와 함께 인쇄), **등재에 없는 것 = RED → exit 2 → push 차단**

### R-4 `pl_bridge NEW` (게이트 층)

- 재조준으로 처음 드러난 26건을 `data/_gold/pl_bridge_baseline.json` 에 건별 등재
- `SUMMARY` 에 `pl_bridge:...NEW` 카운트 추가 → 등재 밖 실패가 하나라도 생기면 골든이 움직여
  push 차단

---

## 3. 그 룰이 지금 어디에 배선됐나

| 룰 | 배선 위치 | scope | exit code 반영 |
|---|---|---|---|
| R-1 | `tests/test_push_gate_wiring.py::test_every_live_fetched_artifact_has_a_declared_reader` · `::test_declared_reader_actually_references_the_artifact` | 배포 HTML 4종 전체 (origin/main) | ✅ 훅 4단계 오프라인 테스트 |
| R-2 | `tests/test_push_gate_wiring.py::test_gate_reads_the_deployed_artifact_not_the_upstream_copy` | 배포/상류 짝 4쌍 | ✅ 동일 |
| R-3 | **`scripts/validate_live_artifacts.py`** (신설) → `scripts/prepush_check.py` **1c 도메인 게이트** | 전 회사·전 분기 | ✅ `n_dom` → `blocked` |
| R-4 | `scripts/validate_master_tables.py::_report_pl_baseline` → `SUMMARY` → `tests/test_master_tables_golden.py` | 전 회사·전 분기 | ✅ 훅 4단계 오프라인 테스트 |
| 소스 재조준 | `scripts/validate_master_tables.py::PL_PATH = "PL_breakdown.json"` | PL 축 3검사 | ✅ 골든 경유 |

`validate_live_artifacts` 는 `tests/test_push_gate_wiring.py::WIRED` 에 사유와 함께 등재됐다
(등재 안 하면 `test_every_validator_is_declared` 가 막는다 — 실제로 이번에 막았고, 그래서
등재했다).

### 이빨 검증 (변이시험)

`scripts/_probes/probe_20260825_mutate_wiring_matrix.py` — 변이 5종 **5/5 발화**,
실행 후 워킹트리 복원 확인(`복원 후 재실행 exit=0`):

| 변이 | 결과 |
|---|---|
| M1 선언 삭제 (`NB_CSM_multiple.json` 줄 제거) | ✅ FAIL |
| M2 소스 되돌리기 (`PL_PATH` → 중간산출물) | ✅ FAIL |
| M2b 상류를 직접 로드 (배포본 리터럴은 주석에 남긴 채) | ✅ FAIL |
| M3 거짓 선언 (읽지 않는 검사기를 reader 로 선언) | ✅ FAIL |
| M4 화면에 새 파일이 붙음 (선언 없음) | ✅ FAIL |

---

## 4. documented exception

**두 개의 baseline 등재부.** 둘 다 **통째 skip 이 아니라 건별 등재**이고, 매 실행 사유와 함께
인쇄되며, 고쳐지면 게이트가 `BASELINE STALE` / `FIXED?` 로 알려준다.

### 4a. `data/_gold/pl_bridge_baseline.json` — 26건

| class | 건수 | 내용 |
|---|---|---|
| `pre_existing` | 10 | 재조준 전에도 실패하던 항목 |
| `basis_mix_csm_amort` | 5 | `원수CSM상각` YTD 누계 vs 당분기 혼입 (동양생명·KDB·ABL) |
| `lob_sum_gap` | 5 | `보험손익 ≠ ΣLOB` (DB생명·DB손해·메리츠×2·흥국화재) |
| `sub_leg_gap` | 3 | `생명장기손익 ≠ 원수+재보험` (교보라플·BNP×2) |
| `copied_cell` | 3 | **에이비엘생명 2024 Q1~Q3 `원수CSM상각` 이 2025 Q1~Q3 와 1원도 다르지 않다** |

### 4b. `data/_gold/live_artifact_baseline.json` — 1,086건

| 룰 | 건수 | 사유 요지 |
|---|---|---|
| `HIST_MASTER_DRIFT` | 933 | 정적 스냅샷 drift (아래 UH-13) |
| `HIST_STAGE_IDENTITY` | 41 | 스냅샷 자체 항등식 파탄 |
| `NB_CENSUS_MISSING` | 31 | 배포본이 한 분기 뒤처짐(28건이 2026.2Q) |
| `AMORT_{YEARLY,BUCKETS}_SUM_NE_TOTAL` | 44 | 장기 꼬리 버킷 누락(16~30년+ 컬럼 미추출) |
| `HIST_CENSUS_MISSING` | 14 | 스냅샷에 없는 14사 |
| `INSPL_CENSUS_MISSING` | 7 | 원표 패널에 없는 7사 |
| `AMORT_STATUS_NOT_OK` | 5 | empty 4 · partial 1 |
| `AMORT_TOTAL_VS_CLOSING_CSM_BAND` | 4 | ratio 0.28~0.57 (PAA 제외분 가능성, 미확인) |
| `TIER_DEPLOYED_VALUE_DIFFERS` | 4 | **§1b 의 라이브 오표시** |
| 기타 | 3 | NB 부호반전 1 · INSPL 파싱사고 1 · INSPL band 1 |

**승격 조건은 등재부의 `_promote` 필드에 박혀 있다**: (1) 고쳐지면 그 줄 삭제,
(2) 등재 밖 신규는 **처음부터 RED**, (3) **기한 2026-10-31** — 그때까지 남은 줄은 legit
레지스트리로 승격하거나 RED 로 되돌린다(무기한 방치 금지), (4) `csm_waterfall_history.json`
은 예외적으로 **파일 자체의 처분**이 승격 조건이다.

### 4c. 우리 룰의 결함으로 판정해 **등재하지 않고 룰을 고친 것**

`TIER_UTILIZATION_IDENTITY` 초안이 `utilization_pct == 분자/한도×100` 이었는데 5사가 실패했다
(NH농협손해 192.9% 등). 데이터가 아니라 **룰이 틀렸다** — 소진율은 owner 결정으로 100 에서
잘린다(memory `reference_kics_capital_tiering`). `min(100, …)` 으로 고쳐 5건이 사라졌다.
**baseline 은 룰 결함을 덮는 데 쓰면 안 된다.**

---

## 5. 미배선 잔여 + 후속 티켓

| ID | 내용 | 상태 |
|---|---|---|
| **UH-13** | **`data/dart/viz/csm_waterfall_history.json` 은 아무도 재생성하지 않는 정적 스냅샷이다.** 선언 빌더 `scripts/ifrs17_batch_historical.py` 는 2026-06 에 아카이브됐다. 마스터 대조 1,581셀 중 **933건(59.0%) drift**, 최대 Δ 43,852억(삼성화재 2023.3Q closing). IFRS17.html 이 그 값을 그린다. 검사는 걸었지만 **파일의 처분이 안 정해졌다** — drift 등재는 "스냅샷이 낡았다"의 박제이지 값의 승인이 아니다 | 발주 `inbox/parser/20260825T1125Z__validation__MULTI__live_viz_artifacts_unchecked.md` §A. 권고: **마스터 파생으로 교체**(그러면 drift 가 구조적으로 0) |
| **UH-14** | **R-1/R-2 는 소스 문자열 검사다.** 정본 증거는 런타임 추적(`probe_20260825_trace_validator_reads.py`)인데, 그건 `validate_data_contract` 한 번 도는 데만 수십 초라 매 push 묶음에 넣지 않았다. 지금 매트릭스는 "경로 리터럴이 소스에 있다"까지만 강제한다 — 리터럴은 있는데 그 코드경로가 죽어 있으면 통과한다 | 검토 방향: 추적 프로브를 **주 1회 또는 릴리스 전** 수동 실행으로 규정하거나, 검사기별 캐시된 read-manifest 를 산출물로 남겨 대조. 지금은 변이시험 M2b(상류 직접 로드)가 가장 흔한 회귀형을 덮는다 |

**해소된 것**: 없음(이 PM 이 신설이다). **없음 명시**: R-1~R-4 는 전부 배선됐고 이빨 검증됐다.

---

## 6. 반증한 것 — 오케스트레이터 census 의 오탐 1건

발주 시점 census 는 문자열 리터럴 기반이라 **동적 경로 조립을 놓쳤다.** 직접 확인한 결과:

- ❌ **`equity_composition.json` 이 라이브에서 404** — **거짓.** `origin/main:IFRS17.html`
  에서 그 이름이 나오는 곳은 **131행의 HTML 주석 하나뿐**이고, "과거 스키마용 죽은 코드는
  이번에 진짜 삭제함"이라고 적혀 있다. fetch 하지 않는다. 티켓 불요.
- ⚠️ `data/dart/viz/csm_waterfall.json` · `data/ir/nb_csm_ratio.json` 은 리터럴 census 에서
  UNREAD 로 보였지만 `validate_nb_csm_multiple` 이 `VIZ / "csm_waterfall.json"` 형태로
  **읽고 있었다.** 오탐.
- ➕ 반대로 census 가 **놓친 것 2건**: `kics_tier{1,2}_utilization.json`. 리터럴은
  `validate_data_contract` 에 있지만(ARTIFACTS 등록) **런타임에 한 번도 열리지 않는다.**
  §1b 의 라이브 오표시 4건이 여기서 나왔다.

> **교훈**: 정적 문자열 census 는 **양방향으로 틀린다** — 동적 조립을 놓쳐 UNREAD 오탐을 내고,
> "등록만 하고 안 읽는" 자리를 읽는 것으로 착각한다. 배선 감사는 런타임 추적으로 확정할 것.
