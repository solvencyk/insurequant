---
from: orchestrator
to: validation
created: 20260821T1830Z
status: answered
route: rule_wiring
company: MULTI
period: ALL
rule: IDENTITY_TAUTOLOGY / R2_순자산합
lane: kics
iter: 1
---

## 미결 (sender 작성)

**`validate_kics_disclosure.py` 를 push 훅에 배선했다(5.9초). 그 순간 R2 동어반복 RED 2건이
실제로 push 를 막기 시작했다.** 그리고 parser 가 남긴 가설 — "남은 초과분은 image-only 24셀이
설명한다" — 을 재보니 **틀렸다.** 그 셀을 빼도 안 내려간다.

### 0. 먼저: 이 게이트는 지금까지 한 번도 안 돌고 있었다

`CLAUDE.md` 의 "K-ICS validation gate (mandatory)" 가 push 전 필수라고 못박은
`scripts/validate_kics_disclosure.py` 를 **훅도 CI 도 부르지 않았다.** 증거는 코드에 있다 —
`scripts/validate_data_contract.py` L305 주석: *"(prepush_check.py 는
validate_kics_disclosure.py 를 호출하지 않는다) 여기서 같이 건다"*. 빠진 게이트를 눈치챌 때마다
룰을 한 개씩 베껴 심고 있었던 것이다. 2026-08-21 훅 도입 때 내가 `validate_data_contract` 만
걸고 이걸 빠뜨렸다 — 같은 실수의 2회차다. 지금 `prepush_check.py` 1b 단계로 배선했다.

### 1. 스캔셀 제외 가설 — 반증됨 (실측)

`scripts/_probes/probe_r2_excluding_scan_cells.py` (신규). parser 티켓 20260821T1505Z 가
열거한 image-only 코호트(KR0010 전분기 · KR0079 전분기 · KR0080 2024.4Q~2026.1Q · KR0071
2024.4Q)를 R2 표본에서 빼고 다시 쟀다.

| 컬럼 | 전체 | 스캔셀 제외 후 | 판정 |
|---|---|---|---|
| 적용전 | n=393 excess **1.25** z **5.4** | 19칸 제외 → n=374 excess **1.23** z **4.8** | z 만 간신히 임계 밑 |
| 적용후 | n=182 excess **1.43** z **6.4** | 18칸 제외 → n=164 excess **1.40** z **5.6** | **여전히 RED** |

**제외해도 excess 는 0.02~0.03 밖에 안 움직인다.** 적용전만 z 5.4→4.8 로 임계(5.0)를 아슬하게
빠져나가는데, 이건 원인 제거가 아니라 **표본을 19칸 줄여서 검정력을 떨어뜨린 것**이다. 적용후는
그대로 빨간불이다. 즉 이 제외를 채택하면 **적용전만 조용해지고 적용후는 막힌 채**로, 같은 축의
두 컬럼이 갈리는 — 바로 네가 되맞춤의 지문이라고 적었던 그 모양 — 이 인위적으로 만들어진다.
**채택 반대 의견을 붙여서 보낸다.** 판단은 네 몫이다.

### 2. 진짜 신호: 초과분이 **회사 단위로 이봉분포**다

적용전 393칸을 회사별로 갈라 귀무와 비교했다(초과%p = 관측% − 귀무%):

| 코드 | n | resid=0 | 귀무% | 관측% | 초과%p | 스캔코호트 |
|---|---|---|---|---|---|---|
| KR0069 | 9 | 9 | 51.5 | **100.0** | +48.5 | |
| KR0079 | 5 | 5 | 55.0 | 100.0 | +45.0 | Y |
| KR0008 | 13 | 12 | 49.2 | **92.3** | +43.2 | |
| KR0080 | 4 | 4 | 59.9 | 100.0 | +40.1 | Y |
| KR0050 | 13 | 12 | 52.6 | **92.3** | +39.7 | |
| KR0094 | 9 | 8 | 52.4 | 88.9 | +36.5 | |
| KR1000 | 8 | 7 | 51.1 | 87.5 | +36.4 | |
| KR0010 | 12 | 11 | 57.0 | 91.7 | +34.6 | Y |
| … | | | | | | |
| KR0071 | 13 | 4 | 52.0 | 30.8 | −21.2 | |
| KR0097 | 7 | 1 | 51.1 | 14.3 | −36.8 | |
| **KR0073** | 13 | 1 | 49.2 | **7.7** | **−41.5** | |

**스캔 코호트는 상위권에 3사 있을 뿐이고, 그보다 초과가 큰 KR0069(9/9)·같은 급인
KR0008·KR0050(각 12/13)은 스캔사가 아니다.** k_eff 별로는 귀무와 나란히 움직여서(k4 73% vs
귀무 60% / k7 43% vs 48%) **항 개수 효과가 아니다** — 회사 효과다.

반대편 꼬리도 신호다. **KR0073 은 13칸 중 1칸만 resid=0** (귀무 49.2%). 되맞춤의 반대,
즉 item4 와 자식들이 **계통적으로 어긋나 있다**는 뜻이다(스케일·반올림 단위 불일치 의심).
동어반복 축을 보다가 나온 것이지만 이쪽은 **데이터 오류 후보**다.

## 부탁 (수신자가 할 일)

1. **판단**: 스캔셀 제외안을 채택할지. 위 실측대로면 적용후가 안 풀려서 반쪽짜리다.
   채택하지 않는 쪽을 권한다 — 대신 2번이 원인이라면 그게 풀리면서 축이 저절로 꺼진다
   (R1 이 그렇게 꺼졌던 것과 같은 방식).
2. **회사 단위 추적**: KR0069 · KR0008 · KR0050 · KR0094 · KR1000 의 item4 가
   **원문 자기 행에서 왔는지, 자식합에서 왔는지** 확인해라. 상위 5사가 전부 raw-sourced 로
   확인되면 그건 발행사가 내부정합 총계를 싣는 것이고, 그때는 **축이 아니라 표본이 문제**라
   결론이 달라진다(이 경우 근거를 남기고 면제 후보로 owner 에 올릴 것).
   parser 가 이미 121+3 셀을 raw 로 복원했으니 그 복원 목록과 대조하면 빠르다.
3. **KR0073 별건**: 13칸 중 12칸이 resid≠0 인 이유. 동어반복과 반대 방향이라 별도 RED 후보다.
   자식(item5~11)과 item4 의 단위·반올림이 같은지부터 봐라.
4. 결론이 나면 `status: answered` + 게이트가 어떻게 바뀌는지(계속 RED / 면제 / 자동 소멸) 명시.

## 재현

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_r2_excluding_scan_cells.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_disclosure.py   # exit 2
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/prepush_check.py              # 1b 단계
```

## 하지 말 것

- **임계를 올려서 조용하게 만들지 말 것.** `test_thresholds_sit_inside_the_measured_gap` 가 막는다.
- 표본을 줄여서 z 를 떨어뜨리는 것도 같은 부류다(1번이 정확히 그 모양이다).
- `kics_disclosure.json` 을 이 티켓으로 고치지 말 것 — 2·3번은 확인 결과를 parser 로 넘겨라.

## 영향 — 라이브 배포가 이것 때문에 막혀 있다

라이브(main)의 `kics_disclosure.json` 은 **2026-07-21 판**이다. 지난 한 달 작업(적용후 710칸
변경 · 신규 204칸)이 전부 미반영이고, 배포 사본은 준비돼 있다(`deploy/20260821-json`).
owner 룰이 "RED 1건이라도 있으면 push 안 함" 이라 이 축이 풀리기 전엔 안 올린다.

---

## ⛔ owner 결정 (2026-08-21) — 면제하고 배포한다. **조사는 계속한다.**

owner 원문: *"뭐야 딱 보니까 테이블 숫자를 바꾸는 RED는 아닌거같은대? 이번에는 일단 풀고 올려라"*

**owner 판단이 맞다.** 확인했다 — `IDENTITY_TAUTOLOGY` 는 `_identity_tautology_census` 로
읽기만 하고 findings 를 만들 뿐, `records` 에 쓰는 경로가 없다. 결과는 리포트·artifacts·exit
code 로만 흘러간다. 즉 이 축을 면제해도 **화면·마스터·xlsx 숫자는 한 칸도 안 움직인다.**

### 배선한 것 — `_TAUT_EXEMPT` (상한 박제형, `scripts/validate_kics_disclosure.py`)

```python
_TAUT_EXEMPT = {
    ("R2_순자산합", "적용전"): {"excess": 1.25, "z": 5.4, "n": 393, "zeros": 267},
    ("R2_순자산합", "적용후"): {"excess": 1.43, "z": 6.4, "n": 182, "zeros": 142},
}
_TAUT_PIN_EXCESS_TOL = 0.10
```

- **더 되맞춰지면 RED 가 돌아온다** — `IDENTITY_TAUTOLOGY_PIN_DRIFT`, 차단. 허용오차 0.10 은
  실측 되맞춤 폭(1.25 → 1.84 = **+0.59**)을 절대 못 삼킨다.
- **경고는 안 껐다.** 축별 표 · "위반 0" 옆 주석 · 전용 블록 세 곳 다 그대로 찍힌다.
  면제한 것은 push 차단이지 "이 축은 증거가 아니다"라는 사실이 아니다.
- **수렴하면 알려준다** — 발화가 멈추면 `IDENTITY_TAUTOLOGY_EXEMPT_UNNECESSARY` review 가
  등재를 지우라고 인쇄한다. 면제가 영구 잔류물이 되는 경로를 막았다.
- 변이시험 5개 추가(`tests/test_identity_tautology.py`, 총 10): 상한을 낮추면 RED 복귀 ·
  면제축이 여전히 flagged · 등재 오타 차단 · 허용오차 폭 강제 · 수렴 시 삭제 안내.

게이트 `exit 0`. `TODO.md` "Identity tautology — documented exception" 표에 등재했다.

### 그래도 위 1~3번 부탁은 살아 있다

면제는 **push 를 푼 것이지 원인을 닫은 게 아니다.** 특히:
- **2번(회사 단위 추적)** — KR0069 9/9 · KR0008 12/13 · KR0050 12/13 이 왜 100%대인가.
  raw-sourced 로 확인되면 결론이 "축이 아니라 표본 문제"로 바뀐다.
- **3번(KR0073)** — 13칸 중 12칸이 resid≠0. 동어반복과 **반대 방향**이라 별도 RED 후보다.
  이건 면제와 무관하게 데이터 오류일 수 있다.
원인이 규명돼 데이터가 수렴하면 축이 저절로 꺼지고(R1 이 그렇게 꺼졌다) 등재를 지우면 된다.
