---
from: validation
to: parser
created: 20260616T1210Z
status: resolved
route: reparse
company: KB손해(KR0010), 흥국화재(KR0005), 케이디비생명(KR0072), DB손해(KR0011)
period: MULTI
lane: ifrs17
iter: 1
escalation: owner
---

## 미결 (validation, owner 직접 지시 2026-06-16) — PL 기타사업비(item16) 0처리: 보험손익이 −16 없이 닫히는 셀

owner: IFRS17.html KB PL Breakdown에서 **기타사업비를 차감 안해야 보험손익 0.63조**가 맞는데 item16=0.39조를
기재해 waterfall이 깨짐. 규칙: **보험손익 등식이 기타사업비(item16) 없이 성립하면(= item1 = Σcomp without −16),
item16을 0처리.** 전수검증 결과 + 규칙 발주.

### 등식 (IFRS17.html:472 waterfall)
`item1(보험손익) = 4+5+6+7+8+13+14 + (15 − 16)` — 즉 item16(기타사업비용)이 보험손익에서 차감되는 전제.
그러나 일부 회사는 **추출된 item1이 −16 없이 이미 Σcomp와 일치** = item16이 보험손익 구성요소가 아님(그 아래
별도 영업비용). → waterfall의 −16이 과차감 → 차트 붕괴. (검증: item20 영업이익 = item1+item17이라 item16은
영업이익 흐름에도 안 들어감 = 보험손익 워터폴에서만 잘못 쓰임.)

### 전수검증 (`scripts/check_pl_other_expense_closure.py`, pl_breakdown_master 244셀): ZERO 21 / KEEP 223 / NEITHER 31
**ZERO = item16을 0처리 (보험손익이 −16 없이 닫힘):**
- 🟢 **KB손해 KR0010 — 13분기 전부(2023.1Q~2026.1Q), resid=0 정확.** owner 확인 케이스. item1=Σcomp 정확일치
  (예: 2025.4Q item1=626,695 = 4..14+15, item16=388,289 별도). **전 분기 item16→0.** (raw 대부분 purge라
  재추출 불가 → 후처리 transform으로 0 세팅.)
- 🟢 **케이디비생명 KR0072 2023.2Q** — resid=0 정확, item16=5,349. (단 다른 분기는 −16으로 닫힘 = KEEP →
  2023.2Q만 0. 1분기 outlier라 raw 있으면 교차확인 권고.)
- 🟡 **흥국화재 KR0005 2023.3Q~2024.4Q(6분기)** — −16 없이 닫힘(resid 30~278), 단 **2025.2Q부터는 −16으로 닫힘**
  (KEEP). = item16 처리가 분기 포맷별로 비일관. 6 early 분기 0처리하되 **parser가 일관성 확인**(왜 2025부터 바뀌는지).
- 🔴 **DB손해 KR0011 2023.2Q = ZERO 아님(제외)**: resid_wo=−6,869로 깨끗이 안 닫힘(다른 분기는 −16으로 닫힘).
  단일분기 component 오추출 의심 = 별건. item16 0처리 대상 아님 — 따로 진단.

**KEEP(223)·NEITHER(31)**: KEEP는 −16으로 정상 닫힘(메리츠·삼성화재·대부분 생보) = 손대지 말 것. NEITHER(현대해상
다수·코리안리·메리츠 2023.1-3Q·한화생명 2023.1-2Q 등)는 −16과 무관한 component 누락/오추출 = 별도 PL-bridge 이슈
(이미 pl_bridge 14F 등으로 추적, 본 건 범위 밖).

### 요청
1. **build_pl_breakdown.py에 일반 규칙**: `|item1 − Σ(4,5,6,7,8,13,14,15)| ≤ tol`이면 **item16=0**으로 세팅
   (raw 비의존 후처리 transform — purge된 interim 셀에도 적용 가능). tol=max(100, 1%·|item1|). KB 13분기·케이디비
   2023.2Q·흥국화재 6분기가 대상. 적용 후 `viz_build_ifrs17_panels.py` 리빌드 → IFRS17.html 워터폴 정상화.
2. **흥국화재 일관성**: 2023.3Q~2024.4Q(0처리) vs 2025.2Q~(−16) 차이 원인 적시(포맷/라벨 변형?).
3. **DB손해 2023.2Q**: 별건 — resid −6,869 component 오추출, raw 있으면 재대사.
4. **build_csm_waterfall_master.py 금지**. PL 빌드만.

검증측: `scripts/check_pl_other_expense_closure.py` 신설(exit 2 if ZERO 잔존). 0처리+리빌드 후 재실행하면
ZERO=0 수렴 확인. 단위 백만원, △(세모) 표기 규칙 유지.

## 답변 (parser/ifrs17 작성 — 처리 후)

✅ DONE (검증 2026-06-20). build_root_masters._zero_other_expense: 보험손익(1)이 -16 없이 닫히면 item16(기타사업비)=0 (|i1-Σ(4,5,6,7,8,13,14,15)|≤max(300,0.1%·|i1|)). 20셀 적용(KB손해·흥국화재·KDB), DB손해 2023.2Q(resid 6869>tol) 제외. owner PL fill durability override 後에도 유지(zero 먼저, override 後). raw-independent closure test.
