# CSM 상각 스케줄 분할표 5사 + 한화생명 연결/별도 표 선택 — 증빙 (2026-10-12, parser-ifrs17, 티켓 20261012T1020Z 항목 6)

재현: `scripts/extract_amort_split_tables_20261012.py`(원문 XML 읽기·항등식·스펙 생성) → `scripts/load_amort_split_tables_20261012.py [--apply|--revert]`(셀 단위 적재). 마스터 `CSM_amortization.json` 2025.4Q 만, 패널·xlsx 는 안 건드렸다.

## 1. 바꾼 칸 전수 (전 → 후, 억원, 소수 1자리 = `build_tidy_exports.num`)

| 회사 | 경과차년 | 전 | 후 | 정확값(억원) | 원천 |
|---|---|---|---|---|---|
| 에이아이에이생명보험 (KR0080) | y9 | (빈 칸) | 613.2 | 613.17 | separate filing back table (9년·10년 columns) |
| 에이아이에이생명보험 (KR0080) | y10 | (빈 칸) | 565.6 | 565.56 | separate filing back table (9년·10년 columns) |
| 처브라이프생명보험 (KR0100) | y9 | (빈 칸) | 21.0 | 21.0 | separate filing back table (9년·10년 columns) |
| 처브라이프생명보험 (KR0100) | y10 | (빈 칸) | 20.4 | 20.44 | separate filing back table (9년·10년 columns) |
| 메트라이프생명보험 (KR0095) | y9 | (빈 칸) | 1042.9 | 1042.87172 | separate filing back table (9년·10년 columns) |
| 메트라이프생명보험 (KR0095) | y10 | (빈 칸) | 960.0 | 959.96153 | separate filing back table (9년·10년 columns) |
| 비엔피파리바카디프생명보험 (KR0075) | y9 | (빈 칸) | 11.1 | 11.05591 | separate filing back table (9년·10년 columns) |
| 비엔피파리바카디프생명보험 (KR0075) | y10 | (빈 칸) | 9.0 | 9.04199 | separate filing back table (9년·10년 columns) |
| 한화생명 (KR0068) | y1 | 4484.3 | 4244.1 | 4244.11 | separate filing single wide table (replaces the consolidated table the panel picked) |
| 한화생명 (KR0068) | y2 | 3933.4 | 3762.3 | 3762.28 | separate filing single wide table (replaces the consolidated table the panel picked) |
| 한화생명 (KR0068) | y3 | 3579.4 | 3433.5 | 3433.46 | separate filing single wide table (replaces the consolidated table the panel picked) |
| 한화생명 (KR0068) | y4 | 3310.8 | 3183.5 | 3183.5 | separate filing single wide table (replaces the consolidated table the panel picked) |
| 한화생명 (KR0068) | y5 | 3065.0 | 2953.3 | 2953.26 | separate filing single wide table (replaces the consolidated table the panel picked) |
| 한화생명 (KR0068) | y6 | 2888.5 | 2790.3 | 2790.32 | separate filing single wide table (replaces the consolidated table the panel picked) |
| 한화생명 (KR0068) | y7 | 2734.4 | 2648.1 | 2648.05 | separate filing single wide table (replaces the consolidated table the panel picked) |
| 한화생명 (KR0068) | y8 | 2599.2 | 2523.2 | 2523.22 | separate filing single wide table (replaces the consolidated table the panel picked) |
| 한화생명 (KR0068) | y9 | 2474.2 | 2407.4 | 2407.39 | separate filing single wide table (replaces the consolidated table the panel picked) |
| 한화생명 (KR0068) | y10 | 2330.8 | 2272.0 | 2272.0 | separate filing single wide table (replaces the consolidated table the panel picked) |

합계 18칸 = 분할표 4사 y9·y10 8칸(빈 칸 → 값) + 한화생명 y1~y10 10칸(연결 → 별도). 라이나 2025.4Q 는 이미 PDF 로 y1~y10 이 채워져 있고 DART 뒷 표와 5자리까지 일치해서 **바꾸지 않았다**.

## 2. 합계 항등식 확인표 (원문 표 직접 읽기, 단위는 회사별 표 단위)

당기 표(문서에서 먼저 나오는 쌍) 합계 = 마스터 2025.4Q 기말 CSM(항목 6), 전기 표 합계 = 마스터 2024.4Q 기말 CSM. 행 단위로는 `y1~y8 + (9년, 10년, 11~15, 16~20, 21~25, 26~30, 30+) = 계` 가 모든 포트폴리오 행에서 닫힌다(허용 3 단위).

| 회사 | 원천(별도) | 단위 | 당기 합계(억원) | 마스터 기말 CSM 2025.4Q | 상대차 | 전기 합계(억원) | 마스터 2024.4Q | 행 항등식 최악 잔차 | 별도=연결 | y1~y8 합 | y9+y10 | y11+ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 에이아이에이생명보험 (KR0080) | `20260407002100_00760.xml` 쌍 13009·13193행 | 백만원 | 15,903.62 | 15,903.6 | +0.000001 | 15,096.53 | 15,096.5 | 0.0 백만원 | 같음(전 행) | 6,094.96 | 1,178.73 | 8,629.93 |
| 처브라이프생명보험 (KR0100) | `20260408003172_00760.xml` 쌍 15442·15600행 | 백만원 | 869.63 | 869.6 | +0.000034 | 980.21 | 980.2 | 0.0 백만원 | 연결 파일 없음 | 205.42 | 41.44 | 622.77 |
| 메트라이프생명보험 (KR0095) | `20260403003824_00760.xml` 쌍 14795·15008행 | 천원 | 26,081.60 | 26,081.6 | +0.000000 | 24,066.91 | 24,066.9 | 0.0 천원 | 같음(전 행) | 12,188.13 | 2,002.83 | 11,890.64 |
| 비엔피파리바카디프생명보험 (KR0075) | `20260406004430_00760.xml` 쌍 14642·14753행 | 천원 | 299.58 | 299.6 | -0.000001 |  |  | 1.0 천원 | 연결 파일 없음 | 224.41 | 20.10 | 55.07 |
| 라이나생명보험 (KR0074) | `20260406004538_00760.xml` 쌍 14807·14977행 | 천원 | 23,760.60 | 23,760.6 | -0.000000 | 27,648.60 | 27,648.6 | 0.0 천원 | 같음(전 행) | 11,793.27 | 1,783.20 | 10,184.13 |

한화생명(KR0068): 별도 표 한 장(분할 아님) — `20260316001304_00760.xml` 18512행, 합계 87,136.52억원 = 마스터 기말 CSM 87,136.5(상대차 +2.30e-07), y1~30+ 합 = 계(잔차 0.0 백만원). 옛 마스터 값 = 연결 표 `20260316001304_00761.xml` 27569행(합계 88,752.04억원, 별도보다 +1.85 %). y11+ = 56,918.93억원(마스터는 y1~y10 만 담는다).

## 3. 안 한 것 / 알려둘 것

- 패널 `data/dart/viz/csm_amort_schedule.json`·`viz_build_ifrs17_panels.py::extract_amort_schedule`(앞 반쪽만 읽는다)·xlsx `CSM상각` 시트는 티켓 규칙대로 안 건드렸다. 패널 `buckets.total`(분할표 4사 + 라이나)은 계속 부분합이고 한화생명 패널은 연결 표다. `build_tidy_exports.py --only amort` 로 마스터를 패널에서 다시 만들면 이 18칸이 되돌아가므로 그 뒤 `scripts/load_amort_split_tables_20261012.py --apply` 를 다시 돌린다.
- 라이나 패널 행을 마스터값으로 바꿀지는 이번 범위 밖(보고만).
- 마스터에는 y1~y10 만 있다. y11 이후(AIA 8,629.93 · 처브 622.77 · 메트라이프 11,890.64 · BNP 55.07 · 라이나 10,184.13 · 한화생명 56,918.93억원)는 `amort_split_evidence.json` 의 `y11plus_eok` 에 있다.
