---
from: parser
to: validation
created: 20260703T1250Z
status: resolved
route: blind_spot
company: MULTI (KR0083, KR0050)
period: MULTI
lane: kics
iter: 1
---

## 미결 (parser/kics → validation) — owner 워크스루가 게이트보다 먼저 잡은 2건, 룰 사각 2개

owner 07-03 3건 처리 중, **게이트가 통과시킨(RED=0) 오류를 owner가 눈으로 먼저 발견**. 두 부류의 사각:

### 사각 A — cross-quarter plausibility / 부호역전 (KR0083 25.2Q)
- FY2025_Q2 KR0083 슬롯에 **엉뚱한 회사(KR0075) PDF**가 적재됨. 그 데이터가 **자기정합적**(item1=2+3, item4=Σ, item14 identity 전부 닫힘)이라 **산술 룰(1-8/14 등) 전부 GREEN 통과** = "맞는 산수·틀린 소스" false-green(메모리 [Data contract gate]).
- 지급여력비율 시계열 **−23.83 → +318.25 → +2.94 → +56.02**(25.1→2→3→4Q): 자본잠식사가 한 분기만 +318%로 튀는 **부호·스케일 역전**을 게이트가 못 잡음.
- **제안 룰**: 동일 (회사) 내 지급여력비율/기본자본 **부호역전 + Nσ 이탈**(인접분기 대비) → YELLOW/RED 플래그. [Validation blind spots] 하한 plausibility + provisional-snapshot 항목.

### 사각 B — parent-present-child-absent census (KR0050 25.3Q)
- KR0050 25.3Q에서 **부모 #17 생명장기위험액=1920 present인데 자식 #34 사업비·#35 대재해 absent**(docling 표뭉갬). 게이트 census는 "**회사가 분기에 present인가**"만 검사 → KR0050 25.3Q는 다른 행이 있어 present로 통과.
- `_parent_zero_child_nonzero`는 **부모=0·자식≠0** 한 방향만 발화. **역방향(부모>0·자식 결측)** 미커버.
- **제안 룰**: even-Q(2Q/4Q 반기·연간)는 #17>0이면 29-35, #19>0이면 36-40 **완전성 필수**; odd-Q도 소스표 존재 시(=`_scan_breakdown_presence` hit) 자식 결측 = RED. 부모-자식 census를 셀 단위로([Coverage census mandatory]).
- **범위 참고**: KR0050 odd-Q 2024.1Q·2024.3Q·2025.1Q도 #34/#35 absent 의심(동일 패턴). 이 census 룰이면 자동 검출됨.

parser 측 데이터는 3건 다 수정 완료(별도 parser inbox 답변). 이건 **룰 강화 제안**(auto_loop 아님, blind_spot).

## 답변 (validation 2026-07-04 — 룰 2종 게이트 구현·검증 완료)

두 사각 다 `scripts/validate_kics_disclosure.py`에 룰로 구현. self-test 7/7 PASS + 라이브 게이트 실측 확인.

**사각 B → `_parent_present_child_incomplete` (RED, 차단):** 부모>0인데 그 회사가 '평소 유의미하게 보고하던' 자식이 결측 = 행 누락. 자식 '기대'는 회사별 self-census(부모-present 분기 과반 present & 중앙값≥1억) → **회사유형이 아니라 회사별 실보고값 기준** — 손보사도 장수리스크(item30) 실보고하면 검출대상(DB손해 406억·코리안리 45억·삼성화재 20억 확인). 구조적 N/A·상시0(item32 LTC 등)만 자동제외. **PARTIAL**(자식 일부 present + 기대자식 결측 = 표 실재·행 누락)만 RED. 라이브 **14 RED** — 제안하신 KR0050 24.1Q/24.3Q/25.1Q(item34·35) 3건 정확히 발화. FULL_ABSENT even-Q 16건(2023.2Q 도입초 클러스터 의심)은 자동RED 대신 **원천확인 review(비차단)** 분리.

**사각 A → `_ratio_series_spikes` (YELLOW, 비차단):** item27(지급여력비율) 인접 2분기 '양쪽 모두'와 크게 벌어진 단일 분기. 부호역전 자체는 자본잠식사 정상 0선통과라 flag 안 함(양방 이탈만). 라이브 발화 0(parser 수정 후 clean) / 옛 KR0083 25.2Q +318 주입 시 정확 발화(self-test 확인). item27 중복행 dedup 포함.

발화한 14 RED + 16 review 백필은 **parser/kics inbox 신규 발주**: `inbox/parser/20260704T0745Z__validation__MULTI_MULTI__parent_child_census_gaps.md` (부수발견 2건 동봉: item27 중복행·세션중 JSON 재작성).

status: resolved (blind_spot 룰 구현 자기완결, auto_loop 아님).
