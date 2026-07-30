---
from: downloader
to: parser
created: 20260730T0010Z
status: open
route: reparse
company: KR0087
period: 2026.2Q (상반기누적, FY2026_Q2)
rule: n/a
lane: ifrs17
iter: 1
---

## 미결 (downloader) — 동양생명 FY2026 상반기 IR 자료 raw 확보 (raw-ready)

2026.2Q 공시 스카우팅(owner 요청) 중 발견: 동양생명(KR0087)만 자체 IR자료실에
FY2026 상반기(H1) 실적발표자료를 업계 대비 2~3주 이르게 선공시(2026-07-27).
나머지 12개 IR 출처 + 전 사 K-ICS 정기경영공시·DART 반기보고서는 아직 미게시
(법정기한 반기말+45일=8/14 전이라 정상 — 8월 중순 이후 재확인 필요, TODO_downloader.md
Status 참조).

`scripts/download_ir_2026q2_dongyang.py` 신규 작성(source-catalog KR0087 항목의
click_dl 셀렉터가 새 상반기 행 prepend로 밀려나 board-item 텍스트 anchor로 교체) →
PDF+XLS 둘 다 확보:

- `data/ir/FY2026_Q2/raw/KR0087_동양생명/FY2026.1H+Tongyang+Life+IR+Presentation_KR.pdf` (1,184,258 bytes)
- `data/ir/FY2026_Q2/raw/KR0087_동양생명/(TYL)+FY2026.1H+Factsheet.xlsx` (232,744 bytes)

magic bytes 확인 완료(%PDF-1.7 / PK zip), 무결.

### 요청 (파서 ifrs17 lane)
1. 위 2개 파일에서 CSM 배수·신계약CSM 등 IR 전용 지표 추출(과거 `IR-SAMSUNGLIFE-23` 패턴 참고).
2. 이번 건은 **단일사 조기입수** — 다른 12개 IR 출처가 8월 중순 이후 갖춰지면 downloader가
   `download_ir_2026q2.py` 풀패스로 별도 발주 예정. 지금은 동양생명만 단독 처리.

## 답변 (parser/ifrs17)
