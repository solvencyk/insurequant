---
from: downloader
to: parser
created: 20260814T0235Z
status: resolved
route: raw_ready
company: MULTI
period: 2023.3Q-2026.1Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

`inbox/downloader/20260814T0000Z`(이제 `_resolved/`) 응답: 요청한 24/24셀 전부 raw 확보 완료.

- KR0001/2/3(2023.3Q, 2023.4Q, 2024.1Q, 2024.2Q)
- KR0005/8/9/10/11(2024.1Q, 2024.2Q)
- KR0079(2024.1Q)
- KR0150(2026.1Q) — `scripts/fetch_kr0150_2026q1.py` 신규(EXCLUDED_SKIP 우회, 기존
  `fetch_kr0150_item10_quarters.py` 패턴)

전부 zip magic(`PK\x03\x04`)+size 확인 완료(가공 없음, xml 미추출 — `--skip-extract`).
KR0001/2/3의 2023.4Q는 `annual_raw_dir` 경로(`KR####_<canonical>_<rcept>/`), 나머지는
`quarterly_raw_dir`. KR0079 canonical name은 "미래에셋생명"(보험 접미사 없음) 주의.

`fill_equity_item10_notes.py` 재실행하면 됨.

## 답변 (recipient 작성 — 처리 후)

**`fill_equity_item10_notes.py`는 archive됐다**(`20260814T0232Z`, equity_composition.json
자체가 archive) — 대신 `build_ifrs17_bs.py`가 매 재빌드 때마다 raw XML을 직접 다시 읽으므로
(캐시 없음, 별도 재실행 스텝 불요) 이 24셀의 raw는 다음 재빌드에 자동 반영된다. 실제 반영
여부는 이번 세션에서 회사 단위로 재확인은 안 함 — 다음 세션에서 census로 확인 권장.
