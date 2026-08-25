# Launch Runbook — insurequant 사이트 배포 절차 (정본)

> 작성: 2026-07-21 · publishing stage · 발주: `inbox/publishing/20260721T0233Z__owner__MULTI__adopt_launch_runbook.md`
> 이 문서는 **절차서**다 — 배경/설계 논의는 `docs/agents/claude-agent-publishing.md` §9(slim-publish)·§10(safe-git),
> 사고 경위는 `docs/postmortems/PM-2026-06-16_two_month_glitch.md` 참조.
>
> **이번 발주 스코프 = 문서화만. 이 문서 작성으로 실제 배포를 하지 않는다.**

## 0. 왜 이 문서가 필요한가 (사실관계 — 새로 정하지 않음)

- **라이브 www.insurequant.com = `main` 브랜치 배포.** 작업 브랜치에 push해도 라이브는 안 바뀐다
  (2026-06-20 사고 원인 — 작업 브랜치 push를 배포로 착각).
- 작업 브랜치가 `main`보다 수백만 줄 앞서 있다 (2026-07-21 기준 `fix/csm-product-segmented-columns`) →
  **통째 merge 금지.** main은 공개 저장소이며 site-assets-only(§9 keep-list)로 슬림하다; 작업 브랜치는
  IP(scripts/src/docs 등)를 포함한 전체 트리다.
- 배포는 **격리 워크트리로 main에 cherry-push**한다. main의 데이터는 보통 이미 최신 분기라, 통상
  **대시보드 HTML(+공용 데이터 JSON 일부)만** 올라간다.
- **owner 승인 필수.** publishing 스테이지는 로컬 git(add/commit/checkout/rm)은 스스로 실행하지만
  **`git push`는 실행하지 않는다** — 보고 + 권고까지가 계약(`claude-agent-publishing.md` 헤더).
- **push 전 게이트 #0 = `python scripts/validate_data_contract.py`(또는 이를 감싸는 `prepush_check.py`).**
  RED이 1건이라도 있으면 push 금지. exception 우회 불가 — RED은 해당 스테이지로 route해서 고쳐 0으로
  만든다 (`feedback_red_blocks_push` 원칙).
- **공유 워킹트리 주의.** 이 저장소는 여러 세션(파서/검증/퍼블리싱/디자이너)이 같은 폴더를 쓴다. 커밋 전
  `git branch --show-current` + `git status`로 남의 미커밋 변경이 있는지 반드시 확인 — 보이면 hold.
- 마스터 JSON을 갱신했으면 `insurequant_master_tables.xlsx` 재생성 필수(`xlsx` skill 사용). **마스터
  xlsx를 openpyxl로 load+save 하지 말 것** — 값 열의 수식 캐시가 전부 wipe된다.
- 배포 에셋(keep-list) = `index.html`/`K-ICS.html`/`IFRS17.html`/`공시보고서.html` + 관련 마스터 JSON +
  `common.css`. **HTML 파일은 publishing 소관 밖(designer 소유)** — publishing이 손대면
  `manual_html_edit` warn 후 정지, designer로 넘긴다.

---

## 1. Pre-flight 게이트 (push 전, 예외 없음)

```bash
python scripts/validate_data_contract.py
# 또는 K-ICS 룰게이트·도메인게이트 4종·inbox 위생·오프라인 테스트까지 묶은 상위 래퍼(권장, ~5분)
python scripts/prepush_check.py
```

- **exit/RED 판정**: `SUMMARY RED=0`이 아니면 **BLOCKED**. YELLOW는 통과(리뷰 큐, 비차단).
- RED이 있으면: 해당 RED의 route(kics parser / ifrs17 parser / downloader / validation)로 inbox
  발주 후 재실행. **documented exception으로 우회하지 않는다** — 진짜 추출 불가로 확정된 것만
  `TODO.md`/게이트 내 registry에 등재(owner 승인 필요, 서브에이전트 자체판단 금지).
- self-test로 게이트 자체의 회귀 확인(신규 룰 추가 후 필수):
  ```bash
  python scripts/validate_data_contract.py --selftest
  ```
- K-ICS 전용 게이트(`validate_kics_disclosure.py`)는 **2026-08-21부터 `prepush_check.py`가 감싼다**
  (단계 1b, exit code가 `blocked`에 들어간다). 그 전까지는 감싸지 않아 K-ICS 게이트에만 배선한 룰이
  push를 못 막았다 — 옛 문서에 그 서술이 남아 있으면 stale이다. 단 `validate_data_contract.py`를
  **단독으로** 돌릴 때는 여전히 K-ICS 룰이 안 돈다(래퍼를 써라).
- **일반 이상치 발견(`scan_generic_anomalies.py`)은 이 게이트 안에 없다**(2026-08-25 분리). push마다가
  아니라 **분기 라운드에 1회** 돌린다 — 시점·책임은 `claude-agent-publishing.md` §3.0b가 정본.

## 2. 무엇을 어디로 (배포 경로 결정)

| 상황 | 대상 | 절차 |
|---|---|---|
| HTML 구조/스타일 변경 없음, 마스터 JSON만 갱신 | keep-list 중 해당 JSON만 | §3 절차, HTML 스킵 |
| designer가 HTML을 바꿈(+거기 맞는 JSON) | 바뀐 HTML + 관련 JSON + `common.css`(HTML 바뀌면 항상 동반) | §3 절차 |
| 마스터 스키마에 새 필드 추가 | JSON만 먼저 배포 가능, HTML 렌더는 designer 후속 | publishing은 `manual_html_edit` 아님(스키마 추가는 자기 소관) — 단 HTML 렌더 필요하면 designer에 handoff 남기고 그 부분은 이번 배포에서 제외 |

**keep-list 정본** — 절대 기억으로 만들지 말 것, 매번 각 HTML의 `fetch(`/`dataPaths(`/`src=`/`href=`을
grep해서 파생. 최근 스냅샷은 `claude-agent-publishing.md` §9 참조(2026-06-16 확인 목록, 변동 시 그
문서를 갱신).

## 3. 격리 워크트리 cherry-push 절차

```bash
# 0) 작업 브랜치에서 in-progress 작업을 먼저 커밋으로 파킹 (stash 금지 — §7 참조)
git add <changed-files>            # git add -A 금지, 명시적 파일 목록
git commit -m "WIP checkpoint <이유>"

# 1) main용 격리 워크트리 생성 (작업 트리를 건드리지 않음)
git worktree add ../insurequant-main-deploy main

# 2) 그 워크트리에서 keep-list 파일만 최신 버전으로 교체
#    (작업 브랜치의 파일을 복사 — git checkout <feature-branch> -- <path> 방식도 가능)
cd ../insurequant-main-deploy
git checkout <feature-branch> -- index.html K-ICS.html common.css kics_disclosure.json ...

# 3) 검증: keep-list와 일치하는지 확인
git status   # keep-list 밖의 변경이 섞이지 않았는지 확인

# 4) 커밋
git commit -m "<期>: <one-line summary>"

# 5) GATE — 여기서 사용자 GO를 받는다 (아래 §4)
git push origin main

# 6) 라이브 확인 (§5)

# 7) 워크트리 정리, 작업 브랜치로 복귀
cd -
git worktree remove ../insurequant-main-deploy
```

메모: 예전(2026-06 초) 절차는 같은 폴더에서 `git checkout main`으로 브랜치를 바꿔치기했다 —
공유 워킹트리에서 다른 세션과 충돌 위험이 있어 **격리 워크트리 방식을 표준으로 채택**
(`claude-agent-publishing.md` §8b에서 지적된 문제의 해결책).

## 4. 승인 지점 (owner GO)

**push 직전, 정확히 무엇이 올라가는지 보여주고 승인을 받는다:**

- 브랜치: `main`
- 커밋될 파일 목록(전체, "등등" 금지)
- 각 파일이 바뀐 이유 1줄
- 게이트 결과: `RED=0` 확인 문구

승인 없이 `git push`를 실행하지 않는다. 로컬 add/commit/checkout/worktree 명령은 승인 없이 스스로
진행(계약상 "기계적 작업"). 사용자는 로그인(브라우저 인증)·push 승인·판단이 필요한 결정만 한다.

## 5. 배포 후 검증

```bash
# 마스터 JSON 하나 + HTML 하나를 raw curl/WebFetch로 확인 (200 + 내용 정상)
curl -sI https://www.insurequant.com/kics_disclosure.json | head -1
curl -s https://www.insurequant.com/K-ICS.html | grep -c "<html"
```

- GitHub Pages 재배포는 push 후 약 1~2분 걸린다 — 바로 404/구버전이 나와도 재시도.
- 화면에서 실제로 바뀐 값이 보이는지 눈으로 1곳 이상 확인(예: 새로 올라간 회사가 드롭다운에 있는지).
- Playwright/브라우저 프리뷰가 가능하면 콘솔 에러 0 확인.

## 6. Rollback 절차 (신규 — 이전 TBD)

### 6a. 잘못된 HTML/JSON이 main에 이미 push됨

```bash
# 안전한 워크트리에서 진행 (작업 브랜치를 건드리지 않음)
git worktree add ../insurequant-main-deploy main
cd ../insurequant-main-deploy

# 방법 A (권장) — 이미 push된 히스토리는 reset이 아니라 revert로 되돌린다
git log --oneline -5                 # 되돌릴 커밋 확인
git revert <bad-commit-sha>          # 새 커밋으로 되돌림, 히스토리 보존
git push origin main                 # ← 여기도 GO 필요 (§4와 동일하게 승인받고 실행)

# 방법 B — 특정 파일 한두 개만 이전 상태로 되돌릴 때
git checkout <last-good-commit> -- <path/to/file>
git commit -m "rollback: revert <file> to <last-good-commit>"
git push origin main                 # ← GO 필요
```

- **`git push --force`는 원칙적으로 쓰지 않는다.** main은 공개 배포 브랜치라 강제 푸시는 다른 클론/포크의
  히스토리와 어긋난다. revert(새 커밋으로 되돌림)가 항상 우선.
- 되돌린 뒤 **§5 검증을 다시 실행** — 특히 캐시(CDN/브라우저) 때문에 즉시 안 바뀐 것처럼 보일 수 있으니
  버전이 다른 필드 값으로 재확인.
- 워크트리 정리는 항상 마지막: `git worktree remove ../insurequant-main-deploy`.

### 6b. 마스터 xlsx(`insurequant_master_tables.xlsx`)가 손상됨

원인은 거의 항상 **openpyxl로 load+save**(값 열의 수식 캐시가 지워져 재오픈 시 0/공백으로 보임) —
공식 `xlsx` skill 대신 다른 경로로 손을 댔을 때 발생.

1. **`.bak` 파일이 있으면 그걸로 복원**: 최근 스크립트(`wire_capital_securities_to_utilization.py` 류)는
   덮어쓰기 전에 `shutil.copy2(f, f + ".bak")`으로 백업을 남긴다 — 대상 파일의 `.bak` 존재 여부 확인 후
   `.bak`을 원본 이름으로 복사.
2. **`.bak`이 없으면 Excel에서 직접 재오픈** — Excel이 열 때 수식을 재계산하므로 캐시가 복구된다. 그 후
   "다른 이름으로 저장" 대신 **같은 파일에 저장**(경로 유지).
3. 위 두 방법이 다 안 되면 `scripts/build_master_xlsx.py`를 **공식 `xlsx` skill 워크플로우 하에**
   재실행 — 소스 JSON에서 처음부터 재생성(값은 정적 export이므로 복구되지만, 시트에 있던 수기 서식/주석은
   사라질 수 있음 — 되돌리기 전 owner에게 알림).
4. 복구 후 mtime이 현재 마스터 JSON들보다 최신인지 확인(`ls -la insurequant_master_tables.xlsx
   CSM_waterfall.json PL_breakdown.json kics_disclosure.json`)해서 다시 stale해지지 않았는지 검증.

### 6c. 되돌린 뒤 공통 확인

- §5 라이브 검증 재실행.
- `TODO_publishing.md` + `docs/changelog_publishing.md`에 rollback 사유/커밋 sha 기록.
- 근본원인이 게이트 사각이었다면(예: RED=0인데 틀린 데이터가 나갔다) `incident-postmortem` skill로
  사고를 게이트 룰로 종결(단순 기록 금지 — "룰이 어디에 배선됐다"까지 확인).

---

## 7. 안전 규칙 요약 (전체는 `claude-agent-publishing.md` §10)

- `git stash`로 작업을 파킹하지 말 것 — WIP 커밋을 쓴다(§3 step 0).
- `git reset --hard`는 커밋/push 전 로컬 되돌림에만. **push된 뒤의 실수는 revert.**
- `git gc`/`git prune`/`git clean`은 복구 대기 중엔 절대 실행 금지 — 안전망을 지운다.
- 파일이 Excel에서 열려있거나 OneDrive 동기화 중이면 `git rm`/`checkout`이 막힌다 — 앱을 닫고 재시도.
- push가 진행 안 되고 멈춰 있으면 대부분 브라우저 로그인 팝업 대기 — 데이터 전송 문제가 아니다.

---

## 8. 실행 체크리스트 (요약)

```
[ ] 1. python scripts/validate_data_contract.py  → SUMMARY RED=0 확인
[ ] 2. (신규 게이트 룰 추가했다면) --selftest 통과 확인
[ ] 3. keep-list 재파생 (각 HTML grep) — 배포 대상 파일 확정
[ ] 4. 마스터 JSON 갱신 있었으면 insurequant_master_tables.xlsx 재생성 (xlsx skill, openpyxl 재저장 금지)
[ ] 5. git branch --show-current + git status  → 남의 미커밋 없는지 확인
[ ] 6. git worktree add ../insurequant-main-deploy main
[ ] 7. keep-list 파일만 워크트리에 반영, git status로 범위 재확인
[ ] 8. 커밋 (로컬, 승인 불필요)
[ ] 9. owner에게 "무엇이 올라가는지" 정확히 제시 → GO 확인
[ ] 10. git push origin main  (승인 후에만)
[ ] 11. 라이브 검증 (curl/WebFetch + 화면 1곳 눈으로 확인)
[ ] 12. git worktree remove, 작업 브랜치 복귀 + git status 클린 확인
[ ] 13. TODO_publishing.md + docs/changelog_publishing.md 갱신
```

문제가 생기면 → §6 Rollback.
