---
from: owner
to: parser
created: 20260620T0238Z
status: open
route: parse
company: MULTI
period: 2023.4Q~2026.1Q
lane: ifrs17
iter: 1
---

## 미결 (owner) — DART "증권의 발행을 통한 자금조달에 관한 사항"에서 자본성증권 발행 잔액 추출 → 자본 소진율 도넛 분자 교체

**근본원인 (2026-06-20 해설서 직접확인):** K-ICS.html "자본성증권 인정 한도 소진율" 도넛(tier1 신종 / tier2 후순위)의 **분자가 정의부터 틀렸다.**
- **tier2(보완자본) 분자**: `scripts/compute_tier2_utilization.py`가 회사 K-ICS MD에서 경과조치 명세표를 못 찾으면(동양·KB·미래에셋 등 proxy 4사) **item3(보완자본 총액)을 raw로 분자 사용**. 그런데 item3엔 **한도에서 제외되는 「다.(3) 해약환급금준비금 상당액 초과분」(조정준비금/미래이익)**이 포함됨(해설서 p102 마.: "보완자본은 총요구자본 50% 한도, 단 다.(3) 재분류액은 한도계산서 제외"). IFRS17사일수록 이게 커서 **전 회사 item3≫SCR×50%**, 소진율 >100%로 부풀음 = artifact. (table 파싱사도 일부 분자 붕괴: 삼성화재 1.8%·메리츠 0.3%, flag `table_proxy_diverge`.)
- **tier1(기본자본 신종) 분자**: excess 추출 누락 artifact 상존(메모리 `reference_kics_capital_tiering`).

**owner 결정:** **분모는 유지**(tier2=SCR×50%, tier1=SCR×10~15%), **분자를 DART 발행 잔액으로 교체.** owner가 사별 DART에서 **"증권의 발행을 통한 자금조달에 관한 사항"** 항목에 신종자본증권·후순위채 발행현황이 나오는 것 확인함.

**요청 (ifrs17 lane = DART 소스):**
1. 사별 × 분기 DART 정기보고서 **"증권의 발행을 통한 자금조달에 관한 사항"**(채무증권/지분증권 발행실적 등 하위표)에서 **신종자본증권 발행 잔액**과 **후순위채(권) 발행 잔액**을 추출.
2. 출력 JSON (예: `data/dart/capital_securities_issuance.json`): `{원보험사코드, 공시분기, 신종자본증권_잔액_억, 후순위채_잔액_억, provenance(접수번호·as-of일)}`.
3. **자본 계층 매핑(해설서 p7·p13 표 확정 — 헷갈리지 말 것):** 신종자본증권 → **기본자본(Tier1)** 분자 / 후순위채 → **보완자본(Tier2)** 분자. 신종은 Tier2 아님.
4. **잔액 = 발행 후 미상환 잔액**(상환·만기 도래분 차감). **as-of 주의**: 분기 기준일 이후 발행은 해당 분기 미반영 (예: KB손보 2026-04-08 발행은 2026.1Q[3/31] 데이터 아님).

**downstream (kics-side, owner/후속):** 이 JSON 들어오면 `compute_tier2_utilization.py` 및 tier1 분자를 item3-proxy/명세표 대신 이 발행잔액으로 교체 + 게이트 CHECK4 전제("proxy 소진율>100%=RED") 재검토. **데이터 들어오기 전까지 도넛은 designer가 잠정 숨김**(별도 발주 20260620T0238Z designer).

근거 메모리: `reference_tier2_utilization_provenance`, `reference_kics_capital_tiering`. 소스: 해설서 p102(마.보완자본한도)·p99~100(다.3 해약환급금초과분 한도제외)·p7/p13(자본증권 계층표). 송미정 수식(recognized 분자)은 틀린 게 아니라 다른 렌즈 — owner는 도넛에 발행/한도 렌즈 채택(tier1 도넛과 일관).

## 답변 (recipient 작성 — 처리 후)

✅ DONE 2026-06-20 (ifrs17 lane = DART 소스). 24사 DART 사업보고서 자금조달/사채발행내역/신종자본증권 세부정보/미상환잔액 주석에서 per-bond 추출(발행일·법만기·콜·금액·잔액·금리) → data/bonds/capital_securities_fy2025.json. 정식 포맷 **data/dart/capital_securities_issuance.json**: {원보험사코드,공시분기,신종자본증권_잔액_억(→Tier1),후순위채_잔액_억(→Tier2),provenance(접수번호·as_of 2025-12-31)}. 신종 15사·후순위 21사·무발행 9사(삼성화재·삼성생명·AIG·라이나·AIA·메트라이프·처브·카카오 등=정상). BS 신종자본증권과 대조일치(예 한화 30,819 vs BS 30,685=발행비용차). **+ 라이브 wire**: scripts/wire_capital_securities_to_utilization.py가 tier1/tier2_utilization 분자를 발행잔액으로 교체(경과조치 pre-2023 별도제외=owner 2026-06-20 결정) + 신한이지 분모 2.68→SCR×50%=268 교정 → data-contract gate RED 4→0 (동양240%/KB218%/미래126% proxy + 신한이지 denom 전부 해소). NB: as_of=2025.4Q(2026.1Q raw 5사만 디스크→2025.4Q+콜 reconcile); 타 분기 발행잔액·푸본 후순위 발행일(회차+신용평가 estimate)은 후속.
