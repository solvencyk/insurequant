---
from: orchestrator
to: downloader
created: 20260911T0115Z
status: resolved
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

**진행 메모 (orchestrator 대행, 2026-09-12 01:15 KST) — 미완, `status: open` 유지.**

- 항목 1(서울보증 6분기 PDF): **이 PC 에서 외부 443 이 막혀 수집 불가.** 01:0x 에 `https://www.sgic.co.kr/...CCGIRI010101F01` 이 한 번 200 을 준 뒤
  01:10:31~01:11:21 6회 연속 `curl: (7) Failed to connect ... port 443` (github.com 도 동일 000) — 보안에이전트/VPN 차단 상태.
  downloader 에이전트는 100분간 산출 0(python/브라우저 프로세스 0개, 첫 문장에서 정지)이라 kill 했다. 네트워크가 열리면 재발주.
- 항목 2(KR0079 2023.2Q MD 미변환): raw 무결성 확인(58p·4,859자·83자/p·"지급여력" 24회, 이미지/벡터 렌더 PDF) 후
  `inbox/parser/20260912T0115Z__downloader__KR0079_2023.2Q__docling_md_missing_image_pdf.md`(route reparse, lane kics) 로 이관.
- 항목 3(정정본 병존 구조): 미착수 — 네트워크 무관한 코드 작업이라 다음 downloader 라운드에서 항목 1 과 같이 처리.

## 종결 (owner 확정, 2026-09-12)

- 항목 1: **owner 가 서울보증 공시 페이지를 직접 확인 — 과거 연도(2023·2024) 분기 경영공시를 회사가 자체적으로 게시하지 않음.** KR0150 2023.1Q~2023.3Q·2024.1Q~2024.3Q 6분기는 **원문 부재**로 확정(파싱 실패·미수집 아님). IFRS17_BS 의 해당 6분기 코어 결측은 정당 결측.
- 항목 2: parser 티켓 `inbox/parser/20260912T0115Z__downloader__KR0079_2023.2Q__docling_md_missing_image_pdf.md` 로 이관 완료.
- 항목 3(정정본 병존 구조): `TODO_downloader.md` Active follow-ups 로 이월(네트워크 무관 코드 작업).
