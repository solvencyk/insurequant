---
from: owner
to: designer
created: 20260616T0036Z
status: resolved
route: backlog
company: MULTI
period: ALL
iter: 1
---

## 발주 (owner) — Anthropic 공식 skill 도입 평가 + 적용 (designer 우선 트랙)

이번 round는 **버그 수정이 아니라 designer 스테이지 워크플로우에 Anthropic 공식 skill 2개를 도입**하는 인프라 작업이다. round3 글리치 트랙(`…live_qa_glitches_round3`)과 **별개**로 진행하되, 도입 결과로 그 글리치들을 더 안정적으로 고칠 수 있으면 활용하라.

### DS1 (primary) — `frontend-design` skill 도입
designer 프롬프트의 미완(TBD) 항목이 정확히 이 skill이 메우는 영역이다:
- **design system** 수립 (색/타이포/spacing 토큰)
- **common.css 추출** (KICS.html / IFRS17.html / index.html 공통화)
- **A11y baseline**
- **차트 legend 밀도 / donut stack breakpoint / 모바일 pass scope**

작업:
1. `frontend-design` skill을 호출해 위 TBD 항목의 baseline을 수립하고, designer 프롬프트(`docs/agents/claude-agent-designer.md`)의 해당 TBD 섹션을 채운다(skeleton → 정식).
2. 공통 스타일을 `common.css`로 추출하되 **3개 HTML의 기존 렌더를 깨지 않게** 점진 적용.
3. **확정 결정은 skill이 덮어쓰지 못하게 보존**(메모리/owner 확정):
   - 음수 = △(세모) 표기 (한국 회계 관행, owner 최우선 지시)
   - tier1 도넛 "100%+" 표기 (발행액/한도라 >100% 정당)
   - 현대해상 키컬러 주황 톤 (round3 D4)
   - 모바일 = 당기/당년도만 (round3 D9)

### DS2 (보조) — `webapp-testing` (Playwright) 하니스 도입
현재 designer 검증이 flaky하다 (메모리: preview_eval/screenshot 반복 행 → Edge headless `--dump-dom`+URL파라미터 우회, 좀비 서버가 포트 소진). 이걸 Playwright 기반으로 정면 대체한다.

작업:
1. `webapp-testing` skill로 로컬 3개 HTML(KICS/IFRS17/index)에 대한 렌더 스모크 테스트 하니스를 구성.
2. **round1~3 라이브-QA 글리치(누적 28건)를 회귀 테스트로 인코딩** — 지금까지 owner가 매번 눈으로 잡던 걸 자동 assert로 전환 (예: K-ICS 드롭다운 48사, shock 표준화 `fmtShock`, 축 윈도잉 5분기/연도, 미제공사 메시지 등).
3. 좀비 서버/포트 소진 회피 — Playwright 자체 서버 라이프사이클 사용, 끝나면 정리.

### 제약
- **master JSON read-only.** 데이터 이상은 parser 소관 — designer는 렌더/스타일/테스트만.
- DS1·DS2는 **인프라/프로세스 변경**이라 데이터 게이트와 무관하지만, HTML 구조 변경 시 기존 차트 동작 회귀 없는지 DS2 하니스로 자체 검증 후 보고.
- 진행 결과·도입 가부 판단(특히 webapp-testing가 현 Edge 우회보다 실제로 나은지)을 이 inbox 답변란에 적어 회신.

## 답변 (designer 2026-06-16)

### DS1 — `frontend-design` skill 도입 ✅ 완료
스킬 호출 → 기존 3개 대시보드의 de-facto 시스템을 정식 토큰화 + `common.css` 추출. **무파괴(extraction, not redesign)** 원칙으로, common.css의 모든 값 = 2026-06-16 렌더값과 1:1.

- **디자인 시스템 토큰** (`common.css :root`): surface/ink(--bg/card/border/text/muted/ink-strong) · brand(--primary/-hover) · 금융 status(--pos/neg/warn) · type(--font-sans) · spacing(--sp-1~6, 4px base) · radius(--r-sm/md/lg/pill) · misc(--bd/t-fast/maxw). 값 변경 없음 — **#0d6efd 팔레트 스왑은 owner-gated(DESIGN-V2 P1)라 토큰만 정식화, 값 유지**.
- **common.css 추출**: 3파일에 동일하던 chrome(header/tabs/brand/container/select/panel h2·p/table base/num·text utils)을 단일화. `<link>`를 inline `<style>` **앞**에 배치 → 페이지별 차이(.panel/.controls 여백)는 inline override로 보존. `*{box-sizing}`·차트/컴포넌트 클래스·@media는 페이지 고유로 **미추출**(레이아웃 안전).
- **A11y baseline**(additive, 마우스 기본렌더 무변경): `:focus-visible` 포커스링 + `prefers-reduced-motion`. 잔여 갭(active-tab 색상전용, 토글 input 포커스, 캔버스 aria-label, medium badge 대비)은 §5.3에 다음 패스로 명시.
- **프롬프트 정식화**: `docs/agents/claude-agent-designer.md` §5 skeleton→정식(토큰표·common.css contract·A11y·차트 규약 legend밀도/donut stack/모바일 scope·확정결정 잠금).
- **확정결정 4개 보존 확인**: △세모·도넛 100%+·현대해상 #F47920·모바일 당기 — preview 라이브로 재확인(삼성생명 senTable △/↑/정수 유지).
- **검증(무회귀)**: preview로 3페이지 reload — common.css 200 로드, 콘솔 에러 0, computed style 일치(데스크탑 베이스는 common, 모바일 @media override 동작), index treemap 39행 로드. K-ICS·IFRS17·index 모두 정상.
- **배포 주의(publishing/owner)**: `common.css`는 신규 루트 에셋 → HTML과 함께 배포돼야 함(루트 + templates/data 미러). publishing handoff 필요.

### DS2 — `webapp-testing`(Playwright) 도입 ✅ 구현 완료 (사용자 "둘 다 진행" 지시로 착수)
- **Feasibility spike 통과**: venv에 `playwright` + chromium 설치 → 번들 Chromium **이 머신에서 정상 구동**("CHROMIUM LAUNCH OK"). Edge/Chrome `--dump-dom` 0바이트 이슈를 우회함(정정: flaky한 건 preview가 아니라 headless dump였음).
- **회귀 하니스 작성**: `tests/regression_dashboards.py`(+`tests/README.md`). `with_server.py`로 서버 라이프사이클 자동관리(좀비포트 0). 데스크탑 뷰포트(1366)라 preview(0폭=모바일고정)가 못 보던 **윈도잉 등 데스크탑 회귀까지** assert.
- **22 assert GREEN (0 fail)**: index(common.css·KPI 4종·typeahead datalist+점프·트리맵·콘솔0) / K-ICS(common.css·드롭다운≥40·**KB 2026.1Q=185.87 라벨변형 수정**·콘솔0) / IFRS17(common.css·as-of·shock↑↓·△·연도윈도잉[2023,2024,2025,2026.1Q]·분기 last5·미제공사 메시지·콘솔0). owner가 매번 눈으로 잡던 걸 자동 assert로 전환.
- **알려진 갭(visual-only)**: 캔버스 텍스트(도넛 "100%+"·ECharts 라벨)는 DOM 미노출이라 미assert → 도넛 컨테이너에 `data-pct` 노출하면 테스트 가능(차기 패스).
- **실행**: `tests/README.md` 참조(repo root에서 1커맨드). 향후 분기/회귀는 이 하니스로 그린 확인.

status: answered (DS1+DS2 모두 구현·검증 완료).
