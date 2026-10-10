---
from: orchestrator
to: designer
created: 20261010T1730Z
status: resolved
route: mock
company: MULTI
period: 2024.4Q-2025.4Q
iter: 1
---

## 미결 (sender 작성)
owner 요청(2026-10-10): 사별 비교(`compare.html`)의 **손해율 비교**가 지금 **모바일에서는 현가손해율(숫자) 끼리만 비교**하고, **데스크톱에서는 손해율 가정 curve(경과차년 꺾은선) 끼리 비교**한다. 모바일에서도 curve 를 비교하게 올리면 어떨지 **목업(mock) 하나**로 보고 싶다. 모바일에서 curve 비교가 너무 난잡해서 숫자 비교로 뒀던 것이므로, curve 를 **간단한 모양**으로 만든다: 데이터 점 표식 없앰, x축 값(눈금 숫자) 표시 없앰 등 장식 최소화.

### 해 줄 것 (목업 단계 — 실제 `compare.html` 은 수정하지 않는다)
1. 먼저 현재 구현을 읽는다: `compare.html` 의 손해율 가정 curve 차트(Chart.js, 경과차년 꺾은선)와 **모바일에서 숫자 비교로 바뀌는 분기**, 데이터 `data/compare/panel_compare.json`. 현재 모바일 화면(375px)을 스크린샷으로 남겨 「지금」과 비교할 수 있게 한다.
2. **별도 목업 파일**(예: `docs/mockups/compare/loss_curve_mobile_mock.html`, 자체 완결 HTML, 실제 패널 JSON 은 fetch 해서 실데이터 사용)에서 모바일 폭(375px)용 간단 curve 비교를 2안 만든다. 아이디어(필요하면 더 좋은 안으로 대체):
   - **안 A**: 한 차트에 선택한 회사들(2~4곳)의 curve 를 겹친다. 선 두께만, 점 표식 없음, x축 눈금 숫자 없음(시작·끝 라벨 정도만), y축은 눈금 2~3개 또는 없이 끝점 값만 우측에 표기, 범례는 선 끝에 회사명 직접 라벨(범례 박스 제거), 터치하면 세로 가이드선 + 값 표시.
   - **안 B**: 회사별 작은 curve(sparkline) 를 세로로 쌓고(small multiples) 같은 y 스케일로 비교, 각 줄 오른쪽에 현가손해율 숫자를 함께 둔다(지금의 숫자 비교를 유지하면서 모양을 보태는 안).
   - 현재 모바일의 「현가손해율 숫자 비교」와 함께 어떻게 공존하는지(대체 vs 보조)도 보여 준다.
3. 실제 데이터(비교 가능한 회사 3~4곳 선택; 곡선이 서로 많이 다른 조합과 비슷한 조합 각 1개)로 그리고, **375px 폭 스크린샷**을 안 A·안 B·현재(지금) 나란히 비교할 수 있게 저장한다(`artifacts/designer/` 아래, 파일명에 날짜). 접근성(색만으로 구분하지 않기: 선 끝 직접 라벨, 대비), △ 표기(음수), 회사코드 비노출, 다크 모드 한 장은 확인.
4. 보고에 **추천안과 이유**, 이 안으로 올릴 때 바뀌는 곳(코드 범위·예상 작업량), 모바일에서 여전히 난잡해지는 경우(회사 수 상한 등)를 적는다. **빠른 1차 목업**이다 — 오래 다듬지 않는다.

### 이미 확정(되묻지 말 것)
- 회사 키 컬러가 있으면 그 색, 없으면 사이트 에메랄드, 보라 금지, 음수는 △, 회사코드 비노출.

### 하지 말 것
- `compare.html`·마스터 JSON 수정 금지(읽기만, 목업은 별도 파일). commit·push 금지. 서브에이전트 금지, 브라우저 탭 1개, 확인 후 임시 서버를 `taskkill //F //T //PID` 로 종료하고 포트 닫힘 확인. 로컬 확인은 `?iq_internal=1`.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), 맨 `python` 금지, `encoding` 명시, UTF-8(BOM 없음). RAM 15.5GB(다른 에이전트 2개 동시 실행).
- 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).

## 답변 (recipient 작성 — 처리 후)
목업 완료(2026-10-10, designer Sonnet effort medium, 약 8분, 토큰 126k): docs/mockups/compare/loss_curve_mobile_mock.html, 스크린샷 artifacts/designer/compare_loss_mobile_*_20261010.png. 추천 안 A(한 차트 겹침 + 현재가치 표 보조). owner 선택 대기.
