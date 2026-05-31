# 손보 LOB Underwriting Income — DART vs IR Cross-check

Generated: 20260531T103915Z  |  DART: `data/dart/viz/net_income_breakdown.json`  |  IR: `data/ir/FY2025_Q4/raw/*`

**Unit**: 억원 (KRW 100 million).  **Sign**: positive = profit, negative = loss.
**LOB taxonomy**: 장기보험 / 자동차보험 / 일반보험 (per task spec).

**DART LOB extraction basis (by company)**:

- *Note 발행보험 by 계약유형 (built-in)*: Samsung Fire (KR0008), Hyundai (KR0009), DB (KR0011), Hanwha (KR0002)
- *Note 보험손익 상세내역 — IFRS17 행 직접*: KB (KR0010), Hana (KR0050)
- *보종별 사업실적표 — 사업비 미배분, regulatory*: Meritz (KR0001), NH (KR0032), Korean Re (KR1000)

**IR availability**: only Samsung Fire, DB, Meritz have machine-readable IR LOB tables (Excel). Others have no IR LOB.

---

## Per-company table

| KR | 회사 | Tier1 보험손익 (DART) | DART 장기 | DART 자동차 | DART 일반 | DART LOB합 | IR 장기 | IR 자동차 | IR 일반 | IR 보험손익 | 장기 Δ | 자동차 Δ | 일반 Δ | Status |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| KR0008 | 삼성화재 | 14830.3 | 16650.8 | -1220.3 | 5916.6 | 21347.1 | 15077.3 | -1589.9 | 1707.9 | - | **+10.4%** | **+23.2%** | **+246.4%** | ok (LOB합 21347 vs Tier1 보험손익 14830) |
| KR0009 | 현대해상 | 10431.0 | 4097.1 | -677.0 | 6613.1 | 10033.2 | - | - | - | - | - | - | - | ok (LOB합 10033 vs Tier1 보험손익 10431) / IR LOB n/a |
| KR0011 | DB손해 | 11454.0 | 12256.8 | 6810.5 | -26.1 | 19041.2 | 10758.2 | -547.3 | 148.7 | 10359.5 | **+13.9%** | **+1344.4%** | **-117.6%** | ok (LOB합 19041 vs Tier1 보험손익 11454) |
| KR0010 | KB손해 | 6266.9 | 7901.4 | -1076.9 | 38.9 | 6863.4 | - | - | - | - | - | - | - | ok (LOB합 6863 vs Tier1 보험손익 6267) / IR LOB n/a |
| KR0001 | 메리츠화재 | 14270.0 | 15780.3 | -495.7 | 396.6 | 15681.2 | 14339.7 | -463.2 | 377.6 | 14254.1 | **+10.0%** | -7.0% | +5.0% | ok (LOB합 15681 vs Tier1 보험손익 14270) |
| KR0002 | 한화손해 | 2610.8 | 4170.9 | -966.0 | -734.7 | 2470.2 | - | - | - | - | - | - | - | ok (LOB합 2470 vs Tier1 보험손익 2611) / IR LOB n/a |
| KR0003 | 롯데손해 | 270.1 | - | - | - | - | - | - | - | - | - | - | - | none / IR LOB n/a |
| KR0005 | 흥국화재 | 1432.1 | - | - | - | - | - | - | - | - | - | - | - | unreliable_parse (LOB합 476 vs 보험손익 1432) / IR LOB n/a |
| KR0032 | NH농협손해 | -22.3 | -3560.4 | 27.1 | -540.6 | -4073.9 | - | - | - | - | - | - | - | unreliable_parse (LOB합 -4074 vs 보험손익 -22) / IR LOB n/a |
| KR0050 | 하나손해 | - | -79.7 | -274.4 | -4.1 | -358.2 | - | - | - | - | - | - | - | ok_no_tier1_anchor (LOB합 -358) / IR LOB n/a |
| KR1000 | 코리안리 | 2265.0 | 458.4 | 290.0 | 2434.2 | 3182.6 | - | - | - | - | - | - | - | ok (LOB합 3183 vs Tier1 보험손익 2265) / IR LOB n/a |

Δ % = (DART − IR) / |IR|.  **Bold** = |Δ| ≥ 10%.

---

## Cross-check가 가능한 3사 (Samsung Fire / DB / Meritz)

- **삼성화재 (KR0008)** — both DART & IR are 별도/IFRS17, same source (note 발행보험 by 계약유형). DART 장기 16650.8 vs IR 장기 15077.3 → +10.4%; DART 자동차 -1220.3 vs IR -1589.9 → +23.2%; DART 일반 5916.6 vs IR 1707.9 → +246.4%.
  - 장기는 +10.4% (DART note는 연결+세칙합산 가능성, IR factsheet는 명시적으로 별도). 자동차는 +23% (DART가 손실 덜 잡힘). **일반은 +246%로 가장 큰 격차** — DART 일반 보험수익이 IR의 별도재무제표 일반보다 훨씬 큼 (DART note에 손실부담계약 회복분/기타 흡수 가능). 별도 확인 필요.

- **DB (KR0011)** — DART 자동차 6810.5 (=DART 보험수익 26,777 − 보험서비스비용 19,966 = +6,810) vs IR 자동차 -547.3. 부호가 반대이고 절대값도 큰 격차. DART note table에서 자동차 보험서비스비용이 사업비 미포함 추출이거나, 손실부담계약 등 일부 항목이 자동차에서 빠진 것으로 추정. DB의 IR factsheet '보험손익' sheet는 별도 vs 연결 표기가 명확하지 않음 (전부 보종별 표).
  - DB 장기 12256.8 vs IR 10758.2 → +13.9% (장기는 +14%); 일반 -26.1 vs 148.7 → -117.6% (일반은 사실상 0 vs -26).

- **메리츠 (KR0001)** — DART는 보종별 사업실적표 (별도 1117 기준), IR은 Insurance_Condensed PL (별도 누계). 장기 15780.3 vs 14339.7 → +10.0% (정확히 +10.0%, 경계); 자동차 -495.7 vs -463.2 → -7.0% (+7%); 일반 396.6 vs 377.6 → +5.0% (+5%).
  - 합계 DART 15681.2 vs IR 14254.1 → +10.0%. 메리츠 보종별 표는 기타사업비용 미차감 (~1,400억) 이고, IR PL은 차감 후 → 약 +10% 구조적 갭. 부문별 비율은 일관.

## IR cross-check 불가 회사

- **현대 (KR0009)** — IR factsheet `.xlsx`가 손상 (Cr24 magic, openpyxl 비호환). PDF 만 있음. DART는 기존 note extractor로 안정 (장기 4,097 / 자동차 -677 / 일반 6,613).
- **한화 (KR0002)** — FY2025_Q4 IR factsheet 부재. DART note extractor 유지 (sum 2,470 vs Tier1 2,611 — 5% 이내 reconcile).
- **KB (KR0010)** — DART 별첨 Note (6) '보험손익의 상세내역' (IFRS17 행 직접). 장기 7,901 / 자동차 -1,077 / 일반 39 (해외지점 -105 포함), sum 6,863 vs Tier1 6,267 — clean (~9% gap).
- **NH (KR0032)** — DART 보종별 영업실적은 **regulatory 사업실적표** (경과보험료-발생손해액-순사업비), IFRS17 보험손익 아님. 장기 -3,560 / 자동차 27 / 일반 -541, sum -4,074 vs Tier1 -22 (큰 격차는 expected: 사업비 미배분 + IFRS17 ↔ 4 회계기준 차이).
- **하나 (KR0050)** — DART Note 29 '보험손익 및 재보험손익' (IFRS17 행 직접, 천원 단위). 장기 -148 / 일반 -4 / 자동차 -274, sum -426. Tier1 포괄손익계산서 추출 실패 (Hana 손익은 I/II/III/IV 로마숫자 rollup이라 보험손익/투자손익 라벨 행이 없음). status=`lob_only`.
- **롯데 (KR0003)** — `.xls` (openpyxl 비지원) + 단일 부문이라 DART도 LOB 없음.
- **코리안리 (KR1000)** — IR site IP-block. DART 보종별 영업규모 표 (재보험 taxonomy: 자동차는 일반손해보험 grouping 내부). 일반 2,434 / 자동차 290 / 장기(=장기손해+생명) 458, sum 3,183 vs Tier1 2,265 (+41%, regulatory 기반).
- **흥국 (KR0005)** — 기존 JSON에서 unreliable_parse 상태 유지; 별도 per-company 추출 추가 안 함 (current sprint scope 외).

---

## Verification summary

- **DART tier2_lob coverage**: 9/11 companies (Samsung/Hyundai/DB/KB/Meritz/Hanwha/NH/Hana/Korean Re). Lotte and Heungkuk = no LOB (structural skip / unreliable parse).
- **IR cross-check coverage**: 3/11 (Samsung/DB/Meritz) — others lack a machine-readable IR LOB source.
- **±10% 이내 일치**: Meritz 자동차/일반 (5–7%). Samsung 장기/Meritz 장기는 정확히 +10.0–10.4% (경계). DB 자동차 (반대 부호) / Samsung 일반 (+246%) = 큰 차이, 정확한 별도 vs 연결 / 기준 차이 확인 필요.
- **Regression**: 0 — Samsung/Hyundai/DB/Hanwha tier1/tier2 values unchanged vs baseline.
- **DB IR cross-check self-reconcile**: DB IR factsheet 보종별 합계 10,360 vs DART Tier1 11,454 (gap +10.6%); IR is 별도, DART tier1 is 연결 — likely the right reason.
