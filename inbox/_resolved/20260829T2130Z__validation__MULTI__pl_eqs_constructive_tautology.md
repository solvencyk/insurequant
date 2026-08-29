---
from: validation
to: validation
created: 20260829T2130Z
status: resolved
route: blind_spot
company: MULTI
period: MULTI
rule: PL_BRIDGE / PL_EQS
iter: 1
---

## 미결 (validation 자체 조사 — 조사 전용, 코드·마스터 무변경)

**`PL_BRIDGE` 의 `pass=3057` 중 1,608 건(52.6%)이 구성상 참(동어반복)이다.** 빌더가 우변의
한 항을 좌변에서 빼서 만들기 때문에 그 등식은 산수상 깨질 수가 없다. 결과적으로 **PL 32개
항목 중 8개(item5·6·9·10·11·19·21·22·23)는 상류에서 잘못 뽑혀도 push 를 막는 어떤 룰에도
안 걸린다** — 변이시험 실측 탐지율 0.0%.

발단: `_resolved/20260829T1700Z__validation__MULTI__pl_item1_leg_coverage.md`(커밋 `289fb79`)
처리 중 곁가지로 기록한 "3=4+5+6+7 잔차 정확0 이 90.2%" 관측.

### 1. 빌더의 plug 위치 (코드 근거, 전부 write-path 유일)

| 항목 | 계산식 | 위치 | 무력화되는 등식 |
|---|---|---|---|
| item7 기타생명장기원수손익 | `3 − (4+5+6)` | `scripts/build_pl_breakdown.py` L166-174 | EQ1 `3 = 4+5+6+7` |
| item12 기타생명장기재보험손익 | `8 − (9+10+11)` | 같은 파일 L198-202 | EQ2 `8 = 9+10+11+12` |
| item2 생명장기손익 | `3 + 8` | 같은 파일 L204-205 | EQ3 `2 = 3+8` |
| item18 투자이익 | `17 − 19` (무조건) | 같은 파일 L213-215 **+** `scripts/fetch_dart_fs.py` L403-404 | EQ4 `17 = 18+19` |
| item21 영업외손익 | `22 − 20` | `scripts/fetch_dart_fs.py` L392-394 (+ build L232-234) | EQ6 `22 = 20+21` |
| item23 법인세 | `22 − 24` (무조건) | `scripts/build_pl_breakdown.py` L226-228 | EQ7 `24 = 22−23` |

`item7`·`item12` 는 **저장소 전체에 다른 write-path 가 없다**(handler 미발행, `_GOLD_CELL_OVERRIDE`
의 KR0074·KR0087 조차 주석에 "7/12는 잔차"라고 적고 실제로 잔차값이다 — KR0087 2023.2Q:
130035 − (127412+22438+5817) = −25632 = 등재된 item7). 즉 **자기를 검사하는 등식의 잔차로만
존재하는 항목**이다.

`scripts/pl_breakdown/companies.py` L1529-1530 의 하이픈 축(코리안리 `7-1`/`12-1`)도 같은
`suje − csm − ra − yes` 형태다 — 그 축에 부모-자식 식을 안 배선한 판단은 옳았다. 배선했으면
126셀이 `GUARDED` 로 보이면서 실제로는 아무것도 검증 안 했을 것이다.

### 2. FS-API 캐시 전수 (1,040 파일 중 손익계산서 보유 418건)

```
418/418 (100.0%)  item23 = 22-24 로 덮어씀  → EQ7 구성상 참
418/418 (100.0%)  item23 원천 법인세 계정이 실제로 있었는데 버려짐
418/418 (100.0%)  item18 = 17-19           → EQ4 구성상 참
410/418 ( 98.1%)  item21 = 22-20           → EQ6 구성상 참
380/410 ( 92.7%)    그 중 독립 영업외수익/비용 계정이 있었는데 안 쓴 건
  8/418 (  1.9%)  item21 독립소스 사용      → EQ6 가 진짜 검산인 유일한 경우
  3/410 (  0.7%)  EQ5 되맞춤(item17 += item19) — 나머지 385 는 원천에서 이미 닫힘
```

재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -X utf8 scripts/_probes/probe_20260829_fsapi_plug_branch_census.py`

### 3. 변이시험 — 결정적 근거

상류 오추출을 두 모드로 주입한다. `NAIVE` = 마스터의 그 칸만 흔든다. `CONSTRUCTIVE` =
같은 칸을 흔들고 **빌더가 그 칸으로부터 계산하는 하류 항을 빌더와 똑같이 다시 계산한다**
(실제로 파서가 틀리면 일어나는 형태). 게이트는 `PL_BRIDGE` + `CSM_AMORT_IDENTITY`.

```
mutation                     buckets   NAIVE det%   CONSTRUCTIVE det%   잡은 룰
item4  원수CSM상각                348      100.0%              99.7%   CSM_AMORT_IDENTITY (PL_EQS 아님)
item5  원수위험조정                334       94.3%               0.0%   없음
item6  원수예실차                 324       97.2%               0.0%   없음
item9  재보험CSM상각              321       93.5%               0.0%   없음
item10 재보험위험조정               317       94.6%               0.0%   없음
item11 재보험예실차                318       94.3%               0.0%   없음
item19 보험금융손익                326       97.9%               0.0%   없음
item22 세전이익                  338      100.0%               0.0%   없음
item23 법인세                   338      100.0%               0.0%   없음 (빌더가 22-24 로 덮음)
item3  생명장기원수손익              317      100.0%              94.0%   보험손익 dual-form bridge
item8  생명장기재보험손익             316      100.0%              94.3%   보험손익 dual-form bridge
item17 투자손익                  327      100.0%             100.0%   EQ5
item20 영업이익                  338       99.4%              96.7%   EQ5
item24 당기순이익                 338      100.0%              83.4%   EQ8
item25 기타포괄손익                282      100.0%             100.0%   EQ8·EQ9
```

주입 크기 `max(10,000백만, |v|×30%)` — floor(200백만) 의 50배 이상이라 탐지 실패가 임계
문제가 아님을 보장한다. 재현:
`... scripts/_probes/probe_20260829_pl_eqs_mutation.py`

data-contract 게이트(`run_gate`) 전체에 물려도 결과는 같다 — item4 만 347건 RED(CSM_AMORT),
나머지 14개 케이스 전부 신규 RED **0**:
`... scripts/_probes/probe_20260829_pl_eqs_datacontract_mutation.py`

**item9(재보험CSM상각)이 왜 CSM 교차대조에 안 걸리나:** `CSM_AMORT_PL_LEGS = ("원수CSM상각",
"수재CSM상각")` — 출재/재보험 leg 는 의도적으로 제외돼 있다(`validate_master_tables.py` L106-107).
설계상 옳은 제외지만, 그 결과 item9 는 **어느 룰의 입력도 아니다.**

### 4. 등식별 판정과 pass 귀속

```
equation                                   pass  fail  skip   판정
보험손익(dual/leg-coverage)  [PL_EQS 밖]      306    32    18   REAL
EQ1 생명장기원수손익 = 4+5+6+7                 315     0    41   TAUTOLOGY (item7 plug)
EQ2 생명장기재보험손익 = 9+10+11+12             300     0    56   TAUTOLOGY (item12 plug)
EQ3 생명장기손익 = 3+8                       314     0    42   PARTIAL   (item2 plug이나 item1 bridge가 별도로 봄)
EQ4 투자손익 = 18+19                        319     0    37   TAUTOLOGY (item18 plug, 2층)
EQ5 영업이익 = 1+17                         327     0    29   REAL      (독립 3계정, 되맞춤 3/410)
EQ6 세전이익 = 20+21                        336     2    18   TAUTOLOGY (item21 plug 410/418)
EQ7 당기순이익 = 22−23                       338     0    18   TAUTOLOGY (item23 plug 418/418)
EQ8 총포괄손익 = 24+25                       282     0    74   REAL      (독립 3태그)
EQ9 기타포괄손익 = 26+…+32                   220     1   135   REAL      (item32 는 leaf 카탈로그 합)
------------------------------------------------------------------------
TOTAL 3057  =  동어반복 1,608(52.6%) · 진짜 1,135(37.1%) · 부분 314(10.3%)
```

합계가 게이트 인쇄값 `pass=3057` 과 정확히 일치한다(복제 정확성 확인).
재현: `... scripts/_probes/probe_20260829_pl_eqs_pass_attribution.py`

**EQ9 는 동어반복이 아니다.** `item32` 는 `25 − (26..30)` 이 아니라 CIS 의 item25~ProfitLoss
구간에서 26-30 이 안 집은 leaf 행을 **카탈로그로 합산**한다(`fetch_dart_fs._oci32_from_rows`).
그래서 카탈로그가 틀리면 깨진다(실제 FAIL 1건 = 교보 2025.4Q).

### 5. `tests/test_identity_tautology.py` 가 왜 이걸 못 덮는가 (두 겹)

**(a) 대상 축이 다르다.** 그 테스트는 `import validate_kics_disclosure`, `MASTER =
kics_disclosure.json` 이다. 축 목록 `_taut_axes()` 실측 = **5개, 전부 K-ICS item 번호 축**
(`R1_가용자본=기본+보완`, `R2_순자산합`, `R5_기준금액`, `R6_item16`, `R23_기타요구자본`).
**PL_breakdown 축은 0개.** `validate_master_tables.py` 에는 `taut`/`동어반복` 문자열이 아예
없다(grep 0건). PL 은 이 탐지기의 우주 밖이다.

**(b) 더 중요 — 지금 그대로 PL 에 배선하면 안 된다. 귀무모형이 이 마스터에서 성립하지 않는다.**
`_taut_null_p0(k)` 는 각 항이 **등식 자신의 단위로 반올림**됐다고 가정한다(K-ICS 는 백만원
정수). PL 마스터 값은 원 ÷ 1e6 후 `round(6)` 이라 **원 단위 정밀도가 살아 있어서, 발행사가
제대로 공시한 건전한 항등식도 잔차가 정확히 0 이 된다.** 실측으로 확인:

```
eq                            n   zeros   rate   null  excess     z   RED?  실제판정
EQ1 3=4+5+6+7               315     313  0.994  0.602    1.65  14.2   RED   TAUTOLOGY
EQ2 8=9+10+11+12            297     292  0.983  0.604    1.63  13.4   RED   TAUTOLOGY
EQ5 20=1+17                 327     320  0.979  0.750    1.30   9.5   RED   REAL   <- 오탐
EQ8 31=24+25                282     282  1.000  0.750    1.33   9.7   RED   REAL   <- 오탐
EQ9 25=26+..+32             221     219  0.991  0.513    1.93  14.2   RED   REAL   <- 오탐, 최고 excess
```

**9개 축 전부 RED 이고, excess 1위(1.93)가 하필 진짜 검산 축인 EQ9 다.** 통계가 두 부류를
분리하지 못한다. `_TAUT_MIN_CELLS=30` 도 문제가 아니다(n≈300). 즉 이 사각은 "탐지기를 PL 에
배선하는 것을 잊었다"가 아니라 **"이 탐지기는 이 마스터에서 작동하지 않는다"** 다.
판별자는 통계가 아니라 **write-path 추적 + 변이시험**이다.
재현: `... scripts/_probes/probe_20260829_taut_detector_on_pl.py`

### 6. 화면 영향

`IFRS17.html` 이 `법인세`·`영업외손익`·`보험금융손익`·`원수예실차` 를 렌더한다. 즉 무검증
항목이 사용자에게 보인다. 다만 `item21`·`item23` 은 **정의상 잔차라 화면 숫자 자체는 항상
표와 일치한다** — 틀릴 수 있는 것은 그 잔차에 무엇이 섞여 들어갔는지다(예: item22 가 틀리면
item21·item23 이 그 오차를 나눠 갖는다).

### 7. 제안 (owner/후속 판단용 — 이 티켓은 아무것도 고치지 않았다)

1. **명문화가 최소선이자 즉시 가능한 조치.** `PL_EQS` 표 옆에 등식별 `TAUTOLOGY/REAL/PARTIAL`
   을 상수로 선언하고, SUMMARY 가 `pass=3057` 대신 `pass=3057 (진짜 1,135 · 구성상 1,608)`
   을 인쇄하게 한다. **무력한 줄 모르고 pass 를 세는 것보다 낫다.**
   `tests/test_rule_coverage_manifest.py` 에 "이 8개 항목은 어떤 룰도 검사하지 않는다"를
   변이시험으로 박제하면, 나중에 커버가 생겼는데 매니페스트가 안 바뀌는 일도 막힌다.
2. **item9(재보험CSM상각)** 은 유일하게 독립 대조원이 있는 후보다 — `CSM_waterfall` 의 출재
   상각 축이 있으면 `CSM_AMORT_PL_LEGS` 와 나란한 별도 등식으로 세울 수 있다. 있는지부터
   확인 필요(있으면 parser/ifrs17 로 발주).
3. **item5·6·10·11(RA변동·예실차)** 은 원문 주석에 개별 공시되는 값이라, 등식이 아니라
   **원천 재대조**(라벨 정확일치 추출값 vs 주석 표 재판독)만이 검증 수단이다. 등식으로는
   영원히 못 본다 — plug 를 없애지 않는 한.
4. **item22(세전이익)** 는 `20 + 21` 이 아니라 **`24 + 23`(원천 법인세 계정, 지금 버려지는
   그 값)** 과 대조하면 진짜 검산이 된다. 418/418 에서 원천 법인세가 존재하므로 대조원이
   이미 디스크에 있다. `item23` 을 plug 로 덮기 **전에** 원천값과 비교해 이탈을 올리는 형태.
   — 오늘 조사 범위 밖이라 시뮬레이션은 안 했다. 배선 전 전 버킷 시뮬레이션 필수.

### 8. 파장 (owner 확인 필요)

오늘 이 게이트의 `pass` 수를 근거로 여러 판단이 나갔다. 그 판단들의 **산술은 맞다** —
등식은 실제로 닫힌다. 다만 **"닫힌다"가 "맞다"를 뜻하지 않는 등식이 5개**라는 것이 새로
확인된 사실이다. RED=0 은 여전히 유효하지만, 위 8개 항목에 대해서는 "검사했더니 깨끗"이
아니라 **"검사 대상이 아니었다"** 로 읽어야 한다.

## 답변

owner 가 제안 1·2·3·4 를 승인해 같은 세션에서 배선했다. **마스터 값은 한 셀도 안 고쳤다** —
바꾼 것은 룰·문서·매니페스트뿐이다.

### 1. 명문화 (완료)

**등식별 판정을 상수로 선언했다.** `scripts/validate_master_tables.py`
`EQ_REAL`/`EQ_TAUTOLOGY`/`EQ_PARTIAL` + `PL_EQ_EVIDENCE`(11개 라벨 = PL_EQS 9 + dual 2, 각각
`(판정, 근거)`). 주석이 아니라 게이트가 읽는 값이다 — `_check_pl_bridge` 가 pass 를 판정별로
집계하고, `_assert_pl_eq_evidence_declared()` 가 **import 시점에** 판정 없는 등식을 죽인다.

**SUMMARY 인쇄 전/후:**

```
전: pl_bridge:3057P/35F/468S/0NEW
후: pl_bridge:3057P(진짜1135·구성상1608·부분314)/35F/468S/0NEW | tax22_src:282P/0F/74S
```

게이트 본문에도 두 블록이 추가됐다 — 등식×증거력 pass 표(11줄, `[TAUTOLOGY] 315P 생명장기
원수손익 = …`)와 `PL_ITEMS_UNCHECKABLE_BY_EQUATION` 건별 인쇄(`NOEQ item6 …`).
숫자는 조사 때 만든 귀속 probe 와 **정확히 일치**한다(1135+1608+314 = 3057).

**매니페스트 박제.** `tests/test_rule_coverage_manifest.py` 에 PL 축을 신설했다 —
`PL_CONSTRUCTIVE_BLIND`(item 5·6·9·10·11·19·23 = 무검사 선언) ·
`PL_CONSTRUCTIVE_GUARDED`(item 3·4·8·17·20·22·24·25 = 검사됨 선언) ·
`PL_DOWNSTREAM`(빌더 plug 재계산 표) + 테스트 4종. 변이는 **CONSTRUCTIVE 모드**다(그 칸을 흔들고
빌더가 그 칸으로부터 계산하는 하류 항을 빌더와 똑같이 다시 계산). 검사 대상은 PL 을 읽는
**차단성 룰 전부** — PL_BRIDGE(+2b/2c) · TAX22 · CSM_AMORT_IDENTITY · COVERAGE hole ·
`validate_data_contract.run_gate().red`.

매니페스트 자신의 변이시험(`scripts/_probes/probe_20260829_pl_manifest_falsifiability.py`):

```
[1] item6 을 GUARDED 로 오선언          -> OK 죽었다 ("item6(원수예실차) 이 무방비다")
[2] item22 를 BLIND 로 오선언           -> OK 죽었다 ("이제 검사된다: {'tax22': 282}")
[3] 게이트 인쇄목록에서 item19 삭제      -> OK 죽었다 (게이트 목록 != 변이시험 선언)
[4] 정상 상태 재확인 (15항목 전수)       -> 실패 0건
```

즉 이 선언은 **면제가 아니라 검사**다. `pytest tests/test_rule_coverage_manifest.py -k pl_`
18 passed / 19.5초.

### 2. item22 대안 배선 (배선함 — 게이트 2f `TAX22_SOURCE_CROSSCHECK`)

`|item22 − item24| == |원천 법인세 계정|`. 부호는 안 본다 — 빌더 주석이 명시하듯 발행사마다
법인세비용 부호 관행이 갈리고, 그게 애초에 잔차 plug 를 도입한 이유다.

**전 버킷 시뮬레이션을 먼저 돌렸다**(`scripts/_probes/probe_20260829_item22_tax_crosscheck_sim.py`,
356 버킷):

```
compared 282 · PASS 282 · FAIL 0
잔차 |원천세|-|22-24| : 정확히 0 = 127건 · <=1 = 282건 · median=p90=max = 0.000 백만원
skip 74 = FS-API 캐시 없음 56 + 마스터 22/24 결측 18
```

**깨지는 버킷 0건**이므로 배선했다. 배선 후 게이트 실측 `tax22_src:282P/0F/74S` — 시뮬레이션과
동일하다. 변이시험(`probe_20260829_tax22_rule_mutation.py`, 주입 max(10,000백만,|v|×30%)):

```
배선 전  item22 CONSTRUCTIVE 탐지율   0.0%   (게이트 전체에서 신규 RED 0건)
배선 후  NAIVE 100.0% · CONSTRUCTIVE 100.0%  (282/282 신규 FAIL)
```

**오프라인·결정적으로 만든 것이 이 배선의 어려운 부분이었다.** `fetch_dart_fs.tier1_for()` 는
`resolve_corp()` → `data/dart/raw/CORPCODE.xml`(30MB, **gitignore**)을 읽고 없으면
**네트워크로 받는다**. 게이트가 그걸 쓰면 새 클론·CI 에서 커버리지가 달라져 골든이 환경마다
흔들린다. 그래서 **git 추적 파일만** 쓴다 — `data/_derived/alotmatter_fetch_census.json` 의
KR코드→corp_code(39/39 resolved) + 추적된 `data/dart/_fs_api_cache/`(1,040 파일). 두 매핑이
같은지 실측했다(`probe_20260829_offline_corpcode_join2.py`): **36/36 일치 · 불일치 0 ·
census 미등재 0**. 캐시 파싱은 `fetch_dart_fs._parse` 를 **그대로 호출**한다(재구현하면 게이트가
빌더와 다른 값을 보게 된다). basis 순서도 `tier1_for` 와 같고, `BASIS_CFS` 가 비어 있다는
전제를 코드로 확인한다. 다른 cwd 에서 실행해도 같은 수치가 나오는 것을 확인했다.

> 첫 후보였던 `_alotmatter_cache` 의 corp_name 색인은 **23/36 만 덮어서 버렸다**
> (상장사 전용 아티팩트 — 13개사가 조용히 빠졌을 것이다).
> 재현: `probe_20260829_offline_corpcode_join.py`.

**이 룰이 증명하지 못하는 것도 코드에 적었다**: `_parse` 가 22·24·23 을 **일관되게** 잘못된
기준(연결 vs 별도)에서 골랐다면 셋 다 같이 틀려 이 등식은 닫힌다. 기준 오선택은 다른 축 소관이다.
그리고 **SKIP 74 버킷의 item22 는 여전히 무검사**이며, 게이트가 사유별로 세어 인쇄한다.

### 3. item5·6·10·11 — "못 본다" 를 명문화 (완료)

`PL_ITEMS_UNCHECKABLE_BY_EQUATION`(게이트가 매 실행 인쇄) + `PL_EQ_EVIDENCE` 주석 +
`docs/domains/claude-agent-ifrs17.md` 상단 경고 블록 + `docs/agents/claude-agent-validation.md`
§1.5 에 남겼다. **item6 은 별도로 강조**했다 —

> 2026-08-29 에 3개사 50분기를 채웠지만 **폐쇄식은 그 값을 전혀 검증하지 못했다.** 그날 실제로
> 쓴 검증은 전부 독립 앵커였다: 농협생명 보험수익 510,001 일치 · 미래에셋생명 3중 대사
> 594,378,172,139(원) · 에이비엘생명 산문 공시 50억/3억 · 서울보증보험 소계 검산.
> **"폐쇄식이 닫혔으니 맞다" 는 아무 증거도 아니다.**

`tests/test_identity_tautology.py` docstring 에도 절을 추가했다 — **그 탐지기를 PL 에 배선하지
말라**는 것과 그 이유(귀무모형이 항의 반올림을 가정하는데 PL 은 원÷1e6 이라 건전한 항등식도
잔차가 0, 실측 9축 전부 RED 이고 excess 1위가 진짜 검산 축 EQ9). plug 구조 자체는 건드리지
않았다(owner 결정 2026-06-08).

### 4. item9 판정 — **대안 축은 존재하지 않는다**

`CSM_AMORT_PL_LEGS` 가 출재를 뺀 결정의 근거를 찾았고, 그 결정은 **옳다**:

- `CSM_waterfall.json` 전수 census = **2,172행 / 6항목**(기초·신계약·이자·가정·상각·기말)
  **단일 축, 출재 항목 0.**
- `build_csm_waterfall_master.py` 가 전 단계에서 의도적으로 배제한다 —
  `_EXCLUDE_KW = ("재보험","출재","보유한재보험",…)`(L307) · `"출재일반모형" in capf` 제외(L95) ·
  `_is_ceded_header`(L269) · 소수 클러스터 drop(L548) · 첫 행이 `재보험/출재`면 drop(L586).
  `viz_build_csm_waterfall.py` 도 같다(L545·574·618·639·698·1405).
- 배제 근거는 실측이다(`validate_master_tables.py` L70-83 주석): 출재는 **보유 재보험계약자산**의
  별도 워터폴이라 발행계약 워터폴에 더하면 안 된다 — `원수+재보험` 식은 346버킷 중 **245건이
  ±1% 밖**, `원수+수재`(정본)는 **20건**.

따라서 `CSM_AMORT_PL_LEGS` 를 넓히는 방식은 답이 아니고, **오늘 쓸 수 있는 대안 축이 없다.**
원문에는 있다(캡션 "원수 및 출재 …" 다수 관측 — KB손해·메리츠·흥국생명 등). 만들려면
**parser/ifrs17 이 출재 rollforward 를 별도 마스터로 추출**해야 한다. 그건 신규 과제라 이 티켓에서
발주하지 않고 3번과 같이 명문화했다(도메인 doc + `PL_CONSTRUCTIVE_BLIND[9]` + 게이트 NOEQ 인쇄).

### 게이트·테스트·골든

- `scripts/prepush_check.py` 가 실제로 도는지 확인: `validate_master_tables` 는 훅에서
  **`tests/test_master_tables_golden.py` 경유**로 돈다(`test_push_gate_wiring.NOT_A_PUSH_GATE`
  선언 — 직접 호출은 `build_root_masters` 숨은 진입점이라 금지). 그 골든이 SUMMARY 를 바이트로
  박제하므로 **새 tax22 FAIL 이 1건이라도 생기면 골든이 깨져 push 가 막힌다.**
  `test_rule_coverage_manifest.py` 도 훅 목록에 이미 있다(L169) — PL 축 신설분이 자동으로 돈다.
- `tests/fixtures/master_tables_golden.json` `--update`(SUMMARY 한 줄, exit_code 2 불변).
- `tests/test_identity_registry.py` 에 `tax22_source_crosscheck` 등재(`kind: IDENTITY`,
  `tol_from` = `TAX22_FLOOR`/`TAX22_REL`). 그 파일의 `test_no_undeclared_threshold_constants`
  가 **설계대로 즉시 실패해서** 등재를 강제했다 — `EQ_TAUTOLOGY` 는 임계가 아니라 문자열 라벨이라
  `_NOT_A_COMPARISON_THRESHOLD` 에 사유와 함께 넣었다.
- `scripts/validate_golden_input_fingerprints.py` **갱신 불요, RED=0 · 6 spec 전부 ok**.
  그 게이트의 SPECS `code_entries` 는 **빌더만** 추적한다(`build_*.py`·`viz_build_*.py`·
  `fill_post_transition_*.py`) — 이번에 고친 것은 게이트와 테스트이고, 게이트는 골든이 매 실행
  서브프로세스로 재실행하므로 구조적으로 stale 해질 수 없다(2026-08-29 leg-coverage 라운드와 동일 판단).
- `validate_data_contract` **RED=0 YELLOW=92 불변**.

### 재현 명령 (전부 오프라인)

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -X utf8 scripts/validate_master_tables.py --no-build
... -m pytest tests/test_rule_coverage_manifest.py -k pl_ -q
... scripts/_probes/probe_20260829_item22_tax_crosscheck_sim.py
... scripts/_probes/probe_20260829_tax22_rule_mutation.py
... scripts/_probes/probe_20260829_pl_manifest_falsifiability.py
... scripts/_probes/probe_20260829_offline_corpcode_join2.py
```

### 남은 것 (이 티켓 밖)

1. **item5·6·9·10·11·19·23 은 여전히 무검사다.** plug 를 없애지 않는 한 등식으로는 못 본다.
   없애는 것은 파급이 크고 owner 결정(2026-06-08)이 걸려 있어 제안까지만 한다.
2. **출재 CSM rollforward 추출**(item9 의 유일한 대안 축) — parser/ifrs17 신규 과제.
3. **tax22 SKIP 74 버킷**(FS-API 캐시 없는 56 + 22/24 결측 18)의 item22 무검사.
