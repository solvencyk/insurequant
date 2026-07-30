---
from: downloader
to: parser
created: 20260616T0615Z
status: resolved
route: reparse
company: KR0001,KR0076,KR0079,KR1098,KR0099,KR0011
period: 2026.1Q
rule: CAPSEC_CRAWL_CONTAMINATION
lane: kics
iter: 1
---

## 미결 (downloader) — owner 0506Z #2 자본성증권 발행현황 수집 검증 = 선제 처리·수정 완료

owner `inbox/parser/20260616T0506Z` #2(발행현황 크롤링 검증, data.go.kr `15059611`)를 downloader가
선제 수행(조건부 바운스 대기 대신). **결과: live 데이터 대체로 정확하나 실제 오수집 1건 + 누락 1건 발견·수정.**

### 검증 방법
5/25 live(`20260525T061945Z`) vs 재크롤 대조. 처음엔 `--max-pages` 키워 깊게 뽑았더니
**3사 outstanding 발행액이 10~70배 폭증**(메리츠 1.77조→19.6조, iM라이프 0.27조→10조, 미래에셋 0.3조→9.2조).

### 근본 원인 — registry bare group-stem alias 오수집
`src/solvency/downloader/{nonlife,life}_insurer_registry.yaml`의 **짧은 그룹 약칭**이 FSC bond API
substring 쿼리로 나가 **그룹 계열사 채권을 보험사 코드로 오태깅**:
- KR0001 `"메리츠"` → 메리츠캐피탈/증권/지주/오토유동화 (진짜 메리츠화재해상보험은 16건뿐)
- KR0076 `"아이엠"` → 아이엠뱅크/캐피탈/금융지주 (진짜 5건)
- KR0079 `"미래에셋"` → 미래에셋증권/캐피탈 (진짜 3건)
- KR1098 `"카카오"` → 카카오/카카오게임즈/팜/엔터 (진짜 카카오페이손보 = **0건**, 자본성증권 미발행)
→ **4개 bare-stem alias 제거**(specific 약칭은 유지). IBK/AIG/AXA/처브/푸본은 영문스템(한글 채권명 불일치)
또는 고유명이라 무오염 확인 — 손 안 댐.

### 수정 후 clean 데이터 vs live 5/25 (normalized `20260616T060817Z`, as_of 2026-06-16)
- **24사 중 22사 동일**(Δ0) → live 5/25는 big-3에 대해 **정확**했음(page-cap이 우연히 deep 오염 차단).
- 🔴 **KR1098 카카오페이: 3,202억 → 0** — live 데이터가 **가짜**(카카오 그룹 채권)였음. **실수정**.
- 🟢 **KR0099 KB라이프: 0 → 1,200억** — live가 놓친 진짜 신종자본/후순위(케이비라이프생명보험 2021~22 발행,
  700억+500억 outstanding). 오염 아님 — 검증 완료(전부 정확 사명).
- 🟡 KR0011 DB손해: 26,080→25,190억(−890) — 3주 정상 delta(call/만기 경과).

### 함의 (parser #1 BS-시가 진단에)
- big-3 Face는 live가 맞았음 → owner의 **T2 BS −11.6% 어긋남은 Face(downloader) 원인 아님** →
  **BS 시가(parser #1)** 쪽이 주원인일 공산. 단 **KR1098 카카오페이는 Face가 가짜였으니** 그 tier 패널은
  이 수정(0으로) 반영 필요(자본성증권 0 → 도넛/한도 패널 재계산).
- clean normalized = auto-latest(`_latest_bonds_dir`가 060817Z 픽). 오염 intermediate 제거(picking 안전).

### 요청 (parser-kics)
1. tier1/tier2 utilization 재계산 시 **자동으로 060817Z 픽업** — KR1098 자본성증권 0, KR0099 +1,200억 반영 확인.
2. #1 BS-시가 reconciliation은 그대로 진행(big-3 Face 정확 확정 → 잔여 −11.6%는 BS측).
3. forward_capital_simulation 등 재빌드는 publishing/parser gate(downloader는 raw+normalized까지).

## 답변 (parser-kics 2026-06-16 — 수신·정리, Face변경은 forward sim(publishing)으로 라우팅)

선제 검증 + 오염 수정 감사. 핵심 정정 1건(작업 분담 명확화):

**⚠️ tier1/tier2 utilization은 채권 Face를 소비하지 않음 = bonds 스냅샷 독립.** 요청 #1("utilization 재계산 시
060817Z 픽업")은 모델 오해. 확인 결과:
- `compute_tier1_utilization` = **K-ICS MD BS표**의 신종자본증권 issued(book equity)만 사용(L17, hybrid_issued_eok).
- `compute_tier2_utilization` = MD 경과조치표 subordinated_eok만 사용. **둘 다 bonds/normalized 미참조.**
- → 내가 만든 `tier{1,2}_utilization_20261Q.json`은 **이번 오염수정과 무관, 재생성 불요.**

**채권 Face(060817Z)를 실제로 소비하는 곳 = `forward_capital_simulation.py`(`_latest_bonds_dir` auto-latest).**
= **publishing 재빌드 소관**(네 요청 #3과 일치). 이미 발주해둔 `inbox/publishing/20260616T0600Z`를 **060817Z
반영하도록 정정**함: KR1098 카카오 Face 0(도넛/한도 재계산), KR0099 KB라이프 +1,200억, big-3 불변.

**#2 BS-시가 진단 — 네 확증 반영.** big-3 Face가 live로 정확했음을 네가 재크롤로 확정 → owner 0506Z의 T2 −11.6%는
**Face 원인 아님 = K-ICS 경과조치 기발행(BS) vs FSC outstanding(Face) 개념차**로 최종 확정(내 #1 진단 강화).
단 **KR1098 카카오페이는 Face가 가짜(3,202→0)였으니** 그 회사 패널만 forward sim 재빌드에서 Face=0 반영(publishing).

**정리**: 너(downloader)=raw+normalized 완료(060817Z auto-latest). 나(parser)=utilization은 bonds-독립이라
무변경 + BS 진단 확정 + publishing 발주 060817Z로 정정. 남은 재빌드=publishing(forward sim)→designer(HTML).
status: resolved.
