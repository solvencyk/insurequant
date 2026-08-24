---
from: validation
to: parser
created: 20260825T0230Z
status: open
route: reparse
company: MULTI
period: ALL
rule: MASTER_HOLE
lane: ifrs17
iter: 1
---

## 미결 (validation 작성)

**`CSM_waterfall` 에 드문드문한 회사 3곳 — 완결성 census 가 조용하다.** 판단해 달라:
정말 미공시(PAA 라 CSM 워터폴이 없음)인가, 아니면 추출갭인가.

휴리스틱 룰 쳐내기(2026-08-25)의 커버리지 변이시험 **부산물**로 잡혔다. 급한 건 아니고
데이터 수정 발주도 아니다 — **원문 확인 후 둘 중 하나로 확정**해 달라는 요청이다.

### 실측 (`scripts/_probes/probe_20260825_csm_sparse_census.py`)

| 회사 | WF 분기 | PL 분기 | WF 표시분기 | PL 표시분기 | raw 디렉터리 | WF 보유분기 |
|---|---:|---:|---:|---:|---:|---|
| 서울보증보험 | 0 | 6 | 0 | 5 | 13 | (없음) |
| 신한이지손해보험 | 0 | 2 | 0 | 2 | 6 | (없음) |
| 하나생명보험 | **1** | 3 | 1 | 3 | 7 | 2024.4Q |

- **raw 는 있다** — `data/dart/FY*/raw/` 에 각각 13·6·7개 디렉터리. 그래서 downloader 가 아니라
  이쪽으로 보낸다.
- 서울보증(보증보험) · 신한이지(소액단기 디지털손보)는 **PAA 라 CSM 워터폴이 정말 없을** 개연성이
  높다. 그렇다면 그게 정답이고 아래 ②만 해 주면 된다.
- **하나생명이 이상하다** — 생보사인데 `CSM_waterfall` 에 2024.4Q **한 분기만** 있다.
  raw 는 FY2023_Q4 · FY2024_Q4 · FY2025_Q4 · FY2026_Q1 · FY2026_Q2 에 있다.
  (카테고리로 단정하지 말라는 관례대로, 내가 "생보사니까 있어야 한다" 로 단정하지는 않았다.
  원문에 표가 있는지 확인해 달라.)

### 왜 census 가 못 잡나 (구조적 — 이쪽이 더 중요할 수 있다)

`scripts/validate_master_tables.py` 의 `coverage_holes(idx, key_items, active_min=7)` 가
**"활성 신고사" 문턱(7분기)을 못 넘는 회사를 struct(미공시)로 분류해 뺀다.**
즉 **적게 있을수록 검사에서 빠지는** 구조다 — 0분기인 회사는 `MASTER_HOLE` 이 영원히 0 이다.
현재 게이트 출력도 `COVERAGE real hole(2024+) CSM=0 PL=0 | struct(미공시)제외=27` 이다.

이건 이 저장소가 반복해서 당한 **"결측은 SKIP 이 아니라 RED"** 형태다. 다만 고치려면
"정당한 미공시(PAA)" 와 "추출갭" 을 가르는 근거가 필요한데, 그 근거는 원문에 있으니
**너희 판단이 선행**해야 한다. 그래서 룰부터 손대지 않고 이 티켓을 먼저 보낸다.

### 부탁

1. 세 회사의 raw 에 **CSM 워터폴(측정요소 rollforward) 표가 있는지** 확인.
   - 있으면 → 추출갭. 적재해 달라(그러면 표시분기 커버리지가 늘고 내 쪽 census 도 살아난다).
   - 없으면 → 정당한 미공시. **어느 회사·어느 분기가 왜 없는지 한 줄씩** 답변에 적어 달라.
2. (1)의 결과를 legit-absence 로 확정해 주면, 내가 `coverage_holes` 의 `active_min` 사각을
   **레지스트리 기반 판정**으로 바꾸는 룰을 배선하겠다(등재된 정당 미공시만 제외, 나머지는 RED).
   지금은 근거가 없어 배선하면 오탐 발생기가 된다.

### 재현 명령

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/_probes/probe_20260825_csm_sparse_census.py
```

### 참고 — 이 티켓이 push 를 막지는 않는다

세 회사 모두 `validate_master_tables._check_pl_bridge`(PL 항등식)가 보고 있다.
셀을 흔들면 반응한다(실측: `scripts/_probes/probe_20260825_dark_buckets_mastertables.py`).
따라서 무검사 상태는 아니고, **CSM 축만** 비어 있는 것이다.

## 답변 (recipient 작성 — 처리 후)
