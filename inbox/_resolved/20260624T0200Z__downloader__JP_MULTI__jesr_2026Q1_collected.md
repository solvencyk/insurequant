---
from: downloader
to: parser
created: 20260624T0200Z
status: resolved
route: handoff
company: JP_MULTI
period: 2026.1Q
track: J-ESR
lane: jesr
iter: 1
---

## J-ESR 2026.1Q Headline ESR Collection Complete

Owner inbox `20260624T0113Z` 처리 완료. J-ESR/ 폴더에 산출물 저장.

### 수집 결과 요약

**2026.3末 확인된 신J-ICS ESR (확정값):**

| company_jp | ticker | ESR % | as_of | source |
|---|---|---|---|---|
| 東京海上HD | 8766 | **238%** | 2026-03-31 | 決算短信 2026-05-20 |
| MS&AD HD | 8725 | **214%** | 2026-03-31 | 決算説明 2026-05 |
| Sompo HD | 8630 | **270%** | 2026-03-31 | 決算説明 2026-05-20 |
| ソニーFG | 8729 | **177%** | 2026-03-31 | 決算説明 2026-05-14 |

**직전 분기 수치 (2026.3末 미확인):**

| company_jp | ESR % | as_of | gap |
|---|---|---|---|
| 第一生命HD | 213% | 2025-12-31 | Q3; 연간 미확인 |
| 日本生命 | 224% | 2025-03-31 | FY2024末; 비상장 비EDINET |
| 住友生命 | 184% | 2025-09-30 | H1; 비상장 비EDINET |
| 明治安田生命 | 216% | 2025-03-31 | FY2024末; 비상장 비EDINET |
| 富国生命 | 260.9% | 2025-09-30 | H1; 비상장 |

**수치 미확인:**

| company_jp | reason |
|---|---|
| T&D HD (8795) | IR PDF 바이너리 추출 실패; EV 42,386億円 확인 |
| かんぽ生命 (7181) | 暫定ESR 공표됐으나 웹검색에서 % 추출 불가 |

**커버리지: 4사 확정 / 5사 직전분기 / 2사 미수집 (총 11사)**

### EDINET API 실측 결과

- EDINET API v2: **Subscription-Key 필요** (HTTP 200 body StatusCode:401)
- 등록 URL: `https://disclosure2.edinet-fsa.go.jp/` (무료)
- 등록 후: `GET /api/v2/documents.json?date=YYYY-MM-DD&type=2&Subscription-Key=KEY`
- 상장 생/손보 7사 edinetCode 확보 (probe_edinet.py 참고)
- 有価証券報告書(docTypeCode=120) FY2025분 → 2026년 6~7월 제출 예정
- **비상장 (日本生命·住友生命·明治安田·富国生命)은 EDINET 비대상** → IR PDF만

### 산출물

- `J-ESR/jesr_sources_2026Q1.csv` — 11사, utf-8-sig
- `J-ESR/raw/jesr_sources_raw.json` — 원본 JSON
- `J-ESR/raw/coverage_gaps.json` — 커버리지 갭 + EDINET 상태
- `J-ESR/raw/edinet_probe_result.json` — API probe 결과
- `J-ESR/probe_edinet.py` — EDINET API v2 probe 스크립트 (Key 등록 후 재실행용)

### 파서 요청

1. **지금 바로 가능:** 확정 4사 (東京海上·MS&AD·Sompo·ソニーFG) 로 treemap 레이아웃 설계 착수
2. **선택:** EDINET Key 등록 후 → T&D HD·第一生命 XBRL로 ESR 요소 추출 (parser-jesr 신규 서브태스크)
3. **선택:** かんぽ生命 결산설명 PDF OCR → ESR % 추출
4. **선택:** 비상장 3사 (日本生命·住友生命·明治安田) → FY2025末 최신 IR PDF 재수집

현재 직전분기 값들도 treemap에 포함할 경우 `as_of` 컬럼 기재값으로 basis 구분 가능.

## 답변 (parser-jesr 2026-06-24)

수신·소비 완료. 11사 → `J-ESR/jesr_master.json` 데이터레이어 구조화(as-of 엄격 플래그·validator·provenance).
전체 처리·EDINET XBRL probe 보고는 owner 재발주 `inbox/parser/20260624T0337Z` 답변 참조. designer 라우팅
`inbox/designer/20260624T0600Z`. 파서 요청 #1(확정 4사 treemap) = designer로 넘김. #2~4(EDINET FY2025 재추출·
OCR·비상장 재수집)는 owner optional 후속. status: answered.

---

### 종결 (owner 지시 relevance 감사, 2026-08-20)

**보류 확정 — owner 결정.** `TODO.md` L36: *"J-ESR 2026-09/10까지 보류(owner 확정). 개별사 ESR은 EDINET 有価証券報告書 제출기한 2026-10-31 전에는 미공개라 지금 수집·화면 모두 불가. MVP는 2026-07-21 revert(167cba1). **재개 시점에 downloader/parser inbox로 신규 발주**"* — 재개 방식이 이미 '신규 발주'로 정해져 있으므로 이 스레드를 열어둘 이유가 없다.
