# Fresh Visualization Proposals for insurequant.html

*2026-05-24 — IR/Visualization subagent (3rd domain output)*

## 목적

`insurequant.html`에 추가할 **신선한 분석 시각화** 10가지 제안. IR PDF 표준 KPI
(CSM waterfall / 신계약 CSM 배수 꺾은선)는 이미 prototype 작업 중이므로 본
문서에서 다루지 않는다. 핵심 원칙:

1. **3개 데이터 소스 결합 우선** — K-ICS (23사 × 9분기 + 보조지표 7개 + 경과
   조치 전·후) × IFRS17 (23사 A1/A2/A3/A4/B1/B5) × IR PDF (6사 카탈로그).
2. **IR PDF에 없는 derived metric** OK — `csm_dependency`, `csm_runway_years`,
   `schedule_run_rate`, `nb_replacement` 등 4종 다운스트림 KPI를 자연스럽게
   만나게 한다.
3. **prototype 가능한 수준** — Bayesian forecast 같은 학술적 추상은 금지.
4. **insurance analyst 한눈에 의사결정**할 수 있어야 함.

---

## 제안 10가지

### #1. Earnings Quality Quadrant — `csm_dependency` × `csm_runway_years`

- **차트 종류:** Scatter (사분면, 23社 dot + 회사명 라벨 + 분기별 trail)
- **데이터 소스:** IFRS17 A1 (`csm_amort_pl`, `insurance_service_result`,
  `closing_total_csm`) + 손익계산서 (`investment_income`, `ifie_pl`)
- **무엇을 보여주는가:** X축 = `csm_dependency` (이익이 CSM release에 얼마나
  의존하는가, 0–1), Y축 = `csm_runway_years` (이 의존도가 몇 년 더 받쳐주는가).
  4사분면 라벨: 좌상 "Safe Cash Cow" / 우상 "CSM-fed but Long Runway" / 우하
  "Fragile" / 좌하 "Earnings Diversified". 23社가 한 화면에 분포.
- **왜 신선한가:** IR PDF는 회사별로 CSM 변동·잔액을 따로 보여줄 뿐, 두 KPI를
  **cross-section quadrant**로 묶어 peer-relative 위치를 보여주지 않음. 사용자
  mental model의 `csm_dependency`와 `csm_runway_years`가 한 차트에서 만남.
- **구현 난이도:** Easy (A1 23/23 + A3 일부만 정규화되면 됨)
- **예상 사용자:** Sell-side analyst (peer positioning), portfolio manager

### #2. CSM Quality Heatmap — 23社 × 분기 × 변동요인 (+/−)

- **차트 종류:** Heatmap (행=23社, 열=분기, 색=조정량의 부호·크기,
  cell hover로 변동요인 5종 breakdown)
- **데이터 소스:** IFRS17 A1 `nb_effect`, `assumption_adjusts_csm`,
  `experience_adj`, `csm_amort_pl`, 분기 시계열
- **무엇을 보여주는가:** 한 화면에서 "어느 회사가 어느 분기에 가정변경/경험조정
  으로 CSM이 +/− 흔들렸는가". 외부 충격(2025년 할인율 변동) 시 23社가
  동일 방향으로 움직였는지, 회사별 outlier가 누구인지 한눈에. 사용자가 "이번
  분기 CSM이 망가진 회사 누구야?" 질문에 1초 답.
- **왜 신선한가:** IR PDF는 단일 회사만 보여주고, 다른 회사 비교 불가. 23社
  cross-section heatmap은 IR에는 없는 시각화. 1社가 가정변경으로 -200이면
  특이치인지 시장 전체 트렌드인지 즉시 판별.
- **구현 난이도:** Medium (A1 분기 정규화 필요 — 현재는 연간 사업보고서만 23/23)
- **예상 사용자:** Sell-side analyst, 보험사 IR 담당 (peer 대비 자기 회사 위치)

### #3. K-ICS Transitional Cliff — 경과조치 전·후 격차 ranking

- **차트 종류:** Dumbbell chart (수직 23社 ranking, 각 사 점 2개 + 연결선)
- **데이터 소스:** K-ICS `값` (적용 전) vs `값_적용후` (적용 후) — 지급여력비율
  + 기본자본비율
- **무엇을 보여주는가:** 경과조치(transitional) 제거 시 K-ICS 비율이 얼마나
  떨어지는지. 23社를 cliff drop 크기로 ranking. 큰 drop = 경과조치 의존, 작은
  drop = 자력 capital 강함. **Hidden capital risk** 가시화.
- **왜 신선한가:** K-ICS 단일 비율 시계열은 IR PDF에 흔하지만, "경과조치 효과
  크기"를 회사별 ranking으로 비교하는 시각화는 **공개 자료 어디에도 없음**.
  K-ICS 데이터 보조지표 7개 활용 (현재 단순 토글 UI에 묻혀 있는 데이터를
  분석 도구로 승화).
- **구현 난이도:** Easy (기존 K-ICS JSON에 `값` + `값_적용후` 둘 다 있음)
- **예상 사용자:** Credit analyst (보험사 채권), 규제 watcher, 일반 투자자

### #4. Risk Composition Radar — 5대 위험액 share (23社 overlay)

- **차트 종류:** Radar chart (5축: 생명장기/일반손해/시장/신용/운영 위험액
  share), 회사 클릭 시 peer 평균 overlay
- **데이터 소스:** K-ICS 항목번호 (생명장기손해보험위험액 / 일반손해보험위험액
  / 시장위험액 / 신용위험액 / 운영위험액)
- **무엇을 보여주는가:** 보험사 risk DNA. 손보-생보 구분 없이 5개 위험 share를
  표준화하면 "이 회사는 시장 위험에 과도 집중", "신용 위험이 peer 대비 1.5배"
  같은 outlier가 즉시. Peer average overlay로 deviation 시각화.
- **왜 신선한가:** K-ICS 분기 공시에 분명히 있는 위험액 5종을 IR PDF는 거의
  공개 안 함 (삼성화재 일부만). Radar로 묶은 시각화는 본 카탈로그 6社 어디에도
  없음. 또한 보조지표(사망/장수/해약/사업비/대재해)와 결합 시 13축 확장 가능.
- **구현 난이도:** Easy (K-ICS JSON 그대로)
- **예상 사용자:** Risk officer, ALM 담당, sell-side analyst

### #5. CSM × K-ICS Coherence Scatter — Cross-source 정합성

- **차트 종류:** Scatter (X = `closing_total_csm` 절대치 또는 / 자본, Y = K-ICS
  비율), 23社 dot, regression line + outlier 라벨
- **데이터 소스:** IFRS17 A1 `closing_total_csm` × K-ICS 지급여력비율
- **무엇을 보여주는가:** "CSM 많이 쌓은 회사 = K-ICS 비율도 높을까?" 직관 검증.
  이론적으로는 CSM이 부채 측 미실현이익이므로 K-ICS 가용자본과 무관. 그러나
  실제로 두 지표가 같은 방향으로 움직이는지 / 어긋나는지 확인. 어긋나는 회사
  (CSM 풍부 but K-ICS 낮음 또는 그 역) = analyst 주목 대상.
- **왜 신선한가:** K-ICS와 IFRS17은 **서로 다른 부처(금감원 vs 회계기준원)**
  관할이라 IR PDF에 함께 비교한 시각화 거의 없음. 두 데이터셋이 모두 23社
  정렬되어 있는 사이트는 insurequant가 최초.
- **구현 난이도:** Medium (corp_name normalize + 분기 align 필요)
- **예상 사용자:** Sell-side analyst, regulator

### #6. CSM Runway vs K-ICS Solvency Map — Forward solvency bubble chart

- **차트 종류:** Bubble chart (X = `csm_runway_years` IFRS17 P&L 시각, Y = K-ICS
  비율 = 규제 capital 시각, size = `closing_total_csm` 절대 규모, color = 손보
  vs 생보)
- **데이터 소스:** IFRS17 A1 + A2 (runway) × K-ICS 지급여력비율
- **무엇을 보여주는가:** "수익 받쳐주는 시계" × "규제자본 여유도" 동시 view.
  4사분면: 우상 "Forward-safe" / 우하 "Profitable but undercapitalized" / 좌상
  "Capital-strong, earnings-thin" / 좌하 "Double-risk". 보험사 forward
  sustainability를 한 차트에서.
- **왜 신선한가:** csm_runway_years는 IR PDF 어디에도 없는 derived KPI (4종
  중 하나). K-ICS와 결합한 bubble map은 본 도메인 최초.
- **구현 난이도:** Medium (#1과 데이터 재활용)
- **예상 사용자:** PM, credit analyst

### #7. Schedule Run-Rate Bullet Chart — A2 1-3년 vs 4년+ 23社 비교

- **차트 종류:** Bullet chart (회사별 가로 막대 — 1-3년 cumulative %를 막대로,
  peer 평균을 marker로, 4년+ tail을 음영 영역으로)
- **데이터 소스:** IFRS17 A2 `csm_amort_schedule` 23/23 자동 추출 완료
- **무엇을 보여주는가:** `schedule_run_rate = sum(buckets_y1_y3) /
  closing_total_csm`. 가까운 미래(1-3년)에 얼마나 빨리 CSM이 풀리는지 = earnings
  front-load. 높으면 단기 수익 강함 but 그 이후 cliff 위험. 낮으면 long-tail
  안정. 회사별 dispersion을 한 차트에서.
- **왜 신선한가:** A2 스케줄은 IR PDF에 거의 없음 (DART 사업보고서 §14(7))
  → 우리만 가진 데이터. 23社 cross-section은 첫 시각화.
- **구현 난이도:** Easy (A2 정규화 완료)
- **예상 사용자:** Sell-side analyst, credit analyst

### #8. NB Replacement Funnel — 신계약이 상각 상쇄하나?

- **차트 종류:** 회사별 horizontal bar (양방향) — 좌측 음수 = `csm_amort_pl`,
  우측 양수 = `nb_effect_csm`, 라벨 = `nb_replacement = nb_effect / amort`
- **데이터 소스:** IFRS17 A1 `nb_effect`, `csm_amort_pl` (23社 분기)
- **무엇을 보여주는가:** 사용자 KPI `nb_replacement` 직관화. >1이면 신계약이
  상각을 초과 보충 (성장 단계), <1이면 CSM 감소 (run-off 단계). 23社가 어느
  편에 있는지 즉시. 분기별 toggle로 trend 추적.
- **왜 신선한가:** 신계약 CSM 막대는 IR PDF 표준이지만, **"상각 대비 비율"**
  로 funnel/replacement 관점에서 시각화한 것은 없음. 한 보험사가 "성장 vs
  소진" 어느 단계인지 1초 판정.
- **구현 난이도:** Easy (A1만 필요)
- **예상 사용자:** Sell-side analyst, equity investor

### #9. Quarter-over-Quarter Volatility Detector — Outlier scatter + spaghetti

- **차트 종류:** Spaghetti plot (23社 K-ICS 비율 9분기 시계열) + Z-score
  threshold band (±2σ) + QoQ change scatter overlay
- **데이터 소스:** K-ICS `값`(또는 `값_적용후`) 9분기 시계열
- **무엇을 보여주는가:** 23社 비율 시계열을 한 차트에 겹쳐 outlier 회사 자동
  표시. 분기별 K-ICS 변동량 (ΔK-ICS)이 σ 이상이면 별도 라벨. "2025.2Q에 누가
  급락했나" 즉시 답. 거시 충격(금리 급변) 시 영향도 회사별 분포.
- **왜 신선한가:** 시계열 한 줄씩은 IR에 흔하지만, **23社 cross-section
  spaghetti + 자동 outlier 라벨**은 없음. 인사이트는 외부 매크로 의존도 판별
  + 동조 vs 독립 그룹 발견.
- **구현 난이도:** Easy
- **예상 사용자:** Analyst, regulator, journalist

### #10. CSM-Sensitivity Tornado — 가정 충격 ranking (23社 cross-section)

- **차트 종류:** Tornado chart (회사별 그룹, 좌우 양방향, 가정 5종 ± 충격
  영향 크기 막대)
- **데이터 소스:** K-ICS B5 `assumption_sensitivity` (현재 미정규화, K-ICS
  분기 공시 primary로 ingest 계획) — 사망/장수/해약/사업비/대재해 충격 시
  지급여력비율 또는 LIC 변동
- **무엇을 보여주는가:** "이 회사 K-ICS가 해약률 +10% 충격에 얼마 흔들리나?"
  를 23社 ranking으로. Tornado 한 paneled view에서 회사 5명 가정 5축 비교.
  Fragility 가장 큰 회사·축 즉시 식별. `csm_dependency`가 높은 회사가 sensitivity
  도 큰지 cross-check (cross-quadrant intuition).
- **왜 신선한가:** IR PDF에는 회사 자체 1-2개 시나리오 (DB의 -50bp/+50bp, 현대
  해상의 50bp 하락)만. 23社 표준화 tornado는 K-ICS 분기 공시 primary 정규화
  후에만 가능 → 우리만 가능.
- **구현 난이도:** Hard (K-ICS B5 정규화 + 가정 라벨 표준화 필요)
- **예상 사용자:** Risk officer, regulator, advanced analyst

---

## 메타 분석

### Top 3 추천 (신선함 + 구현 가능성 + 사용자 mental model 도달도)

1. **#1 Earnings Quality Quadrant** — `csm_dependency` × `csm_runway_years`
   두 KPI가 자연스럽게 한 차트에서 만남. 데이터 23/23 가용. 즉시 prototype 가능.
   "have no idea" 사용자에게 **가장 강력한 첫 시각화** — peer 23社 한눈 비교.

2. **#3 K-ICS Transitional Cliff (dumbbell)** — 기존 데이터 100% 활용. 추가
   ingestion 0. 단순 차트로 "hidden capital risk"라는 신선한 narrative 생성.
   메인 사이트 첫 인상으로 강력.

3. **#7 Schedule Run-Rate Bullet Chart** — A2 23/23 완료. IR PDF에 거의 없는
   데이터를 cross-section으로 visualizing. `schedule_run_rate` KPI 직관화.
   prototype 시간 짧음.

### 데이터 가용성 분류

| 분류 | 제안 | 비고 |
|---|---|---|
| **즉시 prototype (데이터 가용)** | #1, #3, #4, #6, #7, #8, #9 | A1+A2+K-ICS 정규화 완료분만 사용 |
| **추가 정규화 필요 (1-2주)** | #2 분기별 A1, #5 cross-source align | A1을 분기 공시까지 확장 (현재는 사업보고서만 23/23) |
| **B5 정규화 필요 (장기)** | #10 | K-ICS 분기 공시 B5 ingest 계획 + 가정 라벨 표준화 |

### 사용자 mental model 4종 KPI가 어디서 만나는가

| KPI | 자연스러운 chart |
|---|---|
| `csm_dependency` | #1 (quadrant), #10 (sensitivity 상관) |
| `csm_runway_years` | #1, #6 (bubble Y) |
| `schedule_run_rate` | #7 (bullet 본체) |
| `nb_replacement` | #8 (funnel 본체) |

4종 모두 시각화로 매핑되어 있으며, **#1**이 2종을 합친다는 점에서 mental model
'first contact'에 가장 적합.

### "have no idea" 사용자에게 강조하는 첫 3개

1. **#1 Earnings Quality Quadrant** — 23社 한 화면에 sell-side 직관
2. **#3 K-ICS Transitional Cliff** — 단순하고 즉시 wow factor
3. **#8 NB Replacement Funnel** — 회사 단위 "성장 vs 소진" 1초 판정

이 3개로 시작하면 사용자가 IR catalog의 표준 KPI 차트(CSM waterfall / 신계약 CSM
배수)와는 다른 **insurequant.html만의 narrative**가 형성된다.

### 우선순위 매트릭스 (신선함 × 구현 난이도)

```
                  Easy            Medium          Hard
신선함 ↑        #1, #3, #7       #2, #5, #6        #10
신선함 중        #4, #8, #9          —              —
신선함 ↓        (IR 표준)           —              —
```

`(IR 표준)` = CSM waterfall, 신계약 CSM 배수 — 이미 prototype 중. 본 문서 범위
외.

---

## 사용자 결정 필요 항목

1. **Top 3 중 어떤 것부터 prototype** — #1 quadrant / #3 dumbbell / #7 bullet
   순서 추천. 사용자가 다른 우선순위 있으면 알려달라.
2. **#2 heatmap** — 분기별 A1 정규화 작업이 prerequisite. 별도 작업으로
   schedule 할지, 본 prototype과 합칠지 결정.
3. **#10 tornado** — B5 정규화는 IFRS17 agent 작업. visualization을 prerequisite
   완료 후로 보류할지, mock data로 design proto 먼저 만들지 결정.
4. **시각화 라이브러리** — 기존 `insurequant.html`은 vanilla CSS treemap. 위
   제안 대부분 D3 / Plotly / ECharts가 자연스러움. 라이브러리 채택 의향 확인.

---

## 부록: 사용한 데이터 inventory

- **K-ICS:** `kics_disclosure.json` — 23社 × 9분기 × 항목 (`값` 적용 후 ratio
  포함), 5대 위험액 + 보조 KPI.
- **IFRS17 A1 (measurement rollforward):** `data/dart/extracted/*_measurement.json`
  + `*_measurement_mvp.json` — 23/23 사업보고서 추출. 분기별은 P3 (MVP 이후).
- **IFRS17 A2 (CSM amort schedule):** `data/dart/extracted/*_csm.json` — 23/23.
- **IFRS17 A3/A4/B1/B5:** 23/23 MVP (사용자 보고 기준). 정규화 단계 상이.
- **IR PDF 6社:** `artifacts/ir_research/` (5社 PDF + Text).

---

*본 문서는 코드 변경 없음. 다음 세션은 위 Top 3 중 사용자 결정 받은 1건부터
prototype 시작.*
