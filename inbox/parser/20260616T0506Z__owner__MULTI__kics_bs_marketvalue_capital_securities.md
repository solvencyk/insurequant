---
from: owner
to: parser
created: 20260616T0506Z
status: answered
route: backlog
company: MULTI
period: 2026.1Q
lane: kics
iter: 1
---

## 미결 (owner 라이브 QA) — tier1/tier2 모델 신뢰도 / BS 시가 파싱 점검

**증상:** K-ICS.html tier1/tier2 자본 패널에서 **"모델 신뢰도: 낮음" 항목이 너무 많고**, "Face vs BS 차이(T1/T2): 0.4% / −11.6%"처럼 **T2의 BS 시가 reconciliation이 광범위하게 어긋남**(T1은 0.4%로 양호, T2 −11.6%는 큼).

**가설:** 26.1Q 기준 **기발생 자본성증권(신종자본증권·후순위채)의 BS상 시가**를 아직 똑바로 파싱하지 못했을 가능성. Face(발행액)는 맞는데 BS(시가) 쪽이 틀려서 신뢰도가 깎이는 패턴으로 보임.

### 점검 2건
1. **BS 시가 파싱 검증 (parser-kics 본건).** 26.1Q K-ICS 공시의 BS/자본 항목에서 기발생 신종자본·후순위채의 **시가(장부/공정가치)**를 정확히 추출했는지 raw 대조(`data/disclosure/FY2026_Q1/.../parsed/*.md`). tier 산식(`scripts/compute_tier1_utilization.py` / `compute_tier2_utilization.py`)의 **BS-side 입력값**이 올바른지, 어디서 −11.6%가 생기는지 원인 적시.
2. **발행현황 크롤링 검증.** 26.1Q 기준 **발행중인 신종자본증권 + 후순위채(Face/발행액)**가 제대로 수집됐는지. 출처 = data.go.kr 자본성증권 API(`15059611`, `src/bonds/fsc_client.py`) = **downloader 소관**.

### 라우팅
- BS 시가(#1)는 **parser-kics**가 직접 검증.
- 크롤링(#2)이 갭이면 → **downloader inbox로 바운스**(`route: refetch`, "26.1Q 자본성증권 발행현황 stale/누락"). 
- "모델 신뢰도" 산식이 Face/BS 어느 노이즈에 민감한지 진단해 **신뢰도 낮음 다수가 진짜 데이터 갭인지 vs 산식 임계 문제인지** 구분해서 회신.

### 주의
- `data/disclosure/` raw는 git purge 무관(디스크 존재) — 26.1Q 검증 가능.
- 단위 백만원↔억, △(세모) 부호. python 풀패스 `C:\Users\sangwook.cho\venvs\insurequant\Scripts\python.exe`. 인라인 멀티라인 `python -c` 금지.
- 맥락: 메모리 `reference_kics_capital_tiering` — 도넛 분자=신종 **발행액**(KOFIA/Face), 분모=한도; tier1 100%+는 Ⅴ.1 excess 파싱누락 artifact. **이 건은 그 모델의 BS-side(시가) 신뢰도 점검**(별개 축).

## 답변 (parser-kics 2026-06-16 — 진단: 데이터 갭 아님 = stale baseline + 산식 개념차)

**결론: BS 시가 파싱은 정상. "−11.6%"는 파싱오류·데이터갭이 아니라 (a) 패널이 2025.4Q stale baseline +
(b) Face vs BS가 서로 다른 개념을 비교하는 산식 문제.**

**#1 BS 시가 파싱 검증 (parser 본건) — ✅ 정상.** 코드경로: `forward_capital_simulation.py`의 `compute_confidence`
가 Face(FSC 후순위 outstanding)와 BS(`compute_tier2_utilization.subordinated_eok`)를 `_pct_gap`(L179)으로 비교 →
`t2_gap_pct`. 메리츠 KR0001 2026.1Q **직접 재실행**(`--quarter 2026.1Q --md-dir md_inbox/FY2026_Q1`):
- MD `KR0001_…_2026.1Q` L394-395: `(기발행 신종자본증권) 179,195` · `(기발행 후순위채무) 1,775,387`(백만) →
  hybrid **1,791.95억** · sub **17,753.87억** = **소스 그대로 정확 추출**. 39사 전부 파싱(2025.4Q 17,988.8과 일관).
- 즉 BS-side 입력 정상. −11.6% = Face(FSC outstanding **15,910억**) vs BS(K-ICS 기발행 후순위 **17,753.87억**)의
  **1,843억 실차이**.

**왜 차이? = 개념 불일치(파싱오류 아님).** K-ICS "기발행 후순위채무" = **경과조치 기준 2022-까지-발행 자본성증권
인정액**(보완자본 grandfathered). FSC `tier2_subordinated_outstanding_won` = **채권등록 현재 outstanding face**.
경과조치 기발행분 ⊋ 현재 outstanding(상환·신종/후순위 경계·해외발행 차이) → 후순위는 구조적으로 BS>Face.
**T1이 0.4%로 양호한 이유**: 신종자본증권은 두 소스가 거의 일치(개념차 작음); 후순위만 큼.

**#2 발행현황 크롤링(Face) — 신선, downloader 갭 아님(재확인만).** `data/bonds/normalized/20260525T061945Z/`
= 2026-05-25 스냅샷 ⊃ 2026.1Q(3월말). Face stale 아님. (다만 owner가 2026.1Q 신규 후순위 발행 누락을 의심하면
downloader `route: refetch`로 별도 확인 가능 — 현재로선 갭 신호 없음.)

**"모델 신뢰도: 낮음" 다수(2025.4Q manifest 22/37) = 산식·임계 문제, 데이터 갭 아님:**
- **(가) stale baseline**: `forward_capital_simulation.py` L46 `BASELINE_QUARTER="2025.4Q"` 하드코딩 +
  L44 `tier2_utilization_20254Q.json` 경로 고정 → owner가 보는 2026.1Q 패널은 **2025.4Q 수치**(2026.1Q 산출물
  부재였음). 화면 라벨이 분기와 어긋날 수 있음.
- **(나) 산식 민감도**: `_overall_bucket`(L185) = "T1·T2 중 **하나라도 low면 전체 low**". T2 임계
  `T2_GAP_HIGH 30% / MED 75%`(L58) — 후순위 개념차(±10~수십%)가 큰 회사가 T2 low로 떨어지면 전체 신뢰도 low.
  즉 **신뢰도 낮음 = T2 Face-vs-BS 개념차에 산식이 민감**한 것이지 BS 파싱 실패가 아님.

**권고(산식/모델 — parser 소관 밖, 라우팅):**
1. **2026.1Q 패널 재생성**: 내가 `output/tier1_utilization/tier1_utilization_20261Q.json` +
   `tier2_utilization_20261Q.json` **생성해둠**. 남은 건 `forward_capital_simulation.py` baseline=2026.1Q로
   재실행 + K-ICS.html `window.FORWARD_DATA` 갱신 = **model/publishing + designer 소관** → 라우팅 권고.
2. **T2 신뢰도 산식 재고**: Face(채권등록 outstanding)와 BS(K-ICS 경과조치 기발행)는 **동일 개념으로 맞출 수
   없음**(K-ICS는 bond-level outstanding 미공시). 따라서 (옵션) T2 임계를 개념차 반영해 완화하거나, 신뢰도를
   **T1 위주**로 두고 T2 Face-vs-BS는 참고지표로 분리하는 게 맞음. = model owner 결정.

**요약**: parser BS-side = 정상(소스 충실). 진짜 문제 = stale 2025.4Q baseline + Face/BS 개념 불일치에 민감한
신뢰도 산식. **데이터 갭 아님.** 2026.1Q utilization 산출물은 생성 완료, 패널 재생성·산식조정은 model/publishing.
status: parser 진단 완료(answered).

**발주 후속 (2026-06-16, owner "산식까지 손봐서 갱신" 지시):**
- → **publishing** `inbox/publishing/20260616T0600Z` (OPEN): 2026.1Q 재베이스라인 + 신뢰도 산식 수정(T2 디커플링
  권장). 2026.1Q tier1/tier2 utilization 산출물 첨부.
- → **designer** `inbox/designer/20260616T0605Z` (BLOCKED on publishing): K-ICS.html `window.FORWARD_DATA` 재임베드.
