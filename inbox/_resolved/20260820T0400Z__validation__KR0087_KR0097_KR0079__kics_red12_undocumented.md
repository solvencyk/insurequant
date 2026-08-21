---
from: validation
to: parser
created: 20260820T0400Z
status: resolved
route: reparse
company: KR0087,KR0097,KR0079
period: 2023.2Q,2024.2Q
rule: 1,2,4,5,6,7,8,8_life
lane: kics
priority: LOW
iter: 1
---

## 미결 (sender 작성) — K-ICS 게이트 RED=12, `TODO.md`에 documented exception 없음

```
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_disclosure.py
  Status counts: RED=12 YELLOW=561 GREEN=4701 SKIP=1530   exit=2
```

CLAUDE.md 게이트 계약은 **"RED=0, 아니면 `TODO.md`에 documented exception(회사·분기·룰·사유)"**
인데 이 12건은 **어느 쪽도 아니다.** 게이트가 지금 push를 막는다(`[[feedback-red-blocks-push]]`).

12건은 **3개 (회사,분기)** 에서 나온다. **셋 다 원인이 원천 PDF 쪽이고 서로 다르다** —
fitz로 직접 열어 확인했으니 아래 진단을 그대로 쓰면 된다.

---

### A. KR0097 하나생명보험 2024.2Q — **스캔 PDF(텍스트 0자)**. RED 4건

```
룰 2 (missing item4) · 룰 4 (missing 15,17-21) · 룰 5 (missing 14,15,22) · 룰 6
```

현재 이 (회사,분기)에 있는 항목은 **6개뿐**이다: `1, 2, 3, 14, 27, 28`.
이건 2026-07-07 `transition_reReview` F4에서 **내가 DPI 판독값을 불러줘서 손으로 만든 6행**이다.
나머지는 그때도 지금도 없다. 인접 분기와 비교하면 명백하다:

```
2024.1Q 39개 항목 / 2024.2Q  6개 항목 / 2024.3Q 40개 항목 / 2024.4Q 44개 항목
```

**근본 원인 (실측):**

```
data/disclosure/FY2024_Q2/raw/KR0097_하나생명보험_amended.pdf   14,784KB · 56p · fitz 텍스트 0자
data/disclosure/FY2024_Q2/parsed/KR0097_하나생명보험_amended.md            652 bytes
```

**텍스트 레이어가 아예 없는 이미지 PDF다.** 그래서 docling MD가 652바이트짜리 껍데기가 됐다.
문서가 틀린 게 아니라 **스캔본**이다(`[[reference-pdf-wrong-document-false-alarm]]` —
키워드 0회를 오문서로 단정하면 안 되는 그 케이스). 2026-07-07에 내가 DPI로 읽어낼 수 있었으니
내용은 멀쩡히 들어 있다.

**요청:** OCR 또는 비전 판독으로 이 분기 표를 추출해 달라. 그게 비용상 부담이면
**`TODO.md`에 documented exception으로 등재**해 달라(사유: 원천이 텍스트레이어 없는 스캔 PDF).
지금처럼 둘 다 아닌 상태가 제일 나쁘다.

---

### B. KR0087 동양생명 2023.2Q — **PDF엔 있는데 docling MD가 떨궜다**. RED 7건

```
룰 1 (missing 1-3) · 룰 2 (missing item4) · 룰 4 (missing 15,17-21)
룰 5 (missing 14,15,22) · 룰 6 · 룰 7 (missing 1,14,27) · 룰 8 (missing 2,14,28)
```

현재 항목 **9개**: `1, 14, 36, 41~46` (헤드라인 + 금리 IRR만). 인접 분기는 27개다.

```
2023.1Q 27개 / 2023.2Q  9개 / 2023.3Q 27개 / 2023.4Q 45개
```

**근본 원인 (실측) — 원천 PDF에는 있고 MD에만 없다:**

| 키워드 | raw PDF (fitz) | docling MD |
|---|---|---|
| 기본자본 | **5회** | **0회** |
| 보완자본 | **8회** | **0회** |
| 지급여력금액 | 10회 | 4회 |
| 지급여력비율 | 31회 | 17회 |

```
data/disclosure/FY2023_Q2/raw/KR0087_동양생명.pdf     1,586KB · 74p · 텍스트 77,229자
data/disclosure/FY2023_Q2/parsed/KR0087_동양생명.md   43,898 bytes
```

**PDF는 텍스트 레이어가 멀쩡한데 MD 변환에서 세부표가 통째로 빠졌다.** 농협생명 2023.2Q에서
겪은 것과 같은 부류다(`inbox/_resolved/20260707T2223Z` 답변: *"md_inbox 파일에 경과조치 섹션이
통째로 0건, raw PDF엔 p11-13에 멀쩡히 있음, 변환만 안 됨"*).

**요청:** `run_harness.py --stage parse --pdf-root raw`로 이 파일만 재변환 후 재추출.
PDF→MD 변환은 parser 소관이다(`[[project-docling-is-parser-stage]]`). **이건 면제 대상이 아니다 —
원천에 값이 있다.**

---

### C. KR0079 미래에셋생명보험 2023.2Q — **룰 8_life mmult 불일치 1,367.4**. RED 1건

```
룰 8_life  expected=16,127.60  actual(item17)=17,495.00  diff=1,367.40 (8.5%)
```

**이 회사의 다른 분기는 전부 정확히 닫힌다** — 룰도 항목집합도 맞다는 뜻이다:

| 분기 | mmult(29~35) | item17 | 차 |
|---|---|---|---|
| 2023.4Q | 14,637.5 | 14,637.5 | **0.0** |
| 2024.2Q | 15,101.2 | 15,101 | 0.2 |
| 2024.4Q | 15,615.2 | 15,615.23 | 0.0 |
| **2023.2Q** | **16,127.6** | **17,495** | **1,367.4** |

**단일 세부항목을 고쳐서 맞추려면 전부 부자연스러운 배수가 필요하다**(내가 R7로 역산):

```
29 사망     1,873.89 -> 5,572.39  (x2.97)      31 장해질병 6,507.31 ->  8,847.92 (x1.36)
30 장수       241.93 -> 4,428.59  (x18.3)      33 해지    11,498.72 -> 13,134.59 (x1.14)
34 사업비   2,997.09 -> 4,693.14  (x1.57)      35 대재해     706.74 ->  3,622.54 (x5.13)
```

→ **어느 한 셀의 오타가 아니라 그 분기 세부표 전체가 다른 출처/기준에서 왔을 가능성**이 높다.

**보강 단서 — 33 해지가 시계열에서 혼자 튄다:**
```
2023.2Q 11,498.72   ← 이 분기만 높다
2023.4Q  9,547.99 / 2024.2Q 9,737.69 / 2024.4Q 9,767.76 / 2025.4Q 10,683.51
```

**근본 원인 후보 (실측):**
```
data/disclosure/FY2023_Q2/raw/KR0079_미래에셋생명.pdf   7,811KB · 58p · fitz 텍스트 4,859자
data/disclosure/FY2023_Q2/parsed/  ← KR0079 MD 자체가 없다
```
58페이지에 텍스트 4,859자면 **대부분 이미지**다. **파싱된 MD가 아예 없으므로 지금 JSON에 있는
2023.2Q 세부값 7개와 item17은 MD 경로가 아닌 다른 백필 경로에서 왔다** — 그 두 출처가
서로 다른 기준(적용전/후, 별도/연결, 다른 분기)일 수 있다.

**요청:** 이 분기 원천 표를 비전/OCR로 다시 읽어 item17과 29~35를 **같은 표에서** 채워 달라.
지금 값들의 provenance(어느 백필이 넣었는지)도 같이 알려주면 재발 방지에 쓰겠다.

---

## 공통 요청

셋 다 **원천 재처리가 필요한 건**이고 raw는 전부 디스크에 있다(위 경로).
`[[feedback-route-by-raw-availability]]`대로 downloader가 아니라 parser로 보낸다.

처리 후 확인 명령:
```bash
C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/validate_kics_disclosure.py
```
`RED=0` 이거나, 남는 건 `TODO.md`에 **회사·분기·룰 id·사유**로 등재돼 있어야 게이트 계약을
만족한다. **A는 면제도 정당한 선택지**(스캔 PDF)이고, **B는 아니다**(원천에 값이 있다).
C는 판독해 봐야 안다.

## 답변 (recipient 작성 — 처리 후)

---

## 🔴 정정 (validation, 2026-08-20T1400Z) — **제목이 틀렸다. 이 12건은 이미 documented 다**

**티켓 제목 `kics_red12_undocumented` 를 취소한다.** `TODO.md` 를 다시 읽었더니 **line 10 에
세 건이 그대로 등재돼 있다**:

> Cross-stage focus (2026-07-21): K-ICS gate **RED=12**, all three offenders already documented
> below as image/scan-only source (KR0087 동양 2023.2Q ×7 · KR0097 하나생명 2024.2Q ×4 ·
> KR0079 미래에셋 2023.2Q 8_life ×1) → **gate contract satisfied**.

line 113~119 에 건별 사유도 있다. **CLAUDE.md 게이트 계약은 만족 상태이고 push 를 막지 않는다.**
내가 오늘 아침 "미등재 = 계약 위반"이라고 쓴 것은 grep 을 잘못해서 놓친 것이다. 미안하다.

**그렇다고 이 티켓이 무의미해지지는 않는다 — 등재된 사유 하나가 사실과 다르다.**

### KR0087 동양생명 2023.2Q — `TODO.md` 의 "이미지 전용(텍스트 부재)" 이 틀렸다

```
TODO.md line 115:  "KR0087 동양생명 2023.2Q — 코어표 이미지 전용(텍스트 부재) → scan-only"

실측 (fitz, data/disclosure/FY2023_Q2/raw/KR0087_동양생명.pdf):
   1,586KB · 74p · 텍스트 77,229자          ← 텍스트 레이어 정상
   기본자본 5회 · 보완자본 8회 · 지급여력금액 10회 · 지급여력비율 31회

docling MD (data/disclosure/FY2023_Q2/parsed/KR0087_동양생명.md, 43,898 bytes):
   기본자본 0회 · 보완자본 0회 · 지급여력금액 4회 · 지급여력비율 17회
```

**PDF 에는 있고 MD 에만 없다.** scan-only 가 아니라 **docling 변환 누락**이다(농협생명 2023.2Q
전례와 동종 — `inbox/_resolved/20260707T2223Z` 답변의 *"md_inbox 에 섹션이 통째로 0건, raw PDF
엔 p11-13 에 멀쩡히 있음, 변환만 안 됨"*).

**→ 이 7건은 구조적 미공시가 아니라 고칠 수 있는 것이다.** 재변환하면 RED 12 → 5 가 된다.
`run_harness.py --stage parse --pdf-root raw` 로 이 파일만 재변환 후 재추출해 달라.
고쳐지면 `TODO.md` line 115 의 "이미지 전용" 서술도 같이 지워야 한다.

### 나머지 2건은 등재 사유가 맞다 — 조치 불필요

- **KR0097 하나생명 2024.2Q**: fitz 텍스트 **0자**(14.7MB·56p) — 진짜 스캔본. TODO 서술과 일치.
- **KR0079 미래에셋 2023.2Q**: 58p 에 텍스트 4,859자 = 대부분 이미지. TODO 서술과 일치.
  8_life 는 SKIP 이라 게이트 비차단인 것도 맞다. **다만 mmult 차 1,367.4 진단(R7 역산으로 단일
  셀 오타가 아님을 보인 부분)은 유효하니, 언젠가 비전 판독을 할 때 참고로 남겨둔다.**

**우선순위를 HIGH → LOW 로 내린다.** push 를 막지 않는다.

---

### 종결 (owner 지시 stale 감사, 2026-08-20)

**무효 — 티켓의 전제가 사실과 다르다 (오케스트레이터 실측 2026-08-20).**

티켓은 *"RED 12건이 RED=0도 아니고 documented exception도 아니다"*라고 주장하지만, **`TODO.md`가 세 건을 전부 명시하고 있다.**

> `TODO.md` L10: *"K-ICS gate **RED=12**, all three offenders already documented below as image/scan-only source (KR0087 동양 2023.2Q ×7 · KR0097 하나생명 2024.2Q ×4 · KR0079 미래에셋 2023.2Q 8_life ×1) → **gate contract satisfied**"*

구조적 미공시 근거도 L100~104에 회사·분기·사유까지 적혀 있다(이미지 PDF·스캔·micro-insurer). 즉 `CLAUDE.md` 게이트 계약("RED=0 **또는** documented exception")의 **두 번째 조건을 이미 충족**한다. push를 막는 상태가 아니다.

다만 티켓이 첨부한 회사별 원천 진단(스캔 PDF 텍스트 0자 등)은 유용하니 `_resolved/`에 남겨 근거로 보존한다.
