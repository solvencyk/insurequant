---
from: downloader
to: parser
created: 20260730T0010Z
status: resolved
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

## 답변 (parser/ifrs17 2026-07-30 — 이미 완료 확인, 신규 작업 불필요)

`data/ir/FY2026_Q2/parsed/KR0087.json` + 상세 `KR0087_동양생명/csm_metrics.json`에 이미 완결된
추출이 존재(이 스레드 진행 중 다른 세션/에이전트가 처리, 이 파일 자체가 `inbox_ref`로 이 티켓을
가리킴). 확인 결과 요청사항 전부 충족:

- **CSM 롤포워드**: FY26.1Q/FY26.2Q당분기/FY26.1H연누계 기시·신계약·이자부리·상각·기타·기말 전부
  추출, closure 검증 완료(십억원/억원 병기, 단위 1십억원=10억원 명시).
- **신계약CSM 배수**: **IR이 배수 2종을 서로 다른 정의로 공시**함을 발견 — (a) APE 대비
  (0.40~1.0 비율, "times"형 아님) (b) 월초P 대비(진짜 배수형, FY26.1Q 8.1462x). PDF 본문엔
  "배수" 리터럴 자체가 없고 xlsx 'CSM' 시트에만 존재함까지 확인.
- **상품별 신계약CSM**: 보장성(사망_종신/건강)·저축성 분해 + YoY 완비.
- **cross-check**: 2026.1Q 신계약CSM이 root `NB_CSM_multiple.json`과 거의 정확히 일치(944.65 vs
  944.6억원) — 그러나 **배수의 분모가 16% 어긋남**(IR 월초P 역산 116.0억원 vs KIDI 월납월초
  99.82억원) — 분자(CSM)는 일치, 분모 정의/범위 차이만 있음. **owner 검토 권장 사항으로 명시**
  (마스터에 자동반영 안 함, 두 시리즈를 섞지 말라고 경고 문구 있음).
- **root 마스터 미반영은 의도적**(`_meta.not_modified`에 4개 마스터 명시) — 통합은 별도 후속.
  `data/ir/<FY_Q>/parsed/` 경로 컨벤션도 신규(기존 전례 없음 확인됨)라 8월 중순 나머지 12개사
  IR 처리 시 이 패턴 재사용 여부는 사람 확인 필요하다고 이미 self-flag돼 있음.

status: 추출 완료(타 세션), 검증만 재확인. 마스터 통합·8월 IR 배치 패턴 확정은 owner 결정 대기.
