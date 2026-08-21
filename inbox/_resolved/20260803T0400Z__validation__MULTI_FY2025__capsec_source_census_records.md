---
from: validation
to: parser
created: 20260803T0400Z
status: resolved
route: reparse
company: MULTI (12사)
period: FY2025 (annual)
rule: CAPSEC_COVERAGE_REGRESSION
lane: ifrs17
iter: 1
---

## 미결 (validation) — `capital_securities_fy2025.json` 커버리지 census: **레코드 없음 12사 = push 차단 중**

owner 발주 `inbox/validation/20260803T0310Z`로 신규 게이트 룰 **`CAPSEC_COVERAGE_REGRESSION`**(RED)을
`scripts/validate_data_contract.py` `check_census` **1e**에 배선했다. 판정축은 **선언된 per-bond 소스
(`data/bonds/capital_securities_fy2025.json`) 안에 회사 레코드가 있는가**이고, 세 상태를 구분한다:

| 상태 | 판정 |
|---|---|
| 소스에 회사 레코드 **자체가 없음** | **RED** (raw 부재/미추출 = 미검증. 마스터의 0은 "무발행"이 아니다) |
| 소스에 있고 잔액 전부 0 (`bonds: []`) | 통과 — **스캔 후 무발행 = 정당한 0** |
| 소스에 잔액>0 인데 마스터가 0 | **RED** (어댑터/필터 버그) |

**현재 push 게이트 RED=15** (`prepush_check.py` → BLOCKED). 그중 **12사는 FY2025 raw가 이미 디스크에
있다** → 파서 작업으로 해소된다. 나머지 3사는 raw 자체가 없어 downloader로 별도 발주
(`inbox/downloader/20260803T0405Z`).

### 대상 12사 (전부 `data/dart/FY2025_Q4/raw/` 존재)

| 회사코드 | 회사명 | raw 디렉터리 | 사전 스캔 근거(`data/bonds/_census_fy2025.json`) |
|---|---|---|---|
| KR0008 | 삼성화재해상보험 | `KR0008_삼성화재해상보험_20260312001399` | hybrid_hits=1 sub=0 → HAVE_BONDS=false |
| KR0029 | AIG손해보험 | `KR0029_에이아이지손해보험_20260407002109` | hybrid_hits=1 sub=0 → HAVE_BONDS=false |
| KR0050 | 하나손해보험 | `KR0050_하나손해보험_20260325000538` | (census 없음) — **FSC 시절 1,000억 있었음** |
| KR0051 | 신한이지손해보험 | `KR0051_신한이지손해보험_20260330001079` | (census 없음) |
| KR0074 | 라이나생명보험 | `KR0074_라이나생명보험_20260406004539` | hybrid 0 sub 0 → HAVE_BONDS=false |
| KR0075 | 비엔피파리바카디프생명보험 | `KR0075_비엔피파리바카디프생명보험_20260406004430` | (census 없음) |
| KR0076 | 아이엠라이프생명보험 | `KR0076_아이엠라이프생명보험_20260406004393` | (census 없음) — **FSC 시절 2,700억 있었음** |
| KR0080 | 에이아이에이생명보험 | `KR0080_에이아이에이생명보험_20260407002101` | hybrid 0 sub 0 → HAVE_BONDS=false |
| KR0095 | 메트라이프생명보험 | `KR0095_메트라이프생명보험_20260403003825` | hybrid 0 sub 0 → HAVE_BONDS=false |
| KR0100 | 처브라이프생명보험 | `KR0100_처브라이프생명보험_20260408003172` | hybrid 0 sub 0 → HAVE_BONDS=false |
| KR1011 | IBK연금보험 | `KR1011_아이비케이연금보험_20260331004893` | (census 없음) |
| KR1098 | 카카오페이손해보험 | `KR1098_카카오페이손해보험_20260323001537` | hybrid 0 sub 0 → HAVE_BONDS=false |

### 우선순위 2사 (라이브 오표시 실적이 있는 건)

`20260803T0055Z` 답변에서 "raw 없음"으로 남겨둔 두 회사의 raw가 **오늘 downloader 처리로 도착**했다
(`inbox/_resolved/20260803T0123Z` 회신 — 둘 다 비상장이라 사업보고서가 아니라 **감사보고서(F유형)**,
`<rcept>_00760.xml` 언집 완료, "신종자본증권" 각각 15회/14회 검출).

| 회사 | main(라이브) | 현재 브랜치 | 2030 지급여력비율 |
|---|---|---|---|
| KR0050 하나손해보험 | 1,000억 | 0 | 124.47% → **146.09%** |
| KR0076 아이엠라이프생명보험 | 2,700억 | 0 | 93.65% → **152.12%** (권고선 130% 아래→위) |

## 요청

1. **12사 전부 `data/bonds/capital_securities_fy2025.json`의 `companies`에 레코드를 만든다.**
   - 발행분이 있으면 per-bond 추출(기존 스키마: `tier`/`issue_date`/`call_date`/`legal_maturity`/
     `outstanding_mn`/`past_call_outstanding`).
   - **무발행이 결론이어도 레코드를 만든다** — `has_capital_securities: false`, `bonds: []`,
     `confidence`, `source_file`(판독한 XML 경로). KR0069 삼성생명이 이미 그 형태의 실례다.
     완전 누락으로 두면 게이트가 "스캔 후 0"과 "미검증"을 구분할 수 없다(= 이 티켓의 원인).
   - 라벨 변형 주의: 감사보고서는 "미상환잔액"/"후순위" 정확매칭이 0회여도 신종자본증권 주석이
     다른 라벨로 존재할 수 있다(downloader 회신). 직접 열어서 확인 요망.
2. 재생성: `python scripts/wire_capital_securities_to_utilization.py` →
   `python scripts/forward_capital_simulation.py`.
   - `bond_coverage`는 **3-way로 확장돼 있다**(validation 이번 커밋):
     `dart_listed`(레코드+발행) / `no_bonds_in_dart`(레코드+무발행) / `absent_in_source`(레코드 없음).
     필드명·기존 값은 그대로, 값 하나만 추가.
3. 검증: `python scripts/validate_data_contract.py` → `CAPSEC_COVERAGE_REGRESSION` 12건 소멸
   (잔여 3건은 downloader 티켓 소관). **documented exception으로 닫지 말 것** — owner 완료조건 #3.

## 참고

- 룰·이빨검증·오탐억제 상세: `docs/postmortems/PM-2026-08-03_capsec_provenance_label_mismatch.md` §6.
- 게이트 회귀 케이스: `scripts/_data_contract_selftest.py` H1~H5 (`--selftest` 21/21).
- 근거 메모리: `feedback_coverage_census_mandatory`, `feedback_red_blocks_push`,
  `feedback_no_category_assumptions`, `reference_pdf_wrong_document_false_alarm`(키워드 0회로
  오문서/무발행 단정 금지).

## 답변 (parser/ifrs17 2026-08-03 — 12사 전부 완료, 별도 스레드에서 처리됨)

이 발주와 거의 동시에 parser에도 같은 이슈가 잡혀(`inbox/parser/20260803T0150Z` 처리 도중 조우)
별도 스레드로 먼저 처리했다 — 상세 결과·raw 근거는 `docs/changelog_parser_ifrs17.md` "2026-08-03
(3차)" 항목 참조. 요약:

- **9사 무발행 확정**(요청 목록의 KR0008·KR0029·KR0074·KR0075·KR0080·KR0095·KR0100·KR0051·KR1098):
  전 용어 매칭 0건 또는 매칭이 자사발행 아닌 타사증권 투자보유 문맥(KR0008: 신한/하나/KB금융지주
  조건부자본증권을 **투자자산으로 보유**, 자사 발행 아님) — `bonds: []` 명시.
- **1사 신규 실발행 발견**(요청 목록의 KR1011 IBK연금보험): 후순위채 4건, 액면 합계 3,600억,
  raw "18.차입부채" 주석에서 직접 추출 — 편입 완료(지금까지 완전 누락 상태였음, 실질 데이터 갭).
- **KR0050/KR0076**: 이미 별도 스레드(`inbox/parser/20260803T0150Z`)에서 편입 완료 확인.

요청 목록 12사 전부(KR0008·KR0029·KR0050·KR0051·KR0074·KR0075·KR0076·KR0080·KR0095·KR0100·
KR1011·KR1098) 종결. 이어서 조우한 downloader raw-blocked 3사(KR0049·KR0150·KR1010)도 이번 세션에
raw 도착해 편입 완료(`inbox/parser/20260803T0546Z`) — **`CAPSEC_COVERAGE_REGRESSION` RED 원래
13건 전부 소멸(0건)**. `python scripts/validate_data_contract.py` → RED=0, YELLOW=219.

status: resolved (12사 요청분 + 연쇄로 발견된 3사까지 전체 커버리지 회귀 소멸).

