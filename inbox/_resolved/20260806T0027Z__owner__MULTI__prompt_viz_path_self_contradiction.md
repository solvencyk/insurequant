---
from: owner
to: publishing
created: 20260806T0027Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 미결 (sender 작성)

`docs/agents/claude-agent-publishing.md`가 **viz 경로 cutover 여부를 놓고 자기모순**이다. 2026-08-06 규칙문서 감사(리팩토링 6차, `docs/claude-changelog.md`)에서 발견. 데이터 문제가 아니라 **프롬프트 문제** — 이 프롬프트를 읽고 일하는 publishing 세션이 stale 쪽을 따라갈 수 있다.

**모순 지점 (같은 파일 안):**

- **§1 L107 (Path note)** — "the table lists the post-migration canonical (`data/dart/viz/*`). Live `main` **still reads** `data/ifrs17/viz/*` — see §9 'Pending path migration' for detail and the cutover trigger (when `fix/csm-*` lands on `main`)."
- **§9 L266** — "Path migration **LANDED (2026-06-16)**. Live `main` now serves viz from `data/dart/viz/*` (matches §1 canonical); the old `data/ifrs17/viz/*` note is **retired**."

§9가 "그 노트는 폐기됐다"고 명시하는데 **정작 그 노트(§1 L107)가 안 지워졌다.** §1이 문서 앞쪽이라 먼저 읽히므로, 실제로는 종결된 cutover를 "미결"로 오인하게 된다.

**추가로 확인할 것:** §9 L273의 delete-list 예시가 아직 `data/ifrs17/viz`를 "일부 유지·일부 삭제" 디렉터리로 들고 있다. migration이 landed면 이 예시도 현행인지 재확인 필요(슬림 publish 시 잘못된 파일을 남기거나 지울 위험).

**요청:**

1. 실제 라이브 `main`이 어느 경로에서 viz를 읽는지 **git으로 확인**(기억·문서 아님) — `git show main:K-ICS.html`·`main:IFRS17.html`에서 fetch 경로 grep.
2. 확인 결과에 맞춰 **§1 L107과 §9 L266 중 틀린 쪽을 제거**해 한쪽만 남길 것. §9가 맞다면 §1 Path note를 삭제(§9 안내 문구도 "retired" 표현 정리).
3. §9 L273 delete-list 예시의 `data/ifrs17/viz` 언급이 현행인지 같이 판정.

**참고 — 이건 개별 수정이 아니라 패턴이다.** 같은 감사에서 `CLAUDE.md`도 designer/publishing 프롬프트를 "skeleton"이라 오표기하고 있었고(실제론 종결), 원인은 **한 사실이 두 곳에 복사돼 한쪽만 갱신된 것**이었다. 그래서 `CLAUDE.md` 쪽은 "잔여 TBD 정본 = 각 프롬프트의 TBD 절, 복사 금지"로 바꿨다. 이번 건도 고칠 때 **"§1은 canonical 표만, 마이그레이션 상태는 §9만"** 처럼 한 사실의 소유 절을 하나로 정할 것. 루트 TODO의 미결 **DOC-1**(골든테스트 표 4곳·keep-list 4곳 중복)이 같은 뿌리.

## 답변 (recipient 작성 — 처리 후)

`git ls-tree -r main` + `git show main:{K-ICS,IFRS17,index}.html`로 확인: 라이브 `main`은 viz를 전부 `data/dart/viz/*`에서 fetch(`IFRS17.html:173-183`). `data/ifrs17/viz`는 `main`에도 로컬 `data/`에도 **존재하지 않음** — §9(LANDED)가 맞고 §1 Path note가 stale.

`docs/agents/claude-agent-publishing.md` 수정 완료:
1. §1 L107 "Path note"(cutover 미착수라고 오기) **삭제**. Migration 상태 소유 절 = §9만.
2. §9 L266 문구 정리 — "old note is retired" 대신 실측 근거(git ls-tree/local 확인, 2026-08-06)로 교체.
3. §9 L273 delete-list 예시에서 `data/ifrs17/viz` 제거(존재하지 않는 디렉터리를 keep-some/drop-some 예시로 들면 다음 slim-publish 때 혼란). `data/ir` 예시는 로컬 확인 결과 여전히 유효해 유지.

Root `TODO.md`의 DOC-1(중복 표) 은 이번 스코프 밖 — 그대로 둠.
