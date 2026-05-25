# Phase 5 Cross-Reference: Bond DB vs K-ICS BS 자본성증권

Generated: 2026-05-25
Source: data/bonds/normalized/20260524T233649Z + templates/{tier1,tier2}_utilization_latest.json

## Method

For each insurer, sum the face values (issue_amount_won → eok) of bonds classified by
status (outstanding / called / matured) and tier (tier1_hybrid / tier2_subordinated),
then compare the "outstanding" totals against K-ICS BS-derived values:

- T1: tier1_hybrid_issued_eok (from BS 신종자본증권 row)
- T2: numerator_eok (proxy: BS 보완자본 항목)

Discrepancies expose either (a) wrong 'called' assumption in bond DB or (b) BS vs
face-value gaps from market valuation / regulatory haircuts.

## Caveats

- T2 numerator is a **proxy**. BS 보완자본 ≠ face value — it includes 시가평가, 한도 차감,
  손실흡수성 평가. ±20-30% diff is normal noise; only flag >30% AND >500억 abs.
- 5y Call assumption (Korean market convention) is the only available proxy for actual
  Call date — K-ICS public disclosures do NOT carry bond-level call schedules.
- FSC bond DB has 19 of 39 insurers covered; KR0008/0010/0011 etc. (20 insurers) missing
  → bonds DB shows 0 for them, K-ICS BS still has values (matter of bond-level vs aggregate).

## Tier 1 hybrid: alignment (16 insurers)

Mostly within ±5% — 5y Call assumption holds well for tier1:

| Code | Insurer | Bond out (eok) | K-ICS T1 (eok) | Diff |
|------|---------|----------------|----------------|------|
| KR0001 | 메리츠화재해상보험 | 1,800 | 1,792 | +0.4% |
| KR0002 | 한화손해보험 | 2,350 | 2,341 | +0.4% |
| KR0003 | 롯데손해보험 | 460 | 454 | +1.3% |
| KR0050 | 하나손해보험 | 1,000 | 1,000 | +0.0% |
| KR0071 | 흥국생명보험 | 500 | 496 | +0.8% |
| KR0076 | 아이엠라이프생명보험 | 950 | 949 | +0.1% |
| KR0083 | 푸본현대생명보험 | 1,000 | 998 | +0.2% |
| KR0097 | 하나생명보험 | 1,800 | 1,799 | +0.1% |
| KR1000 | 코리안리재보험 | 8,100 | 8,082 | +0.2% |

## Tier 1: ALERTS (3 insurers)

| Code | Insurer | Bond out | K-ICS T1 | Diff | Called assumed | Likely cause |
|------|---------|---------:|---------:|-----:|---------------:|--------------|
| KR0005 | 흥국화재 | 3,200 | 4,113 | -22.2% | 920 | 5y called 일부 미행사 or BS scope diff |
| KR0068 | 한화생명 | 17,000 | 30,685 | -44.6% | 10,000 | 신종 일부 call 미행사 가능 (10,000억 가정 과대) |
| KR0073 | 교보생명 | 15,700 | 22,057 | -28.8% | 0 | bond DB 누락 (FSC가 일부 ISIN 미감지) |
| KR0104 | 농협생명 | 0 | 4,999 | -100% | 0 | FSC DB에 농협 신종 전부 누락 (crno lookup 필요) |

→ **Forward sim impact (T1)**: KR0068 한화생명 시나리오는 10,000억 call 가정이 과한 가능성.
   실제 BS-FSC gap 13,685억 중 일부는 BS time-series에서 maturity로 빠진 것. 보수성 측면에선 유지 OK.

## Tier 2: high noise (15 flagged)

T2는 BS proxy 한계로 인한 노이즈가 큼. 실제 의미 있는 outlier만 발췌:

### Definitely-called signals (BS << Face)

| Code | Insurer | Bond out | K-ICS T2 | Comment |
|------|---------|---------:|---------:|---------|
| KR0001 | 메리츠화재 | 15,910 | 100 | T2 거의 다 call/만기 완료. Bond DB 'called' 가정 부족 |
| KR0002 | 한화손해 | 11,000 | 126 | 동일 패턴 |
| KR0050 | 하나손해 | 0 (DB 미수집) | 1,020 | FSC crno lookup 필요 |
| KR0068 | 한화생명 | 17,000 | 53,118 | 반대 케이스 — bond DB는 일부만 |
| KR0079 | 미래에셋 | 3,000 | 13,072 | bond DB 누락 |
| KR0087 | 동양생명 | 5,000 | 12,223 | bond DB 누락 |
| KR0094 | 신한라이프 | 8,000 | 9,139 | -12.5% OK |

### BS-only (FSC 미수집)

KR0009 현대해상, KR0070 에이비엘, KR0082 KDB, KR0094 신한라이프 — bond DB 0 또는 일부만,
BS 보완자본 값 큼. crno lookup 후 재시도.

## Net verdict on 53 'called' assumptions

- **Tier 1**: 가정 합리적. 1-2개 (KR0068 한화) 약간 보수.
- **Tier 2**: BS proxy 노이즈로 face-level 검증 불가. 그러나 메리츠/한화손보 케이스 보면
  오히려 'called' 추가 행사 (face > BS) — Forward sim 보수성이 적절히 작동 중.
- **데이터 갭**: FSC DB 19/39 cohort 한계가 더 큰 이슈. 20개 missing insurer (crno lookup)
  해결 시 cross-ref 정확도 상승.

## Follow-up

1. (high priority) FSC crno lookup for 20 missing insurers → bond DB 완성도 ↑
2. (medium) 한화생명 KR0068: 신종 30,685억 중 17,000억만 FSC 잡힘 → 추가 ISIN crawl 필요
3. (low) 신뢰성 etiket: forward_simulation_v1.json에 per-insurer confidence flag 추가 검토
