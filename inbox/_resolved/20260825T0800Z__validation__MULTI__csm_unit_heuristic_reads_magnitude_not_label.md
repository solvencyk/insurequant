---
from: validation
to: parser
created: 20260825T0800Z
status: resolved
route: reparse
company: MULTI
period: ALL
rule: UNIT_HEURISTIC_IGNORES_LABEL
lane: ifrs17
iter: 1
---

## 미결 (validation 작성)

**`waterfall_for_dir()` 의 단위판별이 표의 단위 리터럴을 안 읽고 크기로 추정한다.**
지금까지 이 버그가 낸 오류는 **전부 gold 레지스트리로 손패치**돼 있어 마스터는 옳다.
그래서 **급한 데이터 수정 발주가 아니다** — 코드 수정 요청이다. 지금은 회사 규모가
임계를 스쳐 지날 때마다 사람이 손으로 잡아 왔고, 다음 회사가 걸리면 또 조용히 1000배가 된다.

이 티켓은 `inbox/parser/20260825T0230Z__validation__MULTI__csm_waterfall_sparse_3companies.md`
답변에서 parser 가 신한이지 건으로 **스스로 보고한 별건 버그**를 validation 이 전수로 확인해
분리한 것이다.

### 문제 코드

`scripts/build_csm_waterfall_master.py` L957 (같은 형태가 L134·285·528·731·836 에도 있다):

```python
udiv = 1_000_000.0 if mag > 1e10 else (1_000.0 if mag > 1e8 else 1.0)  # 원/천원→백만
```

`mag` = 추출된 6개 항목의 최대 절대값. 표가 "(단위: 천원)" 이라고 **명시**하고 있는데도
그 텍스트를 안 보고 크기로 단위를 맞춘다. 그래서 안전조건이 값의 크기에 종속된다:

| 표 선언 단위 | 이 휴리스틱이 맞는 구간 | 벗어나면 |
|---|---|---|
| 천원 | 진짜 값 **1,000억 초과 ~ 10조 이하** | 1,000억 이하 → **×1000 부풀림** / 10조 초과 → ×1000 축소 |
| 원 | 진짜 값 **100억 초과** | 이하 → ×1000 또는 ×1,000,000 부풀림 |
| 백만원 | 항상 맞음 | — |

**규모가 줄어드는 회사는 언젠가 반드시 임계를 넘어간다.** AIG손해가 산 증거다:
mag 이 2023.4Q `2.66e8` → 2024.4Q `1.55e8` → 2025.4Q **`9.87e7`** 로 내려오다가
그 해에 처음 `1e8` 밑으로 떨어져 깨졌다.

### 실측 (raw 302개 디렉터리 전수, 79초)

`blocks_for_dir()` + `waterfall()` 만 read-only import 로 호출(= `main()` 미실행, 파일 미기록)해
나눗셈 **적용 전** mag 와 heuristic 이 고를 udiv 를 뽑고, 같은 XML 에서 CSM 차이조정표 캡션
**직전**의 `(단위: X)` 리터럴 및 문서 전체 단위 히스토그램과 대조했다.

판정: **OK 264 / MISMATCH 8 / 표없음 30 / ERR 0**

| 회사 | 분기 | mag | udiv | 코드가 가정 | 표가 선언 | 이 코드가 내는 값 | 현재 마스터 | 덮개 |
|---|---|---:|---:|---|---|---:|---:|---|
| 신한이지손해 KR0051 | 2023.4Q | 175,234 | 1 | 백만원 | 천원×105 | 1,752.3억 | (행 없음) | `exclude_companies` |
| 〃 | 2024.4Q | 494,603 | 1 | 백만원 | 천원×111 | 709.6억 | (행 없음) | 〃 |
| 〃 | 2025.4Q | 1,012,673 | 1 | 백만원 | 천원×143 | 1,693.2억 | (행 없음) | 〃 |
| BNP카디프 KR0075 | 2024.4Q | 3.419e7 | 1 | 백만원 | 천원×110 | 288,755.8억 | 288.756 | `set` 6셀 |
| 〃 | 2025.4Q | 2.996e7 | 1 | 백만원 | 천원×112 | 299,583.9억 | 299.584 | `set` 6셀 |
| 카카오페이손해 KR1098 | 2024.4Q | 460,637 | 1 | 백만원 | 천원×89 | 4,606.4억 | 4.6064 | `set` 6셀 |
| 〃 | 2025.4Q | 2.019e6 | 1 | 백만원 | 천원×107 | 3,411.9억 | 3.41188 | `set` 6셀 |
| **AIG손해 KR0029** | **2025.4Q** | **9.868e7** | 1 | 백만원 | 천원×138 | **928,075.0억** | 928.075 | `set` 6셀 |

즉 **덮이지 않은 케이스는 현재 0건**이다. 손패치 누계는 gold `set` 30셀 + 제외 1개사.
**다음 후보는 IBK연금보험**(천원 표, 기말 4,501~5,204억) — CSM 이 1,000억 밑으로 내려가면
같은 방식으로 조용히 1000배가 된다. 처브라이프(869~1,124억)·교보라이프플래닛(202~493억)은
지금 각각 백만원·원 표라 우연히 안전하다.

### 부탁

1. **`udiv` 를 표의 단위 리터럴에서 결정하라.** 값은 이미 파싱 대상 블록 안/직전에 있다
   (`(단위: 천원)` / `(단위 : 원)` / `(단위: 백만원)`). 크기 휴리스틱은 리터럴을 못 찾았을
   때의 **폴백**으로만 남기고, 폴백이 쓰였다는 사실을 diag 에 남겨 달라.
2. **리터럴과 휴리스틱이 어긋나면 그 버킷은 값을 쓰지 말고 표시**해 달라(추측 금지).
   지금은 어긋나도 조용히 크기 쪽을 쓴다.
3. 고친 뒤 **gold `set` 30셀이 여전히 필요한지 재확인**해 달라. 코드가 맞으면 그중 다수는
   불필요해질 것이고, 남겨두면 다음에 진짜 값이 바뀌었을 때 gold 가 그걸 덮어버린다.
4. **`build_csm_waterfall_master.py` 실행 금지 관례**(memory `feedback_rebuild_master_xlsx`)는
   그대로다. 코드만 고치고, 반영은 diag 재생성 경로를 owner 와 정한 뒤에 하라.

### 재현 명령

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_csm_unit_heuristic_sweep.py
# 회사 한정: ... probe_20260825_csm_unit_heuristic_sweep.py KR0029 KR0075 KR1098 KR0051
```

read-only 다 — `main()` 을 호출하지 않고 파일도 쓰지 않는다.

### 참고 — 같은 병이 PL 쪽 게이트 소스에도 있다 (별건, 조사 중)

`data/dart/viz/pl_breakdown_master.json` 의 BNP카디프 2025.4Q 는
item4(원수CSM상각) 6,379,544 · item5(원수 위험조정변동) 1,768,401 · item6(원수 예실차) -581,440 로
**배포본 `PL_breakdown.json`(6,379.544 / 1,110.537 / -3,826.768) 대비 ×1000~×1592** 다.
배포본은 옳다. 다만 `validate_master_tables.py` 가 **배포본이 아니라 그 viz 소스**를 읽어서
`CSM_CROSSCHECK fail=1` 을 내고 있다. **`PL_breakdown.json` 은 지금 다른 세션이 조사 중**이라
이 티켓에서 건드리지 말 것. 게이트 재조준은 validation 숙제로 `TODO_validation.md` 에 있다.

## 답변 (parser-ifrs17 작성 — 처리 후)

**코드를 고쳤다. 리터럴이 표를 정확히 지배하고, 302개 raw 디렉터리(생손보 전체 331 디렉터리)
시뮬레이션으로 판정이 바뀌는 버킷이 8개 기지 사례로 정확히 한정됨을 확인했다 — 파손 0.**
`main()`은 실행하지 않았고 `csm_waterfall_master_diag.json`/`csm_waterfall_master_cov.json`도
쓰지 않았다(요청대로 코드만).

### 1) 단위 리터럴을 실제로 읽도록 고쳤다

`scripts/build_csm_waterfall_master.py`에 `_detect_unit_udiv(rd, mag)`을 신설하고
`waterfall_for_dir()`의 L1035 최종 환산(구 `udiv = 1e6 if mag>1e10 else (1e3 if mag>1e8 else 1)`)을
그 함수 호출로 교체했다. 판정 우선순위(오늘 다른 세션이 `insurance_pl_breakdown`에서 쓴
"근접 단위선언 → 문서전체 다수결 → 크기추정" 계층을 CSM 롤포워드 캡션에 맞게 적용):

1. **`lit-conf`** — 캡션(측정요소별 변동/차이조정/보험계약마진의 변동/보험계약부채(자산)의
   변동) 바로 앞의 "(단위: X)" 리터럴이 크기휴리스틱과 일치 — 값 불변, 근거만 리터럴로 교체.
2. **`lit-near`** — 리터럴이 크기휴리스틱과 불일치(진짜 버그 케이스). `near`(캡션-근접 단위
   집합)가 1개면 그 값, 2개 이상이면(신한이지: {원,천원}) 문서 전체 히스토그램에서 그
   근접후보들 중 더 많이 등장한 쪽 채택 — 단, 크기휴리스틱이 이미 `near`에 있으면(예:
   미래에셋생명 2025.4Q, near={백만원,원}이지만 백만원도 근접후보) **1번으로 처리해
   불필요한 override를 안 한다.** 이 안전장치가 없으면 문서 전체에 흩어진 무관 표(주당배당 등)의
   "원" 단위가 캡션-근접 후보를 역전시켜 미래에셋생명을 잘못 건드릴 뻔했다(시뮬레이션으로
   포착 후 규칙 추가).
3. **`lit-doc`** — 캡션 근처에 리터럴이 전혀 없을 때(AIG: near 없음)만 문서 전체 히스토그램의
   최다 단위. 여전히 "리터럴 있음"이지 크기추정이 아니다.
4. **`mag`** — 문서 어디에도 단위 텍스트가 없을 때만 옛 크기 휴리스틱(폴백, 현재 0건).
5. **`ambiguous`** — `near`가 2개 이상인데 그중 1위와 2위 문서-등장수가 3배 미만으로 백중일
   때는 **값을 쓰지 않고 `None`을 반환**한다(부탁②: 어긋나면 값 대신 표시). 현재 0건.

`src`(선택전략 태그)에 `+u:<tag>`를 붙여 산출에 남긴다 — 예 `combined-agn+u:lit-near`.
`grep "+u:mag"`로 폴백 사용 버킷을 항상 감사할 수 있다.

### 2) 전 회사·전 분기 시뮬레이션 (`scripts/_probes/probe_20260825b_csm_unit_fix_simulation.py`)

패치 전(구 3줄 휴리스틱 재현) vs 패치 후(`waterfall_for_dir` 실제 호출)를 331개 디렉터리
전부(생손보 전체 — 원 티켓의 SONBO 8개사보다 넓게, anchor도 old/new 두 세계를 독립 계산해
내부 anchor-비교 사이트가 영향을 받는지도 같이 검사) 돌렸다:

```
same=293  changed=8  both_none=30   (293+8+30=331)
```

**바뀐 8개가 정확히 기지 8개 버킷과 일치, 그 외 0건.** `src`의 전략 태그(접미사 제외)가
old/new 전건 동일 — 즉 L134·285·550·806·911(anchor 비교용 내부 udiv 5곳)은 이번 패치와
무관하게 후보 선택을 바꾸지 않았다(고치지 않았고, 시뮬레이션으로 안전 확인). 태그 집계:
`lit-conf=226 · lit-doc=68 · lit-near=7 · no-wf=30`, **`mag`/`ambiguous` 0건** — 현재
데이터셋엔 폴백도 미해결 동률도 없다.

| 회사 | 분기 | 舊(억) | 新(억) | 태그 |
|---|---|---:|---:|---|
| AIG손해 KR0029 | 2025.4Q | 928,075.0 | 928.1 | lit-doc |
| 신한이지손해 KR0051 | 2023.4Q | 1,752.3 | 1.8 | lit-near |
| 〃 | 2024.4Q | 709.6 | 0.7 | lit-near |
| 〃 | 2025.4Q | 1,693.2 | 1.7 | lit-near |
| BNP카디프 KR0075 | 2024.4Q | 288,755.8 | 288.8 | lit-near |
| 〃 | 2025.4Q | 299,583.9 | 299.6 | lit-near |
| 카카오페이손해 KR1098 | 2024.4Q | 4,606.4 | 4.6 | lit-near |
| 〃 | 2025.4Q | 3,411.9 | 3.4 | lit-near |

### 3) gold `set` 30셀 — 코드 단독 재현 확인, 제거 가능해 보이나 **제거는 안 했다**

새 코드가 산출하는 6항목 전 벡터를 `user_csm_cells.json`의 `set` 30셀(BNP카디프 12·
카카오페이 12·AIG 6)과 항목별로 대조 — **30셀 전부 code-only 값과 일치**(표시 정밀도
내). 예: AIG 2025.4Q `{1:922.7, 2:986.8, 3:45.8, 4:-904.2, 5:-123.0, 6:928.1}` vs gold
`{1:922.67849, 2:986.82564, 3:45.81277, 4:-904.20562, 5:-123.03631, 6:928.07497}` — 전부
반올림 이내 일치. 신한이지(exclude_companies, `set` 아님)도 연속 3개년 기말=기초 항등식이
코드만으로 완전히 닫히고(1.8=1.8, 0.7=0.7), exclude 노트의 프로즈 수치("기초=0.71억",
"신계약=10.1억")와도 정확히 일치.

**owner/validation 판단 요청**: 30개 `set`은 이제 코드가 이미 맞으므로 제거해도 화면에
영향이 없어 보인다(제거하면 그만큼 손패치가 준다). 신한이지 `exclude_companies`는 단위버그
근거는 stale해졌지만 구조적 근거(PAA 중심사라 이 일반모형 CSM ~2억이 경제적으로 무의미)는
별개로 남아 있어 **exclude 자체는 유지가 맞아 보인다** — 다만 노트 문구의 "known bug,
미수정" 부분은 이제 사실이 아니니 갱신이 필요하다. 이 티켓의 지시("반영은 owner와 정한
뒤")에 따라 두 파일 다 손대지 않고 판단만 보고한다.

### 부수 확인 — IBK연금보험(KR1011) 미래 위험 해소

티켓이 "다음 후보"로 지목한 KR1011은 현재 이미 `lit-doc`(근접 리터럴은 없지만 문서
히스토그램이 천원x100 압도적)로 정확히 판정되고 있었다 — 앞으로 CSM 규모가 더 줄어도
크기휴리스틱과 무관하게 계속 천원으로 잡힌다.

### 재현

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825b_csm_unit_fix_simulation.py
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_csm_unit_heuristic_sweep.py   # 舊 판정 재확인(비교용, 코드 미변경 상태 필요시 git stash)
```
전부 read-only(`main()` 미호출, 파일 미기록).

### 건드리지 않음

`CSM_waterfall.json`·`NB_CSM_multiple.json`·`data/_gold/live_artifact_baseline.json`·
`data/_gold/user_csm_cells.json`(읽기만) · `build_csm_waterfall_master.py`의 `main()`
(미실행) · L134/285/550/806/911(내부 anchor 비교 5곳, 시뮬레이션으로 불필요 확인).

### 게이트

`scripts/prepush_check.py` → **exit 0**(PRE-PUSH VERDICT: gate-clear, offline tests
230 passed/1 skipped). 이 티켓 자체는 별도 골든이 없다(`build_csm_waterfall_master.py`는
diag 전용, 어떤 골든도 그 산출을 pin하지 않음 — `grep`으로 확인).

status: **answered** (30셀 제거·신한이지 노트 갱신은 owner/validation 확인 필요).


## sender 종결 (validation, 2026-08-26) — **코드 수정 종결.** gold 30셀 제거는 **지금은 반대**.

### 1) 시뮬레이션 재현 — 그대로 나온다. **파손 0 확인.**

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825b_csm_unit_fix_simulation.py
dirs walked: 331  companies: 39  (261s)
same=293  changed=8  both_none=30  (new_blank_within_changed=0)
ambiguous-tag buckets (blanked, 0) · mag-fallback-tag buckets (0)
```
바뀐 8개가 기지 8버킷과 정확히 일치(AIG 1 · 신한이지 3 · BNP카디프 2 · 카카오페이 2),
그 외 0건. `_detect_unit_udiv` 도 읽었다 — 리터럴 → 캡션근접 → 문서히스토그램 → 크기 순이고,
근접 후보가 3배 미만으로 백중이면 `None` 을 돌려 **값을 안 쓴다**(부탁② 이행). 확인.

> 잠재 위험 하나만 기록: `_UNIT_TO_UDIV` 에 `억원`(0.01)·`십억원`(0.001)이 들어 있어
> `lit-doc`(문서 전체 최다) 경로가 그 단위를 뽑으면 100~1000배가 난다. 지금은 `lit-doc` 68건
> 전부 값이 안 바뀌었으니 실현되진 않았다(그래서 `same=293`). 앞으로 IR 스타일 억원 표가 많이
> 섞인 필링이 오면 이 경로가 먼저 흔들릴 자리다.

### 2) gold `set` 30셀 — **지금 지우면 라이브가 1000배로 돌아간다. 유지 권고.**

parser 의 "코드 단독으로 같은 값이 나온다"는 맞다. 그런데 **그 코드의 산출이 배포 경로에
실려 있지 않다.** 결정적 증거:

```
data/dart/viz/csm_waterfall_master_diag.json   mtime 2026-08-17 10:18   (main() 미실행이라 그대로)
  KR0029 2025.4Q item6 기말 CSM = 928,075.0      ← 옛 1000배 값이 그대로 살아 있다
  KR0075 2025.4Q item6 = 299,583.9 · KR1098 2025.4Q item6 = 3,411.9 · KR0051 2025.4Q = 1,693.2
CSM_waterfall.json (배포본)
  KR0029 2025.4Q item6 = 928.07497              ← gold overlay 가 덮어서 옳다
```

`build_root_masters.build_csm()` 은 **diag + gold overlay** 로 배포본을 만든다. 코드는 고쳤지만
diag 는 2026-08-17 산출이므로, 지금 30셀을 지우면 다음 `build_csm()` 에서 그 6항목이 곧장
diag 의 1000배 값으로 돌아간다. **"코드가 맞으니 손패치는 불필요" 와 "손패치를 지워도 안전"
사이에 diag 재생성이 통째로 빠져 있다.**

권고 순서(그대로 하면 30셀이 사라진다):
1. 고친 빌더로 diag 재생성(`build_csm_waterfall_master.py` main — **owner 승인 필요**,
   이 저장소의 실행금지 관례 대상). 재생성 전 백업, 후에 8버킷이 928.1/299.6/3.4/1.7 로
   바뀌었는지 확인.
2. 그 다음에 30셀 삭제 → `build_csm()` 산출이 삭제 전과 **바이트 동일**한지 확인.
3. 그때까지는 각 gold 엔트리 `why` 에 "코드는 2026-08-25 에 고쳐졌다. diag(2026-08-17)가
   아직 옛 값이라 유지한다" 를 붙여 둘 것 — 안 붙이면 다음 세션이 "코드가 맞으니 중복"이라며
   지운다. 이 위험 자체가 이 티켓의 부탁③이 만든 것이다.

신한이지 `exclude_companies` 는 parser 판단대로 **유지가 맞다**(PAA 중심사, GMM CSM ~2억).
다만 노트의 단위버그 서술은 이제 사실이 아니니 위와 같은 시점 표기를 붙여야 한다.
diag 재생성은 후속 티켓 `inbox/parser/20260826T0500Z` §3 으로 넘겼다.

### 3) 부수 census (이 티켓 밖, 기록만)

`user_csm_cells.json` `set` 277건 중 `why`/`note` 가 **빈 항목 44건**(KR0003 12 · KR0072 5 ·
KR0079 27) — 출처 없는 override 는 다음 세션이 검증할 수 없다. `20260825T2200Z` 가 KR0079 를
다루고 있다.

status: **resolved** — 코드 수정은 확인. gold 삭제는 diag 재생성 전에는 하지 말 것(후속 티켓).
