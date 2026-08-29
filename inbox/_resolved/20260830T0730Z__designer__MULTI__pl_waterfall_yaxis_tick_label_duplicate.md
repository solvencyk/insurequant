---
from: designer
to: designer
created: 20260830T0730Z
status: resolved
route: backlog
company: MULTI
period: MULTI
iter: 1
---

## 미결 (designer 자체 발견 — 20260830T0600Z LOB 작업 중 실측)

**`IFRS17.html` Panel 5 워터폴의 y축 눈금 라벨이 중복해서 찍힌다.**

눈금 간격(`plYStep`)이 0.05조·0.025조로 잡히는 (회사,분기,모드)에서 축 포매터가
`maximumFractionDigits:1` 로 고정돼 있어 서로 다른 눈금이 같은 문자열이 된다.

```
코리안리 2026.2Q 당분기: min=-100000 max=200000 interval=50000
  라벨 -> ["△0.1", "△0.1", "0", "0.1", "0.1", "0.2", "0.2"]   <- 3쌍 중복
```

### 범위 (전수 측정 2026-08-30)

`plBuildSteps` 로 36사 x 전 분기 x 2필드를 돌려 축 계산을 그대로 재현했다.

| | 건수 |
|---|---|
| 중복이 생기는 (회사,분기,모드) | **213** |
| 그중 비KR1000 | **197** |

즉 **코리안리 전용 문제가 아니라 원래 있던 표시 버그**다. 워터폴은 축 범위를 고정
(`plYMin`/`plYMax`/`plYStep`)하는데, 라벨 소수자리만 그 스텝과 무관하게 1로 박혀 있다.

### 왜 그때 안 고쳤나

20260830T0600Z 티켓의 검수 기준이 **"코리안리 외 다른 회사 회귀 0"** 이었다. 이걸 고치면
비KR1000 197건의 화면 축 라벨이 같이 바뀌어 그 기준과 정면으로 충돌한다. 그래서 손대지 않고
분리했다. **화면 숫자(막대·표 값)는 안 바뀌고 축 눈금 글자만 바뀐다.**

### 제안 (한 줄)

`renderPlWaterfall` 의 `yAxis.axisLabel.formatter` 가 쓰는 소수자리를 `plYStep` 에서 도출한다.

```js
const plYDp = Math.min(2, Math.max(0, Math.ceil(-Math.log10(plYStep/1e6))));
// formatter: ... .toLocaleString("ko-KR", { maximumFractionDigits: plYDp })
```

착수 시 확인할 것: ① 스텝이 1조 이상인 회사에서 라벨이 길어지지 않는지 ② 전 39사 x 2모드
순회로 중복 0 확인 ③ y축 폭(`grid.left=56`)에 소수 2자리가 들어가는지.

## 답변 (recipient 작성 — 처리 후)


## 답변 (orchestrator 처리 — owner 지시로 즉시 수정)

**눈금 간격에서 소수 자릿수를 역산하도록 고쳤다.**

원인: `IFRS17.html:964` 가 `interval: plYStep` 으로 간격을 직접 정하는데(1/2/2.5/5/10 x 10^n
스냅), `966` 의 포매터는 `maximumFractionDigits:1` 로 고정이었다. 간격이 0.05조·0.25조로
잡히는 회사에서 이웃 눈금이 같은 라벨이 됐다.

수정: `plYStep/1e6`(조)을 정확히 표현하는 최소 자릿수를 구해 `min/maximumFractionDigits`
양쪽에 넣는다. 0~3자리로 제한.

```
간격 0.05조 -> 2자리   0.05 · 0.10 · 0.15
간격 0.25조 -> 2자리   0.25 · 0.50 · 0.75      <- 1자리면 0.3/0.5/0.8 로 왜곡
간격  0.5조 -> 1자리   0.5 · 1.0 · 1.5
간격  1.0조 -> 0자리   1 · 2 · 3
간격  2.5조 -> 1자리   2.5 · 5.0 · 7.5
간격  5.0조 -> 0자리   5 · 10 · 15
```

전 간격에서 중복이 사라지고, 2.5 계열의 반올림 왜곡(0.25->"0.3")도 같이 해소된다.

검증: `pytest tests/test_deploy_assets.py` 10/10 · 인라인 script 2블록 JS 문법 통과 ·
`validate_data_contract` RED=0.

**분리 발주가 옳았다.** 이 수정은 213건 중 197건이 코리안리 밖이라, LOB 티켓의 "다른 회사
회귀 0" 기준 안에서는 할 수 없었다. 티켓을 나눈 designer 판단이 정확했다.
