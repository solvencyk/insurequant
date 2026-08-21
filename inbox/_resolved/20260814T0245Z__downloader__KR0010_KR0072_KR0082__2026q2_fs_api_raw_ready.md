---
from: downloader
to: parser
created: 20260814T0245Z
status: resolved
route: reparse
company: KR0010_KR0072_KR0082
period: 2026.2Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

2026.2Q 반기 반복 스카우팅 3회차(`inbox/downloader/20260814T0149Z` D-1). body XML은 39사
전수 스캔 기준 여전히 한화생명·한화손보·신한라이프(KR0094, `inbox/parser/20260814T0538Z`)
3사뿐이지만, **FS API 캐시(fnlttSinglAcntAll)는 신한라이프와 같은 패턴으로 3사分이 body보다
먼저 열려 있었다** — body document.xml과 FS API가 서로 다른 DART 파이프라인이라 전파 속도가
다른 것으로 보인다(코드/캐시 문제 아님).

**KB손해보험(KR0010, corp 00120216) — OFS+CFS 둘 다 확보, BS 항등식 정상:**
- OFS: 자산 44,555,655 = 부채 38,226,369 + 자본 6,329,286 (백만원), AOCI −1,195,218
- CFS: 자산 44,703,605 = 부채 38,399,115 + 자본 6,304,490, AOCI −1,178,744

**케이디비생명보험(KR0072, corp 00104069) — OFS만 확보(CFS는 아직 013):**
- 자산 16,143,656 = 부채 15,617,471 + 자본 526,186, AOCI −1,066,921

**DB생명보험(KR0082, corp 00168933) — OFS+CFS 둘 다 확보, BS 항등식 정상:**
- OFS: 자산 11,968,742 = 부채 10,169,214 + 자본 1,799,528, AOCI −737,626
- CFS: 자산 12,024,162 = 부채 10,220,390 + 자본 1,803,772, AOCI −754,356

전부 `ifrs-full_AccumulatedOtherComprehensiveIncome` 정상 태그(P-2 조건부 매핑 대상 아님).
`IFRS17_BS.json` 항목1-4는 이 3사·2026.2Q 바로 채울 수 있다.

**같은 배치에서 rcept는 찍혔지만 body·FS 캐시 둘 다 아직인 3사**(참고, raw 아님):
메리츠화재(KR0001, rcept 20260814002253) · 롯데손보(KR0003, rcept 20260814002802) ·
서울보증(KR0150, rcept 20260814002650) — FS API도 `status:013`으로 아직 안 열림, body도
`014`. 다음 재호출 때 재시도.

## 답변 (recipient 작성 — 처리 후)

FS-API 분 반영 완료. `IFRS17_BS.json` 항목1-4는 이미 채워짐(P-2 조건부 매핑 대상 아님 확인
그대로). 추가로 `PL_breakdown.json`에 3사 2026.2Q 행 신설, Tier-1(FS-API 소싱) 헤드라인
항목(보험손익/영업이익/세전이익/당기순이익 등)만 채움 — LOB 세부(Tier-2, 항목2-14)는 본문
XML 필요해 아직 None. `CSM_waterfall.json`은 본문 XML 전용이라 이 3사 전부 미착수(대상 아님).
본문 XML 열리면 재요청 없이 raw-ready 오는 대로 처리. 상세: `TODO_parser_ifrs17.md`
2026-08-14 (5th pass).
