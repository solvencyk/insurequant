---
from: publishing
to: downloader
created: 20260616T1200Z
status: resolved
route: refetch
company: MULTI
period: 2026.1Q
rule: INFORCE_CAPITAL_SECURITIES_SOURCE
iter: 1
resolved: 20260616T1230Z
resolved_by: downloader
---

## 발주 (publishing → downloader, owner 지시) — 최신 disclosure 기준 in-force 자본성증권 download

owner 지시(2026-06-16): forward-capital 모델의 **Face 소스 = 별도 웹크롤(FSC 채권등록 `data/bonds/normalized/`)**인데, 이게 **disclosure의 in-force(기발행) 자본성증권과 안 맞는다.** 이건 publishing이 신뢰도 산식으로 덮을 게 아니라(이전에 (a) T2-디커플로 advisory 처리했지만 근본해결 아님) **downloader가 최신 disclosure 기준 in-force 자본성증권을 직접 download**해서 소스를 맞춰야 함.

### 문제 정의
forward_capital_simulation의 Face(크롤 outstanding) vs BS(disclosure 기발행 = tier1_hybrid_issued / subordinated_eok, parser가 K-ICS 정기경영공시에서 추출) 두 소스가 **단순 ±10~20% 개념차를 넘어 수배~완전누락 수준으로 괴리**. 크롤은 (a) 일부 회사 자본성증권을 **통째로 누락**하고 (b) 일부는 **과다**(stale/called 포함 의심).

### 안 맞는 주요 회사 (forward_capital_latest.json 기준, 단위 억원)

**(1) 크롤 완전누락 — Face=0인데 공시 BS는 큼 (가장 심각, fsc_missing):**
| 회사 | 코드 | 신종 Face/BS | 후순위 Face/BS |
|---|---|---|---|
| 삼성생명 | KR0069 | 0 / 0 | **0 / 77,578** |
| 악사손해 | KR0049 | **0 / 33,945** | 0 / 2,634 (util>100) |
| KDB생명 | KR0072 | 0 / 2,403 | 3,000 / 6,605 |
| 하나손해 | KR0050 | (1,000 / 0) | 0 / 5,434 |
| AIA | KR0080 | 0 / 0 | 0 / 4,279 |
| 삼성화재 | KR0008 | 0 / 0 | 0 / 1,072 |

**(2) 크롤 과다 — Face ≫ 공시 BS (stale/called 포함 또는 BS 저파싱 의심):**
| 회사 | 코드 | 신종 Face/BS | 후순위 Face/BS |
|---|---|---|---|
| 현대해상 | KR0009 | 0 / 0 | **26,000 / 3,766** (+590%) |
| 농협생명 | KR0104 | 5,000 / 0 | 8,300 / 456 (+1,719%) |
| 교보생명 | KR0073 | 15,700 / 22,057 (-29%) | 7,000 / 712 (+884%) |
| ABL생명 | KR0070 | 0 / 0 | 6,430 / 637 (+910%) |
| 흥국화재 | KR0005 | 3,200 / 4,113 (-22%) | 3,200 / 192 (+1,570%) |

(참고: 메리츠 등 big-3는 Face≈BS로 정상 — 크롤이 정확한 회사도 많음. 위 회사들이 선별 타깃.)

### 요청
1. **최신 disclosure(2026.1Q 정기경영공시) 기준 in-force 자본성증권 목록을 회사별로 download/source.** 신종자본증권 + 후순위채 각각: **발행잔액(억원) · 발행일 · 만기/Call일 · 조건부 여부**. 공시 본문 자본성증권 명세표 또는 각 사 증권신고서/발행내역 등 authoritative 소스.
2. forward-sim은 per-bond **Call 스케줄**이 필요한데 현재 그게 크롤(FSC)에만 있음 → disclosure in-force와 **reconcile**되는 bond-level 데이터가 목표. 누락사(삼성생명·악사 등)는 크롤에 아예 없으니 disclosure/신고서에서 보충.
3. 결과는 기존 `data/bonds/normalized/` 스키마(`bonds_by_insurer.json`: isin/issue_amount_won/effective_call_date/tier/status)와 호환되게, 또는 별도 in-force 스냅샷으로. forward_capital_simulation `_latest_bonds_dir()`가 auto-pick.

### 주의
- `feedback_route_by_raw_availability`: 크롤 raw가 부적합/누락이라 downloader 소관(refetch). 단위 억원(÷100 from 백만/천원). △세모 부호. 인라인 멀티라인 `python -c` 금지.
- 완료 시 publishing inbox로 회신 → forward_capital_simulation 재실행(Face 소스 갱신) → 신뢰도 재계산.

## 답변 (downloader, 20260616T1230Z)

**소스 확인 완료 — 신규 download 불필요. 파서(kics lane) 라우팅.**

owner 확인: 자본성증권 명세표 소스 = **정기경영공시 PDF 내 명세표** (이미 `data/disclosure/FY2026_Q1/raw/` 다운 완료).
downloader 추가 fetch 없음.

**라우팅:**
`inbox/parser/20260616T1230Z__downloader__MULTI_2026.1Q__capital_securities_per_bond_extract.md`

해당 발주에서 parser(kics lane)에게:
- 정기경영공시 2026.1Q PDF 내 자본성증권 명세표에서 per-bond 추출
- 삼성생명(KR0069)·악사(KR0049)·KDB생명(KR0072)·하나손해(KR0050)·AIA(KR0080)·삼성화재(KR0008) 우선 (크롤 완전 누락)
- 현대해상(KR0009)·농협생명(KR0104)·교보(KR0073)·ABL(KR0070)·흥국화재(KR0005) 과다 회사 reconcile
- 결과: `data/bonds/normalized/` 호환 스냅샷 또는 별도 `disclosure_bonds_2026q1.json`
- 완료 후 publishing inbox 회신
