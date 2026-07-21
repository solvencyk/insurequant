---
from: owner
to: publishing
created: 20260721T0233Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 미결 (sender 작성)

**배경:** 외부 스킬 목록(42종) 검토 중 `launch-runbook`(배포 절차 문서화)이 이 프로젝트에 실효가 있다고 판단 → 도입 발주. **publishing 프롬프트의 기존 TBD("rollback procedure", "site-deploy hook", "branch policy")를 채우는 작업이기도 함.**

**왜 필요한가:** 배포 경로가 비직관적이고 이미 한 번 사고가 났음(2026-06-20). 절차가 사람 기억과 흩어진 메모에만 있음.

**런북에 반드시 들어가야 할 사실관계 (기존 확정 사항 — 새로 정하지 말고 문서화):**
- **라이브 www.insurequant.com = `main` 배포.** 작업 브랜치에 push해도 **라이브 반영 안 됨** (2026-06-20 사고 원인).
- 작업 브랜치가 `main`보다 약 440만 줄 앞서 있음 → **통째 merge 금지.**
- 배포는 **격리 워크트리로 main에 cherry-push**. main 데이터는 이미 2026.1Q 최신이라 보통 **대시보드 HTML만** 올림.
- **owner 승인 필수.** publishing은 **`git push`를 직접 실행하지 않음** — 보고 + 권고까지가 스테이지 계약.
- **push 전 게이트 #0 = `validate_data_contract.py`.** RED이 1건이라도 있으면 push 금지. 우회·exception 처리로 넘기지 말고 fix(해당 스테이지 route)해서 0으로 만들 것.
- 공유 워킹트리 주의: 커밋 전 `git branch --show-current` + `git status` 확인, 남의 미커밋 변경 보이면 hold.
- 마스터 JSON 갱신 시 `insurequant_master_tables.xlsx` 재생성 필수. **단 마스터 xlsx를 openpyxl로 load+save 금지**(값열 수식 캐시 wipe) — xlsx 작업 기본은 공식 `xlsx` skill.
- 배포 에셋: `index.html` / `K-ICS.html` / `IFRS17.html` / `공시보고서.html` + 관련 JSON + `common.css`. HTML 파일은 publishing 소관 밖(designer 소유) — 손대면 `manual_html_edit` warn 후 정지.

**요청 (deliverable):**
1. 위를 **실행 가능한 체크리스트 런북**으로 정리 — "pre-flight 게이트 → 무엇을 어느 브랜치로 → 승인 지점 → 검증 → rollback". 각 단계에 실제 명령/스크립트 경로 명시.
2. **rollback 절차를 새로 작성** (현재 TBD). 최소: 잘못 올라간 HTML/JSON을 main에서 되돌리는 방법, 마스터 xlsx 손상 시 복구(.bak 복원 또는 Excel 재오픈), 되돌린 뒤 라이브 확인 방법.
3. 구현 형태는 위임 — 외부 스킬 설치 vs `skill-creator`로 로컬 스킬. **로컬 권장**(이 저장소는 로컬 스킬 패턴이 있음). 외부 채택 시 이유 명시.
4. 산출물: `docs/` + `docs/agents/claude-agent-publishing.md` 본문/링크. 이력은 `TODO_publishing.md` / `docs/changelog_publishing.md`.

**스코프 밖:** 이번 발주로 **실제 배포를 하지 말 것.** 문서화만. 배포는 별도 owner 승인 건.

## 답변 (publishing 2026-07-21)

**형태**: 로컬 스킬로 채택(권장안 그대로) — 외부 스킬 설치 안 함. 이유: 이 저장소엔 이미 로컬 스킬
패턴이 있고(`a11y-audit`·`incident-postmortem`·`kics-parser`·`ifrs17-parser`), 절차가 이 저장소의
git 상태(공유 워킹트리, main slim keep-list, K-ICS 전용 게이트가 `prepush_check.py`에 안 감싸이는 함정
등)에 강하게 결합돼 있어 범용 외부 런북 스킬로는 이 함정들을 못 담는다.

**산출물**:
- `docs/launch_runbook.md` (신규, 정본 절차서) — §1 pre-flight 게이트, §2 배포 경로 결정,
  §3 격리 워크트리 cherry-push, §4 승인 지점, §5 배포 후 검증, **§6 rollback(신규)**, §7 안전규칙,
  §8 실행 체크리스트.
- `.claude/skills/launch-runbook/SKILL.md` (신규 로컬 skill) — 트리거 조건 + 절차 요약, 상세는
  위 문서로 링크.
- `docs/agents/claude-agent-publishing.md` §8 TBD 3건(branch policy / site-deploy hook / rollback
  contract) 체크 완료 + 링크.

**Rollback 절차(요청 #2, 신규 작성)**: HTML/JSON은 격리 워크트리에서 `git revert`(force-push 금지,
히스토리 보존) → 재검증. 마스터 xlsx 손상은 `.bak` 복원 우선(최근 write 스크립트들이 `shutil.copy2`로
백업을 남김) → 없으면 Excel 재오픈(재계산으로 캐시 복구) → 둘 다 안 되면 `build_master_xlsx.py`
재실행이 최후 수단(수기 서식 손실 가능, owner 통지 필요). 상세 명령어는 `docs/launch_runbook.md` §6.

**스코프 확인**: 이 발주로 실제 배포/push는 실행하지 않음(문서화만, 지시대로).

status: resolved
