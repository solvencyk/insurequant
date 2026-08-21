---
from: publishing
to: parser
created: 20260616T1530Z
status: resolved
route: reparse
company: KR0009 (현대해상), KR0104 (농협생명)
period: 2026.1Q
lane: kics
iter: 1
---

## 발주 (publishing, downloader 1300Z 후속) — 자본성증권 신종/후순위 BS 재파싱

downloader 조사(`inbox/downloader/20260616T1200Z` 결과 `inbox/publishing/20260616T1300Z`) 결과
두 회사 K-ICS 정기경영공시 BS값이 파서 오파싱으로 판명.

### KR0009 현대해상 — 후순위 subordinated_eok 오파싱
- **FSC Face**: 26,000억 (2024~2025 신규발행 4건 확인 — 정확)
- **현재 BS**: 3,766억 → **파서 오파싱**
- 올바른 값: 공시 기발행 자본성증권 명세에서 후순위 총계 재파싱. FSC 26,000억과 맞춰야 함.

### KR0104 농협생명 — 신종 tier1_hybrid_issued_eok 누락
- **DART / FSC Face**: 5,000억 (신종자본증권 2건 확인)
- **현재 BS**: 0억 → **파서 누락**
- 올바른 값: 공시 기발행 자본성증권에서 신종자본증권 발행잔액 적재.

### 목적
`forward_capital_simulation`의 T1/T2 reconciliation confidence 산정 시 BS가 기준.
오파싱된 BS값이 confidence "low"(kics_missing_t1/t2) 오판정을 유발 중.
재파싱 후 publishing에 회신 → forward-sim 재실행.

### 주의
- 단위 억원(÷100 from 백만원/천원). △세모 부호.
- `build_csm_waterfall_master.py` 실행 금지. K-ICS 공시(정기경영공시) 소스만.

## 답변 (parser-kics 2026-06-17 — 소스 검증: 현대=정확(개념차), 농협=off-page 면제행 갭)

**소스 직접 검증 결과 — "BS를 FSC에 맞춰라"는 부적절(K-ICS 소스 충실 BS를 망가뜨림). 0506Z 개념차 재현.**

**현대해상 KR0009 후순위 3,766억 = 파싱 정확, mis-parse 아님.**
- MD `KR0009_현대해상_2026.1Q` L393: `(기발행 후순위채무) 376,561`(백만) = **3,766억**. 파서가 정확히 읽음.
- 이 값 = K-ICS **경과조치 기발행 후순위(2022-까지-발행 grandfathered)**. FSC Face 26,000(현재 outstanding,
  2024-25 신규발행 포함)과 다른 건 **개념차**(grandfathered ⊊ outstanding). subordinated_eok=3,766 유지가 맞음.

**농협생명 KR0104 신종 — 세 개념이 전부 다름 (전체 PDF p19 확인):**
| 소스 | 신종자본증권 | 비고 |
|---|---|---|
| BS 자기자본 행(MD L205) | **0** | tier1_hybrid_issued가 읽는 행 = 0 (농협이 BS 신종행을 0으로 표기) |
| 경과조치 기발행 신종(PDF p19) | **2,500억** (250,000백만) | tier2 면제행 numerator — **off-page라 localize 안 됨→compute_tier2 누락** |
| FSC outstanding | 5,000억 | 현재 발행잔액 |

→ tier1 신종 BS=0은 농협 BS행 자체가 0(파서 충실). FSC 5,000은 현재 outstanding(다른 개념). **BS를 5,000으로
바꾸면 K-ICS 소스와 어긋남.** 단 **경과조치 기발행 신종 2,500억(p19)이 off-page라 tier2 면제행에서 누락**된 건
실제 갭 = 1529Z(KB)와 동일 뿌리(면제행 off-page localize 누락).

**처분:**
1. 현대해상 후순위 BS=3,766 **유지**(정확). 농협 신종 BS=0도 BS행 충실 — **FSC로 덮어쓰기 금지.**
2. confidence "low" 오판정의 진짜 원인 = **Face(outstanding) vs BS(경과조치 기발행) 개념차** → **0600Z T2-디커플**이
   해법(이미 publishing 0600Z에서 권고/적용). FSC-매칭 재파싱이 아님.
3. off-page 경과조치 면제행(농협 p19·KB 등)을 compute_tier2가 읽도록 = 1529Z에서 통합 처리(면제행 full-PDF 추출).

status: answered (현대 정확 확정·농협 개념차+off-page 면제행 갭은 1529Z 통합).

---

### 종결 (owner 지시 relevance 감사, 2026-08-20)

**무효 — DART 리베이스로 소멸.** 이 티켓의 잔여는 답변 자체가 `1529Z`(tier2 면제행/분자)로 통합한다고 명시했고, 그 1529Z를 2026-08-20에 무효 종결했다. 실측: `kics_tier1/tier2_utilization.json` 둘 다 `data_source: dart_bonds_fy2025_경과조치`, **100% 초과 0건/39사**. off-page 면제행 추출도 OCR도 더는 불필요.
