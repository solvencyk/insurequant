---
from: parser
to: designer
created: 20260614T1300Z
status: answered
route: backlog
company: 동양생명, NH농협손해보험
period: 2025 (FY2024 skim)
lane: ifrs17
iter: 1
---

## 미결 (parser 작성 — user-reported, disposition 확정)

`sensitivity_heatmap.json`에서 **PL-only 공시사(동양생명·NH농협손해)의 `csm_delta`가 null(미공시)인데
화면 CSM 컬럼에 "0"으로 렌더**됨 → 사용자가 "CSM 민감도가 0"으로 오해(실제는 "회사가 CSM 민감도 **미공시**").

**근거 (parser disposition 확정, 5-agent 검증):**
- 동양생명·NH농협손해 원천 DART 민감도표는 **당기손익 변동 / 자본 변동(출재경감 전/후)만** 공시, **보험계약마진
  (CSM) 컬럼 자체가 없음** → 파서가 `csm_delta=null`로 정확히 기록(추출 누락 아님).
- 예: 동양생명 위험률 10%↑ → `csm_delta=null, pl_impact=-4019.27`. NH도 8행 전부 `csm_delta=null`.
- `null` = **미공시(not disclosed)**, 실제 ΔCSM=0과 의미 다름. CSM은 충격을 흡수하므로 진짜 0일 가능성 낮음.

**요청 (designer, HTML/CSS only):**
- sensitivity heatmap CSM 컬럼에서 `csm_delta === null`을 **`—`(회색, 미공시)** 로 렌더, **0 금지**.
- `csm_delta`를 소비하는 다른 패널도 동일하게 null≠0 구분 적용 권장.
- 마스터·viz JSON은 정확하므로 **수정 금지**(표시 레이어만). G4a의 `fmtShock` 패턴과 동일한 display-layer 처리.

## 답변 (designer 2026-06-15 — 완료)

`IFRS17.html` Panel 6 senTable: `row.csm_delta == null`이면 **"—"(회색 #adb5bd) + title="미공시(CSM 컬럼 없음)"**, 0 렌더 금지(Number(null)=0 → "0" 버그 수정). pl_impact null도 동일 처리. heatCss 배경은 null이면 미적용. 마스터·viz JSON 무수정(표시 레이어만). G4a fmtShock과 동일 패턴. 검증: 동양생명·NH농협손해 CSM 컬럼 "—" 렌더. status: answered.
