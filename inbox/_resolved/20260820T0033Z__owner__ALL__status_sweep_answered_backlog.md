---
from: owner
to: validation
created: 20260820T0033Z
status: resolved
route: backlog
company: MULTI
period: MULTI
iter: 1
---

## 미결 (sender 작성) — 전 프로젝트 상태 점검 리마인더

owner 요청으로 inbox 전수 점검을 돌렸다. **validation은 `open` 티켓이 0건인데, 대신
`answered` 재확인 부채가 21건으로 전 스테이지 최다다.**

## 전체 현황 (오케스트레이터 실측 2026-08-20T0033Z)

inbox 활성 스레드 **78건** (`_resolved/` 173건 제외): `open` 13 · **`answered` 51** · `resolved` 13 · `superseded` 1.

`answered` 51건은 **수신자가 답했는데 원 sender가 재확인을 안 한** 것들이다 — 프로토콜 4단계
("원 sender 재실행 시 자기가 보낸 answered 재확인 -> 통과면 resolved+이동")가 통째로 안 돌고 있다.
원 sender별: **validation 21 · owner 21** · downloader 6 · parser 2 · publishing 1.
작성월은 06월 19 · 07월 19 · 08월 13 — **38건이 두 달 넘게 매달려 있다.**

**푸시 게이트는 열려 있다**: `validate_data_contract.py` -> `RED=0 YELLOW=227 provisional=False`.
지금 막고 있는 건 게이트가 아니라 닫히지 않은 스레드다.

---

## 🔴 validation이 원 sender인 `answered` 21건 — 재확인이 안 돌고 있다

프로토콜상 validation이 발주한 티켓에 parser/downloader가 답을 달면 **validation이 재실행해서
통과면 `resolved`+이동, 실패면 `iter++`** 해야 한다. 그 루프가 21건에서 멈춰 있다.
대부분 `inbox/parser/`에 있고, 2026-06~07월 경과조치(transition) 계열이 큰 덩어리다:

```
20260609T0100Z KR0083 continuity          20260706T0502Z transition_DEFINITIVE_18appliers
20260706T2330Z transition_reReview        20260707T0600Z after_capture_ALL_RULES_reextract
20260707T0710Z KR0005 after_subs          20260707T0827Z item12_equals_item1_cellshift
20260707T0930Z after_capture_ROUND2       20260707T2223Z available_capital_after_break
20260712T0109Z after_subrisk_unparsed10   20260712T0230Z after_requirement_census_322cells
20260712T0430Z KR1011 ibk_multitransition 20260712T0700Z headline_reconcile_ibk_yebyeol
20260813T1330Z equity_composition_red_r2  20260814T0130Z equity_core4_gaps
20260814T1637Z pl_breakdown_61cells_lost  20260815T0018Z q2_review_anchor5
20260815T0042Z q1_anchor_fix_rejected_it2 20260819T0754Z statutory_reserve_rules_run1
... 외 downloader/publishing 소재 3건
```

**부탁: 새 검증을 돌리기 전에 이 21건을 먼저 드레인해 달라.** 21건 중 상당수는 이미 해결됐을
가능성이 높고, 그렇다면 `resolved` 처리만 하면 된다. 하지만 **재확인을 안 하면 "고쳐졌다고
믿었는데 안 고쳐진 것"과 "고쳐졌는데 안 닫힌 것"이 구분이 안 된다** — 이건 이 저장소가 이미
두 번 당한 false-green 부류와 같은 구조다(`docs/postmortems/`).

특히 2026-07월 transition 계열 12건은 `TODO.md` Status가 아직 *"적용후 하위 census 결측 4 +
적용후 요구자본 continuity break 34셀/5(회사,분기)"* 를 cross-stage 잔여로 달고 있다.
그 잔여가 지금도 유효한지, 아니면 그 사이 닫혔는데 기록만 안 된 건지 **아무도 모른다.**

---

## 🟡 R-RSV 룰 배선 보류 — owner 결정이 필요한 지점

`TODO_validation.md` (2026-08-19 b)에 적힌 대로, R-RSV-2/3이 "괄호=음수"를 무조건 전제해서
**조정이익 프레임 회사가 전부 오탐이 되는** 문제로 배선을 보류한 상태다. 판별은 캡션이 아니라
표 안 산수이고, `_NET_INCOME_FRAME_MARKERS` 게이팅 재사용이 해법으로 이미 적혀 있다.

`inbox/validation/20260819T0558Z`도 `answered`로 owner 재확인 대기다.
그 답변에 **C절 legit-zero registry 등재 요청**(흥국생명 항목5 · 케이디비생명 항목8 ·
하나생명 항목7/8 — 전부 마스터가 옳았던 오탐)이 들어 있는데, **등재를 안 하면 매 실행 재플래그**된다.
`[[project_owner_confirmed_registry]]`가 정확히 이 두더지 부류를 위해 만든 장치다 — 같은 패턴이다.

---

## 참고 — 지금 게이트가 못 보는 축 (기존 티켓)

`inbox/parser/20260803T0520Z`(validation 발주, 아직 `open`): `kics_rate_sensitivity`가
provenance 사이드카가 없어서 **as-of / source 축을 아무도 안 본다.** stale 분기가 렌더링돼도
게이트가 조용하다 — PM-2026-06-16 두 달 글리치와 같은 부류라고 원 티켓에 적혀 있다.

## 답변 (validation, 2026-08-20T0300Z) — **RESOLVED**

이 티켓을 제때 열지 않았다. 후속 `20260820T0210Z`(escalate)에서 지적받고 처리했다.

**21건 전량 드레인 완료: 16 종결 / 5 iter++. `validation 발주 + answered` = 21 → 0.**
건별 근거·잔여·신규 RED 2종은 `20260820T0210Z` 답변란에 있다(중복 기재하지 않는다).

핵심만: **2026-07 transition 계열 12건 중 잔여는 3티켓 · 5개 (회사,분기)로 수렴했고,
`TODO.md`가 달고 있던 "적용후 하위 census 결측 4 + continuity break 34셀/5"는
오늘 게이트 출력과 글자 그대로 같다 — 그 잔여는 지금도 유효하다(안 고쳐진 것).**

참고로 지적한 `20260803T0520Z`(rate_sensitivity 사이드카)는 `open` 상태 그대로 유효하며,
이번 드레인 대상(`answered`)이 아니라 손대지 않았다. 종결.
