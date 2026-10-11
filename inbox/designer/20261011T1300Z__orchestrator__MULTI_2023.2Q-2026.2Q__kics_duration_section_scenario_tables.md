---
from: orchestrator
to: designer
created: 20261011T1300Z
status: open
route: feature
company: MULTI
period: 2023.2Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11): 「금리민감도·듀레이션 테이블을 별도로 올리는 김에, K-ICS 탭의 금리 민감도 부분에 있는 **듀레이션을 별도 섹션으로 떼라. 그 밑에 금리부 자산·부채 테이블을 시나리오별로 나눠서 보여줘라.**」 **push·배포는 보류**(owner 지시) — 이 티켓은 커밋까지만 하고 push 하지 않는다.

### 현재 (K-ICS.html)
- 「금리 민감도」 패널(`#sec-sens`, `data-share-section="금리 민감도"`) 안에 듀레이션 카드 3장(`#dur-strip`: 자산 듀레이션 · 부채 듀레이션 · 듀레이션 갭)과 설명 `#dur-note`(`renderDurationCards`, ? 팝오버 `help-dur-formula`)가 같이 들어 있다. 데이터는 `kics_duration_gap.json`(`durGapData`), 지급여력 ±50/±100bp 차트·표는 `kics_rate_sensitivity.json`.

### 해 줄 것
1. **새 섹션 분리**: 듀레이션 카드(+산식 ? 팝오버·설명)를 `#sec-sens` 에서 떼어 **「자산·부채 듀레이션」 별도 패널**로 만든다. 위치는 금리 민감도 바로 아래(자본비율 Forward Outlook 위). `data-share-section` 공유 버튼(출처 기재 규약, `ea918e4` 패턴)과 목차/섹션 앵커가 있으면 같이 맞춘다. 금리 민감도 패널에는 지급여력 영향 차트·표·KPI 만 남긴다(부제의 「· 자산/부채 듀레이션 갭」 문구도 정리).
2. **시나리오별 금리부 자산·부채 표**(새 섹션 안, 카드 바로 아래): `kics_duration_gap.json` 의 열 `자산_충격전 · 자산_금리상승 · 자산_금리하락 · 자산_금리평탄 · 자산_금리경사 · 자산_평균회귀` 와 `부채_…` 같은 6개를 그대로 쓴다(공시의 금리위험액 현황 표 값). 열 = 충격전 · 금리상승 · 금리하락 · 평탄화(금리평탄) · 경사화(금리경사) · 평균회귀, 행 = 금리부자산 · 금리부부채 · 순자산(금리부자산 − 금리부부채). 시나리오 열마다 충격전 대비 변화(금액·%)를 같이 볼 수 있게 한다(행을 늘리든 보조 줄이든 설계 판단은 designer). 단위는 원자료 백만원×0.01 = **억원**(`data/_derived/kics_irr_balance.json` 의 `scale 0.01` 와 같은 값) — 화면 단위 표기를 다른 패널과 맞추고 확인한다.
3. **원칙**: 화면 음수는 전부 △. 회사코드(KR…)를 화면·주소에 노출하지 않는다. 듀레이션·갭은 마스터 컬럼 그대로(JS 재계산 금지 — 기존 규칙). 순자산·변화량의 단순 뺄셈만 화면에서 하고 각주로 밝힌다. 마스터에 순자산 열이 꼭 필요해 보이면 하드코딩하지 말고 publishing 에 요청 티켓을 낸다(이 티켓에서 마스터를 쓰지 않는다).
4. **빈 값·예외**: 부채 ≤ 0 으로 부채 듀레이션이 정의되지 않는 칸(`비고`), 해당 분기 행이 없는 회사, 재보사(KR1101~1108; `kics_duration_gap.json` 에 일부만 있을 수 있음)는 「—」 + 이유 문구(데이터의 `비고`에서) 로 표시하고 빈 패널로 보이지 않게 한다. 분기 선택은 금리 민감도와 같은 상태를 쓰든 자체 선택을 두든 한 가지로 정하고(권장: 같은 기준 분기를 따르되 섹션 제목 옆에 현재 분기를 표기) 두 패널이 서로 다른 분기를 보여 혼동되지 않게 한다.
5. **모바일·접근성**: 모바일 = 데스크톱과 같은 구성(표는 가로 스크롤 가능, 첫 열 고정 검토), 긴 설명은 ? 팝오버, 표 `caption`·`scope`, 다크 모드, 포커스 순서. 480px·768px·1280px 에서 확인(공용 Browser pane 을 쓰지 말고 headless 로).
6. **자기 작업 범위**: `K-ICS.html`(필요 시 `common.css`·`theme.js`) 만 수정. 마스터 JSON·xlsx·`public_exports`·게이트 금지. **외부 파일 fetch 추가가 필요하면 먼저 그 파일이 `scripts/android_push_and_deploy.sh` 배포 대상(main 에 이미 있거나 `NEW_FILES`)에 있는지 확인**(현재 `kics_duration_gap.json` 은 main 에 있다).

### 규칙
- 맨 `python` 금지, 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), UTF-8(BOM 없음). 서브에이전트 금지.
- 테스트: `tests/test_deploy_assets.py` · `tests/test_push_gate_wiring.py` · `tests/test_share_screenshot.py` (+ `scripts/check_share_screenshot.py` 로 새 섹션 공유 확인) 통과. **풀 훅·push·배포 금지.**
- 커밋은 자기 파일만(`git add -A` 금지, 루트 개인 문서 제외), 메시지 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

### 보고
- 새 섹션 위치·구성(스크린샷 경로 또는 DOM 검증), 시나리오 표 열·행·단위, 빈 값 처리, 3개 너비 확인, 테스트 결과, `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
(오케스트레이터가 종결한다)
