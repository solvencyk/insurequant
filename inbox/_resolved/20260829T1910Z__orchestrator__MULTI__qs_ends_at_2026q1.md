---
from: orchestrator
to: validation
created: 20260829T1910Z
status: resolved
route: blind_spot
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (orchestrator 작성 — validation 자체 보고)

**`scripts/validate_master_tables.py` 의 `QS` 가 `2026.1Q` 에서 끝난다. 최신 분기인
2026.2Q 24버킷을 coverage census 와 qoq_scan 이 통째로 안 본다.**

직전 작업(`_resolved/20260829T1500Z`, 커밋 `9fadad4`)이 스스로 보고한 잔여 사각이다.
`PL_BRIDGE` 는 무관하지만 census·qoq 두 축이 최신 분기를 못 본다.

### 왜 급한가

**오늘 그 분기 데이터를 라이브에 배포했다.** PL_breakdown 항목25~32 신설, 예실차 3사,
CSM상각 as-of, 삼성생명 BS 정정이 전부 2026.2Q 를 포함한다. **검증하지 않은 분기를
내보낸 셈이다.** 게이트가 RED=0 이라고 한 것이 그 분기에 대해서는 "검사했더니 깨끗" 이
아니라 "안 봤다" 였다.

### 요청

1. **`QS` 가 어떻게 정의돼 있는지 확인하고, 왜 2026.1Q 에서 멈췄는지 규명해라.**
   하드코딩인지, 어떤 소스에서 파생되는데 그게 안 늘어난 것인지 가른다. **하드코딩이면
   그것 자체가 재발 구조다** — 분기가 늘 때마다 사람이 고쳐야 하면 다음에 또 빠진다.
   마스터에서 자동 파생하는 방향을 검토해라.
2. **2026.2Q 를 범위에 넣고 census·qoq 를 돌려서 무엇이 나오는지 먼저 보고해라.**
   새 RED 이 대량으로 뜨면 그것부터 판단해야 한다. **고치기 전에 실측부터.**
3. **같은 패턴이 다른 게이트에도 있는지 훑어라.** 분기 목록을 하드코딩하거나 상한이 박힌
   곳이 `validate_data_contract.py`·`validate_kics_disclosure.py` 등에 또 있는지 census 해라.
   이게 이 티켓에서 제일 값어치 있는 산출이다.
4. 고쳤으면 `prepush_check.py` 경유로 **실제로 그 축이 도는지** 확인하고, 골든 `--update` +
   `scripts/validate_golden_input_fingerprints.py` 지문 갱신까지.

### 하지 말 것

- **마스터 데이터를 고치지 마라.** 새 RED 이 나오면 원인만 규명해서 해당 stage 로 route 해라.
- `index.html`·`IFRS17.html`·`public_exports/` 금지. 브랜치 변경 금지. `git push` 금지.
  `git add -A` 금지.

## 답변 (validation 작성 — 처리 후)

**결론: 하드코딩이 맞았고, 세 곳이었다. 파생으로 바꿨다. 2026.2Q 를 넣자 RED 1건이
드러났고 지금 push 는 그 RED 으로 막혀 있다 — 데이터는 고치지 않고 parser 에 발주했다.**

`status: answered` — 오케스트레이터가 (a) 새 RED 라우팅 결과와 (b) 아래 3번의 미조치
항목(리포트 헬퍼 2개)을 재확인해 주면 종결.

---

### 1) `QS` 가 왜 2026.1Q 에서 멈췄나 — 하드코딩, 그리고 **세 곳**

`git log -L 276,277:scripts/validate_master_tables.py` 실측: 이 목록은 **파일 최초
커밋 `9243445` 부터** `2026.1Q` 로 끝나는 리터럴이었고 그 뒤 한 번도 수정되지 않았다.
어떤 소스에서 파생되다가 멈춘 게 아니라 **처음부터 손으로 적은 값**이다.

AST census(주석·독스트링 제외, `scripts/_probes/probe_20260829_gate_horizon_audit.py`)
결과 같은 병이 셋:

| 위치 | 상수 | 무엇을 가두고 있었나 |
|---|---|---|
| `scripts/validate_master_tables.py` L276 | `QS` | coverage census · qoq · spike · wfy · continuity · `prev_quarter()`(→ OCI-vs-BS) |
| `scripts/validate_data_contract.py` L291 | `_DISPLAY_QUARTERS` | **census RED 의 발화 스코프 전체** (`_emit` 24곳) |
| `scripts/validate_kics_rate_sensitivity.py` L33 | `ALL_Q` | RS4 커버리지 census |

같은 파일 안에 **두 번째 지평**도 있었다 — `validate_master_tables._check_plausibility` 의
`FY_Q = {..., "2026": ["2026.1Q"]}` / `PREV_CLOSE` / `for fy in ("2023".."2026")`. `QS` 만
고쳐도 연속성 검사는 여전히 2026.2Q 를 안 봤을 자리다. 셋 다 파생으로 바꿨다.

또 `validate_data_contract.py` L104 에 **죽은 `QS` 리터럴**이 있었다(파일 전체 참조 0).
지평처럼 보이는 자리에 앉아 다음 세션을 오도할 값이라 제거했다.

**자물쇠가 직렬 두 개다 — 이게 이번의 함정.** `_DISPLAY_QUARTERS` 에만 2026.2Q 를 넣고
돌리면 **델타 0**이다(실측). IFRS17 hole 은 `validate_master_tables.coverage_holes`
(→ 그쪽 `QS`)를 거쳐 오기 때문에, **둘 다** 열어야 RED 이 나온다.

**그리고 아는 사람이 있었는데 정본을 안 고쳤다.** `validate_data_contract` 안의 두 검사가
주석에 *"`_DISPLAY_QUARTERS` 는 2026.2Q 를 아직 포함하지 않는데 사이트는 그 분기를 그린다"*
라고 적어 놓고(L2275 배당, L2519 CSM 연속성) **자기만 스코프를 비켜갔다.** 개별 우회로 버틴
것이 재발 구조 자체다.

**자동 파생 — 했다.** `scripts/_quarter_horizon.py` 신설:

- 하한 `QUARTER_FLOOR = "2023.1Q"` **고정**. 데이터 파생하면 `IFRS17_BS.json` 의 2021.4Q
  까지 끌려와 존재하지 않는 분기가 통째로 hole 이 된다.
- 상한 = 마스터 **5개**(`PL_breakdown` · `CSM_waterfall` · `IFRS17_BS` · `kics_disclosure`
  · `dividend`)의 `공시분기` high-water mark. **한 마스터에서만 파생하지 않는 이유**: 그
  마스터가 최신 분기를 통째로 빠뜨리면 지평도 같이 줄어 **결측이 안 보인다**(자기참조 사각).
  다른 마스터가 그 분기를 갖고 있는 한 지평이 남고 빈 쪽이 hole 로 찍힌다.
- `"공시분기"` 필드만 정규식으로 읽는다. 파일 전체를 훑으면 `비고` 산문의 분기 언급까지
  주워 지평이 허수로 는다. 비용 실측 **81ms**.
- `display_quarters()` = owner 스코프(2026-06-20)의 **규칙**을 파생: 연말(4Q) 전부 +
  2025.1Q 이후 전부. 같은 지평에서 돌리면 종전 7개를 **정확히 재현**하고 새 분기만 붙는다
  (`test_display_quarters_still_reproduce_the_owner_set` 가 회귀 가드).

---

### 2) 2026.2Q 를 넣었을 때 나오는 것 — 실측

**RED 1건.** 나머지는 YELLOW(비차단).

```
validate_master_tables.py --no-build   (exit 2, 전후 동일)
  coverage_hole   0CSM/0PL  →  0CSM/1PL     ← HOLE-PL 흥국화재 2026.2Q (부분)
  qoq_warn             211Y →  235Y         (+24, 전부 2026.2Q)
  oci_vs_bs_aoci        13Y →  14Y          (+1, 에이비엘생명 2026.2Q)
  plausibility  0dup/1spike/1cont/0wfy/0zamort  → 변화 없음
  closing / pl_bridge / csm_amort_identity / sens → 변화 없음

validate_data_contract.py
  SUMMARY RED=0 YELLOW=92  →  RED=1 YELLOW=92   (exit 0 → 2)
  RED [PL_breakdown] MASTER_HOLE  흥국화재 2026.2Q
```

**RED 원인 규명 (마스터는 안 건드렸다).** 흥국화재 2026.2Q PL 항목 **2/8/12/13/14** 가
전부 `None` 인데 직전 2026.1Q 는 다섯 항목 다 정상이다 = **최신 분기 회귀**.
자식 다리는 살아 있다(item9 −3,901 · item10 −571 · item11 −7,231) — 부모 item8 만 비고
item12 도 비어 산술로도 못 닫는다. raw 는 디스크에 있고
(`data/dart/FY2026_Q2/raw/KR0005_흥국화재/20260814003618.xml`) 라벨 빈도가 2026.1Q 와
사실상 같다(자동차 60/58 · 일반 64/62 · 장기 88/82 · 재보험 233/229). **원천에는 있다 =
refetch 아님, 추출 실패다.** 구조 단서 하나: 2026.1Q 디렉터리엔 `xml/` 하위 폴더가 있는데
2026.2Q 엔 없다 — 커밋 `2477b04` 가 미래에셋에서 고친 `xml/` glob 사각과 같은 모양.
→ **`inbox/parser/20260829T2010Z__validation__KR0005_2026.2Q__pl_lob_legs_missing.md`**
(`lane: ifrs17` · `route: reparse`).

**서울보증보험도 같은 3항목 중 생명장기손익이 없지만 hole 이 아니다** — 핵심항목 보유
분기가 6개(<`active_min`=7)라 `struct`(미공시)로 분리된다. 보증보험이라 생명장기 leg 자체가
없는 것이 정상이고, `ZLEG_LEGIT` 에도 `"ALL"` 로 등재돼 있다. 카테고리 추론이 아니라 회사별
실데이터로 확인했다.

**YELLOW 중 조사 요청한 것 2건 / 기저효과로 판정한 것 1건** (같은 parser 티켓에 동봉):
- 교보생명 2026.2Q `이자부리` 12,197 → 993 (YoY −91.9%) — 표 변형/행 오픽업 의심.
- 에이비엘생명 2026.2Q `PL_OCI_VS_BS_AOCI` 잔차 −13,196백만 (ΔBS 37,364.6 vs PL당분기 50,560.6).
- 코리안리 2026.2Q `이자부리` +494.2% 는 **기저효과** — 2025.2Q 가 −116.4(음수)다. 조사 불요.

전체 신규 qoq YELLOW 24건은 `data/_derived/qoq_warn.json` 에 있다.

---

### 3) 다른 게이트 하드코딩 census (요청 3 — 이 티켓의 주 산출)

방법: `ast` 로 **주석·독스트링을 제외한 실행코드**만 훑었다(첫 시도의 grep census 는 90%가
산문이라 쓸 수 없었다). 재현:
`C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260829_gate_horizon_audit.py`

| 게이트 | 판정 |
|---|---|
| `validate_master_tables.py` | **지평 하드코딩 2건** (`QS`, `FY_Q`/`PREV_CLOSE`/wfy-year) → 고침 |
| `validate_data_contract.py` | **지평 하드코딩 1건 + 죽은 리터럴 1건** (`_DISPLAY_QUARTERS`, `QS`) → 고침 |
| `validate_kics_rate_sensitivity.py` | **지평 하드코딩 1건** (`ALL_Q`) → 고침. K-ICS 마스터 최신이 아직 2026.1Q 라 **미발현**이었다 — 2026.2Q 공시가 들어오는 순간 RS4 census 가 조용히 건너뛸 자리 |
| `validate_kics_disclosure.py` | clean. `quarters = sorted(by_q)` 로 데이터 파생. 남은 29개 리터럴은 전부 (회사,분기) 예외 등재부이고 `SPOT_QUARTER="2025.4Q"` 는 단일 spot-check 앵커(지평 아님) |
| `kics_json_rules.py` | clean. 43개 전부 (회사,분기[,항목]) 예외 등재부 |
| `validate_csm_continuity` · `validate_csm_waterfall` · `validate_live_artifacts` · `validate_golden_input_fingerprints` · `validate_statutory_reserves` · `check_dart_raw_coverage` · `check_data_file_integrity` · `check_inbox_hygiene` · `prepush_check` | clean (데이터 파생 또는 앵커 상수만) |
| `validate_nb_csm_multiple.py` | clean. `"2024.4Q"` 3건은 FY2024 IR 앵커(고정이 맞다) |

**미조치 2건 — 게이트가 아니라 리포트 헬퍼라 push 를 막지 않는다(기록용, 오케스트레이터 판단
요청):** `scripts/_csm_goldmap.py` L20 과 `scripts/_csm_status_matrix.py` L29 가
`QS = [q for q in QS if q != "2026.2Q"][:13]` 로 **2026.2Q 를 명시적으로 배제**한다. 그
리포트를 근거로 판단할 때는 최신 분기가 빠져 있다는 점만 알고 있으면 된다.

---

### 4) 훅 배선 확인

`tests/test_quarter_horizon.py` 신설(17 tests) → `scripts/prepush_check.py` 의
`fast` 목록에 등록. **배선했다는 말로 끝내지 않았다 — 변이시험으로 확인했다:** `QS` 를 옛
리터럴로 되돌리자 `test_gate_horizon_includes_latest_quarter[validate_master_tables]` 와
`test_no_gate_retypes_the_quarter_horizon[validate_master_tables.py]` **2건이 FAIL** 했고,
되돌리니 17/17 통과 + 파일이 변이 전과 바이트 동일.

훅 전체 실행 (`prepush_check.py`, 실측 ~9분):

```
1. COMPLETENESS CENSUS ... RED=1 YELLOW=72
   RED [PL_breakdown] MASTER_HOLE  흥국화재 2026.2Q
K-ICS gate exit=0 (clear) · 도메인 게이트 5종 exit=0 · DART raw 유실 0
GOLDEN INPUT FINGERPRINT  RED=0 → clear
OFFLINE TESTS  270 passed, 1 skipped
PRE-PUSH VERDICT: gate RED=1 ... → BLOCKED (fix or owner-escalate)
```

**BLOCKED 가 정답이다.** 이 RED 은 documented exception 감이 아니라 fixable —
parser(ifrs17)가 흥국화재 2026.2Q 를 재추출하면 0 이 된다.

`git config --get core.hooksPath` = `.githooks` (배선됨).

### 5) 골든 / 지문

- `tests/fixtures/master_tables_golden.json` → `--update` 재생성. 사유 = 게이트가 분기를
  하나 더 검사하게 된 **의도된 산출 변경**(위 3칸). `exit_code` 는 2 로 불변.
- `scripts/validate_golden_input_fingerprints.py` → **갱신 불요.** 빌더를 하나도 안
  건드렸다(검증기만 수정). 실행 결과 6/6 `ok`, RED=0.

### 6) 커밋

`f45cef8` — `scripts/_quarter_horizon.py` 신설 · 게이트 3종 지평 파생 전환 ·
`tests/test_quarter_horizon.py` + 훅 배선 · 골든 재생성 · parser 발주 · TODO/changelog.
**push 안 함**(RED=1 로 훅이 BLOCK, 그리고 배포는 owner 승인 사항).

### 7) 안 한 것

마스터 JSON·xlsx 미수정(읽기 전용). `data/disclosure/`·`download_*`·`index.html`·
`IFRS17.html`·`public_exports/` 미접근. 브랜치 유지(`fix/csm-product-segmented-columns`),
`git push` 없음, `git add -A` 없음.
`data/_derived/qoq_warn.json` · `pl_oci_vs_bs_aoci_warn.json` 은 게이트 자신의 산출물이라
2026.2Q 행이 늘어난 채 커밋된다(마스터 아님).
