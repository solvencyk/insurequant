---
from: orchestrator
to: designer
created: 20261012T1155Z
status: open
route: feature
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅): 「지금 소진율 도넛 밑에 주석으로 주절주절 적힌 내용들을, 소진율 도넛 밑에 큼직한 셀 2개 만들어서 요약정보를 보여주자. 신종자본이 기본인지 보완인지 분류 이슈는 헷갈리니까 여기서는 신종자본, 후순위채 각각에 한 셀씩.」 「콜 상환 도래일은 제일 콜만기 가까운 놈 하나만.」 목적: 각 보험사가 지금 자본을 차환 발행하려면 비용이 얼마나 드는지 보이게 하는 것.

### 해 줄 것 (`K-ICS.html` 의 소진율 도넛 영역; 앞 티켓 `20261012T1100Z` 라벨 작업을 이어서)
1. **도넛 밑 주석 문구를 걷어낸다**(「주절주절」 = 도넛 아래 설명·부제·메모 줄 전부; 필요한 설명은 기존 `?` 팝오버 안으로만 옮기고 화면에는 남기지 않는다. 앞 티켓에서 이미 정한 도넛 캡션·숫자 줄은 owner 가 이 지시로 대체한 것이니 이 지시를 우선한다 — 도넛 자체와 소진율 숫자·`100%+` 표기는 그대로).
2. 도넛 아래에 **큼직한 셀 2개**(왼쪽 `신종자본증권`, 오른쪽 `후순위채` — 제목은 공시 표기 그대로; 기본자본형/보완자본형 구분 표시는 하지 않는다). 각 셀 안:
   - **맨 위 가장 큰 글씨**: 가장 최근 발행금리 `x.xx%`
   - 그 밑: `총발행액 : x,xxx억 ('23~)`
   - 그 밑: `콜 상환 도래일 : 20xx-xx-xx (x,xxx억)` — 가장 가까운 콜 **한 건만**
   - 값이 없으면(해당 증권 없음) 셀은 유지하고 가운데 `—`(재보사 등; 문구 새로 짓지 말 것).
3. **값은 새 JSON 필드를 읽는다**: `kics_tier1_utilization.json`·`kics_tier2_utilization.json` 회사 행의 `securities_summary` = `{ as_of, hybrid:{latest_coupon_pct, latest_issue_date, issued_since_2023_eok, next_call_date, next_call_eok}, subordinated:{같은 5개} }` (tier 객체 null = 해당 증권 없음; 필드 null = 해당 없음). 이 필드는 publishing 티켓 `20261012T1150Z` 가 만든다 — **그 커밋이 올라올 때까지 기다리지 말고 명세대로 구현**하고, 커밋이 들어오면(`git log -- kics_tier1_utilization.json`) 실제 값으로 점검한다. 필드가 아직 없는 구판 JSON 이면 두 셀 영역을 숨긴다(오류·빈 상자 금지).
4. 숫자 형식: 금리 `x.xx%`, 금액 `x,xxx억`(천 단위 쉼표, `억원` 아님), 날짜 `YYYY-MM-DD`. 툴팁(`title`/`?`)에 `latest_issue_date`·`as_of`("2026-06-30 기준") 정도만. 데이터 인라인 금지. 모바일 375px 에서 셀 2개가 세로로 쌓여도 깨지지 않게(큰 글씨 줄바꿈 금지), 다크 모드.
5. 점검: 헤드리스(`?iq_internal=1`)로 한화생명(신종 외화 6.30%·콜 도래일), 메리츠, 후순위채만 있는 회사 1곳, 재보사(스위스리) 1곳, 삼성생명을 1280px/375px 로 확인, 콘솔 오류 0. `tests/test_deploy_assets.py`·`tests/test_push_gate_wiring.py`·`tests/test_prepush_scope.py`·`tests/test_share_screenshot.py` 한 번에 하나씩 끝까지.

### 규칙
- 쓰는 파일: `K-ICS.html`(필요 시 index.html 의 같은 영역). 마스터·xlsx·`public_exports/`·JSON 수정 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다. PC 가 매우 느리니 시험을 건너뛰지 말고 한 번에 하나씩.

### 보고 (3~5줄 존댓말)
- 바뀐 줄·확인한 회사·실제 값 점검 여부(필드 커밋 전후)·시험 결과·커밋 해시. `TODO_designer.md` Status + `docs/changelog_designer.md`.

## 답변 (recipient 작성 — 처리 후)
