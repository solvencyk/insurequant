---
from: orchestrator
to: designer
created: 20261012T1220Z
status: open
route: feature
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 결정(2026-10-12 채팅, 이 티켓이 우선): 신종자본증권이 기본자본형인지 보완자본형인지 분류 판단이 들어가는 숫자는 「건조하게 뽑을 수 있는 숫자가 아니」라서 화면에서 내린다. 원문: 「지금 당장은 도넛 자체를 내려. 걍 시점별 자본성증권 발행현황 그래프(밑에 신종자본 + 위에 후순위채 형태로 누적그래프)로 바꾸자. forward outlook도 아예 내리고.」 이전 티켓 `20261012T1100Z`(라벨)·`20261012T1155Z`(큼직한 셀 2개)와 충돌하는 부분은 **이 티켓이 우선**한다.

### 해 줄 것 (`K-ICS.html`; `index.html`·`공시보고서.html`·`compare.html` 등에 같은 영역·문구가 있으면 `grep` 으로 찾아 함께)
1. **소진율 도넛(기본자본·보완자본) 영역을 화면에서 제거**한다(`kics_tier1_utilization.json`·`kics_tier2_utilization.json` 의 소진율 숫자·`100%+`·`발행 없음`·`—` 표기 등 도넛 관련 표시 전부). 데이터 파일·xlsx 는 건드리지 않는다(내리는 것은 화면뿐).
2. **Forward Outlook(자본비율 전망) 영역을 완전히 제거**한다(대체 그래프 없음). 섹션 네비게이션 칩·`data-share-section`·목차·앵커·다른 페이지에서 가는 링크·`tests/test_deploy_assets.py` keep-list 에서 `kics_forward_capital.json` fetch 를 빼야 하면 그에 맞게(파일 자체는 지우지 않는다 — 삭제 여부는 별도 결정).
3. 그 자리에 **「자본성증권 발행현황」 누적 막대(시점별)**: 가로축 = 시점(공시시점, 데이터가 있는 모든 시점), 세로 = 억원, **아래 신종자본증권 + 위 후순위채** 누적(stacked), 값이 없는 시점은 막대 없음. 제목·범례는 공시 표기 그대로(`신종자본증권`·`후순위채`), 기본자본형/보완자본형 구분·소진율 계산 표시는 **하지 않는다**. 회사 선택은 페이지의 기존 회사 선택을 따른다. 음수 해당 없음. 툴팁에 시점·tier·금액(억). 색은 기존 토큰/`currentKey` 계열 재사용.
4. 그 차트 **아래에 큼직한 셀 2개**(앞 티켓 `1155Z` 내용 그대로: `신종자본증권`·`후순위채`, 맨 위 가장 큰 글씨 = 가장 최근 발행금리 `x.xx%`, `총발행액 : x,xxx억 ('23~)`, `콜 상환 도래일 : YYYY-MM-DD (x,xxx억)` 가장 가까운 한 건만; 값 없으면 `—`). 도넛 밑 주석 문구는 `?` 팝오버 안으로만(화면 설명 문장 금지).
5. **데이터**: 시점별 누적 막대의 값은 publishing 티켓 `20261012T1210Z` 가 만드는 JSON(`capital_securities_timeline`; 필드 명세는 그 티켓·`docs/changelog_publishing.md` 맨 위)에서 읽는다. 큼직한 셀의 `securities_summary` 는 티켓 `1150Z` 가 만든다. **필드가 아직 없으면 명세대로 구현하고 커밋이 올라오면 실제 값으로 점검**, 구판(필드 없음)에서는 해당 영역을 숨긴다(빈 상자·오류 금지). 데이터 인라인 금지(fetch), 새 fetch JSON 은 배포 keep-list 에 등록(`tests/test_deploy_assets.py`).
6. 점검: 헤드리스(`?iq_internal=1`)로 한화생명·메리츠·후순위채만 있는 회사 1곳·재보사(스위스리, 발행 없음) 확인 — 1280/375px, 다크 모드, 콘솔 오류 0, 섹션 공유 이미지 정상, 제거한 섹션 흔적(빈 간격·죽은 앵커·죽은 칩) 0. `tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py`·`tests/test_prepush_scope.py`·`tests/test_share_screenshot.py` 한 번에 하나씩 끝까지.

### 규칙
- 쓰는 파일: `K-ICS.html`(+ 위 grep 으로 찾은 HTML)·`tests/test_deploy_assets.py` keep-list 정도. 마스터·xlsx·`public_exports/`·JSON 수정 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다. PC 가 느리니 시험은 한 번에 하나씩 끝까지.

### 보고 (3~5줄 존댓말)
- 제거한 영역·바뀐 줄, 새 차트·셀 확인 회사, 실제 값 점검 여부, 시험 결과, 커밋 해시. `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
