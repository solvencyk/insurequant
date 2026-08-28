---
from: orchestrator
to: parser
created: 20260828T2350Z
status: answered
route: reparse
company: MULTI
period: MULTI
rule: ARTIFACT_STALE
lane: ifrs17
iter: 1
---

## 미결 (orchestrator 작성)

**`IFRS17_BS.json` 이 빌더 산출보다 낡았다. 보증준비금(항목8) 7셀이 배포 마스터에서 빠져 있다.**

```
tests/test_ifrs17_bs_golden.py  FAILED (434초)
  rows: 6852 -> 6859  (+7)
  항목8 보증준비금 적립액: 189 -> 196
```

디스크의 `IFRS17_BS.json` 은 6,852행·항목8이 189개다. 즉 **빌더를 돌리면 7셀이 더 나오는데
배포본에는 없다.** `IFRS17.html` Panel 1(BS T자)이 이 마스터를 읽으므로 화면에 안 보이는 값이다.

### 원인 (orchestrator 특정 — 오늘 OCI 작업 탓이 아니다)

```
2026-08-21  0c04537   골든 fixture + IFRS17_BS.json 마지막 동시 갱신
2026-08-26  645d74c   validation 레인이 data/dart/_fs_api_cache 에 데이터 추가
2026-08-28  (오늘)     빌더가 새 캐시를 보고 +7행, 마스터는 08-21 상태 그대로
```

`build_ifrs17_bs.py` 는 `data/dart/_fs_api_cache/*.json` 을 읽는다. 캐시에 데이터가 들어왔는데
BS 마스터를 재빌드하지 않아 생긴 드리프트다. **이틀 동안 아무도 몰랐다.**

오늘 항목32 작업(`d634492`)이 `scripts/fetch_dart_fs.py` 를 고쳤지만 **+141/−0 순수 추가**이고
BS 빌더가 그 모듈에서 쓰는 것은 `resolve_corp`·`REPRT` 뿐으로 둘 다 미변경이다. 무관하다.

### 요청

1. **7셀이 무엇인지 먼저 특정해라.** 어느 회사·분기의 보증준비금인지 열거하고, **원문으로
   값이 맞는지 확인해라.** 캐시에 새로 생긴 데이터라고 자동으로 옳은 것은 아니다.
2. 맞으면 `build_ifrs17_bs.py` 를 돌려 `IFRS17_BS.json` 을 갱신하고 골든을 `--update` 로
   재생성해라. 커밋에 위 타임라인과 7셀 목록을 근거로 남겨라.
3. **화면 영향을 보고해라.** Panel 1 BS T자에서 어느 회사·분기의 보증준비금이 0/빈칸에서
   값으로 바뀌는지. 이건 owner 가 볼 숫자다.
4. 마스터 xlsx `17BS` 시트도 `scripts/sync_master_xlsx_sheet.py` 로 동기화해라.

### 같이 처리할 것 — 이 골든이 push 게이트에 없다 (진짜 문제)

**이 골든은 434초(7분 14초)다.** `scripts/prepush_check.py` 의 전체 예산이 ~5분이라 훅의 오프라인
테스트 세트에 안 들어 있을 개연성이 높다. 그래서 08-26 드리프트가 이틀간 검출되지 않았다.

**확인해서 보고해라:** `prepush_check.py` 가 이 골든을 실제로 돌리는가. 안 돌린다면 그 사실이
`CLAUDE.md` 의 "배선했다 ≠ 강제된다" 항목에 그대로 해당한다. 대안을 제안해라 —
전체 빌더 재실행 대신 **마스터 파일의 행수·항목별 카운트만 캐시와 대조하는 초고속 체크**(수초)를
훅에 넣고 무거운 골든은 별도로 두는 형태가 후보다. **제안만 하고 임의로 훅을 고치지는 마라.**

### 하지 말 것

- `PL_breakdown.json`·`data/dart/viz/pl_breakdown_master.json` 을 건드리지 마라. **다른
  에이전트가 지금 그 마스터에 쓰고 있다**(ABL 예실차). `IFRS17_BS.json` 만 네 대상이다.
- `index.html`·`IFRS17.html` 금지. 브랜치 변경 금지. `git push` 금지. `git add -A` 금지.
- `build_root_masters.py` 의 `main()` 통짜 실행 금지.
- 마스터 xlsx 는 `sync_master_xlsx_sheet.py` 로 `17BS` 시트만. openpyxl 재저장 금지.

## 답변 (recipient 작성 — 처리 후)

**결론부터: 진단된 원인(`645d74c`)은 틀렸다. 진짜 원인은 두 개, 서로 다른 회사, 서로 다른
결론이다 — 한쪽은 반영하지 않았고(오탐), 한쪽은 반영했다(놓친 진짜 드리프트).**

### 0. `645d74c` 원인 가설은 반증됨

`645d74c`가 추가한 CFS 캐시 30개(`data/dart/_fs_api_cache/00120216_2024_11011_CFS.json`
등)를 직접 열어 확인했다. KR0010(KB손해보험) 대상 (회사,분기)은 OFS가 이미 items 1/2/3을
갖고 있어 `extract_quarter()`의 CFS fallback이 애초에 안 걸리고, `dart_GuranteeReserve`
태그·`보증준비금` 계정명 어느 것도 KB의 OFS/CFS 캐시 26개 파일 전체에 없다(재현:
`scripts/_probes/probe_kb_ofs_cfs_item8.py`). 645d74c는 이 드리프트와 무관하다.

### 1. 7셀 정체 — KR0010(KB손해보험), item8(보증준비금 적립액), 2024.4Q+2025.1Q~2026.2Q

`data/_derived/bs_carry_forward_cells.json`에 세션 시작 시점부터 남아 있던 미커밋 diff
(KR0010 item8 6분기 추가, `rollforward_cell_count` 251→257)가 첫 단서였다 — 이전 세션
누군가 이미 이 재빌드를 한 번 돌려봤다가 `IFRS17_BS.json`만 되돌리고 사이드카는 안
되돌린 흔적. 재현: `scripts/_probes/probe_kr0010_bs_drift.py`.

**원문 대조** (`scripts/_probes/probe_kb_parse_filing_item17.py`, `parse_filing()`을
KR0010의 전 raw 필링에 돌려 item17/18과 "보증준비금" 텍스트 위치를 대조):
KB손해보험 필링에 "보증준비금...0"이라는 표 행이 2023.1Q~2024.4Q 내내 실재하지만
`parse_filing()`은 **2024.4Q(사업보고서)에서만** 이를 item17=0.0으로 정확히 추출한다
(다른 분기는 표 구조 차이로 안 잡힘, 2025.1Q부터는 그 행 자체가 필링에서 빠짐). 이
값이 item5/6/7/8 공용 롤포워드(`_rollforward_reserve_series`)를 타고 2025.1Q~2026.2Q로
forward-fill(6칸)되어 2024.4Q 진짜값 1개 + 이월 6개 = 7셀, 골든이 지목한 델타와 정확히
일치했다.

**그런데 값이 틀렸다.** 재빌드 후 `validate_data_contract.py`를 돌리자 **신규 RED
7건**이 떴다:
```
RED [IFRS17_BS] R-RSV-8  KB손해보험 2024.4Q / 2025.1Q~2026.1Q (6건)
  보증준비금은 실측상 생명보험 전용(16사)인데 손해보험사에 값 0.0이 실렸다 —
  미공시(N/A)를 0/값으로 채우면 업권 합계·census가 오염된다
```
(`scripts/validate_statutory_reserves.py:396`, 회사군이 100% 단일 업권일 때 자동
발화하는 파생 룰.) 직접 census(`scripts/_probes/probe_item8_holders_by_biztype.py`)로
재확인: 이 마스터에서 item8이 nonzero인 회사 16/16이 전부 생명보험이고 손해보험은
0사다 — 보증보험 전문사인 서울보증보험조차 item8 행이 아예 없다. 즉 KB손해보험 필링의
"0"은 **손보사 표준 서식이 법정준비금 4종을 보일러플레이트로 나열하다 해당 없는
개념에 찍은 0**이지 진짜 disclosure가 아니다.

**결정: 반영하지 않았다.** "틀린 값을 싣느니 빈 칸" 원칙에 따라 `build_ifrs17_bs.py`의
Tier-1 notes-fallback(item17→item8 매핑)에 `생손보여부 != "생명보험"`이면 skip하는
가드 10줄을 추가해 재발을 코드 레벨에서 막았다(수기 패치는 다음 빌드에서 되살아나므로).
재빌드 후 census 재확인: item8 zero-only 보유사 0사로 원복.

### 2. 티켓에 없던 진짜 드리프트 — KR0069(삼성생명보험), 64셀, 반영함

row-count(+7)만 보는 진단은 **값만 바뀌는 셀**을 놓친다. 셀단위 diff
(`scripts/_probes/diff_ifrs17_bs_rebuild.py`, old-backup vs 재빌드 전수 비교)로
KR0069의 2024년 4개 분기 × 16항목(자산총계·부채총계·자본총계·AOCI + 세부 12종: 현금,
FVTPL/FVOCI금융자산, 상각후원가금융자산, 재보험계약자산, 유형자산, 보험/재보험/투자
계약부채, 차입부채, 기타부채, 이익잉여금)이 연결(CFS) 값에서 별도(OFS) 값으로 바뀌는
것을 발견했다. 예: 자산총계 2024.1Q 315,771,608→280,470,367백만원(-11.2%), 차입부채
2024.4Q 19,958,867→0백만원(-100%).

**원인**: `8c1666b`(2026-08-26 02:17, "fix: PL을 별도 기준으로 — 회사별 감사 369셀")이
삼성생명 2024년 OFS FS-API 캐시 파일(`00126256_2024_1101{1,2,3,4}_OFS.json`) 자체를
정정했다(`git log --follow`로 확인). 그 전엔 이 OFS 캐시에 자산/부채/자본 태그가
없어서 `extract_quarter()`의 "OFS에 1/2/3 없으면 CFS로 폴백" 규칙이 걸려 BS 마스터가
줄곧 연결 값을 쓰고 있었다. 8c1666b가 PL 목적으로 OFS 캐시를 정정하면서 BS에 필요한
태그도 같이 채워졌는데, BS 마스터가 그 이후 한 번도 재빌드되지 않아 드리프트로 남았다.

**검증**: 신·구 값 모두 자산=부채+자본이 원 단위까지 정확히 닫힌다(예: 신규값
280,470,367=243,922,473+36,547,894) — 연결/별도 어느 쪽도 산수 버그가 아니라 순수
기준 전환이다. 캐시 파일의 원문 태그값과 신·구 마스터값이 정확히 일치함도 직접 대조
확인(`scripts/_probes/probe_kr0069_basis_flip.py`).

### 3. 재빌드 + 골든

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/build_ifrs17_bs.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe tests/test_ifrs17_bs_golden.py --update
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe -m pytest tests/test_ifrs17_bs_golden.py -v
```
결과: `IFRS17_BS.json` 6852행(1번의 KR0010 가드로 순변화 0, item8=189 원복) — combo-diff
KR0069 64건 EDIT 외 added=0/removed=0. 골든 PASSED **514.02초**(가드 추가 전 버전으로
1차 실행도 PASSED 492.42초 — 재현성 확인용, 최종 반영본 아님). `validate_data_contract.py`
RED 7(R-RSV-8, 전부 위 KR0010 셀)→**0**. 잔존 RED 1건(`PL_YTD_COLLAPSE_TO_ZERO
에이비엘생명보험`)은 `git status`로 `PL_breakdown.json`이 내 diff에 없음을 확인 —
동시 세션(ABL 예실차)의 무관한 작업.

### 4. 화면 영향

IFRS17.html Panel 1(BS T자, `eqx` 소스)에서:
- **삼성생명보험 2024.1Q~2024.4Q**: 자산총계·부채총계·자본총계·AOCI 및 세부 12항목이
  전부 하향 재조정(별도 기준, 차입부채는 최대 -100%)되어 표시된다. owner가 화면에서
  볼 실측 변화 — 다른 분기(2023·2025·2026)는 원래부터 별도 기준이라 무변화.
- **KB손해보험**: 전 분기 화면 변화 없음(item8 행이 계속 부재 — 세션 시작 전 라이브
  상태와 동일하게 유지, 의도한 결과).

### 5. prepush 훅 — 골든 실제로 안 돈다, 제안만 남김(훅은 손대지 않음)

`scripts/prepush_check.py:140-168`을 직접 읽었다. `test_ifrs17_bs_golden.py`는 훅의
`fast` 리스트에 **없다** — 주석(L142-143)이 이유를 명시한다: "느린 것(ifrs17_bs
~2분, pl_breakdown ~95초 opt-in)은 뺀다". 이건 CLAUDE.md가 경고하는 "배선을 잊음"
케이스는 아니다(문서화된 의도적 제외, `pl_breakdown_golden`과 같은 opt-in 패턴). 하지만
**그 제외 사유 자체가 4배 이상 틀렸다** — 이번 세션 두 차례 실측 492.42초·514.02초, 둘
다 "~2분"이 아니라 ~8분대다. `tests/test_push_gate_wiring.py`는 `scripts/validate_*.py`
하드게이트의 배선 여부만 감시하고, `tests/test_*_golden.py`의 opt-out 목록이나 그
사유(추정 소요시간)의 정확성은 아무것도 감시하지 않는다 — "의도적으로 뺐다"와 "그
사유가 계속 맞다"는 별개인데 후자를 확인하는 장치가 없다.

**제안(적용 안 함)**: 무거운 골든을 훅에 그대로 넣는 대신, `tests/fixtures/
ifrs17_bs_golden.json`에 입력 지문(`data/dart/_fs_api_cache/*.json` +
`data/dart/FY*/raw/**/*.xml` + `data/dart/viz/bs_manual_overrides.json`의 파일명+
mtime+size를 묶은 해시 하나, JSON 파싱 없이 `Path.stat()`만 — 수초)을 같이 저장해
두고, 훅에 그 지문을 재계산해 골든 fixture에 박제된 값과 비교하는 초저비용 staleness
sniff를 추가하는 안을 제안한다. 불일치 시 "입력이 마지막 골든 갱신 이후 움직였다,
push 전에 무거운 골든을 돌려라"로 RED/WARN — 이번 사고처럼 캐시가 바뀌었는데 마스터가
안 따라간 상태를 수초 만에 잡는다. `pl_breakdown_golden`(opt-in, RUN_PL_GOLDEN=1)도
같은 노출이라 같이 적용하는 것을 후보로 함께 제안한다. **채택 여부와 실제 훅 수정은
owner/orchestrator 결정 사항.**

### 6. 잔여 위험 (미수정, 기록만)

item8의 Tier-2 코드경로(`build_ifrs17_bs.py` 라인 ~610-633, TIER2 15사 중 손보 6사:
예별·AIG·악사·하나·신한이지·카카오페이손보)는 KR0010과 같은 매커니즘(parse_filing
경유)을 쓰지만 1번의 가드가 적용 안 돼 있다. census 확인상 현재 이 6사는 전부 item8
행이 0개(문제가 아직 발현 안 함)라 손대지 않았다 — 이 경로에서 향후 같은 패턴(0-only
손보 행)이 나타나면 같은 가드가 필요하다.

### 실행 로그

- 산출 변경: `IFRS17_BS.json`(6852행 유지, KR0069 64셀 값 정정), `scripts/
  build_ifrs17_bs.py`(+10줄, item8 생손보여부 가드), `tests/fixtures/
  ifrs17_bs_golden.json`(재생성).
- xlsx: `scripts/sync_master_xlsx_sheet.py "17BS"` 2회 실행(과정 중 KR0010 오탐이 잠깐
  반영됐다가 최종 수정에서 제거), 매회 "나머지 시트 값 동일" 자체검증 통과. **xlsx는
  커밋 대상에서 제외** — 동시 세션이 같은 파일에 `손익분해PL` 시트 변경을 이미 staged
  중이라(`git status` 확인), 디스크상 `17BS` 시트는 이미 올바르게 반영된 상태로 두고
  그 세션이 다음에 커밋할 때 두 시트분이 함께 들어가도록 함.
- 미건드림 확인: `PL_breakdown.json`·`data/dart/viz/pl_breakdown_master.json`(git status
  로 diff 없음 확인), `index.html`·`IFRS17.html`, 브랜치(`fix/csm-product-segmented-
  columns` 유지), `git push` 없음, `git add -A` 없음(개별 파일만).
- 커밋: `35bfc6d` ("parser(ifrs17): IFRS17_BS.json 재동기화 -- KR0010 R-RSV-8 오탐 배제 +
  KR0069 기준정정 반영").

status: answered — ⑤(훅 대안 채택 여부)는 owner/orchestrator 결정이 필요해 자기완결로
닫지 않았다. ⑥은 비차단 기록.
