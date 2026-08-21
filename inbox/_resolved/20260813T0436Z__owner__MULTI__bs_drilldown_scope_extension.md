---
from: owner
to: parser
created: 20260813T0436Z
status: resolved
route: backlog
company: MULTI
period: 2023.1Q-2026.1Q
lane: ifrs17
iter: 2
---

## 미결 (sender 작성)

**같은 날 발주된 `20260813T0422Z__owner__MULTI__aoci_equity_composition_master.md`의 범위 확장이다.**
그 발주문은 그대로 유효하고, 아래 40번대 항목만 **추가**한다. 마스터 파일명·스키마·단위·기준
(OFS/CFS)·Tier 규칙·하지말것 전부 원 발주문을 따른다.

### 확장 사유 (owner, 2026-08-13)

owner 추가 지시: "IFRS17 기준 **자산/부채/자본**(> AOCI > 해약환급금준비금까지 narrow down)을
IFRS17.html에 별도 칸 할애해서 보여달라."

즉 화면이 요구하는 것은 **3단 드릴다운**이다:

```
L1  자산총계 · 부채총계(그중 보험계약부채) · 자본총계
L2      자본총계 → 자본금 / 자본잉여금 / 신종자본증권 / 이익잉여금 / AOCI / 자본조정
L3          AOCI → 자산측·부채측 평가 분해 (21~28)
            이익잉여금 → 법정준비금 3종 (해약환급금 강조)
```

L2·L3는 원 발주문의 항목 1-30이 이미 커버한다. **비어 있는 건 L1(자산/부채)뿐**이라
그것만 채우면 된다.

### E-1. 추가 항목 (40번대) — 소스는 같은 캐시, 표준계정으로 실측 확인됨

`data/dart/_fs_api_cache/*.json`의 `sj_div == "BS"`. 오케스트레이터가 OFS 캐시 80개 파일을
세어본 실측 빈도를 괄호에 적는다(24개사 × 11분기 중 최대 67).

| 항목번호 | 항목명 | account_id | 실측 |
|---|---|---|---|
| 40 | 자산총계 | `ifrs-full_Assets` | 67 |
| 41 | 부채총계 | `ifrs-full_Liabilities` | 67 |
| 42 | 보험계약부채 | `ifrs-full_InsuranceContractsIssuedThatAreLiabilities` | 67 |
| 43 | 재보험계약자산 | `ifrs-full_ReinsuranceContractsHeldThatAreAssets` | 67 |
| 44 | 재보험계약부채 | `ifrs-full_ReinsuranceContractsHeldThatAreLiabilities` | 66 |
| 45 | 투자계약부채 | `ifrs-full_InvestmentContractsLiabilities` | 36 |
| 46 | FVOCI 금융자산 | `ifrs-full_FinancialAssetsAtFairValueThroughOtherComprehensiveIncome` | 67 |
| 47 | FVPL 금융자산 | `ifrs-full_FinancialAssetsAtFairValueThroughProfitOrLoss` | 67 |
| 49 | 자본과부채총계 | `ifrs-full_EquityAndLiabilities` | 67 |

- 전부 **스톡** → `값 == 값_당분기` (원 발주문 §3 규칙 그대로).
- **46/47을 넣는 이유**: AOCI 항목 21(FVOCI 평가손익)의 모집단이다. 평가손익만 보면
  "얼마짜리 자산에서 난 손익인지"를 알 수 없어 회사 간 비교가 안 된다.
- **48은 비워 둔다** (번호 예약). 상각후원가 측정 투자자산은 회사별로 계정이
  `dart_LoansAtAmortisedCost`(58) / `dart_OtherFinancialAssetsAtAmortisedCost`(58) /
  `ifrs-full_FinancialAssetsAtAmortisedCost`(43) / `dart_SecuritiesAtAmortisedCost`(37)로
  쪼개져 있고 **회사마다 다르게 조합**한다. 단순 합산하면 이중계상 위험이 있다.
  화면 요구(L1)에 없으므로 이번 범위에서 제외한다. 넣고 싶으면 별도 발주.
- 45는 커버리지가 절반(36/67)이다. **결측을 0으로 채우지 말 것** — 투자계약부채가
  없는 회사가 실제로 있다(원 발주문 §6, 그리고 "카테고리 단정 금지" 룰).

### E-2. 추가 항등식 (원 발주문 §4에 이어서 7~9번)

7. `40 == 49` — 자산총계 == 자본과부채총계 (BS 항등식. 어긋나면 파싱/기준 오선택)
8. `40 == 41 + 1` — 자산 = 부채 + 자본 (항목 1 = 자본총계)
9. `42 <= 41` — 보험계약부채는 부채총계 이하 (부호·스케일 sanity)

7·8은 **BS가 제대로 잡혔는지 판정하는 1급 지문**이다. 여기가 깨지면 40번대만의 문제가
아니라 그 (회사,분기) 행 전체를 의심해야 한다.

### E-3. 마스터 파일명은 `equity_composition.json` 그대로 간다

내용이 BS 상위행까지 담는데도 이름이 `equity`인 게 어색하지만, **바꾸지 않는다**:
5개 stage 발주문 + keep-list 2줄 + 골든테스트명(`test_equity_composition_golden.py`) +
provenance 사이드카 이름이 전부 그 문자열로 이미 서술돼 있고, 40번대는 자본 구성을 읽기 위한
**상위 컨텍스트 9행**이지 이 마스터의 주인공이 아니다. 이름을 바꾸면 5개 문서를 동시에
고쳐야 하고 그 동기화 실패가 이 저장소의 알려진 사고 패턴이다(CLAUDE.md DOC-1).

### E-4. 우선순위

Tier-1(캐시 24개사 × 11분기)만으로 L1~L3가 **전부** 나온다. 그것부터 끝내고 1차 산출을 올려라.
Tier-2(15개사 본문 XML) / 2023.1Q·2Q 백필은 그 다음이다 — validation·designer가 스키마를
기다리고 있어서, 커버리지보다 **스키마 확정이 먼저** 크리티컬 패스에 있다.

## 답변 (recipient 작성)

**E-1~E-4 전부 Tier-1 범위에서 완료(2026-08-13), 원 발주(`20260813T0422Z`)와 같은 빌드로 처리.**

E-1 항목 40/41/42/43/44/45/46/47/49 전부 추가(48은 지시대로 예약 상태 유지, 미산출).
실측 빈도표(67/67 등)와 실제 커버리지 일치 확인 — 코드는 `data/dart/_fs_api_cache/*.json`의
BS(`account_detail=="-"`)를 표준 account_id로 그대로 매칭, E-1 표에 적힌 9개 account_id
전부 흥국화재/기타 실제 캐시로 재확인 후 채택. 항목45(투자계약부채)는 지시대로 결측을 0으로
채우지 않음(커버리지 절반 그대로 반영). E-2 항등식 7/8/9(40==49, 40==41+1, 42<=41) 빌드 중
자체체크로 구현 — 42<=41은 0건 위반(clean), 40==49/40==41+1은 KR0069(삼성생명 CFS) 2025.2Q/3Q
에서만 위반(원인: 그 회사 CFS 원본 캐시 자체의 자산총계 반복값, 상세는 `20260813T0422Z`
답변 + changelog). E-3 파일명 `equity_composition.json` 그대로 유지. E-4 우선순위(Tier-1
먼저) 그대로 따름 — Tier-2/2023.1Q·2Q 백필은 다음 세션.

이 스레드는 원 발주(`20260813T0422Z`)와 같은 마스터를 추적하므로 **그쪽과 함께 open 유지**
(Tier-2까지 끝나야 전체 완료). designer 쪽 IFRS17.html "7) 재무상태표 · 자본의 질" 섹션
배치는 이 스키마(9키, 항목번호 1-49)를 그대로 소비하면 된다 — L1(40/41/42/1)·L2(1-7)·
L3-a(20-30)·L3-b(10-15,19) 전부 이번 빌드로 채워짐(Tier-1 커버리지 한도 내).

**2026-08-14 종결**: `equity_composition.json`(이 L1 항목 40-49 포함)이 `20260814T0232Z`로
archive됐다. `IFRS17_BS.json`은 L1(자산1/부채2/자본3)만 자체 번호로 담고 41-49(보험계약부채
등 세부)는 없다 — owner가 "너무 많다"고 명시적으로 줄인 결과. 이 메시지는 역사적 기록으로
닫는다.
