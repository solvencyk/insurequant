---
from: orchestrator
to: parser
created: 20260828T0113Z
status: resolved
route: backlog
company: MULTI
period: MULTI
lane: ifrs17
iter: 1
---

## 미결 (orchestrator 작성)

owner 발주. `PL_breakdown.json` 을 당기순이익에서 끊지 말고 **총포괄손익까지** 연장한다.
화면(IFRS17.html Panel 5)은 designer 가 별도 티켓으로 받는다. 이 티켓은 **마스터 데이터만**.

### 배경 — 왜 하는가

업권 피드백 하나가 "이자율 헤지 손익이 OCI 에 갇혀 당기손익에서 상쇄되지 않는다" 고 주장했다.
지금 화면은 PL 까지만 있어서 이 주장을 확증도 반증도 못 한다. 실제로 캐시를 찔러 보니
현금흐름위험회피 OCI 는 2024 년 +0.9조에서 2025 년 △2.9조로 부호가 뒤집힌 게 사실이지만,
같은 피드백이 말한 "2025 년 OCI 마이너스 전환" 은 우리 별도 표본과 어긋난다(2024 년이 더 나빴다).
이 판정을 화면이 하게 만드는 게 목적이다.

### 데이터 소스 — 새 다운로드 불필요

`data/dart/_fs_api_cache/*_OFS.json` 의 `sj_div == "CIS"` 행에 이미 다 있다.
BS 빌더(`scripts/build_ifrs17_bs.py`)가 같은 캐시의 `sj_div == "BS"` 만 쓰고 있으므로
그 옆에 붙이는 형태가 된다. **별도(OFS) 기준 고정** — BS 와 동일 basis 여야 AOCI 대사가 성립한다.

### 추가할 항목 (7개)

| 번호 | 항목명 |
|---|---|
| 25 | 기타포괄손익 |
| 26 | FVOCI 채무증권 평가손익 |
| 27 | 보험계약금융손익(OCI) |
| 28 | 위험회피 파생상품 평가손익 |
| 29 | FVOCI 지분증권 평가손익 |
| 30 | 재보험금융손익(OCI) |
| 31 | 총포괄손익 |

`값`(누계) + `값_당분기` 둘 다 채운다. **유량이다** — DART API 는 `thstrm_amount` 가
3개월 단독, `thstrm_add_amount` 가 누계다(삼성생명 2026 반기 실측: 지분증권 61.4조 vs 78.7조).
기존 PL 항목 1~24 와 같은 규칙으로 매핑할 것.

### 작업 1 — 라벨 변형 census 를 먼저 돌린다 (필수 선행)

**정확일치로 하면 대량으로 조용히 빠진다. 실측으로 확인된 함정이다.**
orchestrator 가 census 를 돌렸을 때 `기타포괄손익` 정확일치만 썼더니 삼성생명의
2024~2026 년이 통째로 누락됐다. 삼성생명은 2023 년엔 `기타포괄손익`, 2024 년부터는
`법인세비용차감후기타포괄손익` 을 쓴다. 위험회피도 회사마다 다르다 —
`현금흐름위험회피파생상품평가손익`(대다수) vs `위험회피목적파생상품평가손익`(삼성생명).

- `account_id`(예: `ifrs-full_OtherComprehensiveIncome`, `ifrs-full_ComprehensiveIncome`)를
  1차 키로 쓰고 `account_nm` 은 보조로 쓰는 쪽이 안정적일 가능성이 높다. 둘 다 재보고 결정할 것.
- 산출: 회사 × 분기 × 항목 기대 그리드 대비 결손 셀 수. `artifacts/` 에 census 를 남긴다.
- **결손이 있으면 그 목록을 답변에 적는다.** SKIP-on-missing 금지(coverage census 원칙).

### 작업 2 — 커버리지 갭 처리

FS API 캐시는 분기당 23~24 사인데 `PL_breakdown` 항목 24 는 연간 분기에 최대 36 사다.
캐시에 없는 회사는 본문 XML(`data/dart/FY*/raw/`)의 포괄손익계산서 표에서 뽑아야
PL 과 같은 커버리지가 된다. 캐시로 몇 사가 커버되고 본문 XML 이 몇 사 필요한지 census 로 확정한 뒤,
본문 XML 경로가 크면 그 사실을 답변에 적고 1차는 캐시분만 반영해도 된다(단, 결손 목록 명시).

### 작업 3 — 게이트 룰 2개 신설

1. `PL_OCI_TOTAL_IDENTITY` — 항목 24 + 25 = 31 (허용오차는 기존 PL 항등식 관행 따를 것)
2. `PL_OCI_VS_BS_AOCI` — `IFRS17_BS.json` 항목 4(기타포괄손익 누계액)의 전분기 대비 증감 ≈ 항목 25.
   재분류·자본거래·법인세 때문에 정확히 안 맞는다. **먼저 전 버킷 시뮬레이션을 돌려
   실제 잔차 분포를 보고 허용오차를 정한다**(룰 수정 전 시뮬레이션 필수 — 1건 고치려다
   129건 깨뜨릴 뻔한 전례). 잔차가 구조적으로 크면 RED 대신 WARN 으로 배선하고 그 근거를 답변에 적는다.

배선 후 `scripts/prepush_check.py` 에서 실제로 호출되는지 그 자리에서 확인할 것.
문서에 mandatory 라고 쓰는 건 강제가 아니다.

### 하지 말 것 (충돌 방지)

- **`index.html` 을 건드리지 않는다.** 다른 세션이 그 파일에서 작업 중이다.
- **`IFRS17.html` 도 건드리지 않는다.** 화면은 designer 티켓 소관이다.
- **브랜치를 바꾸지 않는다.** 현재 `fix/csm-product-segmented-columns`. 공유 워킹트리다.
- `build_root_masters.py` 의 `main()` 통짜 실행 금지. `build_csm`/`build_pl` 개별 호출.
  `validate_master_tables.py` 는 반드시 `--no-build`.
- 마스터 xlsx 는 `scripts/sync_master_xlsx_sheet.py` 로 바뀐 시트만 cherry-pick.
  `build_master_xlsx.py` 전체 재생성 금지, openpyxl 재저장 금지(수식 캐시 wipe).
- 골든: `tests/test_pl_breakdown_golden.py` 가 PL 산출 바이트를 고정한다. 산출이 의도적으로
  바뀌므로 `--update` 로 재생성하고 커밋 메시지에 이유를 남긴다.

python 은 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe` 풀패스로 호출한다.

## 답변 (recipient 작성 — 처리 후)

**요약**: 항목25-31 신설, 2,492셀(356 company-quarter × 7항목) 추가. account_id 기반
매핑(라벨 정확일치 함정 회피). combo-diff로 항목1-24 무손상 확인. 게이트 룰 2개 신설·배선
확인·전 버킷 시뮬레이션 완료. 골든 2종 재생성. 작업2(본문XML fallback)는 명시적으로
미착수 — 사유는 아래 (2).

### (0) 작업1 — 라벨 census 및 매핑 확정

전수 census(`scripts/_probes/census_oci_labels_pass{1,2}.py`, 36사 × 실제 존재하는
356 company-quarter 전부, `data/dart/_fs_api_cache/*_OFS.json`의 `sj_div=='CIS'`).
**account_id를 1차 키로 확정**(account_nm 보조) — 실측으로 정확히 티켓이 경고한 함정을
재현·해결:
- 삼성생명: account_nm이 2023년 `기타포괄손익` → 2024년부터 `법인세비용차감후기타포괄손익`
  으로 바뀌지만 account_id는 `ifrs-full_OtherComprehensiveIncome`로 불변. account_nm
  정확일치였다면 삼성생명 2024~2026년 항목25가 통째로 빠졌을 것 — account_id 매칭으로
  해결 확인(`scripts/_probes/smoke_tier1_oci.py` 재현: 2023.4Q/2024.4Q 둘 다 정상 추출,
  24+25=31 항등식 둘 다 0.000).
- 위험회피(항목28): `현금흐름위험회피파생상품평가손익`(24사 다수) vs
  `위험회피목적파생상품평가손익`(교보생명 등) — account_id로 흡수.
- FVOCI 채무/지분증권(항목26/29)은 **표준 태그 자체가 분리**돼 있음을 확인:
  `...FinancialAssetsMeasuredAtFairValueThroughOtherComprehensiveIncome`(디폴트=채무
  전용, 지분이 따로 태그될 때) vs `...GainsLossesFromInvestmentsInEquityInstruments`
  (지분 전용) — 둘을 혼동하면 지분/채무가 뒤섞였을 것.

매핑 확정 후 `scripts/fetch_dart_fs.py`에 `ACCT_OCI`(7개 account_id) +
`ACCT_OCI_28_FALLBACK`(교보생명 KR0073 FY2025.1Q+가 표준 태그 대신
`dart_GainFromDerivativesHeldForHedging`류를 **부호 있는 net 값으로 재사용** — raw
실측 2025.2Q -139,938.33백만, "Gain" 태그인데 손실) + `OCI_NM_FALLBACK`(무표준계정코드
row, 케이디비/푸본현대/코리안리 항목26, 흥국화재/KB라이프 항목28)로 배선.
`build_pl_breakdown.py`는 `ITEM_NAMES` 25-31 추가 + `main()`에 배출 루프 신설.
`값_당분기`는 새 코드 불요 — `build_root_masters.py::build_pl()`이 이미 전 PL 항목에
대해 YTD-차분으로 일반화돼 있음(항목번호 하드코딩 없음). 실측 검증(삼성화재 KR0008
2024.2Q/3Q): DART 원본 `thstrm_amount`(3개월 단독)와 YTD차분 값_당분기가 소수 6자리까지
정확히 일치.

### (1) 추가된 셀 수

`data/dart/viz/pl_breakdown_master.json` 8,698→11,190행(+2,492), 루트
`PL_breakdown.json` 동일(+2,492) — **정확히 356 company-quarter × 7항목**.
combo-diff(`scripts/_probes/combo_diff_pl_master.py`, cell-key=(코드,항목번호,분기)
전수 대조, 두 마스터 각각) 결과: **추가 2,492 · 삭제 0 · 항목1-24 변경 0(byte-identical)**
— 손실 없음. `insurequant_master_tables.xlsx` "손익분해PL" 시트도
`sync_master_xlsx_sheet.py`로 동기화(dry-run "변경 셀 0 · 추가 행 2492 · 삭제 행 0" 확인
후 실행, 사후검증 "11190행×9열 마스터와 완전 일치, 나머지 시트 값 동일").

### (2) 결손 셀 목록과 원인

프로덕션 `PL_breakdown.json` 기준: 값 채워짐 1,876/2,492(75.3%), 결측 616(24.7%).
항목별: 25=282/356·26=272/356·27=273/356·28=273/356·29=224/356·30=270/356·31=282/356
(populated/전체). 결손은 세 가지 서로 다른 원인으로 나뉜다(SKIP 아님 — 전부 명시적 null
row로 존재, 마스터에서 grep 가능):

1. **12개사 = 전 분기 결측**(FS-API 캐시는 있지만 그 안에 CIS 섹션 자체가 없음 — 표준
   XBRL 미제출, 감사보고서-only): 예별손해(3q)·AIG손해(3q, corp_code 매핑 자체 실패 —
   기존에 이미 알려진 결함)·악사손해(3q)·신한이지손해(3q)·라이나생명(3q)·
   BNP카디프생명(2q)·AIA생명(1q)·메트라이프생명(3q)·하나생명(3q)·처브라이프생명(3q)·
   교보라이프플래닛(2q)·IBK연금보험(3q). 기존 `_GOLD_CELL_OVERRIDE`/도메인 문서의
   "12개사 감사보고서-only" 목록과 정확히 겹친다 — 새로 발견한 결함이 아니라 알려진
   한계가 이 확장에도 그대로 반영된 것.
2. **23개사 = 2023.1Q/2Q(IFRS17 첫 시행 분기)만 결측**, 나머지 12-13개 분기는 전항목
   정상. DART XBRL CIS 태깅이 그 시점엔 갖춰지지 않았던 것으로 보이는 전사적 패턴(회사
   특성이 아니라 시점 특성) — 메리츠화재·한화손해·현대해상·KB손해·DB손해·한화생명·
   삼성생명 등 대형사도 예외 없이 이 2개 분기만 빠진다.
3. **5개사(흥국화재·삼성화재·에이비엘생명·미래에셋생명·푸본현대생명) = 항목25/31(총계)은
   전분기 있는데 26-30(세부 라인) 태그가 원천에 없음.** 삼성화재는 raw 확인 결과
   2025.4Q부터 세부 태그가 생기고(`scripts/_probes/smoke_tier1_oci.py` 2026.2Q 케이스로
   확인) 그 전(2023.3Q~2025.3Q, 9개 분기)은 총계만 XBRL화됐던 것으로 보인다.
4. **KR0150(서울보증)은 결손 0.**

**작업2(본문XML fallback)는 미착수.** 티켓이 우려한 "캐시가 23-24사만 커버"라는 전제는
실측과 달랐다 — FS-API 캐시 자체는 필요한 356셀 **전부**에 이미 있었다
(`ofs_cache_missing=0`, 새 다운로드 불필요라는 티켓 전제는 확인됨). 실제 결손은 캐시
안의 CIS 섹션 유무 문제이고, 위 12개사는 캐시가 아니라 **감사보고서 XML을 처음부터
새로 파싱**해야 하는 대상이다 — 이는 "몇 셀 채우기"가 아니라 items 1-24의 HTML-fallback
경로(`pl_breakdown/tier1.py`)급 새 추출기가 필요한 규모라 이번 라운드에 넣지 않았다.
1차는 캐시분만 반영(위 결손 목록 명시).

### (3) 게이트 룰 2개 — 배선 위치 및 시뮬레이션 잔차 분포

**룰1 `PL_OCI_TOTAL_IDENTITY`**(항목24+25=31): `scripts/validate_master_tables.py::PL_EQS`
8번째 등식(`"총포괄손익 = 당기순이익+기타포괄손익"`)으로 배선 — 기존
`_check_pl_bridge()`를 그대로 탄다(새 함수 불요). **룰 작성 전** 전 버킷 시뮬레이션
(census pass2, 282개 CIS-보유 셀): 잔차 min=median=p90=max=**0.000** — 반올림조차 없는
정확한 항등식이라 기존 DEFAULT_FLOOR(200백만) 그대로 사용. 실배선 확인:
`pl_bridge:2523P/12F/313S/0NEW`(변경 전) → `2805P/12F/387S/0NEW`(변경 후) — P +282·
S +74(항목25/31 결측 셀)·**F 불변(0건 신규 실패, 내 신설 등식은 0건 기여)**.

**룰2 `PL_OCI_VS_BS_AOCI`**(항목25 값_당분기 ≈ IFRS17_BS 항목4 QoQ 증감): **룰 작성 전**
`scripts/_probes/simulate_pl_oci_vs_bs_aoci.py`로 259개 비교가능 셀(PL 당분기와 BS
전후분기 값이 다 있는 (회사,분기)) 전수 시뮬레이션 결과:
```
잔차 분포(백만원):  min=0.00  p25=0.00  median=0.00  p75=190.28  p90=13770.25  p95=59067.05  max=5391139.00
상대 잔차(|resid|/max(|ΔBS|,500)):  median=0.0%  p90=3.6%  p95=25.0%  max=1294.4%
관대한 문턱(rel100%+abs10,000백만)에서도 259건 중 2건 미달(99.2%가 상한).
```
중앙값·p25가 정확히 0.000이라 **개념 자체는 유효**하지만(다수 셀이 완전히 닫힘), 최악
30건 중 17건(56.7%, 기저율 25% 대비 과다)이 **4Q(연차) 분기에 쏠려 있다** — 이 저장소에
이미 문서화된 별개 패턴(`build_root_masters.py` 주석: "신계약CSM 당분기가 음수(4Q 연차
재서술 artifact)")과 같은 계열. 재분류조정(FVOCI 매도 시 누계OCI→P&L)·자본거래·법인세
조정이 CIS 당기순액과 BS 잔액 증감을 회계상 구조적으로 갈라놓을 수 있다 → **owner 지시대로
RED 아닌 YELLOW로 배선**(exit code 미반영). 허용오차 = max(20%·|ΔBS|, 2,000백만) — 실배선
재현치는 332건 중 13건 flag(319건 tol 이내, 24건 BS 결측 skip; 시뮬 스크립트의 259/14는
독립 재구현이라 근사치로만 참고, 실배선 수치가 정본). worst offender: 삼성생명 2025.4Q
(ΔBS 23,622,471백만 vs PL당분기 18,231,332백만, resid +5,391,139백만, 22.8%).

**배선 확인(honor-system 아님 실측)**: `scripts/prepush_check.py` L146 `fast` 리스트에
`tests/test_master_tables_golden.py`가 있고, 그 골든은 두 룰이 낀 SUMMARY 문자열 전체를
pin한다 — 매 push마다 실행되며 룰이 죽거나 잔차가 이동하면 골든이 막는다. 두 룰 다
`tests/test_identity_registry.py::REGISTRY`에도 등재(룰1=기존 `pl_bridge` 항목의
statement/measured 갱신, 룰2=신규 `pl_oci_vs_bs_aoci` 항목, `kind=HEURISTIC`+`reason`+
`tol_from`) — **등재를 빠뜨렸으면 실제로 잡혔다**: 최초 시도에서
`test_no_undeclared_threshold_constants`가 신설 상수 `OCI_AOCI_TOL_REL`/
`OCI_AOCI_TOL_ABS_MN`을 미등재로 FAIL시켰고, REGISTRY에 등재한 뒤 재실행해 PASS로
전환 확인(무검사 통과가 아님을 실측).

### (4) 골든 재생성 여부

둘 다 재생성함(둘 다 의도된 변경, 사유 커밋에 기재 예정):
- `tests/fixtures/pl_breakdown_golden.json`: master_rows 8698→11190, non_null_values
  7842→9718, sha256 이동. `RUN_PL_GOLDEN=1 pytest tests/test_pl_breakdown_golden.py`
  재확인 PASS(239초).
- `tests/fixtures/master_tables_golden.json`: SUMMARY 이동(`pl_bridge` P+282/S+74/F±0,
  `oci_vs_bs_aoci:13Y` 필드 신설), exit_code 2 불변(기존 12건 pl_bridge baseline·6건
  csm_amort pin과 무관, 이번 변경으로 새로 생긴 exit=2 원인 아님).
  `pytest tests/test_master_tables_golden.py` 재확인 PASS.

### 검증 결과

- `pytest tests/test_identity_registry.py` 14 passed (등록 검증·변이시험 포함).
- `prepush_check.py`의 fast 오프라인 번들 9개 파일 + `tests/unit/` 전체 재실행:
  **229 passed, 1 skipped** — 회귀 0.
- `scripts/validate_data_contract.py` → `SUMMARY RED=0 YELLOW=92`
  (2026-08-26 49th pass 시점과 동일 YELLOW 카운트 — 이번 변경으로 신규 RED/YELLOW 0건).
- `scripts/prepush_check.py`(전체, `FULL_COVERAGE_SWEEP=1` 포함, 456.67초) 실행 완료:
  ```
  PRE-PUSH VERDICT: gate RED=0 · K-ICS rule gate=clear · domain gates=pass ·
  DART raw 유실=0 · inbox 기계적위반=0 · offline tests=pass → gate-clear
  ```
  exit=0. offline tests 229 passed/1 skipped(위 항목과 동일 번들, 전수 커버리지 스윕
  포함 재확인). inbox hygiene: 활성 7 · 종결보관 311 · 위반 0.

### 재현 명령

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_pl_breakdown.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/run_build_pl_only.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_master_tables.py --no-build
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/sync_master_xlsx_sheet.py "손익분해PL"
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/prepush_check.py
RUN_PL_GOLDEN=1 C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_pl_breakdown_golden.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_master_tables_golden.py tests/test_identity_registry.py
```
census 원본: `scripts/_probes/census_oci_labels_pass{1,2}.py`(산출은 gitignore된
`artifacts/parser/`라 로컬에만 있음 — 위 명령으로 재생성). 시뮬레이션 원본:
`scripts/_probes/simulate_pl_oci_vs_bs_aoci.py`.

**손대지 않음**: `index.html`·`IFRS17.html`(designer 소관)·`CSM_waterfall.json`·
`NB_CSM_multiple.json`·`IFRS17_BS.json`(읽기 전용)·`data/_gold/user_{pl,csm}_cells.json`
(항목25-31 기존 등재 0건 확인, 간섭 없음)·`build_root_masters.py::main()`(개별
`build_pl()`만 호출)·브랜치(`fix/csm-product-segmented-columns` 유지, `git push` 없음).
