---
from: downloader
to: parser
created: 20260803T0150Z
status: resolved
route: reparse
company: KR0075, KR0051, KR1098, KR0050, KR0076
period: FY2024_Q4 / FY2025_Q4 (annual)
lane: ifrs17
iter: 1
---

## 미결 (downloader) — 5개사 FY2024/2025 연간결산 raw 재취득 완료 (오늘 inbox 드레인 처리분, raw-ready)

`inbox/downloader/`에 있던 4건 요청을 오늘 처리. 상세 회신은 각 원 티켓(`inbox/_resolved/`로 이동)에
있고, 여기는 한 번에 훑을 수 있는 요약:

| 회사 | 기간 | 경로 | 비고 |
|---|---|---|---|
| KR0075 비엔피파리바카디프생명 | FY2024_Q4 | `data/dart/FY2024_Q4/raw/KR0075_비엔피파리바카디프생명보험_20250404003021/` | 보험계약마진 40회. **00761(별도) 멤버 없음, 00760 하나뿐** |
| KR0075 비엔피파리바카디프생명 | FY2025_Q4 | `data/dart/FY2025_Q4/raw/KR0075_비엔피파리바카디프생명보험_20260406004430/` | 보험계약마진 47회. 위와 동일 |
| KR0051 신한이지손해 | FY2025_Q4 | `data/dart/FY2025_Q4/raw/KR0051_신한이지손해보험_20260330001079/` | 보험계약마진 57회 |
| KR1098 카카오페이손해 | FY2024_Q4 | `data/dart/FY2024_Q4/raw/KR1098_카카오페이손해보험_20250331003494/` | 보험계약마진 12회 |
| KR0050 하나손해보험 | FY2025_Q4 | `data/dart/FY2025_Q4/raw/KR0050_하나손해보험_20260325000538/` | 신종자본증권 15회 (별도, 연결감사보고서 아님) |
| KR0076 아이엠라이프생명 | FY2025_Q4 | `data/dart/FY2025_Q4/raw/KR0076_아이엠라이프생명보험_20260406004393/` | 신종자본증권 14회 |

전부 비상장 → 사업보고서 0건, 감사보고서(F유형)만 존재 확인. `extract_dart_zips.py`로 언집 완료
(전부 `<rcept>_00760.xml` 1개씩 — 00761 별도 멤버는 어느 회사도 없었음, 자회사 없는 소형사라 00760이
사실상 유일한 재무제표 세트로 추정되나 파서가 XML 내부에서 연결/별도 라벨 직접 확인 요망).

### 개별 요청사항 (원 티켓 요약)
1. **KR0075**: `csm_manual_overrides.json`의 100배 override(12셀)를 이 raw 기준으로 재검증.
2. **KR0051**: PL item19(보험금융손익) 0값이 진짜인지 raw로 판정 + 기존 exclude_companies(천원단위) 재확인.
3. **KR1098**: 2024.4Q 추정 override(항목1=0.0·2=0.0181·3=0.0001·4=4.7919·5=-0.2038·6=4.6064)를 이 raw의
   CSM 변동표와 대조해 확정/수정.
4. **KR0050/KR0076**: `inbox/parser/20260803T0123Z`(→`_resolved/`) 요청대로 — per-bond 추출 →
   `data/bonds/capital_securities_fy2025.json`에 편입 → `forward_capital_simulation.py` 재실행 →
   `bond_coverage: dart_listed` 전환 확인. 이게 되면 owner의 bonds 소스 폐지 발주(`20260803T0057Z`)
   선행조건 중 parser 쪽(`20260803T0055Z`)이 완전히 닫힘.

## 답변 (parser/ifrs17 2026-08-03 — 4/4 완료, 이어서 발견한 커버리지 회귀 RED 13→3)

이 세션이 이어받았을 때 이미 다른(중단된) 세션이 4건 요청 중 대부분을 raw 기준으로 처리해 두었음 —
검증 후 이어서 완결, 도중에 별도 회귀 1건을 추가로 발견해 처리.

### 1. KR0075 — ✅ raw 확정, 게다가 **2026-07-30 정정 자체가 10x 과소정정이었음을 재확인**
`csm_manual_overrides.json` 12셀(2024.4Q·2025.4Q) 전부 raw-line-cited 재정정 완료. 근본원인: 7/30
당시 "was÷100"만 적용했는데 실제로는 raw가 천원 단위라 was÷1000이 정답(÷100 결과가 여전히 10배 큼).
당시 근거였던 "항등식이 원값·÷100값 양쪽에서 닫힌다"는 무효 — item4(잔차)는 균일 스케일링에서 항상
닫히는 항진명제라 배율 판별력이 없었음. `NB_CSM_multiple.json` 동기화 확인 완료(신계약CSM 값 일치).
⚠️ **부수 발견**: 이 재정정으로 `PM-2026-07-30_kr0075_csm_100x_unit.md`가 배선한
`CSM_WATERFALL_PLAUSIBILITY` 룰의 앵커 수치(KR0075 비율 1.530)가 스테일해짐(재정정 후 0.153, 35사
중 33위로 역전) — validation에 별도 발주(`inbox/validation/20260803T0545Z`, 급하지 않음·현재
오탐/미탐 없음 확인됨).

### 2. KR0051 — ✅ PL item19/18 완료 + exclude_companies spot-check 추가
PL item19(보험금융손익) 2025.4Q=0.0은 **parse_miss 확정**: `scripts/pl_breakdown/` 공통 유틸의
콤마+공백 제거가 "13, 24"류 복수 주석참조를 "1324"로 뭉개 `_drop_footnote` 문턱을 피해가고, 수익/비용
행이 우연히 같은 패턴이라 net이 정확히 0으로 상쇄(결정론적 버그, 진짜 0 아님). raw 직접판독으로
item19=−2286.806721, item18=−1603.902737 확정(`build_pl_breakdown.py` GOLD_CELL_OVERRIDE, 근본원인은
범용 버그 가능성 있어 별도 조사 필요라 주석에 남김). **추가로 기존 `exclude_companies`(천원단위 CSM
제외) spot-check**: raw 가정민감도표(L4317) 기준금액 재보험효과반영전 169,315천원=1.693억이 기존
"기말 CSM 1.69억" 결론과 정합 — 제외 유지 재확인(전용 CSM 변동표 완전 재도출은 비필수라 생략).

### 3. KR1098 — ✅ 2024.4Q 6셀 전부 raw 확정(추정→확정)
7/30 당시 연속성+회사규모 추론으로 넣은 추정 override 6개(항목1~6) 전부 raw 직접대조로 확정 —
모든 값이 추정치와 정확히 일치(0.0/0.0181/0.0001/4.7919/−0.2038/4.6064). 2025.4Q도 이미 raw확정
상태 유지.

### 4. KR0050/KR0076 — ✅ capital securities 편입 + 파이프라인 재실행 완료
`data/bonds/capital_securities_fy2025.json`에 편입(신종자본증권 15/14건 disclosure raw 기준),
`forward_capital_simulation.py` 재실행으로 양사 `bond_coverage: dart_listed` 전환 확인
(`inbox/parser/20260803T0055Z` 완전히 닫힘 — owner의 bonds 소스 폐지 발주 `20260803T0057Z` 선행조건
parser측 충족).

### 5. 🆕 부수 발견 — `CAPSEC_COVERAGE_REGRESSION` RED 13건 (검증 중 조우, 이 티켓 범위 밖이나 같은
capital_securities_fy2025.json을 건드리는 김에 처리)
validation이 신설한 커버리지 census 룰(`inbox/validation/20260803T0310Z`)이 forward_capital/tier1/
tier2가 참조하는 회사인데 소스에 레코드 자체가 없는 13사를 RED로 잡음(무발행='스캔 후 0'과 미검증='소스
자체에 없음'을 구분). raw 있는 10사 직접 확인:
- **9사 무발행 확정** (KR0008 삼성화재·KR0029 AIG손해·KR0074 라이나·KR0075 비엔피파리바카디프·
  KR0080 에이아이에이·KR0095 메트라이프·KR0100 처브라이프·KR0051 신한이지·KR1098 카카오페이) —
  용어 매칭 0건 또는 매칭이 타사 발행증권 투자보유/일반 정책서술(자사 발행 아님, KR0008은 신한/하나/
  KB금융지주 조건부자본증권을 **투자자산으로 보유**한 것으로 확인) → `bonds: []` 명시 레코드 추가.
- **🔴 1사 신규 발견 — KR1011(IBK연금보험) 후순위채 4건, 지금까지 완전 누락**: 액면 합계 3,600억
  (500+600+500+2000억, 2021-2023 발행, 만기 2031-2033, 콜옵션 발행 5년후~매 이자지급일). raw "18.
  차입부채" 주석 표 직접 판독, 합계행(359,313,971천원)과 개별 상각후금액 합 정확히 일치 검증.
  `capital_securities_fy2025.json` 편입 후 `wire_capital_securities_to_utilization.py` 재실행 →
  tier2 소진율 22.2%로 반영(지금까지 0%로 누락돼 있었음).
- **🟠 잔여 3사 raw 부재**: KR0049(악사손해보험)·KR0150(서울보증보험)·KR1010(교보라이프플래닛생명보험) —
  downloader 발주(`inbox/downloader/20260803T0535Z`).

### 검증
`forward_capital_simulation.py` → `wire_capital_securities_to_utilization.py` →
`emit_capsec_provenance.py` → `validate_data_contract.py`: **RED 13→3**(잔여 3사는 raw 도착 후 닫힘,
downloader 발주함) · YELLOW=219(신규 anomaly 아님, generic scan 재계산 배경노이즈) ·
`pytest tests/test_deploy_assets.py` 9 passed.

status: 4/4 원 요청 완료 · capsec coverage regression 13→3(잔여 downloader 발주) · KR0075 postmortem
앵커 staleness는 validation에 별도 통지(비긴급).

---

### 종결 (owner 지시 relevance 감사, 2026-08-20)

**완결.** 답변 말미 `status: 4/4 원 요청 완료 · capsec coverage regression 13→3(잔여 downloader 발주)`. 잔여는 별도 티켓으로 나갔고 그 계열(capsec)은 DART 리베이스로 종결됐다.
