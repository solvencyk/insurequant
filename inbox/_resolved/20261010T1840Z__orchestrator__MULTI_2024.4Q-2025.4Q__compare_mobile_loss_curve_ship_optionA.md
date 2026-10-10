---
from: orchestrator
to: designer
created: 20261010T1840Z
status: resolved
route: feature
company: MULTI
period: 2024.4Q-2025.4Q
iter: 1
---

## 미결 (sender 작성)
owner 결정(2026-10-10): 모바일 손해율 비교 목업 중 **안 A**(한 차트에 선택한 회사 curve 를 겹침, 점 표식·x축 눈금 숫자 없음, 선 끝 직접 라벨, 업계 중앙값 점선, 현재가치 표 보조)로 **실제 `compare.html` 에 올린다.** 목업 `docs/mockups/compare/loss_curve_mobile_mock.html`(`?opt=A`), 스크린샷 `artifacts/designer/compare_loss_mobile_A_*_20261010.png`.

### owner 수정 지시
- **「짚은 시점」 열은 뺀다**(owner: "그건 빼라"). 표는 **회사 · 현재가치** 두 열만 남긴다.
- 「짚은 시점」 열이 없어지므로 **터치 시 세로 가이드선 + 값 표시 상호작용도 뺀다**(값을 보여 줄 곳이 없다). 차트는 정적으로: 선 끝의 회사명·끝점 값 라벨과 세로 눈금 2~3개로 충분하다. 터치 가이드를 다른 모양(예: 선 위 값 말풍선)으로 살리지는 않는다(owner 가 단순한 모양을 원한다).
- 목업의 보조 안내 문구 중 터치·짚은 시점을 설명하는 문장도 함께 뺀다. 「현재가치 손해율은 선에 넣지 않고 아래 표에 함께 둔다」 정도의 짧은 안내는 유지 가능.

### 구현 범위 (목업 리포트에 적힌 변경 범위 기준)
- `compare.html`: `chartsOn()`(641px 미만 꺼짐) 에서 **손해율 가정 curve 카드만** 모바일에서도 curve 경로로 들어가게 하고, 모바일용 SVG 렌더 함수(목업 안 A 코드 이식)와 현재가치 숫자표(회사·현재가치)를 카드 아래에 붙인다. 가이드 이름 `unitName()` 의 폭 분기도 손본다. 데스크톱(641px 이상)의 Chart.js 꺾은선은 **그대로** 둔다. 모바일의 다른 카드(유지율 등)는 건드리지 않는다.
- 회사 수 상한: 안 A 는 업계 중앙값 포함 4선이 한계 — 선택이 더 많으면 모바일에서는 처음 4개만 그리고 「모바일에서는 4곳까지 겹쳐 봅니다」 한 줄 안내(숫자표는 전부).
- **색**: 목업은 compare 의 기존 4색(첫 색 틸)을 썼다. **owner 확정 규칙 = 회사 키 컬러가 있으면 그 색(IFRS17.html `KEY_COLORS` 참고), 없으면 사이트 에메랄드, 보라 금지.** compare 에서 회사 선 색을 이미 데스크톱 curve 가 어떻게 정하는지 확인하고 **모바일 curve 도 데스크톱과 같은 색 규칙을 쓴다**(색이 데스크톱과 어긋나면 데스크톱 쪽 규칙을 따른다). 선 모양(실선·파선·점선)으로 색 외 구분은 유지.
- 접근성(색만으로 구분하지 않기, 대비), 음수 △, 회사코드 비노출, 다크 모드, 375px 에서 가로 넘침 없음.
- 목업 로드 때 콘솔 404 한 건이 있었다 — 어느 파일인지 확인해 compare.html 쪽 원인이면 고친다.

### 하지 말 것
- 마스터·패널 JSON 수정 금지(읽기만; `data/compare/panel_compare.json` 은 publishing 이 재생성 중이니 건드리지 않는다). 데스크톱 curve 변경 금지. commit·push 금지. 서브에이전트 금지, 브라우저 탭 1개, 확인 후 임시 서버를 `taskkill //F //T //PID` 로 종료하고 포트 닫힘 확인. 로컬 확인은 `?iq_internal=1`.
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 멀티라인 `python -c` 금지(스크립트 파일), 맨 `python`·`python -` 금지, `encoding` 명시, UTF-8(BOM 없음). RAM 15.5GB(다른 에이전트 동시 실행).
- 끝에 `tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py` 를 돌린다. 이 공유 티켓은 고치지 않는다.

### 보고
- 모바일 손해율 카드 변경 요약, 제거한 것(짚은 시점 열·터치 가이드), 회사 수 상한 처리, 색 규칙 적용 결과, 확인한 조합(곡선이 다른 조합·비슷한 조합 각 1, 다크 1)과 375px·데스크톱 비교 스크린샷 경로, 콘솔 404 원인, `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
디자이너 반영 완료(2026-10-11, designer Sonnet, 약 15분, 토큰 210k): compare.html 모바일(640px 이하) 손해율 카드를 안 A(겹침 curve, 선 끝 라벨, 회사·현재가치 표)로 교체, 짚은 시점 열·터치 가이드 제거, 4선 상한 코드. 데스크톱 불변. 색은 데스크톱과 같은 선택 순서 팔레트(compare 에 회사 키컬러 없음). 후속: panel_compare.json loss_curve.note 문구 중립화(빌더), 선 대비 2.1~2.6:1 owner 확인 큐.
