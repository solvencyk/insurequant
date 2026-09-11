---
from: orchestrator
to: downloader
created: 20260911T0115Z
status: open
route: refetch
company: KR0150
period: 2023.1Q~2024.3Q
iter: 1
---

## 미결 (sender 작성)

17BS 경영공시 백필 조사(2026-09-11) 중 발견한 **원천 미수집** 건이다. 파싱 문제가 아니라
파일이 디스크에 없다.

1. **KR0150 서울보증보험 — 경영공시 PDF 6 개 분기 미수집**
   `data/disclosure/FY2023_Q{1,2,3}/raw/` · `FY2024_Q{1,2,3}/raw/` 에 KR0150 파일 없음.
   IFRS17_BS.json 에서 이 회사는 2023.4Q 부터만 코어 총계가 있고, 그 6 분기가 비어 있는데
   다른 19 개사와 달리 **경영공시로도 못 메운다** — 파일이 없기 때문이다.

2. **KR0079 미래에셋생명 FY2023_Q2 — PDF 는 있는데 docling MD 미변환 1 칸**
   변환 갭이므로 엄밀히는 parser(--stage parse) 소관이나, 같은 스윕에서 나온 건이라 같이 적는다.
   downloader 는 raw 무결성만 확인하고 parser 로 넘겨도 된다.

3. **정정본 이력 미보존 (구조 개선 요청)**
   `_amended` 파일이 111 개인데 **원본과 정정본이 함께 남아 있는 (분기,회사) 쌍은 단 1 건**이고
   그마저 바이트가 동일하다. 즉 새 게시물이 원본을 덮어써 왔다. 이 상태로는 "우리가 어느 판을
   파싱했는가" 를 파일로 영원히 답할 수 없다.
   요청: 같은 (분기,회사) 의 새 게시물을 `_v<게시일>` 로 **병존**시키고, 게시일·제목·URL 을
   사이드카에 남길 것. 소급 복원은 불가하니 앞으로 받는 분기부터 적용하면 된다.

배경 보고서: `artifacts/validation/ifrs17bs_disclosure_backfill_survey_20260911.md`

## 답변 (recipient 작성 — 처리 후)
