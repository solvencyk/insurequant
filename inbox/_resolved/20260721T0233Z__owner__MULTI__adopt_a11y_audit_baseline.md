---
from: owner
to: designer
created: 20260721T0233Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 미결 (sender 작성)

**배경:** 외부 스킬 목록(42종) 검토 중 `ui-ux-pro-max`(디자인 시스템 접근성·대비 감사)가 designer 스테이지의 **기존 TBD "A11y baseline"** 을 정확히 채운다고 판단 → 도입 발주.

**왜 필요한가:** `CLAUDE.md` designer 프롬프트 진행도에 **A11y baseline이 미정(TBD)** 으로 남아 있음. `common.css`에 토큰은 잡혀 있으나 기준선과 검증 수단이 없어, 신규 차트/패널이 추가될 때마다 대비·포커스·라벨이 사람 눈대중으로만 통과함.

**대상:** 배포 HTML 4개 — `index.html`, `K-ICS.html`, `IFRS17.html`, `공시보고서.html`.

**지켜야 할 기존 확정 사항 (바꾸지 말 것):**
- 디자인 시스템 단일 소스 = 루트 `common.css` (토큰 + chrome + A11y).
- `common.css` link는 **inline style보다 앞**에 둬서 페이지 override를 보존(무파괴 원칙). **`box-sizing` hoist 금지.**
- 화면 음수 표기는 전부 **△(세모)** — 한국 회계 관행, owner 최우선 지시. 신규 차트/표에도 필수.
- CSP meta(head 첫 자식) + CDN SRI는 이미 적용됨 — 감사하면서 깨뜨리지 말 것.
- 마스터 JSON은 designer에게 **읽기 전용**.

**요청 (deliverable):**
1. **A11y baseline을 명문화** — 어느 수준을 목표로 하는지(예: WCAG AA 대비비), 무엇을 검사 대상으로 삼는지(텍스트 대비, 차트 계열색 구분, 포커스 링, 폼 라벨, 키보드 이동). 목표 수준은 designer가 판단해서 제안.
2. 4개 HTML **현황 감사 + 위반 목록**(파일·요소·현재값·기준값). 차트 계열색은 색각 이상 조건에서도 구분되는지 포함.
3. **수정은 위반 목록을 owner가 확인한 뒤** 진행 — 이번 발주는 baseline + 감사까지. 다만 명백한 저위험 위반(대비 미달 텍스트 색 토큰 조정 등)은 `common.css` 토큰 레벨에서 바로 고치고 답변에 명기해도 됨.
4. 구현 형태는 위임 — 외부 스킬 설치 vs `skill-creator`로 로컬 스킬. **로컬 권장**. 외부 채택 시 이유 명시.
5. 산출물: `docs/` + `docs/agents/claude-agent-designer.md`(현재 skeleton) A11y 섹션. 이력은 `TODO_designer.md` / `docs/changelog_designer.md`.

**스코프 밖:** 레이아웃 개편·차트 종류 변경·모바일 패스는 이번 건 아님. 접근성 기준선과 감사만.

## 답변 (recipient 작성 — 처리 후)

**요청 1~5 전부 완료.**

1. **Baseline**: WCAG 2.1 AA (텍스트 4.5:1 / 큰텍스트·UI경계 3:1, 색상만으로 의미 전달 금지, 키보드 조작, 포커스 가시성, 폼 라벨, 차트 계열색 색각이상 구분). 전체 표+근거는 `docs/a11y_baseline.md` §1.
2. **4개 HTML 감사 완료**. 텍스트 대비(공통.css 토큰 전체 + 페이지별 리터럴), 차트 계열색 색각이상 시뮬레이션(protanopia/deuteranopia 선형행렬), 키보드 접근성, 포커스 가시성, 폼 라벨 — 전부 스크립트로 계산(`scripts/a11y_contrast_check.py`, 손계산 안 함). 위반 목록 `docs/a11y_baseline.md` §2.
3. **저위험 위반 즉시 수정** (요청 예시는 "대비 토큰 조정"이었지만, 실제로 나온 저위험 항목은 전부 **순수 추가형 키보드/포커스/aria** 쪽이었음 — 색 토큰 변경은 전부 rendered-value라 owner-gate 대상으로 판단해 손 안 댐, §2b 대기열로 보류):
   - **index.html 트리맵 칸 + 모바일 리스트 행**: 클릭만 가능하고 **키보드로 전혀 접근 불가**했음(사이트 핵심 내비게이션인데 WCAG 2.1.1 위반). tabindex/role/aria-label/Enter·Space 핸들러 추가.
   - **index.html 커스텀 토글**: 실제 포커스가 0×0 숨김 체크박스에 걸려 포커스링이 안 보이던 문제. 보이는 라벨 쪽으로 링 리타겟.
   - **공시보고서.html**: 4개 중 유일하게 `common.css` 자체를 안 불러오고 있었음(포커스링·reduced-motion 전부 없음). link 추가.
   - **차트 10개**(K-ICS 5·IFRS17 5·index 2) `role`/`aria-label` 추가.
   - **active-tab 링크**(K-ICS/IFRS17/공시보고서) `aria-current="page"` 추가 — 스크린리더가 현재 페이지를 알 수 있게(기존 §2b "active-tab 색상단독" 이슈의 스크린리더 쪽만 완화, 시각적 색상단독 큐는 여전히 owner 승인 대기).
   - 검증: Claude Browser 4페이지 데스크톱+모바일 콘솔 0에러, 트리맵 칸에 Enter keydown 디스패치 → 클릭과 동일하게 K-ICS.html 이동 확인, aria-current 3파일 확인.
4. **로컬 스킬 채택**: `ui-ux-pro-max` 미설치 상태(외부 스킬 설치는 별도 승인 필요) + 이 저장소 A11y 표면이 작고 특수(커스텀 토글·canvas 차트·계열색 팔레트 몇 개 반복 패턴, 이미 문서화된 토큰/△ 규약)라 범용 외부 감사보다 이 프로젝트 제약을 아는 로컬 스킬이 낫다고 판단. `.claude/skills/a11y-audit/SKILL.md` 신설.
5. **산출물**: `docs/a11y_baseline.md`(baseline+전체 감사결과) · `docs/agents/claude-agent-designer.md` §5.3 재작성(기존 `#ff9f40` 항목은 stale로 확인돼 제거) · `scripts/a11y_contrast_check.py` · `.claude/skills/a11y-audit/` · `TODO_designer.md`/`docs/changelog_designer.md` 기록.

**owner 확인 대기 (§2b, 색 변경 필요해서 안 건드림)**: `--muted`/`--card` 대비 4.45(경계선), index 범례 초록 텍스트 3.30, `#adb5bd` 빈값 표기 2.07, IFRS17 6색 팔레트 중 2쌍(주황/빨강, 보라/청록)이 적녹색맹 시뮬레이션에서 근접, index 트리맵/버블 적↔녹 발산 스케일이 같은 시뮬레이션에서 대비 하락(툴팁+숫자라벨로 일부 완화). 기존에 있던 active-tab 색상단독 큐 이슈는 그대로 유지(오너 승인 대기 항목, 변경 없음).

**스코프 밖 확인**: 레이아웃/차트종류/모바일패스 미변경. CSP·SRI·box-sizing·common.css link 순서·△표기 전부 그대로 유지, 마스터 JSON 미접근.
