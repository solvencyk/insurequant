---
from: owner
to: publishing
created: 20260616T0514Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 발주 (owner) — publishing 프롬프트 내부모순 정리 (MD 감사 후속)

`docs/agents/claude-agent-publishing.md`:

- **헤더(line 5) ↔ §5(line 126) 모순 해소.** 헤더 execution-model = "이 에이전트가 git을 **직접 실행**(2026-05-31 결정, 2026-05-30 supersede)". 그런데 §5(line~126) "*Subagent prints these for the user to run. Subagent does **not** execute them*" = 옛 2026-05-30 모델 그대로. → §5를 헤더와 일치(로컬 git은 직접 실행, **push만 gated**)로 수정하거나 그 문장 삭제.
- **§3 "gathering scripts" 표현 정정.** line~90 "Assembly gate — **gathering scripts** exit code 0" — publishing 자기 조립 스크립트를 죽은 stage명으로 칭함. "assembly/build scripts"로.
- **(인지/선택) §1 canonical `data/dart/viz/*` vs 라이브 main `data/ifrs17/viz/*` 분기** — 이미 §9에 self-documented(브랜치 land 시 정리). 지금은 경로 주석 최신화만, 강제 아님.

### 주의
- UTF-8 no BOM, python 풀패스. 인라인 멀티라인 `python -c` 금지.
- xlsx 작업은 `xlsx` skill 상시(이미 채택), `scripts/build_csm_waterfall_master.py` 실행 금지(raw purge 브랜치 붕괴).

## 답변 (publishing 2026-06-16 — 3건 전부 정리 완료)

`docs/agents/claude-agent-publishing.md` 수정 완료:

1. **헤더↔§5 모순 해소** (구 line 126 → 현 line 128). 옛 문장 *"Subagent prints these for the user to run. Subagent does **not** execute them."* 삭제하고 헤더와 일치하도록 교체: *"The agent runs the local-git commands itself (add/commit/branch/checkout/rm); **only the outward `git push` is gated** — show the user exactly what will be pushed, get their GO, then run it (header execution-model · §1 hard rules · §9 procedure)."* → 헤더(L5)·§1 hard-rule(L36)·§9(L201)와 4곳 정합.
2. **§3 "gathering scripts" 정정** (현 line 92): *"Assembly gate — **assembly/build scripts** exit code 0"*. 문서 내 "gathering" 잔존 0건 확인(다른 라이브 오기재 없음).
3. **(선택) §1 경로 주석 최신화** (현 line 58): 표 아래 한 줄 추가 — *"Path note: the table lists the post-migration canonical (`data/dart/viz/*`). Live `main` still reads `data/ifrs17/viz/*` — see §9 'Pending path migration' for detail and the cutover trigger."* 경로 자체는 안 건드림(브랜치 land 시 §9대로 정리). 읽는 사람이 §1만 보고 오해하지 않도록 §9 cross-ref만.

검증: BOM 없음(UTF-8 no BOM, `# A...` 시작), 깨진 한글 없음(편집부 영어), 새 문구 3개 grep 확인 + 옛 모순 문장 제거 확인. python 인라인 멀티라인 미사용, xlsx/`build_csm_waterfall_master.py` 무관(문서 편집).

배포 없음: `docs/agents/*.md`는 IP라 slim keep-list(HTML+master JSON) 비대상 → push 불요. 이 스레드 종결.
