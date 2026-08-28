---
from: orchestrator
to: parser
created: 20260829T1100Z
status: answered
route: reparse
company: KR0070
period: 2024.4Q,2025.1Q
rule: PL_YTD_COLLAPSE_TO_ZERO
lane: ifrs17
iter: 2
---

## 미결 (orchestrator 작성 — owner 지적)

**ABL생명(KR0070) 2024.4Q·2025.1Q 의 item6 를 채운다.** 앞선 작업(`b2fa4e0`)이 산문 불일치를
이유로 비웠는데, **owner 지적대로 값은 있었고 산문 쪽이 더 넓은 개념이었다.**

지금 이 공란이 유일한 RED 을 만들고 있다.

```
RED  PL_YTD_COLLAPSE_TO_ZERO  에이비엘생명보험 2024.4Q
     "누계가 직전분기 → 이번분기 정확히 0.0 — FY 누계는 이렇게 사라지지 않는다
      (파생 값_당분기가 음수로 뒤집힘)"
```

item6 이 2024.3Q 37억 → 2024.4Q 0.0 이라 룰이 옳게 걸렸다. `0` 이 "진짜 0" 이 아니라
"안 채웠다" 였기 때문이다.

### 채울 값 (orchestrator 실측, 양쪽 소계 검산 통과)

**2024.4Q** (사업보고서, `당기` 열, 백만원):

```
예상 4종  359,217 + 5,854 + 85,676 + 11,332 = 462,079
발생 4종  360,329 + 7,314 + 81,443 + 12,407 = 461,493
item6 = +586백만원

수익 소계  462,079 +13,655 +88,926 +137,912 −15,188 +17,398 = 704,782   OK 공시일치
비용 소계  461,493 +68,207 +25,803 +137,912 −15,188 −17,948 = 660,279   OK 공시일치
```

**2025.1Q** (분기보고서, `당분기` 열, 백만원):

```
예상 4종  93,353 + 1,867 + 22,304 + 2,966 = 120,490
발생 4종  98,328 + 1,877 + 20,812 + 3,064 = 124,081
item6 = −3,591백만원

수익 소계  120,490 +2,592 +20,087 +34,763 −4,672 +5,054 = 178,314        OK 공시일치
비용 소계  124,081 +8,863 +2,606 +34,763 −4,672 −4,526 = 161,115         OK 공시일치
```

### 산문 불일치가 풀렸다 — 우리 계산이 옳다

앞선 작업이 이 두 분기를 비운 근거는 주석 37 산문과 안 맞는다는 것이었다. **산문이 4종보다
넓은 개념을 쓴다는 것이 두 분기 모두에서 확인됐다.**

| 분기 | 축 | 우리 4종 | 산문 | 차이의 정체 |
|---|---|---|---|---|
| 2024.4Q | 보험금 | △11.1억 | △270억 | `발생사고요소조정 25,803`(258억) 포함 — **4종 밖** |
| 2025.1Q | 보험금 | △49.75억 | △50억 | **정확히 일치** |
| 2025.1Q | 사업비 | +13.8억 | △17억 | `기타사업비용 3,050`(30.5억) 포함 → +13.8−30.5=△16.7 ≈ △17 — **4종 밖** |
| 2024.4Q | 사업비 | +17.0억 | △97억 | 미규명. 위 패턴상 4종 밖 항목 포함으로 추정되나 특정 못 함 |

**4종 범위는 이 저장소 정본 정의이고(보험금·손해조사비·유지비·재산관리비), 양쪽 소계가
원 단위로 닫히며, 같은 방법으로 뽑은 나머지 8개 분기는 이미 반영돼 있다.** 2024.4Q 사업비
축의 미규명 30.8억 상당은 남지만, 산문이 넓은 개념을 쓴다는 것이 두 축·두 분기에서
확인된 이상 이것만으로 값을 버릴 이유가 없다.

### 요청

1. 위 두 값을 item6 에 채워라. **직접 재현해서 같은 값이 나오는지 먼저 확인하고 넣어라**
   — orchestrator 실측을 그대로 믿지 말 것.
2. item7(기타)은 잔차 plug 이라 자동 감소한다. `item3 = item4+5+6+7` 이 두 분기에서 닫히는지 확인.
3. **`data/_gold/user_pl_cells.json` 의 KR0070 item7 override 를 먼저 확인해라.** 앞선 작업에서
   override 6건이 `item6=0` 전제로 계산돼 있어 고친 전례가 있다(2025.1Q 는 item6 를 안 채웠으니
   그대로 뒀다고 기록돼 있다). **2025.1Q override 가 남아 있으면 이번에 같이 재계산해야 한다.**
   안 그러면 PL_BRIDGE 가 깨진다.
4. 반영 후 `scripts/validate_data_contract.py` 를 돌려 `PL_YTD_COLLAPSE_TO_ZERO` RED 이
   해소되는지 확인하고 로그를 답변에 붙여라.
5. 골든 `tests/test_pl_breakdown_golden.py` `--update` + **지문 갱신도 같이**(아래).

### 새 운영 계약 — 반드시 지킬 것

validation 이 골든 입력지문 게이트를 신설해 훅에 배선했다(커밋 `0ebb0ca`).
**마스터를 재빌드하면 골든 `--update` 뒤에 `scripts/validate_golden_input_fingerprints.py` 의
지문 갱신도 같이 돌려야 한다.** 안 하면 다음 push 가 막힌다. 그 스크립트를 먼저 읽고 정확한
갱신 경로를 확인해라. **스크립트 로직은 validation 소관이니 고치지 마라 — 데이터 갱신만.**

### 하지 말 것

- `index.html`·`IFRS17.html` 등 HTML 금지.
- `CSM_amortization.json`·viz 상각 패널·xlsx `CSM상각` 시트 금지 — 다른 에이전트가 지금 쓰고 있다.
- **xlsx sync 는 맨 마지막에, 직전에 `git status` 확인하고 실행해라.** 사후검증(다른 시트 값
  동일성)이 실패하면 덮어쓰지 말고 보고해라.
- 브랜치 변경 금지. `git push` 금지. `git add -A` 금지.

원문: `data/dart/FY2024_Q4/raw/KR0070_.../*.xml`, `data/dart/FY2025_Q1/raw/KR0070_.../*.xml`

## 답변 (recipient 작성 — 처리 후)

item6 을 두 분기에 채웠다. **orchestrator 실측을 그대로 믿지 않고 직접 raw XML 에서 두 가지
독립 경로로 재현했고, 정확히 일치했다.** gold override 함정도 실제로 있었고 재계산했다.
`PL_YTD_COLLAPSE_TO_ZERO` RED 은 해소됐다(SUMMARY RED=0).

### (1) 직접 재현 — orchestrator 실측과 정확히 일치

`_ABL_ITEM6_SUPPRESS_QUARTERS`(`scripts/pl_breakdown/tier2.py`)에서 두 분기를 뺀 뒤, **기존
코드를 건드리지 않고** 두 개의 독립 스크립트로 raw XML 을 재파싱해 대조했다:

```
scripts/_probes/abl_yesilcha_full_probe.py        (인라인 재구현, 08-28 선례에서 이미 검증된 로직)
scripts/_probes/abl_yesilcha_verify_handler.py     (실제 extract_tier2_abl 핸들러를 직접 호출)

2024.4Q  item6 = 586    (orchestrator: +586백만원)   OK 일치
2025.1Q  item6 = -3,591 (orchestrator: -3,591백만원)  OK 일치
```

핸들러 재검증에서 **다른 8개 분기(2024.1-3Q, 2025.2-4Q, 2026.1-2Q)는 item6_NEW == item6_OLD,
item11_NEW == item11_OLD 로 완전 무변화** — 이번 수정이 그 8분기에 회귀를 만들지 않았다.

### (2) 산문 "넓은 개념" 재확인 (owner 지적의 근거)

마스터 데이터로 교차검증: 2025.1Q item16(기타사업비용) = 3,049.55백만원 = 30.5억 — 티켓이
말한 "기타사업비용 3,050" 과 일치, +13.8−30.5≈△16.7≈산문 △17억. 2024.4Q 발생사고요소조정
25,803백만원(=258억)도 raw 재확인, △11−258=△269≈산문 △270억. 둘 다 "4종 밖" 경계는
`_resolved/20260828T1400Z` 기존 owner 결정과 동일하게 적용했다(새 규칙 발명 안 함).
2024.4Q 사업비 축 잔여 미규명분은 티켓이 이미 "이것만으로 값을 버릴 이유가 없다"고 판단했으므로
그대로 미규명 상태로 둔다(추가 조사 안 함).

### (3) gold override 함정 — 실제로 있었다, 재계산함

`data/_gold/user_pl_cells.json` KR0070 전체 14건 override 를 먼저 전수 확인했다
(`scripts/_probes/abl_yesilcha_2024q4_2025q1_check_gold.py`). item7 override 7건 중 5건은
08-28 에 이미 재계산됐고(`FOLLOW-UP 2026-08-28` 마커), **2025.1Q 만 그때 item6 이 억제
상태라 손 안 대고 남아 있었다**(-5,947.368229, item3-item4override(20087)-item5-item6(0)
가정으로 계산됨). 2024.4Q 는 애초에 item7 override 자체가 없다(census 로 확인 — 손댈 것 없음).

08-28 선례와 동일한 공식으로 재계산(신설 `scripts/_probes/abl_yesilcha_fix_gold_overlay_2025q1.py`,
`FOLLOW-UP 2026-08-29` 마커, idempotent):

```
item7_new = item7_old - item6_new = -5,947.368229 - (-3,591.0) = -2,356.368229
검산(item4 override 값 20,087 사용): 17,198.63 - 20,087 - 3,059 - (-3,591) = -2,356.37   OK
```

### (4) 전후 combo-diff — 셀 손실 0

`pl_breakdown_master.json` 패치(`abl_yesilcha_apply_patch.py` 재실행, idempotent 확인됨):
**딱 4 키** (KR0070 × {item6,item7} × {2024.4Q,2025.1Q}) 변경, 11546행 → 11546행 불변,
회사=KR0070 단일, 항목={6,7} 단일로 스코프 체크 통과.

`build_root_masters.build_pl()` 개별호출(`main()` 미실행) 전후 diff(신설
`abl_2024q4_2025q1_build_pl_and_diff.py`): **6 키** 변경 — 위 4개 + item6/item7 **2025.2Q 의
값_당분기만**(YTD 는 불변) — Q1→Q2 flow-diff 리플로 예상된 부수효과(`_flow_dangi` 설계상 당연).
11546행 → 11546행 불변, 회사·항목 스코프 동일.

`validate_master_tables.py --no-build`: `pl_bridge:3025P/13F/522S/0NEW` — **0NEW = 회귀
없음**(13건 전부 기지 등록된 무관 회사). 에이비엘생명보험 관련 PL_BRIDGE FAIL 0건(있는 건
전부 무관 섹션: QoQ_warn/sensitivity/OCI_vs_BS_AOCI YELLOW).

폐쇄식 직접 검산(배포본 값 기준):
```
2024.4Q  item3 = item4+item5+item6+item7 = 88926+12282+586-57291.914754 = 44502.085246 ~= 44502.09  OK
2025.1Q  item3 = item4+item5+item6+item7 = 20087+3059-3591-2356.368229 = 17198.631771 ~= 17198.63   OK
item8=item9+item10+item11+item12 는 item11/12 미변경이라 양쪽 분기 그대로 닫힘(불변)
```

### (5) 타깃 RED 해소 확인

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_data_contract.py
```
반영 전 유일 RED 이던 `PL_YTD_COLLAPSE_TO_ZERO`(에이비엘생명보험 2024.4Q)가 출력에서 완전히
사라짐 — grep 0건. 4개 섹션 전부 `RED=0`:
```
1. COMPLETENESS CENSUS      RED=0 YELLOW=72
2. AS-OF MATCH+EFFECTIVE    RED=0 YELLOW=0
3. CROSS-SOURCE tolerance   RED=0 YELLOW=18
4. DOMAIN IDENTITY          RED=0 YELLOW=2
SUMMARY  RED=0  YELLOW=92  provisional=False
```

### (6) 골든 + 신설 지문 게이트 — 둘 다 갱신 (오늘 신설 운영계약, `0ebb0ca`)

**PL 골든**(빌더 재실행 없음 — 이 브랜치는 raw git-purge 로 `build_pl_breakdown.py` 전체
재실행이 파괴적이라 KR0032/08-28 선례와 동일하게 on-disk 아티팩트만 재해시):
```
python tests/test_pl_breakdown_golden.py --update
```
diff: `sha256_master` 만 이동(f8de5b...→f2961a...). `sha256_coverage`·`master_rows`(11546)·
`company_quarters`(356)·`coverage_rows`(426)·`non_null_values`(9994) 전부 불변 —
coverage 는 item6 이 0→값 으로 바뀐 것이지 None→값 이 아니라서(0 도 이미 non-null) 안 움직인
게 맞다.

**신설 지문 게이트** (`scripts/validate_golden_input_fingerprints.py`, 로직은 validation
소관이라 안 건드림 — `--update` 실행만):
```
--update 전: 다른 5개 spec(ifrs17_bs/viz_csm_waterfall/viz_ifrs17_panels/dividend/
  post_transition) 전부 "ok" 확인(공유 워크트리에서 동시작업 중인 CSM상각 as-of 에이전트의
  in-flight 상태를 지문에 박제하지 않기 위한 사전 clean 체크, git status 로도 확인).
--update 전 대조: RED=2 (pl_breakdown 만 CODE_MOVED+FIXTURE_MOVED, 나머지 5개 무관)
--update 후 재대조: RED=0 clear
diff 범위: pl_breakdown spec 의 code_sha256(tier2.py 편집)·fixture_sha256(골든 갱신)·
  outputs.sha256_master 만 이동. code_files 목록 자체는 불변(파일 추가/삭제 없음).
  나머지 5개 spec 은 byte-identical.
```

### (7) 회귀 확인 — 오프라인 pytest 전체 스위트

**468 passed / 2 skipped / 1 failed (456.90s)**. 그 1 fail 은
`archive/2026-08_equity_composition/test_equity_composition_golden.py::test_builder_output_matches_golden`
— 아카이브된(2026-08-14) 모듈의 fixture 파일 자체가 디스크에 없는 `FileNotFoundError`, 내
변경과 무관, 종전 세션(08-28 티켓)에도 동일 원인으로 기록된 pre-existing 패턴. 2 skip 은
`RUN_PL_GOLDEN`/`RUN_IFRS17_BS_GOLDEN` opt-in 게이트(이 브랜치에서 의도적으로 미실행).

### (8) xlsx sync — 맨 마지막, 사후검증 통과

직전 `git status --porcelain -- insurequant_master_tables.xlsx` 로 clean 확인(세션 시작
시점 스냅샷엔 M 이었으나 실행 시점엔 이미 다른 작업이 커밋되어 clean 이었다) 후:
```
python scripts/sync_master_xlsx_sheet.py "손익분해PL"
```
10셀 편집((4)의 6키 × 값/값_당분기, 2025.2Q 는 값_당분기만) · 행추가 0 · 행삭제 0 (11546행
불변). 출력: **"검증 OK — 손익분해PL 11546행 × 9열 마스터와 완전 일치, 나머지 시트 값
동일"** — 동시작업 중인 CSM상각 시트를 포함해 다른 모든 시트가 셀 단위로 무변화임을
스크립트 자체 사후검증이 확인했다.

### 파일 · 재현 명령

- `scripts/pl_breakdown/tier2.py`: `_ABL_ITEM6_SUPPRESS_QUARTERS = set()`(기존
  `{"2024.4Q","2025.1Q"}`), 상단 주석·`_abl_note26_yesilcha` docstring 갱신(해소 경위 기록).
- `data/dart/viz/pl_breakdown_master.json` / `PL_breakdown.json`: KR0070 item6/7, 2024.4Q·
  2025.1Q(+2025.2Q 값_당분기 리플) — surgical patch, `build_pl()` 개별호출로 전파.
- `data/_gold/user_pl_cells.json`: KR0070 item7 2025.1Q override 재계산(1건).
- `insurequant_master_tables.xlsx`: `sync_master_xlsx_sheet.py "손익분해PL"` cherry-pick.
- `tests/fixtures/pl_breakdown_golden.json` / `tests/fixtures/builder_input_fingerprints.json`:
  `--update` 재생성(둘 다 재해시만, 빌더 미실행).
- 재현: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe
  scripts/_probes/abl_yesilcha_full_probe.py`(직접 재현),
  `abl_yesilcha_verify_handler.py`(핸들러 대조),
  `abl_yesilcha_2024q4_2025q1_check_gold.py`(gold 전수 확인, 신설),
  `abl_yesilcha_apply_patch.py`(마스터 패치, idempotent),
  `abl_yesilcha_fix_gold_overlay_2025q1.py`(gold 재계산, 신설, idempotent),
  `abl_2024q4_2025q1_build_pl_and_diff.py`(build_pl() 전후 combo-diff, 신설),
  `abl_2024q4_2025q1_pre_state.py`(패치 전 스냅샷 덤프, 신설).

commit: `d60bb83`

### 후속 필요 (orchestrator/owner 재확인)

- gold override 재계산(위 (3))은 08-28 선례와 동일 공식을 그대로 적용한 것이지만, 파생값
  수정이라 orchestrator 재확인을 요청한다.
- 2024.4Q 사업비 축의 미규명 잔차(주석37 산문 대비)는 여전히 미규명이다 — 티켓 지시대로
  "이것만으로 값을 버릴 이유가 없다"는 판단을 그대로 따랐고 추가 조사는 하지 않았다.
