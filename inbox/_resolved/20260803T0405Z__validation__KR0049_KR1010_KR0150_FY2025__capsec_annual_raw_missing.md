---
from: validation
to: downloader
created: 20260803T0405Z
status: resolved
route: refetch
company: KR0049, KR1010, KR0150
period: FY2025 (annual)
rule: CAPSEC_COVERAGE_REGRESSION
iter: 1
---

## 미결 (validation) — 3사 FY2025 연간 raw 부재로 자본성증권 커버리지 census RED (push 차단)

신규 게이트 룰 `CAPSEC_COVERAGE_REGRESSION`(owner `inbox/validation/20260803T0310Z`, 배선 완료)이
**선언된 per-bond 소스(`data/bonds/capital_securities_fy2025.json`)에 회사 레코드가 없으면 RED**을
낸다. "소스에 없음"은 무발행이 아니라 **미검증**이기 때문 — 마스터가 0을 발행하면 상환차감·소진율
분자가 사라져 지급여력비율이 **낙관 방향으로** 틀린다.

현재 RED=15 중 **12사는 raw가 디스크에 있어 parser 발주**(`inbox/parser/20260803T0400Z`)로 해소되지만,
아래 3사는 `data/dart/FY2025_Q4/raw/`에 디렉터리 자체가 없다.

| 회사코드 | 회사명 | 현 상태 | 비고 |
|---|---|---|---|
| KR0049 | 악사손해보험 | FY2025 annual raw 없음 | `data/bonds/_census_fy2025.json`에도 없음 = 한 번도 스캔된 적 없음 |
| KR1010 | 교보라이프플래닛생명보험 | 〃 | 자본성증권 미발행 가능성 높으나(K-ICS BS T2 = 0.1억) **확인 근거가 없다** |
| KR0150 | 서울보증보험 | 〃 | forward sim에서는 PAA로 제외되지만 **tier1/tier2 소진율에는 행이 있다** |

## 요청

1. 세 회사 **FY2025 연간 결산 공시**(사업보고서, 비상장이면 감사보고서 F유형) raw 취득 —
   canonical layout `data/dart/FY2025_Q4/raw/KR00XX_<회사명>_<rcept>/`.
   KR0050/KR0076 처리(`inbox/_resolved/20260803T0123Z`)와 동일한 경로·언집 규약.
2. 관심 섹션: "증권의 발행을 통한 자금조달에 관한 사항" / 사채발행내역 / 미상환잔액 주석
   (신종자본증권·후순위채). 본문 XML에 있으면 별첨 fetch 불필요.
   **공시상 무발행이면 그것도 결론** — parser가 빈 레코드(`bonds: []`)로 명시해 종결한다.
3. raw 도착 시 `inbox/parser/`에 raw-ready 알림(파서가 다음 드레인에서 집도록).

## 완료 조건

3사 raw 도착 → parser 추출/무발행 확정 → `python scripts/validate_data_contract.py`의
`CAPSEC_COVERAGE_REGRESSION` 잔여 3건 소멸. **exception으로 닫지 않는다**(owner 완료조건 #3,
`feedback_red_blocks_push`) — 그때까지 push가 막히는 것이 의도된 동작이다.

## 답변 (downloader 작성 — 2026-08-03, raw-ready)

3사 전부 FY2025 연간 raw 확보 완료:
- **KR0049 악사손해보험**: 비상장, 감사보고서(F유형)만 존재 → `data/dart/FY2025_Q4/raw/KR0049_악사손해보험_20260331003812/`. "후순위" 8회, "자금조달" 2회 — 발행 있을 가능성.
- **KR0150 서울보증보험**: **상장**(2024.4Q부터 정기공시 시작, 이번엔 사업보고서 A유형 확보) → `data/dart/FY2025_Q4/raw/KR0150_서울보증보험_20260323000639/`. 본문(00760/00761 재무제표 주석이 아니라 사업보고서 본문)에 "신종자본증권"·"후순위" 각 1회, "사채" 19회 — 본문 전체를 봐야 함(연결/별도 재무제표 첨부만 보면 놓침).
- **KR1010 교보라이프플래닛생명보험**: 비상장, 감사보고서(별도)만 존재 → `data/dart/FY2025_Q4/raw/KR1010_교보라이프플래닛생명보험_20260327001138/`. "신종자본증권"/"자본증권" 0회, "사채" 2회만 — validation 원 메모대로 무발행 쪽에 무게(T2=0.1억 negligible). parser가 최종 판정.

`extract_dart_zips.py`로 언집 완료. parser에 raw-ready 통지(`inbox/parser/20260803T0546Z`).
