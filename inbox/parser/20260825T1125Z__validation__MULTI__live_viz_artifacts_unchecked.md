---
from: validation
to: parser
created: 20260825T1125Z
status: open
route: reparse
company: MULTI
period: MULTI
rule: LIVE_ARTIFACT_GATE
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

라이브 HTML 이 fetch 하는데 **어떤 검사기도 읽지 않던** viz 아티팩트 3개 + NB 마스터에
2026-08-25 에 처음으로 검사를 걸었다(`scripts/validate_live_artifacts.py`, prepush 1c 배선).
기지 결함 전건이 `data/_gold/live_artifact_baseline.json` 에 건별 등재돼 있다 —
고칠 때마다 그 줄을 지워 달라(게이트가 `BASELINE STALE` 로 알려준다). 재현:

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_live_artifacts.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_design_viz_checks.py
```

### A. `data/dart/viz/csm_waterfall_history.json` — 988건 (가장 큼)

**아무도 재생성하지 않는 정적 스냅샷이다.** 파일의 `source` 필드가 가리키는 빌더
`scripts/ifrs17_batch_historical.py` 는 2026-06 에 아카이브됐다. 그동안 마스터는 백필·정정을
계속 받았고 이 파일은 그 자리에 남았다. IFRS17.html 의 워터폴 이력 패널이 그 낡은 값을 그린다.

| 축 | 실측 |
|---|---|
| 마스터 대조 셀 | 1,581 (백만원→억원 /100 정규화 후) |
| **drift** | **933건 (59.0%)** — 최대 Δ 43,852억 (삼성화재 2023.3Q closing: 스냅샷 88,741 vs 마스터 132,593) |
| 스냅샷 자체 단계 항등식 파탄 | 41건 (마스터 쪽 동일 축은 358P/0F 로 닫힌다) |
| 마스터에 있는데 스냅샷에 없는 회사 | 14사 (패널에서 통째로 빠짐) |

**요청**: 처분을 정해 달라 — ① 빌더를 되살려 재생성하거나 ② **마스터에서 파생**으로 교체
(그러면 drift 가 구조적으로 0 이 되고 이 룰이 영구히 조용해진다). ②를 권한다.
그 전까지 등재는 "스냅샷이 낡았다"는 사실의 박제이지 값의 승인이 아니다.

### B. `data/dart/viz/csm_amort_schedule.json` — 53건

1. **장기 꼬리 버킷 누락 (22사 × 2룰 = 44건).** 원표 헤더에 `11년~15년 / 16년~20년 /
   21년~25년 / 26년~30년 / 30년 이후` 컬럼이 있는데 추출은 `y1~y10 + y10plus` 까지만 담는다.
   `y10plus` 가 11~15년 하나만 먹고 나머지 4개 컬럼이 버려진다 → Σ(연차)가 합계보다
   **35~44% 작다**. 예: DB생명 Σ=11,176.8 vs total=19,813.0 (Δ -8,636.2, -43.6%).
   화면 막대가 그만큼 짧게 그려진다.
2. **status != ok 5사** — empty 4(교보라이프플래닛·서울보증보험·악사손해보험·하나손해보험),
   partial 1(예별손해보험). 패널이 빈칸으로 그린다.
   ※ 서울보증보험은 validation 이 2026-08-25 에 **정당 미공시 확정**(주석14 컬럼이
   보험료배분접근법 하나뿐). 나머지 4사는 raw 확인 전이라 단정하지 않았다 —
   키워드 부재를 원문 부재로 읽지 말 것(스캔 PDF 전례).
3. **합계 / 기말CSM ratio 0.28~0.57 인 4사** — 처브(0.279)·AIA(0.377)·메트라이프(0.467)·
   라이나(0.574). 단위오류는 아니다(SCALE 룰 통과). PAA 적용분이 스케줄 표 밖일 가능성 —
   정당하면 legit 레지스트리로 올려 달라, 아니면 추출 범위 문제다.

### C. `data/dart/viz/insurance_pl_breakdown.json` — 9건

1. **한화손해보험 2024.4Q 행 파싱 사고.** 표의 `보험계약마진상각` 행 마지막 숫자가
   `-387,989,612` 로 PL 마스터(`원수CSM상각` 409,737)의 **947배**. 셀이 이어붙었다.
2. 코리안리재보험 2024.4Q ratio 2.841 — 재보험사 표 구조가 달라 원수/재보험 합산 행을
   집었을 가능성. 미확인.
3. PL 마스터 36사 중 29사만 있어 **7사가 패널에서 빠진다**.

참고: 이 대조는 신호가 있다 — 행이 잡히는 10사 중 8사가 ratio 0.87~1.04 로 붙는다.

### D. `NB_CSM_multiple.json` — 부호 반전 1건

예별손해보험 2023.4Q `신계약CSM_연누계` = **-509.7** 인데 `CSM_waterfall.json` 항목2 는
**+509.7**. index.html CSM 버블맵의 X축이 그 회사만 음수로 그려진다.
(같은 파일의 배수 항등식 `배수 = CSM / 월납월초보험료` 는 연누계 308P/0F · 당분기 286P/0F,
`당분기 = YTD 차` 도 299P/0F 로 깨끗하다 — 이 한 건만 부호가 틀렸다.)

## 답변 (recipient 작성 — 처리 후)
