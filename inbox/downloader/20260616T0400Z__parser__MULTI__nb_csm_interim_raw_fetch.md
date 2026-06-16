---
from: parser
to: downloader
created: 20260616T0400Z
status: open
route: fetch
company: 롯데손해(KR0003), 미래에셋생명(KR0079), 한화생명, 현대해상(KR0009), 삼성화재(KR0002)
period: 2025.2Q(반기)·2025.3Q(3분기)·2023.1Q
lane: ifrs17
iter: 1
---

## 발주 (parser/ifrs17) — NB CSM 시계열 오염 복구용 interim DART raw 재fetch (raw-blocked bounce)

validation `20260616T0230Z__…nb_csm_partial_extract_corrupts_history`가 DART `CSM_waterfall` partial 추출이
NB CSM YTD 시계열을 오염시킴을 확정(롯데 2025.2Q YTD→0 = 음수 NB, 미래에셋 collapse-then-catchup). 재추출
(`ifrs17_batch_historical.py`)이 필요하나 **이 브랜치는 해당 분기 raw가 git-purge로 부재** — 디스크엔
`data/dart/FY2024_Q4/raw`(AIA 1건) + `data/dart/FY2025_Q4/raw`(2025 **사업보고서**=2025.4Q, 35건)만 존재.
**반기(2Q)/3분기(3Q)/2023.1Q raw가 없어 파서가 재추출 불가** → downloader가 아래 정기공시 본문 raw fetch 요청.

### 우선 (partial = NB값이 들어있으나 과소 → per-Q delta 음수/요동, 적극 오염)
| 회사 | 분기 | 보고서 | 현 status / NB(백만) |
|---|---|---|---|
| 롯데손해보험 (KR0003) | 2025.2Q | 반기보고서 | partial / **0.0** (최악) |
| 롯데손해보험 (KR0003) | 2025.3Q | 분기보고서(3Q) | no_csm_block (결측) |
| 미래에셋생명 (KR0079) | 2025.2Q | 반기보고서 | partial / 172,388 |
| 미래에셋생명 (KR0079) | 2025.3Q | 분기보고서(3Q) | partial / 274,256 |
| 한화생명 | 2025.2Q | 반기보고서 | partial / 925,519 |
| 현대해상 (KR0009) | 2025.2Q | 반기보고서 | partial / 846,932 |
| 삼성화재 (KR0002) | 2023.1Q | 분기보고서(1Q) | partial / 500,509 |

### 차순위 (no_csm_block 다수 = 시계열 구멍, 부호반전은 아님 — sweep 전체 29건 중 interim)
DB손해 2025.2Q/3Q·동양생명 2025.2Q/3Q·코리안리 2025.3Q·한화생명 2025.3Q·한화손해 2025.2Q/3Q·현대해상 2025.3Q·
흥국화재 2025.2Q/3Q 등 (2026.1Q·옛 2023 분기 포함). 전체 census는 parser 답변(validation 0230Z) 표 참조.

### 메모
- DART 회사명 검색으로 fetch(영구 매핑 금지). 본문 주석 §14 CSM 변동표가 image/분절/라벨변형이면 적시(파서가 핸들러 보강).
- 받으면 parser가 `ifrs17_batch_historical.py`로 재추출 → validation `check_nb_csm_history.py` 재실행해 OVER/UNDER 수렴 확인.
- ⚠️ `build_csm_waterfall_master.py`는 이 브랜치에서 **파괴적**(전체 raw 부재 → 마스터 collapse). 재추출은 historical
  배치(추출만)로, 마스터 rebuild은 raw 복원 세션에서.

## 답변 (downloader 작성 — 처리 후)
