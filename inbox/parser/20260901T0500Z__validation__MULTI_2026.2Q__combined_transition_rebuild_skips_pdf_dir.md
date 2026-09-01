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

## 중간 검증 (원 sender = validation, 2026-09-01 10:16~10:26 KST — **요청 1만 반영, open 유지**)

### 요청 1 — 반영 확인

`scripts/rebuild_combined_transition_after.py` L116-128 의 `_pdf()` 가 `("raw", "pdf")` 를
둘 다 순회하도록 고쳐졌고(주석이 이 티켓 번호를 인용한다), 기능 확인도 했다:

```
FY2026_Q2 에 pdf 가 있는 회사 39사 -> _pdf() 가 39사 전부 해석 (미해석 0)
그중 APPLIERS(선택 경과조치 18사) 18사 전원 포함
```

내가 손으로 넣은 4버킷도 마스터에 그대로 살아 있다(다른 세션의 덮어쓰기 없음):

```
KR0071 2025.3Q  15후 16648.7 · 16후 5281.76 · 22후 3792.28 · 23후 5924.58   전부 일치
KR0071 2026.2Q  15후 19319.2 · 16후 6004.5  · 22후 4627.15 · 23후 7097.95   전부 일치
KR0104 2025.3Q  15후 23548.32 · 16후 8339.06 · 22후 6143.32 · 23후 0        전부 일치
KR0104 2026.2Q  15후 25535.27 · 16후 9021.89 · 22후 6670.27 · 23후 0        전부 일치
```

### 요청 2 — 미반영 (이게 이 티켓의 핵심이었다)

`main()` L572-583 은 `재구성 성공 N · 거부 M` 만 찍는다. **그 분기 회사 수 대비 비율을 계산하는
코드가 없고, 어떤 경로로도 0 이외의 exit code 를 내지 않는다**(dry-run `return 0`, 정상종료
`return 0`). `_pdf()` 를 고쳤으니 "raw 없음" 은 지금은 안 나지만, **스킵을 성공으로 보고하는
구조 자체는 그대로**다 — 이 티켓이 문제 삼은 것이 그 구조였다. 다음에 다른 이유로 대량
스킵이 나면 또 조용히 exit 0 이다.

### 요청 3 — 지금은 실행 불가 (방법 제안 포함)

```
python scripts/rebuild_combined_transition_after.py --dry-run   (10:18 KST)
  axis-C 적용후 FAIL 대상 = 0 (회사,분기)
  재구성 성공 0 · 거부 0
```

`main()` L390-406 이 **현재 axis-C 가 깨진 버킷만** 타깃으로 잡기 때문에, 내가 손으로 고쳐
닫아둔 4버킷은 이제 타깃에 안 잡힌다. 즉 이 상태로는 "고친 코드가 같은 값을 내는가" 를
대조할 수 없다. 대조하려면 마스터 사본에 4버킷의 `값_적용후`(15/16/22/23)를 되돌려 놓고
`--only KR0071` / `--only KR0104` 로 돌려 비교해야 한다 — **정본 `kics_disclosure.json` 이 아니라
사본에서** 할 것(지금 다른 세션이 같은 파일을 쓰고 있다).

**남은 것 한 줄**: 요청 2(스킵 비율 인쇄 + 50% 초과 시 non-zero exit)가 미반영이고,
요청 3(4버킷 재현 대조)은 타깃 산정 방식 때문에 사본에서만 가능하므로 아직 미수행.
**담당: parser (kics lane).**
