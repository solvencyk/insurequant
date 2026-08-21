---
from: owner
to: parser
created: 20260814T1250Z
status: resolved
route: backlog
company: MULTI
period: ALL
rule: BS_DETAIL_EXPANSION
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

**`IFRS17_BS.json`(현 항목 1-7)에 재무상태표 세부 계정을 추가한다.** owner 원문(2026-08-14):
*"OpenDart API 이용해서 BS 추가항목들 좀 추가하는거 (…) 재무상태표처럼 왼쪽 자산 & 우상단 부채 &
우하단 자본 그림 그려주고, 그 아래에 세부 테이블 — 자산 옆에 + 아이콘 클릭하면 좀 더 세부적으로
나오는 식)"*. 화면(T자 레이아웃 + 드릴다운)은 designer 동시 발주
(`inbox/designer/20260814T1250Z`). **이 메시지는 데이터 쪽만.**

> **순서.** `20260814T0149Z`가 예고한 "BS 세부항목 발주"가 **이 메시지다**(그 스레드에 적힌
> `bs_line_items_full` 파일은 만들어진 적 없음 — 여기로 대체, 루트 `TODO.md`도 갱신함).
> owner가 화면까지 요구하면서 우선순위가 LOW → 보통으로 올라왔다. 다만 **2026.2Q 본문 XML이
> 열리면 그게 여전히 먼저다**(`20260814T0149Z` 잔여). BS 세부는 그 대기시간에 진행할 일이지,
> 반기 적재를 밀어내라는 뜻이 아니다.

### S-0. 신규 fetch 불필요 — 캐시에 이미 다 있다 (오케스트레이터 확인)

`scripts/fetch_dart_fs.py`가 때리는 엔드포인트가 `fnlttSinglAcntAll.json`(**전체 재무제표**)이라
BS 전 계정이 이미 `data/dart/_fs_api_cache/*.json` 안에 들어와 있다. 실측(2026-08-14, `*_OFS.json`
581개 스캔):

- BS 행이 있는 캐시 파일 **261개 / 24개 corp**
- `sj_div=="BS" and account_detail=="-"` 기준 **distinct account_id 95개**
- 빈도 상위(파일수/회사수): `PropertyPlantAndEquipment` 261/24 · `IssuedCapital` 260/24 ·
  `RetainedEarnings` 260/24 · `FinancialAssetsAtFairValueThroughProfitOrLoss` 259/24 ·
  `InsuranceContractsIssuedThatAreLiabilities` 258/24 · `ReinsuranceContractsHeldThatAreLiabilities`
  248/24 · `FinancialAssetsAtFairValueThroughOtherComprehensiveIncome` 240/23 ·
  `InvestmentProperty` 240/23 · `ReinsuranceContractsHeldThatAreAssets` 226/21 ·
  `dart_CapitalSurplus` 202/19 · `dart_HybridBonds` 179/18 · `ifrs-full_Borrowings` 173/18 ·
  `InvestmentContractsLiabilities` 169/17 · `dart_CapitalAdjustments` 167/16 ·
  `CashAndCashEquivalents` 156/15 · `FinancialAssetsAtAmortisedCost` 154/16 ·
  `dart_LoansAtAmortisedCost` 146/18 · `dart_CashAndDuefromBanks` 133/14 ·
  `dart_PolicyholdersEquityAdjustment` 107/13 · `dart_SecuritiesAtAmortisedCost` 120/12

→ **`build_ifrs17_bs.py`의 `ACCOUNT_IDS`를 넓히는 작업이지 수집 작업이 아니다.**
다운로더 발주 금지. OFS 고정·`account_detail=="-"`·원→백만원(/1e6)은 현행 그대로.

### S-1. 스키마 계약 (designer와의 접점 — 이 부분만 두 발주가 공유한다)

기존 8열은 그대로 두고 **2열만 추가**한다:

| 열 | 값 | 뜻 |
|---|---|---|
| `섹션` | `자산` \| `부채` \| `자본` \| `준비금` | T자 배치 + 폐쇄검산 단위 |
| `레벨` | `1` \| `2` | 1=총계 타일(현 항목1/2/3), 2=드릴다운 세부 |

- 항목번호 블록: **1-7은 현행 유지**(이미 배포된 HTML이 읽는다), 신규는 자산 `10-29` /
  부채 `30-49` / 자본 `50-69`. 표시 순서는 항목번호 오름차순 = 재무상태표 관행 순서로 부여할 것.
- 기존 1-7의 섹션/레벨 부여: 1=자산/L1, 2=부채/L1, 3=자본/L1, 4(AOCI)=자본/L2,
  **5·6·7(해약환급금·비상위험·대손 준비금)=`준비금`/L2**. 준비금 3종은 이익잉여금 내부
  적립이라 자본 L2 합에 섞으면 이중계상 → 반드시 별도 섹션으로 떼고 **폐쇄검산 대상에서 제외**.
- **HTML은 항목번호를 하드코딩하지 않는다**(designer에 같은 문장으로 발주함). 섹션·레벨로
  그룹핑하고 항목번호로 정렬만 한다 → 나중에 계정을 더 붙여도 HTML 무수정.

### S-2. 수용 기준 = 폐쇄검산 (이 작업의 유일한 안전장치)

각 (회사, 분기)에 대해 **Σ(섹션 L2) == 그 섹션 L1 총계**가 허용오차 안에서 닫혀야 한다
(자산=항목1, 부채=항목2, 자본=항목3).

- **이중계상이 이 작업의 진짜 함정이다.** 회사마다 부모/자식 태그를 섞어 쓴다 — 예:
  `ifrs-full_FinancialAssetsAtAmortisedCost`(154파일/16사)와
  `dart_LoansAtAmortisedCost`(146/18)·`dart_SecuritiesAtAmortisedCost`(120/12)·
  `dart_OtherFinancialAssetsAtAmortisedCost`(143/16)가 어떤 회사에선 부모-자식, 어떤 회사에선
  형제다. 태그 목록만 보고 매핑하면 조용히 두 배가 된다. **회사별로 실제 공존 여부를 세고
  결정하라**(레인 원칙: 카테고리 단정 금지, 회사별 실데이터).
- 남는 차액은 숨기지 말고 **명시 항목으로 emit**(예: 자산 `29 기타·미분류`, 부채 `49`, 자본 `69`).
  **잔차 절대값이 그 섹션 총계의 5%를 넘는 (회사,분기)는 "매핑 미완"으로 보고**하고 목록을 답변에
  적어라. 0으로 눌러 닫지 말 것 — 0값 맹점이 이 저장소의 상습 사고다.
- `-표준계정코드 미사용-`(130파일/24사)로 오는 BS 행이 있다. account_nm 폴백은 **폐쇄가 안 될
  때만**, 그리고 어떤 회사/계정에 썼는지 답변에 남겨라.

### S-3. 커버리지 — 세부는 Tier-1만이다 (지금 확정하고 보고할 것)

캐시에 BS가 있는 corp은 **24개**뿐이고, Tier-2 15사(`build_equity_composition_tier2.TIER2`)는
XBRL 미제출이라 본문 XML 총계(1/2/3 + 준비금)밖에 없다. 즉 **세부 드릴다운은 24사, 나머지는 총계만**.
이게 정상 상태다 — census를 돌려 (회사 × 분기 × 섹션) 실제 숫자를 답변에 적고, 세부 결측
회사군은 **문서화된 예외로 등재**해 검증 게이트가 RED로 때리지 않게 validation에 통지하라.
**Tier-2 본문 XML에서 세부 BS를 새로 파싱하는 작업은 이번 범위 밖.**

### S-4. 하지 말 것

- 새 DART 호출·새 캐시 fetch (S-0)
- `equity_composition.json`(항목 1-49) 되살리기 — owner가 어제 아카이브했다
  (`archive/2026-08_equity_composition/`). 이번 건은 **BS T자용 세부**지 자본구성 마스터가 아니다.
- 3단계 이상 드릴다운 / 신규 파생지표. **2단계(총계→세부)까지가 owner 요구 전부.**

### S-5. 마무리

1. `pytest tests/test_ifrs17_bs_golden.py` — 산출이 **의도적으로** 바뀌므로 `--update` 재생성 +
   커밋 메시지에 이유 기록(CLAUDE.md 불변식 3).
2. `insurequant_master_tables.xlsx` 재생성(공식 `xlsx` skill). MASTERS에 없는 수기 시트가
   날아가므로 재생성 전 확인.
3. 완료 시 **designer inbox에 schema-ready 한 줄**(섹션/레벨 실제 항목 목록 첨부) +
   **validation inbox에 census/예외 갱신** 통지.

## 답변 (recipient 작성 — 처리 후)

**owner 취소 (2026-08-15, live 세션).** 착수 직전(계정 census·부모/자식 co-occurrence 조사만
완료, 코드 미착수)에 owner가 직접 스코프를 되돌림 — "OpenDart API로 나오는 BS항목 정도 +
해약환급금준비금 + 가능하면 대손준비금 등 정도만." 현재 `IFRS17_BS.json`(항목1-7: 자산/부채/
자본/AOCI + 해약환급금·비상위험·대손준비금)이 정확히 이 범위 — 추가 확장 없이 그대로 최종.
이 스레드가 요구한 `섹션`/`레벨`/항목10-69 T자 드릴다운은 미착수 확정.
