---
from: orchestrator
to: validation
created: 20261011T2300Z
status: open
route: register
company: KR1101-KR1107,MyBrown
period: 2023.1Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
**owner 승인 기록(채팅, 2026-10-11 밤).** 오케스트레이터가 owner 에게 질문했다: 「보험손익 원표 패널(DART 표 기반)에 새 재보사 7곳과 마이브라운 8곳이 구조상 들어갈 수 없어 생기는 검사 실패인데, 기존 7개사(AIG, 교보플래닛 등)와 같은 방식으로 면제 8줄을 등재할까요?」 — owner 가 선택지 **「8줄 등재 (권장)」** 를 골랐다(다른 선택지: 「검사 대상을 좁힘」·「등재하지 않음」은 선택되지 않음). 이 답은 owner 가 직접 입력한 것이다.

### 해 줄 것
`data/_derived/pre_push_final_20261011/pre_push_final_proposed_baseline_inspl_20261011.json` 의 `_how_to_apply` 그대로 8줄을 `data/_gold/live_artifact_baseline.json` 에 등재한다(entries 추가, `_counts['insurance_pl_breakdown.json|INSPL_CENSUS_MISSING']` 7→15, entries 18→26, detail·first_seen=2026-10-11). **게이트 코드는 좁히지 않는다**(owner 가 「등재」를 골랐다). 이어서 `scripts/validate_live_artifacts.py` 재실행(기대: RED 0, YELLOW(baselined) 25, STALE_BASELINE 0), 베이스라인 파일을 읽는 테스트·`tests/test_push_gate_wiring.py`·`tests/test_rule_coverage_manifest.py` 통과 확인, 등재 목록이 적힌 문서(기존 7줄과 같은 자리)·`TODO_validation.md` Status·`docs/changelog_validation.md` 갱신.

### 규칙
- 이 8줄 외 신규 등재 금지. 마스터 JSON 수정 금지. 커밋은 자기 파일만(명시 경로, `qoq_warn.json` 제외), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. push 금지(오케스트레이터 몫). 파이썬은 풀패스·스크립트 파일만. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 커밋 해시, `validate_live_artifacts` 전후, 테스트 결과, 「훅이 이제 통과하는가」 한 줄 결론(28분 풀 훅 사전 실행에서 이 항목 외에는 모두 clear 였으므로 전체 재실행은 불필요).

## 답변 (recipient 작성 — 처리 후)
