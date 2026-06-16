---
from: owner
to: parser
created: 20260616T0514Z
status: open
route: backlog
company: MULTI
period: ALL
lane: kics+ifrs17
iter: 1
---

## 발주 (owner) — parser 소관 문서 정합성 정리 (MD 감사 후속, owner 결정 반영)

owner MD 감사에서 parser 소관 문서의 stale/모순 발견. owner 결정 2건(misc=현행유지, kics doc=stub 동결)을 반영해 정리.

### A. 공유 프롬프트 `docs/agents/claude-agent-parser.md`
- **"gathering" → "publishing" 개명.** §1 표 "merge into `kics_disclosure.json` is done by **gathering**" + "that's **gathering's** job" — gathering은 2026-05-31 **publishing으로 머지된 죽은 stage**. 루트 마스터 조립/병합 주체는 publishing.
- **SKELETON 헤더 갱신.** line 3 "Status: SKELETON"이 실질과 안 맞음(프롬프트 충실 + kics/ifrs17 SKILL 2개 보유). "substantially populated; 운영 정본은 `.claude/skills/{kics,ifrs17}-parser/` SKILL" 정도로.
- **misc (owner 결정: 현행 유지 + 문서만 정리).** §0 Contract `kics|ifrs17|misc` + §2.3 misc — **3번째 레인 승격/삭제 아님**. "2 primary lane(kics/ifrs17) + **보조 misc**(IR/채권/KIDI, 메인세션 처리, 별도 lane·inbox 없음)"로 위상만 명확화.
- (선택) §1 K-ICS 출력 경로 `md_inbox/<KR>/<period>.md` 표기가 실제 `data/disclosure/FY*/parsed/*.md`와 다르면 정정.

### B. ifrs17 도메인 doc `docs/domains/claude-agent-ifrs17.md` (lane: ifrs17) — 🔴 HIGH
- §7.3 / §9 Q8 / §10이 *"민감도 primary = K-ICS 분기공시, DART 주석은 skim PoC·primary 아님(`sensitivity_extractor.py` misaligned)"*로 단언 → **현행 owner-directed DART CSM/PL 민감도 실파이프라인**(`sensitivity_extractor.py` → `sensitivity_heatmap.json`, IFRS17.html 렌더)과 **정면 충돌**. 새 ifrs17 SKILL은 "코드+SKILL 우선"으로 못 박았으나 **tracked SOT는 옛말 그대로** = owner가 계속 보는 민감도 표를 틀리게 가리킴.
- → 해당 절에 **"⚠️ superseded: DART 민감도는 현행 실파이프라인. 'K-ICS-primary / DART=skim PoC' 표기는 폐기"** 정정·포인터 박기(SKILL traps와 동일 취지, 복붙 말고 1줄 정정).

### C. kics 도메인 doc `docs/domains/claude-agent-kics.md` (lane: kics) — owner 결정: **design stub 동결 + 포인터**
- 상단 헤더 추가: **"운영 정본 = `.claude/skills/kics-parser/` SKILL + `docs/agents/kics-json-validation-rules.md`. 본 문서는 2026-05 설계 stub(부분 stale) — 시장위험 36-40 / IRR 41-46 / 금리민감도는 SKILL·rules 참조."**
- 명백한 오기만 정정(전면 리프레시 아님): 출력명 `kics_data.json` → `kics_disclosure.json`; flow 링크(`claude-download-flow.md` 등 pre-reorg) → `docs/flows/*` 또는 제거.
- §3 "push 완료 전 세션 종료 금지" 삭제/수정 — 현 정책(push=owner-gated, "parser self-approve 안 함", TODO 정책 #7)과 충돌.
- (선택) "K-ICS 37社" 카운트는 현행 38(kics_disclosure)와 어긋 — stub 동결이라 강제 아님, 헤더 경고로 갈음 가능.

### 주의
- UTF-8 no BOM, 한글 깨질 환경이면 영어. python 풀패스. 인라인 멀티라인 `python -c` 금지.
- SKILL=머신-로컬(gitignored) 운영 트리거, doc=tracked 설계 SOT — 역할 분담 유지. 내용 복붙 말고 포인터.

## 답변 (parser/ifrs17 2026-06-16 — §A 공유프롬프트 + §B ifrs17 doc 정리 완료; §C는 kics 세션)

### §B ifrs17 도메인 doc `docs/domains/claude-agent-ifrs17.md` — DONE (🔴 HIGH)
§7.3 머리에 **⚠️ SUPERSEDED (2026-06-16)** 블록 추가 — "민감도 primary=K-ICS / DART=skim PoC(`sensitivity_extractor.py`
misaligned)"가 현행 코드와 충돌함을 명시하고, **운영 정본 = 코드 + `.claude/skills/ifrs17-parser/` SKILL**, 실파이프라인
경로(`sensitivity_extractor.py`→`viz_build_ifrs17_panels.py`→`sensitivity_heatmap.json`→`IFRS17.html`)를 1블록으로 정정.
§9 Q8·§10 Q8도 같은 포인터로 커버(복붙 없이 1정정). SOT는 tracked 유지, SKILL은 머신-로컬 트리거 — 역할분담 유지.

### §A 공유 프롬프트 `docs/agents/claude-agent-parser.md` — DONE
- **gathering → publishing 개명**: §1 표 kics행("merge into kics_disclosure.json is done by **publishing**, not here") +
  §1 본문("that's **publishing's** job (gathering was merged into publishing 2026-05-31)").
- **SKELETON 헤더 갱신**: "substantially populated; 운영 정본(자동로드 트리거) = `.claude/skills/{kics,ifrs17}-parser/`
  SKILL, 본 프롬프트는 공유 contract + working principle, §4 일부 TBD만 미작성".
- **misc 위상 명확화** (owner 결정: 현행 유지): §2.3에 "보조(auxiliary) — kics·ifrs17 2 primary lane + misc는 메인
  세션 처리, 별도 lane·inbox 없음, 3번째 레인 승격/삭제 아님" 1줄 추가.
- (선택) §1 K-ICS 출력경로 `md_inbox/<KR>/<period>.md`는 표기에서 "Docling MD (parsed)"로 일반화(경로 단정 회피) —
  실제 경로 `data/disclosure/FY*/parsed/*.md` 정합 정정은 **kics 세션 소관**으로 남김(ifrs17 단정 회피).

### §C kics 도메인 doc — kics 세션 (2-lane split)
`docs/domains/claude-agent-kics.md` stub 동결 헤더·오기 정정·§3 push정책 충돌 삭제는 **K-ICS 세션**에서 처리(본 건 lane:
kics+ifrs17이나 §C는 kics 소관). kics 세션이 자기 SKILL 결정화 시 함께 처리 예정.

status: §A(공유)·§B(ifrs17) done. §C는 kics 세션.

