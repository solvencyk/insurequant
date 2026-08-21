---
from: validation
to: parser
created: 20260616T0230Z
status: resolved
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

## 후속 확인 2026-07-30 (parser/ifrs17)

`check_nb_csm_history.py` 재실행 확인: 롯데손해(KR0003) 7건·미래에셋생명(KR0079) 5건 등 여전히
OVER/UNDER 다수(총 27, 6주 전과 유사 규모). **단, 중요 발견**: 이 체커는 root `CSM_waterfall.json`이
아니라 별도 파일 `data/dart/viz/csm_waterfall_history.json`(진단용 히스토리 캐시)을 읽는다. 직접
대조 결과 **root 마스터는 이미 정상**(예: 롯데 2025.2Q 신계약 YTD=2135.4, 미래에셋 2025.2Q=2451.95 —
전부 단조증가, partial 붕괴 없음 — 언제·어느 세션이 고쳤는지 불명, TODO 미기록). 즉 **실제 라이브
데이터(root 마스터)는 이 건 대부분 해소된 상태**이나, **진단 파일(`csm_waterfall_history.json`)이
그 갱신을 못 따라가 재실행 시 여전히 옛 문제를 보고**한다 — false-negative 방향(실제 좋은데 진단이
나쁘다고 함)이라 라이브 리스크는 낮지만, 이 체커를 신뢰하는 향후 세션이 혼란스러울 수 있음.
**req1(반기/3분기 interim 레이아웃 추출기 미인식)은 root 마스터 우회 경로로 실질 해소됐을 가능성이
높으나, `csm_waterfall_history.json` 자체의 재생성(및 그 생성 스크립트의 interim 레이아웃 인식)은
여전히 미완 — dedicated 세션에서 (a) root 마스터가 어떻게 고쳐졌는지 역추적(diag/override 확인),
(b) `csm_waterfall_history.json` 재생성 스크립트를 그 방식과 정합시키는 작업 권장. 이번 세션은
범위 밖으로 두고 기록만.**

## 갱신 (2026-08-15, parser/ifrs17) — 생성기 실행 완료, 부분 개선, 진짜 남은 스코프 확정(여전히 open)

생성 스크립트를 찾아 실행했다 — `scripts/viz_build_csm_waterfall_history.py`가 아니라
`archive/2026-06_csm_nb_reverse_engineering/viz_build_csm_waterfall_history.py`로 옮겨져 있었다
(예전에 "일회성 reverse-engineering 도구"로 분류돼 archive됐는데, 산출물은 계속
`check_nb_csm_history.py`에 연결돼 있던 상태 — 고아 파이프라인). 경로 깊이 문제(`ROOT =
parents[1]` 하드코딩, archive 이동으로 한 단계 어긋남) 때문에 `scripts/`에 임시 복사해 실행 후
삭제(원본은 안 건드림).

**결과**: status 분포 `no_csm_block 29·partial 6→3·no_extract 3→5·empty_extract 1`(41→38
non-ok) — partial(가장 심각한 카테고리, YTD 붕괴)이 6→3으로 절반 개선. company/period
커버리지 손실 0(23사×13분기 그대로).

**그런데 `check_nb_csm_history.py` 재실행해도 OVER/UNDER **여전히 27건**(줄지 않음).** 원인
확인: 이 생성기는 `data/dart/extracted_history/*_csm.json`(원시 추출 중간산출물)에서
읽는데, **root `CSM_waterfall.json`을 실제로 고친 경로(owner-verified override 등)가
`extracted_history`를 거치지 않았다** — 즉 중간산출물 자체가 여전히 옛 버그값을 담고 있어서,
"정직하게" 재생성해도 같은 값이 재생산된다. root가 옳고 진단파일이 root를 못 따라간다는
원래 진단이 정확했고, **재생성만으로는 못 고친다**는 게 이번에 새로 확정된 사실.

**진짜 남은 선택지 (다음 세션용, 둘 중 하나)**:
1. `extracted_history/*_csm.json`을 27건 대상으로 raw 재추출(진짜 fix, 근본적) — interim
   레이아웃 인식 보강 필요, 큰 작업.
2. root `CSM_waterfall.json`의 이미 올바른 값을 `csm_waterfall_history.json`에 직접
   overlay하는 sync 스크립트(재추출 아님, 진단파일을 authoritative source에 맞추는 것) — 작지만
   "진짜 재추출"은 아님, 라벨링 명확히 할 것.
이번 패스는 시간상 여기서 stop — 큰 결정(1 vs 2, 또는 owner 판단) 없이 진행하지 않음. 스레드
open 유지, 스코프는 이제 훨씬 명확.

---

### 종결 (owner 결정, 2026-08-20)

NB CSM 진단파일 오염 **drop (owner 2026-08-20)** — 대상 파일이 이미 화면에서 폐기됐다.

parser가 제시한 두 선택지(27건 raw 재추출 vs sync 스크립트)는 **둘 다 불필요하다.**
오케스트레이터 실측:

- `IFRS17.html` L1525 주석: *"기존 csm_waterfall_history.json은 stale(...)이라 **폐기**"* —
  Panel 6 CSM 시계열은 이제 `CSM_waterfall.json`(`ix.wfx`)을 쓴다.
- `ix.hist` Map은 선언·적재만 되고 **읽는 코드가 없다**(`.hist` 참조는 전부 `charts.hist`=
  Chart.js 인스턴스명). 즉 `csm_waterfall_history.json`은 **fetch만 되고 안 쓰이는 죽은 요청**이다.
- 라이브가 실제로 읽는 `NB_CSM_multiple.json`은 **정상**이다 — 롯데손해 2025년 시계열이
  1,098.5 → 2,135.4 → 3,147.3 → 4,121.7(YTD 누계 단조증가)로, 이 티켓이 보고한
  'YTD 0 추락 → 음수 NB' 증상이 **없다**.

죽은 fetch 제거는 designer에 별도 발주(`20260820T0430Z`).
