---
from: validation
to: parser
created: 20260825T1120Z
status: open
route: reparse
company: MULTI
period: MULTI
rule: PL_BRIDGE_DART_INTERNAL
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

**게이트가 지금까지 안 보던 셀에서 나온 결함이다.** `scripts/validate_master_tables.py` 의
PL 축이 파서 중간산출물 `data/dart/viz/pl_breakdown_master.json` 을 읽고 있었다. 2026-08-25 에
배포본 `PL_breakdown.json` 으로 재조준했고, **배포본에만 있던 1,307셀이 처음으로 PL 항등식을
받으면서 16건이 드러났다.** (같은 재조준으로 그 게이트가 찍던 `HOLE-PL` 24건은 24/24 전부
phantom 이었음이 확인돼 사라졌다 — 회귀가 아니다.)

전건이 `data/_gold/pl_bridge_baseline.json` 에 분류·사유와 함께 등재돼 있다. 고칠 때마다 그
줄을 지워 달라(게이트가 `FIXED?` 로 인쇄해 알려준다). 재현:

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_master_tables.py --no-build
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_simulate_pl_source_reaim.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_csm_amort_cell_provenance.py
```

### 1) copied_cell (3건) — 가장 급한 것. 연도 통째 복사 지문

에이비엘생명보험 `원수CSM상각`(항목4) 배포본 값이 **다음 해 값과 완전히 같다**:

| 분기 | 배포본 | viz | 같은 값을 가진 분기 |
|---|---|---|---|
| 2024.1Q | 22,447 | 2,313 | **2025.1Q = 22,447** |
| 2024.2Q | 44,994 | 4,652 | **2025.2Q = 44,994** |
| 2024.3Q | 66,762 | 7,155 | **2025.3Q = 66,762** |

배포본 2024 Q1~Q3 세 셀이 2025 Q1~Q3 와 1원도 다르지 않다. 우연일 확률이 없다.
단 **viz 쪽 값(2,313 / 4,652 / 7,155)도 미심쩍다** — 증분이 2.3k/분기인데 2024.4Q 가
88,926 으로 튄다(12배). 즉 둘 다 못 믿는 상태이니 **raw 확인 후 확정**해 달라.
raw: `data/dart/FY2024_Q*/raw/KR0070_에이비엘생명보험/`

### 2) basis_mix_csm_amort (5건) — YTD 누계 vs 당분기 혼입

동양생명 2024.2Q/3Q · 케이디비생명 2023.2Q/3Q · 에이비엘 2023.1Q.
동양생명은 **배포본 쪽이 깨끗한 YTD 계열**이다(2024: 64,196 / 129,439 / 196,194 / 259,987,
증분 ~64k 균일). viz 쪽 65,243·66,756 은 그 증분(=당분기)이다. 문제는
`기타생명장기원수손익` 이 **잔차 plug** 라 당분기 기준으로 계산돼 있어서, YTD CSM상각과
같은 행에 놓이면 항등식이 정확히 그 차이만큼 벌어진다는 점이다.
→ plug 를 배포본 기준으로 재계산해야 한다.

### 3) lob_sum_gap (5건) — 보험손익 ≠ ΣLOB

DB생명 2023.1Q(Δ4,179) · DB손해 2023.2Q(Δ6,869) · 메리츠화재 2023.1Q(Δ12,370)/2023.2Q(Δ71,547)
· 흥국화재 2025.1Q(Δ5,552).
DB손해 2023.2Q 의 잔차 6,869 는 `scripts/build_root_masters.py::_zero_other_expense` docstring 이
이미 "partial mis-extract" 로 명시하고 있다 — 기지 결함이 이제 게이트에 보인 것이다.
대부분 `기타영업수익`/`기타사업비용` 미추출이라 dual-form 의 adj 쪽을 평가할 수 없다.

### 4) sub_leg_gap (3건) — 생명장기손익 ≠ 원수+재보험

교보라이프플래닛 2024.4Q(Δ-6,261) · BNP카디프 2024.4Q(Δ-10,169)/2025.4Q(Δ-10,148).

### 5) pre_existing (10건)

재조준과 무관하게 이전부터 실패하던 항목. 등재부에 `class: pre_existing` 로 표시돼 있다.

**주의**: `build_root_masters.py` 의 `main()` 을 통짜로 돌리지 말 것(과거 PL 7,799→2,940행 절단).
`build_pl` 만 호출하고 전후 combo-diff 로 셀 손실 0 을 확인할 것. `validate_master_tables.py` 는
반드시 `--no-build`.

## 답변 (recipient 작성 — 처리 후)
