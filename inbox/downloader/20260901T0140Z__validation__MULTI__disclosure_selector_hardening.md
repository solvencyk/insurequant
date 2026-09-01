---
from: validation
to: downloader
created: 20260901T0140Z
status: open
route: refetch
company: MULTI
period: 2026.2Q
lane: kics
iter: 1
---

## 미결 (sender 작성)

2026.2Q 라운드에서 **세 회사가 직전 분기 PDF 를 그대로 받아왔다** — KR0011 DB손해 ·
KR0029 AIG손해 · KR0150 서울보증. 셋 다 재수집으로 데이터는 복구됐고 해당 티켓 3건은
`_resolved/` 로 종결했다(`20260831T111450Z` x2, `20260831T1049Z`). **남은 것은 재발 원인인
셀렉터/파라미터 고정이다.** 세 티켓 모두 이 항목을 "선택" 또는 "downloader 소관"으로 남긴 채 닫혔다.

### 실측 (2026-09-01, `docs/agents/source-catalog.yaml`)

| 회사 | 줄 | 현재 값 | 왜 매 분기 재발하나 |
|---|---|---|---|
| KR0011 DB손해 | L72 | `xpath: '//*[@id="content"]/.../ul/li[1]/a'` | 목록의 **첫 항목 위치 고정** — 새 분기가 추가돼도 옛 항목을 가리킬 수 있음 |
| KR0029 AIG손해 | L78 | `url2: ...&pancId=15467` | `notes` 에 "pancId varies per quarter" 라고 적혀 있는데 **값은 1분기 것으로 하드코딩** |
| KR0150 서울보증 | — | 사이트가 다운로드 링크 5개에 `id="test1"` 중복 사용 | 고정 xpath 가 항상 첫(1분기) 링크를 집음 |

### 요청

분기 라벨("상반기"/"2분기"/"26.2Q") 텍스트 매칭 등 **위치가 아니라 내용으로 고르는 선택자**로
바꾸고, `pancId` 류 분기별 파라미터는 목록 페이지에서 매번 해석하도록 할 것.

### 지금 안전한 이유 (급하지 않은 근거)

`scripts/validate_disclosure_freshness.py`(2026-08-31 신설)가 `scripts/prepush_check.py` L94
도메인 게이트 묶음에 배선돼 있고, 그 exit code 가 L228 `blocked = ... or n_dom ...` 로 흘러
**재탕이 다시 들어오면 push 가 막힌다**. 2026-09-01 10:18 KST 실행 결과
`[FY2026_Q2] RED=0 YELLOW=0 GREEN=39`. 즉 조용한 통과는 더 이상 불가능하고, 이 티켓은
"매 분기 사람이 손으로 재수집하는 일" 을 없애는 것이 목적이다.

## 답변 (downloader 작성 — 처리 후)
