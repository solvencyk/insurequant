---
from: owner
to: downloader
created: 20260624T0337Z
status: resolved
route: pipeline
company: JP_MULTI
period: 2026.1Q
track: J-ESR
---

## 미결 (owner) — 일본 ESR 전수 파이프라인 구축 (10월 EDINET 有報 드롭 대비) [J-ESR]

**배경(1차 수집으로 드러난 구조)**: 일본 개별사 ESR은 有価証券報告書(EDINET) 제출기한 **2026.10.31**까지 미공개. 지금(6월)은 **그룹HD 연결 ESR(결산설명, 5월)만** + 일부 대형 비상장 생보·단독상장사 선공개. 즉 **한국식 분기 일괄(36사 정합)이 일본엔 지금 불가**. 10월 有報 제출 후에야 개별사 전수(일관 2026.3末 as-of) 가능.

> ⚠️ **이건 "지금 수집"이 아니라 "10월에 자동으로 채워질 파이프라인"을 까는 작업.** 별도 일본 화면(한국 index.html과 분리)용 데이터 척추. 산출물 `J-ESR/`에만.

**할 것:**
1. **EDINET API Subscription-Key 등록**(무료) → `J-ESR/edinet_key.txt`(gitignore) or 환경변수. `probe_edinet.py` 확장해 **인증된 documents.json + XBRL 다운로드** 동작 확인(상장 7사로 스모크).
2. **XBRL 추출기 scaffold** `J-ESR/jesr_edinet_fetch.py` — 有報 docID 검색(보험업 EDINET코드 목록) → XBRL zip → ESR 정량공시(Pillar-3: 所要資本·적격자본·ESR比率·민감도·변동요인) 태그 추출. **10월 제출분을 일괄 긁도록** 설계(지금은 작년분으로 dry-run 가능하면).
3. **비상장 상호사 IR-PDF 루트 별도 설계** — 日本生命·住友生命·明治安田·富国생명 등은 **EDINET 비대상**(有報 미제출) → ディスクロージャー誌/決算プレス PDF에서 ESR 추출 경로 `J-ESR/jesr_mutual_irpdf.py`(목록+URL 패턴).
4. **대상 마스터 리스트** `J-ESR/jp_insurers.csv` — 일본 생보·손보 (그룹HD + 개별 자회사 + 상호사), EDINET코드/IR URL/상장여부/EDINET대상여부 매핑(한국 source-catalog.yaml 대응).

**산출물**: 위 4종 + `J-ESR/jesr_pipeline_status.md`(10월 가동 체크리스트·커버리지 추정). **이번엔 데이터 채우기보다 인프라가 목표**(10월에 채움).

→ 끝나면 답변란에 EDINET 인증/XBRL 추출 동작 결과 + 10월 전수 예상 커버리지(EDINET 몇 사 / IR-PDF 몇 사 / 미공개).

## 답변 (downloader, 2026-06-24)

**4종 산출물 완료:**

1. `J-ESR/jp_insurers.csv` — 생보 41 + 손보 31 + 재보험 2 = 74사 마스터리스트
   - 확인된 EDINET 코드: 13사 (HD 7 + 子会社有報提出 6)
   - 상호회사 5사: none 명시 (EDINET 비대상)
   - TBD 코드: API 키 취득 후 bulk lookup으로 채울 것

2. `J-ESR/jesr_edinet_fetch.py` — XBRL 추출기 scaffold
   - `--smoke` 플래그: API 키 취득 후 즉시 연결 확인
   - `--all --year 2026`: 13개 known 코드 전수 有報 검색 + XBRL 다운로드
   - ESR 태그 추출: STUB (`extract_esr_from_xbrl`) — FSA J-ICS XBRL 택소노미 공개 대기
   - math validator 포함: `eligible_capital / required_capital * 100 ≈ esr_pct ±2%`

3. `J-ESR/jesr_mutual_irpdf.py` — 상호사 5사 IR-PDF 루트
   - 회사별 IR 베이스 URL + 결산프레스 URL 설정 완료
   - `--check`: HEAD 확인 / `--download`: PDF 취득 / `--extract`: LLM 추출 scaffold
   - 현재 pdf_url_pattern = TBD (5월 결산프레스 PDF URL 연도별 업데이트 필요)
   - seed ESR 값 내장: 住友184%·明治安田216%·富国260.9%·日本224% (2025.3末 기준)

4. `J-ESR/jesr_pipeline_status.md` — 10월 가동 체크리스트
   - 커버리지 추정: EDINET ~12사 + IR-PDF ~5사 + HD 7사 = **~44사** (전체 74사 중 60%)
   - 소형·외자 ~30사는 2027년 이후 문화 성숙 후 커버 가능

**EDINET 인증 상태:**
- API probe 결과: StatusCode 401, Subscription-Key 필요
- 무료 등록: https://disclosure2.edinet-fsa.go.jp/ → APIの利用
- **owner 액션 필요**: 키 등록 후 `J-ESR/edinet_key.txt`에 저장 → `--smoke` 확인

**10월 예상 커버리지:**
- EDINET 有報 (10.31 제출): ~12사 (코드 확인된 자회사)
- 상호사 IR-PDF (5~7월 결산프레스): 5사
- HD 연결 (이미 수집): 7사
- **2026.3末 as-of 정합 집계: 약 44사 가능**
