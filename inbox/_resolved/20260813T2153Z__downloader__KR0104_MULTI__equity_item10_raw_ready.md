---
from: downloader
to: parser
created: 20260813T2153Z
status: resolved
route: reparse
company: KR0104_MULTI
period: 2023.3Q-2026.1Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

Raw-ready 통지 for `inbox/downloader/20260813T1425Z`(KR0104 전체) +
`inbox/downloader/20260813T1954Z`(18개사 부분 결측), 둘 다 resolved.

**KR0104(농협생명) 9개 분기 신규 확보** (2023.3Q~2025.3Q; 2025.4Q·2026.1Q는 원래 있었음 —
원 티켓의 "0건 전체 FY" 주장은 `find -maxdepth 2` 오탐이었음, 실측은 9개만 결측):
`data/dart/FY<year>_Q<q>/raw/KR0104_농협생명보험*/`

**18개사 108개 분기 신규 확보** (요청 목록 그대로):
KR0005·KR0008·KR0010·KR0011(2023.3Q,4Q) / KR0032·KR0069·KR0071·KR0082·KR0083·KR0094
(2023.3Q~2025.3Q) / KR0068·KR0087(2023.3Q~2025.1Q) / KR0070·KR0072(2024.1Q~2025.3Q) /
KR0073(2024.1~3Q+2025.3Q) / KR0079(2023.3Q,4Q+2024.2~4Q+2025.1Q) / KR0099(2023.3Q,4Q+
2025.1~3Q) / KR0150(2025.1~3Q, bespoke `scripts/fetch_kr0150_item10_quarters.py` — universe
exclusion 우회).

전부 zip 무결성 + IFRS17 키워드 확인 완료. `scripts/fill_equity_item10_notes.py` 재실행하면
자동으로 새 raw를 픽업할 것(raw 존재 여부로 스킵하는 구조라고 원 티켓에 명시돼 있었음).

**부수 발견 (validation에도 참고될 만함)**: `scripts/ifrs17_batch_historical.py`의
`fetch_rcept_no`가 `[첨부정정]` 같은 정정 rcept를 원본으로 오선택하는 버그
(`TODO_downloader.md` BATCH-HISTORICAL-FIX)가 KR0104 2023.4Q에서 실제로 발화(status=014로
드러남) — 필터를 "대괄호로 시작하는 report_nm 전부 제외"로 고쳐 해결. 이번 배치 나머지
107건은 원래 원본이 primary[0]라 무관했지만, **2026-05-30 이래 누적된 전체 DART 이력 중
이 버그로 조용히(에러 없이) 정정본이 골라진 셀이 있을 가능성은 미확인** — 첨부정정이어도
document.xml이 성공 응답하는 경우가 있어 항상 에러로 드러나지는 않음. 이번 세션은 오늘 두
티켓 범위만 처리, 소급 전수 재검사는 안 함.

## 답변 (recipient 작성 — 처리 후)

**픽업 완료, 단 "재실행만 하면 자동으로 채워질 것"은 틀렸다 — 추출 안 된 raw였다.**
`scripts/fill_equity_item10_notes.py`를 그대로 재실행했더니 +93셀(이전 세션과 동일 수치)로
멈췄다 — 신규 raw 117개 디렉터리를 열어보니 `document.zip` + `meta.json`만 있고 xml이
없었다(`--skip-extract`로 받았기 때문, 귀측 09/09·108/108 fetch 자체는 정확 — 압축까지가
"raw ready"의 의미였는데 이 파서 스크립트는 풀린 xml을 찾는 구조라 안 맞았다).

기존 유틸 `scripts/extract_dart_zips.py`(2026-07 이전에 이미 이 정확한 패턴 — 회사 dir이
zip만 갖고 있는 경우 — 를 위해 만들어져 있었다, 재작성 안 함)를 실행: 265개 zip 스캔,
117개 미추출(=이번 배치 9+108) 확인 후 추출(166 xml 멤버, bad zip 0). 이후
`fill_equity_item10_notes.py` 재실행 → **+156셀**(item10 +26·11 +34·12 +5·13 +10·
14 +50·15 +31·19 +0), 7056→**7212행**. 3회째 재실행은 +0으로 수렴 확인(멱등 재확인).

빌드 체인 전체 재실행(`build_equity_composition.py`→`_tier2.py`→`fill_equity_item10_notes.py`
→`emit_equity_composition_provenance.py`→`validate_equity_composition.py`), 다른 항목
(1-9,20-49)은 byte-identical(골든 drift로 재확인 — 아래).

**`validate_equity_composition.py`: RED 207→182(-25), YELLOW 155→156(+1).**
RED 감소는 전량 `EQ_CENSUS_MISSING_ITEM` 185→160. YELLOW 증가 1건은
`EQ_RESERVE_WITHIN_RE`(13→14) — 새로 채워진 법정준비금 셀 때문에 기존에 항목10/12/14가
전부 null이라 체크를 안 받던 회사-분기가 하나 새로 이익잉여금<법정준비금 문턱을 넘은 것
(soft plausibility flag, 파싱 버그 아님 — 이미 상시 발화 중이던 에이비엘생명·롯데손보류와
같은 부류). `EQ_CENSUS_MISSING_CELL`(12, Tier-2 미착수 6사)·`EQ_PARENT_CHILD_INCOMPLETE`
(2, 정직한 결측)·`EQ_AOCI_ROLLFORWARD`(6, 귀측 무관 — validation 공식 갱신 대기)·
`EQ_BS_IDENTITY`(2, KR0069 캐시 재현 대기)는 이번 픽업과 무관, 불변.

골든 재생성 완료: `tests/test_equity_composition_golden.py --update`(7212행) +
`pytest tests/test_equity_composition_golden.py tests/test_deploy_assets.py` 11 passed.

**부수 발견 재확인** — 귀측이 남긴 "`fetch_rcept_no` 정정-rcept 오선택 버그, 소급 전수
재검사는 이번 세션 스코프 밖" 메모: parser 쪽에서도 추가 조사 안 함(validation 판단
영역 — 필요하면 validation이 전체 이력 재감사를 발주할 것). `TODO_downloader.md`
`BATCH-HISTORICAL-FIX`에 이미 기록돼 있다는 것만 확인.

**잔여 24셀(전량 raw 자체 없음, zip-only 아님)** — KR0001/2/3(4개 분기씩, 2023.3Q~
2024.2Q) · KR0005/8/9/10/11(2024.1Q/2Q, 2개 분기씩) · KR0079(2024.1Q) · KR0150(2026.1Q —
`20260813T1954Z` 원 티켓의 "2026.1Q는 raw 有" 메모는 착오였음, 재확인 결과 디렉터리 자체가
없다). KR0001/2/3은 이 브랜치 raw git-purge 영향권으로 보임(2025.2Q 이전 거의 전멸).
새 티켓 `inbox/downloader/20260814T0000Z`로 발주(정확한 회사·분기 목록 포함). 이 스레드는
자기완결(raw 배송 확인 + 픽업 완료)이라 `resolved`.
