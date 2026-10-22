---
from: validation
to: validation
created: 20261023T0030Z
status: open
route: gate-fix
lane: ifrs17
company: MULTI (KR0087 KR0104 + every blanked single-quarter cell)
period: 2024.4Q-2025.3Q
iter: 1
---

## 미결 (sender 작성)

e20 PL 최신 비교열 적재(미커밋)를 독립 검증하다 게이트 자신의 사각을 하나 찾았다. 적재 자체는 PASS(증거 `data/_derived/remaining_20261022/e20_held_and_remaining/verify/`).

`scripts/validate_master_tables.py::_check_pl_oci_vs_bs_aoci` 가 PL 항목25 의 `값_당분기` 가 None 인 칸을 `continue` 로 건너뛰는데(SKIP-on-missing), 출력 문구의 「비교가능 N건은 tol 이내」 는 `len(pl_dangi) - n_skip - len(rows)` 로 센다. `pl_dangi` 에는 None 칸이 들어 있어 **비교하지 않은 칸이 「tol 이내」로 집계된다**.

- 실측(`verify/v14_nullcount.txt`): 항목25 374행 중 값_당분기 None 이 적재 전 110 → 후 122. 「비교가능 350건」 중 122건은 아예 비교되지 않았다.
- 효과: 동양생명 2024.4Q(resid +35,861)·농협생명 2024.4Q(resid −31,361)가 YELLOW 목록에서 빠졌다(23→21Y). 해소가 아니라 4Q 단일분기를 공란으로 만들어서 사라진 것이다(연간 새 판 − 9개월 옛 판 이음매, 정당한 공란). 그런데 게이트 SUMMARY·골든 fixture 는 이를 「개선」으로 읽는다.
- 같은 모양의 사각이 이 셀 말고 다른 YELLOW/RED 룰에도 있는지 `값_당분기 is None` 을 건너뛰는 모든 `_check_*` 를 조사한다.

## 하면 되는 일

1. `_check_pl_oci_vs_bs_aoci` 를 「비교한 칸 / 단일분기 공란으로 비교 못 한 칸 / BS 결측으로 못 한 칸」 3분할로 출력하고, 비교 불가 칸 수를 SUMMARY 에 별도 필드(예: `oci_vs_bs_aoci:21Y/122blank`)로 싣는다. 「tol 이내」 문구는 실제 비교한 칸만 센다.
2. 룰을 고치기 전에 전 버킷 시뮬레이션(양방향)으로 flagged 집합이 변하지 않는지 확인한다. 골든(`tests/test_master_tables_golden.py`)은 `--update` 로 재생성하고 커밋에 이유를 남긴다.
3. 같은 사각이 있는 다른 검사(`load_pl_dangi` 소비처 전부)를 열거한다.

## 답변 (recipient 작성 — 처리 후)
