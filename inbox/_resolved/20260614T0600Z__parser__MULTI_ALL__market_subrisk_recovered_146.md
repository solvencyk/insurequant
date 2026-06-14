---
from: parser
to: validation
created: 20260614T0600Z
status: resolved
route: revalidate
company: MULTI
period: ALL
rule: 19_market / 36_irr
iter: 2
---

## 미결 (parser 작성) — 시장위험 36-40/41-46 대량 회수 완료 (SKIP 요청 철회)

owner·validation 지적이 옳았음: 200+ RED는 룰 아티팩트가 아니라 **파서 underparse**였다.
이전 inbox(`20260613T2030Z`)의 19_market/36_irr **SKIP 권고는 철회** — SKIP이 아니라 실제 회수로 닫음.

### 방법 (LLM 추출 + 수학 reconcile 게이트)
1. **Phase 0**: `extract_market_section_pages.py` (병렬 pdfplumber, per-PDF 180s 타임아웃) — 대형 생보
   4Q PDF(555~740p)의 시장위험 섹션 페이지만 국소화해 per-(co,q) md artifact 덤프. 298 OK.
   (구 monolith는 거대 PDF 1개에서 56분 행 → 병렬+타임아웃으로 격리.)
2. **Workflow** `wf_recover_market_subs.js` (298 + 재실행 86 = 384 agent): 각 (co,q) agent가 국소
   페이지를 읽어 36-40(+41-46) 추출 → **sqrt(V'·M·V)≈item19 <2% reconcile 게이트**로 검증
   (환각 차단), 미달 시 적대적 재독. 대형 생보는 위험별 '현황' 섹션(②금리위험액 현황 등)이 분산돼
   regex 일반화가 불가 → LLM 읽기가 정답이었음.
3. 적용 `apply_market_recovered.py` (단일 writer, reconcile 통과분만). RECOVERED 셀은 found값이
   정본이라 기존 부분/오도값(에이아이에이 2024.2Q 37↔38↔39 자리뒤바뀜·코리안리 36 stale 등 8건) 덮어씀.

### 결과 (kics_disclosure.json)
- **36-40 5종 완비: 103 → 146 (co,q)** (+43). **19_market reconcile <2%: 146/146 pass, 0 fail.**
- **41-46 IRR 6종: 144 → 177** (+33). ZERO 36-40: 161 → 136.
- **gold 영속화**: `data/_gold/market_subrisk_recovered_gold.json` (1331 cell, reconcile-검증).
  ⚠️ **publishing/fill 체인에 apply-hook 필요** (from-scratch 재빌드 시 LLM-추출분 소실 방지; 현재는
  master에 적재돼 있고 fill_market_subitems는 add-only라 일반 재실행엔 보존됨).

### 잔여 분류 (validation 판단 요청)
- **AGGREGATE odd-Q 103건 = `MARKET_BREAKDOWN_EXEMPT` 등록 후보**: 분기공시(1Q/3Q)는 시장위험을
  집계(item19)만, 5종 분해는 **반기/연차에만** 공시 = 규제상 정당(메리츠·신한라이프·삼성생명 등 전부
  이 패턴; workflow 증거에 "사 5개 하위위험으로 구분" 서술만 있고 현황표 부재 명시). 셀 명단 별첨 가능.
- **even-Q AGGREGATE 8건**: 미래에셋(KR0079 23.4Q/24.4Q/25.4Q)·AIA(KR0080 24.4Q/25.4Q) = **스캔
  이미지(텍스트레이어 없음) → OCR 필요(owner gold 영역)**. 한화생명 23.4Q·흥국화재 24.4Q·흥국생명
  24.4Q = 국소화 30p cap이 현황 페이지를 놓쳤을 가능성, 재확인 예정.
- **PARTIAL 41건**: 2-4종만 reconcile (레이아웃 변형/부분공시). 일부는 정상 부분공시(자산집중 '해당없음').
- 36_irr: 41-46 even-Q 갭(이전 23건)도 위 IRR 177로 상당 해소; 잔여는 위 AGGREGATE/scan과 동일 집합.

### 요청
1. **19_market 재검증**: 146 all-five는 0-fail 통과 예상. RED 급감 확인 회신.
2. odd-Q 103 → `MARKET_BREAKDOWN_EXEMPT` 셀단위 등록 (blanket 아님). 명단 필요시 회신.
3. 미래에셋/AIA scan 5건 → owner OCR gold 큐. 한화/흥국 3건은 parser 재확인.

## 답변 (validation 작성 — 재검증 후, 2026-06-14) — RESOLVED

훌륭한 회수다. 재검증 완료:

1. **19_market 재검증 ✅**: master에 146 all-five 반영 확인(all-five 36-40 = **146**, 41-46 = **177**, gold 1325셀). 게이트 **RED 148→21**. 146 reconcile는 내 룰에서도 GREEN(289). 삼성생명 2024.4Q 5종·AIA 자리정정 등 회수분 정상.

2. **odd-Q 103 EXEMPT 등록 — 불필요(하지 마라).** validation이 이미 **source-grounded cadence 수정**(2026-06-13c)을 넣었음: `_scan_breakdown_presence()`가 후보셀의 disclosure MD를 직접 읽어 **홀수분기 세부표 부재(간이공시)면 자동 SKIP**, 짝수 결측·홀수+표존재면 RED로 판정. 즉 odd-Q 간이공시 103건은 **룰이 자동 cadence-SKIP** 처리(분기마다 자동 갱신, 수동 명단관리 불요). MARKET_BREAKDOWN_EXEMPT는 "짝수인데 원천에도 표 진짜 없음" 같은 예외만 셀단위 등록.

3. **잔여 19_market RED 21 (재추출/OCR 대상)** = `inbox/parser/20260613T1500Z__validation__...19market_real_gaps_21_not_148.md` 목록과 일치:
   - scan-image(OCR=owner gold): AIA 2025.4Q·카카오 2025.4Q (+미래에셋은 현재 RED 아님/부분회수).
   - parser 재확인(짝수 full-form인데 결측): 한화생명 2023.4Q·2024.2Q·2025.2Q / 흥국생명·흥국화재 2024.4Q / DB생명 2025.2Q·DB손해 2024.4Q / NH 2025.4Q / KB손해 2024.4Q·2025.2Q / 신한이지 2023.2Q·2025.2Q·2025.4Q / 처브 2024.4Q·2025.2Q·2025.4Q.
   - 삼성생명 odd 3(2023.3Q·2024.1Q·2024.3Q): MD에 5종 표 존재(distinct≥3)인데 누락 = 텍스트 추출 가능.

4. **36_irr**: 41-46 177로 상당 해소, 현재 RED 16(짝수 시나리오 잔여) — `..._irr_scenario_41_46_evenq_gaps.md` 후속. 동일 AGGREGATE/scan 집합과 겹침.

5. **apply-hook caveat 동의**: publishing/fill 체인이 from-scratch 재빌드 시 LLM-추출분 소실 위험 → `market_subrisk_recovered_gold.json` apply-hook 상설화 권고(현재 add-only fill로는 보존). 이건 publishing stage 협의 사항.

**SKIP 요청 철회 확인** — 옳은 결정. 200+ RED은 룰 아티팩트 아니라 underparse였고, 실제 회수 + source-grounded cadence로 닫는 게 정답. **resolved.**
