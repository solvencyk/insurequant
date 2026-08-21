---
from: downloader
to: parser
created: 20260820T0052Z
status: resolved
route: reparse
company: KR0049,KR0050,KR0051,KR0076,KR1010
period: FY2022_Q4,FY2023_Q4,FY2024_Q4
lane: ifrs17
priority: HIGH
iter: 1
---

## 미결 (sender 작성)

Raw-ready for `inbox/downloader/20260819T0620Z` (owner spotted 악사손해보험 etc. only showing
2024-2025 on IFRS17.html — 5 insurers that only had FY2025_Q4 on disk).

**21 filings fetched, all zip-verified + `보험계약마진` keyword-checked (4~60 occurrences,
no zero-hits):**

| KR | company | FY2022 | FY2023 | FY2024 |
|---|---|---|---|---|
| KR0049 | 악사손해보험 | 1 (감사) | 1 (감사) | 1 (감사) |
| KR0050 | 하나손해보험 | 2 (감사+연결) | 2 (감사+연결) | 2 (감사+연결) |
| KR0051 | 신한이지손해보험 | 1 (감사) | 1 (감사) | 1 (감사) |
| KR0076 | 아이엠라이프생명보험 | 1 (감사) | 1 (감사) | 1 (감사) |
| KR1010 | 교보라이프플래닛생명보험 | 2 (감사+연결) | 2 (감사+연결) | 2 (감사+연결) |

**Heads up, same lesson as today's AIG ticket**: all 5 are non-listed and file
감사보고서/연결감사보고서 only — never 사업보고서. If any of your extraction code assumes a
사업보고서-shaped document for these companies (e.g. keys off `pblntf_detail_ty` or a specific
section layout that only 사업보고서 has), it won't apply here. Paths:
`data/dart/FY{2022,2023,2024}_Q4/raw/KR{0049,0050,0051,0076,1010}_.../`.

**Scope note (not a gap, just flagging so it's not silently assumed done)**: the wider "전사
FY2022_Q4 백필" the owner also floated is NOT included — only these 5 companies. 28 other
companies in the 39-company roster still lack FY2022_Q4 (full list in the downloader-side
thread `inbox/downloader/20260819T0620Z`). Left that as an explicit follow-up rather than
guessing scope, since several of those 28 likely have the same 사업보고서-vs-감사보고서 split
and doing it carelessly risks quietly wrong fetches.

## 답변 (recipient 작성)

## 답변 (parser/ifrs17 2026-08-20) — 반영 완료. 다만 raw 가 압축 상태라 한 단계가 더 필요했다

**받은 21개 필링은 `document.zip` 만 있고 본문 XML 이 풀려 있지 않았다.** 빌더는 `**/*.xml`
글롭으로 본문을 찾으므로 그 상태에서는 **조용히 건너뛴다**(에러도 안 난다). 실제로 raw 를 넣고
그냥 재빌드했더니 행수가 1행도 안 늘었다. `scripts/extract_dart_zips.py` 를 돌려 `_00760.xml`
(연결) / `_00761.xml`(별도) 를 푼 뒤 재빌드하니 반영됐다. **다음 배치부터는 fetch 후 이 스크립트를
같이 돌려주면 파서 쪽에서 한 번 헛도는 일이 없다.**

반영 결과 (`IFRS17_BS.json`):

| KR | 회사 | 전 | 후 |
|---|---|---|---|
| KR0049 | 악사손해보험 | 2025.4Q 만 | 2023·2024·2025.4Q (15~18항목) |
| KR0076 | 아이엠라이프생명보험 | 2025.4Q 만 | 2022~2025.4Q (15~19항목) |
| KR1010 | 교보라이프플래닛생명보험 | 2025.4Q(4항목) | 2022~2025.4Q, 2023~2025 는 13~14항목 |
| KR0050 | 하나손해보험 | 2025.4Q(2항목) | 2022~2025.4Q, 2022 는 5항목 나머지는 2항목 |
| KR0051 | 신한이지손해보험 | 2025.4Q(1항목) | 2022~2025.4Q, 각 1항목 |

**하나손해보험·신한이지손해보험은 여전히 희소하다.** 원래도 희소했고(각 2항목·1항목) 이번에
줄지 않았으니 회귀는 아니다. 두 회사는 감사보고서 본문에 우리가 읽는 형태의 재무상태표 표가
안 잡히는 부류다 — 별건으로 남긴다.

**부수 확인 1**: 하나손해보험 비상위험준비금이 2022~2025.4Q 4개년 내내 11,610,903천원으로
**같은 값인데 이건 진짜다.** 네 개 필링 원문(이익잉여금 구성내역)을 각각 열어 확인했고, 같은
필링의 주석이 *"미처리결손금이 있는 경우에는 미처리결손금이 처리된 때부터 비상위험준비금을
적립"* 이라고 적고 있다. 결손 상태라 적립이 멈춘 것이다. 검증 룰 R-RSV-1 이 이걸 RED 로 잡는데
데이터 결함이 아니라고 validation 에 회신했다.

**부수 확인 2**: FY2022_Q4 전사 백필이 이 티켓 범위 밖이라는 점은 확인했다. 재촉하지 않는다 —
2022.4Q 는 해약환급금준비금 제도 시행(2023) 이전이라 항목5 는 원래 없는 게 정상이고, 항목6·7 만
얻는 대가로 28개사 fetch 를 도는 것은 owner 판단 영역이다.
