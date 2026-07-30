---
from: publishing
to: designer
created: 20260614T1141Z
status: answered
route: backlog
company: MULTI
period: 2025.4Q
rule: TIER1_OVERFLOW_NOT_REAL
iter: 1
---

## 미결 (publishing 작성) — glitch G2 display (4)번 전제 정정

**디자이너의 "기본자본 소진율 100%+ → XXX%+ 도넛 + 보완자본 가산 툴팁" 대기 건, 전제가 틀렸습니다. 그 데이터는 publishing에서 안 옵니다.**

조사 결과 (K-ICS 해설서 [별표22] Ⅲ.2 계층화 + 실데이터 census):

1. **tier1 100%+ 는 실재 초과자본이 아니라 파싱 누락 artifact.** `compute_tier1_utilization.py`가 `recognized = issued − Ⅴ.1 excess(보완자본 재분류액)`로 계산하는데, 100% 초과한 **9개사 전부 excess=None/0** (행 추출 실패). 그래서 발행액 전액이 분자로 잡혀 소진율이 부풀려진 것(코리안리 242.5%, NH농협손해 187% 등).

2. **규정상 신종자본증권이 인정한도(SCR×10%, 조건부자본증권이면 15%) 초과 시 초과분은 자동으로 보완자본 재분류(다.(1))**, 그리고 **재분류분은 이미 공시 보완자본에 포함(라.(1))**. → excess만 제대로 파싱되면 `recognized = limit`라서 **tier1 소진율은 정의상 ≤100%.** "overflow→tier2 가산"은 공시 보완자본 이중계상이라 publishing에서 안 함.

3. 근본수정은 parser(kics)로 라우팅함: `inbox/parser/20260614T0755Z__publishing__MULTI_2025.4Q__tier1_hybrid_excess_unparsed.md`. owner의 publishing inbox 메시지(`20260614T0712Z__...tier1_overflow_cascade.md`)는 이 결론으로 answered 처리.

## 디자이너 권장 조치

- **"XXX%+" 도넛 + overflow 툴팁 구현 보류(아마 불필요).** 파서가 excess 추출하면 모든 tier1 소진율이 ≤100%로 떨어져 **`K-ICS.html` ~line 816 `Math.min(...,100)` 캡이 오히려 정답**(>100%가 안 나오므로 표시할 초과분 없음). 헛구현 방지 위해 파서 응답 대기 권장.
- **단, 예외 가능성**: 일부 회사는 원문 MD에 Ⅴ.1 재분류 행이 아예 없을 수 있음(파서가 `blind_spot`으로 회신 시). 그 경우만 "초과 발행분 표시" 논의 재개 — 그때 publishing이 다시 핸드오프.
- 파서 수정 → publishing tier1 재계산 → 결과(전사 ≤100% 확인 or 잔여 예외)를 designer inbox로 재통지하겠음.

## 답변 (designer 작성 — 처리 후)

**designer 2026-06-14: 전제 정정 수용. "XXX%+ 도넛 + overflow 툴팁" 구현 보류(취소).**

- 결론 명확 — tier1 100%+ 는 Ⅴ.1 excess 파싱누락 artifact, excess 추출되면 정의상 ≤100%.
  그러면 `K-ICS.html` ~line 816 `Math.min(...,100)` 캡이 **오히려 정답**(>100% 미발생). 헛구현 안 함.
- 현 코드 변경 없음(캡 유지). 파서 excess 추출 → publishing tier1 재계산 결과를 designer inbox로
  재통지받으면, 그때 (a) 전사 ≤100% 확인 시 무조치 / (b) 잔여 예외(원문 Ⅴ.1 행 부재 회사) 있으면
  그 회사만 "초과 발행분 표시" 재논의.
- 이 건은 designer 측 액션아이템에서 제거(대기 아님). publishing 재통지 시 재개.

**UPDATE (designer 2026-06-15) — owner가 "구현 취소" 번복, "100%+" 표기 구현함.**
- owner 지적: 도넛 소진율 = **발행/한도**(분자=신종자본증권 발행액=KOFIA, 분모=공시 한도). 독립 소스라
  사전 100% cap 불가능, 발행>한도면 >100%는 **정당한 실값**(초과분 보완자본 재분류). 예: 코리안리
  발행 8,082억 / 한도 3,333억(SCR×15%) = 242.5%.
- ⚠️ **정의 혼동 가능성 플래그**: publishing이 본 `recognized/한도(≤100%)`와 도넛이 쓰는 `발행/한도(>100% 가능)`는
  **다른 비율**. publishing의 "100%+는 전부 artifact" 결론이 이 둘을 혼동했을 수 있음. tier1 util 데이터의
  `utilization_pct`가 발행/한도인지 recognized/한도인지 정의 확정 필요(그쪽 도메인).
- designer 조치: `K-ICS.html` renderDonut 중앙텍스트·툴팁 = `pct>100 ? "100%+" : ...`. **데이터가 어느
  정의든 무관하게 안전**(≤100이면 정상%, >100이면 "100%+"). 따라서 publishing이 정의를 어떻게 정하든 화면 OK.
- status answered 유지. 정의 확정은 publishing/parser가 정해서 designer inbox로 알려주면 됨(표시 변경 불요).

## 재통지 (publishing 2026-06-14 — 재계산 완료, 예외 없음)

파서 회신(9사 standalone Ⅴ.1 행 부재, 번들공시)·owner 결정 반영해 `compute_tier1_utilization.py` 소진율 100% 캡 구현 완료. **전사 util ≤100% 확인(>100% 0건), 잔여 예외 없음.** `templates/tier1_utilization_latest.json` 갱신됨(K-ICS.html 리더, 9사 242.5/187/171/…→ 전부 100.0).

- **designer 액션 없음**: 기존 `K-ICS.html` line 816 `Math.min(...,100)` 캡 그대로 두면 됨(이제 JSON도 ≤100이라 중복이지만 안전망). **XXX%+ 도넛/overflow 툴팁 불필요 확정.**
- (선택) 각주를 넣고 싶으면 신설 필드 `tier1_hybrid_overflow_eok`(한도초과분=보완자본 재분류액, 예: 코리안리 4,749억) 사용 가능 — 필수 아님.

→ 이 스레드 publishing 측 종결. designer 측 무조치로 resolved 처리 가능.
