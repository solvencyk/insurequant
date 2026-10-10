---
from: orchestrator
to: designer
created: 20261011T0000Z
status: resolved
route: fix
company: MULTI
period: 2023.4Q-2024.4Q
iter: 1
---

## 미결 (sender 작성)
IFRS17.html 섹션 3 콤보(연도 모드 2023 · 2024 · 2025 · 2026.2Q)에 **백필 데이터가 들어왔다**(parser-ifrs17, 커밋 bc42f66, 런로그 `data/disclosure/_meta/ilp_backfill_pre2025_runlog.md` §2·§5). 오케스트레이터가 `viz_build_csm_combo_panel.py` 를 한 번 돌려 패널을 새로 만들었고(작업트리, 미커밋) 삼성화재로 확인한 결과 **2023 연말 칸에 구멍이 있다**.

### 지금 데이터 상태 (포트폴리오 마스터 `insurance_liability_portfolio.json`)
- **2024.4Q**: 39사 항목 1~8(잔여보장요소 BEL·RA·CSM·PAA) + 10~15(발생사고요소) 모두 적재(캐롯만 해당 없음).
- **2023.4Q**: 항목 10~15(발생사고요소·DART 부채 기준 잔여보장요소 합계 14·보험계약부채 합계 15)는 39사 전부, **항목 1~8(BEL·RA·CSM 구성)은 23사만**. 나머지 16사(메리츠·흥국화재·삼성화재·KB손보·DB손보·AIG·신한EZ·삼성생명·흥국생명·교보·AIA·코리안리 등 원천 부재 12 + 라이나·미래에셋·KB라이프 owner 결정 대기 3 + 카카오페이 등)는 구성이 없고 항목 14 합계만 있다. 캐롯은 항목 전부 해당 없음.
- 2024.1Q~3Q·2023.1Q~3Q 는 아직 백필 전(다음 round) — 분기 모드의 직전 5분기는 영향 없음.

### 문제
- 패널 행이 **있는데**(`co.q["2023.4Q"]` 가 존재: 발생사고요소·BS 값은 있음) 잔여보장요소 구성 인덱스 0~7 이 전부 null 이라, 현재 HTML 은 CSM 막대를 그리지 않는다(CSM 칸 「—」, 섹션 2 에는 2023 CSM 이 있는데 섹션 3 에서 빠짐). 지금 코드(`renderHistCombo`)는 「패널 행이 없을 때만」 CSM_waterfall 기말 CSM 으로 대체한다.

### 할 일
1. **패널 행은 있지만 잔여보장요소 구성(0~7)이 비어 있으면 CSM 을 CSM_waterfall 기말 CSM(섹션 2 와 같은 값·단위)으로 채운다**(기존 `csmOnly` 처리를 일반화: 값은 가짜가 아니라 같은 화면 섹션 2 의 값). 구성이 없는 BEL·RA·PAA 는 「—」, 안내문에 이 시점은 경영공시에 구성 표가 없다는 점을 적는다(데이터 유무로 판단, 날짜 하드코딩 금지).
2. 왼쪽 막대 높이를 어떻게 할지: DART 부채 기준 잔여보장요소 합계(항목 14)가 있으니(**패널에 지금 항목 14 가 없다 — 빌더에서 패널에 추가**) 「CSM + 그 외 잔여보장요소(구성 미분리) = 항목 14」로 쌓을지, CSM 만 그릴지는 designer 가 판단한다. 단 항목 14 는 2-4(순액) 와 기준이 다르다는 점(보험계약자산 상계)을 안내에 적고, 왼쪽·오른쪽 합이 BS 항목 20(재무상태표)과 어긋나면 기존 「보험계약자산 상계 등 차이」 행 로직을 그대로 쓴다.
3. 2023.4Q 항목 1~8 이 있는 23사는 지금처럼 BEL·RA·CSM·PAA 로 쌓는다. 값 표의 해당 칸이 두 경우(구성 있음 / 합계만 있음)에서 일관되게 읽히는지 확인한다.
4. 빌더(`scripts/viz_build_csm_combo_panel.py`)는 항목 14 추가와 `--check` 통과까지, 패널을 다시 빌드해 같은 커밋 상태로 맞춘다. **빌더는 `--help` 가 없고 인자 없이 바로 빌드한다**(publishing 이 확인하다 덮어쓴 전례).
5. 확인 회사: 삼성화재(2023 구성 없음), 한화생명 또는 구성이 있는 회사, 사이드카 1사(ABL/KDB생명/푸본현대: 2023.4Q 구성이 있는지 확인), DB손보, 라이나(2023.4Q 보류 3사 중 1), 카카오페이손보. 연도·분기 두 모드, 데스크톱 + 375px 한 번.

6. **작은 문구 1건(빌더 `scripts/viz_build_compare_panel.py`)**: 모바일 손해율 안 A 반영 때 알려진 건 — `data/compare/panel_compare.json` 의 `loss_curve.note` 에 「범례 옆 숫자로 적었습니다」 문구가 있는데 모바일에서는 틀리다(모바일은 아래 표). 「숫자로 적었습니다」처럼 중립 문구로 바꾸고 `viz_build_compare_panel.py --check` 가 깨끗하도록 패널을 다시 빌드한다(숫자 불변).

### 이미 확정(되묻지 말 것)
- CSM 은 회사 키 컬러 그대로(없으면 사이트 에메랄드, 밝히거나 섞지 않음), 보라 금지, 표 BEL→RA→CSM, 차트는 CSM 이 맨 아래, 음수 △, 증감 띠 없음, 컨트롤 줄 없음.

### 하지 말 것
- 마스터 JSON 수정 금지(읽기만). commit·push 금지. 서브에이전트 금지, 브라우저 탭 1개(다른 에이전트와 같은 탭을 쓰니 시작 시 열려 있는 탭 상태를 확인하고, 끝나면 에뮬레이션을 desktop 으로 되돌린다), 확인 후 임시 서버를 `taskkill //F //T //PID` 로 종료하고 포트 닫힘 확인. 로컬 확인은 `?iq_internal=1`.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), 맨 `python`·`python -` 금지, `encoding` 명시, UTF-8(BOM 없음). 끝에 `viz_build_csm_combo_panel.py --check`, `tests/test_deploy_assets.py`, `tests/test_push_gate_wiring.py`.
- 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 구성 없는 연말(2023)의 왼쪽 막대 처리 방식, 빌더 변경(항목 14), 확인 회사별 표·스크린샷 경로, 패널 `--check` 결과, `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
디자이너 반영 완료(2026-10-11, designer Sonnet, 약 24분, 토큰 208k): 2023 연말 구성 없는 회사(13곳)는 CSM(섹션 2 기말 CSM)+회색 구성 미분리(항목 14−CSM) 두 조각, 패널에 lrc_dart(항목 14) 열 추가, CSM 불일치 오표시 14→3건, panel_compare loss_curve.note 문구 중립화. 후속: 라이나·미래에셋·KB라이프 재작성 기준 통일(inbox/parser/20261011T0100Z) 후 사이드카 ilp_restated_comparative.json 을 합계 행에 쓰는 마무리.
