# Agent: IFRS17 DART Disclosure

**목표:** 금감원 DART 분기/반기/사업보고서에서 IFRS17 관련 주요 재무 테이블 파싱.

> **⚠️ 2026-07-22 — PL 빌더가 패키지로 분할됐다. 핸들러 수정 전 필독.**
>
> `scripts/build_pl_breakdown.py`(4,885줄) → 엔트리 567줄 + `scripts/pl_breakdown/`
> (`common` 34 · `tier1` 355 · `tier2` 475 · `companies` 3,438).
>
> - **회사별 주석 대응 = `pl_breakdown/companies.py`** 에 함수 추가 후 파일 끝
>   `SONBO_HANDLERS` / `LIFE_HANDLERS`에 **등록**. 등록 안 하면 죽은 코드가 된다
>   (실제로 `extract_tier2_koreanre`가 그 상태였다 — 디스패치는 철자가 다른
>   `extract_tier2_coreanre`를 쓰고 있었고, 2026-07-22 제거).
> - **24-항목 조립·항등식·gold override는 엔트리 스크립트**(`assemble`,
>   `_GOLD_CELL_OVERRIDE`)에 남아 있다.
> - **의존은 단방향**: `companies → tier1/tier2/common`, `tier1 ↔ tier2` 간선 0.
>   companies가 바깥에서 쓰는 이름 11개는 파일 상단에 명시적 import로 적혀 있다.
> - **고쳤으면 골든 게이트 필수**: `RUN_PL_GOLDEN=1 python -m pytest
>   tests/test_pl_breakdown_golden.py` (~95초, 결정론적·오프라인). 값이 의도적으로
>   바뀐 경우에만 `python tests/test_pl_breakdown_golden.py --update`로 재생성하고
>   **왜 움직였는지 커밋에 적을 것.**
>
> 운영 상세(회사별 함정 포함) = `.claude/skills/ifrs17-parser/SKILL.md`
> "PL breakdown is a package now".

> **⚠️ 2026-07-22 — 골든 테스트 + DART 캐시 정정공시 절차 (수정 전 필독).**
>
> - **`fill_post_transition_to_disclosure.py`** (경과조치 적용후, 라이브 마스터 인플레이스
>   기록): `_extract_post_values` 569→389줄 분해(`_apply_post_corrections` 신설). 고쳤으면
>   `python -m pytest tests/test_post_transition_golden.py`(6,114셀 고정, 오프라인).
> - **viz 빌더 골든**: `viz_build_ifrs17_panels.py`(4패널)·`viz_build_csm_waterfall.py`를 고치면
>   `python -m pytest tests/test_viz_{ifrs17_panels,csm_waterfall}_golden.py`. 두 빌더는
>   `data/dart/viz/`를 인플레이스로 덮어쓰므로 골든이 백업·복구한다. 의도적 변경 시 `--update`.
> - **DART FS 캐시 정정공시**: `_fetch_raw`는 캐시를 만료 없이 신뢰한다. DART 정정공시가 뜨면
>   `python scripts/fetch_dart_fs.py --refresh <corp_code> <year>` → 마스터 재빌드 → PL 골든
>   재생성 → 캐시+마스터+골든 함께 커밋. owner 정책: 캐시는 계속 커밋(정정공시 드묾).
> - 상세 절차 = SKILL "경과조치 적용후" / "viz 빌더 골든" / "DART FS API 캐시" 절.

> **⚠️ 2026-08-28 — PL_breakdown 항목25-31(기타포괄손익~총포괄손익) 소계-구성요소 불일치 원인 규명.**
>
> 항목25(기타포괄손익 총계, `ACCT_OCI[25]="ifrs-full_OtherComprehensiveIncome"`)와 항목26-30
> (5개 세부: FVOCI채무증권/보험계약금융손익/CF헤지/FVOCI지분증권/재보험금융손익) 합이 대량으로
> 안 맞는 티켓(`inbox/parser/20260828T0700Z`) 조사 결과. **파생값으로 갈아끼우지 않고** 원인만
> 규명, 마스터는 무수정. 356개 (회사,분기) 셀 중 로컬 raw+FS-API 캐시로 대조 가능한 282개를
> 전수 재구성(`_fs_api_cache/*_OFS.json`의 CIS 섹션에서 항목25 행과 다음 `ifrs-full_ProfitLoss`
> 행 사이 **모든** 태깅된 leaf row를 합산 — 우리 5개 슬롯만이 아니라 원천이 실제로 가진 전부).
>
> - **270/282(96%) 는 원천이 스스로 정합적이다.** DART FS-API가 이미 태깅해 둔 leaf row를 전부
>   더하면 항목25에 원 단위로 일치한다 — 다만 **그 leaf 중 다수가 우리 5-슬롯 스키마에 없다**:
>   `ifrs-full_OtherComprehensiveIncomeNetOfTaxGainsLossesOnRemeasurementsOfDefinedBenefitPlans`
>   (확정급여제도의 재측정요소), `...ExchangeDifferencesOnTranslation`(해외사업환산손익),
>   `...GainsLossesOnRevaluation`(자산재평가잉여금),
>   `dart_OtherComprehensiveIncomeNetOfTaxCreditLossesOfFinancialAssetsMeasuredAtFairValueThrough
>   OtherComprehensiveIncome`(기타포괄손익-공정가치측정 신용손실) 4종이 여러 회사에 걸쳐 반복
>   확인됐다(DB손해보험·코리안리·신한라이프·메리츠·교보생명 등). **즉 항목25≠sum(26-30)의 지배적
>   원인은 "API가 본문보다 불완전"이 아니라 "우리가 뽑는 항목이 원천 leaf 전체보다 적다".** 4종을
>   새 항목으로 추가할지는 별도 owner 판단 — 이미 FS-API 캐시에 태깅돼 있어 재다운로드 불요.
> - **삼성화재(KR0008) 2023.3Q~2025.3Q(9개 분기)는 진짜 API 결측이다.** 이 구간은 FS-API가
>   기타포괄손익 총계 + 재분류/비재분류 두 소계 행만 주고 **leaf row를 단 하나도 안 준다**
>   (leaf 태그 자체가 없음 — 마스터 항목26-30은 정확히 None, 오염 아님). **2025.4Q부터는 DART
>   쪽에서 자체적으로 leaf 태그가 나타나기 시작**해 정상 정합(항목25 vs sum(26-30) 잔차 <1%).
>   즉 회사 고유가 아니라 **그 회사의 그 시기 제출분에 한정된 DART 태깅 관행**으로 보인다.
>   9개 분기의 항목26-30을 채우려면 FS-API가 아니라 raw XML 본문표 직접 파싱이 필요 — 미착수,
>   범위 밖.
> - **푸본현대생명(KR0083) 2024.3Q는 유일하게 확인된 DART API 부호반전 결함이다.** raw XML
>   (`data/dart/FY2024_Q3/raw/KR0083_푸본현대생명보험/20241114000568.xml` L5670-5710, 괄호=음수)
>   과 캐시(`data/dart/_fs_api_cache/00459844_2024_11014_OFS.json`)를 직접 대조: CF헤지·
>   재보험금융손익·보험계약금융손익 3개 태그의 `thstrm_add_amount`(당기 누적) 부호가 원문과
>   반대(같은 태그의 `thstrm_amount`(당기 3개월)는 정상). 셋 다 손으로 부호만 뒤집으면 소계
>   -149,010,393,849원과 원 단위로 일치. **282개 대조 가능 셀 중 이 1건만** 해당 — 전수census
>   에서 다른 부호반전 사례 없음. DART 원천 결함으로 판단됐고, **2026-08-28 후속 티켓
>   (`inbox/parser/20260828T1200Z`)에서 orchestrator 지시로 수정 완료** — 아래 addendum 참고.
>
> 재현: `scripts/_probes/oci_full_universe_census.py` (오프라인, `_fs_api_cache/` + 로컬
> `data/dart/FY*/raw/*/meta.json`만 사용). 상세 = 티켓 `inbox/_resolved/` 이관본.
>
> **➕ 2026-08-28 addendum — 위 KR0083 건 수정 + 동일결함 전캐시 census (`inbox/parser/
> 20260828T1200Z`, resolved).** 항목27/28/30 `값`(누계) 부호만 반전(값_당분기는 미손, 하류
> 재계산으로 자연 정정 — 아래). 셀단위 패치 2곳: `data/dart/viz/pl_breakdown_master.json`
> (`scripts/_probes/fix_kr0083_2024q3_oci_sign.py`, 3줄만 diff) + `data/_gold/user_pl_cells.json`
> gold override 3건 신설(근거 전문 포함) — `build_root_masters.build_pl()`(개별 호출, `main()`
> 아님) 재실행해 root `PL_breakdown.json`도 정정, 이때 항목27/28/30의 `값_당분기`가 YTD차분으로
> **자동** 재계산되어 raw의 당3개월 열과 소수점까지 정확히 일치(예: 항목27 -139173.254688 =
> raw "보험계약자산(부채)순금융손익" 당3개월 그대로) — 손으로 안 건드려도 정정됨을 확인.
> 2024.4Q의 `값_당분기` 3건도 기저(2024.3Q YTD) 정정에 따라 올바르게 리플(정상 동작, 버그
> 아님). combo-diff(cell-key=(코드,항목,분기) 전수, `scripts/_probes/combo_diff_kr0083_fix.py`):
> 11190행→11190행 불변, 변경 정확히 6셀(위 3항목×2분기), 손실/추가 0, 원수사명 등 타필드 변경 0.
> **`pl_breakdown_master.json`은 override로 보호 안 됨** — `_GOLD_CELL_OVERRIDE`(build_pl_
> breakdown.py)는 항목1-24만 커버하고 25-31(OCI 확장)엔 override 훅이 없어서, 그 빌더를
> 통짜 재실행하면 이 3셀은 (여전히 버그인) FS-API 캐시에서 다시 잘못된 부호로 채워진다 —
> `RUN_PL_GOLDEN=1 pytest tests/test_pl_breakdown_golden.py`도 빌더를 재실행하므로 **이 세션에서
> 의도적으로 미실행**. root `PL_breakdown.json`은 `user_pl_cells.json` override가 빌드 마지막
> 단계에서 무조건 UPSERT하므로 안전(실측: `build_pl()` 재실행 로그 "pl overrides: 199 set").
> **census(같은 결함 전캐시 재검색, `scripts/_probes/census_dart_sign_reversal.py` +
> `_census_summarize.py`)**: 판별식(캐시 thstrm_amount/thstrm_add_amount 부호반대)을 IS/CIS
> 전체(1040개 캐시파일, 8,753 rows in-scope) 돌리고 같은-FY 직전분기 YTD연속성으로 자동 교차검증
> — "SIGN-BUG-LIKELY" 6건 중 3건은 위 KR0083(확정), 나머지 3건(KR0082 DB생명보험 2024.1Q
> 항목27/28/30)은 raw XML 직접 대조 결과 **다른 현상**: 원문 표 자체가 당기 3개월=당기누적이어야
>할 Q1인데 두 컬럼이 정확히 부호만 반대(같은 크기) — 상위 소계("후속적으로 당기손익으로
> 재분류될 수 있는 항목" -142,381,181,792원)를 항목26/28/27/30/신용손실 leaf로 원 단위 검산하니
> **음수 쪽이 맞고 마스터는 이미 그 값을 쓰고 있음** → 손대지 않음(오탐, 건드리면 오히려 깨짐).
> "?"(직전분기 YTD 없어 자동판정 불가, 대부분 2023.3Q — 기존에 이미 문서화된 2023.1Q/2Q 결측의
> 여파) 44건 중 상위후보 10건 shortlist, 대표로 KR0032(NH농협손해보험) 2023.3Q 항목1(보험손익,
> P&L 헤드라인)을 raw 직접확인 — 당3개월 -493.36억/당누적 +639.66억은 원문 표 자체가 그렇게
> 찍혀 있고(Q3라 3개월≠누적이 정상) 내부모순 없음 → 통상적 분기 변동성, 버그 아님. 나머지 shortlist·"neither-
> close"(15건, 2%허용오차 미달)는 이 패턴(값이 원천과 자체정합)과 동일 소견으로 판단, 개별
> raw대조는 생략(패턴 근거는 위 KR0032/KR0082 두 대표사례). **결론: KR0083 외 추가 수정 0건.**
> data/_derived/dart_sign_reversal_census{,_summary}.json에 전 후보 원장.

> **➕➕ 2026-08-28 — 항목32 `기타 포괄손익(미분류)` 신설 (owner 컨펌, ticket `inbox/parser/
> 20260828T1600Z`, resolved).** 위 두 addendum이 규명만 하고 남겨둔 "항목25≠sum(26-30)의
> 96%는 우리 5-슬롯이 원천 leaf 전체보다 좁아서"를 실제 항목으로 메웠다. **정의는 catch-all**
> (특정 계정 하드코딩 아님): `fetch_dart_fs.py::_oci32_from_rows` — 그 필링의 CIS 섹션에서
> item25(`ifrs-full_OtherComprehensiveIncome`) 행과 다음 `ifrs-full_ProfitLoss` 행 사이
> (ord 기준 위치 윈도, census와 동일 경계) 모든 leaf를 스캔해, 2개 재분류/비재분류 소계 태그와
> 항목26-30(+`ACCT_OCI_28_FALLBACK`·`OCI_NM_FALLBACK`가 이미 claim한 것)을 뺀 나머지를 합산.
>
> **TAGGED 행 vs UNTAGGED 행에 다른 필터**(구현 중 실측으로 확정, 셋 다 raw 대조 완료):
> - TAGGED 행은 `"OtherComprehensiveIncome" in account_id`일 때만 포함 — 케이디비생명(KR0072)
>   2025.4Q/2026.2Q에서 그 윈도 안에 `ifrs-full_OtherOperatingIncomeExpense` 계열(기타영업손익/
>   비용/수익, OCI와 무관한 다른 주석표)이 ord 우연으로 같이 걸려 있어서 필요했다 — 이 필터
>   없이는 item32가 이 무관한 행들까지 합산해 반올림 아닌 실질 오차를 냈다.
> - UNTAGGED 행(`account_id == "-표준계정코드 미사용-"`)은 **윈도 위치만으로 신뢰**한다(census
>   원안과 동일 — 태그 유무로 차별 안 함). 이유: 푸본현대(KR0083) 2023.4Q에 `기타포괄손익-
>   공정가치측정금융자산관련손익`(389,702백만, item25 잔차의 거의 전부)이 UNTAGGED로 잡히는데,
>   그 라벨이 `OCI_NM_FALLBACK[26]`의 정확 문자열("...평가손익")과 한 글자 그룹만 다르다
>   ("...관련손익") — 정확일치 폴백만으로는 놓친다. 이 저장소가 이미 경고한 라벨-변형 함정의
>   실물 사례. 단 소계 행이 UNTAGGED로 나올 가능성에 대비해 `OCI_SUBTOTAL_NM`(문자열 소계
>   2종)도 별도로 배제한다.
> - `OCI_NM_FALLBACK`의 nm-매칭은 **untagged 여부와 무관하게** 전체 행에 적용된다는 걸 재확인
>   (기존 `_parse()` 동작 그대로) — 케이디비생명 2026.2Q의 item26이 REAL-하지만-비표준 태그
>   (`dart_...ChangeInFairValueOf...`)를 이름으로 claim한 사례. item32도 이 규칙을 그대로
>   따라야 이중계상을 피한다(처음엔 "untagged일 때만 nm-claim 인정"으로 짰다가 이 사례로
>   깨짐 — item26이 이미 가져간 값을 item32가 또 더해 잔차가 item26 크기만큼 뜸).
>
> **검증(282개 item25-보유 셀, `scripts/_probes/validate_item32_from_saved_master.py`,
> `data/dart/_fs_api_cache/`만 사용 — 오프라인): 282/282(100%) 설명됨** — 273개(96.8%)가
> `항목25==26+27+28+29+30+32`를 1% 이내로 닫고(그중 132개는 반올림 없이 정확히 0.000), 9개
> (삼성화재 KR0008, 이미 규명된 리프 결측 구간)는 item32도 정확히 `None`(오염 없음, 26-30도
> 전부 None인 것과 정합). **결정론 항등 검증 221건 기준 top-2 잔차**: KR0032 2026.2Q
> 175.14백만(0.06%, 반올림), 교보생명보험 2025.4Q 1283.9백만(0.72%) — 후자는 DART 이중
> CF헤지 태그(아래 baseline 참고), 나머지 219건은 ≤0.000001(부동소수 잡음 수준).
>
> **Provenance**: `data/_derived/pl_oci_item32_provenance.json`(267 company-quarter, 회사·
> 분기별 어떤 account_id가 합산됐는지). 전수 집계: 24개사·14종 account_id — 최다순
> 확정급여재측정(247x·23사)·신용손실(164x·15사)·자산재평가(112x·14사)·untagged 각종(83x·18사)·
> 해외사업환산(57x·6사)·**관계기업 기타포괄손익지분**(16x·6사, 티켓의 4예시엔 없던 5번째
> 반복패턴)·유형자산재평가(7x·3사)·삼성화재 전용 공정가치헤지 태그(3x, item28이 명시적으로
> 배제하는 바로 그 태그 — item32가 정확히 그 몫을 받는다, 설계대로)·특별계정/오버레이접근법
> 등 소수 태그.
>
> **게이트**: `validate_master_tables.py::PL_EQS`에 9번째 등식(`기타포괄손익 =
> FVOCI채무증권+보험계약금융(OCI)+위험회피파생상품+FVOCI지분증권+재보험금융(OCI)+기타(미분류)`)
> 신설, DEFAULT_FLOOR(200백만) 그대로. 전 버킷 시뮬레이션(`--no-build` 전/후 diff): pass
> 2805→3025(+220) fail 12→13(+1, 아래) skip 387→522(+135, 항 하나라도 None인 셀 — 대부분
> 삼성화재+FVOCI지분증권 미보유사, 추측 대신 스킵). 신규 fail 1건(교보생명보험 2025.4Q)은
> `data/_gold/pl_bridge_baseline.json`에 등재(원인: raw 확인 결과 이 필링만 CF헤지를 비표준
> 태그 2개로 이중공시 — `dart_GainsValuationDerivativesCashFlowHedge`(item28이 실제로 쓰는
> dominant 태그) vs `dart_LossesValuationDerivativesCashFlowHedge`(+1283.875백만, item28
> fallback 리스트 4번째라 도달 못 함) — 둘 다 item32의 claimed set 안이라 item32에도 안 잡힘.
> `ACCT_OCI_28_FALLBACK` 주석에 이미 문서화된 "dominant 태그만 취함" 설계의 그림자이지 item32
> 결함이 아니다). `test_identity_registry.py::REGISTRY["pl_bridge"]`는 기존 `_check_pl_bridge`
> 전체를 가리키는 항목이라 별도 등록 불요 — measured 텍스트만 갱신.
>
> **KR0083 override 갭도 같이 메움**: `build_pl_breakdown.py::_GOLD_CELL_OVERRIDE`에
> `("KR0083","2024.3Q")` 항목27/28/30 추가(`user_pl_cells.json`과 동일 값) — 이전엔 이
> override 딕셔너리에 항목25-31 슬롯을 쓴 사례가 없어서, 이 빌더를 통짜 재실행하면
> `pl_breakdown_master.json`만 부호가 되돌아갈 잠재 위험이 있었다(루트는 `user_pl_cells.json`
> gold-overlay가 항상 보호). `_reconciled=True` 부작용 확인: 이 셀은 items 2-14가 이미
> non-null(override 이전에도 Tier-2 RC 게이트 통과 상태)이라 no-op.
>
> 마스터 반영: `pl_breakdown_master.json` 11190→11546행(+356, 항목32만 신규 — combo-diff로
> 변경/삭제 0 확인), `PL_breakdown.json` 동일하게 전파(`build_root_masters.build_pl()` 개별
> 호출, `main()` 미실행). 재현: `scripts/_probes/{apply_item32_to_pl_master,
> validate_item32_from_saved_master,residual_distribution_item32}.py` (모두 오프라인).

> **⚠️ 2026-08-29 — PL 폐쇄식은 8개 항목을 **원리상** 검증하지 못한다. "닫혔으니 맞다"로 판단하지 말 것.**
>
> `assemble()` 이 잔차(plug)로 만드는 항목이 있어서, 그 항목을 우변에 갖는 등식은 **산수상
> 깨질 수가 없다.** 상류에서 잘못 뽑아도 잔차가 그 오차를 그대로 흡수한다.
>
> | 항목 | 계산식 | 무력화되는 등식 | 그래서 무검사가 되는 항목 |
> |---|---|---|---|
> | item7 기타생명장기원수손익 | `3 − (4+5+6)` | `3 = 4+5+6+7` | **5(원수RA) · 6(원수예실차)** |
> | item12 기타생명장기재보험손익 | `8 − (9+10+11)` | `8 = 9+10+11+12` | **9(재보험CSM상각) · 10 · 11** |
> | item18 투자이익 | `17 − 19` (2층 무조건) | `17 = 18+19` | **19(보험금융손익)** |
> | item21 영업외손익 | `22 − 20` (410/418) | `22 = 20+21` | — |
> | item23 법인세 | `22 − 24` (418/418 무조건) | `24 = 22−23` | **23(법인세)** |
>
> 실측(CONSTRUCTIVE 변이시험 — 그 칸을 흔들고 빌더가 계산하는 하류 항을 빌더와 똑같이 다시
> 계산): 위 8개 항목 전부 **탐지율 0.0%**. `validate_master_tables` 와 `validate_data_contract`
> 를 다 물려도 신규 RED 0 건이다. 재현: `scripts/_probes/probe_20260829_pl_eqs_mutation.py` ·
> `probe_20260829_pl_eqs_datacontract_mutation.py`.
>
> **item6(예실차)에 특히 주의.** 2026-08-29 에 3개사 50분기를 채웠는데 **폐쇄식은 그 값을
> 전혀 검증하지 못했다.** 그날 실제로 쓴 검증은 전부 **독립 앵커**였다 — 농협생명 보험수익
> 510,001 일치 · 미래에셋생명 3중 대사 594,378,172,139(원) · 에이비엘생명 산문 공시 50억/3억 ·
> 서울보증보험 소계 검산. 예실차를 채우거나 고칠 때는 **원문 표를 다시 읽는 것만이 검증**이고,
> `3 = 4+5+6+7` 이 닫히는 것은 아무 증거도 아니다.
>
> **item9(재보험CSM상각)에는 대안 축이 없다.** 유일한 후보였던 CSM 워터폴에 **출재 축 자체가
> 없다** — `build_csm_waterfall_master.py` 가 `_EXCLUDE_KW = ("재보험","출재","보유한재보험",…)`
> 로 전 단계에서 배제하고, `CSM_waterfall.json` 은 6항목(기초·신계약·이자·가정·상각·기말)
> 단일 축 2,172행이다(출재 항목 0). **그 배제는 옳다** — 출재는 보유 재보험계약자산의 별도
> 워터폴이라 발행계약 워터폴에 더하면 안 된다(실측: `원수+재보험` 식은 346버킷 중 245건이
> ±1% 밖, `원수+수재`는 20건). 따라서 `CSM_AMORT_PL_LEGS` 를 넓히는 방식은 답이 아니다.
> 만들려면 **파서가 출재 rollforward 를 별도 마스터로 추출**해야 한다(원문에는 있다 — 캡션
> "원수 및 출재 …" 다수 관측). 신규 과제이고, 그때까지 item9 는 원문 재대조만이 수단이다.
>
> **item22(세전이익)만 2026-08-29 에 메웠다.** 원천 법인세 계정
> (`ifrs-full_IncomeTaxExpenseContinuingOperations`)이 418/418 FS-API 캐시에 있는데 `assemble()`
> 이 곧바로 잔차로 덮어써서 버려지고 있었다. 그 값을 되살려 `|item22 − item24|` 와 크기 대조하는
> 룰이 `validate_master_tables._check_tax22_crosscheck`(게이트 2f) 다 — 부호는 발행사 관행이
> 갈려서 안 본다. 전 버킷 시뮬레이션 **282/282 PASS · 신규 FAIL 0**(잔차 max 0.000백만원),
> 변이시험 탐지율 **0.0% → 100.0%**.
>
> 이 사실들은 코드에도 박혀 있다(`validate_master_tables.PL_EQ_EVIDENCE` ·
> `PL_ITEMS_UNCHECKABLE_BY_EQUATION`)이고, `tests/test_rule_coverage_manifest.py` 의
> `PL_CONSTRUCTIVE_BLIND` / `PL_CONSTRUCTIVE_GUARDED` 가 변이시험으로 매 push 검증한다.
> **커버리지를 늘리면 그 매니페스트가 갱신을 강제한다.**

## 0. 운영 환경 & 회사 매핑 규칙

- **OpenDART API key**는 `.env`의 `OPENDART_API_KEY`에서 읽음 (코드에 박지 말 것, 로그에도 찍지 말 것).
- **회사 매핑은 그냥 회사명으로 검색.** "메리츠화재" 한 단어 던지면 얼추 나옴. KR0001 ↔ corp_code 8자리 영구 매핑 파일은 만들지 말 것. 사용자의 명시적 지시.

### 0.1 모듈/스크립트 레이아웃 (2026-05-23 부트스트랩)

- 모듈: `src/ifrs17/`
  - `config.py` — `.env`만 읽음 (값/소스 모두 로그 X).
  - `opendart_client.py` — REST 래퍼. 주요 메서드:
    - `ping()` — `status=000` 확인.
    - `find_corp_codes_by_name(query)` — master XML substring 매칭. 첫 호출 시 `data/dart/raw/CORPCODE.xml`을 자동 다운로드 후 캐시.
    - `list_filings(corp_code, bgn_de, end_de)` — 정기공시 목록.
    - `fetch_document_xml(rcept_no, dest)` — filing 본문 zip 다운로드.
  - `csm_extractor.py` — CSM 상각 표 추출기 (semantic scoring, §3.2).
  - `measurement_extractor.py` — §14(4) 측정요소 롤포워드 skim (A1, §2).
  - `liability_extractor.py` — 보험계약부채 구조 skim (B3/P4).
  - `universe.py` — 운영 유니버스·slice 규칙 (Open Q1–Q9).
- 데이터: `data/dart/`
  - `raw/CORPCODE.xml` — 회사명 검색용 마스터 (캐시).
  - `raw/<canonical_corp_name>_<rcept_no>/document.zip + *.xml` — filing 원본.
  - `extracted/<canonical_corp_name>_<rcept_no>_csm.json` — 정규화된 CSM 표 후보.
- PoC 스크립트: `scripts/ifrs17_*.py`
  - `ifrs17_verify_api_key.py` / `ifrs17_smoke_search.py` / `ifrs17_fetch_one_filing.py` / `ifrs17_extract_csm_poc.py` / `ifrs17_batch_poc.py`

### 0.2 회사명 검색 주의사항

- substring 매칭이라 모호한 입력은 자회사가 먼저 잡힘. 예:
  - `"삼성생명"` → 1순위 **삼성생명서비스** (자회사). 진짜 본사는 `삼성생명` (정확 일치).
  - `"삼성화재"` → 1순위 **삼성화재해상보험** (본사). OK.
- `batch_poc`는 `corp_name == query` exact 매치를 우선시하지만, 호출자가 풀네임 (`"삼성생명보험"`, `"한화생명"`, `"교보생명보험"` 등)을 주는 게 안전.

### 0.3 분석 목표 & 범위 (2026-05-23 확정)

**다운스트림 Insight (Product goal):**

- **Earnings quality:** 이 회사 손익이 **CSM release(보험서비스)** 에 기대는지, **투자수익·보험금융손익(IFIE)** 에 기대는지.
- **Forward support:** CSM 변동(기초 → 신계약 → 가정변동 → 상각 → 기말)과 **향후 상각 스케줄**로 “앞으로 수익이 어느 정도 받쳐주는지”.
- **Reinsurance & risk:** 출재 재보험 구조·순원가(마진)·불이행위험이 순손익·CSM에 미치는 영향.
- **Assumption fragility:** 계리적 가정·**민감도** 충격이 LIC/CSM/당기손익에 미치는 규모.

**분석 Slice (보종):**

- **생명·장기 부문만** 집중. 일반·자동차 등 단기 손보 라인은 스크래핑·분석 대상에서 **제외**.
- **손보사:** 주석 14 등에서 **`장기`** 열 (또는 동의어 `생명장기`, `장기손해`).
- **생명보험사:** **`장기` 라벨 없음 → 전사 합계**를 손보 `장기`와 peer 비교 proxy로 사용 (2026-05-24 확정). UI/JSON 메타: `slice_label=whole_company_life`.
- **운영 유니버스 (2026-05-24):** K-ICS 37社 − 비상장 12 − AIG 1 − 서울보증 1 = **실질 23社** (사업보고서 CSM ok). 코드: `src/ifrs17/universe.py`.

**측정모형 (2026-05-24 Q6 확정):**

- 대표값은 **`total_csm`** (3열 합산). “대부분 공정가치법” 가정 **금지**.
- 공시가 **`수정소급법` / `공정가치법` / `그 외 보험계약` 3열**로 분리되어 있으면 **별도 컬럼을 조건부 보존** (material할 때만; downstream은 `total_csm` 우선).
- **VFA(보험료배분접근법):** 1차 로드맵에서 별도 Tier로 두지 않음. §(5) 보험손익 상세에 VFA 블록이 material하면 후속 추가.

**공시 위치 (참고 — 메리츠화재 2024 사업보고서):**

- 별도재무제표 주석 **`14. 보험계약자산부채`** (`*_00760.xml` 등 부속 XML). (1)~(10) 하위 절 + 리스크관리 주석 **가정민감도**.

---

## 1. 키 지표 스크래핑 우선순위 (마스터 인덱스)

| Tier | table_id | 주석 절 (메리츠 기준) | slice | 상태 |
|---|---|---|---|---|
| **A1** | `measurement_rollforward` | §14 **(4)** 측정요소별 변동내역 | 원수 × **장기** (생보: **전사**) | 🔲 PoC (`measurement_extractor.py`) |
| **A2** | `csm_amort_schedule` | §14 **(7)** CSM 향후 상각 | 원수/출재 × **장기** | ✅ PoC (`csm_extractor.py`) |
| **A3** | `insurance_pl_detail` | §14 **(5)** 보험손익 상세 | **장기** | 🔲 미구현 |
| **A4** | `reinsurance_rollforward` | §14 **(3)(4)** 출재 변동·측정요소 | 출재 × **장기만** (일반·자동차 출재 블록 **별도 table_id 저장 안 함** — Q7) | 🔲 미구현 |
| **B1** | `bs_snapshot` | §14 **(1)** 자산부채 현황 | **장기** | 🔲 미구현 |
| **B2** | `new_business_impact` | §14 **(6)** 최초 인식 계약 영향 | **장기** | 🔲 미구현 |
| **B3** | `liability_rollforward` | §14 **(3)** 보험부채 변동 (잔여보장/발생사고) — **§8 multi-index와 동일 테이블** (Q9 통합) | 원수 × **장기** | 🔲 Skimming only |
| **B4** | `ifie_bridge` | §14 **(8)(9)** + 손익계산서 | 전사 / **장기** where split | 🔲 미구현 |
| **B5** | `assumption_sensitivity` | **K-ICS 분기 공시** 가정민감도 (primary); DART 주석은 secondary/future (Q8) | **장기** / 원수 잔여보장 | 🔲 미구현 |

**Minimum viable scrape set (Insight MVP):** A1 + A2 + A3 + **A4** + B1 + B5 (+ 손익계산서 투자·IFIE 라인).

---

## 2. Tier A — CSM / 측정요소 롤포워드 (`measurement_rollforward`)

**CSM 변동분석의 본체.** 사용자 mental model:

> 기초 CSM + 신계약 CSM − CSM 상각 ± (CSM 조정/비조정) 계리적 가정 변동 ≈ 기말 CSM

실제 공시는 IFRS 17 §92 스타일로 더 촘촘함. **CSM 3열 합산** 후 아래 row alias에 매핑.

### 2.1 캡션·위치

- `(4) 원수 및 출재 측정요소별 변동내역` → `1) … 원수 … 보험부채 상세변동내역` (**장기** 블록).
- 헤더 컬럼: `미래 현금흐름의 현재가치 추정치` | `비금융위험에 대한 위험조정` | `보험계약마진(수정소급법)` | `보험계약마진(공정가치법)` | `보험계약마진(그 외 보험계약)` | `합계`.

### 2.2 필수 row keys (정규화 alias)

| alias | 공시 라벨 (예) |
|---|---|
| `opening_net` | `기초 순장부금액` |
| `opening_csm_gmm` / `_fvpa` / `_other` | 기초 행의 CSM 3열 |
| `nb_effect` | `신계약효과` |
| `assumption_adjusts_csm` | `보험계약마진을 조정하는 추정치 변동` |
| `assumption_not_adjusts_csm` | `보험계약마진을 조정하지 않는 추정치 변동` |
| `csm_amort_pl` | `당기손익으로 인식한 보험계약마진 금액` |
| `ra_release` | `위험해제에 따른 위험조정 변동` |
| `experience_adj` | `경험조정` |
| `past_service_cf` | `발생사고의 이행현금흐름 변동` |
| `insurance_service_result` | `보험서비스결과` |
| `insurance_finance_result` | `순보험금융손익` |
| `closing_net` | `기말 순장부금액` |
| `closing_csm_*` | 기말 CSM 3열 |

### 2.3 파서 접근

- **[Skimming First]** §9 legacy와 동일 — 헤더·row stub 먼저 보고, 회사별 YAML 매핑 후 추출.
- **교차검증:** `csm_amort_pl` ≈ §(5) `당기손익으로 인식한 보험계약마진`; 기말 CSM 합 ≈ §(7) 스케줄 `합계`.

---

## 3. Tier A — CSM 향후 상각 스케줄 (`csm_amort_schedule`)

- **타겟:** 회계연도별 보험계약마진 상각 표 (**장기** 행만 정규화).
- **주의사항 (Fuzzy Matching):** 회사마다 공시 명칭이 다름. 하드코딩 정규식 지양, semantic scoring.

### 3.1 관찰된 표 형태 (2026-05-23 PoC)

**Form A — 포트폴리오 × 연도버킷 (예: 삼성화재)**
- 캡션: `② 보험계약마진 상각`
- 헤더: `구분 | 포트폴리오 | 1년 | 2년 | ... | 10년 | 11년~15년 | ... | 30년 이후 | 계`
- 행: Non-Par × N + Indirect-Par × M + 합계

**Form B — 잔여기간 분포 (예: 메리츠화재)**
- 캡션: `(7) 당기말과 전기말 현재 남아있는 보험계약마진의 향후 상각금액은 다음과 같습니다. <당기>`
- 헤더: `구 분 | 1년 미만 | 1~2년 | ... | 30년 이상 | 합 계`
- 행: `발행한 보험계약` / `장기손해` / `보유한 재보험계약` / `장기손해` (4행)

### 3.2 추출기 점수 룰 (`csm_extractor.py`)

| 신호 | 점수 |
|---|---|
| caption에 `보험계약마진` + (`상각` / `예상` / `인식`) | +3 |
| caption에 `보험계약마진`만 | +2 |
| header에 연도 버킷 ≥3개 | +2 |
| header에 `년` 텍스트 (위 조건 미만) | +1 |
| header에 `계` / `합계` | +1 |
| caption에 다른 토픽 + CSM 미언급 | -3 |

기본 임계점수 `min_score=4`.

### 3.3 PoC 결과 (2024 사업보고서)

#### 5-company PoC (2026-05-24 갱신 — 5/5 자동 커버)

| 회사 | 결과 | form_type | 비고 |
|---|---|---|---|
| 메리츠화재 | ✅ 8 tables | unknown | 별도/연결, 본문/부속 중복 |
| 삼성화재 | ✅ 4 tables | A | `② 보험계약마진 상각` |
| DB손해 | ✅ 8 tables | A_rows | 시간버킷이 행에 있음 |
| 한화생명 | ✅ 16 tables | A + unknown | THEAD 없음 → 첫 행 추론 |
| 삼성생명 | ✅ 20 tables | A | `(12) … 기대상각기간별 당기손익인식 예상액` |

#### 37-company batch (K-ICS `원수사명` 전체)

| 상태 | 회사 수 | 비고 |
|---|---|---|
| ok | **23** | CSM 표 자동 추출 성공 |
| no_csm_table_found | 1 | 서울보증보험 (CSM 단어 자체 미존재 — IFRS17/PAA 검증 필요) |
| no_annual_filing | 12 | OpenDART에 사업보고서 미제출 (비상장 보험사) |
| no_corp_match | 1 | AIG손해보험 (DART 매핑 부재 — 외국지점일 가능성) |

**ok 23개사:** DB생명, DB손해, KB라이프, KB손해, NH농협손해, 교보생명, 농협생명, 동양생명, 롯데손해, 메리츠화재, 미래에셋생명, 삼성생명, 삼성화재, 신한라이프, 에이비엘생명, 케이디비생명, 코리안리, 푸본현대생명, 한화생명, 한화손해, 현대해상, 흥국생명, 흥국화재.

**no_annual_filing 12개사:** IBK연금(아이비케이연금), 교보라이프플래닛, 라이나, 메트라이프, 비엔피파리바카디프, 신한이지손해, 아이엠라이프, 악사, 처브라이프, 카카오페이손해, 하나생명, 하나손해. (pblntf_ty=A 정기공시 0건. 외감보고서(pblntf_ty=F) ingest 여부 사용자 결정 필요.)

### 3.4 알려진 한계

- 서울보증보험: 보험계약마진 단어 미존재 (사업 모형 차이 — 보증보험은 PAA 가능).
- AIG손해보험: DART corp_master에 손해보험 본사 매핑 없음.
- 12개 비상장 보험사: 정기공시 의무 미적용. 외감보고서 채널 추가 검토 필요.
- 분기/반기 미실험 (P3 — 사용자 진행 결정 대기).
- form_type=`unknown` 표(메리츠/한화손해 등 16+8): rollforward/snapshot 혼재. P4 보험계약부채 구조 캡처 후 자동 분류 가능.

### 3.5 추출기 강화 이력 (2026-05-24)

`csm_extractor.py` 갱신 — 5개 핵심 룰 추가/수정:

1. **`huge_tree=True`**: lxml HTMLParser가 큰 filing(>5MB)에서 default tree limit으로 표가 잘리는 회귀 방지.
2. **Sub-caption skip**: `1) 당기말`, `2) 2024년 12월 31일 현재`, `<당기>` 같은 짧은 enumerator 라인은 main caption을 덮어쓰지 않음 (현대해상 케이스).
3. **THEAD-less header inference**: THEAD가 없는 표에서도 첫 (또는 단위표시 skip 후) body row가 모두 텍스트면 헤더로 인정 (한화생명/흥국화재).
4. **Body-left-column year buckets**: 시간버킷이 행에 있는 표 (DB손해 `1년, 2년, …` × Non-Par/Indirect-Par) 도 +2 점수.
5. **Hard gate**: 캡션에 `보험계약마진`이 없으면 score를 3으로 cap. DB손해 IBNR development triangle 등 구조적으로 유사하지만 무관한 표 제외.
6. **form_type 분류**: `A` (시간버킷=열), `A_rows` (시간버킷=행), `B` (당기말/전기말 snapshot), `unknown`.

---

## 4. Tier A — 보험손익 상세 (`insurance_pl_detail`)

§14 **(5) 보험손익 상세** — **장기** 열.

### 4.1 필수 row keys

| alias | 공시 라벨 (예) |
|---|---|
| `insurance_revenue` | `보험수익` (하위: `예상보험금 및 보험서비스비용`, `위험해제에 따른 위험조정 변동`, **`당기손익으로 인식한 보험계약마진 금액`**, `보험취득현금흐름의 회수`) |
| `insurance_service_expense` | `보험서비스비용` (하위: `보험금 및 보험서비스비용`, `보험취득현금흐름`, `손실부담계약의 손실 및 환입`) |
| `insurance_service_result` | `총 보험서비스결과` |

### 4.1b 회사별 LOB 택소노미 — 슬롯 이름을 믿지 마라 (2026-08-30 신설)

PL 스키마의 LOB 슬롯 셋(`item2 생명장기` · `item13 자동차` · `item14 일반`)은 39개사 공통
서식을 전제하지만 **실제 공시는 회사마다 다르다.** 슬롯 이름을 보고 내용을 단정하면 틀린다 —
2026-08-30 하루에 두 회사에서 확인됐다.

| 회사 | 원문 LOB 구분 | item13(자동차) 판정 | 근거 |
|---|---|---|---|
| 코리안리재보험 (KR1000) | 장기보험 · 생명보험 · 일반보험 | **미해당(N/A)** — 자동차 컬럼 자체가 없다 | FY2026_Q2 보험수익 분석 공시 컬럼 헤더 |
| 서울보증보험 (KR0150) | 보증 · 해외 · 상해 · 자동차 · 기타 | **실재(값 있음)** — 단 전량 수재 | FY2026_Q1 주석 23: 원수 자동차 `-` / 수재 12,516,475천원 |

**두 회사가 같은 슬롯에서 정반대다.** 그래서 `validate_master_tables.py` 에 `lob_na` 축을
신설해 "미해당" 과 "추출 실패" 를 구별한다(`NA`=등재된 미해당, `BAD`=등재됐는데 값이 실재).
**미해당을 `0` 으로 채우지 마라** — 화면·집계가 그 회사를 자동차 영위사로 센다.

코리안리는 `item"2-1"`(장기재보험)이 별도 슬롯으로 들어가 있어 `생명(item2)/장기(2-1)/일반(14)`
3분해가 이미 성립한다. leg-coverage 등식이 이 회사에서 `2-1` 을 필요로 하는 이유가 그것이다.

**주의**: `item2` 의 항목명은 "생명장기 손익" 이지만 코리안리에서는 실제 내용이 **생명보험**이다.
항목명은 스키마 전역이라 한 회사 때문에 바꾸면 나머지가 어긋난다 — 이 표가 그 간극을 메운다.

### 4.2 Earnings dependency (다운스트림 KPI)

파싱 후 **손익계산서**와 결합:

```
csm_dependency     = csm_amort_pl / (insurance_service_result + |ifie_pl| + investment_income)
csm_runway_years   = closing_total_csm / csm_amort_pl          # §2 × §3
schedule_run_rate  = sum(schedule_buckets_y1_y3) / closing_total_csm
nb_replacement     = nb_effect_csm / csm_amort_pl              # §2; >1 이면 신계약이 상각 상쇄
```

단위·부호는 회사별 P&L 표기에 맞게 후처리 YAML.

---

## 5. Tier A — 출재 재보험 상세 (`reinsurance_rollforward`)

**출재(held reinsurance)는 Tier A.** 금융재보험·대량해지재보험 등은 **`수정소급/공정가치/그 외`** 및 narrative에 섞여 나올 수 있음 — 키워드 `금융재보험` 하드코딩보다 **측정요소·출재 블록 전체 캡처** 우선. 코리안리 기준 실측 결과는 **§5.4**.

### 5.1 캡션·위치

- §14 **(3)** `출재 … 재보험자산 변동내역` — **장기 출재만** (Q7: 일반·자동차 출재 블록은 slice 규칙과 동일하게 제외, 별도 table_id 없음).
- §14 **(4)** `출재 … 재보험자산 상세변동내역` — FCF / RA / CSM(재보험 순원가) 3열 구조는 원수와 **미러**.

### 5.2 필수 row keys

| alias | 공시 라벨 (예) |
|---|---|
| `opening_reins_asset` / `opening_reins_liab` | `기초 재보험계약자산` / `부채` |
| `premiums_allocated` | `재보험료의 배분` |
| `nb_reins_gmm` / `_fvpa` / `_other` | `신계약효과` (측정모형별) |
| `recoveries` | `재보험자로부터 회수한 금액` |
| `reinsurance_margin` | `재보험 순원가(마진)` |
| `reins_ifie` | `순재보험금융손익` |
| `reinsurer_default_risk` | `재보험자 불이행위험 변동효과` |
| `reins_ifie_other` | `재보험자 불이행위험 외 재보험금융손익` |
| `csm_amort_pl_reins` | `당기손익으로 인식한 보험계약마진 금액` (출재) |
| `closing_reins_asset` / `closing_reins_liab` | `기말 재보험계약자산` / `부채` |

### 5.3 Insight

- **Net reinsurance** = 재보험자산 − 재보험부채 → §(1) `순재보험계약자산`과 reconcile.
- 출재 CSM(순원가) 변동 + **불이행위험** → cedant earnings volatility.
- 원수 CSM roll-forward(§2)와 **페어**로 저장 (`side: direct` | `ceded`).

### 5.4 금융재보험(공동재보험·대량해지) 분리 가능성 — 실측 2026-08-31

owner 질문: 코리안리의 금융재보험 실적을 LOB(생명/장기/일반)에서 발라낼 수 있나.
**결론: 볼륨·예실차 지표는 분리 공시되지만 손익(PL)과 CSM은 분리되지 않는다. PL·CSM 분리는
불가로 종결한다.**

**먼저 코리안리 LOB 매핑을 확인하고 읽을 것.** 코리안리는 예외적으로 **생명 / 장기 / 일반**
3분할이다(다른 원수사는 생명장기 / 자동차 / 일반). 파서가 생명 → items 2~12, 장기 →
items 2-1~12-1, 일반 → item14 로 싣고(`scripts/pl_breakdown/companies.py`
`extract_tier2_coreanre`), 자동차는 **컬럼 자체가 없다**(미해당 ≠ 결측). 마스터의 항목명은
`생명장기 손익` 처럼 **전 회사 공통 슬롯 이름**이라 이 회사의 실제 LOB 이 아니며, 화면이
`PL_LOB_DISPLAY`(IFRS17.html)로 `생명`·`장기` 라벨을 덮는다. **슬롯 이름을 내용으로 읽으면
"생명과 장기가 분리 안 돼 있다" 는 틀린 결론이 나온다** — 2026-08-31 오케스트레이터가 실제로
그렇게 오독했다.

**분리되는 것 (FY2025 사업보고서, rcpNo 20260319001095):**

- XBRL 축 `전통형재보험 / 공동재보험`(`TraditionalReinsuranceCoReinsuranceOf…OfAxis`)이 존재하고,
  `CoReinsuranceMember` 가 붙은 **값 셀 996개**.
- 붙는 measure 는 **예실차 계열 6종뿐**: 예상보험금 / 위험보험료 / 보험금 예실차비율 ·
  예상유지비 / 예정유지비 / 유지비 예실차비율.
- 하위 축: 계약의 유형(**생명보험 · 장기손해보험**) × 포트폴리오(Non-Par 무배당사망/건강/기타/자산)
  × 만기구간. 예) 생명보험 Non-Par 무배당사망 1년 이내 예상보험금 = 7,793 백만원.
- **일반손해보험에는 `CoReinsuranceMember` 가 없다** → 공동재보험은 item14(일반)에 안 섞이고
  item2(생명) · item2-1(장기)에만 섞인다.

**분리되지 않는 것:**

- 보험손익 · CSM · 보험수익에는 이 축이 **붙지 않는다**. "공동재보험 손익만 얼마" 는 이 공시로
  나오지 않는다 — 위험보험료·예실차 수준의 볼륨 지표가 천장이다.
- **대량해지재보험은 아예 불가.** `대량해지` 키워드 0회. 영문 `Mass Lapse` 는 임원 내부교육
  이력표 한 줄(2023.11.06 금융재보험팀)뿐이라 실적 라인이 없다.

**주기 함정 — 연 1회, 사업보고서에만 있다.** 필링별 `CoReinsuranceMember` 값 셀 실측:

```
FY2023 사업보고서   0셀 (공동재보험 서술 18회)
FY2024 사업보고서   0셀 (서술 15회)
FY2025 사업보고서 996셀   <- 여기서 신설
2026.1Q 분기보고서  0셀
2026.2Q 반기보고서  0셀
```

분기·반기로는 못 따라가고 시계열은 현재 1개 시점뿐이다.

**부수적으로 건질 수 있는 것** (분리 축과 별개, narrative·표):
자산유보형 공동재보험 **유보금 잔액 2,243억**(2026.2Q 반기 매출채권 주석) · 담보 약정 표의
`약정의 유형 = 공동재보험` 금액 · 해약환급금준비금은 공동재보험 출재비율대로 별도 산출·적립
(보험업감독규정 제7-12조 제1항 제3호) · 유보형 금융재보험 계약 현금흐름이 현금흐름위험회피
대상항목.

**이 조사에서 실제로 걸린 탐지기 함정 2개 (재사용 시 필수):**

1. **DART 숫자 셀은 `<TD>` 가 아니라 `<TE>` 다.** `<TD ...>` 만 매칭한 1차 추출기가 **0건**을
   반환했고, 같은 파일에서 `<TE>` 로 바꾸자 1,344셀이 나왔다. 태그를 확인하기 전에는 0건을
   "공시 없음" 으로 읽지 말 것.
2. **키워드 0회 ≠ 원문 없음** (이 저장소가 흥국생명 스캔 PDF·듀레이션 census 에서 이미 두 번
   데인 함정과 동종). 라벨과 값이 다른 셀에 있고 축 이름은 영문 XBRL 토큰이라, 한글 키워드
   카운트만으로는 축의 존재 여부를 판정할 수 없다.

---

## 6. Tier B — BS 스냅샷·신계약·IFIE

### 6.1 `bs_snapshot` — §14 (1), **장기**

- `보험계약부채`, `순보험계약부채`, `보험계약자산`, `재보험계약자산`, `재보험계약부채`, `순재보험계약자산`.

### 6.2 `new_business_impact` — §14 (6), **장기**

- 최초 인식 시: `미래 현금 유출/유입`, `위험조정`, `보험계약마진` — **`비손실계약` / `손실계약`** split.
- NB economics·적자 신규 비중.

### 6.3 `liability_rollforward` — §14 (3), **장기**

- 컬럼: `잔여보장(비손실요소|손실요소)` | `발생사고` | `합계`.
- **`손실부담계약집합의 손실 및 환입`** — onerous / loss component.
- 파서 난이도 높음 → Skimming First (§9).

### 6.4 `ifie_bridge` — §14 (8)(9) + 손익계산서

- 투자손익 vs **순보험금융손익** 관계; OCI vs P&L IFIE 누적차.
- **투자 의존도** Insight에 필수.

---

## 7. Tier B — 계리적 가정 & 민감도 (`assumption_sensitivity`)

### 7.1 §14 (2) — 현행 추정 가정

| alias | 예시 |
|---|---|
| `mortality_morbidity` | `위험률` |
| `lapse` | `해약률` |
| `expense` | `사업비율` |
| `discount_rate` | `할인율` (범위) |
| `ra_confidence` | `비금융위험에 대한 위험조정 신뢰수준` |

### 7.2 리스크 주석 — 가정민감도

- 캡션: `가정민감도`, `보험위험의 민감도 분석` 등 (주석 번호는 회사마다 다름).
- 축: **손해율(위험률) / 해약률 / 사업비** 등 ± shock → **LIC(잔여보장) 변동**, **당기손익 영향**.
- 각주 (메리츠 등): *「당기손익 영향」= 가정변동으로 CSM 장부금액을 초과하는 최선추정부채 증가분* — **CSM runway와 연결**해 해석.

### 7.3 파서 접근 (2026-05-24 Q8 확정)

> ⚠️ **SUPERSEDED (2026-06-16).** 아래 "민감도 primary = K-ICS 분기공시 / DART 주석 = skim PoC·primary 아님
> (`sensitivity_extractor.py` misaligned)"은 **현행 코드와 정면 충돌** — DART CSM/PL 민감도는 지금 **owner-directed
> 실파이프라인**(`src/ifrs17/sensitivity_extractor.py` → `scripts/viz_build_ifrs17_panels.py` →
> `data/dart/viz/sensitivity_heatmap.json` → `IFRS17.html` 렌더)이다. **운영 정본 = 코드 + `.claude/skills/ifrs17-parser/`
> SKILL(traps).** 본 §7.3·§9 Q8·§10 Q8의 "K-ICS-primary / DART=skim PoC" 표기는 폐기.

- **Primary source: K-ICS 분기 공시** (`kics_disclosure` / md_inbox). DART 주석(§14 (2) + 리스크 민감도)은 **secondary / 추후**.
- `sensitivity_extractor.py` DART batch는 skim PoC일 뿐 — B5 정규화 파이프라인의 primary가 **아님** (방향 오류; K-ICS ingest 우선).
- 표 형태: `가정 | 민감도 | LIC 영향 | 당기손익 영향` (회사별 변형). source 필드로 `kics_disclosure` vs `dart_note14` 구분 저장.

---

## 8. 보험계약부채 multi-index (Skimming First — B3 `liability_rollforward`와 통합, Q9)

- **타겟:** §14 (3) 상세 변동 — multi-index header. **B3 `liability_rollforward`와 동일 테이블** — 별도 트릭·table_id 유지하지 않음 (`liability_extractor.py` = §8 P4 구조 캡처).
- **룰:** 즉시 JSON 생성 금지 → 구조 스kim → 사용자/YAML 승인 → 추출.
- **추천 스키마:** Structural-first (헤더 + values) → long format 후처리 (K-ICS docling→md→정규화와 동형).

### 8.1 삼성화재 2024 관찰 (참고)

- 3-row header: VFA 미적용 그룹 × (잔여보장 손실요소제외/손실요소 | 발생사고 FCF/RA).
- 보종별 반복: 장기 / 일반 / 자동차 — **장기 블록만** 매핑.

### 8.2 P4 PoC (2026-05-24): `src/ifrs17/liability_extractor.py`

후보 C 스키마(원본 무손실)로 구조 캡처. 회사별 YAML 매핑 미작성 (정규화는
별도 단계).

| 회사 | tables | kind 분포 | 비고 |
|---|---|---|---|
| 메리츠화재 | 48 | rollforward 48 | 본문 24 + 부속 24 (별도×연결 / 원수×출재 중복) |
| 삼성화재 | **0** | - | 캡션-표 거리(2500+ 줄) 멀어 last_caption lost. caption stack 도입 시 회복 가능 |
| DB손해 | 14 | rollforward 14 | |
| 한화생명 | 32 | rollforward 32 | |
| 삼성생명 | 8 | rollforward 8 | |

산출물: `data/dart/extracted/<dir>_liability.json`,
`data/dart/extracted/_liability_poc_summary.json`.

스코어링 룰 (csm_extractor와 spirit 동일, 회사별 정규식 X):

- 캡션: BS 키워드(보험계약부채/재보험계약자산 등) ≥2 → +2; rollforward
  키워드(잔여보장/발생사고/측정요소/변동내역) ≥1 → +1
- 헤더: BS 키워드 ≥2 → +3, 1 → +1; rollforward 키워드 ≥2 → +3, 1 → +1
- `kind`: rollforward → snapshot_or_partial → bs_snapshot → unknown 우선순위

기본 임계점수 `min_score=4`.

---

## 9. 생명보험사 특수사항 & 확정 설계 결정 (Q1–Q9)

- **CSM 상각 표:** 한화생명·삼성생명 PoC ❌ — 캡션·XML 분할·표 임베딩 방식 상이. **A1 롤포워드(§2)가 생보의 primary anchor**일 수 있음 (스케줄 없이도 CSM amort·기말 추출 가능).
- **Slice:** `장기` 없으면 **전사 합계** (2026-05-24 Q5 — `생명`/`보험` 키워드 fallback 사용 안 함). 메타 `slice_label=whole_company_life`.
- **VFA:** 변액·VA 비중 큰 생보만 §(5)에서 VFA sub-block 추가 검토.
- **Q6 CSM 3열:** `total_csm` 대표값 + 3열(수정소급/공정가치/그 외) 조건부 보존 (§0.3).
- **Q7 출재:** 장기 출재만 — 일반·자동차 출재 블록 별도 table_id 없음.
- **Q8 민감도:** K-ICS 분기 공시 primary; DART 주석 secondary/future.
- **Q9 B3 vs §8:** 통합 — `liability_rollforward` = §8 multi-index P4 구조 캡처.

---

## 10. 사용자에게 결정 요청할 항목 (Open Questions)

### 답변 받은 항목 (2026-05-23 ~ 2026-05-24)

- ✅ **CSM 추출 커버리지**: 패턴 추가 자동화 (수동 YAML 룰 없이) → 5/5 + 37사 23/37 자동.
- ✅ **CSM 스키마**: Form A + Form A_rows + Form B + unknown 4종을 `form_type` 필드로 캡처.
- ✅ **보험계약부채**: 후보 C (구조 원본 + 회사별 YAML 후처리).
- ✅ **회사 범위**: K-ICS 37개사 전체 (kics_disclosure.json `원수사명`).
- ✅ **보고서 종류**: 사업 + 반기 + 분기 모두 → P2 사업보고서 23/37 완료. P3 반기/분기 확장은 MVP 이후.
- ✅ **archive 정리**: 메인 세션 처리 완료.
- ✅ **CSM PoC 확장 (A2 vs A1)**: A2 (스케줄) 자동 23/37 달성으로 우선순위 정리됨.
- ✅ **Q1 비상장 12사 (2026-05-24):** Skip — **상장 25개만** 운영. 외감(pblntf_ty=F) ingest 안 함. `universe.NON_LISTED_SKIP`.
- ✅ **Q2 AIG손해보험:** Skip — 분석 대상 제외 (`universe.EXCLUDED_SKIP`).
- ✅ **Q3 서울보증보험:** 분석 대상 제외 — PAA-only / `보험계약마진` 없음.
- ✅ **Q4 P3 반기/분기:** **MVP (A1/A3/A4/B1/B5) 완성 후** 진행. 23사 × 2 ≈ 46회 추가 호출 예상.
- ✅ **Q5 장기 slice (생보):** **무조건 전사 합계** — 손보 `장기`와 peer proxy 비교. `universe.expected_slice_policy()`.
- ✅ **Q6 CSM 3열 (2026-05-24):** **`total_csm` 대표값** + 공시가 3열(수정소급법/공정가치법/그 외)로 분리되어 있으면 **조건부 컬럼 보존**. §0.3 규칙.
- ✅ **Q7 출재 범위 (2026-05-24):** **장기 출재만** capture — life/long-term slice 규칙과 일관. 일반·자동차 출재 블록을 **별도 table_id로 저장하지 않음**.
- ✅ **Q8 민감도 source (2026-05-24):** **K-ICS 분기 공시 우선 (primary)**. DART 주석은 **secondary / 추후**. B5는 OpenDART primary가 **아님** — `sensitivity_extractor.py` DART batch는 misaligned skim PoC.
- ✅ **Q9 B3 vs §8 (2026-05-24):** **통합** — B3 `liability_rollforward` = §8 multi-index P4 구조 캡처. 별도 트릭·table_id 유지하지 않음.

### 미답

_(Q1–Q9 모두 확정. 정규화 단계 잔여: crawl manifest 작성 → 23社 full normalization.)_

---

## 11. Changelog

변경 이력은 `docs/claude-changelog.md` (전사 통합 로그) 참조.
