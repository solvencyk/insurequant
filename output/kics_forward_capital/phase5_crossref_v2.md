# Phase 5 Cross-Reference v2: Bond DB vs K-ICS BS 자본성증권 (post alias-fix)

Generated: 2026-05-25
Source: data/bonds/normalized/20260525T050759Z + templates/{tier1,tier2}_utilization_latest.json

## Update vs v1

FSC alias-loop fix (`scripts/ingest_fsc_bonds.py`): query ALL aliases per insurer instead of
just `search_names[0]`. Insurers covered grew 19 → **24** (+5: KR0010 KB / KR0011 DB /
KR0032 NH농협손보 / KR0072 KDB생명 / KR1098 카카오페이).

Forward sim re-run with new data — new findings:
- **KR0032 NH농협손보**: baseline 130.97% → 2030 **84.21%** (100% 하회 진입)
- **KR0072 KDB생명**: baseline 70.99% (이미 100% 미만) → 2030 48.9%
- KR1098 카카오페이: 2030 -704% (baseline 작은 회사 노이즈; cap 필요)

## Method (same as v1)

For each insurer, sum bond face values by status/tier and compare 'outstanding' vs K-ICS BS.

## Net findings

### T1 hybrid (5 alerts in 24 covered)

| Code | Insurer | Bond out | K-ICS T1 | Diff | Called | Likely cause |
|------|---------|---------:|---------:|-----:|-------:|--------------|
| KR0011 | DB손해 | 13,090 | 8,650 | +51% | 0 | BS에 한도 차감? (face > 인정금액) |
| KR0032 | NH농협손보 | 0 | 4,500 | -100% | 0 | FSC에 신종 누락 (T2만 잡힘) |
| KR0068 | 한화생명 | 17,000 | 30,685 | -45% | 10,000 | 신종 13,685억 FSC 누락 |
| KR0072 | KDB생명 | 0 | 2,403 | -100% | 700 | T1 신종 FSC 누락 |
| KR0104 | 농협생명 | 0 | 4,999 | -100% | 0 | T1 신종 FSC 누락 |

→ **Forward sim impact (T1)**: 한화생명/KDB생명/농협생명 시나리오는 누락 신종을 미반영 →
   "콜 시 자본비율 하락" 시나리오가 underestimate (실제 더 떨어질 가능성).

### T2 subordinated (16 alerts in 24 covered)

T2는 BS = 시가평가 후 인정금액, bond = face value → ±30-50% 노이즈 정상.
의미 있는 outlier만 발췌:

**Definitely-called (BS << Face)**:
- KR0001 메리츠화재: face 15,910 vs BS 100 → 후순위채 거의 전부 만기/콜 완료
- KR0002 한화손해: face 11,000 vs BS 126 → 동일
- KR0010 KB: face 8,860 vs BS 71,809 (BS가 더 큼 — FSC가 KB T2 일부 누락)

**Data gap (FSC 누락)**:
- KR0050 하나손해, KR0097 하나생명, KR1000 코리안리 — T2 bond=0이지만 K-ICS엔 값
- KR0079 미래에셋, KR0087 동양, KR0094 신한라이프 — FSC 누락 비율 50%+

## Remaining 15 missing insurers

After alias fix still uncovered (likely no FSC bond DB entry):
- 외국계: KR0029 AIG, KR0049 악사, KR0074 라이나, KR0075 BNP, KR0080 AIA, KR0095 메트라이프, KR0100 처브
- 디지털/신생: KR0051 신한이지, KR1059 캐롯, KR1010 교보라이프플래닛, KR0099 KB라이프
- 정부/특수: KR0150 서울보증, KR1011 IBK연금
- 대형사 (의심스러움): **KR0008 삼성화재, KR0069 삼성생명** — 둘 다 발행 이력 있을 텐데 FSC API에 안 잡힘. 추가 alias 시도 (예: "삼성생명보험주식회사") 필요

## Verdict on 53→80 'called' assumptions

- T1: 5y Call 가정 대체로 합리적. 1-2개 보수 가능.
- T2: BS proxy 노이즈로 face-level 검증 불가. 메리츠/한화손해 케이스 보면 'called' 추가 행사 정상.
- 주요 이슈는 여전히 **FSC DB 갭** (15사 미수집). KR0008/KR0069 특별 follow-up 필요.

## Follow-up

1. **(high)** KR0008 삼성화재 + KR0069 삼성생명 alias 추가 시도 ("삼성생명보험", "삼성생명보험주식회사", etc.) — 데이터 누락이 가장 의외인 케이스
2. **(medium)** Forward sim에 confidence flag 추가 (BS/Bond gap >30% 시 "low_confidence" 표시)
3. **(low)** KR1098 카카오페이 같은 small-baseline 케이스 cap (음수 ratio 방지)
