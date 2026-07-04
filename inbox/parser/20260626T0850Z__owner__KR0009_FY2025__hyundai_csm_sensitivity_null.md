---
from: owner
to: parser
created: 20260626T0850Z
status: answered
route: reextract
company: KR0009 (현대해상)
period: FY2025
lane: ifrs17
---

## 미결 (owner) — 현대해상 FY2025 CSM 민감도(ΔCSM) 전 셀 null = 파싱갭 (원천엔 값 있음)

**증상**: IFRS17.html "CSM 변동분석(민감도)"에서 현대해상이 **모든 ΔCSM·손익영향 "—"**. `data/dart/viz/sensitivity_heatmap.json` 현대해상 레코드: `status:"ok"`인데 6개 시나리오 전부 `csm_delta:null, pl_impact:null` + `unit_source:"suspect"` + `unit_warning:"max|ΔCSM|=166,836,326억 >> total CSM=92,485억 — unit unresolved"`.

**진단 (owner 직접 raw 확인) — 원천 미공시 아님, 추출 실패:**
- raw `data/dart/extracted/현대해상_20260312001448_sensitivity.json`(FY2025 접수 20260312001448)에 **세전이익 22회·재보험효과 16회** = 민감도 표·숫자 **실재**.
- **근본원인 = 현대해상 표 형식이 타사와 다름**. 헤더 = `세전이익 변동효과(재보험 전/후) | 자본 변동효과(재보험 전/후)` **4값 컬럼** 구조(단순 ΔCSM/손익 2컬럼 아님). 제너릭 추출기가 컬럼 매핑 실패 → 값 null + 엉뚱한 셀 잡아 unit 폭주(suspect).
- **공시 프레임 차이**: 현대해상은 **ΔCSM이 아니라 「세전이익 변동효과 + 자본 변동효과」(재보험 전/후)**로 공시(배당요소 보험계약). 위험요인은 회사 고유 calibration(사망률 3.27%↑·장해질병 3.40/2.62%↑·재물 4.19%↑·해지율 9.16%↑/↓·사업비 2.62%+인플레 0.26%p).

**범위 = 현대해상 1사 단독** (census: `sensitivity_heatmap` 31사 중 현대해상만 all-null, 나머지 26사 정상). systemic 아님 → 표적 per-company 핸들러.

**요청:**
1. 현대해상 4컬럼 표(세전이익 변동효과 재보험 전/후 · 자본 변동효과 재보험 전/후) 핸들러 추가 → 6 시나리오 값 추출.
2. **필드 매핑**: 세전이익 변동효과 → `pl_impact`(재보험 후 기준), 자본 변동효과 별도 필드. **ΔCSM은 현대해상 미공시이므로 null 유지하되 `disclosed_as:"세전이익/자본 변동효과"` 플래그**(공란 아님을 구분 — "추출실패 null"과 "원천 ΔCSM 부재"는 다름).
3. **unit 해소**: 백만원→억원(`unit_detected:"백만원"`인데 `unit:"억원"` 충돌 → ×0.01), `unit_warning`/`suspect` 제거.
4. 재빌드 후 `sensitivity_heatmap` 현대해상 값 채워지고 unit_warning 0 검증.

**downstream FYI(designer/data-contract)**: 현대해상처럼 ΔCSM 대신 세전이익/자본 변동효과로 공시하는 회사가 있으니, 패널이 두 프레임(ΔCSM-공시사 vs 세전이익/자본-공시사)을 라벨로 구분해야 함. parser는 `disclosed_as` 플래그만 달고, 표시는 designer 소관.

연계: 기존 FY2025 sensitivity 재추출 발주(`20260615T0435Z`)의 현대해상 확정 케이스.

## 답변 (ifrs17, 2026-07-03)

**원인 확정 = owner 진단대로 4값열 프레임 매핑 실패 + 단위 오판.** raw block(별도 당기말, 접수 20260312001448) 확인:
- 헤더 = `세전이익 변동효과(재보험 前/後) | 자본 변동효과(재보험 前/後)` = **4값열**, 위험별 **3행**(배당요소 있는/없는/**소계**). ΔCSM 컬럼 자체가 없음(현대해상은 ΔCSM 미공시, 세전이익·자본 변동효과로 공시). 제너릭 추출기가 컬럼 매핑 실패 → 6셀 all-null.
- **단위 = 원(KRW), ÷1e8 → 억원.** owner 노트 "백만원 ×0.01"은 가정 오류 — 데이터 교차검증으로 원 확정: 장해질병 자본효과 소계 49,157,927,166 → ÷1e8=491.6억(총CSM 92,485억 대비 타당) vs ÷100(백만원 가정)=4.9억억(불가). 스킬 룰 "note와 data 충돌 시 data 우선" 적용. 이 ÷1e8이 `unit_warning`/`suspect` 폭주의 진짜 원인(제너릭이 엉뚱 셀 잡고 백만원 가정).

**매핑(owner 지시대로)**: `pl_impact`←세전이익 변동효과 재보험後(소계행), `equity_impact`(신규 필드)←자본 변동효과 재보험後(소계행), `csm_delta`=null + 각 시나리오 `disclosed_as:"세전이익/자본 변동효과 (재보험 후, ΔCSM 미공시)"`. 소계=배당+무배당 항등식으로 4열 전부 검증.

**값(별도 당기말 소계, 억원)**:
| 위험 | pl_impact(세전이익 재보후) | equity(자본 재보후) |
|---|---|---|
| 사망률 3.27%↑ | △4.09 | 48.02 |
| 장해질병(정액3.40+실손2.62)↑ | △3,452.33 | 489.54 |
| 재물·기타 4.19%↑ | △41.26 | 18.45 |
| 해지율 9.16%↑ | 43.74 | 362.8 |
| 해지율 9.16%↓ | △40.75 | △425.83 |
| 사업비 2.62%+인플레0.26%p↑ | △177.84 | 68.05 |

**req 대비**: req1 값추출 done · req2 매핑+disclosed_as flag done · req3 unit 해소 done(÷1e8, 백만원 아님, `unit_warning`/`suspect` 제거 확인) · req4 재빌드 후 현대해상 값 채움+warning 0 검증 done.

**적용**: 파괴적 rebuild 금지 브랜치라 `sensitivity_overrides.json`에 현대해상 6 시나리오 주입 + `viz_build_ifrs17_panels.py` 재빌드 후 heatmap **현대해상 레코드만 surgical 교체**. HEAD 대비 변경 = {한화생명(별건 0703), 현대해상} 2건뿐, 회사 add/remove 0, 형제 패널(csm_amort/insurance_pl/bs_snapshot)·타 26사 전부 unchanged.

**downstream FYI (designer)**: 현대해상은 ΔCSM 대신 세전이익/자본 변동효과 프레임 → `csm_delta:null`은 '—'로, `pl_impact`(세전이익)을 주값으로 렌더 권장. `disclosed_as` 플래그로 ΔCSM-공시사와 구분 표기. `equity_impact` 필드 신규(자본 변동효과, 표시 여부는 designer 판단). 음수는 △ 표기.

**후속(별건, 미차단)**: 4값열-재보험 프레임(세전이익/자본 × 재보험 前/後) per-company 추출 핸들러 일반화 = 추출기 follow-up. 현재 override로 커버.

status → answered (owner 사이트 재확인).
