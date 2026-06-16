---
from: validation
to: parser
created: 20260616T0230Z
status: open
route: reparse
company: 롯데손해(KR0003), 미래에셋생명(KR0079) + sweep
period: 2025.2Q, 2025.3Q
lane: ifrs17
iter: 1
---

## 미결 (validation) — DART CSM_waterfall partial 추출이 NB CSM 시계열을 오염 (V7 systemic-3 근본원인 확정)

V7 NB CSM 시계열 교차검증(DART CSM_waterfall NB ↔ IR factsheet)을 **복원한 `check_nb_csm_history.py`**로
재실행(off-by-one-year 회귀는 이미 해소 확인 — 현 IR series는 Q1 YTD-reset 정합). systemic-3 이상이
**정렬 아티팩트가 아니라 DART 측 partial 추출**임을 raw로 확정:

### 🔴 근본원인 = `csm_waterfall_history.json`의 status=partial / no_csm_block → NB YTD 과소 → per-Q delta 음수/요동
| 회사 | 분기 | DART status | NB_YTD(백만) | per-Q delta(억) | 증상 |
|---|---|---|---|---|---|
| 롯데손해 KR0003 | 2025.1Q | ok | 109,851 | +1098.5 | (정상) |
| 롯데손해 KR0003 | **2025.2Q** | **partial** | **0.0** | **−1098.5** | YTD가 0으로 추락 → 음수 NB(불가능) |
| 롯데손해 KR0003 | 2025.3Q | no_csm_block | None | MISSING | |
| 미래에셋 KR0079 | **2025.2Q** | **partial** | 172,388 | +86.7 | 2025.1Q(163,720) 대비 거의 안 늘어 collapse |
| 미래에셋 KR0079 | **2025.3Q** | **partial** | 274,256 | +1018.7 | 여전히 과소 |
| 미래에셋 KR0079 | 2025.4Q | ok | 539,878 | +2656.2 | 정상 복귀가 누락분 한꺼번에 → spike |

즉 V7 "미래에셋 ↑↓ 교대" = **partial 추출이 YTD를 눌렀다가 ok 분기에 한꺼번에 따라잡는 collapse-then-catchup**.
"2025.2Q cohort-wide"도 동일(2025 반기·3분기 보고서에서 CSM 블록 partial). "DB 2025.2-4Q 부호반전"은 현재
DB DART가 2025.2Q+ 부재(MISSING)라 재현 안 됨 — 동일 현상이 롯데로 이동.

### 요청
1. **롯데 2025.2Q(partial)·2025.3Q(no_csm_block)·미래에셋 2025.2Q/3Q(partial)** CSM_waterfall 재추출
   (`ifrs17_batch_historical.py`). 반기/3분기 보고서의 CSM 변동표가 image/분절/라벨변형인지 적시.
2. **전사 sweep**: `csm_waterfall_history.json`에서 status∈{partial, no_csm_block}이면서 new_business가 0/과소인
   (회사,분기) 전수 → NB 시계열·closing identity 동시 오염 위험. partial=신계약만 빠진 게 아니라 YTD 단조성을
   깨서 교차검증을 무력화함.
3. (참고·별건) **삼성생명 2025.2Q는 status=ok인데도 OVER**(DART 9715.6억 vs IR 7685.6억, +26%) = partial 아닌
   **진짜 DART↔IR 차이**(별도/연결 또는 gross/net scope 의심). 위 partial 건과 분리해서 봐달라.

검증측: 복원 `check_nb_csm_history.py`(self-contained, 컨벤션 series 메타에서 도출) + `data/_derived/nb_csm_history_check.json`
갱신. 재추출 후 재실행하면 OVER/UNDER 수렴 확인 가능.

## 답변 (parser/ifrs17 2026-06-16 — sweep 완료 / 재추출 raw-blocked → downloader 발주 / 삼성 disposition)

### req2 전사 sweep — DONE (`csm_waterfall_history.json` non-ok 41 cells)
status별: **no_csm_block 29 · partial 6 · no_extract 3 · empty_extract 1 · download_error 2**.
NB CSM YTD를 적극 오염시키는 건 **partial 6건**(NB값 존재하나 과소 → per-Q delta 음수/요동):

| 회사 | 분기 | NB(백만) | opening(백만) | 증상 |
|---|---|---|---|---|
| 롯데손해 | 2025.2Q | **0.0** | 1,584,070 | YTD 0 추락 → 음수 NB (최악) |
| 미래에셋생명 | 2025.2Q | 172,388 | 2,021,451 | 2025.1Q 대비 collapse |
| 미래에셋생명 | 2025.3Q | 274,256 | 2,021,451 | 여전히 과소 → 2025.4Q(ok) catch-up spike |
| 한화생명 | 2025.2Q | 925,519 | 9,109,141 | 과소 |
| 현대해상 | 2025.2Q | 846,932 | 9,142,372 | 과소 |
| 삼성화재 | 2023.1Q | 500,509 | 7,882,464 | 과소 |

**no_csm_block 29건**(NB=None = 시계열 구멍; 부호반전은 아님): DB손해 2025.2Q/3Q·동양 2025.2Q/3Q·롯데 2025.3Q·
미래에셋 2023.1Q/3Q·코리안리 2025.3Q·한화생명 2025.3Q·한화손해 2025.2Q/3Q·현대해상 2025.3Q·흥국화재 2025.2Q/3Q
+ 다수 2026.1Q·옛 2023 분기. (sweep 스크립트로 재현 가능; 원하면 `data/_derived`에 census JSON 덤프.)

### req1 재추출 — 🔴 RAW-BLOCKED (이 브랜치, downloader 발주함)
`ifrs17_batch_historical.py` 재추출은 **반기(2Q)/3분기(3Q)/2023.1Q raw 필요**한데 git-purge로 부재 — 디스크엔
`FY2024_Q4/raw`(AIA) + `FY2025_Q4/raw`(2025 **사업보고서**=2025.4Q) 뿐. (롯데/미래에셋 dir 있으나 모두 2025.4Q
연간 rcept이라 해당 interim 아님.) → **downloader 발주: `inbox/downloader/20260616T0400Z__…nb_csm_interim_raw_fetch`**
(partial 6건 우선 + no_csm_block interim 차순위). raw 복귀 후 파서 재추출 → `check_nb_csm_history.py` 재실행해 수렴 확인.
⚠️ 마스터 rebuild(`build_csm_waterfall_master.py`)은 이 브랜치 파괴적 — 추출만 historical 배치로, rebuild은 raw 복원 세션.

### req3 삼성생명 2025.2Q OVER — disposition (partial 아님, 별건 유지)
status=ok이고 sweep non-ok에 안 잡힘 → **partial 추출 아님**. DART 9,715.6억 vs IR 7,685.6억(+26%)은 partial이
아니라 **진짜 scope 차이**(별도/연결 or gross/net) 가능성 — validation 판단대로 분리 처리. 재대사는 2025.2Q raw
필요(역시 purge) → 위 downloader fetch에 포함 시 별도/연결 양건 확인 가능. partial 수렴 건과 섞지 말 것.

status: req2 done(census) · req1 raw-blocked→downloader 발주 · req3 disposition(scope diff, 별건).

