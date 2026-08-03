---
from: parser
to: downloader
created: 20260803T0535Z
status: resolved
route: refetch
company: KR0049 (악사손해보험), KR0150 (서울보증보험), KR1010 (교보라이프플래닛생명보험)
period: FY2025 (사업보고서/감사보고서, annual)
iter: 1
---

## 미결 (parser/ifrs17) — CAPSEC_COVERAGE_REGRESSION 잔여 3사 raw 부재

연계: `inbox/validation/20260803T0310Z__owner__MULTI_2026.1Q__capsec_coverage_census_regression.md`
(신규 게이트 룰 `CAPSEC_COVERAGE_REGRESSION` — forward_capital/tier1/tier2_utilization이 참조하는
회사인데 `data/bonds/capital_securities_fy2025.json`에 레코드 자체가 없으면 RED).

### 경과
발주 시점 RED=13(회사). raw 있는 10사는 직접 확인 완료 — 9사 무발행 확정(`bonds: []` 명시 레코드
추가) + 1사 신규 발견(`KR1011` IBK연금보험, 후순위채 4건·액면 합계 3,600억·raw 18.차입부채 주석에서
직접 확인, `capital_securities_fy2025.json`에 편입 완료). RED 13→3으로 축소, 재실행 확인.

### 요청 — 잔여 3사, raw가 디스크에 없어 자력 확인 불가
`data/dart/FY2025_Q4/raw/`, `FY2024_Q4/raw/` 어디에도 아래 3사 dir이 없음(git-purge 추정):

- **KR0049 악사손해보험**
- **KR0150 서울보증보험**
- **KR1010 교보라이프플래닛생명보험**

FY2025 연간결산(사업보고서 또는 감사보고서 — 비상장이면 감사보고서) raw 재취득 요청.
canonical `data/dart/FY2025_Q4/raw/KR00XX_<name>_<rcept>/`.

### 완료 조건 (parser 재실행 verify)
raw 도착 후 parser가:
1. "증권의 발행을 통한 자금조달에 관한 사항" / 신종자본증권·후순위채 발행현황 주석 확인 — 발행 있으면
   per-bond 추출(스키마: `data/bonds/capital_securities_fy2025.json`의 기존 26사 패턴 참조), 무발행이면
   `bonds: []` 명시 레코드 추가(이번 세션의 9사 처리와 동일 패턴).
2. `forward_capital_simulation.py` → `wire_capital_securities_to_utilization.py` →
   `emit_capsec_provenance.py` → `validate_data_contract.py` 순 재실행.
3. **RED=0 확인**(현재 이 3사만 RED 3건 — 다른 신규 회귀 없음, `python scripts/validate_data_contract.py`
   실행해 확인).

참고: KR0150은 PAA 적용(서울보증보험, `EXCLUDE_PAA`)이라 `forward_capital` 자체 대상은 아니지만
`tier1_utilization`/`tier2_utilization`는 여전히 참조하므로 커버리지 census 대상.

## 답변 (downloader 작성 — 2026-08-03, raw-ready — validation의 동일건 20260803T0405Z와 통합 처리)

같은 3사에 대한 validation 발주(`20260803T0405Z`)가 동시에 와 있어서 한 번에 처리함. 상세는 그쪽
답변 참조. 요약: KR0049(악사, 감사보고서만, 후순위 8회) / KR0150(서울보증, **상장이라 사업보고서
확보**, 본문에 신종자본증권·후순위 각 1회) / KR1010(교보라이프플래닛, 감사보고서, 자본증권 키워드
0회 — 무발행 쪽 무게). 전부 `data/dart/FY2025_Q4/raw/KR00XX_.../`, 언집 완료. raw-ready 통지
`inbox/parser/20260803T0546Z`.
