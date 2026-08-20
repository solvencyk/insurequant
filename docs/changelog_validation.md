# Validation Changelog (Stage 3)

> Last updated: 2026-08-20 · Stage 3/5 — validation
> Prompt: docs/agents/claude-agent-validation.md · Authoritative rules: docs/agents/kics-json-validation-rules.md

Validation-only history. Cross-stage changes also keep a 1-line cross-reference in [`docs/claude-changelog.md`](claude-changelog.md).

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
