---
from: owner
to: designer
created: 20260820T0430Z
status: resolved
route: backlog
company: MULTI
period: MULTI
iter: 1
---

## 미결 (sender 작성) — IFRS17.html의 죽은 fetch 1건 제거

owner가 NB CSM 진단파일 건을 drop 결정(`inbox/_resolved/20260616T0230Z`)하면서 확인된 부수 건이다.
**데이터 문제가 아니라 순수 정리다.**

`IFRS17.html`이 `csm_waterfall_history.json`을 **받아만 놓고 안 쓴다.**

```
L260   hist: dataPaths("../data/dart/viz/csm_waterfall_history.json", "data/dart/viz/...")
L275   const charts = { ..., hist: null };      ← Chart.js 인스턴스(다른 것)
L278   const payload = { ..., hist:null, ... }
L284   const ix = { ..., hist: new Map(), ... } ← 적재는 되는데 읽는 코드가 없음
L1525  // 기존 csm_waterfall_history.json은 stale(...)이라 폐기.   ← 이미 갈아탄 흔적
```

Panel 6(CSM 시계열)은 **이미 `CSM_waterfall.json`(`ix.wfx`)으로 갈아탔고**, 그 주석이 L1525에
그대로 남아 있다. `.hist` 참조는 전부 `charts.hist`(차트 인스턴스명)라 `ix.hist`/`payload.hist`는
**아무도 안 읽는다.**

### 요청

`hist` 경로·payload·ix 엔트리를 걷어내 달라. 사용자 눈에 보이는 변화는 없고, **매 페이지 로드마다
쓰지도 않는 JSON 요청 한 건이 사라진다.**

### 주의

- `charts.hist`는 **남겨야 한다** — Panel 6 차트 인스턴스 이름이라 이름만 같고 별개다.
  이걸 같이 지우면 Panel 6이 죽는다.
- `data/dart/viz/csm_waterfall_history.json` **파일 자체는 지우지 말 것**. `build_tidy_exports.py`·
  `check_nb_csm_history.py`·`ifrs17_promote_history_to_measurement.py`·`verify_parser_change.py`가
  아직 읽는다(오프라인 진단용). 화면에서만 끊는 것이다.
- 변경 후 `node --check`로 인라인 스크립트 문법 확인 + Panel 6이 정상 렌더되는지 실측할 것.

## 답변 (recipient 작성 — 처리 후)

`IFRS17.html`에서 죽은 `csm_waterfall_history.json` fetch 경로를 제거했다.

- `PATHS.hist`(L260), `payload.hist`(L277), `ix.hist`(L283) 엔트리 삭제.
- boot()의 `Promise.all` 배열에서 `fetchJsonSafe(PATHS.hist)` 호출과 `histx` 구조분해 삭제,
  `payload.hist=histx` 대입 삭제.
- `charts.hist`(Chart.js 인스턴스명, Panel 6 사용)와 `destroyCharts()`의 `"hist"` 키는
  그대로 보존 — 이름만 같고 별개.
- `data/dart/viz/csm_waterfall_history.json` 파일 자체는 미변경(오프라인 진단 스크립트가 계속 읽음).

검증: `node --check`로 인라인 스크립트 문법 통과. 로컬 http 서버로 IFRS17.html을 띄워 메리츠화재
선택 후 콘솔 에러 없음 확인, `#canvasHist` 정상 렌더(Panel 6 CSM 시계열 표시됨), 네트워크 요청에서
`csm_waterfall_history.json` 요청이 사라진 것 확인.
