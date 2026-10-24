---
name: launch-runbook
description: insurequant 사이트(www.insurequant.com) 배포 절차 — pre-flight 게이트, main 격리 워크트리 cherry-push, owner 승인 지점, 배포 후 검증, rollback(HTML/JSON 되돌리기, 마스터 xlsx 손상 복구). Use when publishing a change to the live site, deciding what belongs on main vs the working branch, or recovering from a bad deploy / corrupted master xlsx. NOT for local dev-only changes that never reach main.
---

# Launch runbook (insurequant publishing stage)

정본: [`docs/launch_runbook.md`](../../../docs/launch_runbook.md) — 절차의 모든 단계, 명령어,
rollback 상세는 그 문서에 있다. 이 파일은 트리거 조건과 절차 순서만 요약한다.

## 언제 쓰나

- 라이브 사이트에 실제로 배포할 때 (HTML, 마스터 JSON, `common.css` 등 keep-list 파일).
- "이거 지금 main에 올려야 하나 작업 브랜치에만 둬야 하나" 판단이 필요할 때.
- 배포 후 문제가 발견돼 되돌려야 할 때 (잘못된 값이 라이브에 노출, 마스터 xlsx 깨짐).

## 절차 순서 (요약 — 명령어는 `docs/launch_runbook.md` §1-6)

1. **Pre-flight 게이트**: `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe scripts/prepush_check.py`(훅과 같은 게이트, 약 11분 — background로 끝까지) → RED=0·verdict 확인. RED이면
   해당 스테이지 inbox로 route, 여기서 멈춘다. exception 우회 없음.
2. **keep-list 재파생**: 각 HTML의 `fetch(`/`src=`/`href=`를 grep해서 배포 대상 파일을 확정한다 —
   기억으로 판단하지 않는다.
3. **마스터 xlsx 최신화 확인**: JSON 마스터를 갱신했다면 바뀐 시트만 `scripts/sync_master_xlsx_sheet.py`로 맞춘다
   (전체 재생성·openpyxl load+save 금지, CLAUDE.md §8).
4. **공유 워킹트리 확인**: `git branch --show-current` + `git status` — 다른 스테이지의 미커밋 변경이
   보이면 hold.
5. **격리 워크트리로 main에 cherry-push**: 같은 폴더에서 `git checkout main`으로 바꿔치기하지 않는다
   (다른 세션과 충돌 위험). 수동이면 `git worktree add`, 현행 경로(아래 6단계 `android_push_and_deploy.sh`)는 스크립트가 임시 워크트리로 같은 격리를 한다.
6. **owner GO**: `git push origin main` 직전, 올라갈 파일 전체 목록 + 이유 + 게이트 결과를 제시하고
   명시적 승인을 받는다. 로컬 add/commit/checkout은 승인 없이 진행(계약상 "기계적 작업").
   main 반영 실행 경로는 CLAUDE.md §11·`publishing.md`가 정본이다 — owner 구두 GO 뒤 오케스트레이터가 이 PC 에서 직접 `scripts/android_push_and_deploy.sh --from-origin --branch <작업브랜치>`를 돌리므로 작업 브랜치를 먼저 push해 둔다. git live push 가 막히면 직접 2번 시도하고, 그래도 안 되면 owner 에게 폰 Termux 명령과 배치파일을 제시한다(CLAUDE.md §11).
7. **배포 후 검증**: 라이브 URL 1개 이상 curl/WebFetch로 200 + 값 확인.
8. **문제 발생 시 rollback**: `docs/launch_runbook.md` §6 — HTML/JSON은 `git revert`(force-push 금지),
   마스터 xlsx는 `.bak` 복원 또는 Excel 재오픈(전체 재생성 금지, CLAUDE.md §8).

## 이 저장소 특유의 함정

- 작업 브랜치 push는 라이브에 반영되지 않는다 — main만 배포된다(2026-06-20 사고).
- `prepush_check.py`는 2026-08-21부터 K-ICS 전용 게이트(`validate_kics_disclosure.py`)를 **감싼다**
  (단계 1b). 단 `validate_data_contract.py`를 단독으로 돌리면 K-ICS 룰은 안 돈다 — 래퍼를 써라.
- 일반 이상치 발견(`scan_generic_anomalies.py`)은 2026-08-25에 게이트에서 분리됐다. push마다가 아니라
  **분기 라운드 1회** 돌린다(`claude-agent-publishing.md` §3.0b가 정본) — "게이트에 없으니 안 해도
  된다"로 읽지 말 것.
- HTML 파일은 이 스킬의 실행자(publishing) 소관 밖이다. 고쳐야 하면 `manual_html_edit`로 표시하고
  designer에게 넘긴다 — 대신 고치지 않는다.
