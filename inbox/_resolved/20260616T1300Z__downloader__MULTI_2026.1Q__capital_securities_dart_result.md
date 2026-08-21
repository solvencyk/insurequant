---
from: downloader
to: publishing
created: 20260616T1300Z
status: resolved
route: data_ready
company: KR0072,KR0104
period: 2026.1Q
rule: INFORCE_CAPITAL_SECURITIES_SOURCE
iter: 2
---

## 자본성증권 per-bond DART fetch 결과

연계: publishing `inbox/downloader/20260616T1200Z` → downloader 조사·취득 완료.

### 취득 완료 (2개사)

파일: `data/bonds/disclosure/2026q1_capital_securities.json`

**KDB생명 (KR0072)** — 신종자본증권 2건, 합계 2,410억:
| 채권 | 금액 | 발행일 | Call일 | 만기 |
|---|---|---|---|---|
| 케이디비생명보험 신종자본증권 2023 | 2,160억 | 2023-05-19 | 2028-05-19 | 2053-05-19 |
| 케이디비생명보험 신종자본증권 2024 | 250억 | 2024-12-26 | 2029-12-26 | 2054-12-26 |

BS 비교: 신종 2,403억 (≈DART 2,410억 ✓), 후순위 6,605억 (DART 없음 → 사모 추정)

**농협생명 (KR0104)** — 신종자본증권 2건, 합계 5,000억:
| 채권 | 금액 | 발행일 | Call일 | 만기 |
|---|---|---|---|---|
| 농협생명 신종자본증권 2022-09 | 2,500억 | 2022-09-28 | 2027-09-28 | 2052-09-28 |
| 농협생명 신종자본증권 2022-12 | 2,500억 | 2022-12-26 | 2027-12-26 | (영구채) |

BS 비교: 신종 0 (파서 누락 의심), 후순위 456억 (FSC 8,300억 vs BS 456억 → 파서 이슈)

### 취득 불가 — 사유별 정리

| 회사 | Face/BS(억) | 불가 사유 |
|---|---|---|
| 삼성생명 KR0069 | 0/77,578 | 사모채 — FSC·DART 어디에도 없음 |
| 악사손해 KR0049 | 0/33,945 | 외국계 모회사(AXA) 자본주입 구조 추정, 한국 공개 등록 없음 |
| KDB생명 후순위 KR0072 | 3,000/6,605 | DART B-type에 후순위 공시 없음 (사모) |
| 하나손해 KR0050 | 0/5,434 | DART·FSC 0건 |
| AIA KR0080 | 0/4,279 | 외국계, AIA 그룹 내 자본 |
| 삼성화재 KR0008 | 0/1,072 | DART B-type 없음 (소규모 사모) |
| 교보생명 KR0073 | 15,700/22,057 | DART 유일 공시 = 2023 해외 미발행 확인 |

### 중요 수정 사항 — "과다" 회사 재진단

publishing 발주의 "과다" 회사 중 **현대해상 KR0009는 FSC가 정확**:
- FSC outstanding 4건 모두 2024~2025 신규 발행 확인 (stale 아님)
  - 5,000억 (2024.06, call 2029.06) / 4,000억 (2024.11, call 2029.11)
  - 9,000억 (2024.12, call 2029.12) / 8,000억 (2025.03, call 2030.03) = 총 26,000억
- BS 3,766억 = **파서가 K-ICS 공시에서 subordinated_eok 오파싱**. FSC 쪽이 맞음.
- forward-sim은 FSC 26,000억 / call 2029~2030 기준으로 사용해야 함 (BS 값 아님).

농협생명도 동일 이슈: FSC 신종 5,000억 ≈ DART 5,000억 (일치), BS 신종 0 = 파서 누락.

### 권고

1. `data/bonds/disclosure/2026q1_capital_securities.json`의 KDB생명·농협생명 per-bond → forward_capital_simulation 보조 소스로 사용.
2. 현대해상·농협생명 후순위 BS 오파싱 → **parser(kics lane)에 신종/후순위 breakdown 재파싱 발주 필요**.
3. 삼성생명·악사·하나손해·AIA·삼성화재의 사모채 per-bond = 공개 소스 없음 → forward-sim에서 BS 총계(신종+후순위) 기준 단순 잔존만기 가정 처리 불가피.

## 답변 (publishing 2026-06-16)

인수 완료. 처리:

1. **KDB생명 신종(2,410억) — 사용 가능**: DART ≈ BS(2,403억) 일치, forward-sim 보조 소스 확인.
2. **현대해상(KR0009) 후순위 BS 3,766억 = 파서 오류** (FSC 26,000억이 정확) → parser(kics) 재파싱 발주 (`inbox/parser/20260616T15xxZ`).
3. **농협생명(KR0104) 신종 BS=0 = 파서 누락** (DART/FSC 5,000억) → parser(kics) 재파싱 발주 (동일).
4. 사모채 7사(삼성생명·악사·하나손해·AIA·삼성화재·KDB후순위·교보) = 공개 소스 없음 확인, forward-sim BS 총계 단순가정 유지.
5. **forward_capital_simulation 재실행**: parser(kics) KR0009/KR0104 BS 재파싱 완료 + data-contract gate RED=0 후 재실행 예정 (현재 게이트 BLOCKED).

---

### 종결 (owner 지시 relevance 감사, 2026-08-20)

**무효 — DART 리베이스로 소멸.** 잔여 항목(농협생명 신종 BS=0 재파싱, 사모채 7사 공개소스 부재, forward_capital 재실행)은 전부 FSC-Face 기반 산식 전제였다. 실측: tier1/tier2 둘 다 이제 `dart_bonds_fy2025_경과조치` 소스이고 100% 초과 0건. 같은 날 `20260616T0506Z`(T2 신뢰도)도 '화면에서 제거된 지표'로 종결했다.
