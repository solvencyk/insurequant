# Parser Changelog — IFRS17 lane (Stage 2)

> Last updated: 2026-08-03 · Stage 2/5 — parser (ifrs17 lane)
> Prompt: docs/agents/claude-agent-parser.md (shared) + docs/domains/claude-agent-ifrs17.md · TODO: TODO_parser_ifrs17.md

IFRS17 extraction history: DART body XML → CSM_waterfall / PL_breakdown / NB-CSM-multiple masters.
Code: `src/ifrs17/` (csm / measurement / insurance_pl / reinsurance / bs_snapshot / sensitivity extractors +
`scoring.py` config layer). Validators: CSM golds, PL golds, csm_waterfall / pl_bridge crosscheck.

**Pre-split combined history (before 2026-06-13): [`changelog_parser.md`](changelog_parser.md)** (frozen).
Convention: see [`docs/agents/doc-style.md`](agents/doc-style.md).

## 2026-08-03 (4차) — bonds 폐지 체인 parser측 완결(KR0049/KR0150/KR1010) + golden re-drift 종결 + PL 근접사고 자체복구

**발주**: downloader `inbox/parser/20260803T0546Z`(잔여 3사 raw-ready) + validation
`inbox/parser/20260803T0400Z`(중복 발주, 이미 처리됨) + `inbox/parser/20260803T0540Z`(golden re-drift).

### CAPSEC_COVERAGE_REGRESSION 잔여 3사 — 완료, RED 13→0

- **KR0150(서울보증보험) — 무발행 확정, 최고신뢰도.** 사업보고서 본문(재무제표 첨부 아님)
  "7. 증권의 발행을 통한 자금조달에 관한 사항"의 **표준 DART 구조화표** [신종자본증권 미상환잔액]·
  [조건부자본증권 미상환잔액] 둘 다 공모/사모/전 잔여만기구간 전부 "-"(0). 자유서술 스캔이 아니라
  회사가 직접 기입하는 정형 공시표라 이번 체인 전체에서 가장 신뢰도 높은 무발행 확인 사례.
- **KR1010(교보라이프플래닛생명보험) — 무발행 확정.** 신종자본증권/후순위 전 용어 매칭 0건.
- **KR0049(악사손해보험) — 🔴 실발행 발견, 편입(confidence=medium).** "17.금융부채" 주석: JPY
  5,000,000,000엔 사모 후순위채 1건(투자자 AXA Life Insurance Co.,Ltd/AXA Life Japan, 그룹
  계열사향), 표면금리 1~5년차 1.57%고정/6년차~만기 z-Tibor+1.37%변동, 최종만기 10년, 콜옵션
  발행일로부터 5년 경과 후 매 이자지급일. 당기말 KRW환산 장부가액 45,881.5백만원 편입. ⚠️ 절대
  발행연도가 disclosure에 없어 `call_date`를 as_of(2025-12-31)로 보수적 추정(콜 가능 시점 이미
  도래 가정) — 발행 사실·금액은 정확, 정확한 콜 타이밍만 추정치.

`forward_capital_simulation.py` → `wire_capital_securities_to_utilization.py` →
`emit_capsec_provenance.py` → `validate_data_contract.py` 재실행: **`CAPSEC_COVERAGE_REGRESSION`
RED 3→0**(원래 13건 전부 소멸). `bond_coverage_distribution: dart_listed=27 / no_bonds_in_dart=11 /
absent_in_source=0`. 전체 게이트 RED=0·YELLOW=219. `data/bonds/capital_securities_fy2025.json`
최종 39사.

→ **`inbox/parser/20260803T0055Z`(forward_capital FSC→DART rebase) 완료조건 ①(발행잔액>0 ≥24사)
최종 충족**(dart_listed=27) — owner 확인 후 최종 resolved 가능, downloader의 bonds 소스 폐지
(`20260803T0057Z`) 착수 게이트 오픈. `inbox/parser/20260803T0400Z`(validation 중복 발주)도 같이 종결.

### golden re-drift(`qoq_warn:198Y→197Y`) — 근본원인 특정 + 재생성

`inbox/parser/20260803T0540Z`(validation)이 골든 재생성(11:20:41) 후 마스터가 다시 바뀌어
(11:46~11:56, 이 세션의 KR0075/KR1098/KR0051 fix) 재drift됐다고 보고. 코드 추적으로 정확히 특정:
`validate_master_tables.py::qoq_scan`의 신계약CSM YoY 체크가 참조분기(KR0075 2024.4Q) 값이
`floor(50억)` 미만이면 평가를 skip한다. 재정정 전 2024.4Q 신계약CSM=98.312억(>50, 평가됨) →
2025.4Q(128.465억) 대비 YoY +30.66% > threshold 30%(`new_business_csm`) → YELLOW 발화 중이었음.
재정정 후 98.312→9.831억(**<50, 평가 자체 skip**) → 경고 소멸. **비율은 안 변했다**(양쪽 분기 모두
정확히 ÷10이라 30.66%로 동일) — floor 미달로 룰 평가대상에서 빠진 것뿐. (경쟁 후보였던 이자부리는
YoY −3.46%로 threshold 20% 미달, 재정정 전후 무관.) `python tests/test_master_tables_golden.py
--update` 재실행(마스터 편집 완료 후) → PASS.

### 🔴 자체 근접사고 — `PL_breakdown.json` 7799→2940행 붕괴, 즉시 복구

위 근본원인 추적 중 `python scripts/validate_master_tables.py --help`를 실행 — `--help`가
스크립트에 등록된 플래그가 아니라 **에러 없이 기본 경로(빌드 포함)로 그냥 실행**돼버려
`build_root_masters.py::build_pl()`이 (stale한 diag 소스로) `PL_breakdown.json`을 7799→2940행/
319→117조합으로 붕괴시킴 — [[project_git_purge]]에 이미 기록된 정확히 같은 near-miss 패턴을
직접 재현한 것. combo-count 안전점검으로 즉시 발견 → `git checkout HEAD -- PL_breakdown.json`으로
복구 → 이 세션에서 유실된 유일한 변경분(KR0051 item18/19 override)을 수기로 재적용 → HEAD 대비
combo/row 수 무손실 재확인(319 combos, 7799 rows). **CSM_waterfall.json은 무관**(build_csm()의
diag 소스는 완전해서 영향 없음, 327 combos 항상 불변 확인됨).
**교훈**: `validate_master_tables.py`는 인식 못하는 인자를 조용히 무시하고 기본(빌드) 경로로
빠진다(argparse 미사용 추정) — `--no-build` 없이 직접 호출 금지, 항상
`pytest tests/test_master_tables_golden.py`(내부에서 `--no-build` 고정 전달) 경유할 것.

**검증(최종)**: `validate_data_contract.py` RED=0·YELLOW=219 · `pytest tests/test_deploy_assets.py
tests/test_master_tables_golden.py` 10 passed · combo-count HEAD 대비 CSM/PL 둘 다 무손실.

## 2026-08-03 — forward_capital bonds source rebase FSC → DART per-bond (inbox `20260803T0055Z`)

**발주**: owner, `inbox/parser/20260803T0055Z__owner__MULTI_2026.1Q__forward_capital_rebase_fsc_to_dart.md`
— 다운로더 `bonds`(FSC data.go.kr) 소스 폐지 전수조사 중 유일하게 남은 FSC 실사용처(`kics_forward_capital.json`)
를 DART per-bond로 옮기는 작업. tier1/tier2_utilization은 2026-06-20에 이미 DART 전환됨
(`wire_capital_securities_to_utilization.py`) — 이번이 세 번째이자 마지막 소비처.

- **소스 교체**: `scripts/forward_capital_simulation.py::load_outstanding_bonds()`가
  `data/bonds/normalized/**/bonds_by_insurer.json`(FSC) 대신 `data/bonds/capital_securities_fy2025.json`
  (DART FY2025 사업보고서 per-bond, 24사)을 직독. 어댑터 한 겹만 추가(tier hybrid/subordinated →
  tier1_hybrid/tier2_subordinated, `outstanding_mn`×1e6 → `issue_amount_won`, `call_date or
  legal_maturity` → `effective_call_date`, `outstanding_mn==0` 드롭) — `simulate_one()`/
  `compute_confidence()`의 콜 roll-off·한도·경과조치 로직은 무변경. `outstanding_mn`(not
  `face_amount_mn`) 선택 이유: 부분상환 반영된 "실제 투자자 지급액 기준"(2026-05-26 owner directive)에
  더 정확. `past_call_outstanding=true`(6/119건)는 콜일자를 그대로 사용 — FSC 시절 동일 실물(흥국화재
  KR0005 신종자본증권1)이 이미 이렇게 처리돼 있던 전례 확인 후 그대로 계승(로직 신설 아님).
  `bond_coverage` enum값도 `fsc_listed`/`no_bonds_in_fsc` → `dart_listed`/`no_bonds_in_dart`로 동시 정정
  (필드명 유지). `data/bonds/normalized/**` 참조 완전 제거(grep 확인).
- **실측 영향**: 38사 전부 재시뮬레이션. 대부분 회사는 채권 스케줄 정밀도가 올라감(예: 푸본현대생명
  2030 ratio 20.03%→104.35% — FSC 쪽 채권 매칭이 약했던 회사일수록 변동 큼). `KR0004`(예별손해)는
  FSC엔 없던 680억 채권이 처음 반영됨(baseline capital 이미 음수라 표시비율 0%클램프는 불변, 내부
  정확도만 개선).
- **🟠 커버리지 회귀 2건, downloader 발주로 이관**: `KR0050`(하나손해보험)·`KR0076`(아이엠라이프생명보험)은
  FSC엔 채권이 잡히는데 DART 24사 목록엔 없음 — FY2025 사업보고서 raw가 디스크에 없음(git-purge 추정,
  `FY2026_Q1/raw/`엔 무관한 `no_filing:true` 스텁만). 이 둘만 `dart_listed`→`no_bonds_in_dart`로 역행,
  2030 ratio가 낙관적으로 뜀(하나손보 124.47%→146.09%, iM라이프 93.65%→152.12% — 채권상환에 따른
  미래 자본감소가 더는 반영 안 됨). raw 없이는 parser가 자력으로 못 채움 →
  `inbox/downloader/20260803T0123Z__parser__KR0050_KR0076_FY2025__capital_securities_annual_raw_missing.md`
  발주(route by raw availability 원칙).
- **as-of 정합 — 사이드카는 이미 배선돼 있었음(발견).** 작업 중 `scripts/emit_capsec_provenance.py`
  (미커밋)와 `validate_data_contract.py`의 `source_id_for_lineage()`/`_SOURCE_LINEAGE`가 **이미
  존재**함을 발견 — validation companion 발주(`inbox/validation/20260803T0056Z`)가 이미 처리된 상태였음
  (하드코딩 `FSC_BONDS` enum → 계보-기반 `SOURCE_ID_LINEAGE_MISMATCH` 검사로 전환 완료). 직접 사이드카
  writer를 추가하려다 **철회** — 이미 있는 "하드코딩 금지, 계보에서 derive" 원칙의 단일 writer와 중복/
  분기 위험. 대신 내 교체가 깨뜨릴 뻔한 지점 하나만 수정: `emit_capsec_provenance.py::_forward_source_file()`
  가 `bonds_source`를 FSC 시절 bare-timestamp로 가정하고 경로를 재구성하던 로직 — 이제
  `bonds_source`가 전체 상대경로 문자열이라 재구성이 필요 없어짐(내가 직접 유발한 지점이라 같이 fix).
  `quarter`/`as_of_date`는 `BASELINE_QUARTER`(2026.1Q/2026-03-31, K-ICS baseline 신선도)를 그대로 유지 —
  채권 스케줄 자체의 vintage(FY2025 사업보고서, 2025-12-31)와는 별개 개념임을 `check_as_of()` 코드로
  확인(`:507-513`, `manifest.baseline_quarter` 대비 검사).
- **검증**: `python scripts/forward_capital_simulation.py` → `python scripts/emit_capsec_provenance.py`
  (사이드카 재발행, source_id FSC_BONDS→DART 확인) → `python scripts/validate_data_contract.py` →
  **RED=0, YELLOW=210**(세션 시작 전과 동일 — 신규 anomaly 없음) → `pytest tests/test_deploy_assets.py`
  → 9 passed.
- **리뷰한 나머지 open ifrs17 inbox 항목 2건은 현상 유지** (프리세션이 이미 dedicated-session material로
  정확히 스코프함): `20260616T0230Z`/`20260616T0420Z` twin threads(`csm_waterfall_history.json`
  진단캐시 재생성 — root 마스터는 확인상 정상, false-negative 방향만) — 재작업 불필요, 그대로 open.
  P2 백로그 `KR0004 PL breakdown`(`scripts/pl_breakdown/`에 신규 회사 핸들러 필요)도 이번 세션 스코프
  밖으로 유지.

## 2026-08-03 (2차) — inbox 드레인: master_tables golden drift 해소 + raw-ready 배치(KR0075/KR1098/KR0051/KR0050/KR0076)

**발주**: validation `inbox/parser/20260803T0245Z`(golden drift) + downloader `inbox/parser/20260803T0150Z`
(5사 FY2024/2025 연간 raw-ready 배치, 4개 개별 요청 통합).

- **golden drift (`test_master_tables_golden.py`) — 원인 확인 후 재생성**: 늘어난 3쌍은 전부
  `(KR0004, 예별손해보험, {2023,2024,2025}.4Q)` — 2026-07-30 세션이 온보딩·continuity 검증까지 끝냈으나
  미커밋 상태로 남아있던 것 (validation의 "제품 세그먼트 컬럼/KR0075 override 계열" 추정은 빗나감, branch
  이름과 무관). `git show HEAD:CSM_waterfall.json` vs 워킹트리를 (원보험사코드,원수사명,공시분기) 단위로
  직접 diff해 확정 — SUMMARY 3축(closing+3P·crosscheck+2S·qoq_warn+5Y) 전부 방향 일치, 나머지 무변동.
  `python tests/test_master_tables_golden.py --update` → PASS. `inbox/parser/20260803T0245Z` resolved.
  **부수 발견(범위 밖, 손 안 댐)**: `test_viz_csm_waterfall_golden.py`·`test_viz_ifrs17_panels_golden.py`도
  별도로 drift 중 — 원인은 KR0004가 아니라 `data/dart/extracted/`에 쌓인 **163개 미커밋 raw 추출 파일**
  (여러 회사 FY2023-2026 sensitivity/csm/insurance_pl 백필로 보임, 어느 세션 소산인지 이 브랜치 이력에
  기록 없음). in-place 덮어쓰기 빌더라 CLAUDE.md 불변식 3대로 건드리지 않음(테스트가 자체 backup-restore
  하므로 라이브 오염은 없음) — **owner에게 별도 보고, dedicated 세션에서 provenance 확인 필요**.
- **raw-ready 배치 4건 (3개 병렬 서브에이전트)**:
  - **KR0075** (2024.4Q+2025.4Q, 12셀 100x override): 2026-07-30에 raw 부재로 "산술로 확정"했던 값을
    신규 raw로 재검증.
  - **KR1098** (2024.4Q, 6셀): "추정 정정(확정 아님)"이었던 override를 신규 raw로 재검증/확정.
  - **KR0051**: PL item19(보험금융손익) 2025.4Q=0.0이 진짜인지 raw 판정 + `exclude_companies`(CSM 제외,
    천원단위 오인) 재확인.
  - **KR0050/KR0076**: `data/bonds/capital_securities_fy2025.json` per-bond 편입(24→26사) →
    `forward_capital_simulation.py` 재실행 → `bond_coverage: dart_listed` 전환 → `validate_data_contract.py`
    RED=0 재확인. 완료 시 owner의 bonds 소스 폐지 발주(`20260803T0057Z`) 선행조건 완전 종결.
  - (상세 결과는 각 서브에이전트 완료 후 이 changelog에 후속 추가 — 작성 시점엔 진행 중)

## 2026-08-03 (3차) — 위 (2차) 배치 완결 확인 + `CAPSEC_COVERAGE_REGRESSION` 회귀 13→3

세션이 (2차)를 쓰던 도중 종료돼(3개 서브에이전트 dispatch 후 "결과는 후속 추가"로 남김) 다음 세션이
이어받음. 서브에이전트들은 이미 작업을 마쳐 워킹트리에 결과가 있었음(미커밋) — 각각 raw/combo-diff로
검증 후 마무리, 도중 별도 회귀 1건 발견해 같이 처리.

- **KR0075 — 2026-07-30 fix 자체가 10x 과소정정이었음 확정.** raw(FY2024_Q4·FY2025_Q4 `_00760.xml`,
  Note(4) 측정요소별 변동내역)를 직접 대조한 결과 필요 배율은 was÷100이 아니라 **was÷1000**(raw가
  천원 단위, 즉 ÷100,000이 정상 천원→억원 환산인데 7/30엔 ÷100만 적용해 최종값이 여전히 10배 컸음).
  12셀(2024.4Q·2025.4Q × 6항목) 전부 raw 행 번호 인용해 재정정. 7/30 당시 "항등식이 원값·÷100값
  양쪽에서 닫힌다"는 근거는 무효 판정 — item4(가정조정)가 나머지의 residual이라 균일 스케일링에서는
  항상 닫히는 항진명제(배율 판별력 없음). `NB_CSM_multiple.json` 신계약CSM 값 재확인 결과 이미 정합
  (다른 세션이 동기화까지 완료해둔 상태).
  **부수 발견**: 이 재정정으로 `PM-2026-07-30_kr0075_csm_100x_unit.md` §3이 배선한
  `CSM_WATERFALL_PLAUSIBILITY`(median×10) 임계값의 앵커 사례(KR0075 비율 1.530, 35사 1위)가 스테일해짐
  — 재정정 후 재계산하면 0.153(35사 중 33위, median의 0.27배)로 완전 역전. 현재 threshold(median×10=5.6)
  기준으로는 발화 대상이 KR0075든 현 최댓값 KR0076(0.9989)이든 미달이라 **당장 오탐/미탐 없음** — 급하지
  않은 건이라 validation에 통지만(`inbox/validation/20260803T0545Z`).
- **KR1098 — 2024.4Q 6셀 추정→확정.** 7/30에 연속성+회사규모 implausibility 추론만으로 넣은 추정
  override(항목1~6)를 신규 raw(`20250331003494_00760.xml`, Note(4) "순보험계약부채의 변동" 표)로 전부
  직접대조 — 6개 전부 추정치와 정확히 일치(단위: 천원, ÷100,000 환산). 2026-06 KR0004 케이스와 함께
  "raw 없이 연속성+규모 추론만으로 넣은 override가 나중에 raw로 100% 확인된" 두 번째 사례 — 이 저장소의
  추정 override 방법론 자체의 신뢰도를 뒷받침.
- **KR0051 — PL item19(보험금융손익) parse_miss 확정 + exclude_companies spot-check.** raw 직접판독
  (제23기 포괄손익계산서, 단위 원): 보험금융수익 36,452,010 + 재보험금융수익 3,149,145,386 −
  보험금융비용 5,458,298,595 − 재보험금융비용 14,105,522 = −2,286,806,721원 = −2286.806721백만원.
  근본원인 확정: `scripts/pl_breakdown/common.py::to_num`의 콤마/공백 제거가 "13, 24"류 복수 주석참조를
  "1324"로 뭉개 `tier1.py::_drop_footnote`의 문턱(abs≤99)을 피해가고, 수익/비용 두 행이 우연히 같은
  주석번호를 인용해 오채택값이 동일해 net이 정확히 0으로 상쇄되는 **결정론적 버그**(진짜 0 아님).
  `_GOLD_CELL_OVERRIDE[("KR0051","2025.4Q")] = {18: -1603.902737, 19: -2286.806721}` 추가, 근본원인은
  다른 회사·분기의 복수-주석 행에도 영향 가능한 범용 버그라 주석에 명시(별도 조사 필요, 이번엔 셀 1개만
  대증). **추가로 기존 `exclude_companies["KR0051"]`(CSM 제외, 천원단위 오인) spot-check**: raw
  가정민감도표(L4317, 기준금액 재보험효과반영전) 169,315천원=1.693억이 기존 결론("기말 CSM 1.69억")과
  정합 — 제외 유지 재확인(CSM 변동표 완전 재도출까지는 안 함, 비필수 판단).
- **KR0050/KR0076 — 검증만(이미 완료돼 있었음).** `capital_securities_fy2025.json`에 이미 편입,
  `forward_capital_simulation.py` 재실행 결과 이미 양사 `bond_coverage: dart_listed` 확인 — 추가 작업
  불요, `inbox/parser/20260803T0055Z` 완전히 닫힘.

### 🆕 부수 발견 — `CAPSEC_COVERAGE_REGRESSION` RED 13건 (검증 중 조우)

위 4건을 raw-verify하던 중 `python scripts/validate_data_contract.py`가 RED=13으로 나옴 — 원인은
이 건들과 무관, validation이 신설한 별도 룰(`inbox/validation/20260803T0310Z`, capital-securities 커버리지
census: forward_capital/tier1/tier2가 참조하는 회사인데 `capital_securities_fy2025.json`에 레코드
자체가 없으면 RED — "스캔 후 무발행"과 "미검증"을 구분). 같은 소스 파일을 만지는 김에 처리:

- raw 있는 10사 직접 확인 → **9사 무발행 확정**: KR0008(삼성화재)·KR0029(AIG손해)·KR0074(라이나)·
  KR0075(비엔피파리바카디프)·KR0080(에이아이에이)·KR0095(메트라이프)·KR0100(처브라이프)·KR0051(신한이지)·
  KR1098(카카오페이) — 신종자본증권/후순위채/후순위사채/무보증사채/조건부자본증권/사채발행내역 6개 용어
  전부 매칭 0건이거나(대부분), 매칭이 있어도 **자사 발행이 아닌 타사 증권 투자보유**로 확인
  (KR0008: 신한/하나/KB금융지주 조건부자본증권 8건 매칭 → AFS/AC 유가증권 명세표, 투자자산이지 자사
  발행 부채 아님). `bonds: []` 명시 레코드 추가(KR0069 기존 패턴과 동일 스키마).
- **🔴 1사 신규 발견 — KR1011(IBK연금보험) 후순위채 4건, 완전 누락 상태였음.** raw "18. 차입부채" 주석
  표(단위 천원, 당기말)에서 직접 확인: 제1~4회 무보증 사모 후순위사채, 발행 2021-12-28~2023-03-30,
  만기 2031-2033, 금리 3.98~7.40%, 액면 합계 360,000,000천원(=3,600억), 사채할인발행차금 차감 후
  당기말 장부금액 합계 359,313,971천원(raw 합계행과 정확히 일치 검증). 콜옵션: 발행일로부터 5년째
  되는 날 및 이후 매 이자지급기일에 전액 중도상환 가능(전부 as_of 2025-12-31 기준 미도래).
  `capital_securities_fy2025.json`에 편입 → `wire_capital_securities_to_utilization.py` 재실행 →
  tier2 소진율 22.2%로 반영(지금까지 0%로 완전히 빠져 있었음 — forward_capital/tier2_utilization
  둘 다 이 회사의 실제 후순위채 부담을 반영하지 못하고 있었던 실질 데이터 갭).
- **잔여 3사 raw 부재**: KR0049(악사손해보험)·KR0150(서울보증보험)·KR1010(교보라이프플래닛생명보험) —
  downloader 발주(`inbox/downloader/20260803T0535Z`).

**검증**: `forward_capital_simulation.py` → `wire_capital_securities_to_utilization.py` →
`emit_capsec_provenance.py` → `validate_data_contract.py`: RED 13→3(잔여는 downloader 발주로 설명됨,
미설명 RED 0) · YELLOW 210→219(신규 anomaly 아님 — CSM cohort median이 KR0075/KR1098 재정정으로
이동하며 생긴 배경노이즈, generic scan 재계산 결과) · `pytest tests/test_deploy_assets.py` 9 passed.
`inbox/parser/20260803T0150Z` status: answered.

## 2026-07-30 — inbox 드레인(17건) + KR0075/KR1098 100x/1000x unit bug fix + KR0004 온보딩 + PL near-miss

**전체 처리**: `inbox/parser/` lane:ifrs17 17건 전수 처리(2건 이미 완결분 bookkeeping만 정정+이동, 9건
신규/재확인 답변, 3건 raw-refetch를 downloader에 재발주, 1건 신규 룰을 validation에 발주). 상세는 각
inbox 파일의 `## 답변` 참조 — 요약만 아래.

- **KR0075(비엔피파리바카디프생명) CSM_waterfall 100x 과대 — fix.** owner가 항등식+35사 census(CSM÷K-ICS
  지급여력금액, KR0075=153.01 유일 이상치)로 확정한 건. raw는 이 브랜치에 없음(meta.json만) → 산술
  근거로 `csm_manual_overrides.json` 12셀 ÷100 override. **포스트모템 작성**
  (`docs/postmortems/PM-2026-07-30_kr0075_csm_100x_unit.md`, README UH-6) — 근본원인은
  `build_root_masters.CSM_ABS_CAP=5e5`가 절대값만 보고 상대규모(동종 대비)를 안 봐서 통과(false-green).
  `CSM_WATERFALL_PLAUSIBILITY`(기말CSM÷K-ICS지급여력금액, median×20) 신규 룰을 validation에 발주.
- **KR1098(카카오페이손해) CSM_waterfall 1000x 과대 — fix (raw 직접대조).** 원 발주(`20260614T1330Z`)의
  "신계약CSM 2조원대 비현실" flag를 FY2025 raw XML(`20260323001537_00760.xml`)에서 직접 확인: 해당
  노트가 "(단위: 천원)"인데 combined-agn 추출기가 천원→백만원(÷1000) 환산을 건너뛰어 net ÷100(정답
  ÷100,000)이 됨. 2025.4Q 6셀은 raw 확정 override, 2024.4Q 6셀은 raw 부재로 연속성+회사규모
  implausibility 추론 적용(미확정 — downloader에 FY2024 raw 재취득 발주).
- **KR0029(AIG) 동일 유형 — 이미 해소 확인.** 원 발주 당시(~2000x 과대) 대비 현재 마스터가 정확히
  ÷1000된 정상값으로 이미 들어와 있음(경위 불명, 어느 세션이 고쳤는지 TODO 미기록 — 재작업 불요, 확인만).
- **KR0004(예별손해=구MG) 신규 온보딩(3개년).** `waterfall_for_dir()`를 raw 3개 dir(FY2023/24/25_Q4)에
  개별 호출(전체 raw-glob 아님, 안전) → 항등식 정확히 닫히는 18행 확보 → `csm_waterfall_master_diag.json`에
  직접 append(override 아님 — 이 회사는 diag에 행 자체가 없어 override "set"이 no-op됨, 아래 근접사고 참조).
- **KR1011(IBK연금보험) 잠재 데이터손실 방지.** 위 리빌드 검증 중 발견: KR1011(2026-07-04 온보딩, diag에
  없음)이 `build_csm()` 재실행 시 18행 통째로 사라지는 것을 확인 → committed 값 그대로 diag에 append해 보호.
- **🔴 근접사고 — `build_root_masters.py::main()` 통짜 실행 금지 확인.** KR0075 fix 검증 중
  `build_pl()`(PL_breakdown.json 재생성)까지 같이 돌아 **PL 마스터가 7,799행/319 (company,quarter)조합
  →2,940행/117조합으로 붕괴**(207조합 소실, 예: KR0001 전 분기)를 diff로 발견 → 즉시 `git checkout HEAD --
  PL_breakdown.json`로 복구, PL은 이번 세션 미변경. 원인=`pl_breakdown_master.json` diag도 이 브랜치에서
  raw-purge로 stale(CSM 쪽과 동일 근본원인, 이전엔 CSM만 알려져 있었음). 상세·재발방지 =
  [[project_git_purge]] 메모리 갱신. **향후 이 브랜치에서는 `build_csm()`/`build_pl()` 개별 호출 +
  git HEAD 대비 (company,quarter) combo-diff 필수 — bare `main()` 금지.**
- **`sensitivity_heatmap_provenance.json` 신규 발행** (validation `20260721T0530Z`, UH-3 잔여). 신규
  `scripts/emit_sensitivity_provenance.py` — rcept_no로 raw dir 역탐색해 source_file 확인 + as_of/quarter
  파생(게이트와 동일 로직) + 회사는 코드가 아닌 **이름으로 조인**(이 마스터의 게이트 join key 특성).
  31/32 사(엠지손해 SA=0 제외) 커버, 게이트 RED=0 확인.
- **FY2025 sensitivity 전사 refresh — 이미 완료 확인.** TODO엔 "흥국만 FY2025, 나머지 FY2024"로 남아
  있었으나 실제로는 **32/32사 전부 FY2025/2025-12-31**(언제 누가 했는지 미기록) — TODO 정정.
- **NB CSM interim partial 이슈 — root는 상당수 해소, 진단파일만 stale.** `check_nb_csm_history.py`가
  여전히 27건 OVER/UNDER 보고하나, 이는 별도 진단파일 `csm_waterfall_history.json`(재생성 안 됨)을 읽는
  것이고 **root `CSM_waterfall.json` 자체는 이미 정상**(롯데/미래에셋/한화생명 등 2025.2Q/3Q 단조증가
  확인) — false-negative 위주. extractor의 interim 레이아웃 인식 보강은 여전히 미완(dedicated 세션).
- **KR0087(동양생명) FY2026.1H IR 신규 추출** (신규 raw, 서브에이전트). `data/ir/FY2026_Q2/parsed/KR0087_동양생명/csm_metrics.json`
  신규(마스터 미수정 — 통합은 owner 판단 대기). 신계약CSM 1Q=944.7억(기존 마스터 944.6억과 근접 교차검증)·
  2Q=1,480.2억·1H누계=2,424.9억. **배수는 IR 자체가 2가지 다른 정의(APE대비/월초P대비)를 공시**하는데
  둘 다 이 저장소의 KIDI-월납월초 기준과 다름 — 같은 2026.1Q에 대해 마스터 9.463x vs IR 자체 8.15x(~16%
  괴리) 확인, **정의 재조정 없이 그대로 병합 금지** 플래그.
- **교보생명(KR0073) csm_extractor.py period_type 추가 + 3개 분기(2023.4Q/2024.1Q/2024.2Q) 전기 재추출**
  (downloader `20260617T1130Z`, 서브에이전트) — 결과는 다음 세션 노트 참조.
- **신한이지(KR0051) item19 raw 재확인** — 6주 전과 동일하게 여전히 raw 없음(meta.json뿐), downloader
  발주가 실제로는 안 나가 있었던 것 발견 → 이번에 실제 발주.
- **하나생명(KR0097) FY2025 audit-annual — 조사만, 미반영.** 주석 14-4 CSM 변동표(단위 천원,
  수정소급법/공정가치법/이외모든계약 3-way 서브컬럼) 발견했으나 산출 기초값(4,446.82억)이 현재
  마스터 2024.4Q 기말(4,389.6억)과 57억(1.3%) 어긋나 원인 미판별 — 신뢰도 부족해 마스터 미반영,
  코드기반 재파싱 필요.

## 2026-07-30 (2차) — inbox 재확인: NB_CSM_multiple.json half-sync fix + 6건 already-done 확인

owner가 "inbox 다시 확인하고 작업 실시" 재발주. 1차 세션 종료 시점에 아직 open이던 lane:ifrs17
9건(backlog digest 제외 실질 8건) 전수 재확인.

- **`NB_CSM_multiple.json` half-sync — fix.** owner가 직접 지적(`inbox/_resolved/20260730T0823Z`,
  route:reparse): 1차의 KR1098 ÷1000 fix가 `CSM_waterfall.json`에만 반영되고 파생 마스터
  `NB_CSM_multiple.json`(빌더: `scripts/build_nb_csm_multiple.py`)은 재생성 안 된 채였음. 정식
  스크립트는 `data/kidi/premium_summary.json`(gitignored, KIDI 라이브 재수집 필요)이 로컬에 없어
  실행 불가 → 기존 파일의 월납월초보험료/티커 필드는 그대로 보존하고 `CSM_waterfall.json`에서
  갱신된 신계약CSM만 다시 읽어 4개 파생필드(신계약CSM_연누계/당분기, 배수_연누계/당분기, 동일
  `_ratio`/`_MULT_CAP=40`/`_MULT_FLOOR=1.0` 로직)만 재계산 — 전체 재실행과 수학적으로 동일한
  결과, before/after 전수 diff로 무관 필드 불변 확인. KR1098: 2024.4Q 배수 12.8169→**0.0128**
  (owner 기대값 일치), 2025.4Q 배수 null→**2.9711**(owner 수기계산 2.9707과 오차 0.0004, 반올림차).
  **부수 발견 — 같은 half-sync 버그가 7개사 더**: KR0029(AIG, null→986.8)·KR0011(DB손해 2023
  4개분기)·KR0073(교보 26.1Q)·KR0001(메리츠 26.1Q)·KR0094(신한라이프 26.1Q)·KR1000(코리안리
  2023.4Q~2024.4Q, 당분기 부호반전 1건 포함 — 기존 disposition-pass의 "코리안리 Q4 불연속=
  사업보고서 연간재작성" 기록과 일치, 신규 이상 아님)·KR0083(푸본현대 26.1Q) — 전부 함께 재동기화.
  KR0004/KR1011은 파생파일에 행 자체가 없었어서 6행 신규 추가(월납 오프라인 미확보 → 배수 null).
  **⚠️ 별건 회귀 발견, 미수정**: `CSM_waterfall.json`의 티커 필드가 20개사+에서 zero-pad 유실
  ("000060"→"60") — `update_tickers_from_dart.py` 기준 6자리 zfill이 정본. `NB_CSM_multiple.json`엔
  전파 안 함(기존 캐시 티커 보존), 소스 자체 회귀는 DART API 재조회 필요해 후속 세션 flag만.
- **6건 already-done 확인, 인박스 페이퍼워크만 정리**:
  - FY2025 sensitivity mass-refresh(`20260615T0520Z`) — 32/32사 확인(28사 원 요청 + IBK/AIG/MG/
    카카오페이 4사), 흥국생명 파일럿 부호/크기 정확 일치. 티켓이 우려한 "장해질병 라벨 변형"은 raw
    재확인 결과 **K-ICS 보험위험 방법론 서술 섹션의 무관한 키워드 매치**로 판명(IFRS17 민감도 표와
    무관) — 헛다리, 조치 불요.
  - `sensitivity_heatmap_provenance.json`(`20260721T0530Z`) — 게이트(`check_as_of` L483, "published"=
    scenarios 비어있지 않은 회사) strict 모드 RED=0 실행 확인.
  - KR0004 CSM 통합(`20260616T0210Z`) — continuity 검증 완료. PL breakdown은 여전히 미착수(행 0개,
    전용 핸들러 필요) → `TODO_parser_ifrs17.md` P2 등록, 스레드는 open 유지.
  - **KR0073(교보) 13개 분기 전체 — 1차 세션이 발주한 서브에이전트가 이미 완료**해 있었음(1차
    changelog "결과는 다음 세션 노트 참조" 예고분, 이 항목이 그 노트). closure 13/13 정확, 연도경계
    continuity(Q4말→익년Q1초) 3개년 전부 완전 일치 재검증. **조사 과정에서 아키텍처 확인**:
    `csm_extractor.py`는 CSM 상각 스케줄(연차버킷) 전용이고, 티켓이 지목한 "17-4 요소별 변동내역"
    롤포워드 표(컬럼=미래현금흐름/위험조정/보험계약마진)는 캡션에 "보험계약마진" 리터럴이 없어
    `score_table()`에서 항상 score=0 → 애초에 선택 안 됨(period_type 유무와 무관한 별개 gap).
    실제로 이 표를 다루는 건 `measurement_extractor.py`(§14(4), `_iter_tables_with_context`를
    csm_extractor.py에서 shared import)로 보이나 거기도 당기/전기 라벨 구분은 미구현 — 다음에 이
    gap이 재발하면 `measurement_extractor.py` 쪽에 period_type을 추가하는 게 맞는 위치.
  - KR0087(동양생명) FY2026 H1 IR(`20260730T0010Z`) — 이미 완료 확인(`data/ir/FY2026_Q2/parsed/`,
    다른 세션). CSM 롤포워드+상품별 신계약CSM+배수 2종(APE대비/월초P대비)+보험손익 전부 추출·상호검증
    완료, 자체적으로 "IR 월초P 기준 배수 분모가 KIDI 대비 16% 큼(분자는 일치)" 발견까지 플래그.
    루트 마스터 미반영은 의도적(4개 마스터 명시 보호) — 통합은 owner 결정 대기.
- **2건은 open 유지(의도적)**: `20260616T0230Z`/`20260616T0420Z` 쌍 — `data/dart/viz/
  csm_waterfall_history.json`의 생성 스크립트(`viz_build_csm_waterfall_history.py`)가 디스크에서
  완전히 사라짐(`.pyc`만 잔존) — 재생성은 실질적 고고학 작업, 1차 세션이 이미 "dedicated session
  대상"으로 정확히 스코프함(root 마스터 자체는 확인상 정상, false-negative 방향만 — 라이브 리스크 낮음).
- **게이트 재확인**: `python scripts/validate_data_contract.py` 전체 재실행 — RED=0, YELLOW=210
  (동일 generic-anomaly baseline, 신규 anomaly 없음).
- **master xlsx 재생성 필요**(publishing, 공식 xlsx skill) — `NB_CSM_multiple.json` 추가 변경.

## 2026-07-04 — IBK연금보험 KR1011 신규 온보딩 (CSM + PL + viz 전파)

- **universe.py**: IBK연금보험을 `NON_LISTED_SKIP`에서 제거 → `AUDIT_REPORT_ANNUAL`에 추가. DART 감사보고서 F형 라우트.
- **ifrs17_ingest_audit_annual.py**: `NAME_ALIASES` 적용 (IBK연금보험 → 아이비케이연금보험 DART 검색).
- **CSM_waterfall.json**: 3개년 18레코드 hand-assemble (measurement block0 당기 whole-book, 천원→억원). closure/continuity 3중 검증 통과. waterfall viz partial (newbiz 스테이지 누락 — parser 추가 대응 필요).
- **build_pl_breakdown.py 4패치**: IBK 라벨 변형 처리 — `NI_LABELS`+당기순손익, `_is_income_statement`+영업손익, `extract_tier1` ni_raw+op 확장.
- **_GOLD_CELL_OVERRIDE KR1011 3개년**: notes [166][167] (보험수익/보험서비스비용 내역) 직접 계산. item3=보험수익합계−서비스비용합계, item4=CSM상각, item5=RA변동, item6=예실차(예상−실제), item7=잔차(손실부담계약). closure 5종 Δ=0 전부. item8-12=0(재보없음), 13-14=0(자동차/일반없음).
- **viz 전파 재빌드**: sensitivity_heatmap(27/32), csm_amort_schedule(28/30), insurance_pl_breakdown(29/29), csm_waterfall(47 total), csm_bubble, downstream_kpis, earnings_quadrant.
- **publishing inbox**: `20260704T0600Z__parser_ifrs17__KR1011__ibk_masters_ready.md` 발송.

---

## 2026-06-20 — owner-fill durability · capital securities · CSM continuity (교보/삼성) · provenance
- **Owner xlsx fill durability (0811Z):** owner가 root에 sync한 fill을 빌드 소실서 보호. PL은 override 레이어가 없어 신규 **`data/dart/viz/pl_manual_overrides.json`** + `build_root_masters._apply_pl_overrides`(_zero_other_expense 後) 도입(121셀). CSM 10셀(AIG손해 2025.4Q 6·하나손해 이자부리/조정 4)→`csm_manual_overrides.json`. 재빌드=owner root 값 정확 재현(값 변경 0 검증). 현대해상 26셀 estimate 플래그.
- **자본증권 발행잔액→한도소진율 (0238Z, owner):** 24사 DART 사업보고서 자금조달/사채/신종 주석 per-bond 추출(발행일·법만기·**콜(=실효만기 5y)**·금액·잔액) → `data/bonds/capital_securities_fy2025.json` + 정식 `data/dart/capital_securities_issuance.json`(신종→Tier1·후순위→Tier2·provenance). `wire_capital_securities_to_utilization.py`로 tier1/tier2_utilization 분자 라이브 교체(**경과조치 pre-2023 별도제외**=owner 결정) + 신한이지 분모 SCR×50% 교정 → **data-contract gate RED 4→0**(동양240%/KB218%/미래126% proxy + denom). forward outlook=콜 roll-off(`capital_securities_forward_outlook.json`), 흥국식 콜경과 예외 플래그. census: 보유25/무발행11(삼성화재·삼성생명·외국계). NB: as_of 2025.4Q(2026.1Q raw 5사만→콜 reconcile), 푸본 후순위 발행일 estimate.
- **CSM continuity 정정 (0600Z 교보 / 0545Z 삼성):** 교보 2023.4Q 기말+2024.1Q/2Q 기초→58,249.2(재작성 통일, FY2024 rollforward 확인), 삼성 2023.4Q 기말 123,926→122,474(owner gold). item4(가정조정) 흡수로 identity 유지. csm_manual_overrides. **validate_master_tables cont 6→0**, 8셀만 변경·무클로버.
- **Provenance 사이드카 (1242Z-B/1252Z):** `emit_ifrs17_provenance.py` → `CSM_waterfall_provenance.json`(321)·`PL_breakdown_provenance.json`(632), source_id=DART+item_block, owner_override/estimate 플래그.
- **진단(미해소, open):** nb_csm 0420Z=8/30 회수·22 interim §14 추출기갭. sensitivity 3 partial(미래에셋 OCR·신한라이프 prose·한화손해 시장위험형)=자동복구불가. 한화 CSM 상각스케줄 1029Z=form_type unknown 추출갭. 삼성화재 자동차손익 2026.1Q=-40=owner 확인 정답(pass).

---

## 2026-06-16 — CSM 워터폴 continuity 전사 RED 8→0 (2026.1Q 기시 misparse + within-FY drift)

owner 직접 검증 + validation `20260616T0605Z`/downloader `20260616T0640Z`. `validate_csm_continuity.py` **RED 8(7사)→0**.

**근본원인** = `build_csm_waterfall_master`의 product-set 합산 버그(missing raw 아님 — 재추출이 committed 동일 misparse
재현). 당기 발행(원수) 유배당+무배당+변액 sub-table을 부분만 집거나 전분기 copy 혼입:
- **2026.1Q 5사** 기시(검증 워크플로우 9사 병렬, raw 후보블록 재구성): 푸본 1669.3→**1906.5**(유212.1+무1669.3+변25.1),
  메리츠 111893.5→**111037.0**(전분기 copy 제거), 신한 74422.9→**75537.3**, 에이비엘 9229.7→**9702.5**, 교보 70768.8→
  **65109.6**. 전부 = 직전 2025.4Q 기말(owner 검증).
- **within-FY drift**: FY2023(현대 88281.1·에이비엘 7017.8·KDB 5239.4·교보 46967.3)·FY2024(KB라이프 30176.4·코리안리
  8031.5) 기초 상수화. drift 원인 = 소급재작성(연중 기초 재공시) 또는 전기 copy.

**수정(비파괴)**: `build_csm_waterfall_master.py` 미실행(파괴적). 검증값을 `data/dart/viz/csm_manual_overrides.json`
'set'(+62) 인코딩 → `build_root_masters.build_csm()`(diag+override 공식 재조립, 값_당분기 정식 재계산). **durable**.
감사기록 `data/_derived/csm_continuity_corrections.json`. identity 무파손(15셀), within-FY 상수·FY경계 연속 검증, pytest 110.
⚠️ 다운스트림 viz(csm_bubble/NB_CSM_multiple/history/diag)·근본 파서 수정은 raw 복원 세션(별track).

## 2026-06-16 — designer/validation 후속: sensitivity period/as_of + NB-CSM partial sweep

**A. sensitivity period/as_of** (designer `20260616T0030Z`): `sensitivity_heatmap.json` entry가 rcept_no만 있고
`period`/`as_of`=null이던 것 → `viz_build_ifrs17_panels.py` `build_panel`에 `_period_asof_from_rcept` 추가
(`add_as_of` 플래그로 **sensitivity 패널만**) → 27社 FY2024/2024-12-31, 흥국 FY2025/2025-12-31. scenario 무변경,
타 패널 3종 byte-identical, pytest 110. designer `asOfFromRcept` fallback과 동일 규약(rcept 제출월).

**B. NB-CSM partial 오염 sweep** (validation `20260616T0230Z`): `csm_waterfall_history.json` non-ok **41 cells**
census(no_csm_block 29·partial 6·no_extract/empty/download_error 6). **partial 6건**(롯데 2025.2Q NB=0·미래에셋
2025.2Q/3Q·한화생명/현대해상 2025.2Q·삼성화재 2023.1Q)이 NB YTD 적극 오염. 재추출은 **반기/3분기 raw 부재로
raw-blocked** → downloader 발주(`inbox/downloader/20260616T0400Z__…nb_csm_interim_raw_fetch`). 삼성생명 2025.2Q
OVER(+26%)는 partial 아닌 **scope diff(별도/연결)**로 별건 disposition.

## 2026-06-16 — round3 IFRS17 QA (P1/P2/P3) + IFRS17 도메인 SKILL 결정화

**round3 데이터 글리치** (inbox `20260616T0007Z__…ifrs17_pl_sensitivity_round3`) → **commit 5b9b0eb**:
- **P1 흥국 해지율 방향** = staleness(부호버그 아님). heatmap 흥국이 FY2024(rcept 2025…)였음 → FY2025 재추출
  (rcept 20260331004251) 반영. 해지율↑ csm/pl **둘 다 −**(FY2024는 csm−/pl+ 반대), 사망률↑ +27.95/+5.78 =
  owner 기대 일치. `viz_build_ifrs17_panels.py` best-status dedup으로 **흥국 1社만 교체**, 27社+패널3종
  byte-identical, pytest 110. (가비지사 농협/케이디비 미혼입 — phase-2 잔존.)
- **P2 푸본현대 투자손익 −1,487.7억** = **REAL**. FY2025 별도 포괄손익계산서 line-by-line + 요약 교차검증,
  24항목 전부 백만단위 일치, 당기순이익 −1,187억 = FY2025 연간순손실 실재. no-op.
- **P3 하나생명 투자손익 None** = **parse_miss**(실제 0 아님). II.투자수익/III.투자비용 2-line 공시 →
  build_pl_breakdown L275 단일 `L("투자손익")` 미스. 정확값 item18=317,891.06·item17=**+821.41백만**
  (영업이익=item1+item17 gap0; owner flag 예측 +15,037은 기타사업비용 이중차감 오폐합). `_GOLD_CELL_OVERRIDE
  [(KR0097,2025.4Q)]` 추가(메트라이프 audit-only 패턴). ⚠️ 라이브 master 반영 = raw-enabled rebuild 필요
  (이 브랜치 파괴적, [[project-git-purge]]). → TODO out_of_scope "하나 item17=FS-API" 항목 **해소**(파서측 정정).

**IFRS17 도메인 SKILL 결정화** (inbox `20260616T0043Z__…skill_creator_domain_skills`):
- Anthropic `skill-creator`로 `.claude/skills/ifrs17-parser/` 작성 — `SKILL.md`(트리거 description + 운영 코어) +
  `references/pipeline-map.md`(배선·파일맵·스키마·run/verify) + `references/quirks-and-traps.md`(단위/부호/사별
  quirk/destructive-rebuild/항등식). **SOT = `docs/domains/claude-agent-ifrs17.md` 유지**, SKILL은 그 위
  운영 트리거 레이어(요약+참조, 복붙 없음); SOT의 2026-05 PoC-status가 코드와 충돌 시 코드+SKILL 우선 명시.
  `.claude/` gitignore → 머신-로컬(미push). **K-ICS SKILL은 K-ICS 세션 별도**(2-lane split).

## 2026-06-14 — CSM sensitivity panel: column-map / unit / 손보-recovery (inbox 20260614T0712Z)

Owner live-site QA on the CSM sensitivity pipeline — fixed 3 glitches in
`scripts/viz_build_ifrs17_panels.py` (panel parser only; no extractor change):
- **G4b (column mapping)**: `_extract_sensitivity_band` used a fixed LEFT-anchored csm_idx, so
  rowspan-elided 2nd+ risk rows (기준금액 columns dropped) shifted → wrong ΔCSM + null PL. Now RIGHT-anchors
  (negative idx) for the standard 기타포괄손익-trailing layout; other layouts (위험경감/product-row) guarded, no regression.
- **G6 (units → 억원, data-determined)**: cue (억원/백만원/천원/만원) else cross-check table base CSM vs
  `CSM_waterfall.json` total CSM (억원) → power-of-10 snap. Owner's notes were BOTH wrong: 삼성=백만원 (not 만원),
  현대=천원 (not 원). 현대 사망률 ΔCSM −853억 ≈ 삼성 −1,334억 (640× anomaly gone). Output carries
  `unit/unit_detected/unit_source`. Sanity guard: max|ΔCSM| > 3× total CSM → `unit_source=suspect` + null + warning
  (메트라이프 default-백만원 −59조 blocked).
- **G7 (missing 손보)**: panel read only `_sensitivity_mvp.json` (is_mvp dropped valid tables) + the picker
  preferred CSM-less tables. Now reads full `_sensitivity.json` (build_panel skips non-rcept K-ICS files), picker
  prefers a 보험계약마진 column, methodology-table penalty, + a PL-only handler (NH 출재경감 당기손익). Recovered
  메리츠/DB손해/KB/NH (한화 = 별첨, legit partial) + bonus AIA/케이비라이프. **0 regressions, 25/28 ok.**
- Verify: production build touched only `sensitivity_heatmap.json` (other panels byte-identical); pytest 110;
  whole-cohort mvp-vs-full diff CHANGED 0.
- **Follow-up (same session, decision-free sweep):** F16 흥국생명 product-as-rows **DONE** — new
  `_extract_heungkuk_product_rows` + `_is_heungkuk_csm_pl_capital_layout` (4th path, 흥국-specific bare-'CSM'×2 +
  손익효과 + 자본효과 header guard) → 6 proper risk scenarios (사망률/해지율/사업비 × 상승/하락; was garbage
  risk='건강보험' shock='5,852'). status unchanged (was already ok), 0 regression, other panels byte-identical,
  pytest 110. 미래에셋생명·신한라이프 confirmed **legit-absent** (no insurance-risk CSM sensitivity table in body
  — only market-risk/pension; current unavailable/partial correct). **BLOCKED on this branch (raw DART purged):**
  closing-5 label variants / 흥국화재 NEW 2025.4Q-2026.1Q / 흥국생명 2026.1Q doubling — every target (사,분기) raw
  XML was history-purged → can't reproduce or verify; owner must restore raw (backup `insurequant_git_backup_20260614`)
  or run on a branch that still has it. NOTE: gold gate also non-runnable here (`_verify_csm_golds.py` globs repo-root
  `CSM waterfall_*.xlsx` → 0/0; `build_csm_waterfall_master.py` collapses the committed diag to 1 company).
- **Follow-up (validation reparse 20260614T1135Z):** 푸본현대 csm_delta under-scale (csm 9.86억 vs pl 1164.85억)
  root cause was NOT a unit/ratio bug — all 4 of its SA-tagged blocks are the SAME measurement rollforward
  ("기말 보험계약부채(자산)", no ± shock rows); the panel read its rollforward columns as csm/pl = garbage. Fix:
  `_has_shock_rows` (a real sensitivity table has X% 증가/감소/상승/하락 rows) → added as the top picker signal
  AND a guard in extract_sensitivity that returns `partial` when the picked block has no shock rows. Also caught
  KB손해 (5 mis-tagged '(14) 가정변경…변동 내역' rollforwards, no real shock table). 푸본현대 + KB ok→partial
  (garbage→honest); 미래에셋/신한/한화 unchanged; **0 regression on the 23 real ok companies**; pytest 110. This
  removes the peer-scale outlier so validation's SENSITIVITY_UNIT_SANITY should clear. (NB: high within-row
  |csm/pl| for 현대/삼성/한화생명 is legit — CSM absorbs the shock, not an error.)

## 2026-06-14 — REFACTOR 6/6 (bs_snapshot/sensitivity externalization) + GOLDEN-E2E expansion

Finished the owner `parser_refactor` backlog (inbox `20260613T0200Z`) for the ifrs17 lane:
- **REFACTOR-2 → 6/6**: externalized bs_snapshot + sensitivity scoring keywords (15 lists) to
  `data/ifrs17/table_scoring_keywords.yaml` via `scoring.py` `load_scoring().extra` (bespoke sets — all
  ride in `.extra`, no standard fields). Module constant names unchanged → consumers
  (`viz_build_ifrs17_panels`, batch scripts) untouched. intra-block DEDUP `&bs_slices` anchor
  (`_HEADER_BS_SLICES`==`_ROW_SLICES`). New golden tests `test_{bs_snapshot,sensitivity}_extractor.py`.
- **GOLDEN-E2E**: hermetic multi-table fixtures for measurement/insurance_pl/reinsurance (삼성화재
  20250311001055 real values, 2 decoys + 1 genuine), proving table SELECTION end-to-end. +3 tests.
- **Verification** (main session re-ran, did not trust subagent report): `pytest tests/unit/` **110 passed**;
  independent HEAD-vs-config byte-identity **15/15** (non-circular — compares git HEAD constants, not the
  golden literals); E2E asserted values 9/9 present in source JSON; 6-extractor diff is import + constant-load
  only (logic unchanged, −280/+74).
- **Remaining**: REFACTOR-3 slice2 (`src/solvency/parser/` column-picker → registry) is K-ICS/solvency lane,
  out of ifrs17 session scope → kics lane to pick up.
- **Method note**: a workflow subagent HUNG the Windows shell on a multi-line `python -c "..."` JSON dump
  (default Bash timeout never fired → runner wedged, unstoppable via TaskStop). Recovery: drove Phase 2 via a
  hardened fresh Agent (script files / Read tool, never inline multi-line `python -c`). Bake this into future
  fan-out prompts.

## 2026-06-13 — Lane split
Parser forked into two parallel lanes (kics / ifrs17). IFRS17-scoped history starts here; older IFRS17 entries
remain in the frozen combined `changelog_parser.md`. In-flight: REFACTOR-1/2 (scoring config layer, 4/6
extractors + golden tests). Open work: [`TODO_parser_ifrs17.md`](../TODO_parser_ifrs17.md).
