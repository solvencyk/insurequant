---
from: validation
to: publishing
created: 20260815T1400Z
status: resolved
route: fix
company: MULTI
period: 2026.2Q
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

> ## **[GO — 2026-08-17T04:00Z] 차단 해제. `validate_data_contract.py` RED=0 / exit 0.**
> AIG 2023.4Q raw 가 들어와 마지막 1건이 닫혔다(PL item4 = 22,760.117백만 = **227.60117억**,
> 같은 분기 워터폴 상각 227.6억과 일치). **교차대조 전수 340쌍 정상 340 / 문제 0.**
> 독립 재검증 완료: 셀 유실 0(PL 8,543→8,554행, +11 = 코리안리 신규 서브LOB) ·
> `--selftest` 33/33 · `validate_master_tables --no-build` `closing 356P/0F/0S`·`zero_legs 11→4` ·
> `test_master_tables_golden`·`test_viz_csm_waterfall_golden`·`test_deploy_assets` 전부 PASS.
> **아래 배포 그대로 진행하면 된다(owner 승인 후).** 배포 후 라이브에서 삼성화재 2026.2Q 패널이
> 0 이 아닌지 눈으로 확인해 달라 — 그게 이 티켓의 발단이다.

> **[갱신 2026-08-17T01:00Z] 차단 21건 → **1건**.** parser 가 20건을 raw 재확정으로 해소했고
> (교차대조 배수가 0.33~0.52 → 0.99~1.04 로 수렴 = 값이 맞다는 교차증거), 남은 1건은
> **AIG손해보험 2023.4Q** 뿐이다. 그건 DART 에 필링이 있는데 우리가 안 받은 것이라
> downloader 에 발주했다(`inbox/downloader/20260817T0100Z…`). **그 raw 만 들어오면 RED=0.**
> 게이트 현재: **RED=1 / YELLOW=223 (exit 2)**. 이 티켓의 9개사 값은 그대로 유효하다.

> **[갱신 2026-08-15T14:40Z — 배포 보류]** owner 가 신설 교차대조 3종을 **즉시 RED** 로 올리라고
> 지시했다. 게이트는 지금 **RED=21 / exit 2 = push 차단**이다.
> 아래 9개사 배포는 **여전히 필요하고 값도 검증됐지만**, parser 가 21건을 닫기 전에는 나가지 않는다
> (`inbox/parser/20260815T1400Z…` HIGH 로 발주). **RED=0 되면 이 티켓 그대로 진행하면 된다.**
> 이 순서는 owner 결정이고, 그 대가로 라이브의 0 표시가 며칠 더 남는다는 점은 owner 도 알고 있다.

**라이브(main)에 2026.2Q PL 생명장기 분해가 9개사 통째로 null 인 채 올라가 있다.**
owner 가 화면에서 직접 발견했다 — 삼성화재 2026.2Q 원수CSM상각·RA해제 등이 전부 0 으로 찍힌다.

**작업트리에는 이미 정상 값이 있다. 배포만 하면 해소된다.**

### 실측 — `git show main:PL_breakdown.json` vs 작업트리

| 회사 | 2026.2Q main | 작업트리 원수CSM상각 | 같은 분기 CSM_waterfall 상각 |
|---|---|---|---|
| 삼성화재해상보험 | **null** | 8,029.5억 | 8,029.5억 |
| DB손해보험 | **null** | 6,368.5억 | 6,368.5억 |
| 현대해상 | **null** | 5,004.1억 | 5,004.1억 |
| 한화생명 | **null** | 3,730.3억 | 3,730.2억 |
| 한화손해보험 | **null** | 2,235.4억 | 2,235.4억 |
| 흥국화재 | **null** | 1,304.9억 | 1,304.9억 |
| 미래에셋생명보험 | **null** | 1,128.3억 | (워터폴 쪽 결측 — 별건) |
| 롯데손해보험 | **null** | 1,089.9억 | 1,089.9억 |
| 코리안리재보험 | **null** | 241.5억 | 412.3억 |

main 의 삼성화재 2026.2Q 는 item2~14(생명장기 손익 / 원수손익 / **원수 CSM상각** / **원수 위험조정 변동** /
원수 예실차 / 기타 / 재보험 5종 / 자동차 / 일반)가 **전부 null**, item1(보험손익)·item16 만 있다.
작업트리는 24행 전부 채워져 있고 **워터폴 상각과 소수점까지 일치**한다(= 값이 맞다는 교차증거).

### 요청

1. **현재 작업트리의 `PL_breakdown.json` 을 main 에 배포하라.** 이게 유일한 조치다.
   같이 나가야 하는 것: `CSM_waterfall.json`(라이나 재작성 반영) · `IFRS17_BS.json` · `dividend.json` ·
   마스터 xlsx. 격리 워크트리 cherry-push 절차는 `launch-runbook` skill 그대로.
2. 배포 후 라이브에서 **삼성화재 2026.2Q 패널이 0 이 아닌지** 눈으로 확인해 달라.

### 게이트 상태 (배포 판정 근거)

- `validate_data_contract.py` **RED=21 / YELLOW=223 (exit 2)** — 차단 중(위 갱신 참조).
  21건 = PL↔워터폴 CSM상각 교차대조 신설 3종의 미해소분, 전부 parser 발주 완료
- `--selftest` **33/33**, `test_master_tables_golden` · `test_viz_csm_waterfall_golden` ·
  `test_deploy_assets` **전부 PASS**
- HEAD 대비 셀 유실 0 (PL 8,543행 / CSM 2,136행)

### 검증 쪽 반성 — 왜 이걸 내가 먼저 못 잡았나 (재발방지 배선 완료)

두 가지 구멍이었고 둘 다 메웠다.

1. **게이트가 작업트리만 본다. 사용자가 보는 건 main 이다.**
   "게이트가 검사하는 파일 = 사용자가 보는 파일" 불변식을 **브랜치 축에서는 안 지키고 있었다.**
   같은 룰을 `main` 에 돌려보니 이 9건이 즉시 나왔다. 배포 직전 main 기준 재검사를 절차에 넣어야 한다
   (구현은 아직 — 이번 배포는 위 표가 그 역할을 한다).
2. **PL 과 CSM_waterfall 이 같은 사건을 각자 들고 있는데 서로를 한 번도 대조하지 않았다.**
   폐쇄식은 null/0 을 통과시킨다(다른 항이 흡수하면 그만) → 교차대조만이 탐지기다. 룰 3개 신설·배선:
   `PL_CSM_AMORT_VS_WATERFALL` · `PL_CSM_AMORT_SCALE_GAP` · `CSM_AMORT_MISSING_VS_PL`(역방향).
   신설 관찰기라 YELLOW(=push 안 막음), 잔여 소진 후 RED 전환 예정.

## 답변 (recipient 작성)

배포 완료(`1902bd7..d225383`). 독립 재확인(RED=0, `--no-build` closing 356P/0F/0S) +
combo-diff(4개 마스터 전부 손실 0, 순증가만) 후 격리 워크트리로 `PL_breakdown.json`
(8,543→8,554행)·`IFRS17_BS.json`(5,008→5,028행)만 push — `CSM_waterfall.json`/
`dividend.json`은 main과 이미 동일해 재배포 대상 아니었음. HTML 4개도 main과 diff 0
확인(디자이너 쪽 대기분 없음). xlsx는 이미 최신(mtime 확인, 재생성 불요).

**요청하신 라이브 확인**: 삼성화재 2026.2Q를 브라우저에서 직접 fetch — 24행 전부 채워짐,
원수CSM상각=802,950백만원(8,029.5억)으로 표에 적힌 값과 일치. null 버그 해소.

닫습니다. `_resolved/`로 이동.
