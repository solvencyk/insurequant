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

1. **Pre-flight 게이트**: `python scripts/validate_data_contract.py` → `SUMMARY RED=0` 확인. RED이면
   해당 스테이지 inbox로 route, 여기서 멈춘다. exception 우회 없음.
2. **keep-list 재파생**: 각 HTML의 `fetch(`/`src=`/`href=`를 grep해서 배포 대상 파일을 확정한다 —
   기억으로 판단하지 않는다.
3. **마스터 xlsx 최신화 확인**: JSON 마스터를 갱신했다면 `insurequant_master_tables.xlsx`를 재생성
   (공식 `xlsx` skill 경유, openpyxl load+save 금지).
4. **공유 워킹트리 확인**: `git branch --show-current` + `git status` — 다른 스테이지의 미커밋 변경이
   보이면 hold.
5. **격리 워크트리로 main에 cherry-push**: 같은 폴더에서 `git checkout main`으로 바꿔치기하지 않는다
   (다른 세션과 충돌 위험). `git worktree add` 사용.
6. **owner GO**: `git push origin main` 직전, 올라갈 파일 전체 목록 + 이유 + 게이트 결과를 제시하고
   명시적 승인을 받는다. 로컬 add/commit/checkout은 승인 없이 진행(계약상 "기계적 작업").
7. **배포 후 검증**: 라이브 URL 1개 이상 curl/WebFetch로 200 + 값 확인.
8. **문제 발생 시 rollback**: `docs/launch_runbook.md` §6 — HTML/JSON은 `git revert`(force-push 금지),
   마스터 xlsx는 `.bak` 복원 또는 Excel 재오픈(재생성은 최후 수단).

## 이 저장소 특유의 함정

- 작업 브랜치 push는 라이브에 반영되지 않는다 — main만 배포된다(2026-06-20 사고).
- `prepush_check.py`는 2026-08-21부터 K-ICS 전용 게이트(`validate_kics_disclosure.py`)를 **감싼다**
  (단계 1b). 단 `validate_data_contract.py`를 단독으로 돌리면 K-ICS 룰은 안 돈다 — 래퍼를 써라.
- 일반 이상치 발견(`scan_generic_anomalies.py`)은 2026-08-25에 게이트에서 분리됐다. push마다가 아니라
  **분기 라운드 1회** 돌린다(`claude-agent-publishing.md` §3.0b가 정본) — "게이트에 없으니 안 해도
  된다"로 읽지 말 것.
- HTML 파일은 이 스킬의 실행자(publishing) 소관 밖이다. 고쳐야 하면 `manual_html_edit`로 표시하고
  designer에게 넘긴다 — 대신 고치지 않는다.
