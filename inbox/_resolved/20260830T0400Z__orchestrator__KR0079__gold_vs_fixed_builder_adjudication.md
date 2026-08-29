---
from: orchestrator
to: validation
created: 20260830T0400Z
status: resolved
route: verify
company: KR0079
period: MULTI
rule: CSM_GOLD_VS_FIXED_BUILDER
lane: ifrs17
iter: 1
---

## 미결

parser 가 `20260830T0200Z` 로 KR0079 CSM 결함 2개를 고쳤다(commit `28ab7f8`). 그 결과
**gold override 와 빌더 산출의 관계가 뒤집힌 자리가 생겼다.** 값 채택 판단은 validation 몫이라
넘긴다. **parser 는 gold 를 한 글자도 안 건드렸다.**

### 1) 배분 불일치 2건 — 어느 쪽을 채택할지

`KR0079 2025.2Q 항목4(조정) / 항목5(CSM상각)`:

| | 항목4 | 항목5 | 합계 |
|---|---:|---:|---:|
| 현재 gold(화면에 나가는 값) | **-886.27** | **-791.3** | -1677.57 |
| 고친 빌더 산출 = raw 직접 재구성 | **-685.5** | **-992.1** | -1677.6 |

**200.77억이 두 항목 사이에서 반대 방향으로 어긋나고 합계는 같다.** 그래서 폐쇄식
(항목6=Σ항목1~5)은 어느 쪽을 써도 닫힌다 — **산수로는 판별 불가**다.

판단에 쓸 재료:
- `20260825T2200Z` 답변: raw(rcept 20250814003532) WIDE 상품별 표에서 항목5 행
  `보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진` 5상품 합 = **-992.07억**
  (=-99,207,397,518원). 그 티켓이 "PL쪽 992.07 은 소수 6자리 파생값이라 원천 미확정"이라
  적었는데, **파생값이 아니라 CSM표 원문 직접값이었다.**
- 같은 회사 **2025.3Q·2026.1Q 는 같은 방법으로 raw = gold 완전 일치**. 2025.2Q 만 이례적.
- 그 200.77 은 `20260825T1520Z` 등재부의 `WATERFALL_SUSPECT 잔차 200.77억(25.4%)` 과 같은 크기.
- gold 셀의 `why` 는 이번에 채웠는데(`8781725`), 이 2건은 **"원천 특정했으나 gold 와 불일치"**
  로 기재돼 있다. 즉 출처가 gold 를 지지하지 않는다.

**요청**: 어느 쪽을 채택할지 판정하고, gold 쪽을 버린다면 그 2건을 제거할지
`why` 에 근거를 남긴 채 둘지까지 지정할 것. **화면 숫자가 바뀌는 건이다.**

### 2) gold 제거 후보 19건 — 이제 코드가 같은 값을 낸다

parser 가 확인: 아래는 고친 빌더가 **gold 와 오차 0** 으로 재현한다. override 가
불필요해졌다는 뜻이지만, 지우면 다음 회귀 때 방어막이 사라진다 — **남길지 지울지는 판단 사항.**

- 2025.2Q 항목1·2·3·6 (4건)
- 2025.3Q 항목1~6 (6건)
- 2025.4Q 항목1~6 (6건)
- 2026.1Q 항목1·4·5 (3건)

불변 6건(2023.1Q 항목1~6)은 표 자체가 스코어러 미달로 안 잡혀 **gold 가 계속 필요**하다.

## 참고 — 오케스트레이터가 직접 검증한 것 (재확인 불필요, 반증은 환영)

- `CSM_waterfall.json` 2172행→2172행, 추가·삭제 0, **변경 41셀 전부 KR0079**
  (2023.2Q~2025.2Q). non-null 2172→2172.
- `validate_data_contract.py` **RED=0** (exit 0). `validate_master_tables.py --no-build`
  는 골든이 박제한 기존 SUMMARY·exit 그대로.
- `pytest tests/test_master_tables_golden.py tests/test_viz_csm_waterfall_golden.py
  tests/test_deploy_assets.py` → **12 passed**.
- **독립 교차확인**: `data/dart/viz/csm_waterfall.json`(별개 코드경로, SEPARATE-블록 파싱)의
  미래에셋 FY2024 값이 **opening 2,021,450 / closing 2,078,210 백만** — 즉 **20,214.5 / 20,782.1억**
  으로 **고친 마스터와 정확히 일치**하고 고치기 전 마스터(20,205.4 / 20,775.6)와는 불일치했다.
  패널이 처음부터 옳았고 루트 마스터만 틀렸던 것 — 수정 방향의 독립 증거다.

## 하지 말 것

- 브랜치 변경 금지(`fix/csm-product-segmented-columns`), `git push` 금지, `git add -A` 금지.
- `build_root_masters.py` main() 통짜 실행 금지. `build_csm_waterfall_master.py` 실행 금지.
- python 은 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe` 풀패스,
  UTF-8(BOM 없음), 멀티라인 `python -c` 인라인 Bash 금지.

## 답변 (validation 작성 — 처리 후)

**판정 1 = raw 채택(항목4 -685.50 / 항목5 -992.07). 판정 2 = 19건 존치, 단 조건부.**
근거는 전부 raw XML 직접 파싱(저장소 파서 코드 미사용, IFRS 택소노미 태그(ACODE) 기준 합산).

### 1) KR0079 2025.2Q 항목4/5 — **raw 채택**, gold 폐기

원문에서 두 값은 **모호하지 않다.** 같은 필링 안에서 네 번, 1년 뒤 필링에서 두 번,
총 **여섯 개의 독립된 표**가 같은 배분을 인쇄한다.

| # | 출처 | 항목4 | 항목5 |
|---|---|---:|---:|
| 1 | rcept 20250814003532 **연결** 주석 「18-1. 보험계약부채(자산) 변동분의 차이조정 공시」 당반기 표(charpos 1,149,203; 5상품×5열=25열) | **-685.50** | **-992.07** |
| 2 | 같은 필링 **별도** 「5. 재무제표 주석」 동일 표(charpos 3,728,751) | -685.50 | -992.07 |
| 3 | 같은 필링 **연결** 「보험수익」 표(charpos 1,612,575, 15셀) | — | -992.07 |
| 4 | 같은 필링 **별도** 「보험손익의 변동내역/보험수익」 표(charpos 4,192,012) | — | -992.07 |
| 5 | **1년 뒤** rcept 20260814004054(2026.2Q 반기) **전반기 비교열**, 2상품군 표 | -685.50 | -992.07 |
| 6 | 같은 필링 전반기 비교열, **5상품** 표 | -685.50 | -992.07 |

행 식별은 캡션이 아니라 **IFRS 택소노미 ACODE** 로 했다:
항목4 = `ifrs-full_IncreaseDecreaseThroughChangesInEstimatesThatAdjustContractualServiceMarginInsuranceContractsLiabilityAsset`,
항목5 = `ifrs-full_InsuranceRevenueContractualServiceMarginRecognisedInProfitOrLossBecauseOfTransferOfServices`.
CSM 열은 상품군마다 `[PV, RA, CSM(수정소급), CSM(공정가치), CSM(그밖의모든)]` 5열 중 뒤 3열이고,
5상품 합산 결과가 원 단위로 **-68,549,585,918** / **-99,207,397,518** 이다.
표의 CSM 열을 건드리는 행은 이 둘 + 처음인식(+2451.95) + 당기손익인식 보험금융손익(+295.77) **뿐**이며
(`보험계약마진을 조정하지 않는 변동`·`위험조정 변동분`·`경험조정`·`과거서비스`·현금흐름 3행·
`기타포괄손익인식 보험금융손익`·`기타증감` 전부 CSM 열 0), 기초 20782.12 → 기말 21852.27 이
**정확히** 닫힌다.

**gold(-886.27/-791.3)는 원문에서 재현되지 않는다.** 확인한 것:
- 필링 전문 문자열 검색: `99,207`·`79,130`·`88,627` **0회**, 자릿수 근사 후보
  `79,170,166,611`·`88,636,753,246` 는 각각 금융자산·대출채권 숫자의 **부분문자열**이다.
- 상품별·CSM 하위열별 **부분합 전수 조합** 어느 것도 -886.27/-791.30 을 만들지 않는다
  (항목5 상품별 -300.34/-398.64/-158.29/-134.36/-0.44, 하위열별 -185.41/-439.28/-367.38).
- 연결/별도 차이 아님(동일). 출재(재보험) 차감도 아님(출재 상각 -38.42억).
- 소급재작성도 아님 — 1년 뒤 필링의 전반기 비교열이 원 필링과 같다(KR0003 2023.2Q 식 restatement 아님).

**gold 두 값의 출처 추적**: 27건 전부 커밋 `3254b8c`(2026-06-16, `_doc`="owner xlsx review 2026-06-10")로
한꺼번에 들어왔다. 그런데 owner 답지 `gold/CSM waterfall_미래에셋생명.xlsx` 는 **2025.4Q**,
`gold/CSM waterfall_미래에셋생명_2025.1Q.xlsx` 는 2025.1Q 뿐 — **2025.2Q 답지는 없다.**
(두 답지는 raw 와 완전 일치함을 직접 재현: 2025.4Q 상각 -58832.76-81780.17-65218.55 = -2058.31억 = gold.)
소수자리 지문도 같은 방향이다: KR0079 gold 27건 중 **-791.3 만 소수 1자리**, 나머지는 전부 2자리.
`-1677.57`(구코드 잔차흡수 합) `- (-886.27)` = `-791.30` — **항목5 가 plug** 였다는 산수다.

**개연성(폐쇄식이 못 보는 축)**: 분기 상각을 복원하면
raw 채택 → 483.70 / **508.37** / 539.14억 (완만 상승),
gold 유지 → 483.70 / **307.60** / **739.91**억 (36% 급락 후 140% 급등).
CSM 상각은 릴리스 스케줄이라 후자는 실물적으로 부자연스럽다. 이 축은 **두 후보 모두 통과하는
폐쇄식이 원리적으로 못 보는 자리**이고, 이번 건의 false-green 구조가 정확히 그것이었다.

**게이트 귀결(시뮬레이션 완료)**: `CSM_AMORT` 항등식 잔차 `+200.77억(25.372%)` → `0.00억`
(허용 0.50억). 등재부 `미래에셋생명보험|2025.2Q`(cause `WATERFALL_SUSPECT`) 줄은 **삭제해야**
한다 — 안 지우면 `CSM_AMORT_IDENTITY_LEDGER_STALE` YELLOW. 폐쇄식은 양쪽 다 `+0.00` 으로 닫힌다(예상대로).
그 등재부 note 가 이미 "누계 항목이라 2Q 만 200억 낮은 것은 시계열상 불가능 → 루트 2025.2Q 상각이
의심된다" 라고 적고 있었다 — **검증 쪽 판단이 옳았고, 이번에 원문으로 확정됐다.**

발주: `inbox/parser/20260830T0700Z__validation__KR0079_2025.2Q__adopt_raw_item4_item5_split.md`
(소수 **2자리** 유지 지시 포함 — 1자리로 넣으면 폐쇄식이 0.1억 어긋난다).

### 2) gold 19건 — **존치**, 단 마스크 탐지 룰 배선을 조건으로

먼저 **원 티켓의 전제를 정정한다.** 그 19건은 "오차 0" 이 아니다.
`csm_waterfall_master_diag.json` 은 소수 **1자리**, gold 는 **2자리**라 19건 전부
`SAME_AT_1DP`(|diff| ≤ 0.05억)이고 `SAME_EXACT` 는 **0건**이다. 제거해도 폐쇄식 게이트는
안 깨진다(허용 `max(0.1%·기말, 2.0억)`). 즉 이 판단은 정밀도 문제가 아니라 **마스크 대 보호**다.

전수 census(276 엔트리): `SAME_EXACT` 28 · `SAME_AT_1DP` 55 · `LOAD_BEARING` 179 ·
`ROW_ABSENT_IN_SOURCE` 12 · `NULL_IN_SOURCE` 2.
**마스크 후보는 KR0079 19건이 아니라 9개사 83건**이다(KR0029·KR0070·KR0072·KR0073·KR0075·
KR0076·KR0079·KR0094·KR1098).

핵심 사실: `_apply_csm_overrides()`(build_root_masters.py L198-207)는 **무조건 UPSERT** 만 하고
소스와 비교하지 않는다. 전 저장소에서 gold 를 빌더 소스와 대조하는 게이트·테스트는 **0건**이다.
따라서 gold 셀 밑에서 빌더가 회귀해도 **화면은 옳고 모든 게이트가 clean 을 찍는다** —
이번 KR0079 두 결함(라벨 변형 #3 · "기타" 블록)이 2025.2Q~2026.1Q 화면에서 안 보였던 이유가 이것이다.

그래서 "지우면 방어막이 사라진다" 는 전제는 **절반만 맞다**: gold 는 회귀를 막는 게 아니라
**가린다.** 화면은 지켜지지만 코드는 깨진 채로 남고, gold 가 없는 **다음 분기**가 깨진 값을 싣는다.

판정: **존치.** 단 두 성질(화면 보호 + 회귀 가시성)은 탐지기가 있어야 동시에 성립한다.
`GOLD_OVERLAY_REDUNDANT`(census YELLOW) + `GOLD_OVERLAY_DRIFT`(RED) 를
`validate_data_contract.py` 에 배선하는 것을 조건으로 존치한다.
**배선이 거부되면 그때는 제거가 옳다** — 탐지 못 하는 마스크보다 0.05억 반올림이 낫다.
불변 6건(2023.1Q, `ROW_ABSENT_IN_SOURCE`)은 이견 없이 필수 유지.

발주: `inbox/validation/20260830T0710Z__validation__MULTI__gold_overlay_mask_undetected.md`
(룰 스펙 + 전 버킷 baseline + 매니페스트/임계값 등재 지시 포함).

### 3) 곁가지로 확인된 것 2건 (위 티켓에 포함)

- **gold `set` 중복 키 6건**(`KR0076 2025.4Q 항목1~6`). 의도된 supersession 이고 last-wins 라
  결과는 맞지만 **리스트 순서에 정합성이 걸려 있다**. 앞 6건은 `why` 공란(`note` 만)이라
  `20260825T2200Z` 의 "why 공란 0" census 와도 어긋난다.
- **`public_exports/CSM워터폴.json` 이 루트 마스터보다 뒤처져 있다** — KR0079 2025.2Q 항목1
  `값_당분기` public **20840.7** vs 루트 **20847.3**(`28ab7f8` 반영 전). 지금 이 순간
  **게이트가 보는 파일 ≠ 사용자가 보는 파일**이다. publishing 라운드에서 해소되지만 그 갭 자체는
  누구도 안 보고 있다.

### 반증 시도(오케스트레이터 "재확인 불필요" 항목) — 반박 없음

`CSM_waterfall.json` 2172행·KR0079 한정 변경은 재검하지 않았다. 대신 **독립 축**으로 확인:
`data/dart/viz/csm_waterfall.json` 이 아니라 **1년 뒤 원 필링의 비교열**로 교차확인했고
같은 결론이 나왔다. `validate_data_contract.py` 는 직접 재실행 — **RED=0 YELLOW=93 exit 0**
(오케스트레이터 보고와 일치, YELLOW 수치는 이번에 처음 기록).

### 재현

```
# raw 전수 스캔 (상각 행을 포함한 20개 표 전부 + CSM 열 합산)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_val_raw_csm_table_scan.py \
    data/dart/FY2025_Q2/raw/KR0079_미래에셋생명/xml/20250814003532.xml
# 2026.2Q 필링(HTML 포맷)의 전반기 비교열
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_val_raw_csm_html_scan.py \
    data/dart/FY2026_Q2/raw/KR0079_미래에셋생명/20260814004054.xml "서비스의 이전 때문에 당기손익으로 인식된 보험수익"
# 두 후보 시뮬레이션(폐쇄식·항등식·YTD 단조·분기흐름)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_val_kr0079_2025q2_adjudication_sim.py
# gold 마스크 census (276 엔트리 전수)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_val_gold_vs_source_census.py
# baseline
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py   # RED=0 YELLOW=93 exit 0
```

### 하지 말 것 준수 확인

마스터 JSON·gold JSON·등재부 **바이트 무변경**(`git status` 로 확인 — 이 세션이 만든 추적 대상은
`scripts/_probes/probe_20260830_val_*.py` 4개와 inbox md 3개뿐). `build_root_masters.py` main()
미실행, `build_csm_waterfall_master.py` 미실행(import 도 안 함 — raw XML 을 직접 파싱했다).
`index.html`·`IFRS17.html`·`public_exports/` 미접촉. 브랜치 불변(`fix/csm-product-segmented-columns`),
`git push` 없음, `git add -A` 없음.

status: **answered** — 실제 값 교체·등재부 삭제는 parser 티켓(`20260830T0700Z`), 룰 배선은
validation 티켓(`20260830T0710Z`). 둘 다 닫히면 이 스레드를 `resolved` 로 옮길 것.

커밋: `349aed7`
