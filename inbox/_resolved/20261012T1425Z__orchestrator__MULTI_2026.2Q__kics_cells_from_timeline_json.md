---
from: orchestrator
to: designer
created: 20261012T1425Z
status: resolved
route: fix
company: MULTI
period: 2026.2Q
iter: 1
---

## 미결 (sender 작성)
owner 지시(2026-10-12 채팅): 소진율·전망 숫자(분류 판단이 들어간 값)를 공개에서 내린다. K-ICS 큼직한 셀 2개가 지금 `kics_tier1_utilization.json` 의 `securities_summary` 를 읽는데, 그 파일은 소진율 숫자도 담고 있어 비공개 대상이다(publishing 티켓 `20261012T1420Z`). **셀 값을 `kics_capital_securities_timeline.json`(채권별 슬림 목록)에서 클라이언트 계산으로 바꿔 `kics_tier1_utilization.json` fetch 를 없앤다.** 빨리(배포 대기 중).

### 해 줄 것
1. `K-ICS.html` 의 큼직한 셀 로직을 타임라인 JSON(`securities[code] = [{tier:'hybrid'|'subordinated', issue_date, call_date, coupon_pct, face_eok, outstanding_eok, as_of}]`)으로 계산: tier 별로 ⓐ 최근 발행금리 = 잔액이 남은 증권 중 `issue_date` 가 가장 늦은 증권의 `coupon_pct`(같은 날 여럿이면 금액이 큰 쪽; 잔액 0 인 증권은 제외) ⓑ 총발행액 '23~ = `issue_date >= 2023-01-01` 인 증권의 `outstanding_eok` 합 ⓒ 콜 상환 도래일 = `outstanding_eok > 0` 이고 `call_date >= as_of` 인 증권 중 **가장 이른 콜일 한 건**(같은 날 여러 건이면 금액 합), 금액 = 그 건의 `outstanding_eok`. 값이 없으면 지금처럼 `—`/영역 숨김. 표시 형식·툴팁은 지금과 같다.
2. **검증**: 한화생명·메리츠·현대해상·삼성생명·스위스리·교보라이프플래닛에서 **현재 화면 값(securities_summary 기반)과 새 계산 값이 같은지** 비교(다르면 원인 보고 — 타임라인에 상환 0 증권·잔액 기준일 차이가 있을 수 있음). `fetch('kics_tier1_utilization.json')` 와 관련 변수·주석을 걷어내고 `tests/test_deploy_assets.py` keep-list/fetch 검사를 그에 맞게 고친다(시험을 느슨하게 풀지 말고 정확히 갱신). 1280/375px, 다크, 콘솔 오류 0. 시험은 한 번에 하나씩 끝까지.
3. **이 수정만 먼저 커밋**(`K-ICS.html`·시험 파일만, 메시지에 `cells from timeline json` 포함)하고 바로 보고 — publishing 이 이 커밋을 기다려 `kics_tier1_utilization.json` 을 비공개로 돌린다.

### 규칙
- 쓰는 파일: `K-ICS.html`·`tests/test_deploy_assets.py`(필요 시 `tests/test_share_screenshot.py`). 마스터·xlsx·JSON 수정 금지. 커밋은 자기 파일만 명시 경로(`git add -A` 금지, 루트 개인 문서·`data/_derived/qoq_warn.json`·다른 에이전트 미커밋 제외), 끝에 `Co-Authored-By:` 줄. **push 금지.** 서브에이전트 금지. 이 공유 티켓은 고치지 않는다.

### 보고 (2~4줄 존댓말)
- 값 비교 결과·바뀐 줄·시험 결과·커밋 해시.

## 답변 (recipient 작성 — 처리 후)
처리 완료(2026-10-12, 커밋 1624aba): K-ICS 큼직한 셀 2개를 kics_capital_securities_timeline.json 에서 클라이언트 계산으로 바꾸고 kics_tier1_utilization.json fetch 제거(K-ICS.html·tests/test_deploy_assets.py). 한화생명·메리츠·현대해상·삼성생명·스위스리·교보라이프플래닛 18건 비교 차이 0, 1280/375px·다크 확인, 시험 3종 통과(deploy_assets 12; tier1·tier2·전망 fetch 금지 검사 포함). docs/changelog_designer·TODO_designer 갱신은 다음 문서 커밋.
