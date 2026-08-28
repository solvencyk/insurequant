---
from: orchestrator
to: parser
created: 20260828T1600Z
status: resolved
route: reparse
company: MULTI
period: MULTI
rule: PL_OCI_TOTAL_IDENTITY
lane: ifrs17
iter: 1
---

## 미결 (orchestrator 작성 — owner 컨펌 2026-08-28)

**항목 32 `기타 포괄손익` 을 신설한다.** 지금 항목25(총계)와 26~30(세부) 합이 안 맞는
잔차의 96% 가 우리 스키마에 슬롯이 없는 구성요소들이다. 그것들을 **하나로 묶어** 한 항목으로 받는다.

owner 결정: 4종을 따로 세우지 않는다. 이 패널의 논지는 금리와 헤지인데 확정급여·환산·재평가·
신용손실은 넷 다 그 이야기가 아니라, 막대를 넷이나 늘릴 값어치가 없다.

### 정의 — 특정 4개를 하드코딩하지 마라

`ifrs-full_OtherComprehensiveIncome` 계열로 태깅된 **leaf row 중 항목26~30 슬롯에 매핑되지 않는
전부의 합**으로 정의해라. 소계 행(`당기손익으로 재분류되는/되지 않는 ... 구성요소`, 재분류 소계 등)은
중복이므로 제외한다.

선행 조사에서 반복 관측된 것들(하드코딩 대상이 아니라 **예시**다):

```
확정급여제도의 재측정요소     ...GainsLossesOnRemeasurementsOfDefinedBenefitPlans
해외사업환산손익             ...ExchangeDifferencesOnTranslation
재평가잉여금 / 자산재평가손익   ...GainsLossesOnRevaluation
기타포괄손익-공정가치측정 신용손실  dart_OtherComprehensiveIncomeNetOfTaxCreditLosses...
```

회사·연도마다 라벨이 다르다(예: `확정급여제도의재측정요소` vs `확정급여제도의재측정요소의 변동`
vs `확정급여부채 재측정요소`). **`account_id` 를 1차 키로 쓰고 `account_nm` 은 보조로.** 정확일치
라벨 매칭은 이 저장소에서 이미 대량 누락을 낸 전례가 있다(삼성생명 2024~2026 통째 누락).

catch-all 이므로 **무엇이 들어갔는지 provenance 를 남겨라.** 회사-분기별로 어떤 `account_id` 가
항목32 에 합산됐는지 기록해야 나중에 "이 기타가 뭐냐" 에 답할 수 있다.

### 기대 효과 (검증 기준)

신설 후 `항목25 == 26+27+28+29+30+32` 가 **282개 대조 가능 셀 중 270개(96%)에서 원 단위로
닫혀야 한다.** 안 닫히면 정의가 틀린 것이다. 남는 12개는 선행 조사에서 원인이 규명돼 있다
(삼성화재 9개 분기 = API 가 leaf 미제공, 푸본현대 2024.3Q = API 부호반전, 별도 티켓 처리 중).

### 게이트

`PL_OCI_TOTAL_IDENTITY`(`scripts/validate_master_tables.py` 의 `PL_EQS`)는 현재 24+25=31 이다.
**항목32 를 반영한 소계 항등식을 추가할지 판단해서 근거와 함께 보고해라.** 넣는다면 위 12셀이
알려진 예외이므로 baseline 등재 방식이 필요하다. 전 버킷 시뮬레이션을 먼저 돌려라 —
룰 수정 전 시뮬레이션은 이 저장소 필수 절차다.

### 화면 (designer 소관 — 이 티켓 범위 아님)

데이터가 들어오면 orchestrator 가 designer 에 별도 발주한다. 워터폴 순서는 금리 관련을 앞에,
기타·지분증권을 뒤에 둔다: `... 26 → 27 → 28 → 30 → 32 → 29 → 31`. designer 가 만든
`기타 포괄손익(미분류)` 잔차 막대는 그대로 두되 항목32 를 뺀 나머지만 받게 되어 대부분 사라진다.

### 선행 조건 — 해제됨 (orchestrator 2026-08-28)

동시에 같은 마스터에 쓰던 두 티켓이 **모두 종결됐다**(`ca827ed` KR0083 부호반전, `72cc896`
KR0032 예실차). 워킹트리에 남은 미커밋 변경은 downloader 레인 것뿐이라 마스터와 무관하다.
**지금 시작해도 된다.** 다만 시작 전에 `git status` 로 다시 확인하고, 끝난 뒤 전수 항등식
감사로 앞선 두 수정이 살아있는지 확인해라 — 특히 아래 두 셀은 반드시 살아 있어야 한다.

```
KR0083 2024.3Q  item27 = △2,652억 · item28 = △53억 · item30 = △5억   (gold override)
KR0032 2026.2Q  item6  = △102억  · item7  = △797억                    (합 △899억)
```

### 같이 메울 것 — 빌더 override 갭 (KR0083 티켓의 잔여)

`scripts/build_pl_breakdown.py:584` 의 override 루프가 `for n in range(1, 25)` 라
**항목 25~31 에는 gold override 훅이 없다.** 그 빌더를 통짜 재실행하면 KR0083 의 정정된 부호가
(여전히 버그인 캐시 때문에) 되돌아간다.

폭발 반경은 현재 작다 — 게이트와 사이트 둘 다 루트 `PL_breakdown.json` 을 읽고
(`validate_master_tables.py:44`), 루트는 `build_root_masters.build_pl()` 의 gold 적용으로
보호된다. `pl_breakdown_master.json` 은 그 파일에 "참고용, 더 이상 검사 대상 아님" 으로 명시돼
있다. **그래도 잠재 불일치이므로 이 티켓에서 같이 메워라** — 어차피 같은 빌더를 건드린다.
항목번호 상한을 새 항목(32 포함)까지 넓히고, 넓힌 뒤 KR0083 3셀이 재빌드를 견디는지 실제로 확인해라.
### 하지 말 것

- 4개 계정을 하드코딩하지 마라. catch-all 정의로 가라.
- 소계 행을 leaf 로 오인해 이중계상하지 마라.
- `index.html`·`IFRS17.html` 금지. 브랜치 변경 금지. `git push` 금지. `git add -A` 금지.
- `build_root_masters.py` 의 `main()` 통짜 실행 금지. `validate_master_tables.py` 는 `--no-build`.
- 마스터 xlsx 는 `sync_master_xlsx_sheet.py` 로 바뀐 시트만. openpyxl 재저장 금지.
- 골든 `tests/test_pl_breakdown_golden.py` 는 `--update` 재생성 + 커밋에 이유 기록.

## 답변 (recipient 작성 — 처리 후)

**신설했다. 검증 결과가 목표(96%/270셀)를 초과했다 — 282개 대조가능 셀 중 273개(96.8%)가 원
단위(반올림 수준)로 닫히고, 나머지 9개(삼성화재, 이미 규명된 원천 결측)는 item32도 정확히
`None`이라 오염 없이 설명된다. 즉 282/282(100%)가 "닫히거나, 왜 안 닫히는지 안다."**

### (1) 정의와 검증 (요청한 96% 재현)

`scripts/fetch_dart_fs.py`에 `_oci32_from_rows()`를 신설했다 — item25(`ifrs-full_
OtherComprehensiveIncome`) 행과 다음 `ifrs-full_ProfitLoss` 행 사이 **위치(ord)** 윈도에서
2개 소계 태그(재분류/비재분류)와 항목26-30이 이미 claim한 것을 뺀 나머지 leaf 전부를 합산한다
— 특정 계정 하드코딩 없음.

구현 중 raw 직접대조로 3가지를 실측 확정했다(전부 이 catch-all 설계를 정확히 만들기 위해
필요했던 것이지, 사후 튜닝이 아니다):
- **TAGGED 행은 `"OtherComprehensiveIncome" in account_id`일 때만 포함.** 케이디비생명
  (KR0072) 2025.4Q·2026.2Q에서 무관한 다른 주석표(`ifrs-full_OtherOperatingIncomeExpense`류,
  "기타영업손익/비용/수익")가 같은 ord 윈도에 우연히 걸려 있어서, 이 필터 없이는 item32가
  실질 오차(수백~수천백만원)를 냈다.
- **UNTAGGED 행(`-표준계정코드 미사용-`)은 census 원안대로 위치만으로 신뢰한다** — 태그
  유무로 차별하지 않는다. 근거: 푸본현대(KR0083) 2023.4Q에 389,702백만원짜리(item25 잔차의
  거의 전부) leaf가 UNTAGGED로 잡히는데, 그 라벨("기타포괄손익-공정가치측정금융자산**관련**
  손익")이 `OCI_NM_FALLBACK[26]`의 정확 문자열("...**평가**손익")과 한 글자 그룹만 다르다 —
  정확일치 폴백만으로는 놓친다. 지시하신 "account_id 1차, account_nm 보조" 원칙이 실전에서
  걸린 지점이다.
- **`OCI_NM_FALLBACK`의 nm-매칭은 untagged 여부와 무관하게 전체 행에 적용된다**(기존
  `_parse()` 동작). 케이디비생명 2026.2Q의 item26이 REAL-하지만-비표준 태그
  (`dart_...ChangeInFairValueOf...`)를 이름으로 claim한 사례에서 처음엔 놓쳐 이중계상됐다
  (item26이 이미 가져간 값을 item32가 또 더함) — 수정 후 해소.

**검증 재현** (전부 오프라인, `data/dart/_fs_api_cache/`만 사용):
```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/validate_item32_from_saved_master.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/residual_distribution_item32.py
```
결과: 282개 item25-보유 셀 중 273개(96.8%)가 1% 이내로 닫힘(132개는 반올림 없이 정확히
0.000000). 221개 "항 6개 전부 존재" 부분집합 기준 top-2 잔차 = KR0032 2026.2Q(0.06%, 반올림
수준) · 교보생명보험 2025.4Q(0.72%, 아래 게이트 절 참고) — 나머지 219개는 ≤0.000001. 9개
(삼성화재해상보험, 9개 분기)는 item32 자체가 `None`(윈도를 못 잡음 — leaf 태그가 원천에
아예 없어 26-30도 이미 None인 것과 정합, 오염 아님).

### (2) 항목32에 실제로 들어간 account_id — provenance

`data/_derived/pl_oci_item32_provenance.json`(267 company-quarter, 회사·분기별 어떤
account_id가 합산됐는지 기록). 전수 집계(`scripts/_probes/summarize_item32_provenance.py`):
**24개사 · 14종 account_id.** 빈도순:
```
247x·23사  확정급여제도의재측정요소 (ifrs-full_...GainsLossesOnRemeasurementsOfDefinedBenefitPlans)
164x·15사  기타포괄손익-공정가치측정 신용손실 (dart_...CreditLossesOfFinancialAssets...)
112x·14사  자산재평가손익/재평가잉여금 (ifrs-full_...GainsLossesOnRevaluation)
 83x·18사  untagged 각종(위치신뢰로 캡처, 라벨 다양)
 57x· 6사  해외사업환산손익 (ifrs-full_...ExchangeDifferencesOnTranslation)
 16x· 6사  관계기업 기타포괄손익지분 (ifrs-full_ShareOfOCI...AssociatesAndJointVentures...)
  7x· 3사  유형자산재평가잉여금 (dart_...RevaluationOfPropertyPlandAndEquipment)
  3x· 1사  삼성화재 전용 공정가치헤지 태그 (dart_...GainsLossesOnHedgingInstrument —
           item28 주석이 명시적으로 배제하는 바로 그 태그, item32가 정확히 그 몫을 흡수)
  기타      특별계정/오버레이접근법 등 5종, 각 1건
```
티켓에 예시로 든 4종(확정급여재측정·해외사업환산·재평가잉여금·신용손실) 모두 최상위 4개에
들었고, **관계기업 지분법 OCI**가 5번째 반복패턴으로 새로 확인됐다 — 예시가 아니라 실측으로
카탈로그를 채웠다.

### (3) override 갭을 메운 뒤 KR0083 재빌드 생존 확인 방법

`build_pl_breakdown.py:584`(`for n in range(1, 25)`, 항목 1-24 행 방출 루프) 자체가 override
"훅"을 막고 있진 않았다 — override 적용 코드(`for _k, _val in ov.items(): v[_k] = _val`,
override 딕셔너리 조회 직후)는 항목번호에 무관하게 동작하고, 항목25-31은 그 아래 별도
`OCI_ITEMS` 루프가 `v.get(n)`으로 방출해 override 값을 그대로 반영한다(정적 코드 추적으로
확인). **실제 갭은 `_GOLD_CELL_OVERRIDE` 딕셔너리에 KR0083 항목이 아예 없었다는 것**이었다
— KR0083 부호수정은 이 딕셔너리가 아니라 별도 메커니즘(`user_pl_cells.json` gold-overlay,
루트만 보호)으로 했었기 때문. `("KR0083","2024.3Q"): {27:-265226.939791, 28:-5322.135208,
30:-536.616012}` 항목을 추가했다(값은 기존 `user_pl_cells.json` 항목과 동일, 재확인 완료).

**"실제로 확인"** — 이 브랜치에서 raw 전체를 재발견하는 `build_pl_breakdown.py::main()` 통짜
재실행은 위험(git-purge로 raw 커버리지가 disk 상태에 종속)해서 하지 않았다. 대신 `main()`이
이 셀에서 실제로 밟을 코드 경로만 분리 재현했다: `_fs_tier1()`로 FS-API t1을 얻고
`assemble()`을 거친 뒤 `_GOLD_CELL_OVERRIDE.get(("KR0083","2024.3Q"))`를 적용 — override
적용 전에는 캐시의 (여전히 버그인) 원래 부호가 나오고, 적용 후에는 3개 값이 정확히
`-265226.939791 / -5322.135208 / -536.616012`로 나옴을 확인했다. `v["_reconciled"]=True`
부작용도 점검 — 이 회사·분기는 items 2-14가 이미 전부 non-null(override 이전에도 Tier-2
RC 게이트 통과 상태)이라 no-op임을 확인.

### (4) 게이트 판단 — `PL_OCI_TOTAL_IDENTITY`에 항목32 반영 등식을 넣었다

**결론: 넣었다.** 근거: 220/221(99.5%)이 기존 `DEFAULT_FLOOR`(200백만/0.1%)로 아무 예외 없이
통과했고, 유일한 예외 1건(9개가 아니라 1개 — 삼성화재 9개 분기는 항 자체가 None이라 기존
PL_EQS 의미론대로 자동 skip, fail 아님)은 원인이 완전히 규명됐다: 교보생명보험 2025.4Q는 CF헤지
개념을 비표준 태그 2개로 이중공시하고(`dart_GainsValuationDerivativesCashFlowHedge`=item28이
실제로 취하는 dominant 태그 vs `dart_LossesValuationDerivativesCashFlowHedge`=+1283.875백만,
`ACCT_OCI_28_FALLBACK` 리스트 4번째라 도달 못 함), 두 태그 다 item32의 claimed set에 포함돼
있어 **item28에도 item32에도 안 잡힌다** — `ACCT_OCI_28_FALLBACK`의 기존 주석("dominant 태그만
취함, 부호관례 불확실한 나머지와 넷팅 안 함")이 이미 설명한 설계의 그림자이지 item32 결함이
아니다. `validate_master_tables.py::PL_EQS`에 9번째 등식으로 추가했고 이 1건을 `data/_gold/
pl_bridge_baseline.json`에 등재했다(class `dart_dual_tag`, 근거 전문 포함). 전 버킷
시뮬레이션(`--no-build` 수정 전/후 diff): pass 2805→3025(+220) fail 12→13(+1, 등재됨)
skip 387→522(+135, 26-30 중 하나라도 기존부터 None인 셀 — 대부분 삼성화재+FVOCI지분증권
미보유사, 추측 대신 스킵). `test_identity_registry.py::REGISTRY["pl_bridge"]`는
`_check_pl_bridge` 함수 전체를 가리키는 기존 항목이라 별도 신규 등록은 불요했고, measured
텍스트만 최신 수치로 갱신했다.

### (5) 전수 항등식 감사

`scripts/_probes/full_identity_audit_item32.py` (재현 가능, 오프라인):
```
=== 1. Row-count / cell-count sanity ===
before: 11190 rows / 11190 unique keys
after:  11546 rows / 11546 unique keys
added: 356  removed: 0  changed: 0
PASS: exactly item32 rows added, zero rows removed or modified elsewhere.

=== 2. Ticket-flagged cells survive ===
  OK   KR0083 item27 2024.3Q: expected=-265226.939791 actual=-265226.939791
  OK   KR0083 item28 2024.3Q: expected=-5322.135208 actual=-5322.135208
  OK   KR0083 item30 2024.3Q: expected=-536.616012 actual=-536.616012
  OK   KR0032 item6 2026.2Q: expected=-10243.0 actual=-10243.0
  OK   KR0032 item7 2026.2Q: expected=-79693.0 actual=-79693.0
PASS: all 5 flagged cells match exactly.

=== 4. Company-quarter group count unchanged ===
before: 356  after: 356  (unchanged: True)
ALL CHECKS PASS.
```
`insurequant_master_tables.xlsx`도 "손익분해PL" 시트에 항목32 356행이 정확히 반영됨을
확인(`sync_master_xlsx_sheet.py` 자체 검증 "11546행×9열 완전 일치" + xlsx 재오픈 카운트
교차확인).

**오프라인 테스트 94개 중 93 passed·1 skipped**(`RUN_PL_GOLDEN` 게이트, 통짜 재실행이라
의도적 미실행) — kics_rules·master_tables(golden 갱신 완료)·post_transition·deploy_assets·
rule_coverage_manifest·identity_tautology·identity_registry(golden 갱신 완료)·
push_gate_wiring·dividend_golden 전부 통과. **유일한 1 FAIL은 `test_ifrs17_bs_golden.py`**
(다른 빌더 `build_ifrs17_bs.py` — `fetch_dart_fs.py`에서 그쪽이 쓰는 `resolve_corp`/`REPRT`는
이번 세션 diff에 없음, `IFRS17_BS.json` 자체도 `git status` clean, 테스트 자체가 실패 시
자동복원). 이번 작업과 무관한 공유워크트리 드리프트로 판단해 별도 task로 분리
발주했다(task_d1a18657, item32 범위 밖).

### 마스터 반영 (개별 빌더만, `main()` 미실행)

`pl_breakdown_master.json`을 `scripts/_probes/apply_item32_to_pl_master.py`(356개
(코드,분기) 전부에 `tier1_for()` 재호출 — `_fs_api_cache/`만 읽음, raw 무관)로 직접 패치
11190→11546행(+356) → `build_root_masters.build_pl()` **개별 호출**(`run_build_pl_only.py`,
`main()`·`build_csm()` 미실행)로 루트 `PL_breakdown.json` 동일 전파 → `sync_master_xlsx_sheet.py
"손익분해PL"`로 xlsx 동기화. 골든 2종(`pl_breakdown_golden.json`·`master_tables_golden.json`)
`--update`(빌더 재실행 아님, 디스크 현재 파일 해싱만 — 매 sha256 이동을 combo-diff로 사전 확인
후 재생성).

### 커밋

`fix/csm-product-segmented-columns` 브랜치에 커밋 예정(이 답변 작성 직후). 커밋 해시는
`git log -1`로 확인 가능 — TODO_parser_ifrs17.md 55th pass 항목에 상세 기록.

status: resolved (자기완결 — 모든 주장이 재현 명령·실측 수치로 뒷받침됨, 원 sender 재확인
불요 판단).
