---
from: validation
to: parser
created: 20260901T0500Z
status: open
route: reparse
company: MULTI
period: 2026.2Q
rule: TRANSITION_AFTER_MMULT_MISMATCH
lane: kics
iter: 1
---

## 미결 (sender 작성)

`scripts/rebuild_combined_transition_after.py` 가 **2026.2Q 40개사 중 39개사를 조용히 건너뛴다.**
그래서 결합 경과조치 적용후 체인이 이번 라운드에 재구성되지 못했고, 그 자리에 단일표 값과
헤드라인이 섞인 값이 남아 `TRANSITION_AFTER_MMULT_MISMATCH` 로 터졌다(흥국생명·농협생명 4건,
validation 이 손으로 정정 완료).

### 원인 — raw 경로만 본다

```python
# scripts/rebuild_combined_transition_after.py L116-119
def _pdf(period: str, code: str):
    raw = DISCLOSURE / period / "raw"
    pdfs = sorted(raw.glob(f"{code}_*.pdf"))
```

실측 (2026-09-01):

```
data/disclosure/FY2026_Q2/raw/  ->  1개  (KR0050_하나손해보험.pdf 뿐)
data/disclosure/FY2026_Q2/pdf/  -> 40개  (실제 이번 분기 PDF 전부)
```

`_pdf()` 가 None 을 돌려주면 그 (회사,분기)는 `rejects` 에 "raw 없음" 으로 들어가고 **경고 없이
넘어간다.** 즉 "재구성 0건" 이 "재구성할 게 없었다" 로 읽힌다 — false-green 이다.

### 요청

1. `_pdf()` 가 `raw/` 와 `pdf/` 를 **둘 다** 보게 할 것(둘 다 있으면 기존 우선순위 규칙 유지).
2. `rejects` 의 "raw 없음" 이 **그 분기 회사 수 대비 몇 %인지** 를 마지막에 인쇄하고,
   50% 를 넘으면 exit code 를 0 이 아닌 값으로 낼 것. 스킵은 성공이 아니다.
3. 고친 뒤 `--dry-run` 으로 2026.2Q 전사를 돌려, validation 이 손으로 넣은 아래 4버킷과
   같은 값이 나오는지 대조해 줄 것(다르면 그 차이가 곧 이 티켓의 답이다).

### validation 이 이미 정정한 4버킷 (재현 대조용)

| 회사 | 분기 | item15후 | item16후 | item22후 | item23후 |
|---|---|---|---|---|---|
| KR0071 | 2025.3Q | 16648.7 | 5281.76 | 3792.28 | 5924.58 |
| KR0071 | 2026.2Q | 19319.2 | 6004.5 | 4627.15 | 7097.95 |
| KR0104 | 2025.3Q | 23548.32 | 8339.06 | 6143.32 | 0 |
| KR0104 | 2026.2Q | 25535.27 | 9021.89 | 6670.27 | 0 |

근거·재현: `scripts/_probes/fix_20260901_kr0071_kr0104_combined_transition.py`
(정본 methodology = `rebuild_combined_transition_after.py` docstring 그대로. 14후 는 원문
헤드라인 앵커라 손대지 않았다).

원문 위치(0-idx page):
- KR0071 2026.2Q `data/disclosure/FY2026_Q2/pdf/KR0071_흥국생명보험.pdf` — ②/③ 표는
  md_inbox MD L338·L366, 헤드라인 4-2-3 은 L399 (21,790).
- KR0104 2026.2Q `data/disclosure/FY2026_Q2/pdf/KR0104_농협생명보험.pdf` p20(②)·**p21(③)**
  — ③ 표는 docling MD 에서 통째로 유실됐다(별건: 20260831T0700Z 티켓과 같은 계열).
- KR0071 2025.3Q `data/disclosure/FY2025_Q3/raw/KR0071_흥국생명보험.pdf` p19(②)·p20(③)·p21(헤드라인)
- KR0104 2025.3Q `data/disclosure/FY2025_Q3/raw/KR0104_농협생명보험.pdf` p18(②)·p19(③)·p20(헤드라인)

## 답변 (recipient 작성 — 처리 후)
