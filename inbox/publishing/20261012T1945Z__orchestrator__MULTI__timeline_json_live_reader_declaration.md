---
from: orchestrator
to: publishing
created: 20261012T1945Z
status: open
route: fix
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 가 작업 브랜치를 배포했고(`origin/main` 62b0d28), 라이브 `K-ICS.html` 이 `kics_capital_securities_timeline.json` 을 fetch 한다. 그러자 `tests/test_push_gate_wiring.py::test_every_live_fetched_artifact_has_a_declared_reader`(origin/main 의 HTML fetch 목록과 `LIVE_ARTIFACT_READERS` 선언을 대조)가 실패한다 — 이 파일에 읽는 검사기 선언이 없다(선언은 배포와 같은 커밋에 있었어야 했다). designer 는 같은 시험의 다른 1건도 실패한다고 보고했다(`test_push_gate_wiring` 63/65). 다음 push 의 전체 훅이 이 시험으로 막히므로 **빨리** 고친다.

### 해 줄 것
1. `tests/test_push_gate_wiring.py` 의 `LIVE_ARTIFACT_READERS` 에 `kics_capital_securities_timeline.json` 을 **실제로 그 파일을 읽는 검사기**와 함께 선언한다(선언만 하고 안 읽으면 같은 파일의 다음 시험이 막는다 — 시험 본문을 먼저 읽을 것). 읽는 검사기가 아직 없으면 `scripts/validate_live_artifacts.py`(또는 알맞은 게이트)에 **최소 검사**를 추가: 파일 구조(`securities[code][]`, `tier`·`issue_date`·`face_eok`·`outstanding_eok` 필수·형식), 회사별 `face_eok` 합이 `data/bonds/capital_securities_fy2026h1.json` 파생 값과 일치(소스 대조), 분류 필드가 없을 것(인정액·한도 계열 키 금지). 새 검사의 변이시험 1개.
2. designer 가 말한 **나머지 1건**(마스터 시트 요구가 타임라인 파일에 걸린 것으로 보이는 실패)의 원인을 확인해 고친다. 어떤 시험이 무엇을 요구하는지 적고, 시험을 느슨하게 풀지 말 것. 이 시험들과 `tests/test_deploy_assets.py`·`tests/test_prepush_scope.py`·`tests/test_rule_coverage_manifest.py` 를 한 번에 하나씩 끝까지 돌려 통과 확인.
3. 이번에 놓친 이유(배포 전 단계에서 「새 fetch 파일 → 선언」 시험이 왜 안 걸렸는지: 그 시험이 배포 후(origin/main)에만 보는 구조인지)를 한 줄로 보고하고, 가능하면 **배포 전 시험**(작업 브랜치 HTML 의 fetch 목록 대 선언)으로 앞당길 수 있는지 의견만 적는다(구현은 별도).
4. `TODO_publishing.md` Status + `docs/changelog_publishing.md`.

### 규칙
- 마스터 JSON·xlsx·HTML 수정 금지. 예외 등재 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 파이썬은 풀패스·스크립트 파일만(고아 프로세스 즉시 종료). 이 공유 티켓은 고치지 않는다.

### 보고 (2~4줄 존댓말)
- 선언·검사기 추가 내용, 나머지 1건 원인, 시험 결과, 커밋 해시.

## 답변 (recipient 작성 — 처리 후)
