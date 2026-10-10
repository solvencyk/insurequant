---
from: orchestrator
to: designer
created: 20261011T0830Z
status: resolved
route: feature
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
publishing 이 새 마스터 시트 `보험계약부채`(발생사고요소 포함, `public_exports/보험계약부채.json`, 커밋 822c99c)를 만들었다. 사이트 「테이블 다운로드」 목록은 `download-survey.js` 의 `SHEETS` 배열에 직접 적혀 있어서 거기에 줄을 넣어야 화면에 나온다(HTML/JS 는 designer 몫).

### 할 일
1. `download-survey.js` `SHEETS` 배열에 아래 줄을 기존 항목 형식·순서 관행에 맞춰 추가:
   `{ name: "보험계약부채", file: "public_exports/보험계약부채.json", code: "ILP", label: "보험계약부채 (잔여보장·발생사고요소)" }`
   (필드명·`code` 값 규칙은 기존 줄을 따를 것. `code` 가 내부 용어 노출이 되는지 확인 — 기존 줄의 관행 그대로.) 같은 배열에 없는 `자본성증권발행현황`·`금리듀레이션갭` 이 의도된 누락인지(공개 시트인지) `public_exports/manifest.json` 으로 확인하고, 공개 시트인데 빠졌으면 같이 넣는다(판단 근거를 답변에 한 줄).
2. 다운로드 목록·팝업 렌더링 확인(데스크톱+모바일, 새 시트 라벨이 잘리거나 겹치지 않는지), 콘솔 오류 0, 배포 keep-list 테스트(`tests/test_deploy_assets.py`)·`tests/test_push_gate_wiring.py` 통과.
3. **K-ICS.html 낡은 문구**: forward outlook / 자본성증권 패널의 빈 상태 문구 「(19사 cohort 외)」 는 재보사 8곳이 추가되어 더는 맞지 않는다. 현재 데이터 구성(`kics_forward_capital.json`·`kics_tier1/2_utilization.json` 의 회사 집합)에 맞게 문구를 고치거나, 맞는 일반 문구(예: 「이 회사는 해당 자료가 없습니다」)로 바꾼다. 데이터를 읽어 동적으로 나오게 할 수 있으면 하드코딩하지 않는다.
4. **서울보증보험(KR0150)** 은 `kics_forward_capital.json` 에 행이 없어 Forward 패널이 비는데, 이 빈 상태 문구가 이유(「자본성증권 발행 없음」 등 사실에 맞는 말)를 정확히 말하는지만 확인(문구가 틀렸으면 고침). 데이터는 건드리지 않는다.

### 규칙
- 마스터 JSON·xlsx·`public_exports` 수정 금지(읽기만). 커밋은 자기 파일만(`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`), push·배포 금지. 서브에이전트 금지, docling 금지. 브라우저 검증은 headless(Playwright/Edge)로 — **공용 Browser pane 을 쓰지 말 것**(오케스트레이터가 다른 일에 쓴다).
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), **맨 `python`·`python -`(stdin heredoc) 절대 금지**, `encoding` 명시, UTF-8(BOM 없음). 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 변경 파일·줄, 검증(헤드리스 스크린샷 경로 또는 DOM 텍스트), 테스트 결과, `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
answered by designer 1335d0d (2026-10-11): download-survey.js SHEETS 12->15(보험계약부채·자본성증권발행현황·금리듀레이션갭), K-ICS 전망 패널 낡은 문구 교체, 서울보증 PAA 제외 사유 문구. 헤드리스 검증·테스트 통과. 오케스트레이터 종결. 남은 것: 서울보증 제외 행·사유를 kics_forward_capital.json 에 넣는 일은 publishing.
