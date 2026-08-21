---
from: owner
to: validation
created: 20260814T0035Z
status: resolved
route: backlog
company: MULTI
period: 2023.1Q-2026.1Q
iter: 1
---

## 미결 (sender 작성)

**발주 범위 정정 — 이전 발주(`20260813T0422Z`)의 census 코어가 과설정이었다. 오케스트레이터 잘못이다.**

owner 원래 요구는 이거였다:

> high level의 17BS (자산/부채/자본/AOCI) 를 빠르게 OpenDart API로 가져오고,
> 가능하면 해약환급금준비금 정도까지 긁어보라고 (**안되면 pass**)

즉 **해약환급금준비금은 optional("안되면 pass")** 이었는데, 이전 발주 §V-2에서 항목 10을
**필수 코어 + 결측=RED**로 못박았다. 지금 RED 182건 중 **160건(EQ_CENSUS_MISSING_ITEM)이
사실상 항목 10 결측**이다. owner가 "없으면 넘어가라"고 한 걸 게이트가 막고 있는 상태다.

### 고칠 것

1. **census 코어를 `[1, 6, 40, 41]`로 축소**
   (자본총계 / 기타포괄손익누계액 / 자산총계 / 부채총계 = owner가 실제로 요구한 high-level BS).
2. **항목 10·11(해약환급금준비금) → optional.** 있으면 싣고, 없으면 결측으로 두고 **RED 아님.**
   BS 주기행으로 공시하는 회사(24사 중 11사)만 값이 있는 게 정상이다.
   탐지 자체를 지우진 말고 **YELLOW(정보성)** 로 강등.
3. **항목 5·20·29·30도 코어에서 제외** → optional. AOCI 흐름 분해(20-31)는 owner가 요구한 적
   없다(내가 넣었다). 데이터는 이미 있으니 두되, **게이트로 강제하지 말 것.**
4. `EQ_PARENT_CHILD_INCOMPLETE`(6 있는데 20/29/30 없음)도 **YELLOW로 강등** — 같은 이유.
5. `EQ_TIER2_SCOPE_GAP` 제거 — Tier-2 자체를 접는다(parser 발주 별도).

### 유지할 것 (건드리지 말 것)

- `EQ_BS_IDENTITY`(자산 = 부채 + 자본), `EQ_AOCI_ROLLFORWARD`, `EQ_AOCI_STOCK_FLOW_TIE`,
  `EQ_UNIT_SCALE_JUMP`, provenance 사이드카 RED — 이건 **owner가 요구한 4개 항목의 정확성**을
  지키는 룰이다. 살아 있어야 한다.
- 코어 4개 항목(1/6/40/41)의 결측은 계속 **RED**.
- owner-confirmed 억제 레지스트리, `--selftest` 22/22.

### 기대 결과

RED 182 → **20 내외**(코어 4항목 결측 + 진짜 항등식 위반만 남음). 남은 RED은 진짜 고칠 것들이다.

### 하지 말 것

- 이미 추출된 항목(2-5,7,8,12-19,20-31,42-49)을 **파일에서 지우지 말 것.** 같은 API 응답에
  딸려온 거라 유지비 0이다. 게이트/화면에서 빼는 것으로 충분.
- 이 정정을 계기로 룰을 더 만들지 말 것. **줄이는 작업이다.**

## 답변 (recipient 작성)

**status: answered (2026-08-14, validation) — RED 182 → 21.** 지시 5개 전부 반영, 룰은 하나도
새로 만들지 않았다(줄이는 작업).

| 지시 | 반영 |
|---|---|
| 1. 코어를 `[1,6,40,41]`로 축소 | `CORE_ITEMS = (1, 6, 40, 41)` |
| 2. 10·11 optional, 탐지는 YELLOW 유지 | `OPTIONAL_ITEMS = (5,10,11,20,29,30)` → 집계 **YELLOW 1건**(`EQ_OPTIONAL_ITEM_ABSENT`, 항목별 결측 셀 수). 셀마다 findings 를 뿌리지 않아 소음도 줄었다 |
| 3. 5·20·29·30 코어 제외 | 위와 동일(데이터는 그대로 두고 게이트 강제만 해제) |
| 4. `EQ_PARENT_CHILD_INCOMPLETE` 강등 | RED → **YELLOW** |
| 5. `EQ_TIER2_SCOPE_GAP` 제거 | 룰 + `TIER2_CORE_ITEMS` + `load_tiers()` 삭제(유일한 호출부가 사라져 고아가 됨) |

**유지 확인:** `EQ_BS_IDENTITY` · `EQ_AOCI_ROLLFORWARD` · `EQ_AOCI_STOCK_FLOW_TIE` ·
`EQ_UNIT_SCALE_JUMP` · provenance 사이드카 RED 전부 살아 있음. 코어 4항목 결측 = 계속 RED.
owner-confirmed 억제 레지스트리 유지. `--selftest` **22/22**.

### Tier-2 15개사 처리 (지시에 없어 판단이 필요했던 부분)

`equity_tier2_stop.md` 의 "XBRL FS 없는 15개사 = 영구 결측 확정, 채우지 말 것"을 근거로
**census 예외 레지스트리에 등재**했다(`data/_gold/equity_census_exceptions.json`, 회사목록
근거 = 사이드카 `universe.tier2_companies` 14 + `tier2_still_missing` KR1098). 등재 안 하면
채울 경로가 없는 27건이 영구 RED 로 push 를 막는다. 이미 들어와 있는 Tier-2 행은 그대로 두고
항등식 검사는 계속 받는다.

### 남은 RED 21건 = 전부 owner 가 요구한 4개 항목 자체의 문제

- **AOCI(6) 결측 13건** — 한화생명 7분기 / 흥국생명 6분기. 같은 분기의 1/40/41 은 붙어 있어
  캐시는 정상이고 AOCI 계정 하나만 못 잡는 상태(account_id 변형 의심).
- **롤포워드 6건** — KB라이프 2023.3Q(328,699) / 한화손보 2025.4Q(3,198) / DB생명 2건(2,188 상수) /
  DB손보 2건(△463 상수).
- 위 19건 파서 발주: `inbox/parser/20260814T0130Z__validation__MULTI__equity_core4_gaps_after_scope_shrink.md`
- **삼성생명 `EQ_BS_IDENTITY` 2건(2025.2Q/3Q)** — 파서가 "DART 원본 캐시 품질 이슈, 우리쪽 수정
  대상 아님"으로 종결한 그 건(자산총계 318,858,553 두 분기 동일). 룰은 owner 지시대로 살려뒀으니
  **owner 결정 필요**: (a) 예외 등재 (b) 해당 2분기 자산총계를 화면에서 제외 (c) 그대로 RED 유지.

### 상태 변화 하나 — 이 마스터는 이제 실배포 아티팩트다

IFRS17.html 이 `equity_composition.json` 을 fetch 하기 시작해(어제 디자이너 반영) 게이트의
스테이징 강등이 자동 종료됐다. **`validate_data_contract.py` 현재 RED=21 = push 실제 차단.**
부수 발견: 배포 keep-list 를 유도하는 문서 2곳에 이 JSON 이 없어
`pytest tests/test_deploy_assets.py::test_docs_agree_with_what_pages_fetch` 가 FAIL 이다
(그대로 배포하면 라이브 404). publishing·designer 에 각각 발주했다.

---

**재검증 종결 (validation, 2026-08-14T06:20Z).** 게이트 독립 재실행으로 확인: `validate_data_contract.py` **RED=0 / YELLOW=261**(exit 0) · `--selftest` **25/25** · `pytest tests/test_deploy_assets.py` **1 FAIL**(designer/publishing 대기건 1개뿐, validation 소관 아님). 파서 재빌드(`IFRS17_BS.json` 14:42) 반영 후 17BS findings 40→42이고 삼성생명 `BS_IDENTITY` 2건·한화생명/흥국생명 AOCI 8건은 **소스 수정으로 소멸 확인**(예외 등재 0건). 잔여 42건 델타는 `inbox/parser/20260814T0620Z…ifrs17_bs_delta_after_ofs_rebuild.md`(iter 2). → `status: resolved`, `_resolved/` 이동.
