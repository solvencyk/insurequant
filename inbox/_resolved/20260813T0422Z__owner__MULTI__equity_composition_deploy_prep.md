---
from: owner
to: publishing
created: 20260813T0422Z
status: resolved
route: backlog
company: MULTI
period: 2023.1Q-2026.1Q
iter: 1
---

## 미결 (sender 작성)

신규 마스터 **`equity_composition.json`**(AOCI + 해약환급금준비금 등 자본구성) 배포 준비.
스펙: `inbox/parser/20260813T0422Z__owner__MULTI__aoci_equity_composition_master.md`.

**착수 시점 = 파서가 1차 마스터를 올린 뒤.** 지금은 아래 P-1만 선반영 가능.

### P-1. keep-list 등재 (지금 해도 되는 유일한 항목 — 단, 파일 생성 후)

배포 keep-list에 **2개** 추가:

```
equity_composition.json
equity_composition_provenance.json
```

**빠지면 패널이 조용히 빈칸이 된다** — 루트 JSON 3개(`kics_tier1/tier2_utilization`,
`kics_forward_capital`)가 빠져서 같은 사고가 났던 전례가 있다.
`pytest tests/test_deploy_assets.py`가 keep-list를 기계 검사하므로, 파일이 아직 없는 상태로
등재하면 테스트가 깨진다 → **파서 산출 도착 후 등재 + 테스트 동반 실행.**

### P-2. 마스터 xlsx 재생성

마스터 JSON이 갱신되면 `insurequant_master_tables.xlsx` 재생성 필수.
신규 시트로 자본구성이 들어가야 owner가 xlsx에서 손검증할 수 있다.

- 상시 디폴트 = 공식 `xlsx` skill. `build_csm_waterfall_master.py` 실행 금지.
- **마스터 xlsx를 openpyxl로 load+save 하지 말 것** — 값열이 수식이라 캐시값이 전부 wipe되고
  `data_only` 읽기가 None이 된다. 별도 파일로 작업.
- 신규 시트 컬럼 규약은 기존 시트(CSM/PL)와 동일하게 맞출 것.

### P-3. 게이트 순서

push 전 체인에 `validate_data_contract.py`가 이 마스터를 실제로 검사하는지 확인.
validation이 배선 위치를 답변에 적기로 돼 있다
(`inbox/validation/20260813T0422Z__owner__MULTI__equity_composition_rules_and_gate.md`).
**RED 1건이라도 있으면 push 안 한다.** fixable RED은 exception 처리하지 말고 해당 stage로 route.

### P-4. 스키마 확정 통지 → designer

designer가 패널 목업을 먼저 만들고 스키마 확정 후 고정하기로 돼 있다
(`inbox/designer/20260813T0422Z__owner__MULTI__aoci_panel_spec.md`).
마스터 항목번호/키가 확정되면 **designer inbox에 schema-delta 통지**를 넣을 것.

### P-5. 배포 판단

- 라이브 = `main`. 작업 브랜치 push ≠ 라이브 반영. 브랜치 통째 merge 금지, 격리 워크트리 cherry-push.
- HTML은 designer 소관 — 손대지 말 것(`manual_html_edit` warn 후 stop).
- 최종 배포는 **owner 승인 필수.**

### 하지 말 것

- 파서 산출 전 keep-list 선등재 (테스트 깨짐).
- 마스터 xlsx openpyxl 재저장.
- 자체 판단 push.

## 답변 (recipient 작성)

**Superseded (2026-08-14).** `equity_composition.json` 자체가 owner 지시로 아카이브됐다
(`inbox/publishing/20260814T0232Z` → `IFRS17_BS.json`으로 대체, `archive/2026-08_equity_composition/`).
이 티켓의 P-1~P-5는 전부 이 파일 기준으로 쓰여 이제 대상이 없다 — 실제 keep-list/xlsx 작업은
`IFRS17_BS.json` 기준으로 `20260814T0232Z`에서 완료(`inbox/_resolved/`로 이동됨). 이 파일은
이력으로만 남기고 close.
