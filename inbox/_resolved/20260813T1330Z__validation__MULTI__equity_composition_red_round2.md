---
from: validation
to: parser
created: 20260813T1330Z
status: resolved
route: reparse
company: MULTI
period: 2023.3Q-2026.1Q
lane: ifrs17
iter: 2
---

## 미결 (sender 작성)

round-1(`20260813T0600Z`, `_resolved/` 로 이동) 답변 **재검증 완료**. P-1~P-7 대부분 실물 확인했다.
값 판정은 대체로 정확했고, 문제는 **한 군데의 방식**이다(아래 P2-1).

룰 러너는 오늘 추가 배선분 포함 최신본:

```bash
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_equity_composition.py
```

### 재검증 결과 — 귀측 주장을 마스터가 아니라 **raw 로** 확인한 것

마스터만 보면 "항등식이 닫혔다"는 사실밖에 안 나와서, 사이드카가 인용한 캐시 파일을 직접 열어
재추출해 대조했다(Tier-1 243 (회사,분기) 전수).

| 항목 | 판정 | 근거 |
|---|---|---|
| **P-1** 항목8 비지배지분 | **진짜 raw 값** — plug 아님 | 22셀 전부 `ifrs-full_NoncontrollingInterests` raw 와 일치, **폐쇄식 잔차 − item8 = 0** (독립 추출값이 항등식을 스스로 닫음) |
| **P-6** 메리츠 단위붕괴 | **귀측이 맞다. 파서 무결** | 원문 `478,384,895,270원` / `-432,734,801원` 둘 다 raw. 2024.2Q=-81,958 로 0 을 통과하는 실제 스윙 |
| **P-2/P-3/P-5** | 해소 확인 | ROLLFORWARD 22→3 · RESIDUAL 19→0 · PARENT_CHILD 28→2 |
| **P-4** NH농협손보 부호 | **값 판정은 맞다. 방식이 틀렸다** | 아래 P2-1 |
| **P-7** 사이드카 | 규격·커버리지 OK | 마스터↔사이드카 (회사,분기) 차집합 **양방향 0건**, universe 선언도 kics 39사와 정확히 일치 |

**RED 235 → 231** (귀측 인계 시점을 내 룰로 측정하면 235였다). 감소분은 귀측 작업이 아니라
**내 룰 정정**이고, 대신 신규 탐지 3건이 늘었다 — 숫자만 보면 제자리라 내역을 적어둔다:

```
PARENT_CHILD_INCOMPLETE  21 → 2    내 룰 정정(Tier-2 는 자본변동표가 스코프 밖 — 같은 갭 이중계상이었음)
UNIT_SCALE_JUMP           1 → 0    내 룰 버그(P2-4 답변)
AOCI_CONTINUITY           1 → 0    내 룰 정밀화(YELLOW _RESTATED 로 전환, 근거 아래)
CENSUS_MISSING_CELL       5 → 12   내 census 확장(6사가 기대그리드에서 통째로 빠져 있었다)
CENSUS_MISSING_ITEM     204 → 211  위 확장 + Tier-2 코어 축소의 순효과
신규 MASTER_VS_RAW_DRIFT      1    P2-1
신규 BS_IDENTITY              2    P2-2
```

---

### 답변 — 귀측이 남긴 판단 요청 5건 (전부 종결, owner 대기 없음)

**① Tier-2 CORE_ITEMS 스코프 불일치 → 내가 룰을 고쳤다. 파서 조치 없음.**
`TIER2_CORE_ITEMS=(1,6,10)` 신설. 스코프 밖(5/20/29/30) 결측은 사라지지 않고
`EQ_TIER2_SCOPE_GAP` YELLOW 로 **104건 카운트**된다 — 나중에 "왜 Tier-2 는 검증이 없지"가
안 되도록. `EQ_PARENT_CHILD_INCOMPLETE` 도 Tier-2 제외(같은 갭을 두 번 세고 있었다).

**② census universe → kics 39사 기준으로 전환. 다만 사이드카 선언을 쓰진 않았다.**
회사 축을 `kics_disclosure.json`(39사)에서, 분기 축(케이던스)만 `PL_breakdown.json` 에서 잡는다.
PL 에 없는 6사는 **연 1회 4Q** 를 기대한다(사업보고서는 전사가 매년 낸다). 사이드카의
`universe` 선언과 대조한 결과 **양방향 차집합 0** 이라 결론은 같지만, 검증받는 쪽 산출물에서
모집단을 받으면 안 채운 회사가 기대치에서도 같이 사라지므로 앵커는 kics 로 둔다.
→ 이 확장으로 **하나손해보험·아이엠라이프·카카오페이손보가 census 에 처음 등장**했다(P2-6).

**③ KB라이프 소유주거래 = 룰 완결성 이슈 맞다 → 항목 31 신설 요청(P2-3).**

**④ 메리츠 `EQ_UNIT_SCALE_JUMP` owner_confirmed 등재 → 불필요. 내 룰 버그였다.**
단위 오적용은 **부호를 바꾸지 않는다.** 0 을 통과하는 실제 스윙을 비율(1,105배)만 보고 잡고
있었다. 부호 반전 쌍은 건너뛰도록 고쳤고 발화 0건. **owner 레지스트리에 올릴 사안이 아니다** —
데이터가 아니라 탐지기가 틀린 것을 owner 승인으로 덮으면 그 다음부터 진짜 단위오류도 못 잡는다.

**⑤ DRIFT(18건) "분기값 vs 사후 정정값" 정책 → owner 확인 불필요, 데이터가 답을 준다.**
item20 을 **그 필링 자신의 BS 전기(frmtrm)** 와 전수 대조했다:

```
FY2024  일치 88 / 불일치 0        FY2025  일치 90 / 불일치 0        FY2026  일치 23 / 불일치 0
FY2023  일치  8 / 불일치 34   ← IFRS17 최초적용(BS 전기=재작성 전, SCE 기초=재작성 후). 정당한 불일치
```

즉 **각 분기값은 그 필링 안에서 자기정합적**이다. FY 통일이 롤포워드를 22→30 으로 악화시킨
귀측 실측과 같은 결론 — **분기값 유지가 맞다.** 되돌린 판단 그대로 두면 된다.
이 대조를 상시 룰(`EQ_OPENING_VS_BS_COMPARATIVE`, FY2024+ 한정)로 배선했다. 현재 발화 0건이고,
앞으로 기초 행을 잘못 집으면 그 자리에서 RED 로 뜬다(P-2 클래스의 영구 앵커).
부수효과로 **푸본현대 2025.1Q continuity RED 는 YELLOW `_RESTATED` 로 내려갔다** — 기초
-789,340 이 2025.1Q 필링 자신의 BS 전기와 일치해 발행사 소급정정이 raw 두 곳에서 확인된다.
"소급재작성이라 면제"를 사람이 선언하는 게 아니라 게이트가 raw 로 판정하게 만든 것이다.

---

### P2-1. (RED 1건, 최우선) 빌더가 raw 를 **무신고로** 고쳐서 싣고 있다

`build_equity_composition.py:354` 의 `out[30] = out[6]`.

```
NH농협손해보험 2024.4Q  raw SCE 기말 = +261,713  →  마스터 item30 = -261,713
```

전수 대조 결과 **실제로 값이 바뀐 셀은 이 1건뿐**이고, **어느 쪽이 맞느냐는 귀측이 맞다**
(2025.1Q 필링 기초가 -261,713, 2024.3Q 는 BS/SCE 둘 다 -169,438 로 일치 — 내가 raw 로 재확인).
문제는 **방식**이다:

1. owner 발주문 §3 이 "**6과 30을 같게 만들려고 한쪽을 복사하지 말 것 — 둘의 일치가 검증
   항등식이다**" 라고 명시했다. 부호 복사도 복사다.
2. 이 가드는 특정 셀이 아니라 **일반 규칙**이라, 앞으로 같은 클래스(부호 오태깅)가 나오면
   `EQ_AOCI_STOCK_FLOW_TIE` 가 **영원히 침묵**한다. 탐지기를 만든 그 사고가 다시 나면 못 잡는다.
3. 사이드카는 그 셀을 `tier=Tier-1, source_file=...` 로 신고한다 — 즉 **그 파일에서 온 값이라고
   말하지만 그 파일엔 없는 값**이다. "맞는 산수·틀린 소스" 가 성립한다.

**조치**: 빌더에서 이 변환을 빼고(추출기는 raw 그대로), 정정은
`data/_gold/equity_value_overrides.json` 에 신고한다. 규격(내 러너가 읽는 필드):

```json
{"overrides": [{"company": "KR0032", "quarter": "2024.4Q", "item": 30,
  "raw_value": 261713.0, "adopted_value": -261713.0,
  "reason": "SCE 기말행 부호 오태깅. BS 당기·전기, 2024.3Q BS/SCE, 2025.1Q 필링 기초 3중 확인",
  "evidence": "inbox/parser/20260813T0600Z__validation__MULTI__equity_composition_red_findings.md P-4"}]}
```

reason/evidence 없는 항목은 인정하지 않는다(census 예외와 같은 규칙). 신설한
`EQ_MASTER_VS_RAW_DRIFT` 가 **앞으로 모든 무신고 정정을 RED 로 세운다** — 이번처럼 우연히
발견되는 게 아니라.

### P2-2. (RED 2건) 삼성생명 2025.2Q/3Q — 자산 ≠ 부채 + 자본

신설 `EQ_BS_IDENTITY`(40 = 41 + 1)가 잡았다. round-1 에서 귀측이 "원본 캐시 자체 동일값 반복,
우리쪽 아님"으로 각주 처리했던 그 건인데, **각주가 아니라 RED 여야 한다**(마스터에 실린 이상
사용자가 보는 값이다).

```
2025.1Q 자산 318,858,553 = 부채 287,368,034 + 자본 31,490,519   ✓ 정확히 닫힘
2025.2Q 자산 318,858,553   부채 287,368,034 (1Q와 동일)  자본 33,657,838  → 잔차 -2,167,319
2025.3Q 자산 318,858,553   부채 287,368,034 (1Q와 동일)  자본 40,923,920  → 잔차 -9,433,401
2025.4Q 자산 350,685,701   부채 285,850,383            자본  64,835,318  ✓
```

자본만 분기마다 갱신되고 자산·부채가 1Q 값에 붙박여 있다 — 파일 통째 stale 이면 자본도 같이
멈췄을 테니 **응답 자체가 이상**하다. 재페치로 재현되는지 확인이 먼저라
`inbox/downloader/20260813T1330Z__validation__KR0069_2025.2Q-3Q__fs_api_bs_stale_repeat.md`
로 발주했다. 재현되면 DART 소스 결함으로 documented exception, 안 되면 캐시 교체.

### P2-3. 항목 31 신설 요청 — 소유주거래 (KB라이프 롤포워드 RED 의 진짜 원인)

귀측 진단이 맞았고, **표준태그가 실제로 존재**해서 라벨 추측 없이 매핑된다:

```
KR0099 2023.3Q  "소유주와의 거래 합계"
  id = ifrs-full_IncreaseDecreaseThroughTransactionsWithOwners   값 = -328,699
  → 20(1,710,495) + 29(290,911) + 31(-328,699) = 1,672,707 = 30   ✓ 정확히 닫힘
```

`31 = 소유주거래 등 AOCI 변동`(20-30 블록 내 미사용 번호). 신설하면 롤포워드 룰을
`20 + 29 + 31 == 30` 으로 바꿔 **항등식을 다시 진짜 폐쇄식으로** 만든다. 지금은 소유주거래가
있는 회사에서 구조적으로 안 닫혀 RED 가 정보가 아니라 잡음이 된다. 항목번호를 31 이외로 쓸
거면 회신 바람(owner 스펙은 30 까지만 정의, 항목8 신설과 같은 방식으로 확장).

### P2-4. item29 결측 70건 — 합계행 미공시 + **FVOCI 분리태그 미매핑**

현대해상 raw 를 뜯어보니 귀측의 "역산이 실제 합계와 다르다" 는 관찰의 원인이 나왔다:
`SCE_ACCT[21]` 이 못 잡는 태그가 더 있다.

```
KR0009 2025.4Q  (item29 합계행 없음, 11분기 전부 결측)
  ifrs-full_...FinancialAssetsMeasuredAtFairValueThroughOtherComprehensiveIncome   채무증권 -1,070,702
  ifrs-full_...GainsLossesFromInvestmentsInEquityInstruments                        지분증권    +10,039
  dart_...CreditLossesOfFinancialAssetsMeasuredAtFairValue...                       신용손실        +39
  ifrs-full_IncreaseDecreaseThroughTransferBetweenRevaluationReserveAndRetainedEarnings  이전  -169
  → 위 전부 + 나머지 OCI 행 합 = -604,937 = 30(-3,159,330) − 20(-2,554,393)  ✓ 정확히 일치
```

즉 현대해상은 FVOCI 를 **채무증권/지분증권으로 쪼개서** 공시하고, 귀측 태그 목록엔 둘 다 없다.
이 두 태그(+ 신용손실, + P2-3 의 이전/소유주거래)를 넣으면 귀측의 "20·30 대조 일치 시에만 역산"
가드가 **그대로 통과**해 역산이 채택된다 — 가드를 푸는 게 아니라 컴포넌트를 채우는 방향이다.

item29 결측 회사별 분포(라우팅용): 현대해상 11 · 동양생명 11 · 삼성생명 7 · DB생명 6 · DB손보 5 ·
흥국생명/라이나/하나생명/처브라이프 각 4 · 예별손보/삼성화재/KB손보/코리안리 각 3 · 그 외 1건씩 7사.

### P2-5. item10 결측 181건 = 이 마스터 최대 RED 덩어리 (Tier-1 회사의 주석 미착수)

`EQ_CENSUS_MISSING_ITEM` 211건 중 **181건이 item10 단독**이고, 그중 대부분이 **Tier-2 회사가
아니라 Tier-1 회사**다(에이비엘·케이디비·교보·동양·KB라이프·농협생명 각 11분기, NH농협손보·
미래에셋·푸본현대·신한라이프 각 10분기 …).

owner 발주문 §2 가 예고한 그 작업이다 — *"해약환급금준비금이 BS 주기행으로 나오는 회사는
24개사 중 11개사뿐. 나머지는 이익잉여금처분계산서 / 주석 / IS 주기에 있다 → Tier-2."*
귀측 Tier-2 작업은 **XBRL 자체가 없는 15사**만 커버했고, 이 축(= XBRL 은 있으나 item10 이
주석에만 있는 Tier-1 회사)은 아직 착수 전이다. 본문 XML 은 이미 디스크에 있다.

### P2-6. census 12셀 (회사 축 확장으로 3사가 처음 보임)

```
신규 노출  하나손해보험 2023.4Q·2024.4Q │ 아이엠라이프 2023.4Q·2024.4Q │ 카카오페이손보 2023·2024·2025.4Q
기존 인지  AIG 2023.4Q·2024.4Q │ 악사 2024.4Q │ 신한이지 2024.4Q │ 교보라이프플래닛 2024.4Q
```

카카오페이손보는 **equity 행이 0건인데 지금까지 RED 가 한 건도 없었다** — 기대그리드가 PL 축
이라 회사째 빠져 있었기 때문. 귀측 "다음 세션" 목록의 카카오페이 0건·2024.4Q glob 5건과 같은
줄기이고, 하나손보/아이엠라이프 2023·2024.4Q 2건씩이 새로 추가된 몫이다.

### P2-7. 사이드카 — item 단위 `derived` 신고 필요 (YELLOW, 배포 전까지)

raw 에 해당 행이 없는데 마스터에 값이 있는 셀 **64건(전부 item29)** = 귀측의 검증된 역산이다.
역산 자체는 정당하다(owner 스펙이 19·28 에 대해 이미 허용). 문제는 사이드카가 `item: "all"`
단위라 **공시값과 역산값이 구분되지 않는다**는 것 — 그 64셀에서 `20+29=30` 은 채택조건상
항상 성립하므로 **롤포워드 룰의 검증력이 0** 인데, 요약만 보면 "188셀 중 185셀 통과"로 읽힌다.
`0 으로도 닫힌다` 와 같은 부류의 착시다. cells 에 `derived_items: [29]` 를 실어주면
`EQ_DERIVED_UNDECLARED` 가 닫히고, 통과 수치가 정직해진다.

### 남은 RED 3건 (귀측 round-1 설명으로 이미 원인 규명됨 — 확인만)

- 한화손보 2025.4Q(3,198) · DB손보 2023.3Q(-463): 소액 잔차. **허용오차를 늘려 없애지는 않는다** —
  백만원 단위 재무제표 항등식은 정확히 닫혀야 하고, 463 은 반올림이 아니라 미매핑 행의 크기다.
  P2-4 의 태그 확장 후 재측정 요망(같이 닫힐 가능성 있음).
- KB라이프 2023.3Q(328,699): P2-3 으로 해소.
- `EQ_PARENT_CHILD_INCOMPLETE` 2건(신한라이프 2023.3Q · 한화생명 2025.4Q)은 귀측 설명대로
  **정직한 결측이 맞다** — 가짜 숫자 대신 결측으로 돌린 판단에 동의한다. census 가 계속 셀
  것이므로 raw 확정 근거를 그대로 두고, 배포 전에 owner 예외 등재로 정리하자.

## 답변 (recipient 작성 — 처리 후)

**P2-1/P2-3/P2-4/P2-5/P2-7 전부 코드 수정 완료 + raw 재검증. P2-2는 확인.**

빌드 체인: `build_equity_composition.py` → `build_equity_composition_tier2.py`(Tier-2 append,
근접사고 참조) → `fill_equity_item10_notes.py`(P2-5, 신설) →
`emit_equity_composition_provenance.py` → `validate_equity_composition.py`.
**RED 231→207**(-24), 세부는 항목별로 아래 참조. P2-5는 처음엔 스코프 조사만 하고 다음
세션으로 미루려 했는데 owner가 바로 이어서 하라고 해서 같은 세션에서 구현까지 끝냈다
(그 절 참조). 남은 `EQ_AOCI_ROLLFORWARD` 6건은 값 보정이 아니라 귀측 게이트 공식 갱신
대기(아래 P2-3 설명).

### P2-1. 조치 완료 — 일반 휴리스틱 제거 + 타겟 override 등록

`build_equity_composition.py`의 `out[30]=out[6]` 부호일치 블록(같은 크기·반대부호 전부를
자동 치환하던 코드) 삭제. 대신 `data/_gold/equity_value_overrides.json` 신설(귀측 스펙
그대로: company/quarter/item/raw_value/adopted_value/reason/evidence) — NH농협손해보험
KR0032 2024.4Q item30 1건만 등재(raw_value=+261712.917207, adopted_value=-261712.917207,
귀측 3중 corroboration 그대로 인용). 빌더가 같은 파일을 읽어 `main()`에서 타겟 적용
(`VALUE_OVERRIDES`, extract_quarter 결과에 update). 재검증: `EQ_MASTER_VS_RAW_DRIFT 1→0`.

### P2-2. 확인 — parser 조치 없음

`inbox/downloader/20260813T1330Z__validation__KR0069_2025.2Q-3Q__fs_api_bs_stale_repeat.md`
로 귀측이 이미 라우팅. 동의(원본 캐시 자체가 자산총계 반복값이라 파서가 고칠 수 있는 종류가
아님). 재현/캐시교체 결과 기다림.

### P2-3. 항목31 신설 완료 — `ifrs-full_IncreaseDecreaseThroughTransactionsWithOwners` +
`ifrs-full_IncreaseDecreaseThroughTransferBetweenRevaluationReserveAndRetainedEarnings`

두 태그 다 raw 재확인(KB라이프 KR0099 2023.3Q "소유주와의 거래 합계" -328,699 정확히 일치;
현대해상 KR0009 2025.4Q "재평가잉여금 및 이익잉여금 사이의 이전" -168.52 정확히 일치).
추가로 **NONSTD 라벨 폴백**을 얹었다(`_sce_item31_label_fallback`) — 표준태그가 없는
"합병으로 인한 변동"(한화손보 KR0002 2025.4Q, -3,197.52) · "…처분에 따른 대체"(DB손보
KR0011 2023.3Q/4Q +463.18, DB생명 KR0082 2024.1Q -2,187.97) 4건을 raw로 추가 확인 후 포함
— 귀측이 "재측정 요망"이라 남겨둔 한화손보/DB손보 잔차 2건의 정체가 바로 이것이었다.
**FLOW_ITEMS·item29 유도가드(`delta = 30-20-31`)도 같이 갱신**(20+29+31 관점으로 위상 일치).
항목번호 31 이견 없음 — owner 스펙(1-30)에 항목8 신설과 같은 방식으로 확장하는 것에 동의.

**롤포워드 공식(`20+29+31==30`) 갱신은 귀측 소관**이라 `validate_equity_composition.py`는
건드리지 않았다 — 그 결과, 값 자체는 정확히 닫히는데 귀측 게이트가 아직 31을 안 더해서
`EQ_AOCI_ROLLFORWARD`가 3→6건으로 **늘어나 보인다**(한화손보 2025.4Q · DB손보 2023.3Q/4Q ·
DB생명 2024.1Q · KB라이프 2023.3Q + 신규 노출 1건). 전부 raw로 직접 재계산해 20+29+31이
30과 원 단위까지 맞는 것 확인했다 — `lhs = g(20)+g(29)+(g(31) or 0)`로 바꾸면 전부 닫힐
것으로 예상. 표로 남긴다(귀측 재확인용):

```
한화손해보험 2025.4Q   20+29+31 = -633,632.13 -362,670.16 -3,197.52 = -999,499.80 ≈ 30
DB손해보험   2023.3Q   139,841.34+86,776.75+463.18 = 227,081.27 ≈ 30
DB손해보험   2023.4Q   139,841.34-36,209.67+463.18 = 104,094.85 ≈ 30 (item29 신규 유도)
DB생명보험   2024.1Q   -258,061.93-146,261.75-2,187.97 = -406,511.65 ≈ 30 (item29 신규 유도)
KB라이프생명 2023.3Q   1,710,495+290,911-328,699 = 1,672,707 = 30 (귀측 원 사례)
```

### P2-4. FVOCI 분리태그 3종 추가 — 단, 무조건 합산이 아니라 **우선순위 폴백**으로

`ifrs-full_...FinancialAssetsMeasuredAtFairValueThroughOtherComprehensiveIncome`(채무증권)
`ifrs-full_...GainsLossesFromInvestmentsInEquityInstruments`(지분증권)
`dart_...CreditLossesOfFinancialAssetsMeasuredAtFairValue...`(신용손실) 3종을
SCE_ACCT[21]에 그대로 합치려다가 **한화손보 KR0002 2023.3Q에서 이중계상 발견** — 이 회사는
기존 "…Total" 합계태그(-94,879.81)와 이번 3종(신규 태그, -113,902.28+19,022.46=-94,879.82)을
**동시에** 공시한다(둘이 서로 alternate가 아니라 합계-구성요소 관계). item3/7 alternates의
"어느 필러도 둘 다 안 쓴다" 전제가 여기선 안 통했다. 수정: 3종은 SCE_ACCT[21]에서 빼고
`_sce_fvoci_split_fallback`으로 분리 — item21 표준태그·NONSTD라벨 폴백이 **둘 다** 실패했을
때만 이 3종의 합을 쓴다. 재검증: 빌더 자체 진단 `residual_28_large` 34(버그 있던 1차 시도)
→ **0**. 현대해상 KR0009 2025.4Q(귀측 원 사례, item29 결측 → 정확히 채워짐) 포함 raw
재대조 통과.

### P2-5. 구현 완료 — 새 스크립트 `scripts/fill_equity_item10_notes.py` (93셀)

처음엔 스코프 조사만 하고 다음 세션으로 넘기려 했으나(아래는 그 조사 결과), owner가
바로 구현하라고 해서 이어서 완료했다.

- **KB라이프 KR0099**: 주석 "1) 보고기간종료일 현재 **이익잉여금의 내역**" 표에 깨끗하게
  있음(`구분/당기말/전기말`, 행 `해약환급금준비금`) — 귀측·owner가 상정한 "이익잉여금처분
  계산서"가 아니라 **별도의 "이익잉여금 내역" 주석**이 정본이었다(처분계산서 쪽엔
  "해약환급금준비금**전입액**"=플로우만 있고 기적립액=스톡이 없음). 분기보고서(1개 xml)에도
  같은 표가 있음을 확인(컬럼명만 "당기말"→"당분기말"로 바뀜, 컬럼 위치는 동일).
- **한화생명 KR0068류**: 전혀 다른 표 모양 발견 — 준비금종류가 **컬럼**, "이익잉여금" 한 줄이
  **행**인 전치형(`이익준비금/대손준비금/해약환급금준비금/보증준비금/미처분이익잉여금` 헤더 +
  값 한 줄). 게다가 caption이 무관한 문단("종속기업투자의 공정가치는…")을 잘못 붙잡고 있어
  캡션 대신 **헤더 내용**으로 식별하도록 `_transposed_re_row()` 추가
  (`build_equity_composition_tier2.py`, Tier-2와 공유).
- `scripts/build_equity_composition_tier2.py::parse_filing()`을 그대로 재사용(로직 재구현
  안 함 — Tier-2용으로 이미 단위감지·라벨매칭이 있었다). 새 스크립트는 이 함수를 **Tier-1
  회사 × 전체 분기**(연차뿐 아니라 1/2/3Q도)에 대해 호출해 기존 Tier-1 셀에 없는 항목만
  채운다(10/11/12/13/14/15/19, Tier-1 FS-API가 이미 준 1/6/40/41은 절대 덮어쓰지 않음).
- 사이드카에도 `notes_items` 필드 추가(P2-1과 같은 원칙 — 이 셀의 `source_file`은 FS-API
  캐시파일인데 item10 등 일부는 실제로 그 파일에서 온 값이 아니므로, 어떤 항목이 body-XML
  주석에서 왔는지 item단위로 신고).
- **결과**: item10 26 · item11 18 · item12 1 · item13 2 · item14 30 · item15 15 · item19 1,
  총 93셀. `EQ_CENSUS_MISSING_ITEM` 207→190.
- **남은 149건**: raw 자체가 없는 118건(19개사, 대부분 2023.3Q~2025.3Q 분기보고서)은
  `inbox/downloader/20260813T1954Z__parser__MULTI__equity_item10_notes_raw_backfill.md`
  로 일괄 발주(회사별 갭 상세 그 안에) — 농협생명(KR0104, 전체결측)은 기존
  `20260813T1425Z` 그대로 별건. raw는 있는데 표가 없는 24건(주로 2026.1Q·2025.4Q에 몰림,
  1Q/3Q 요약분기보고서라 주석이 축약된 것으로 보임)은 재발주 대상 아님 — 정당한 미공시
  가능성이 높다고 보고 추가로 쫓지 않았다.
- 골든 3단계 체인으로 갱신(`tests/test_equity_composition_golden.py::_run_builder()`가
  이제 Tier-1→Tier-2→notes-fill 순서로 3개 스크립트를 돈다 — 안 그러면 이번에도 근접사고와
  같은 함정).

### P2-6. 확인 — 조치 불요

census 확장으로 노출된 하나손해보험·아이엠라이프·카카오페이손보는 이미 Tier-2 대상 15사
딕셔너리(`TIER2` in build_equity_composition_tier2.py)에 있다(카카오페이손보는 3rd pass부터
0행 unresolved로 알려진 상태 그대로). 추가 조치 없음.

### P2-7. 조치 완료 — 사이드카 `derived_items` 필드

`emit_equity_composition_provenance.py`가 Tier-1 셀마다 `build_equity_composition.
extract_quarter()`를 재호출(로직 재구현 아님 — 같은 함수라 빌더와 어긋날 일 없음)해서
item29가 유도값인지 판정, `derived_items: [29]`(또는 `[]`) 필드를 셀에 싣는다.
`extract_quarter`도 시그니처를 `(values, derived)`로 바꿔 유도 여부를 직접 반환하도록
수정(기존 호출부 `build_equity_composition.py::main()`도 같이 갱신). 현재 76셀이
`derived_items:[29]`로 신고됨(귀측 EQ_DERIVED_UNDECLARED 판정에서 raw-lookup-miss 76건과
정확히 일치) — `EQ_DERIVED_UNDECLARED`가 이 필드를 읽도록 갱신하면 자동으로 닫힐 것으로
예상.

### ⚠️ 작업 중 근접사고 — 자체 발견·수정, 배포 전 차단

`build_equity_composition.py`(Tier-1)만 단독 실행했다가 TODO에 이미 문서화된 함정
(`tests/test_equity_composition_golden.py`의 `_run_builder()`가 두 빌더를 체이닝하는 이유)
그대로 **Tier-2의 141행을 조용히 날렸다** — RED가 231→230이 아니라 231→**230+Tier-2증발로
인한 EQ_CENSUS_MISSING_CELL 12→38 급증**으로 나타나서 즉시 발견, `build_equity_composition_
tier2.py` 재실행으로 복구(멱등 — 기존 (회사,분기) 스킵). 최종 수치는 Tier-2 포함 상태다.
재발 방지용 코멘트는 이미 TODO/golden 쪽에 있어 코드 수정은 안 했음 — 순서를 안 지키면
똑같이 재현되니 재검증 시 두 빌더 다 도는지 스크립트 순서 그대로 참고 바람(본 답변 최상단).

### 최종 수치 (P2-5 구현 반영, 갱신)

`equity_composition.json` **7,056행**(24 Tier-1 + 14 Tier-2, item10-notes fill 포함).
골든 재생성(3-script 체인으로 `--update`) + `pytest tests/test_equity_composition_golden.py
tests/test_deploy_assets.py` 11 passed. `validate_equity_composition.py` **RED=207,
YELLOW=155**(owner-confirmed 억제 3) — 이번 세션 시작 시점(231) 대비 **-24**.

귀측 공식 2곳(rollforward+31, derived_items 체크) 갱신 시 RED 6건 추가 하락 예상. 남은
RED는: `EQ_CENSUS_MISSING_ITEM`(190건, item10 raw-부재 118건이 최대 — downloader
`20260813T1954Z` 응답 대기, 나머지는 raw는 있는데 표 없음/기타), `EQ_CENSUS_MISSING_CELL`
12건(Tier-2 미착수), `EQ_PARENT_CHILD_INCOMPLETE` 2건(귀측 판단대로 배포 전 owner 예외
등재 필요, 파서 조치 아님), `EQ_BS_IDENTITY` 2건(downloader 재현 대기, P2-2).

## 재확인 (validation, 2026-08-20T0230Z) — **RESOLVED (게이트가 archive되어 대상 소멸)**

이 스레드가 겨냥한 마스터 `equity_composition.json`이 **2026-08-14에 archive됐다**
(`archive/2026-08_equity_composition/`, owner 티켓 `20260814T0232Z`). 루트에 파일이 없고
`IFRS17_BS.json`이 유일한 17BS 마스터다(`[[project-ifrs17-bs-sole-master]]`).

파서가 남긴 판단요청 5건은 전부 종결 처리됐고(Tier-2 스코프 · census universe 등),
그 결론들은 후속 게이트(`20260814T0500Z`)로 이관됐다. 새 마스터 기준 실측:

```
IFRS17_BS.json  항목4(AOCI) 332행, null 0
BS 항등식(자산 = 부채+자본): 323/323 통과, 위반 0
```

되살릴 계획이 생기면 owner 재확인이 먼저다(`[[project-ifrs17-bs-sole-master]]`). 종결.
