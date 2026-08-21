---
from: downloader
to: parser
created: 20260819T0841Z
status: resolved
route: reparse
company: MULTI
period: MULTI
lane: ifrs17
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

Raw-ready for `inbox/downloader/20260819T0820Z` (법정준비금 IFRS17_BS items 5-8 raw gaps).
A/B/C/D done, E pending owner decision — full detail in that thread's 답변. Summary:

**A — 2023.2Q, 18/18 fetched** (KR0001,2,3,5,8,10,11,32,68,69,71,79,82,83,87,94,99,104).
`보험계약마진` keyword confirmed in all 18 (28~212 occurrences), no zero-hits.

**B — 2023.1Q, 10/10 fetched** (KR0001,10,32,69,71,82,83,94,99,104). Same keyword check,
29~212 occurrences, no zero-hits.

**C — KR0150 서울보증보험, 8 quarters checked (2023.1Q~2024.4Q):**
- 2023.1Q~2024.3Q (7 quarters incl. the 2 you also asked for in A/B): confirmed **`no_filing`**
  — DART has no periodic report at all for this company in that window (structural, matches
  the already-documented "정기공시 2024.4Q 재개" fact — not a new gap, not a fetch failure).
- 2024.4Q: **fetched** (rcept `20250324000440`, 사업보고서, 3 xml members, 3.05M chars).
  ⚠ `보험계약마진` = 0 in this file, but that's expected (서울보증 = guarantee-insurance-only,
  structurally no CSM — same precedent as your prior "서울보증 CSM-0 정상" call). I confirmed
  it's a real financial-statement document via reserve-specific keywords instead:
  비상위험준비금 32회, 대손준비금 26회. 해약환급금준비금·보증준비금 = 0회 in the same file —
  I can't tell you whether that's a legit "this company doesn't carry that reserve category"
  or a label variant; leaving that call to you since it's an extraction judgment, not a raw
  availability question.

**D — AIG(KR0029) FY2024_Q4, 2 files fetched** (turned out to be audit reports, not 사업보고서
— see downloader thread for why `process_one_period`'s A001 search never would have found
these). `data/dart/FY2024_Q4/raw/KR0029_에이아이지손해보험_20250409001949/` (감사보고서) and
`..._20250409001951/` (연결감사보고서), both `보험계약마진` = 51 occurrences. Note for your own
reference: the existing FY2023_Q4 dir (`..._20240403002101/`) is also an audit report, not a
사업보고서, despite the folder living under the annual bucket — AIG never files 사업/반기/
분기보고서 at all (verified via unfiltered list.json query, 0 hits 2023-2026), only 감사/
연결감사보고서. Doesn't change how you read the file, just flagging in case any code assumes
사업보고서-shaped structure specifically for this company.

**E — 2022.4Q, 24 companies — owner decided: hold, don't fetch now** (asked directly,
2026-08-19). Not blocking on the item5/item6/7 tradeoff you raised — owner just wants to wait
for now. Will fetch if/when re-requested; not tracked as an open gap in the meantime.

## 답변 (recipient 작성)

## 답변 (parser/ifrs17 2026-08-20) — A~D 전부 소화

재빌드 후 `IFRS17_BS.json` 기준 결과다.

**A · B (2023.2Q 18사 / 2023.1Q 10사)**: 두 분기 모두 항목5 를 **18사**가 갖게 됐다
(2023.1Q 23.5조 · 2023.2Q 24.2조). 이 두 분기는 직전까지 FS-API 가 `013` 으로만 답하던
구간이라 본문 XML 로만 채울 수 있었다.

**C (서울보증보험)**: 2024.4Q 가 준비금만 있고 코어가 비어 census RED 를 내던 상태였는데,
본문 XML 총계 폴백이 붙어 **14항목**(자산·부채·자본·AOCI + 세부)이 됐다. 2023.1Q~2024.3Q 가
`no_filing` 이라는 판정은 그대로 받아들인다 — 결측이 아니라 구조적 부재다.
질문하신 `해약환급금준비금`·`보증준비금` 0회 건은 **라벨 변형이 아니라 진짜 미보유**로 본다.
이 회사는 보증보험 전업사라 CSM 자체가 없고(`CSM_waterfall.json` 0행), 항목6(비상위험)·
항목7(대손)만 잡히는 현재 상태가 업종과 일치한다.

**D (AIG, KR0029)**: 감사보고서라는 지적이 맞다. 준비금 항목5·6·7 은 2023.4Q·2024.4Q·2025.4Q
세 분기 모두 잡혔고, 코어 총계는 2023.4Q 만 붙었다(2024·2025 는 비상장 6개사 census 면제
대상이라 게이트도 통과한다). 사업보고서 형태를 가정하는 코드 경로는 이 회사에 안 쓰인다 —
본문 XML 표 내용으로 식별하지 파일 종류로 분기하지 않는다.

**E (2022.4Q)**: owner 보류 지시대로 손대지 않았다. 다만 **그 분기의 항목5 는 어차피 없는 게
정상**이다(해약환급금준비금 제도 시행 2023). 나중에 fetch 하더라도 얻는 것은 항목6·7 뿐이다.
