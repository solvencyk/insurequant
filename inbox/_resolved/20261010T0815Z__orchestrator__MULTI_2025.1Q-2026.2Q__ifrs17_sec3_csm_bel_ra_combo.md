---
from: orchestrator
to: designer
created: 20261010T0815Z
status: resolved
route: feature
company: MULTI
period: 2025.1Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 요청(2026-10-10): `IFRS17.html` **섹션 3 "CSM 시계열"**(`#sec-hist`, `canvasHist`, 코드는 "Panel 6" 주석 블록 ~2497행, Chart.js)을 **누적 막대 + 보조축 꺾은선 콤보 차트**로 보강해 BEL·RA 를 함께 보여 준다. 참고 그림: `docs/design_refs/combo_stacked_column_line_reference_20261010.png` (Power BI 예시: 누적 막대 + 우측 보조축 꺾은선).

### owner 지정 사양
- **누적 막대, 아래부터 CSM**(주축). **주축 범위는 0부터 시작** — 사람들은 CSM 의 절대 크기를 궁금해하므로 CSM 이 바닥에서 시작해 크기가 바로 읽혀야 한다.
- CSM 위에 **BEL(최선추정부채) · RA(위험조정)**를 누적. **가능한 회사는 PAA · VFA 도** 누적("가능한 회사들은"이라고 했으므로 해당 값이 있는 회사만).
- **보조축 꺾은선은 지금처럼 신계약 CSM**.
- 색·툴팁·접근성·모바일·△ 표기(음수는 전부 △)는 기존 패널 규칙을 따른다.

### 데이터 (이미 마스터에 있음 — 이번 세션에서 빈 칸을 메웠다)
- `insurance_liability_portfolio.json`(경영공시 2-4, 억원, 39사 × **2025.1Q~2026.2Q 6개 분기만**). 항목 1~3 = 일반모형 BEL/RA/CSM, 4~6 = VFA BEL/RA/CSM, 7 = PAA 부채, 8 = 합계(= 1~7 합), 9 = 해지율 예외모형 플래그(차트에 안 씀).
- **잔여보장요소(LRC)만이라 BS 보험계약부채보다 작다**(발생사고요소 LIC 제외). 차트 제목·툴팁·주석에 "잔여보장요소 기준"을 분명히 쓴다.
- 기존 CSM 시계열(CSM_waterfall 기말 CSM, 단위 확인)은 더 긴 기간이 있다. **BEL·RA 는 2025.1Q 부터만 있으므로** 그 이전 분기는 CSM 막대만 두고(또는 구간을 제한하고) 그 사실을 화면에 적는다. 포트폴리오 CSM(항목 3+6)과 기존 시계열 CSM 이 일치하는지(정의·단위·분기말 기준) 먼저 대조해서 어긋남이 있으면 결과를 적는다.
- 재보사(KR11xx·KR1000 일부)는 이 데이터가 없다(다음 round). 데이터 없는 회사는 지금 CSM 시계열처럼 안내 문구.
- 알려진 미결 칸: 하나생명 2026.2Q(발행사 합계 행 오류, owner 판단 대기)·아이엠라이프 2025.1Q(발행사 합계 한 행 누락, owner 판단 대기) — 이 둘은 값이 바뀔 수 있으니 판단 전까지 화면에 문제 없게(회색 처리 또는 현재 값).

### ★ 사양 변경 2026-10-10 (이 절이 위 사양보다 우선): 잔여보장요소 + 발생사고요소 묶음 누적 막대
owner 가 "보험부채가 발생사고부채까지 포함한 것이냐"를 물었고, **지금 데이터(경영공시 2-4)는 잔여보장요소(LRC)만이라 발생사고요소(LIC, 지급준비금)가 빠져 있다**(BS 보험계약부채 = LRC + LIC). owner 지시:
- 분기마다 **막대 두 개를 나란히 묶는다**(묶음 + 누적, 참고 그림 2: `C:/Users/sangwook.cho/.claude/uploads/e15a5832-0270-4430-8e3e-4cba8a1f182c/39524103-image.jpg` — 묶음 막대 + 보조축 회색 꺾은선).
  - **왼쪽 막대 = 잔여보장요소**: 위에서 정한 대로 아래부터 CSM → BEL → RA → (가능한 회사는 PAA·VFA) 누적.
  - **오른쪽 막대 = 발생사고요소**: **BEL · RA 로 나눠 누적**.
  - 보조축 꺾은선 = 신계약 CSM(지금처럼). 주축은 0 부터.
  - Chart.js 는 데이터셋마다 `stack` 이름을 달리해 묶음+누적을 만든다(왼쪽 stack="LRC", 오른쪽 stack="LIC").
- **발생사고요소 BEL·RA 데이터는 아직 마스터에 없다.** parser(ifrs17 레인)가 출처 정찰 중이다(`inbox/parser/20261010T0830Z__orchestrator__*lic_bel_ra_scout.md`, 결과 `data/disclosure/_meta/lic_scout_20261010.md`). 정찰이 끝나기 전 목업에서는 오른쪽 막대를 **가짜 값 없이 자리 표시**(예: BS 보험계약부채 `IFRS17_BS.json` 항목 20(백만원→억원) − LRC 합계 = 발생사고요소 추정치를 단색 "추정" 막대로, BEL/RA 로 나눈 모양은 비율 가정 없이 레이아웃 스케치만)로 두고, **화면·툴팁에 "추정"을 분명히 표시**한다. 배포 금지(목업 단계).
- LIC 가 일부 분기·일부 회사에만 있을 수 있다(정찰 결과 대기). 없는 칸은 막대를 그리지 않고 안내한다.

### 설계 판단이 필요한 부분 (먼저 목업으로 owner 확인)
1. **VFA 를 어떻게 쌓을지**: (가) CSM·BEL·RA 를 일반모형+VFA 합산으로 쌓고 VFA 는 툴팁에서 분해 / (나) 일반모형 CSM·BEL·RA 위에 VFA 를 별도 색 구간으로 / 기본안은 (가), 필요하면 (나)를 토글. 두 안을 모두 목업으로 만들어 보여 준다.
2. **BEL 이 음수인 회사**(AIG 등 일부 회사·분기에서 합계 BEL 이 음수)와 합계 8 이 음수인 경우: 0 선 아래로 누적하되 CSM 은 항상 0 위 바닥에 두는 방식을 제안하고 owner 에게 보인다. 주축을 0 에서 시작하라는 지시와 충돌하면 음수가 있는 회사만 하한을 내린다.
3. PAA 가 큰 손보사(예: 합계의 대부분이 PAA)는 막대가 PAA 로 지배된다 — 이 경우 CSM 이 작게 보이는 것은 사실이므로 그대로 두되, PAA 를 접는 토글(CSM·BEL·RA 만 보기)을 제안한다.

### 방법
- 빠른 1차(effort medium) 목업(로컬 미리보기, 실제 회사 2~3곳: 생보 대형·손보 대형·BEL 음수 회사) → owner 확인 → 딥다이브. 목업 단계에서는 push·배포 없음.
- 데이터 가공은 designer 의 viz 빌더(`scripts/viz_build_*_panel.py` 스타일, `--check` 지원)로 패널 JSON 을 만들고 HTML 은 JSON 을 fetch 한다(인라인 금지). 마스터 JSON 은 읽기만 한다. 새 JSON 이 배포 keep-list 에 들어가야 하면 `tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py` 배선과 publishing 필요 사항을 `TODO_designer.md` 에 적는다.
- 라이브 확인·디버그는 `?iq_internal=1`. designer 는 push·commit 하지 않는다. RAM 15.5GB PC: 서브에이전트 금지, 브라우저 탭 1개.

## 답변 (recipient 작성 — 처리 후)
designer 이식 완료(2026-10-10, 미커밋). IFRS17.html 섹션 3 콤보+값 표, panel_csm_combo.json(--check 동일). 발생사고요소는 BS 항목 20 − LRC 추정 자리 표시(lic_estimate() 한 곳), 실 BEL/RA 는 정찰 lic_scout_20261010.md 후 별도 티켓. owner 정정으로 증감 띠 제외. 모델 Sonnet.
