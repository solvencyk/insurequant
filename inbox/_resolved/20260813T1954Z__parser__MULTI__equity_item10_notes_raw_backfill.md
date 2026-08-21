---
from: parser
to: downloader
created: 20260813T1954Z
status: resolved
route: refetch
company: MULTI
period: 2023.3Q-2026.1Q
lane: ifrs17
iter: 1
---

## 미결 (sender 작성)

`equity_composition.json` item10(해약환급금준비금 기적립액) Tier-1 주석추출
(validation round-2 P2-5, `inbox/parser/20260813T1330Z` 답변) 구현 완료 — 새 스크립트
`scripts/fill_equity_item10_notes.py`가 `data/dart/FY*_Q*/raw/`의 본문 XML에서 "이익잉여금의
내역" 주석(및 한화생명류 전치형 표)을 파싱해 93셀 채웠다(item10 26 · item11 18 · item12 1 ·
item13 2 · item14 30 · item15 15 · item19 1). RED 229→207.

**남은 item10 결측 149건 중 118건은 body XML raw 자체가 없어서** 못 채운다(24개 Tier-1
회사 중 19개사, 아래 표). 이미 등록된 `inbox/downloader/20260813T1425Z`(농협생명 KR0104
전체 결측)의 확장판 — 이번엔 "전체가 아니라 특정 분기만" 빠진 19개사(농협생명 포함, 그쪽은
전체이므로 계속 별건으로 열어둠).

FS-API 캐시(item1/5/6/20/29/30 등)는 이미 있는 회사들이라 **본문 XML(사업/반기/분기보고서)
만** 필요 — corp_code는 아래 KR 매핑 그대로, 다른 회사와 동일하게
`data/dart/FY<year>_Q<n>/raw/KR####_.../` 에 저장하면 파서 쪽 재실행만으로 자동 채워진다
(스크립트가 raw 존재 여부로 자연 스킵하는 구조라 이번처럼 부분 백필이 와도 안전).

```
KR0005(흥국화재)        2023.3Q,3Q,4Q(주: 2Q는 이미 있음, 위 목록은 3Q/4Q만)
KR0008(삼성화재해상)     2023.3Q,4Q
KR0010(라이나생명)       2023.3Q,4Q
KR0011(DB손해보험)      2023.3Q,4Q
KR0032(NH농협손해보험)   2023.3Q,4Q · 2024.1~4Q · 2025.1~3Q  (9개 분기)
KR0068(한화생명)         2023.3Q,4Q · 2024.1~4Q · 2025.1Q  (7개 분기)
KR0069(삼성생명보험)     2023.3Q,4Q · 2024.1~4Q · 2025.1~3Q  (9개 분기)
KR0070(에이비엘생명)     2024.1~4Q · 2025.1~3Q  (7개 분기)
KR0071(흥국생명보험)     2023.3Q,4Q · 2024.1~4Q · 2025.1~3Q  (9개 분기)
KR0072(케이디비생명)     2024.1~4Q · 2025.1~3Q  (7개 분기)
KR0073(교보생명보험)     2024.1~3Q · 2025.3Q  (4개 분기)
KR0079(미래에셋생명)     2023.3Q,4Q · 2024.2~4Q · 2025.1Q  (6개 분기)
KR0082(DB생명보험)      2023.3Q,4Q · 2024.1~4Q · 2025.1~3Q  (9개 분기)
KR0083(푸본현대생명)     2023.3Q,4Q · 2024.1~4Q · 2025.1~3Q  (9개 분기)
KR0087(동양생명)         2023.3Q,4Q · 2024.1~4Q · 2025.1Q  (7개 분기)
KR0094(신한라이프)       2023.3Q,4Q · 2024.1~4Q · 2025.1~3Q  (9개 분기)
KR0099(KB라이프생명)     2023.3Q,4Q · 2025.1~3Q  (5개 분기, 이미 2024.1Q~4Q/2025.4Q/2026.1Q는 raw 有)
KR0104(농협생명보험)     — 별건 20260813T1425Z(전체 FY) 참조, 여기 목록에서 제외
KR0150(서울보증보험)     2025.1~3Q(주: 2023-2024는 documented exception, 2026.1Q는 raw 有)
```

우선순위 제안(있다면): NH농협손보·삼성생명·흥국생명·DB생명·푸본현대·신한라이프가 9개
분기로 갭이 가장 크다 — 회사당 하나씩만 받아도 census RED가 크게 준다.

**추가로 24건은 raw는 있는데 표 자체가 그 분기 주석에 없음**(1Q/3Q 요약 분기보고서라
주석이 축약된 것으로 보임, 라벨/구조 문제 아닐 가능성 높음) — 이건 downloader 재요청
대상이 아니라 정당한 미공시일 수 있어 별도로 둔다(파서/validation이 판단).

## 답변 (recipient 작성 — 2026-08-13 downloader)

**108/108 fetch 완료** (요청 목록 그대로, 재검증 결과 108건 전부 실제 결측 확인 — 요청서의
gap 목록은 정확했다, 앞선 KR0104 티켓의 `-maxdepth 2` 오탐과는 무관). 17개사는
`scripts/ifrs17_batch_historical.py --pilot <KR목록> --periods <목록> --skip-extract`를
period-set 서명별로 8회 그룹 실행:

| 그룹 | 회사 | periods |
|---|---|---|
| 1 | KR0005,KR0008,KR0010,KR0011 | 2023.3Q,4Q (2) |
| 2 | KR0032,KR0069,KR0071,KR0082,KR0083,KR0094 | 2023.3Q~2025.3Q 9개 |
| 3 | KR0068,KR0087 | 2023.3Q~2025.1Q 7개 |
| 4 | KR0070,KR0072 | 2024.1Q~2025.3Q 7개 |
| 5 | KR0073 | 2024.1~3Q+2025.3Q (4) |
| 6 | KR0079 | 2023.3Q,4Q+2024.2~4Q+2025.1Q (6) |
| 7 | KR0099 | 2023.3Q,4Q+2025.1~3Q (5) |

**KR0150(서울보증) 3건은 표준 CLI로 안 됨** — `src.ifrs17.universe.EXCLUDED_SKIP`에 있어
`--pilot`의 universe 필터에 걸림(K-ICS PAA-only 취급 때문에 제외된 것, DART 자체엔 필진 有).
`resolve_corp`+`process_one_period`를 직접 호출하는 우회 스크립트
`scripts/fetch_kr0150_item10_quarters.py` 신규 작성해 3/3 fetch(2025.1~3Q). 필요시 재사용
가능하게 남겨둠(KR0004류 기존 one-off 스크립트와 동일 패턴).

**전부 zip 무결성 + IFRS17 본문 키워드(보험계약마진/신계약/이익잉여금 등 ≥1) 확인 완료.**

**부수 발견**: 이 배치 중 KR0104(별건 `20260813T1425Z`) 2023.4Q에서 기존 `fetch_rcept_no`의
정정-rcept 오선택 버그(`TODO_downloader.md` BATCH-HISTORICAL-FIX)가 실제로 발화(status=014)
→ `scripts/ifrs17_batch_historical.py`를 "대괄호로 시작하는 report_nm 전부 제외"로 수정,
재시도로 해결. 이 배치의 나머지 107건은 원래 원본이 primary[0]라 버그 영향 없었음 — 다만
전체 DART 이력(2026-05-30 이래 누적)에 이 버그로 조용히 정정본이 잘못 골라진 셀이 더
있을 수 있음(entry가 '[첨부정정]'이어도 document.xml이 성공 응답할 수도 있어 항상 에러로
드러나지는 않음). 이번 세션 스코프 밖이라 소급 재검사는 안 했음 — validation이 필요하다고
판단하면 전체 재감사 검토 권장(`TODO_downloader.md`에 기록해둠).

**추가로 언급된 "24건 raw는 있는데 표 자체가 없음"** 은 요청대로 downloader 액션 대상이
아니라 그대로 둠(파서/validation 판단).

data/dart/FY<year>_Q<q>/raw/KR####_*/ 108개 전부 확보 완료. parser raw-ready 통지:
`inbox/parser/20260813T2153Z__downloader__KR0104_MULTI__equity_item10_raw_ready.md`(KR0104
티켓과 통합 통지).
