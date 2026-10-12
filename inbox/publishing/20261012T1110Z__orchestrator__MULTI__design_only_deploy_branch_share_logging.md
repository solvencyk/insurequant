---
from: orchestrator
to: publishing
created: 20261012T1110Z
status: open
route: feature
company: MULTI
period: MULTI
iter: 1
---

## 미결 (sender 작성)
owner 가 공유 버튼 기록(시트 `shares`)을 시험했는데 라이브(`main`)의 `theme.js` 에 기록 코드가 없어 기록되지 않았다(라이브 `theme.js` 에 `shLog` 0건 확인). 작업 브랜치 전체 push 는 다른 에이전트 작업(validation·parser)이 끝나야 하므로, **지난번처럼 데이터 없는 「디자인만」 배포 브랜치**를 만들어 owner 가 폰에서 먼저 배포할 수 있게 한다.

### 해 줄 것
1. **격리 워크트리**(공유 워킹트리의 브랜치를 바꾸지 말 것 — `git worktree add`)에서 `origin/main` 기준으로 새 브랜치 `deploy/design-20261012` 를 만든다. 담을 파일은 **딱 3개**: `theme.js`, `privacy.html`, `compare.html` 을 작업 브랜치 HEAD 의 내용으로(커밋 `b3a2ae2`·`18bd037` 의 결과). 다른 파일·마스터·데이터·`public_exports/` 는 담지 않는다. (오케스트레이터 확인: 라이브 `theme.js`·`privacy.html`·`compare.html` 과 작업 브랜치 HEAD 의 차이는 공유 버튼 기록 + 모바일 섹션 공유 이미지 폭 수정뿐이다 — 너도 `git diff origin/main HEAD -- theme.js privacy.html compare.html` 로 재확인하고, 이 둘 외의 차이가 있으면 담지 말고 보고.)
2. 지난 디자인 배포(`origin/deploy/design-20261011`, 커밋 `6e8763b`/`59f7e0c`/`adeef08`)의 방식·커밋 메시지 형식을 따른다. 라이브 사이트가 이 3파일만으로 정상인지 확인: `forms-config.js` 가 라이브에 있는지(없으면 보고), CSP `connect-src`, `scripts/compute_sri.py`/`tests/test_deploy_assets.py` 의 keep-list·SRI 대조(작업 트리에서), `tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py`·`tests/test_prepush_scope.py`·`tests/test_share_screenshot.py` 를 **한 번에 하나씩 끝까지**.
3. 로컬 파일 서빙으로 `?iq_internal=1` 없이 공유 버튼을 눌렀을 때 요청 본문이 가로채기(fetch 스텁)로만 확인되는지 — **실제 구글로 보내지 않는다**. 이미 designer 가 한 점검이라 재현은 가볍게.
4. **push 는 하지 않는다**(오케스트레이터가 한다). 끝나면 브랜치 이름·HEAD 해시·담긴 파일 목록·`git diff --stat origin/main..deploy/design-20261012` 를 보고. 워크트리는 정리.

### 규칙
- 이 브랜치에 푸시·마스터 변경 금지. 다른 작업 트리의 미커밋 파일 건드리지 말 것. 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만. 서브에이전트 금지. 이 공유 티켓은 고치지 않는다.

### 보고 (3~5줄 존댓말)
- 브랜치·해시·파일 3개·테스트 결과·owner 폰 배포 한 줄 명령(`cd ~/insurequant && git fetch origin && git checkout -B deploy/design-20261012 origin/deploy/design-20261012 && bash scripts/android_push_and_deploy.sh --from-origin --branch deploy/design-20261012`).

## 답변 (recipient 작성 — 처리 후)
