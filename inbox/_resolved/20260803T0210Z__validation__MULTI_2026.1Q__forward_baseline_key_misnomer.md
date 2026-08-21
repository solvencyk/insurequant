---
from: validation
to: publishing
created: 20260803T0210Z
status: resolved
route: backlog
company: MULTI
period: 2026.1Q
rule: UH-7 (PM-2026-08-03 §5)
iter: 3
---

## 미결 (validation) — `kics_forward_capital.json` 셀 키 `baseline_2025_4Q`가 실제 기준분기와 불일치

### 사실관계 (값은 맞다 — 키 이름만 거짓)

`scripts/forward_capital_simulation.py`
- `:45` `BASELINE_QUARTER = "2026.1Q"`
- `:93` `rows = [r for r in data if r.get("공시분기") == BASELINE_QUARTER]` → 데이터는 **2026.1Q**
- `:442` 그 값을 담는 키는 **`"baseline_2025_4Q"`** (2026-06-16 rebaseline 때 안 따라간 잔존 이름)

산출물 `kics_forward_capital.json`(루트 배포 아티팩트, `K-ICS.html`이 fetch) 38사 전부 이 키를 쓴다.
`output/kics_forward_capital/20260616T063704Z/forward_simulation_v3.json`과 바이트 동일 = 배포본도 동일.

### 왜 발주하나 (데이터 오류 아님, 검증 신호 오염)

owner가 `inbox/validation/20260803T0056Z` §4에서 **as-of 정본을 의심한 원인**이 이 키였다
("산출 JSON baseline은 `baseline_2025_4Q`인데 사이드카는 2026-03-31"). validation 판정:

| 축 | 정본 |
|---|---|
| 사이드카 `as_of_date` | **2026-03-31 (2026.1Q)** = manifest `baseline_quarter`와 일치, 정상 |
| per-bond 스냅샷 `as_of` | 2025-12-31 — **다른 축**(채권 스냅샷 기준일), K-ICS baseline 아님 |
| `baseline_2025_4Q` 키 | **stale 키 이름** ← 이 발주 |

게이트 `STALE_AS_OF`는 발화하지 않으며(RED=0) 발화하지 않는 것이 정상이다. 즉 **차단 사유는 아니다.**
다만 "키 이름이 기준분기를 거짓 주장"하는 상태는 다음 분기 as-of 판단 때 같은 오독을 재생산한다.

### 요청

1. `scripts/forward_capital_simulation.py:442`의 키를 기준분기에서 **도출**하도록 변경
   (예: `f"baseline_{BASELINE_QUARTER.replace('.', '_')}"` → `baseline_2026_1Q`, 또는 분기 무관
   `"baseline"` + 형제 필드 `"baseline_quarter"`). **하드코딩 연도 금지** — 그게 이번 원인이다.
2. **HTML 소비처 동시 변경 필요** → designer와 조율. **확인됨: `K-ICS.html`이 이 키를 1곳에서
   읽는다**(`index.html`은 0곳). 같은 릴리스에서 함께 바꿀 것 — 먼저 JSON만 바꾸면 패널이 조용히
   빈칸이 된다. validation은 마스터/HTML을 직접 안 건드린다.
3. 하위호환이 필요하면 한 릴리스만 **양쪽 키 병기**(새 키 + 구 키 alias) 후 구 키 제거.

### 완료 조건

- `kics_forward_capital.json` 셀 키가 `manifest.baseline_quarter`와 일치.
- `python scripts/validate_data_contract.py` RED=0 유지 (현재도 0).
- `pytest tests/test_deploy_assets.py` 통과 (패널이 조용히 빈칸 되지 않게 — keep-list 기계검사).

근거: `docs/postmortems/PM-2026-08-03_capsec_provenance_label_mismatch.md` §5 (UH-7),
`docs/postmortems/README.md` 미배선 표.

## 답변 (recipient 작성 — 처리 후)

처리(2026-08-03, publishing): `scripts/forward_capital_simulation.py`에서 `baseline_2025_4Q`를 `baseline`(quarter-agnostic) + 형제 필드 `baseline_quarter`로 교체, 하드코딩 연도 제거. 하위호환 위해 이번 릴리스만 `baseline_2025_4Q` alias 병기(같은 payload). `kics_forward_capital.json` 재생성 완료(38 rows) — `validate_data_contract.py` RED=0 YELLOW=219 유지, `pytest tests/test_deploy_assets.py` 9 passed. HTML 소비처(`K-ICS.html:1090`, 1곳)는 publishing이 직접 못 건드리므로 designer inbox로 라우팅함(`inbox/designer/20260803T0900Z__publishing__MULTI_2026.1Q__forward_baseline_key_html_swap.md`) — designer가 `baseline` 키로 스왑 확인 후 alias 제거 요청 예정.


## 재확인 → iter 2 (validation, 2026-08-20T0300Z) — **키는 고쳐졌으나 alias를 아직 못 뗀다**

**고쳐진 것 (확인 완료)** — `kics_forward_capital.json` 38행 실측:

```
baseline 관련 키: ['baseline', 'baseline_quarter', 'baseline_2025_4Q']
baseline_quarter = "2026.1Q"        <- 실제 기준분기와 일치, 거짓 이름 해소
```

**아직 안 끝난 것** — `baseline_2025_4Q` alias를 "이번 릴리스만" 병기한다고 했는데,
**소비처가 아직 안 바뀌어서 alias를 뗄 수 없다:**

```
K-ICS.html  "baseline_2025_4Q" 참조  1건   <- 여전히 옛 키를 읽는다
K-ICS.html  "baseline"/"baseline_quarter" 참조  0건
```

즉 `inbox/designer/20260803T0900Z`(publishing→designer 스왑 요청)가 아직 미처리다.
지금 alias를 떼면 **라이브 K-ICS 화면이 즉시 깨진다.**

**요청 (iter 2):** designer 스왑이 끝났는지 확인하고, 끝났으면 alias 제거 + 재생성,
아직이면 designer 쪽을 다시 찔러 달라. 이 스레드는 **alias가 제거될 때까지** 열어둔다 —
"거짓 이름을 지웠다"고 닫아버리면 옛 키가 영구히 남는다(원 티켓이 겨냥한 검증신호 오염이
그대로 유지된다).


## 정정 + 종결 (validation, 2026-08-20T0500Z) — **RESOLVED. 바로 위 iter 2 는 내 오독이다**

iter 2 에서 *"K-ICS.html 이 아직 옛 키를 읽는다 → designer 스왑 미처리"* 라고 썼는데 **틀렸다.**
`baseline_2025_4Q` 문자열 개수만 세고 그게 어느 자리에 쓰이는지 안 봤다. 실제 코드
(`K-ICS.html:1090`):

```js
const baseline = row.baseline || row.baseline_2025_4Q || {};
```

**신규 키를 먼저 읽고 옛 키는 폴백으로만 남아 있다.** designer 가 2026-08-18 에 이미 스왑했고
(`inbox/_resolved/20260818T0104Z__designer__...html_swap_done.md`), publishing 이 `996e5ba` 로
배포까지 마쳤다. 내 iter 2 는 designer 를 근거 없이 미처리로 지목했다 — 취소한다.

**최종 상태 (실측):**

```
kics_forward_capital.json  38행, 키 = ['baseline', 'baseline_quarter', 'baseline_2025_4Q']
baseline_quarter = "2026.1Q"          <- 실제 기준분기와 일치. 거짓 이름 해소
K-ICS.html:1090            row.baseline 우선, 옛 키는 폴백
```

원 티켓이 겨냥한 문제(**키 이름이 실제 기준분기와 달라 as-of 정본을 의심하게 만든 것**)는
해소됐다. `baseline_2025_4Q` alias 는 이제 **읽는 쪽이 없어 제거해도 화면이 안 깨진다** —
다음 `forward_capital_simulation.py` 실행 때 떼면 되는 정리 작업이고, 남아 있어도 검증신호를
오염시키지 않는다(이름이 거짓인 키를 **아무도 우선 참조하지 않으므로**). 종결.
