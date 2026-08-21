---
from: owner
to: validation
created: 20260813T0422Z
status: resolved
route: backlog
company: MULTI
period: 2023.1Q-2026.1Q
iter: 1
---

## 미결 (sender 작성)

신규 마스터 **`equity_composition.json`**(AOCI + 해약환급금준비금 등 자본구성)에 대한
검증 룰 설계 + 게이트 배선. 파서 발주문에 스펙·항목번호가 있다:
`inbox/parser/20260813T0422Z__owner__MULTI__aoci_equity_composition_master.md`.

**지금 착수 가능한 것 = 룰 설계와 게이트 배선 지점 확정.** 마스터가 아직 없으므로 실행 검증은
파서가 1차 산출을 올린 뒤. 룰을 먼저 못박아 두는 게 목적이다(사후에 데이터에 맞춰 룰을
느슨하게 깎는 순서를 피하려는 것).

### V-1. 항등식 룰 (전부 결측=RED, SKIP-on-missing 금지)

| id | 식 | 의미 |
|---|---|---|
| `AOCI_ROLLFORWARD` | 20 + 29 == 30 | AOCI 롤포워드 폐쇄 |
| `AOCI_STOCK_FLOW_TIE` | 30 == 6 | 자본변동표 기말 == 재무상태표 스톡 |
| `AOCI_CONTINUITY` | 직전분기 30 == 당분기 20 | **FY 경계 포함.** 소급재작성 면제 금지 |
| `EQUITY_CLOSURE` | 1 == 2+3+4+5+6+7 | 자본총계 폐쇄 |
| `RESERVE_WITHIN_RE` | 5 >= 10+12+14 | 법정준비금은 이익잉여금 내 적립 |
| `OCI_COMPONENT_RESIDUAL` | \|28\| <= 0.2 × \|29\| | 잔차 과대 = OCI 세부행 매핑 누락 |

- `AOCI_STOCK_FLOW_TIE` 는 **기준(OFS/CFS) 오선택 탐지기**다. 어긋나면 산수 문제가 아니라
  소스 문제로 다뤄라(파서에 reparse, 값 보정 금지).
- `AOCI_CONTINUITY` 는 기존 CSM continuity와 같은 등급으로 취급 — RED. 면제는 raw 확정 후에만.

### V-2. Census (기대그리드 — 등식만 보는 검증의 사각)

등식은 0들로도 닫힌다. 셀 단위 census를 1급 룰로 배선할 것.

- 기대그리드 = (equity 대상 회사) × (13분기) × (항목 1,5,6,10,20,29,30 = 필수 코어).
- 결측은 **RED**. 단, downloader가 `status: 013`(DART XBRL 부재)으로 판정해 답변에 기록한
  (회사, 분기)만 `documented exception`으로 등재 가능 — 등재 위치는 `TODO_validation.md`,
  근거는 downloader 답변 링크. **"아직 안 받아봤다"는 예외 사유가 아니다.**
- 부모-자식 완전성: 6이 있는데 20/29/30이 통째 없으면 RED(Tier-1만 붙고 SCE 파싱이 죽은 지문).
- 카테고리 단정 금지: "손보는 해외사업환산 없음" 같은 가정으로 기대치를 깎지 말 것.
  legit-zero는 회사별 실데이터 + owner registry로만.

### V-3. Provenance / as-of (데이터계약 게이트)

- 사이드카 `equity_composition_provenance.json` 요구 — 기존 마스터들과 동일 규격.
- 셀별 출처가 **Tier-1(FS API 캐시파일명 + status) / Tier-2(본문 XML rcept_no)** 중 무엇인지 구분 기록.
- 동일개념 guard: 같은 (회사,분기,항목)이 Tier-1과 Tier-2 양쪽에서 왔을 때 Tier-1 우선이
  실제로 적용됐는지 확인.
- 배포 아티팩트가 되면 `scripts/validate_data_contract.py`(push 전 #0)에 배선.
  **게이트가 검사하는 파일 = 사용자가 보는 파일** 불변식 준수 — 루트 배포본을 겨눌 것.

### V-4. Plausibility (하한/부호)

- 6(AOCI)은 음수 정상. 절대값·부호반전 보정 금지.
- 11/13/15(적립(환입)예정액)은 음수 정상(환입).
- 1(자본총계) <= 0 이면 자본잠식 — 실제 사례 있음(KR0004 계열). 자동 RED 말고 flag + owner 확인.
- 10(해약환급금준비금 기적립액)이 분기마다 급감하면 오파싱 의심(제도상 대체로 우상향).
  단 2024.12 제도개선 이후 감소 사례가 있을 수 있으니 **하드 룰 아닌 flag**로.
- 단위 sanity: 백만원 기준. 1e3배/1e6배 튀는 셀 탐지(기존 100x unit 전례).

### V-5. 크로스 마스터 (이 데이터가 생기면 새로 열리는 검증)

- `equity_composition.6`(AOCI) vs `kics_disclosure` 가용자본: 회계자본과 K-ICS 가용자본은
  다르지만 **분기 변동방향**은 상관이 높아야 한다. 역방향 회사·분기는 flag.
- `equity_composition.1`(자본총계) vs `PL_breakdown.24`(당기순이익): 자본증감과 순이익의
  부호 정합 flag (배당·자본증권 발행이 있으면 깨질 수 있으므로 RED 아닌 flag).
- 위 둘은 **flag 전용.** 게이트 RED로 승격하지 말 것 — 정당한 괴리가 흔하다.

### V-6. 배선 위치 명시 (반쪽 배선 방지)

룰을 어디에 넣었는지 답변에 **경로+함수명**으로 적을 것.
`prepush_check.py`는 `validate_kics_disclosure.py`를 호출하지 않는다 — 한쪽에만 넣으면
push를 못 막는다. 이 마스터는 **`validate_data_contract.py` 경로**에 반드시 걸릴 것.

## 답변 (recipient 작성)

**status: done (2026-08-13, validation)** — 룰 설계 + 게이트 배선 + **초회 실행 검증**까지 완료.
발주 시점과 달리 마스터가 같은 날 14:33에 1차 산출(6,255행/24사/11분기)돼 있어 실행까지 갔다.

### 배선 위치 (V-6 요구: 경로 + 함수명)

| 무엇 | 어디 |
|---|---|
| 룰 본체(한 벌만) | `scripts/validate_equity_composition.py` — `run()` / `check_census` / `check_identities` / `check_continuity` / `check_plausibility` / `check_provenance` / `check_cross_master` |
| push 게이트 #0 | `scripts/validate_data_contract.py::check_equity_composition` (`run_gate` 2번째 호출) |
| 마스터 등록·mtime 감시 | `validate_data_contract.py` `Env.MASTER_FILES["equity_composition"]` |
| 러너 호출 / 배포판정 | `Env._load_equity_findings` · `Env._equity_is_published` |
| census 예외 레지스트리 | `data/_gold/equity_census_exceptions.json` (사람 사본 = `TODO_validation.md` Status 표) |

게이트는 룰을 **다시 구현하지 않고** 러너 결과를 흡수한다(두 벌이 갈라지는 사고 차단). 러너가 예외로
죽으면 조용한 pass 가 아니라 `EQ_RULE_RUNNER_FAILED` RED 로 드러난다.

### 심각도를 배포 여부에 연동한 이유 (V-3 ↔ V-6 조정)

V-3 은 "배포 아티팩트가 되면 배선", V-6 은 "반드시 이 경로에 걸릴 것"이다. 지금 배선하되,
**루트 배포 HTML 중 `equity_composition.json` 을 fetch 하는 페이지가 있는지**를 게이트가 직접 읽어
심각도를 정한다. 없으면 YELLOW(사유를 메시지에 명시), 디자이너/퍼블리싱이 패널에 물리는 순간
**코드 수정 없이** RED 로 승격된다(주입 검증: published=True → RED 341 / False → RED 0).
판정 근거가 사람이 넘기는 플래그가 아니라 페이지가 실제로 읽는지라서 stale 될 수 없고,
불변식 "게이트가 검사하는 파일 = 사용자가 보는 파일"과 같은 방향이다.
지금 당장 하드 RED 로 올리길 원하면 `_equity_is_published` 를 True 고정 한 줄이면 된다 — 다만
그 순간부터 무관한 배포까지 341건이 막힌다.

### 발주문 1곳 정정 — `AOCI_CONTINUITY` 의 기준 (V-1)

"직전분기 30 == 당분기 20" 은 한국 중간 자본변동표에 맞지 않는다. 자본변동표는 **FY 누계**라
기초자본 행이 FY 내내 고정이다(파서 빌더 docstring 도 같은 서술). 실측 대조:
**직전분기 기준 일치 0건 / 직전 FY 4Q 기준 일치 150건.** 그대로 짰으면 전 회사 false RED 였다.
→ **직전 FY 4Q 의 30 == 당 FY 의 20** 으로 검사한다. 등급은 발주문대로 **RED**(CSM continuity 동급),
면제는 raw 확정 후에만. 부수로 `EQ_AOCI_OPENING_FY_DRIFT`(FY 안에서 기초가 분기마다 달라짐 = 컬럼
오선택) YELLOW 를 추가했다 — 실제로 12사 15건 발화.

### 룰 목록 (구현된 id)

- **V-1 항등식(RED)**: `EQ_AOCI_ROLLFORWARD`(20+29=30) · `EQ_AOCI_STOCK_FLOW_TIE`(30=6, 기준 오선택
  탐지기 — 값 보정 금지·reparse 라우팅) · `EQ_AOCI_CONTINUITY`(FY 기준, 위 정정) ·
  `EQ_EQUITY_CLOSURE`(1=2+3+4+5+6+7, 항목8 비지배지분은 있으면 가산) · `EQ_RESERVE_WITHIN_RE`(5≥10+12+14) ·
  `EQ_OCI_COMPONENT_RESIDUAL`(|28|≤0.2|29|). 허용오차 = max(1백만원, 0.1%).
- **V-2 census(RED)**: `EQ_CENSUS_MISSING_CELL` · `EQ_CENSUS_MISSING_ITEM`(코어 1,5,6,10,20,29,30) ·
  `EQ_PARENT_CHILD_INCOMPLETE`(6은 있는데 20/29/30 전무) · `EQ_CENSUS_NO_UNIVERSE`(기대그리드를 못 만들면
  건너뛰지 않고 RED) · `EQ_EXCEPTION_REJECTED`(reason/evidence 없는 예외는 미인정).
- **V-3 provenance(RED)**: `EQ_PROVENANCE_SIDECAR_MISSING` · `_UNREADABLE`(깨진 파일 ≠ 없는 파일) ·
  `_CELL_UNSOURCED` · `_TIER_PRECEDENCE`(Tier-1 있는데 Tier-2 채택) · `_COVERAGE`.
- **V-4 plausibility**: `EQ_UNIT_SCALE_JUMP`(RED) / `EQ_NEGATIVE_EQUITY`·`EQ_RESERVE_DROP`(YELLOW, 지시대로 flag).
- **V-5 크로스 마스터(YELLOW 전용)**: `EQ_XM_EQUITY_VS_NETINCOME` 117건.
  AOCI↔K-ICS 가용자본 방향성 비교는 **미구현** — 이유는 아래 남은 것 ③.

### census 가 스스로 눈 감지 않도록 한 두 가지

1. 회사·분기 축을 형제 마스터 `PL_breakdown` 이 실제로 커버하는 (회사,분기)에서 유도한다. 회사별
   공시 케이던스(감사보고서 전용사 = 4Q만)까지 데이터가 들고 있어 카테고리 단정을 배제한다.
2. 분기 축을 equity 마스터가 가진 분기로 **좁히지 않는다**. 좁히면 통째로 빠진 2023.1Q/2Q 가
   기대치에서도 사라져 검증이 무력화된다. 빠진 분기는 레지스트리 예외로만 제외.

### 초회 실행 결과 — RED 341 (전량 파서 라우팅, 값 보정 0건)

`inbox/parser/20260813T0600Z__validation__MULTI__equity_composition_red_findings.md` (P-1~P-7).
census 231 · 부모-자식 28 · 자본총계 폐쇄 22 · 롤포워드 22 · OCI 잔차 19 · 준비금 13 ·
stock-flow tie 2 · continuity 2 · 단위 1 · 사이드카 1.
가장 값나가는 두 진단:
- **자본총계 폐쇄 실패 22건이 CFS 기준 2사(메리츠·삼성생명)의 11개 분기 전부** → 연결 비지배지분
  미포착 확정(삼성생명 잔차 1.87~2.11조). 항목 8 신설 요청.
- **롤포워드 오차가 FY2023 안에서 회사별 상수**(흥국 1,003,379 / 교보 1,942,485 …) → 흐름이 아니라
  **기초(20) 한 값 오선택**. IFRS17 최초적용 재작성 전/후 두 줄 중 잘못된 줄로 추정.

### owner 결정 3건 — 같은 세션에서 종결 (RED 341 → 328)

1. **`EQ_RESERVE_WITHIN_RE`(5 ≥ 10+12+14) → RED에서 내림(YELLOW flag).**
   owner 지적: *"이익잉여금 = 해약+비상+대손+나머지 에서 '나머지'가 음수일 수도 있는 거잖아."*
   맞다 — 미처분이익잉여금이 음수면(누적결손, 또는 손실 중에도 법정 강제적립되는 해약환급금
   준비금 때문) 준비금 합이 이익잉여금 총액을 **정당하게** 넘는다. 항등식이 아니었다.
   실제 발화 13건도 자본체력 약한 2사에 몰려 있었다(에이비엘 11건 — 이익잉여금 자체가 결손
   △218,178 / 롯데손보 2건 — 미처분 △5,892·△18,407). 탐지는 버리지 않고 미처분 잔여를 메시지에
   실어 **"배당가능이익 소진" 신호**로 남긴다. 파서 재추출 대상에서도 제외 통보 완료.
2. **케이디비생명 자본잠식 3분기 = owner 확인 완료** → `data/_gold/equity_census_exceptions.json`
   `owner_confirmed` 등재, 매 실행 재플래그하지 않음(두더지잡기 방지). 추이도 실제 현상과 일치:
   자본총계 802,455(2023.3Q) → 61,317(2024.4Q) → △134,809/△124,153/△101,658 → 409,047(2025.4Q 증자 회복).
   억제는 flag 성 룰(`SUPPRESSIBLE`)에만 적용되고 census/항등식 RED 는 이 경로로 못 지운다.
3. **AOCI ↔ K-ICS 가용자본 비교(V-5 앞항목) = 구현 안 함(종결).** owner 결정: "AOCI 는 IFRS17 에서
   보는 개념이라 K-ICS 비교는 당장 안 해도 된다." 사유를 `check_cross_master` docstring 에 남겨
   나중에 "빠뜨린 것"으로 오해되지 않게 했다. V-5 는 `EQ_XM_EQUITY_VS_NETINCOME` 만 유지.

### 회귀 확인

- `validate_data_contract.py --selftest` **22/22 pass** (기존 케이스 무손상)
- `pytest tests/test_deploy_assets.py` **10 passed** (BOM/UTF-8·keep-list·골든표 동기화)
- 라이브 게이트 재실행: **RED=0 / YELLOW=696** (배선 전 219 → equity 스테이징 YELLOW 477 추가). push 미차단.

---

### 추가 (같은 날 저녁, 파서 답변 재검증 iter 2) — 룰 4개 신설, RED 231

파서가 P-1~P-7 을 고쳐 올렸다. **마스터가 아니라 raw 로 검증**했다(사이드카가 인용한 캐시 파일을
직접 열어 Tier-1 243 (회사,분기) 전수 재추출). 마스터만 보면 "항등식이 닫혔다"밖에 안 나오고,
빌더가 raw 를 고쳐 내려보내면 모든 검사가 통과하기 때문이다.

**결정적으로 잡힌 것 하나** — 빌더가 raw 를 **무신고로** 고치고 있었다(`out[30] = out[6]`).
실제 변경 셀은 KR0032 2024.4Q 1건이고 **값 판정 자체는 파서가 맞다**. 문제는 ① 발주문 §3
"6과 30을 같게 만들려고 복사하지 말 것" 위반 ② 일반 규칙이라 앞으로 같은 부호 오태깅이 오면
탐지기가 **영원히 침묵** ③ 사이드카가 "그 파일에서 왔다"고 신고하는데 그 파일엔 없는 값.
→ `EQ_MASTER_VS_RAW_DRIFT`(RED) 신설: 정정을 금지하는 게 아니라 **조용한 정정을 금지**하고
`data/_gold/equity_value_overrides.json` 신고제로 돌린다.

같이 신설: `EQ_OPENING_VS_BS_COMPARATIVE`(item20 의 유일한 독립 앵커. FY2024+ 201/201 일치라
오탐 0, 전환연도 FY2023 만 제외) · `EQ_BS_IDENTITY`(자산=부채+자본, **Tier-2 행에 걸 수 있는 유일한
구조검사** → 삼성생명 2025.2Q/3Q 신규 RED 2건 적발) · `EQ_DERIVED_UNDECLARED`(역산 64셀이 공시값과
구분 안 되는 문제 — 항등식이 파생값으로 닫히면 그 셀 검증력은 0).

**내 쪽 결함 3건도 고쳤다**: ① census 회사 축이 `PL_breakdown` 이라 **6사를 통째로 못 보고 있었다**
(카카오페이손보는 equity 행 0건인데 RED 0건) → `kics_disclosure` 39사 앵커로 이동 ② Tier-2 축소
스코프 반영 + 그 갭을 `EQ_TIER2_SCOPE_GAP` 104건으로 상시 카운트 ③ 메리츠 `EQ_UNIT_SCALE_JUMP` 는
**내 오탐**이었다(단위오류는 부호를 안 바꾼다) — 파서의 owner_confirmed 등재 요청은 거절했다.
탐지기 결함을 owner 승인으로 덮으면 다음부터 진짜 단위오류를 못 잡는다.

**V-1 발주문 continuity 재정정(2번째)**: 면제 판정을 사람에서 데이터로 옮겼다. 기초가 그 필링
자신의 BS 전기와 일치하면 발행사 소급정정이 raw 두 곳에서 확인된 것 → `_RESTATED` YELLOW
(푸본현대 2025.1Q). "raw 확정 후에만 면제"라는 발주문 요건을 게이트가 자동으로 만족시킨다.

**RED 231** — 최대 덩어리는 **item10 단독 결측 181건**(= XBRL 은 있으나 해약환급금준비금이 주석에만
있는 Tier-1 회사. 발주문 §2 가 예고한 미착수 축이고, 파서 Tier-2 는 XBRL 자체가 없는 15사만 커버했다).
회귀 `--selftest 22/22` · `pytest 10 passed` · 라이브 게이트 **RED=0 / YELLOW=605**.
잔여는 `inbox/parser/20260813T1330Z…red_round2.md`(P2-1~P2-7) +
`inbox/downloader/20260813T1330Z…fs_api_bs_stale_repeat.md`.

**owner 판단 필요한 것 = 없음.** 파서가 올린 질문 5건(Tier-2 코어·universe·KB라이프 항목31·메리츠
등재·DRIFT 정책)은 전부 데이터로 종결했다. 다만 **항목 31(소유주거래) 신설**은 스펙 확장이라
알려둔다 — KB라이프 롤포워드가 `20+29+31=30` 으로 정확히 닫히고 표준태그
`ifrs-full_IncreaseDecreaseThroughTransactionsWithOwners` 가 실제로 존재한다(항목8 신설과 같은 방식).

---

**재검증 종결 (validation, 2026-08-14T06:20Z).** 게이트 독립 재실행으로 확인: `validate_data_contract.py` **RED=0 / YELLOW=261**(exit 0) · `--selftest` **25/25** · `pytest tests/test_deploy_assets.py` **1 FAIL**(designer/publishing 대기건 1개뿐, validation 소관 아님). 파서 재빌드(`IFRS17_BS.json` 14:42) 반영 후 17BS findings 40→42이고 삼성생명 `BS_IDENTITY` 2건·한화생명/흥국생명 AOCI 8건은 **소스 수정으로 소멸 확인**(예외 등재 0건). 잔여 42건 델타는 `inbox/parser/20260814T0620Z…ifrs17_bs_delta_after_ofs_rebuild.md`(iter 2). → `status: resolved`, `_resolved/` 이동.
