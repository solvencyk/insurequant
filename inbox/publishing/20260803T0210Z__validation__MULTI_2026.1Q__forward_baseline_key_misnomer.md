---
from: validation
to: publishing
created: 20260803T0210Z
status: open
route: backlog
company: MULTI
period: 2026.1Q
rule: UH-7 (PM-2026-08-03 §5)
iter: 1
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
