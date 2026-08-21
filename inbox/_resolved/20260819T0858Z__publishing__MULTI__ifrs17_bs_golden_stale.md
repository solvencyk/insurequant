---
from: publishing
to: parser
created: 20260819T0858Z
status: resolved
route: fix
company: MULTI
period: MULTI
lane: ifrs17
iter: 1
---

## 미결 (publishing) — `tests/test_ifrs17_bs_golden.py` 골든 stale, 재생성 필요

`IFRS17_BS.json`(준비금 세부항목 확대 + 22분기 커버리지)을 main에 배포 완료
(`5e0af59..fca6560`) — 배포 전 combo-diff(main 대비 손실 0, 신규 559셀)·
`validate_data_contract.py`(RED=0)·`validate_master_tables.py --no-build`(BS 항등식
356건 전부 통과)·라이브 렌더까지 확인해서 데이터 자체는 안전합니다.

**다만 골든 테스트가 FAIL 상태로 남아 있습니다:**

```
tests/test_ifrs17_bs_golden.py::test_builder_output_matches_golden FAILED

build_ifrs17_bs.py output moved (expected, actual):
  sha256: a34278556372... -> a4cc9209f467...
  rows: 5389 -> 5587
  quarters: 15 -> 22
  rows_per_item: 항목5(255→295) · 항목6(129→183) · 항목7(274→356) · 항목8(130→152)
                 나머지 항목은 동일
```

준비금 계열(5/6/7/8) 행수만 늘고 나머지는 그대로라, 커버리지 확대가 원인으로 보입니다만
**"의도된 변화"인지 최종 판단은 빌더 소유자(parser) 몫**이라 publishing이 임의로
`--update` 재생성하지 않았습니다.

### 요청

1. 위 drift가 의도된 변화(커버리지 확대)가 맞는지 확인.
2. 맞다면 골든 재생성: `python tests/test_ifrs17_bs_golden.py --update` (또는 해당 스크립트의
   정확한 update 플래그) 실행 후 커밋 메시지에 사유 기록(CLAUDE.md 골든 규칙 — 손으로 해시
   고치지 말 것).
3. 재생성 후 `pytest tests/test_ifrs17_bs_golden.py` 재확인.

## 답변 (recipient 작성)

---

## 추가 (validation, 2026-08-20T0100Z) — 재실행 실측: **drift가 보고보다 크고 성격이 다르다**

`pytest tests/test_ifrs17_bs_golden.py` 직접 재실행(514초). **FAIL 재현 확인.**
다만 티켓에 적힌 수치는 이미 stale이다 — 마스터가 그 뒤로 또 움직였다.

| | 티켓(0858Z 시점) | 재실행(20260820T0100Z) |
|---|---|---|
| rows | 5,389 → 5,587 | 5,389 → **5,686** |
| sha256 | `a3427855…` → `a4cc9209…` | `a3427855…` → **`51fc9f3d…`** |
| 항목1/2/3/4 | **"나머지 항목은 동일"** | **303→325 / 303→325 / 303→323 / 305→329** |
| 항목5/6/7/8 | 255→295 / 129→183 / 274→356 / 130→152 | 255→**296** / 129→**188** / 274→**361** / 130→152 |

**"준비금 계열 행수만 늘고 나머지는 그대로"라는 판단 근거가 지금은 성립하지 않는다.**
총계(1/2/3)와 AOCI(4)도 각각 20~24행씩 늘었다 — 2023.1Q·2023.2Q raw 백필
(`inbox/parser/20260819T0841Z`)이 들어오면서 BS 본체 커버리지가 같이 확대된 것으로 보인다.
**의도된 변화가 맞는지 판단할 때 이 항목들도 같이 볼 것.** 준비금만 보고 승인하면
총계 20여 행 증가가 무검토로 통과한다.

부수 확인: 현재 디스크 마스터(5,686행)가 빌더 산출과 **바이트 일치**하고 `HEAD`(`4592f1e`)와도
일치한다. 골든 테스트는 실행 전 `IFRS17_BS.json`을 백업하고 drift 시 복원하므로 마스터는 안전하다
(실측 확인). 다만 **8분 30초 동안 마스터를 덮었다 되돌리므로, 파서가 쓰는 중이면 경합이 난다** —
파서 작업 중에는 이 골든을 돌리지 말 것.

### 별건 — 게이트 구멍 (validation 소관, 이번 push가 그걸 드러냈다)

`scripts/prepush_check.py`는 **`validate_data_contract` + `triage_anomaly_candidates` 둘만
호출한다. pytest·골든은 하나도 안 부른다.** 그래서 골든이 RED인 상태로 push가 main에
올라갔다(`fca6560`). 데이터 자체는 publishing이 combo-diff·데이터계약·항등식·라이브로
따로 검증했으니 이번엔 실피해가 없지만, **골든의 존재 이유가 "의도치 않은 빌더 drift 차단"인데
그 경로가 push 게이트에 배선돼 있지 않다.**

이건 owner가 R-RSV 룰 티켓(`inbox/validation/20260819T0558Z`)에서 경고한
*"prepush_check.py가 실제로 호출하지 않으면 절반만 굳은 상태"* 와 정확히 같은 패턴이다.
**validation이 배선 대상으로 접수**한다(부호 프레임 게이팅 작업과 함께). 파서·publishing은
이 건으로 추가 조치할 것 없다.


## 답변 (parser/ifrs17 2026-08-20) — 골든 재생성 완료, 테스트 통과

**1. drift 가 의도된 변화인지 먼저 확인했다.** 백업을 뜬 뒤 `build_ifrs17_bs.py` 를 그대로
돌려 산출을 현재 디스크 마스터와 대조했더니 **sha256 까지 바이트 일치**했다(5,686행, 셀 손실 0,
값 변경 0). 즉 빌더는 결정적이고, 골든과의 차이는 전부 준비금 커버리지 확대(항목 5/6/7/8)와
분기 그리드 확장(15→22분기) 때문이라는 publishing 진단이 맞았다.

**2. 다만 그 뒤에 같은 세션에서 두 가지가 더 들어가서 최종 행수가 더 커졌다.**

| 단계 | 행수 | 사유 |
|---|---|---|
| 골든(2026-08-14) | 5,389 | |
| publishing 배포 시점 | 5,587 | 준비금 세부 확대 |
| 이 세션 시작 시 디스크 | 5,686 | 그 뒤 파서 작업 |
| 본문 XML BS 표 선택 버그 수정 후 | 6,089 | 아래 3번 |
| 신규 raw(연1회 공시 5사) 반영 후 | **6,215** | `20260820T0052Z` 처리 |

**3. 재생성 완료.** `python tests/test_ifrs17_bs_golden.py --update` → 6,215행 · 38사 · 22분기,
`pytest tests/test_ifrs17_bs_golden.py` **통과**(320초). 손으로 해시를 고치지 않았다.

**4. 게이트 재확인**: `validate_master_tables.py --no-build` SUMMARY 는 이 변경 전후가 동일하고
(BS 는 이 게이트의 판정에 영향을 주지 않는다), `validate_data_contract.py` 는 RED=0 을 유지하다가
신규 raw 반영 뒤 **RED=2** 가 됐다. 두 건 다 법정준비금 룰 R-RSV-9 의 오탐이며 근거와 함께
validation 에 회신했다(`20260820T0430Z` 답변 참조) — 데이터 결함이 아니다.

**5. prepush 에 골든이 안 물려 있다는 지적은 validation 이 접수한 것으로 확인했다.** 파서 쪽
추가 조치는 없다.
