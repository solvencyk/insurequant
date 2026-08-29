---
from: orchestrator
to: parser
created: 20260830T0200Z
status: answered
route: reparse
company: KR0079
period: MULTI
rule: CSM_WIDE_PRODUCT_STAGE_LOSS
lane: ifrs17
iter: 1
---

## 미결

`20260825T2200Z` 는 §2(gold 출처 44건)만 처리하고 **status: answered** 로 닫혔다.
그 §1 이 미착수로 남았고, 처리 과정에서 **같은 코드 경로의 두 번째 결함**이 새로 확정됐다.
둘은 같은 표(미래에셋 상품별 WIDE 측정요소표)를 읽는 같은 경로라 **한 번에 고쳐야 한다.**

### A) 세 번째 라벨 변형 — 항목5 가 통째로 항목4 에 흡수된다

`20260825T2200Z` 답변이 raw 로 확정한 것:

- KR0079 의 상품별 WIDE 표에서 CSM상각(항목5) 행 라벨이
  **`보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진`** 이다.
- 이 라벨이 `viz_build_csm_waterfall.py::extract_stages()` / `block_stages()` 패턴에 **없다.**
  → 항목5 = `None` → `build_csm_waterfall_master.py` L1198 의 잔차식(`... or 0`)이
  항목5 를 **항목4 에 통째로 흡수**한다.
- 실측 영향: KR0079 **2025.2Q · 2025.3Q · 2026.1Q**. 2025.3Q 는 흡수 결과
  `was = -1864.4` 라는 틀린 값을 냈고 gold 가 그걸 덮어써서 화면이 우연히 맞았다.
- **이건 2026-08-29 71st pass(`9a067dd`)가 고친 두 변형(부모헤더 폴백 / 줄바꿈 공백)과 다른
  세 번째 변형이다.** 같은 WIDE 상품별 포맷을 쓰는 **다른 회사에도 영향 가능** — 회사를
  KR0079 로 좁히지 말고 전수로 확인할 것.

### B) `20260825T2200Z` §1 — "기타" 상품 블록 누락, 범위가 넓어졌다

원 티켓은 **항목1(기말잔액) 6.52억** 차이로만 잡았는데, §2 처리 중 확대 확인됐다:

- KR0079 2025.4Q 는 **항목2 diff 만 38.18억** — "기타" 블록이 잔액뿐 아니라
  **상각·이자 등 다른 스테이지에서도 같이 빠지고 있다.** 즉 누락은 항목1 한 칸이 아니라
  **항목2~6 전체**다.
- 원 티켓의 확정 사실(그대로 유효): 원수 CSM 측정요소표가 상품별(사망/건강/연금/저축/기타)
  5개 SEPARATE 블록. FY2024.4Q 기말 5블록 합 = 785,941+883,688+239,327+168,607+**649**
  = 2,078,212백만 = **20,782.12억**. FY2025.1Q 기초·FY2025.2Q 반기 WIDE 표
  (`2,078,212,068,979원`)까지 일치. 그런데 `waterfall_for_dir` 는 **20,775.6억**.

### C) 표 자체를 못 찾는 케이스 (같이 볼 것, 고칠지는 판단)

KR0079 **2023.1Q** 는 상품별 로마숫자 캡션 표라 `extract_measurement_tables()` 의
score=3 (threshold 5 미달)로 **전량 탈락**, `waterfall_for_dir` 가 `src=None` 을 반환한다.
현재는 gold 6건이 그 자리를 메우고 있다(출처 확인 완료). A/B 를 고치는 김에 스코어러가
이 표 형태를 잡을 수 있는지 보고, 임계값을 함부로 낮추는 게 안전하지 않으면 **안 고치고
그 판단 근거를 적을 것.**

## 요청

1. **합산·라벨 경로의 결함 지점을 코드로 특정**하라. A 와 B 가 같은 함수인지 다른
   지점인지부터 확정할 것.
2. **고치기 전에 전 분기·전 회사 스윕으로 영향범위를 먼저 확정**하라. 원 티켓의 지시가
   그대로 유효하다: **"셀 2~3개만 고치면 안 본 분기와 새 불일치를 만든다."**
   WIDE 상품별 포맷을 쓰는 회사가 KR0079 뿐인지 전수로 확인할 것.
3. 스윕 결과를 근거로 **한 번에 정정**하고, 정정 전후 마스터 diff 를 셀 단위로 남겨라.
4. 고친 뒤 **gold override 가 여전히 필요한지 재판정**하라. 코드가 옳은 값을 내게 되면
   그 자리의 gold 는 불필요해지거나(제거 후보), 반대로 **gold 가 틀렸다는 증거**가 된다.
   **단 gold 값 삭제·변경은 이 티켓에서 하지 말고 후보 목록만 만들 것** — 아래 (D) 참조.

### D) 값 변경이 걸린 미결 1건 — 손대지 말고 목록만

`20260825T2200Z` 답변 (B): **KR0079 2025.2Q 항목4/항목5**.
raw 재구성 = 항목4 **-685.50** / 항목5 **-992.07**, gold = **-886.27** / **-791.3** —
**200.77억씩 반대 방향**으로 어긋나고 합계(-1677.57)는 동일해 폐쇄식은 안 깨진다.
같은 회사 2025.3Q·2026.1Q 는 같은 방법으로 raw=gold 완전 일치라 **2025.2Q 만 이례적**이다.
A 를 고치면 빌더가 raw 쪽 배분을 내게 될 텐데, **그렇다고 gold 를 갈아끼우지 마라.**
어느 쪽을 채택할지는 validation 판단이다. 고친 코드의 산출값을 티켓에 적어두면 된다.

## 하지 말 것

- `build_root_masters.py` main() 통짜 실행 금지 — `build_csm` 개별 호출 + combo-diff.
- `data/_gold/user_csm_cells.json` 의 `값`/`was` 변경 금지(제거·수정 후보 목록만).
- `index.html`·`IFRS17.html`·`public_exports/`·`scripts/validate_*`·`prepush_check.py` 금지.
- 브랜치 변경 금지(`fix/csm-product-segmented-columns`), `git push` 금지, `git add -A` 금지.
- python 은 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe` 풀패스,
  UTF-8(BOM 없음), 멀티라인 `python -c` 인라인 Bash 금지.

**골든**: `viz_build_csm_waterfall.py` 를 고치면 `tests/test_viz_csm_waterfall_golden.py`
가 막는다. 산출이 **의도적으로** 바뀐 것이므로 손으로 해시 고치지 말고 `--update` 로
재생성 + 커밋 메시지에 이유를 남길 것. 그 빌더는 산출 JSON 을 **인플레이스로 덮어쓰므로**
실행 전 백업하고 예외 시 복구할 것.

## 답변 (parser 작성 — 처리 후)

**A·B 둘 다 코드로 고치고, 전사 스윕 → 마스터 반영까지 완료. 항목C는 조사만 하고 미수정
(판단 근거 아래).**

### (1) A·B는 같은 함수인가

**다른 파일·다른 함수다.**

- **A (항목5 라벨 세 번째 변형)**: `scripts/viz_build_csm_waterfall.py`의
  `STAGE_PATTERNS["amortization"]` 리스트(공유 딕셔너리). KR0079의 실제 행 라벨은
  `보험수익, 서비스의 이전으로 당기손익에 인식한 보험계약마진`인데, 기존 패턴 중
  가장 가까운 `당기손익으로 인식한 보험계약마진`과 조사 하나(`손익에` vs `손익으로`)가
  달라 substring 불일치였다. 흥미롭게도 이 정확한 문구가 **이미 주석에 인용되어 있었다**
  (line 121-123, "2026.2Q 반기보고서부터... `서비스의 이전으로 당기손익에 인식한
  보험계약마진` → 아래 문구로 어순 변경" — 그 주석이 가리키는 OLD 라벨 자체가 패턴
  리스트엔 없었다). 이 딕셔너리는 `extract_stages()` → `find_csm_leaf_cols()`가 소비하고,
  `build_csm_waterfall_master.py`가 그 함수를 직접 import해서 쓰며(`block_stages()`),
  **동시에** `build_csm_waterfall_master.py::_wide_product_stages()`도 같은
  `STAGE_PATTERNS["amortization"]`을 자체 라벨매칭에 재사용한다 — 그래서 패치 한 곳으로
  두 소비 경로(`block_stages`/`pick_combined_agnostic` 계열과 `_wide_product_stages`/
  `_pick_wide_product` last-resort 계열) 모두 고쳐졌다.
- **B ("기타" 상품 누락)**: `scripts/build_csm_waterfall_master.py::pick_combined_agnostic()`
  의 `prod` 리스트 산출부(구 코드: `prod = [st for st, cap in cands if any(kw in cap for kw
  in _PROD_KW)]`, `_PROD_KW = ("사망","건강","연금","저축","종신","보장","상해")` —
  **"기타"가 원래부터 없었다**). 이건 A와 무관한 별개 지점 — A는 라벨(row) 매칭, B는
  블록(caption) 매칭이다.
  - **"기타"를 단순 추가하지 못하는 이유(raw로 확인)**: 미래에셋 필링엔 **두 개의 서로
    다른 분해축**이 같은 `cands` 리스트에 나란히 들어온다 — 배당축(`i)유배당` / `ii)기타`
    =무배당, 전체 책의 97%) 와 상품축(`i)사망`/`ii)건강`/`iii)연금`/`iv)저축`/`v)기타`).
    양쪽 다 "기타"라는 캡션을 쓰는데, 배당축의 "기타"는 **회사 전체와 거의 같은 크기**다
    (2025.4Q 실측: `ii)기타`=무배당 단독 항목1=19,956.11억 ≈ 상품축 5블록 합
    20,782.10억). `"기타" in cap` 단순매치였다면 상품축 4블록(사망+건강+연금+저축=
    20,775.61억) + 배당축 기타(19,956.11억)가 같이 잡혀 **거의 두 배로 과대계상**됐을
    것이다 — 지금 6.49억~38.13억 과소계상보다 훨씬 나쁜 회귀.
  - **고친 방법**: document-order 인접성 게이트. `cands`를 순서대로 훑으며
    `_prev_hard`(직전 cand가 하드 키워드(사망/건강/연금/저축 등)에 매칭됐는지) 상태를
    들고, "기타" cand는 **직전 cand가 하드매칭이었을 때만** `prod`에 편입한다. raw로
    확인한 문서 순서가 상품축은 항상 `[사망,건강,연금,저축,기타]`로 저축 바로 다음에
    기타가 오고, 배당축은 `[유배당,기타]`로 기타 앞이 유배당(하드매칭 아님)이라 이 게이트로
    정확히 분리된다(2023.2Q~2025.1Q 전 분기 + 2025.4Q 연차 `_00760` 첨부 8개 데이터포인트
    모두 이 순서 확인, 예외 없음).

### (2) 스윕이 찾은 영향 회사·분기 전수

**전사 스윕(SONBO 25개사, `data/dart/FY2022_Q4`~`FY2026_Q2` 전체 15분기, 426
company-quarter, `waterfall_for_dir()` read-only 재실행 — `build_csm_waterfall_master.py`
/`build_root_masters.py`의 `main()` 실행 없이 git stash로 수정전/후 두 스냅샷을 비교)
결과: **12개 분기·50개 diag셀, 전부 KR0079. 다른 24개사는 0건.**

- KR0079 변경 분기(12개): 2023.2Q, 2023.3Q, 2023.4Q, 2024.1Q, 2024.2Q, 2024.3Q, 2024.4Q,
  2025.1Q, 2025.2Q, 2025.3Q, 2025.4Q, 2026.1Q.
- 불변으로 확인된 분기: **2023.1Q**(항목C, 스코어러가 표 자체를 못 찾아 `src=None` — A/B와
  무관, 아래 참조) / **2026.2Q**(2026.2Q+ 라벨 재구성이 이미 기존 패턴으로 매칭되고 있어
  Bug A 대상 아님, Bug B의 `_PROD_KW`/캡션 매칭 경로 자체를 안 탐).
- **WIDE 상품별 포맷(`find_product_segmented_csm_cols` 히트) 사용사는 KR0069(삼성생명)·
  KR0079(미래에셋)·KR0087(동양생명) 3개사뿐**(전사 헤더 스캔, `scripts/_probes/
  probe_20260830_sweep_product_format_universe.py`). KR0069·KR0087의 실사용 후보 블록은
  item5(CSM상각)를 **각자 이미 매칭되는 다른 라벨**로 뽑고 있었다 — 삼성생명은 "제공한
  서비스에 대해 인식한 보험계약마진", 동양생명은 "서비스 이전을 반영하기 위해 당기손익으로
  인식한 보험계약마진 금액"(둘 다 기존 패턴에 이미 있음). item5=None이 뜨는 두 회사의
  서브블록은 item2도 함께 None이라(신계약 행이 없는 별개 표) 애초에 후보에서 걸러진다
  (`_seg_cands`/downstream 게이트가 `item2 OR item5` not None을 요구). **A/B 둘 다 실질
  영향은 KR0079 전용**임을 raw 라벨 덤프로 직접 확인.
  - "기타" 캡션 인접성 오탐 후보 하나 조사: **KR1011(IBK연금보험) 2025.4Q**가 스윕
    휴리스틱(캡션에 `_PROD_KW` 2개 이상 hit)에 걸렸으나, 실제로는 단일 캡션 문장
    "연금과 저축보험<당기>"가 "연금"+"저축" 두 단어를 우연히 포함한 것뿐 — 실제
    `pick_combined_agnostic`의 `seg`(≥3 hit) 게이트 자체가 안 걸린다(오탐 확인,
    `scripts/_probes/probe_20260830_kr1011_check.py`).

### (3) 마스터 셀 단위 변경 건수와 대표 수치 전후

**`csm_waterfall_master_diag.json` 수술적 패치(50셀, `git diff` 정확히 50 insertions/50
deletions, 전부 `"값":` 라인만) → `build_root_masters.build_csm()` 개별호출(main() 미실행)
→ combo-diff.**

- `CSM_waterfall.json`: **before 2172행 = after 2172행**(row-level 유실/추가 0),
  **41개 셀 변경**(`값` 38 + `값`은 안 바뀌었지만 `값_당분기`(분기 흐름 파생값)만 연쇄
  변경된 셀 3 — 2025.2Q 항목1/4/5, gold가 `값`은 이기지만 `값_당분기`는 여전히
  직전분기(2025.1Q) YTD 사슬로 파생되므로 그쪽만 갱신), **전부 KR0079, 다른 회사 0**.
- 대표 수치 전후 (2025.4Q, 연차 — B의 가장 큰 영향):
  | 항목 | before(`was`, 버그값) | after(고친값=gold와 오차 0) |
  |---|---:|---:|
  | 1 기초 CSM | 20775.6 | 20782.1 |
  | 2 신계약 CSM | 5360.6 | **5398.8** |
  | 3 이자 부리 | 606.4 | 606.6 |
  | 4 가정·경험조정 | -4134.2 | -4144.9 |
  | 5 CSM 상각 | -2056.2 | -2058.3 |
  | 6 기말 CSM | 20552.3 | 20584.2 |

  (항목2 5360.6→5398.8, 차이 38.2억 — 티켓이 지목한 "item2 diff 38.18억"과 사실상 일치.
  "기타" 상품 5블록의 값을 직접 raw로 재구성하면 항목2=3813백만원=38.13억, 반올림누적
  포함 오차 0.05억.)
- 대표 수치 전후 (2025.3Q — A의 전형 사례, `... or 0` 잔차흡수가 항목5를 항목4로
  삼키던 자리):
  | 항목 | before | after |
  |---|---:|---:|
  | 4 가정·경험조정 | **-1864.4**(버그: 항목4+항목5 합산값) | -333.2 |
  | 5 CSM 상각 | **None**(라벨매칭 실패) | -1531.2 |

  (-333.2 + -1531.2 = -1864.4 — 구코드가 항목5를 항목4로 통째로 흡수하고 있었다는
  걸 산수로 재확인.)
- `insurequant_master_tables.xlsx`: `scripts/sync_master_xlsx_sheet.py "CSM워터폴"`로
  cherry-pick 동기화(75셀 EDIT, 행 추가/삭제 0, 스크립트 자체 "검증 OK — 2172행×9열
  마스터와 완전 일치, 나머지 시트 값 동일" 확인).
- **gold가 이미 덮는 셀(2025.2Q/2025.3Q/2025.4Q/2026.1Q)은 이번 반영으로 화면 값이
  바뀌지 않는다** — gold-overlay가 build 마지막에 무조건 UPSERT되므로. **실제로 화면에
  반영되는 건 2023.2Q~2025.1Q(8개 분기, gold 미부여 구간, 38개 값 + 연쇄 당분기)뿐이다.**

### (4) gold 제거·재판정 후보 목록 (값 미변경 — `data/_gold/user_csm_cells.json` 안 건드림)

| 분류 | 건수 | 대상 |
|---|---:|---|
| ① 제거후보(코드가 이제 gold와 오차 0 재현) | 19 | 2025.2Q 항목1/2/3/6, 2025.3Q 항목1-6, 2025.4Q 항목1-6, 2026.1Q 항목1/4/5 |
| ② 재판정후보(값 상충, validation 판단 필요) | 2 | 2025.2Q 항목4/항목5 — 아래 (5) |
| ③ 불변(항목C, 여전히 필요) | 6 | 2023.1Q 항목1-6 |
| **합계** | **27** | KR0079 gold 전량 |

### (5) KR0079 2025.2Q 항목4/5 — 고친 코드가 내는 값 (gold는 손 안 댐)

고친 코드(`waterfall_for_dir`, src=`combined-agn`) 산출: **항목4 = -685.5억, 항목5 =
-992.1억.** raw WIDE 표(rcept 20250814003532) 직접 재구성값(`20260825T2200Z` 답변 (B))인
-685.50/-992.07과 **정확히 일치**(반올림 오차만) — 즉 이 티켓이 A를 고친 결과, 빌더는
raw 원문의 배분을 그대로 낸다. 현재 gold는 -886.27/-791.3(200.77억씩 반대방향, 합계는
raw=gold=-1677.57로 동일해 폐쇄식은 안 깨짐). **어느 쪽을 채택할지는 validation 판단 —
이번 세션은 gold를 갈아끼우지 않았다.**

### 항목C(2023.1Q 표 자체를 못 찾음) — 조사만, 미수정

`src/ifrs17/measurement_extractor.py::_score_table()`을 KR0079 2023.1Q(rcept
20230515002900)의 "i)사망" 캡션 표에 대해 직접 실행해 분해했다(`scripts/_probes/
probe_20260830_kr0079_2023q1_score_detail.py`):

```
score=3  reasons=['header: 1 measurement column', 'rows: weak stubs x2/x3', 'slice: whole_company_life policy']
```

캡션이 그냥 `i)사망`(로마숫자 상품명 하나)뿐이라 `_CAPTION_PRIMARY`/`_CAPTION_SECONDARY`
(측정요소/보험계약마진 등) 히트가 **0** — 실제 "측정요소별 변동" 같은 표제어는 부모/조상
캡션에 있고 이 회사는 서브테이블 캡션에 반복 안 함(2026-08-25 이미 알려진 "상품별 캡션이
'i)사망' 등으로 truncate" 함정과 동일 원인). header 1점 + row weak-stub 1점 + slice 1점 =
3점, `min_score=5` 미달로 전량 탈락 → `waterfall_for_dir`가 `src=None`.

**`min_score`를 낮추지 않기로 판단.** 이 파라미터는 `extract_measurement_tables()`의
공유 기본값이라 25개사 전체·전 분기의 모든 표 스코어링에 영향을 준다 — 회사 1개·분기
1개(2023.1Q, gold 6건이 이미 정확한 값으로 메우고 있어 화면 영향 없음)를 위해 전사
스코어링 문턱을 흔드는 건 새 false-positive 표 매칭 리스크에 비해 얻는 게 없다고 판단해
안 고쳤다. 캡션-컨텍스트 상속(부모 캡션을 서브테이블에 전파) 같은 구조적 수정이 진짜
해법이겠지만, 그건 이 스코어러를 공유하는 모든 회사에 영향을 주는 더 큰 변경이라 이
티켓 범위 밖으로 판단.

### (6) 골든 재생성 여부

- **`tests/test_viz_csm_waterfall_golden.py`: drift 없음, `--update` 불필요.** 이 빌더가
  소비하는 `data/dart/extracted/*_measurement.json`은 KR0079 기준 FY2024.4Q(rcept
  20250318001228) 파일 하나뿐인데, 그 파일의 항목5 행은 **SEPARATE-블록 포맷**이라
  A가 고친 라벨과 무관하게 이미 기존 패턴("서비스 제공에 따른..." 계열)으로 매칭되고
  있었다(raw 덤프로 직접 확인). 실행 결과 sha256 불변 — 백업(`data/dart/viz/
  csm_waterfall.json.bak_20260830_kr0079wideprod`)은 drift 없어 곧바로 지움.
- `tests/test_master_tables_golden.py`(`--no-build` 내장): SUMMARY/exit code 불변.
- `tests/test_csm_continuity_exception.py`: 18/18 통과 유지.

### 재현 명령

```
# 전사 스윕 (git stash로 전/후 비교, 수정 전 커밋으로 checkout 없이도 재현 가능)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_full_sonbo_sweep.py <out.json>
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_diff_sweep.py
# KR0079 cands 순서(문서순서 인접성 증거)
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_kr0079_prod_cands_all_quarters.py
# 항목C 스코어 분해
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260830_kr0079_2023q1_score_detail.py
# 골든/연속성
python -m pytest tests/test_viz_csm_waterfall_golden.py tests/test_master_tables_golden.py tests/test_csm_continuity_exception.py -q
```

### 하지 말 것 준수 확인

`build_root_masters.py`의 `main()` 미실행(`build_csm()` 개별 import+호출만). `data/_gold/
user_csm_cells.json` 바이트 무변경(이번 세션 미접촉, `git status`로 확인). `index.html`·
`IFRS17.html`·`public_exports/`·`scripts/validate_*`·`prepush_check.py`·`data/disclosure/`·
`kics_disclosure.json` 전부 미접촉. 브랜치 불변(`fix/csm-product-segmented-columns`),
`git push` 없음, `git add -A` 없음(개별 파일 add만).

### 백업

`data/dart/viz/csm_waterfall_master_diag.json.bak_20260830_kr0079wideprod` ·
`CSM_waterfall.json.bak_20260830_kr0079wideprod` ·
`insurequant_master_tables.xlsx.bak_20260830_kr0079wideprod` (전부 패치 직전 스냅샷).

status: **answered** — (5)의 2025.2Q 항목4/5 채택 방향, (4)②의 재판정 여부는 validation
판단 필요. 그 외(A/B 코드수정, 전사 스윕, 마스터 반영, gold 후보 목록, 항목C 판단근거)는
이 세션에서 자기완결.

커밋: `28ab7f8`
