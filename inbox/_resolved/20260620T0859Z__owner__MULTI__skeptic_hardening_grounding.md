---
from: owner
to: publishing
created: 20260620T0859Z
status: resolved
route: prompt_hardening
company: MULTI
period: "-"
iter: 1
---

## 미결 (owner) — LLM-skeptic(§3) 하드닝: 마스터 grounding + fabricate 금지 + owner-registry 존중

2026-06-20 skeptic이 owner-확정 셀을 반복 오플래그하고(코리안리·삼성화재 자동차·신한이지), 심지어 **입력에 없는 형제항목(코리안리 기타생명장기재보험손익=43)을 지어내** "dup"이라 판정함(실제 −11817). 마스터는 정확했음. publishing prompt §3(LLM-skeptic)에 아래 규칙 **명문화**:

1. **입력 한정**: skeptic은 `data/_derived/anomaly_skeptic_input.json`(triage가 suppress 적용한 큐)만 검토. 마스터에서 raw로 후보를 재유도하거나 **입력에 없는 셀/항목을 생성(fabricate) 금지**.
2. **마스터 grounding 필수**: EXTRACTION_ERROR 판정 전, 해당 셀의 **실값을 마스터(`PL_breakdown.json`/`CSM_waterfall.json`, 원수사명+공시분기+항목명)에서 직접 확인** + 자기-이력(own history) 대조. "두 항목 값이 같다=dup"는 **두 값을 실제로 읽어 동일함을 확인한 뒤에만**.
3. **owner-confirmed 존중**: `data/_gold/user_pl_confirmed_cells.json` 매칭 셀은 triage가 이미 `OWNER_CONFIRMED`로 suppress → skeptic 입력에 안 옴. 혹 보이면 = 레지스트리 미등록이니 **데이터 수정 말고 등록 권고**.
4. **LLM 역할 축소**: 결정론적 own-history triage(REAL/NOISE)가 정밀도 대부분 담당. skeptic은 **UNCERTAIN 잔여만** 판단(REAL을 재심하지 말 것 — 이중 노이즈).

검증: 위 규칙 반영 후 `prepush_check.py` 재실행 시 owner-confirmed 5셀이 skeptic에 안 뜨는지 확인(현재 통과). 근거 메모리: `project_owner_confirmed_registry`.

## 답변 (recipient 작성 — 처리 후)

처리 완료(구체 시점 불명 — 이전 세션이 이미 반영, 이번 세션에서 확인 후 정식 close). `docs/agents/claude-agent-publishing.md` §3 LLM-skeptic 절에 "Hardening rules (owner 2026-06-20, ...)" 블록으로 4개 규칙 전부 명문화돼 있음을 확인:

1. 입력 한정(UNCERTAIN만, fabricate 금지, 코리안리 사례 명시) — 반영됨.
2. 마스터 grounding 필수(EXTRACTION_ERROR 전 실값 대조) — 반영됨.
3. owner-confirmed 존중(`user_pl_confirmed_cells.json` 매칭 시 데이터 수정 대신 등록 권고) — 반영됨.
4. LLM 역할 축소(UNCERTAIN 잔여만 판단) — 반영됨.

검증: `docs/agents/claude-agent-publishing.md` §0 "Current live" 라인에 이번 세션 재실행한 `prepush_check.py` 앤_스켑틱 트리아지 수치 병기(REAL=73 UNCERTAIN=6 NOISE=133) — owner-confirmed 셀이 skeptic 입력에 재등장하지 않음. `_resolved/`로 이동.
