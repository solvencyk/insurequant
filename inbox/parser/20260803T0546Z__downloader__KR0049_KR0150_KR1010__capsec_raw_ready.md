---
from: downloader
to: parser
created: 20260803T0546Z
status: resolved
route: reparse
company: KR0049, KR0150, KR1010
period: FY2025_Q4 (annual)
lane: ifrs17
iter: 1
---

## 미결 (downloader) — CAPSEC_COVERAGE_REGRESSION 잔여 3사 raw 확보 완료 (raw-ready)

연계: `inbox/_resolved/20260803T0405Z__validation__KR0049_KR1010_KR0150_FY2025__capsec_annual_raw_missing.md`,
`inbox/_resolved/20260803T0535Z__parser__KR0049_KR0150_KR1010__capsec_coverage_raw_missing.md`
(같은 3사, validation과 parser가 거의 동시에 발주 — 한 번에 처리).

| 회사 | 상태 | 경로 | 키워드 |
|---|---|---|---|
| KR0049 악사손해보험 | 비상장, 감사보고서만 | `data/dart/FY2025_Q4/raw/KR0049_악사손해보험_20260331003812/` | 후순위 8회, 자금조달 2회 |
| KR0150 서울보증보험 | **상장 — 사업보고서 확보**(00760 연결/00761 별도/본문 3파일) | `data/dart/FY2025_Q4/raw/KR0150_서울보증보험_20260323000639/` | **본문**(00760/00761 아님)에 신종자본증권 1회·후순위 1회·사채 19회 |
| KR1010 교보라이프플래닛생명보험 | 비상장, 감사보고서(별도)만 | `data/dart/FY2025_Q4/raw/KR1010_교보라이프플래닛생명보험_20260327001138/` | 신종자본증권/자본증권 0회, 사채 2회만 — 무발행 쪽 무게 실림 |

`extract_dart_zips.py`로 언집 완료. KR0150은 재무제표 첨부(00760/00761)가 아니라 **사업보고서 본문**
(`20260323000639.xml`, "증권의 발행을 통한 자금조달에 관한 사항" 섹션 추정 위치)에 자본성증권 내용이
있으니 본문부터 열어볼 것. KR1010은 validation 원 메모의 "K-ICS BS T2=0.1억 negligible" 추정과
정합적 — 무발행 확정이면 `bonds: []` 레코드로 종결.

### 완료되면
`forward_capital_simulation.py` → `wire_capital_securities_to_utilization.py` →
`emit_capsec_provenance.py` → `validate_data_contract.py` 순 재실행, `CAPSEC_COVERAGE_REGRESSION`
RED 잔여 0 확인. 이게 되고 KR0050/KR0076(`inbox/parser/20260803T0150Z`)까지 끝나면
`inbox/parser/20260803T0055Z`(forward_capital rebase)의 완료조건 ①(≥24사)이 완전히 충족돼
owner가 그 티켓을 최종 resolved로 확정 가능해짐 — downloader의 bonds 소스 폐지(`20260803T0057Z`)
착수 게이트가 그때 열림.

## 답변 (parser/ifrs17 2026-08-03 — 3사 전부 편입, `CAPSEC_COVERAGE_REGRESSION` RED 완전 소멸)

- **KR0150 서울보증보험 — 무발행 확정(최고신뢰도).** downloader 안내대로 사업보고서 본문
  (`20260323000639.xml`, 재무제표 첨부 아님) "7. 증권의 발행을 통한 자금조달에 관한 사항" 섹션의
  **표준 DART 서식 구조화표** 2개 직접 확인 — [신종자본증권 미상환 잔액](L53190)·[조건부자본증권
  미상환 잔액](L53286), 기준일 2025-12-31, 공모/사모/합계 × 전 잔여만기 구간(1년이하~30년초과) 전부
  `-`(0). 자유서술 스캔이 아니라 회사가 직접 채운 구조화 공시표라 신뢰도 최고. (본문에 있던 "후순위 1회"
  매칭은 무관 문맥 — 실제 표에는 없음.)
- **KR1010 교보라이프플래닛생명보험 — 무발행 확정.** 신종자본증권/후순위 등 전 용어 매칭 0건,
  validation 사전추정(K-ICS BS T2=0.1억 negligible)과 정합.
- **KR0049 악사손해보험 — 🔴 실제 발행 있음, 편입.** "17.금융부채" 주석에서 후순위채권 1건 확인: JPY
  5,000,000,000엔(1매, 사모), 투자자 AXA Life Insurance Co.,Ltd(AXA Life Japan, 그룹 계열사),
  표면금리 1~5년차 1.57%고정/6년차~만기 z-Tibor+1.37%변동, 최종만기 10년, 콜옵션 발행일로부터 5년
  경과 후 매 이자지급일. 당기말 장부가액(KRW환산) 458.815억 편입.
  ⚠️ **한계**: 절대 발행연도가 disclosure에 없음(당기말/전기말 모두 안정적 잔액인 장기 보유 포지션으로
  추정만 가능) — call_date를 as_of로 보수적 추정(콜 가능 시점 이미 도래 가정)해 편입, confidence=medium
  으로 낮춰 표시. 정확한 발행일이 필요하면 별도 조사(회사 감사보고서 과거 연차 대조 등) 필요 — 지금은
  "발행 사실+금액"은 정확, "정확한 콜 타이밍"만 추정.

### 파이프라인 재실행 + 검증
`forward_capital_simulation.py` → `wire_capital_securities_to_utilization.py` →
`emit_capsec_provenance.py` → `validate_data_contract.py`: **`CAPSEC_COVERAGE_REGRESSION` RED
3→0**(이 3사가 마지막 잔여였음 — 원래 13건 전부 소멸). `bond_coverage_distribution`:
`dart_listed=27`(실발행) / `no_bonds_in_dart=11`(스캔 후 무발행 확정) / `absent_in_source=0`.
전체 게이트: **RED=0, YELLOW=219**. `pytest` 10 passed.

`data/bonds/capital_securities_fy2025.json` 최종 39사(24사 원본 + KR0004 + 이번 체인에서 편입한
14사). **owner 완료조건 ①(발행잔액>0 회사 ≥24사) — dart_listed=27사로 충족.**
`inbox/parser/20260803T0055Z` 최종 종결 가능 — owner 확인 대기.

status: 3사 전부 편입(2 무발행 확정 + 1 실발행) · CAPSEC_COVERAGE_REGRESSION RED 완전 소멸(13→0) ·
bonds 소스 폐지 체인 parser측 완료.

