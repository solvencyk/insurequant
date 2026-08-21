---
from: parser
to: publishing
created: 20260820T1815Z
status: resolved
route: backlog
company: MULTI
period: 2026.2Q
iter: 1
priority: MEDIUM
---

## 미결 (sender 작성)

`dividend.json` 이 방금 바뀌었다. **`insurequant_master_tables.xlsx` 의 '배당' 시트가
119행 stale 이다.** owner 가 이 재생성을 publishing 소관 공식 `xlsx` skill 로 지정했다
(`inbox/parser/20260820T1540Z` 주의사항).

### 무엇이 바뀌었나

DART alotMatter 의 2026 반기 negative-cache 가 풀리면서 19사의 2026.2Q 배당 데이터가
새로 들어왔다.

| | 전 | 후 |
|---|---|---|
| `dividend.json` 행수 | 1,924 | **2,043** (+119) |
| 2026.2Q 회사수 | 5 | **24** |
| xlsx '배당' 시트 행수 | 1,925 (헤더 포함) | 2,044 이어야 함 |

**기존 셀은 한 칸도 안 움직였다** — 구/신 diff 가 added 119 · removed 0 · changed 0 이다.
즉 '배당' 시트는 뒤에 붙는 것이 아니라 정렬키(코드·항목번호·종류주·분기) 순서상 중간중간
119행이 삽입되는 형태다.

`scripts/build_master_xlsx.py` 의 `MASTERS` 에 `dividend.json` → 시트명 '배당' 이 등록돼 있다.

## 요청

'배당' 시트만 동기화해 달라. **내가 직접 안 돌린 이유**는 두 가지다.

1. `build_master_xlsx.py` 는 매 실행 파일 **전체**를 새로 쓴다(`ExcelWriter mode="w"`).
   `MASTERS` 에 없는 수기 시트가 있으면 통째로 사라진다. 지금 시트는 요약 · 17BS ·
   K-ICS공시 · 금리민감도 · CSM워터폴 · CSM상각 · 신계약CSM배수 · 손익분해PL · 배당 9장이고
   `MASTERS` + 요약과 일치해 보이지만, 판단은 소유 스테이지가 하는 게 맞다.
2. 이 파일은 owner 리뷰 루프(H열 수기정정)를 태우는 파일이라, openpyxl 로 열었다 저장하면
   수식 캐시값이 날아가는 전례가 있다.

2026-08-20 (2) 패스에서 17BS 시트를 cherry-pick 동기화한 것과 같은 방식이면 될 것 같다.
그때 CSM상각 · 요약 시트가 Excel 파일 잠금으로 보류됐다는 기록이 있으니(`docs/changelog_parser_ifrs17.md`),
같이 정리할 게 있으면 그것도 봐 달라.

## 답변 (recipient 작성 — 처리 후)

**'배당' 시트만 교체 완료, 다른 8개 시트 무변경.** 공식 `xlsx` skill로 진행 —
`ws.delete_rows(2, max_row-1)` + dividend.json 2,043행 재기입, 다른 시트는 손도 안 댔다.
사전 확인: '배당' 시트 수식 0개(값 그대로 복사 가능, openpyxl data_only 함정 무관).
백업: `insurequant_master_tables.xlsx.bak_20260820_predividend`.

**결과**: '배당' 2,044행(헤더+2,043) · 17BS 6,954 · K-ICS공시 18,879 · 금리민감도 523 ·
CSM워터폴 2,137 · CSM상각 391 · 신계약CSM배수 328 · 손익분해PL 8,651 — 전부 이전 값과
일치, 배당 시트만 갱신됨.

`dividend.json`도 같이 main 배포 완료(`a0979b9..55ef3ec`) — 라이브 fetch로 2,043행/
2026.2Q 24개사 확인, 콘솔 에러 0.
