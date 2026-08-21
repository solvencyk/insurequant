---
from: orchestrator
to: parser
created: 20260821T1900Z
status: open
route: reparse
company: MULTI
period: ALL
rule: CSM_WATERFALL_BALANCE_INCOMPLETE
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

**`scripts/validate_csm_waterfall.py` 가 exit 1 로 실패하고 있는데, 이 게이트를 부르는 곳이
아무 데도 없어서 아무도 몰랐다.**

2026-08-21 에 push 훅에 게이트를 전수 배선하다 발견했다. `scripts/validate_*.py` 8개 중
훅이 부르던 것은 `validate_data_contract` 하나뿐이었고, 나머지를 전수 실행해 보니
**3개는 통과 중인데 미배선**(바로 배선함), **1개는 실패 중인데 미배선**(이 티켓)이었다.

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_csm_waterfall.py
  → exit 1, 3초
  FAIL <회사명>: balance_incomplete:assumption
  → needs_reparse_for_new_business: run run_ifrs17_csm_reconcile_loop.py
```

게이트 자신이 다음 단계까지 알려주고 있다(`run_ifrs17_csm_reconcile_loop.py`). 그 루프가
언젠가부터 안 돌고 있었던 것으로 보인다.

## 부탁 (수신자가 할 일)

1. `balance_incomplete:assumption` 이 걸린 (회사, 분기)를 **전수 열거**해라. 몇 건인지,
   어느 분기에 몰려 있는지부터.
2. 게이트가 지시하는 `run_ifrs17_csm_reconcile_loop.py` 를 돌릴 수 있는 상태인지 확인하고,
   돌려서 닫히는 것과 안 닫히는 것을 나눠라.
3. **안 닫히는 것은 원인을 원문까지 내려가서 적어라.** "재파싱 필요" 로 끝내지 말 것.
4. 게이트가 exit 0 이 되면 알려라 — `tests/test_push_gate_wiring.py` 의 매니페스트에서
   `NOT_A_PUSH_GATE` → `WIRED` 로 옮기고 훅 1c 단계에 넣는다.

## 참고 — 지금은 이 게이트가 push 를 막지 않는다 (일부러)

지금 배선하면 **모든 push 가 막힌다.** 그래서 `tests/test_push_gate_wiring.py` 의
`NOT_A_PUSH_GATE` 에 **사유를 적어서** 등재해 뒀다. 다만 같은 파일의
`test_unwired_gates_still_fail` 이 매 push 마다 이 스크립트를 실제로 돌려서
**"아직도 실패하는지"를 재확인**한다 — 네가 고쳐서 통과시키는 순간 그 테스트가 실패하면서
배선하라고 막는다. 즉 이 티켓을 조용히 묻어둘 수는 없다.

## 하지 말 것

- 게이트 임계를 낮추거나 실패 케이스를 skip 처리해서 exit 0 을 만들지 말 것.
- `build_root_masters.py` 의 `main()` 통짜 실행 금지(PL 절반 파괴 전례). `build_csm` 개별호출
  + combo-diff. `validate_master_tables.py` 는 반드시 `--no-build`.
- `insurequant_master_tables.xlsx` 는 전체 재생성 금지 — `scripts/sync_master_xlsx_sheet.py`
  로 해당 시트만 cherry-pick (2026-08-21 현재 8개 시트 전부 마스터와 0 drift 상태다,
  네가 마스터를 바꾸면 그 시트만 다시 맞춰라).
