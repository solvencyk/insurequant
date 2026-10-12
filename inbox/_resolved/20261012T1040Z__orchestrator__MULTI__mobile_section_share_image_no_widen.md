---
from: orchestrator
to: designer
created: 20261012T1040Z
status: resolved
route: fix
company: MULTI
period: MULTI
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅, 스크린샷 첨부): 모바일에서 섹션 「공유」(이미지 저장)를 누르면 「테이블 전체를 다 보여주려다」 이미지가 못생겨진다. 증상: IFRS17 · 손해율 가정 · 뮌헨 섹션 이미지가 약 1000px 폭으로 넓어지는데 **차트(canvas)는 원래 폰 폭 그대로** 왼쪽 1/3 만 차지하고 오른쪽이 텅 비며, 아래 표만 넓게 펼쳐진다.

원인(확인함): `theme.js` 의 섹션 스크린샷 `o.widen` 경로(약 583~588행·628~638행)가 가로 스크롤되는 표(`.table-container, .table-wrap`)의 `scrollWidth - clientWidth` 만큼 이미지 폭(`cw = cw0 + extra`)과 복제본 섹션 폭을 늘린다. 이미 그려진 차트 canvas 는 늘어난 폭에 맞춰 다시 그려지지 않는다.

### 해 줄 것
1. **좁은 화면(폰·`W < 520` 또는 coarse pointer)의 섹션 이미지는 widen 을 하지 않는다**: 이미지 폭 = 화면에서 보이는 섹션 폭 그대로. 차트는 화면 그대로 폭을 가득 채우고, 가로로 스크롤되는 표는 화면에 보이는 열까지만 찍는다(스크롤 영역이 잘린 채로 — 지금 화면과 같은 모습). 새 안내 문구는 만들지 않는다. 데스크톱(넓은 화면)은 widen 이 필요 없으니 지금 동작 그대로.
2. 이 변경이 **다른 섹션 이미지**(표 없는 섹션·모바일 K-ICS·index·compare)를 깨지 않는지 같은 방식으로 3~4곳 확인. 페이지 전체 이미지 경로(`o.widen` 없음)는 건드리지 않는다.
3. 시험: `tests/test_share_screenshot.py`(있으면)가 widen 전제를 검사하면 새 동작에 맞게 고친다(요구 변경이니 시험도 같이). 375px 헤드리스로 IFRS17 · 손해율 가정 섹션 이미지를 만들어(캡처는 로컬 canvas 에서만, 업로드 없음) 차트가 폭을 채우는지 확인. `tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py`·`tests/test_prepush_scope.py` 한 번에 하나씩 끝까지.
4. **이 수정은 IFRS17 예실차 섹션 작업(티켓 `20261012T1000Z`)보다 먼저 끝내고 `theme.js` 만 따로 커밋한다**(커밋 메시지에 `mobile section share: no widen` 포함). owner 가 바로 배포하려 한다.

### 규칙
- 쓰는 파일: `theme.js`(+ 해당 시험). `privacy.html`·`scripts/appsscript/`·`compare.html` 은 건드리지 않는다. 마스터·xlsx·`public_exports/` 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 파일 제외), 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다.

### 보고 (2~4줄 존댓말)
- 바뀐 줄·확인한 화면·커밋 해시. `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
처리 완료(2026-10-12, 커밋 18bd037). theme.js: 폰(화면 폭 520px 미만·터치)의 섹션 공유 이미지는 표 폭만큼 넓히지 않고 화면 폭 그대로(375px 뮌헨 손해율 가정·삼성생명 NB·코리안리 예실차 모두 차트가 폭을 채움, 이전 약 1000px). 데스크톱 1280px·페이지 전체 이미지는 그대로. test_share_screenshot 1개 추가.
