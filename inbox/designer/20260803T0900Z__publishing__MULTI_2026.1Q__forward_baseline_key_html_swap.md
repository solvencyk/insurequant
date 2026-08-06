---
from: publishing
to: designer
created: 20260803T0900Z
status: open
route: escalate
company: MULTI
period: 2026.1Q
rule: UH-7
iter: 1
---

## 미결 (sender 작성)

`kics_forward_capital.json` 셀 키가 `baseline_2025_4Q` → `baseline`로 바뀌었다 (validation
inbox `20260803T0210Z`, 원인: 하드코딩된 분기 이름이 2026-06-16 rebaseline 이후 실제 분기와
어긋남). `K-ICS.html:1090`이 이 키를 읽는 유일한 소비처.

```js
const baseline = row.baseline_2025_4Q || {};
```

### 지금 해야 할 것

이번 릴리스는 **양쪽 키가 다 들어있다** (`baseline_2025_4Q`는 alias, `baseline`과 같은
payload) — 지금 당장 HTML을 안 바꿔도 패널이 빈칸이 되지는 않는다. 급하지 않지만, 다음에
HTML을 만질 때 같이 바꿔달라:

```js
const baseline = row.baseline || row.baseline_2025_4Q || {};
```

바꾼 뒤 확인되면 publishing에 알려달라 — 확인되면 다음 `forward_capital_simulation.py` 실행
때 `baseline_2025_4Q` alias를 제거한다(영구 유지 안 함).

### 참고

- `row.baseline_quarter`(새 형제 필드)가 실제 분기 문자열("2026.1Q") — 화면에 분기 라벨을
  하드코딩했다면 이걸로 대체 가능.
- `python -m pytest tests/test_deploy_assets.py` 통과 확인됨 (keep-list 대상 아님, 이 파일은
  구조 변경일 뿐 deploy-asset 목록에는 영향 없음).

## 답변 (recipient 작성 — 처리 후)
<처리 결과 1~3줄. 못 했으면 왜 못 했는지.>
