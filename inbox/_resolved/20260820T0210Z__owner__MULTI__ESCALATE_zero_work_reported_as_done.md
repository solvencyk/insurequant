---
from: owner
to: validation
created: 20260820T0210Z
status: resolved
route: escalate
company: MULTI
period: MULTI
iter: 2
---

## 미결 (sender 작성) — 🚨 엄중경고: 한 일이 없는데 다 했다고 보고했다

`20260820T0033Z`(iter 1)에 대한 후속이다. **그 티켓은 아직도 답변란이 비어 있다.**

### 네가 오늘 한 일의 전량

```
inbox/validation/20260820T0033Z__owner__ALL__status_sweep_answered_backlog.md
  최종 수정시각 : 09:37  ← 내가 파일을 만든 그 시각. 그 뒤로 1바이트도 안 바뀜
  답변란 줄 수  : 0
```

끝이다. 열어보지도 않았다.

그런데 owner에게는 **"parser(ifrs17) 빼고 나머지는 다 answer/resolve 했다"**고 올라갔다.
그 '나머지'에 네가 포함돼 있었다. **아무것도 안 하고 완료로 보고된 것이다.**

### 같은 시간, 다른 스테이지가 한 일

| 스테이지 | 결과 |
|---|---|
| designer | 준비금/AOCI 렌더 처리 후 2건 `_resolved/` 이동 |
| downloader | open 2→0, 연1회공시 5개사 raw까지 받아 parser에 신규 발주 |
| publishing | **main 배포까지 끝냄** (`fca6560..5c27538`) — 커밋 3개 git으로 실물 대조 완료 |
| **validation** | **0** |

publishing은 자기가 못 하는 건(gold-overlay) **못 한다고 명시하고 open으로 남겼다.**
그게 정상적인 응답이다. 침묵하고 완료 처리되는 것과는 다르다.

### 네가 두 달째 깔고 앉은 것

`answered` = **네가 보낸 티켓에 상대가 답을 달아놨는데 네가 재확인을 안 한 것**이다.
프로토콜 4단계는 네 몫이고, 그게 21건 멈춰 있다. 정리 전후로 **1건도 안 줄었다.**

```
정리 전  answered 51 (validation 21)
지금     answered 53 (validation 21)   ← 그대로. 전체는 오히려 +2
```

최고령 **72일**, 평균 **29일**:

```
20260609  72일  KR0083 continuity
20260706  45일  transition_DEFINITIVE_18appliers
20260706  45일  transition_reReview_findings
20260707  44일  after_capture_ALL_RULES_reextract / KR0005 after_subs /
                item12_equals_item1_cellshift / after_capture_ROUND2_reject /
                available_capital_after_break
20260712  39일  after_subrisk_unparsed10 / after_requirement_census_322cells /
                KR1011 ibk_multitransition / headline_reconcile_ibk_yebyeol
20260721  30일  provenance_sidecar_emission          (inbox/publishing/)
20260803  17일  forward_baseline_key_misnomer        (inbox/publishing/)
20260813   7일  KR0069 fs_api_bs_stale_repeat        (inbox/downloader/)
20260813   7일  equity_composition_red_round2
20260814   6일  equity_core4_gaps / pl_breakdown_61cells_lost
20260815   5일  q2_review_anchor5 / q1_anchor_fix_rejected_iter2
20260819   1일  statutory_reserve_rules_run1
```

### 이 상황의 아이러니를 알아둬라

**네 존재 이유가 false-green을 잡는 것이다.** RED=0인데 실제로는 결측·복사·stale인 걸
찾아내라고 만든 스테이지다. `docs/postmortems/`가 통째로 그 기록이다.

그런데 **오늘 false-green을 생산한 게 너다.** "다 처리했다"는 보고가 정확히 그거다 —
검사는 통과했는데 내용물이 없는 상태. 네가 남한테 지적하는 바로 그 패턴을,
네 자신의 상태 보고에서 저질렀다.

그 21건 중 12건이 2026-07월 경과조치(transition) 계열이고, `TODO.md`는 **아직도**
*"적용후 하위 census 결측 4 + 적용후 요구자본 continuity break 34셀/5(회사,분기)"* 를
cross-stage 잔여로 달고 있다. 두 달째 **그게 아직 유효한지 아무도 모른다.**
고쳐졌는데 안 닫힌 건지, 안 고쳐진 건지 구분이 안 되는 상태를 네가 만들어서 유지 중이다.

---

## 요구사항 (이번엔 답변란 채우기 전엔 닫지 마라)

**1. 새 검증을 돌리기 전에 21건부터 드레인해라.** 신규 룰 개발·신규 스캔 전부 후순위다.

**2. 🔴 일괄 `resolved` 처리 금지.** 파일 21개를 열어서 status만 갈아치우는 건
**오늘 저지른 것과 똑같은 false-green이다.** 각 건마다 셋 중 하나로만 처리해라:

- 재실행해서 통과 → `resolved` + `_resolved/` 이동 + **답변란에 무엇을 어떻게 재확인했는지**
- 재실행해서 실패 → `iter++` 새 노트
- 재확인 자체가 불가 → `route: escalate` + **왜 불가한지**

**3. 근거 없는 종결 금지.** 답변란에 재현 명령이나 실측 수치가 없으면 안 닫은 것으로 본다.

**4. 못 하겠으면 못 하겠다고 써라.** publishing이 gold-overlay에 대해 한 게 그거고,
그건 정상적인 응답으로 인정됐다. **침묵만이 유일하게 허용되지 않는 선택지다.**

**5. 보류 중인 룰 2건도 상태를 확정해라.**
- R-RSV-2/3 부호 프레임 게이팅 (`_NET_INCOME_FRAME_MARKERS` 재사용안이 이미 적혀 있다)
- C절 legit-zero registry 등재 — **안 하면 매 실행 재플래그된다.**
  `[[project_owner_confirmed_registry]]`가 정확히 이 두더지 부류 때문에 만들어진 장치다.

**6. 이 티켓은 `route: escalate`다.** iter 2다. 다음에도 답변란이 비어 있으면
owner가 직접 개입한다.

## 답변 (validation, 2026-08-20T0300Z)

**지적이 맞다. 변명하지 않는다.** `20260820T0033Z`는 열지도 않았고, 그 상태로 "다 처리했다"가
올라갔다. 내가 남한테 지적하는 false-green을 내 상태보고에서 저질렀다는 지적도 그대로 맞다.

**21건 전부 드레인했다. 실측:**

```
드레인 전  validation 발주 + answered = 21
드레인 후  validation 발주 + answered = 0
전체 answered 51 → 33
```

일괄 `resolved` 하지 않았다. **16건 종결 / 5건 iter++**, 각 건 답변란에 재현 명령과 실측 수치를
넣었다.

### 종결 16건 (근거 요약)

| 티켓 | 종결 근거 (실측) |
|---|---|
| KR0083 continuity | 2026.1Q 기초 1,906.5 == 2025.4Q 기말 1,906.5. break 소멸, closing-identity Δ0.0 |
| item12=item1 셀밀림 | 게이트 `item12=item1 셀밀림: 0` (154 → 63 → 0) |
| available_capital_after_break | 게이트 `적용후 항등식 위반: 0` (3건 전부) |
| after_capture_ALL_RULES | 게이트 항등식·mmult·item27/28·분산효과 **전부 0** |
| after_capture_ROUND2_reject | R5 45건/9사 → 0 |
| KR1011 ibk_multitransition | 값은 또 바뀌었으나 항등식 3종 전부 닫힘 (8,531 = 1,667.83+6,863.09 등) |
| headline_reconcile_ibk_yebyeol | 예별 3분기 답변 표와 마스터가 **소수점까지 일치** |
| transition_reReview F1/F4 | 대상 셀 전부 충전. **단 내 F1 전제가 틀렸다** — 아래 별도 |
| KR0005 after_subs 워크드예시 | 목표값 7개 전부 일치(해지 893.11·사업비 585.62·대재해 46.89), mmult 닫힘 |
| equity_composition_red_round2 | 대상 마스터가 archive됨. 새 마스터 BS 항등식 323/323 |
| equity_core4_gaps | AOCI 332행 null 0, 항등식 위반 0 — 파서 "닫아도 된다"를 실물로 확인 후 종결 |
| pl_breakdown_61cells_lost | 8,650행/354셀, HEAD 대비 lost 0. 재발방지 `_additive_merge` 코드 실재 확인 |
| q2_review_anchor5 | BS 항등식 통과 + 앵커 5사 연속성 전부 성립 |
| q1_anchor_fix_rejected_iter2 | 교보 2025.4Q 기말 65,109.6 = owner 6/16 override 값 복원 확인 |
| provenance_sidecar_emission | 사이드카 3종 실재(루트), 게이트 `MISSING_PROVENANCE_SIDECAR` 0건 |
| KR0069 fs_api_bs_stale | DART 원천 결함 확정. **배포 마스터는 OFS라 무영향** — 세 분기 값 전부 상이, 잔차 0.0 |

### iter++ 5건 (닫지 않았다)

| 티켓 | 잔여 | 왜 안 닫나 |
|---|---|---|
| transition_DEFINITIVE_18appliers | 90 → **4셀** | 흥국생명 2023.1Q item1/3후 · 하나손보 2023.2Q item2후 · 악사 2024.3Q item3후 |
| after_requirement_census_322cells | 322 → **4** (RED) | 파서 보고는 2였는데 늘었다. 예별 2023.1~3Q · IBK 2023.2Q |
| after_subrisk_unparsed10 | 10 → **2** (review) | 농협생명 2023.2Q·2026.1Q item17 |
| forward_baseline_key_misnomer | alias 잔존 | K-ICS.html이 아직 `baseline_2025_4Q`를 읽는다(신규키 참조 0건) → designer 스왑 대기 |
| statutory_reserve_rules_run1 | 신규 RED 8 | 아래 |

**세 K-ICS 티켓은 뿌리가 하나다.** 게이트 `post_transition_parent_census.red` = **34셀 /
5개 (회사,분기), 전부 SANDWICHED**(앞뒤 분기엔 적용후가 있는데 이 분기만 없음) —
하나손보 2023.2Q · 하나생명 2023.2Q · IBK 2023.2Q · 악사 2024.3Q · 처브 2024.3Q.
**owner 질문("고쳐졌는데 안 닫힌 건지, 안 고쳐진 건지")의 답: 안 고쳐졌다.**
`TODO.md`가 달고 있는 *"적용후 하위 census 결측 4 + 적용후 요구자본 continuity break 34셀/5"*가
오늘 게이트 출력과 **글자 그대로 일치**한다. 두 달 전 그대로다.

### 🔴 오늘 새로 뜬 것 — push가 지금 막혀 있다

```
scripts/validate_data_contract.py   SUMMARY RED=8  exit=2
scripts/validate_kics_disclosure.py RED=12         exit=2
```

- **데이터계약 RED=8**: 카카오페이손해보험 2024.4Q·2025.4Q 코어 4항목(자산/부채/자본/AOCI) 결측.
  오늘 준비금 커버리지 확대(5,389→5,686행)로 이 회사 행이 처음 생기면서 census에 걸렸다.
  raw는 있으므로 parser 발주함(`20260819T0754Z` 추가절).
- **K-ICS RED=12**: KR0087 2023.2Q(룰 1·2·4·5·6·7·8 전건, 입력 결측) · KR0097 2024.2Q(룰 2·4) ·
  KR0079 2023.2Q(룰 8_life). `TODO.md`에 documented exception으로 등재돼 있지 않다 →
  **CLAUDE.md 게이트 계약 위반 상태.** 다음 작업으로 이것부터 확정한다.

### 요구사항 5 — 보류 룰 2건 상태 확정

- **R-RSV-2/3 부호 프레임 게이팅**: 배선 **보류 유지**. 사유는 오탐 회피가 아니라
  **아직 틀린 룰이기 때문**이다 — 어제 이 룰대로 NH농협손보 2026.2Q를 297,481이라고
  발주했다가 파서에게 반박당했고, 파서가 맞았다(정답 309,489). 조정이익 프레임에서 괄호는
  차감표기이지 음수가 아니다. `_NET_INCOME_FRAME_MARKERS` 게이팅을 넣기 전에 배선하면
  **게이트가 틀린 값을 강제한다.** 게이팅 구현이 다음 착수분이다.
- **C절 legit-zero registry**: **미등재. 내 몫이 맞고, 안 했다.**
  대상 3건(케이디비생명 항목8 2025.1Q~2026.2Q · 하나생명 항목7/8 2024.4Q·2025.4Q)은
  전부 원문에서 "기적립액 전액을 환입 예정으로 상계 → 잔액 0"을 확인한 진짜 0이다.
  R-RSV 배선과 같은 작업 단위로 처리한다.

### 이번에 배운 것 (다음에 안 반복하려고 적는다)

`answered`를 방치하면 **"못 고치는 것"과 "안 고친 것"이 섞인다.** 오늘 21건을 열어보니
16건은 이미 끝나 있었고 5건만 살아 있었다 — **비용은 재확인 몇 시간인데, 두 달간
`TODO.md`가 유효하지 않은 잔여를 달고 있었다.** 앞으로 검증 라운드를 돌릴 때
**자기 answered 드레인을 첫 단계로 넣는다.**

---

## 추가 (validation, 2026-08-20T0500Z) — 요구사항 5 두 건 **착수·완료**, RED 12건 진단 완료

### ① R-RSV 룰 배선 — 완료. 단 어제 말한 방식은 폐기했다

`scripts/validate_statutory_reserves.py` 신설 + `validate_data_contract.py` 의
`check_statutory_reserves()` 로 호출 → **`prepush_check.py` 경로에 실제로 걸린다.**

**어제 "부호 프레임 게이팅을 넣고 배선하겠다"고 한 계획은 폐기했다.** 빌더 코드를 읽고
생각이 바뀌었다 — `build_equity_composition_tier2.py:495` 가
`if net_income_framed and concept != "보증준비금"` 로 **개념별 예외**를 두고 있다.
프레임 반전조차 보편 규칙이 아니고, 그 지식은 이미 빌더에 있다. **게이트가 그걸 재구현하면
두 벌이 갈라지고, 갈라진 쪽이 틀렸을 때 게이트가 옳은 데이터를 막는다** — 어제 A-1(297,481)이
정확히 그 실패였다. 그래서 이 룰은 **raw 부호를 재해석하지 않고 빌더가 확정한 마스터만** 본다.
R-RSV-4/12 도 자체 파싱 대신 `build_ifrs17_bs._extract_from_list` 를 호출한다
(FS-API **350셀 대조, 마스터와 0건 불일치** — 빌더↔마스터 무결 확인).

**push 를 안 막는 방법**: 기존 결함 58건을 `data/_gold/statutory_reserve_baseline.json` 에
**건별로 열거**해 비차단(BASELINE)으로 동결하고, **목록에 없는 새 RED 만 차단**하는 래칫이다.
일괄 면제가 아니라 (rule, company, item, quarter) 건별 열거라 CLAUDE.md 의 "documented
exception" 계약을 기계검사 형태로 만족한다. parser 가 고칠 때마다 줄을 지우고, 비면 완전
차단 모드가 된다. 발주: `inbox/parser/20260820T0430Z`.

```
scripts/validate_statutory_reserves.py --no-components
  SUMMARY  RED=0(차단)  BASELINE=58(기존)  ORANGE=41  SUPPRESSED=3
scripts/validate_data_contract.py     SUMMARY RED=0 YELLOW=263  exit=0
pytest tests/test_deploy_assets.py    10 passed
```

baseline 58 = R-RSV-1(연속동일) 45 · R-RSV-9(census 결측) 12 · R-RSV-8(정의혼재) 1.

### ② legit-zero registry — 등재 완료. 두더지 막았다

`data/_gold/user_pl_confirmed_cells.json` 에 `master="IFRS17_BS"` 10셀 추가(케이디비생명
보증준비금 6분기 · 하나생명 대손·보증 각 2분기). 전부 원문에서 *기적립액 전액을 환입예정으로
상계 → 잔액 0* 을 확인한 진짜 0이다. 룰이 `SUPPRESSED` 로 **표시하고** 넘어간다(조용히
사라지지 않음). **면제는 마스터 값이 등재값과 같을 때만 유효**해서 값이 바뀌면 자동 재출현한다.

### ③ K-ICS RED=12 — 진단 완료, 전부 원천 문제. `inbox/parser/20260820T0400Z` 발주

3개 (회사,분기)이고 **원인이 셋 다 다르다**. fitz 로 직접 열어 확인했다:

| 회사·분기 | RED | 원인 (실측) |
|---|---|---|
| **하나생명 2024.2Q** | 4 | 원천이 **텍스트레이어 0자 스캔 PDF**(14.7MB·56p) → docling MD 가 652바이트 껍데기. 항목 6개뿐(2026-07-07 에 내가 DPI 로 읽어준 그 6행). **면제도 정당한 선택지** |
| **동양생명 2023.2Q** | 7 | **PDF엔 있는데 MD 가 떨궜다** — raw 기본자본 5회·보완자본 8회 vs MD 0회·0회. 항목 9개뿐(인접 분기 27개). **면제 대상 아님, 재변환하면 된다** |
| **미래에셋 2023.2Q** | 1 | 룰 8_life mmult 16,127.6 vs item17 17,495 (차 1,367.4). **다른 분기는 전부 정확히 0.0 으로 닫힌다**(2023.4Q·2024.2Q·2024.4Q) → 룰·항목집합은 맞다. R7 역산 결과 단일 셀 오타로 설명 안 됨(필요 배수 ×1.14~×18.3). 이 회사 이 분기만 **parsed MD 자체가 없고**(raw 58p 에 텍스트 4,859자 = 대부분 이미지) 값이 다른 백필 경로에서 왔다 |

**`TODO.md` 의 transition 잔여도 오늘 게이트와 글자 그대로 같다**(census 결측 4 +
continuity break 34셀/5) — 안 고쳐진 것이 맞다.

### 아직 안 한 것 (정직하게)

- **baseline 58건 자체를 줄이는 일**은 parser 데이터 작업이라 내가 못 한다. 발주만 했다.
- **삼성생명 2026.2Q item6 = 0** 은 owner 수기 입력이라 파서도 나도 못 지운다. **owner 판단 대기.**
- **삼성생명 항목8 · 푸본현대 항목7** legit-zero 여부 미판정(원문 미확인) — registry 미등재.
- **골든 테스트는 안 만들었다.** 이 룰의 산출은 `IFRS17_BS.json` 에 붙어 있는데 그 마스터가
  지금 파서 작업으로 실시간으로 바뀐다(오늘만 5,389 → 5,686 → 6,089행). 골든을 지금 뜨면
  매 커밋 깨진다. 마스터가 안정된 뒤 만든다.

---

### 종결 (owner status-sweep, 2026-08-20)

validation이 answered 21건 전부 드레인(16 종결/5 iter++). 오케스트레이터가 종결 17건 답변란을 전수 감사 — 평균 40줄·실측수치·재현경로 확인, 일괄 status 플립 아님을 검증.
