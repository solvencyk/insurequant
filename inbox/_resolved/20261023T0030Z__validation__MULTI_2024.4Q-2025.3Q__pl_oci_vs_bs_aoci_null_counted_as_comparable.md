---
from: validation
to: validation
created: 20261023T0030Z
status: resolved
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

**2026-10-23 (validation 32차, 커밋 전 작업트리)** -- 수정 완료, 재확인은 sender(오케스트레이터)가 닫는다.

- **원인 확인**: `_check_pl_oci_vs_bs_aoci` 의 「비교가능」 = `len(pl_dangi) - n_skip - len(rows)` 에 `값_당분기 None` 칸이 들어 있었다. 작업트리 실측: 항목25 374버킷 = 비교 258 + 공란 108 + BS 결측 8(8칸 전부 2023.1Q, 직전 분기 없음). 종전 인쇄 「비교가능 340」 중 108이 비교되지 않은 칸이었다.
- **전 버킷 시뮬레이션**(`data/_derived/remaining_20261022/e22_gate_cleanup/sim_oci_counting.py` -> `sim_oci_counting.txt`, 적재 8단계+작업트리): flag 집합은 계수 방식과 무관하게 동일(판정식 불변). 단계별 과대집계 = 공란 수(`b8c37fff` 109 · `5419a817` 122 · 지금 108). 공란 때문에 YELLOW 에서 사라진 행은 4건 -- NH농협손해 2023.4Q(+40,909.6) · 농협생명 2024.4Q(-31,361.1) · 동양생명 2024.4Q(+35,860.7) · KB손해 2023.4Q(+77,358.0). 값이 고쳐져 닫힌 행은 교보 2023.4Q 1건뿐.
- **수정**(`scripts/validate_master_tables.py`): 공란을 `n_blank` 로 따로 세고 인쇄를 「비교한 258건 중 tol 이내 232건 | 비교 못 함: 단일분기 공란 108건 + BS 결측 8건」 으로 바꿨다. SUMMARY `oci_vs_bs_aoci:26Y` -> `26Y/108blank/8bsskip`(`counts_out` 인자, 반환값 불변). 게이트 전후 diff = 6번 섹션 한 줄 + SUMMARY 한 필드뿐(YEL 26줄 동일).
- **시험·골든**: `tests/test_master_tables_golden.py::test_oci_vs_bs_aoci_counts_blank_cells_as_not_compared` 신설(합성 마스터 4칸, 계수 2/1/1/1 + flag 집합 박제; 계수식 변이 시 FAIL 확인). `master_tables_golden.json` 은 `--update`(이동 = 이 필드 하나, 수정 전 fixture 가 직전 상태와 일치). 관련 시험 250개 통과.
- **3번(같은 사각의 다른 검사)**: `load_pl_dangi` 소비처는 이 함수 하나뿐이고 `값_당분기` 를 읽는 다른 `_check_*` 도 없다(`validate_master_tables.py`·`validate_data_contract.py` grep 전수). 다른 검사들의 SKIP 은 SUMMARY 에 `S` 로 따로 세어진다(closing `0S` · pl_bridge `2657S` · tax22_src `361S` · csm_amort `4S`).
- **참고(게이트 입력 아님)**: 지금 공란 108칸(4Q 55) 중 누계 차로 재구성되는 17칸에서 6칸이 tol 초과(농협생명 2024.4Q -39,298 · 미래에셋생명 2023.4Q -36,084 · 동양생명 2024.4Q +32,151 · 한화생명 2025.3Q -22,291 · 농협생명 2025.3Q · 흥국생명 2025.3Q). 공란이 정당한 이음매인지 판정은 parser/owner 몫.
- 함께 한 JOB 1(죽은 등재 7줄 철거) 기록: `docs/changelog_validation.md` 2026-10-23 (32차).
