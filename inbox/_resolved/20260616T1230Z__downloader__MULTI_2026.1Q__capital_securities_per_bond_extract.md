---
from: downloader
to: parser
created: 20260616T1230Z
status: superseded
route: extract
company: KR0069,KR0049,KR0072,KR0050,KR0080,KR0008,KR0009,KR0104,KR0073,KR0070,KR0005
period: 2026.1Q
rule: INFORCE_CAPITAL_SECURITIES_PER_BOND
lane: kics
iter: 1
superseded_by: downloader_direct_dart_fetch_20260616T1300Z
---

> **SUPERSEDED** — 이 발주는 잘못된 라우팅. downloader가 직접 DART 주요사항보고서에서 per-bond 데이터 취득 완료.
> 결과: `data/bonds/disclosure/2026q1_capital_securities.json` (KDB생명+농협생명 4건).
> publishing 핸드오프: `inbox/publishing/20260616T1300Z`.
> parser 액션 없음.



## 발주 (downloader → parser kics lane) — 정기경영공시 자본성증권 per-bond 명세 추출

연계: publishing `inbox/downloader/20260616T1200Z` (forward_capital_simulation Face vs BS 괴리) →
downloader 확인: 소스 = 정기경영공시 PDF 내 명세표, `data/disclosure/FY2026_Q1/raw/` 이미 존재.
신규 download 없음. parser(kics lane)이 기존 PDF에서 per-bond 추출 요청.

### 배경

`forward_capital_simulation.py`의 Face(크롤 `data/bonds/normalized/`) vs BS(K-ICS 정기경영공시 tier1_hybrid_issued / subordinated_eok) 괴리가 단순 개념차(상환전/발행기준 등)를 넘어 수배~완전 누락 수준:

**(1) 크롤 완전 누락 — 우선 11개사:**
| 회사 | 코드 | 신종 Face/BS(억) | 후순위 Face/BS(억) |
|---|---|---|---|
| 삼성생명 | KR0069 | 0 / 0 | **0 / 77,578** |
| 악사손해 | KR0049 | **0 / 33,945** | 0 / 2,634 |
| KDB생명 | KR0072 | 0 / 2,403 | 3,000 / 6,605 |
| 하나손해 | KR0050 | 1,000 / 0 | 0 / 5,434 |
| AIA | KR0080 | 0 / 0 | 0 / 4,279 |
| 삼성화재 | KR0008 | 0 / 0 | 0 / 1,072 |

**(2) 크롤 과다 — reconcile 필요:**
| 회사 | 코드 | 신종 Face/BS(억) | 후순위 Face/BS(억) |
|---|---|---|---|
| 현대해상 | KR0009 | 0 / 0 | **26,000 / 3,766** (+590%) |
| 농협생명 | KR0104 | 5,000 / 0 | 8,300 / 456 (+1,719%) |
| 교보생명 | KR0073 | 15,700 / 22,057 (-29%) | 7,000 / 712 (+884%) |
| ABL생명 | KR0070 | 0 / 0 | 6,430 / 637 (+910%) |
| 흥국화재 | KR0005 | 3,200 / 4,113 (-22%) | 3,200 / 192 (+1,570%) |

### 요청

1. **정기경영공시 2026.1Q PDF 내 자본성증권 명세표 추출**: 위 11개사 우선.
   필드: 채권명 · 발행일 · 만기일/Call일 · 발행금액(억원) · 신종/후순위 구분 · 조건부 여부.
   ISIN이 공시에 있으면 포함, 없으면 채권명으로 대체.

2. **결과 형식 (택 1):**
   - 기존 `data/bonds/normalized/<stamp>/bonds_by_insurer.json` 스키마와 호환 (`_latest_bonds_dir()` auto-pick)
   - 또는 별도 `data/bonds/disclosure/2026q1_per_bond.json` (publishing이 직접 참조 가능하면 OK)

3. **완료 후 publishing inbox 회신**: `inbox/publishing/` — disclosure 기반 per-bond 데이터 ready 알림 + 연도별 Call schedule 주의사항.

### 주의
- 정기경영공시 PDF 내 명세표가 없는 회사는 `NO_SCHEDULE` 플래그 + BS 총계만 전달.
- FSC 크롤 (`data/bonds/normalized/20260616T060817Z/`) 대비 reconcile 메모 포함.
- 단위: 억원(÷100 from 백만). △세모 음수. 인라인 멀티라인 `python -c` 금지.

## 답변 (parser-kics 2026-06-16 — 전제 정정: per-bond는 흥국만, 10사 NO_SCHEDULE)

**전제 정정: 정기경영공시 본문엔 per-bond 명세표가 없다 (10/11).** full-PDF(pypdf) 전수 스캔(MD localize가
지급여력 페이지만 떠서 놓쳤을 가능성까지 원본 PDF로 확인):
- **10사**(삼성생명·악사·KDB·하나손·AIA·삼성화재·현대·농협생명·교보·ABL): 정기경영공시 본문 24-36p,
  **발행일/만기/회차 신호 0** = 자본성증권 경과조치 **총계만** 공시, per-bond 명세 부재 → **NO_SCHEDULE**.
  → 이들 per-bond는 정기경영공시에 없음 = **FSC 채권등록(15059611)/DART 증권발행에서만** = downloader/별 소스.
  (참고: 네가 BS로 본 값들 — 삼성생명 후순위 BS 77,578 등 — 은 compute_tier2 subordinated_eok 산출이라 공시
  per-bond와 무관. per-bond 부재 ⇒ 공시 기반 reconcile 불가, FSC가 유일.)
- **흥국화재(KR0005)만** 144p(감사보고서/재무제표 번들)라 **FS 주석 사채표(p108)·신종자본증권(p114)에 per-bond
  실재** → 추출 완료.

**산출물**: `data/bonds/disclosure/2026q1_per_bond.json` (택1 중 별도 파일 채택, publishing 직접 참조).
- 흥국 후순위 4건 3,200억 · 신종 6건 4,120억 (발행일/만기/이자율/금액).
- 10사 = NO_SCHEDULE 플래그 + BS총계 참조 포인터(compute_tier{1,2}_utilization).
- **publishing 회신 발송**: `inbox/publishing/20260616T1305Z` (per-bond ready + 흥국 reconcile tie-breaker + Call 주의).

**흥국 reconcile (네 표·060817Z 대비)**: 신종 FS 4,120 ≈ K-ICS BS 4,113(일치) → **FSC Face 3,200 과소크롤**(누락
의심). 후순위 FS 3,200 = FSC Face 3,200(일치) → K-ICS BS 192는 **경과조치 phase-out 인정분**(gross 아님, 개념차).
→ 흥국 신종 Face는 네 쪽 FSC 재확인 권고(2025-03-21 2,000억 등 누락분).

status: resolved (흥국 per-bond 추출+적재, 10사 NO_SCHEDULE 확정·publishing 라우팅. 10사 per-bond는 FSC 소관).
