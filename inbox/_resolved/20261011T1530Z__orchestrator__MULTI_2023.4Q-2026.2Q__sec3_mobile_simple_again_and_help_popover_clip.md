---
from: orchestrator
to: designer
created: 20261011T1530Z
status: resolved
route: feature
company: MULTI
period: 2023.4Q-2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-11 오후, 라이브에서 폰으로 확인): 
① 「보험계약부채 추이 그래프는 모바일에서 여전히 못생기게 나온다. 축에 단위가 너무 넓게 적히는 게 문제 같긴 하다. **모바일은 내가 전에 말한 대로 기말 CSM(주축, 막대)과 신계약 CSM(보조축, 꺾은선)만 보여주는 걸로 해라.**」 
② 「K-ICS.html 에서 ? 를 누르면 나오는 설명이 아래 섹션에 가려서 잘 안 보인다. 이거 수정해라.」
push·배포는 하지 않는다(커밋까지만; 오케스트레이터가 디자인 전용 브랜치에 반영 여부를 정한다).

### ① IFRS17.html 섹션 3 「보험계약부채 시계열」 — 모바일 단순형 재도입
- 이전 지시(`inbox/_resolved/20261011T0200Z…combo_mobile_simple_csm_line.md`)를 owner 가 한 번 취소(`…T0350Z…`: 데스크톱 콤보 그대로)했다가 **이번에 다시 단순형으로 확정**했다. 단순형 구현은 커밋 `da15845` 의 `IFRS17.html` 에 있었고 `244fd75` 에서 철회됐다 — 그대로 되살리지 말고, **`244fd75` 이후에 들어간 것(긴 설명 ? 팝오버, 「보험계약부채 시계열」 이름, 재작성 † 표시·사유 팝오버 등)은 유지**하면서 모바일 분기만 단순형으로 바꾼다.
- **좁은 화면(`max-width:640px`)에서만**: 막대 = 기말 CSM 잔액(주축, 0 에서 시작, 회사 키 컬러·없으면 사이트 에메랄드), 꺾은선 = 신계약 CSM(보조축). BEL·RA·PAA·발생사고요소·구성 미분리 막대/범례는 모바일 **차트**에서 뺀다(값은 아래 표에 그대로). 범례는 2개(CSM / 신계약 CSM)만. 데스크톱(641px 이상)은 지금 그대로.
- **축 단위 문제를 근본 확인**: owner 는 「축에 단위가 너무 넓게 적힌다」고 했다. 현재 모바일에서 y축·보조축 눈금 라벨이 얼마나 넓은지(예: 6~7자리 억원 숫자, 단위 접미) 실측해서, 모바일에서는 눈금을 조·천억 단위로 줄여 쓰거나(예: `12조`, `3,000억` → 짧은 형) 눈금 개수를 줄이고 `maxTicksLimit`·`ticks.callback` 으로 폭을 줄인다. 눈금 단위는 축 제목 한 줄(「조원」「억원」)로 한 번만 적는다. 음수는 △.
- 연도/분기 모드 둘 다, 라이트·다크, 재작성 3사(†)·사이드카 3사 안내·구성 없는 회사 안내가 단순형에서도 유지되는지 확인. 375px · 414px 에서 스크린샷 각 2장 이상.

### ② ? 도움말 팝오버가 아래 섹션에 가려지는 문제
- K-ICS.html 에서 「?」(`.iq-help-btn` → `.iq-help-pop`)를 누르면 설명 상자가 **바로 아래 섹션(패널)에 가려진다.** 원인을 확인한다(후보: 패널/표 컨테이너의 `overflow:hidden|auto`·`contain`·`transform`·`z-index` 로 생긴 쌓임 맥락, 다음 `.panel` 이 위에 그려짐, 모바일에서 `position:static` 전환 시 폭·위치). **K-ICS 뿐 아니라 같은 `.iq-help` 를 쓰는 IFRS17.html · compare.html 도 같은 증상인지 같이 본다.** 공통 원인이면 `common.css` 에서 고친다(`.iq-help-pop` 의 `z-index`, 패널의 쌓임 맥락 정리 등 — 패널 간 겹침·sticky 헤더·공유 메뉴와 충돌하지 않게).
- 확인 대상: K-ICS 의 모든 ? (자본비율 Forward 가정, 듀레이션 표 기준·산식, 금리 민감도 표 기준 등) × 데스크톱 1280px · 모바일 375px × 라이트·다크. 팝오버가 화면 밖으로 잘리는 경우(오른쪽/하단)도 같이 정리. 키보드 포커스·Esc 닫기·터치 탭 동작은 지금 그대로.

### 규칙
- `IFRS17.html` · `K-ICS.html` · `compare.html` · `common.css` · `theme.js` 만 수정. 마스터·패널 JSON·xlsx·`public_exports`·게이트 금지. 서브에이전트 금지. 공용 Browser pane 은 쓰지 말고 headless 로 확인.
- 테스트 `tests/test_deploy_assets.py` · `tests/test_push_gate_wiring.py` · `tests/test_share_screenshot.py` 통과(공유 스크린샷 `RUN_SHARE_SHOT=1` 포함). 풀 훅·push·배포 금지. 커밋은 자기 파일만(명시 경로), 메시지 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. 이 공유 티켓은 고치지 않는다(오케스트레이터가 종결).
- 파이썬은 풀패스 `C:/Users/sangwook.cho/venvs/insurequant/Scripts/python.exe`, 스크립트 파일만(멀티라인 `-c`·맨 `python`·stdin heredoc 금지), UTF-8(BOM 없음).

### 보고
- ① 모바일 단순형 구성·축 라벨 폭 실측과 해결 방식·스크린샷 경로, ② 원인과 수정 위치(공통/개별)·확인한 ? 목록, 테스트 결과, `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
(designer 44c7afc·6f92fb0, orchestrator 종결 2026-10-11) ① IFRS17 섹션 3 모바일(640px 이하) = 기말 CSM 막대(주축)+신계약 CSM 선(보조축)만, 눈금 숫자만·단위는 축 제목 1회(축 폭 좌 61→34~43px·우 64→34~55px, 그림 영역 184→245px), 데스크톱 불변. ② ? 팝오버 가려짐 원인 = common.css `.panel.revealed` 의 `animation … forwards` 가 패널마다 쌓임 맥락을 남긴 것 → forwards 제거 + 팝오버 z-index 1950 + 하단 잘림 시 위로 뒤집기(theme.js). K-ICS·IFRS17 공통 원인, compare 는 재현 안 됨. 추가(owner): index 마켓맵 재보험·보증 그룹 면적 절반(RE_MIN_SHARE 0.18→0.07, 높이 246→122px)·「칸 크기는 이 업권 안에서만 비교」 삭제 — 부작용: 칸 이름 표시 5곳→2곳(나머지는 호버). 테스트 84 통과. push·배포 보류 중이며 디자인 전용 브랜치 `deploy/design-20261011` 에는 adeef08 로 반영.
